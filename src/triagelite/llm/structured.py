"""Typed LLM output: tool use + Pydantic validation + one validation retry (TL-02, TL-05)."""

from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from triagelite.domain.enums import CallStatus
from triagelite.domain.errors import (
    ConfigError,
    LLMOutputValidationError,
    LLMProviderError,
    LLMRateLimitError,
    TriageError,
)
from triagelite.domain.models import LLMCallRecord
from triagelite.llm.client import CallRecorder, LLMClient
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile
from triagelite.llm.types import ModelRequest, ModelResponse, ToolSpec
from triagelite.metrics import log_call_record

TRUNCATED_STOP_REASONS = frozenset({"max_tokens", "model_context_window_exceeded"})
REFUSAL_STOP_REASON = "refusal"
MAX_ERRORS_IN_RETRY = 20
RETRY_INSTRUCTION = (
    "Your previous output failed validation:\n{errors}\nCall the tool again with corrected input."
)

_STATUS_BY_ERROR: dict[type[TriageError], CallStatus] = {
    LLMOutputValidationError: CallStatus.VALIDATION_ERROR,
    LLMRateLimitError: CallStatus.RATE_LIMITED,
    LLMProviderError: CallStatus.PROVIDER_ERROR,
}


@dataclass(frozen=True)
class LLMResult[T: BaseModel]:
    """Validated output plus the records of every attempt that produced it."""

    output: T
    call_id: str
    records: tuple[LLMCallRecord, ...]

    @property
    def attempts(self) -> int:
        """Number of model calls made (1, or 2 after a validation retry)."""
        return len(self.records)


class StructuredLLM:
    """Runs prompts against an `LLMClient` and returns validated Pydantic objects."""

    def __init__(
        self,
        client: LLMClient,
        models: ModelsConfig,
        prices: PriceTable,
        recorder: CallRecorder = log_call_record,
    ) -> None:
        self._client = client
        self._models = models
        self._prices = prices
        self._recorder = recorder

    def generate_structured[T: BaseModel](
        self, prompt: PromptFile, variables: Mapping[str, str], schema: type[T]
    ) -> LLMResult[T]:
        """Call the model and return output validated against `schema`.

        A validation failure (truncated, no tool call, schema error) is retried once with
        the errors appended to the user message; the system prompt stays identical. A second
        failure raises `LLMOutputValidationError` so the caller can mark items `needs_manual`.
        Availability errors are raised immediately: backoff belongs to Step Functions.
        """
        if prompt.schema_name != schema.__name__:
            msg = f"{prompt.id} declares schema {prompt.schema_name!r}, got {schema.__name__!r}"
            raise ConfigError(msg)
        stage = self._models.for_stage(prompt.stage)
        rendered = prompt.render(variables)
        request = ModelRequest(
            model_id=stage.model_id,
            max_tokens=stage.max_tokens,
            system=rendered.system,
            user=rendered.user,
            tool=ToolSpec(
                name=prompt.tool_name,
                description=prompt.tool_description,
                input_schema=schema.model_json_schema(),
            ),
            thinking=stage.thinking,
            effort=stage.effort,
            timeout_seconds=self._models.client.timeout_seconds,
        )
        call_id = uuid4().hex
        records: list[LLMCallRecord] = []
        try:
            output = self._attempt(request, prompt, schema, call_id, records)
        except LLMOutputValidationError as error:
            retry = request.model_copy(update={"user": with_retry_instruction(request.user, error)})
            output = self._attempt(retry, prompt, schema, call_id, records)
        return LLMResult(output=output, call_id=call_id, records=tuple(records))

    def _attempt[T: BaseModel](
        self,
        request: ModelRequest,
        prompt: PromptFile,
        schema: type[T],
        call_id: str,
        records: list[LLMCallRecord],
    ) -> T:
        started = perf_counter()
        response: ModelResponse | None = None
        try:
            response = self._client.complete(request)
            output = parse_tool_output(response, request.tool.name, schema)
        except (LLMOutputValidationError, LLMRateLimitError, LLMProviderError) as error:
            records.append(
                self._record(request, prompt, call_id, records, started, response, error)
            )
            raise
        records.append(self._record(request, prompt, call_id, records, started, response, None))
        return output

    def _record(
        self,
        request: ModelRequest,
        prompt: PromptFile,
        call_id: str,
        previous: list[LLMCallRecord],
        started: float,
        response: ModelResponse | None,
        error: TriageError | None,
    ) -> LLMCallRecord:
        input_tokens = response.input_tokens if response else 0
        output_tokens = response.output_tokens if response else 0
        record = LLMCallRecord(
            call_id=call_id,
            stage=prompt.stage,
            model_id=request.model_id,
            prompt_version=prompt.id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._prices.cost_usd(request.model_id, input_tokens, output_tokens),
            latency_ms=round((perf_counter() - started) * 1000),
            stop_reason=response.stop_reason if response else None,
            attempt=len(previous) + 1,
            status=_STATUS_BY_ERROR[type(error)] if error else CallStatus.OK,
            error_type=type(error).__name__ if error else None,
        )
        self._recorder(record)
        return record


def parse_tool_output[T: BaseModel](response: ModelResponse, tool_name: str, schema: type[T]) -> T:
    """Check `stop_reason` and the tool call *before* trusting anything, then validate.

    Raises:
        LLMOutputValidationError: with `errors` phrased for the model to fix on retry.
    """
    if response.stop_reason in TRUNCATED_STOP_REASONS:
        raise LLMOutputValidationError(
            "truncated",
            errors=[
                f"Your answer was cut off (stop_reason={response.stop_reason}). "
                "Keep each rationale short."
            ],
        )
    if response.stop_reason == REFUSAL_STOP_REASON:
        raise LLMOutputValidationError(
            "refusal", errors=["You declined to answer. Classify the data as instructed."]
        )
    calls = [call for call in response.tool_calls if call.name == tool_name]
    if len(response.tool_calls) != 1 or len(calls) != 1:
        raise LLMOutputValidationError(
            "no tool call", errors=[f"Answer by calling the `{tool_name}` tool exactly once."]
        )
    try:
        return schema.model_validate(calls[0].input)
    except ValidationError as error:
        raise LLMOutputValidationError("schema", errors=format_validation_errors(error)) from error


def format_validation_errors(error: ValidationError) -> list[str]:
    """Turn Pydantic errors into short `path: message` lines the model can act on."""
    lines = [
        f"{'.'.join(str(part) for part in detail['loc']) or '<root>'}: {detail['msg']}"
        for detail in error.errors(include_url=False)
    ]
    return lines[:MAX_ERRORS_IN_RETRY]


def with_retry_instruction(user: str, error: LLMOutputValidationError) -> str:
    """The original user message plus the validation errors, for the single retry."""
    errors = "\n".join(f"- {line}" for line in error.errors or [str(error)])
    return f"{user}\n\n{RETRY_INSTRUCTION.format(errors=errors)}"
