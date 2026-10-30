from collections.abc import Iterator
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.stub import Stubber
from pydantic import JsonValue

from tests.llm.conftest import TOOL
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.llm.bedrock import AnthropicMessagesClient, BedrockLLMClient, ConverseLLMClient
from triagelite.llm.fake import FakeLLMClient, tool_response
from triagelite.llm.types import ModelRequest, ToolSpec
from triagelite.settings import Settings

REPO_CONFIG = Path(__file__).parents[2] / "config"
SCHEMA: dict[str, JsonValue] = {"type": "object", "properties": {"items": {"type": "array"}}}
REQUEST = ModelRequest(
    model_id="moonshotai.kimi-k2.5",
    api="converse",
    max_tokens=512,
    system="You label bug reports.",
    user="<incidents>...</incidents>",
    tool=ToolSpec(name=TOOL, description="Submit.", input_schema=SCHEMA),
    timeout_seconds=30,
)
EXPECTED_PARAMS = {
    "modelId": "moonshotai.kimi-k2.5",
    "system": [{"text": "You label bug reports."}],
    "messages": [{"role": "user", "content": [{"text": "<incidents>...</incidents>"}]}],
    "inferenceConfig": {"maxTokens": 512},
    "toolConfig": {
        "tools": [
            {"toolSpec": {"name": TOOL, "description": "Submit.", "inputSchema": {"json": SCHEMA}}}
        ],
        "toolChoice": {"auto": {}},
    },
}


def converse_response(
    content: list[dict[str, object]], stop: str = "tool_use"
) -> dict[str, object]:
    return {
        "output": {"message": {"role": "assistant", "content": content}},
        "stopReason": stop,
        "usage": {"inputTokens": 321, "outputTokens": 45, "totalTokens": 366},
        "metrics": {"latencyMs": 900},
    }


@pytest.fixture
def stubbed() -> Iterator[tuple[ConverseLLMClient, Stubber]]:
    runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
    with Stubber(runtime) as stubber:
        yield ConverseLLMClient(runtime), stubber
        stubber.assert_no_pending_responses()


def test_sends_one_auto_tool_and_keeps_only_tool_use(
    stubbed: tuple[ConverseLLMClient, Stubber],
) -> None:
    client, stubber = stubbed
    content: list[dict[str, object]] = [
        {"reasoningContent": {"reasoningText": {"text": "thinking..."}}},
        {"text": "Here are the labels."},
        {"toolUse": {"toolUseId": "t1", "name": TOOL, "input": {"items": []}}},
    ]
    stubber.add_response("converse", converse_response(content), EXPECTED_PARAMS)

    response = client.complete(REQUEST)

    assert response.stop_reason == "tool_use"
    assert [(c.name, c.input) for c in response.tool_calls] == [(TOOL, {"items": []})]
    assert (response.input_tokens, response.output_tokens) == (321, 45)


def test_effort_becomes_reasoning_effort(stubbed: tuple[ConverseLLMClient, Stubber]) -> None:
    client, stubber = stubbed
    stubber.add_response(
        "converse",
        converse_response([{"text": "no tool"}], stop="end_turn"),
        EXPECTED_PARAMS | {"additionalModelRequestFields": {"reasoning_effort": "low"}},
    )

    response = client.complete(REQUEST.model_copy(update={"effort": "low"}))

    assert response.tool_calls == ()
    assert response.stop_reason == "end_turn"


@pytest.mark.parametrize(
    ("code", "expected", "retryable"),
    [
        ("ThrottlingException", LLMRateLimitError, None),
        ("ServiceQuotaExceededException", LLMRateLimitError, None),
        ("ModelTimeoutException", LLMProviderError, True),
        ("ServiceUnavailableException", LLMProviderError, True),
        ("ValidationException", LLMProviderError, False),
        ("AccessDeniedException", LLMProviderError, False),
    ],
)
def test_service_errors_map_by_type(
    stubbed: tuple[ConverseLLMClient, Stubber],
    code: str,
    expected: type[Exception],
    retryable: bool | None,
) -> None:
    client, stubber = stubbed
    stubber.add_client_error("converse", service_error_code=code, http_status_code=400)

    with pytest.raises(expected) as raised:
        client.complete(REQUEST)

    if retryable is not None:
        assert isinstance(raised.value, LLMProviderError)
        assert raised.value.retryable is retryable


def test_connection_failure_is_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

    def fail(**_: object) -> None:
        raise EndpointConnectionError(endpoint_url="https://bedrock-runtime")

    monkeypatch.setattr(runtime, "converse", fail)

    with pytest.raises(LLMProviderError) as raised:
        ConverseLLMClient(runtime).complete(REQUEST)

    assert raised.value.retryable is True


def test_router_sends_each_request_to_its_api() -> None:
    messages = FakeLLMClient([tool_response(TOOL, {"from": "messages"})])
    converse = FakeLLMClient([tool_response(TOOL, {"from": "converse"})])
    router = BedrockLLMClient(messages, converse)

    first = router.complete(REQUEST)
    second = router.complete(REQUEST.model_copy(update={"api": "messages"}))

    assert first.tool_calls[0].input == {"from": "converse"}
    assert second.tool_calls[0].input == {"from": "messages"}
    assert (len(messages.requests), len(converse.requests)) == (1, 1)


def test_from_settings_builds_both_transports() -> None:
    router = BedrockLLMClient.from_settings(Settings(config_dir=REPO_CONFIG), 30)

    assert isinstance(router._clients["converse"], ConverseLLMClient)
    assert isinstance(router._clients["messages"], AnthropicMessagesClient)
