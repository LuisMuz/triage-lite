"""Runs the real Anthropic SDK against a fake HTTP transport: real serialization, no network."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic
import httpx2
import pytest
from anthropic import AnthropicBedrock

from tests.llm.conftest import TOOL, valid_payload
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.llm.bedrock import AnthropicMessagesClient, to_domain_error
from triagelite.llm.types import ModelRequest, ToolSpec
from triagelite.settings import Settings

REPO_CONFIG = Path(__file__).parents[2] / "config"

Handler = Callable[[httpx2.Request], httpx2.Response]

REQUEST = ModelRequest(
    model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0",
    api="messages",
    max_tokens=512,
    system="You label bug reports.",
    user="<incidents>...</incidents>",
    tool=ToolSpec(name=TOOL, description="Submit.", input_schema={"type": "object"}),
    timeout_seconds=30,
)


def message_body(content: list[dict[str, Any]], stop_reason: str = "tool_use") -> dict[str, Any]:
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-4-5",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 321, "output_tokens": 45},
    }


def bedrock_client(handler: Handler) -> AnthropicMessagesClient:
    sdk = AnthropicBedrock(
        aws_region="us-east-1",
        # Dummy values: SigV4 signing needs *some* credentials; nothing leaves the process.
        aws_access_key="testing",
        aws_secret_key="testing",  # noqa: S106
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicMessagesClient(sdk)


def capture(sent: list[dict[str, Any]], response: httpx2.Response) -> Handler:
    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(json.loads(request.content))
        return response

    return handler


def test_tool_use_response_is_converted() -> None:
    tool_block = {"type": "tool_use", "id": "tu_1", "name": TOOL, "input": valid_payload()}
    body = message_body([{"type": "text", "text": "Sure."}, tool_block])
    client = bedrock_client(lambda _: httpx2.Response(200, json=body))

    response = client.complete(REQUEST)

    assert response.stop_reason == "tool_use"
    assert [call.name for call in response.tool_calls] == [TOOL]
    assert response.tool_calls[0].input == valid_payload()
    assert (response.input_tokens, response.output_tokens) == (321, 45)


def test_request_body_uses_one_tool_with_auto_choice() -> None:
    sent: list[dict[str, Any]] = []
    ok = httpx2.Response(200, json=message_body([], stop_reason="end_turn"))
    bedrock_client(capture(sent, ok)).complete(REQUEST)

    [body] = sent
    assert body["tools"] == [
        {"name": TOOL, "description": "Submit.", "input_schema": {"type": "object"}}
    ]
    assert body["tool_choice"] == {"type": "auto"}
    assert body["system"] == "You label bug reports."
    assert body["messages"] == [{"role": "user", "content": "<incidents>...</incidents>"}]
    assert "thinking" not in body
    assert "output_config" not in body


def test_thinking_and_effort_are_sent_only_when_configured() -> None:
    sent: list[dict[str, Any]] = []
    ok = httpx2.Response(200, json=message_body([], stop_reason="end_turn"))
    request = REQUEST.model_copy(update={"thinking": "disabled", "effort": "low"})

    bedrock_client(capture(sent, ok)).complete(request)

    assert sent[0]["thinking"] == {"type": "disabled"}
    assert sent[0]["output_config"] == {"effort": "low"}


def test_throttling_maps_to_rate_limit_error() -> None:
    client = bedrock_client(lambda _: httpx2.Response(429, json={"message": "Too many requests"}))

    with pytest.raises(LLMRateLimitError):
        client.complete(REQUEST)


@pytest.mark.parametrize(
    ("status", "retryable"),
    [(500, True), (503, True), (529, True), (400, False), (403, False), (404, False)],
)
def test_status_errors_map_to_provider_error(status: int, retryable: bool) -> None:
    client = bedrock_client(lambda _: httpx2.Response(status, json={"message": "nope"}))

    with pytest.raises(LLMProviderError) as raised:
        client.complete(REQUEST)

    assert raised.value.retryable is retryable


def test_connection_failure_is_retryable() -> None:
    def refuse(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("connection refused", request=request)

    with pytest.raises(LLMProviderError) as raised:
        bedrock_client(refuse).complete(REQUEST)

    assert raised.value.retryable is True


def test_missing_credentials_are_not_retryable() -> None:
    error = to_domain_error(anthropic.CredentialsError("SSO token expired"))

    assert isinstance(error, LLMProviderError)
    assert error.retryable is False


def test_from_settings_disables_sdk_retries() -> None:
    # TL-15: hidden SDK retries would be attempts without an LLMCallRecord.
    client = AnthropicMessagesClient.from_settings(Settings(config_dir=REPO_CONFIG))

    assert client._sdk.max_retries == 0
