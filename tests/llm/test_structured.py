import pytest

from tests.llm.conftest import MODEL_ID, TOOL, VARIABLES, valid_payload
from triagelite.domain.enums import CallStatus, Severity
from triagelite.domain.errors import (
    ConfigError,
    LLMOutputValidationError,
    LLMProviderError,
    LLMRateLimitError,
)
from triagelite.domain.models import ClassifyOutput, LLMCallRecord, RawIncident
from triagelite.llm.config import ModelsConfig
from triagelite.llm.fake import (
    DEFAULT_INPUT_TOKENS,
    DEFAULT_OUTPUT_TOKENS,
    FakeLLMClient,
    ScriptStep,
    text_only,
    tool_response,
    truncated,
)
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import (
    MAX_ERRORS_IN_RETRY,
    RETRY_INSTRUCTION,
    StructuredLLM,
    parse_tool_output,
)
from triagelite.llm.types import ModelResponse, ToolCall

BAD_ENUM = tool_response(TOOL, valid_payload(severity="blocker"))
GOOD = tool_response(TOOL, valid_payload())
RETRY_MARKER = RETRY_INSTRUCTION.splitlines()[0]


def run(
    script: list[ScriptStep],
    prompt: PromptFile,
    models: ModelsConfig,
    prices: PriceTable,
    recorded: list[LLMCallRecord],
) -> tuple[FakeLLMClient, StructuredLLM]:
    client = FakeLLMClient(script)
    return client, StructuredLLM(client, models, prices, recorder=recorded.append)


class TestHappyPath:
    def test_returns_validated_output(
        self,
        prompt: PromptFile,
        models: ModelsConfig,
        prices: PriceTable,
        recorded: list[LLMCallRecord],
    ) -> None:
        _, llm = run([GOOD], prompt, models, prices, recorded)

        result = llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

        assert result.output.items[0].severity is Severity.CRITICAL
        assert result.attempts == 1

    def test_request_carries_tool_built_from_schema(
        self,
        prompt: PromptFile,
        models: ModelsConfig,
        prices: PriceTable,
        recorded: list[LLMCallRecord],
    ) -> None:
        client, llm = run([GOOD], prompt, models, prices, recorded)

        llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

        request = client.requests[0]
        assert request.tool.name == TOOL
        assert request.tool.input_schema == ClassifyOutput.model_json_schema()
        assert request.model_id == MODEL_ID
        assert request.max_tokens == 4096
        assert request.timeout_seconds == 30
        assert "critical = outage" in request.system
        assert '<incident id="inc-1">' in request.user

    def test_records_one_ok_attempt_with_cost(
        self,
        prompt: PromptFile,
        models: ModelsConfig,
        prices: PriceTable,
        recorded: list[LLMCallRecord],
    ) -> None:
        _, llm = run([GOOD], prompt, models, prices, recorded)

        result = llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

        [record] = recorded
        assert record.status is CallStatus.OK
        assert record.error_type is None
        assert record.attempt == 1
        assert record.call_id == result.call_id
        assert record.prompt_version == "classify/v1"
        assert record.stop_reason == "tool_use"
        assert record.input_tokens == DEFAULT_INPUT_TOKENS
        assert record.cost_usd == pytest.approx(
            (DEFAULT_INPUT_TOKENS * 1.0 + DEFAULT_OUTPUT_TOKENS * 5.0) / 1_000_000
        )
        assert result.records == (record,)


@pytest.mark.parametrize(
    ("bad", "reason"),
    [
        (truncated(TOOL, valid_payload()), "truncated"),
        (text_only(), "no tool call"),
        (BAD_ENUM, "schema"),
    ],
    ids=["truncated", "no-tool-call", "bad-enum"],
)
class TestValidationRetry:
    def test_retries_exactly_once_then_raises(
        self,
        bad: ModelResponse,
        reason: str,
        prompt: PromptFile,
        models: ModelsConfig,
        prices: PriceTable,
        recorded: list[LLMCallRecord],
    ) -> None:
        client, llm = run([bad, bad], prompt, models, prices, recorded)

        with pytest.raises(LLMOutputValidationError, match=reason):
            llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

        assert len(client.requests) == 2
        assert [r.status for r in recorded] == [CallStatus.VALIDATION_ERROR] * 2
        assert [r.attempt for r in recorded] == [1, 2]
        assert len({r.call_id for r in recorded}) == 1

    def test_retry_appends_errors_and_keeps_system_prompt(
        self,
        bad: ModelResponse,
        reason: str,
        prompt: PromptFile,
        models: ModelsConfig,
        prices: PriceTable,
        recorded: list[LLMCallRecord],
    ) -> None:
        client, llm = run([bad, GOOD], prompt, models, prices, recorded)

        result = llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

        first, retry = client.requests
        assert retry.system == first.system
        assert retry.user.startswith(first.user)
        assert RETRY_MARKER in retry.user
        assert RETRY_MARKER not in first.user
        assert result.attempts == 2
        assert [r.status for r in recorded] == [CallStatus.VALIDATION_ERROR, CallStatus.OK]


def test_retry_message_names_the_invalid_field(
    prompt: PromptFile, models: ModelsConfig, prices: PriceTable, recorded: list[LLMCallRecord]
) -> None:
    client, llm = run([BAD_ENUM, GOOD], prompt, models, prices, recorded)

    llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

    assert "items.0.severity:" in client.requests[1].user


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (LLMRateLimitError("429"), CallStatus.RATE_LIMITED),
        (LLMProviderError("503", retryable=True), CallStatus.PROVIDER_ERROR),
        (LLMProviderError("403", retryable=False), CallStatus.PROVIDER_ERROR),
    ],
    ids=["throttled", "server-error", "forbidden"],
)
def test_availability_errors_raise_without_validation_retry(
    error: LLMRateLimitError | LLMProviderError,
    status: CallStatus,
    prompt: PromptFile,
    models: ModelsConfig,
    prices: PriceTable,
    recorded: list[LLMCallRecord],
) -> None:
    client, llm = run([error, GOOD], prompt, models, prices, recorded)

    with pytest.raises(type(error)) as raised:
        llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

    assert raised.value is error
    assert len(client.requests) == 1
    [record] = recorded
    assert record.status is status
    assert record.error_type == type(error).__name__
    assert record.input_tokens == 0
    assert record.cost_usd == 0
    assert record.stop_reason is None


def test_throttled_retry_attempt_is_recorded_as_attempt_two(
    prompt: PromptFile, models: ModelsConfig, prices: PriceTable, recorded: list[LLMCallRecord]
) -> None:
    _, llm = run([BAD_ENUM, LLMRateLimitError("429")], prompt, models, prices, recorded)

    with pytest.raises(LLMRateLimitError):
        llm.generate_structured(prompt, VARIABLES, ClassifyOutput)

    assert [(r.attempt, r.status) for r in recorded] == [
        (1, CallStatus.VALIDATION_ERROR),
        (2, CallStatus.RATE_LIMITED),
    ]


def test_schema_mismatch_with_prompt_is_a_config_error(
    prompt: PromptFile, models: ModelsConfig, prices: PriceTable, recorded: list[LLMCallRecord]
) -> None:
    client, llm = run([GOOD], prompt, models, prices, recorded)

    with pytest.raises(ConfigError, match="RawIncident"):
        llm.generate_structured(prompt, VARIABLES, RawIncident)

    assert client.requests == []


def test_unconfigured_stage_is_a_config_error(
    prompt: PromptFile, prices: PriceTable, recorded: list[LLMCallRecord]
) -> None:
    no_stages = ModelsConfig.model_validate({"client": {"timeout_seconds": 30}, "stages": {}})
    _, llm = run([GOOD], prompt, no_stages, prices, recorded)

    with pytest.raises(ConfigError, match=r"stages\.classify"):
        llm.generate_structured(prompt, VARIABLES, ClassifyOutput)


class TestParseToolOutput:
    def test_refusal_is_a_validation_error(self) -> None:
        refused = GOOD.model_copy(update={"stop_reason": "refusal"})

        with pytest.raises(LLMOutputValidationError, match="refusal"):
            parse_tool_output(refused, TOOL, ClassifyOutput)

    def test_context_window_exceeded_counts_as_truncated(self) -> None:
        cut = GOOD.model_copy(update={"stop_reason": "model_context_window_exceeded"})

        with pytest.raises(LLMOutputValidationError, match="truncated"):
            parse_tool_output(cut, TOOL, ClassifyOutput)

    def test_wrong_tool_name_is_no_tool_call(self) -> None:
        with pytest.raises(LLMOutputValidationError, match="no tool call"):
            parse_tool_output(tool_response("other_tool", valid_payload()), TOOL, ClassifyOutput)

    def test_two_tool_calls_are_rejected(self) -> None:
        call = ToolCall(name=TOOL, input=valid_payload())
        twice = GOOD.model_copy(update={"tool_calls": (call, call)})

        with pytest.raises(LLMOutputValidationError, match="no tool call"):
            parse_tool_output(twice, TOOL, ClassifyOutput)

    def test_error_list_is_capped(self) -> None:
        items = [valid_payload(confidence=9)["items"][0] for _ in range(MAX_ERRORS_IN_RETRY + 5)]

        with pytest.raises(LLMOutputValidationError) as raised:
            parse_tool_output(tool_response(TOOL, {"items": items}), TOOL, ClassifyOutput)

        assert len(raised.value.errors) == MAX_ERRORS_IN_RETRY


def test_fake_client_fails_loudly_when_script_runs_out(
    prompt: PromptFile, models: ModelsConfig, prices: PriceTable, recorded: list[LLMCallRecord]
) -> None:
    _, llm = run([], prompt, models, prices, recorded)

    with pytest.raises(LookupError, match="script exhausted"):
        llm.generate_structured(prompt, VARIABLES, ClassifyOutput)
