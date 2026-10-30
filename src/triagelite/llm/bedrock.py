"""Claude, other Bedrock models and Titan: the only module that imports the Bedrock SDKs."""

import json
from typing import TYPE_CHECKING, Any, Self

import anthropic
import boto3
from anthropic import AnthropicBedrock
from anthropic.types import (
    Message,
    MessageParam,
    OutputConfigParam,
    ThinkingConfigDisabledParam,
    ToolParam,
)
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, HTTPClientError
from botocore.exceptions import ConnectionError as BotoConnectionError
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from triagelite.domain.errors import LLMProviderError, LLMRateLimitError, TriageError
from triagelite.llm.client import LLMClient
from triagelite.llm.config import ModelApi
from triagelite.llm.types import (
    EmbeddingRequest,
    EmbeddingResponse,
    ModelRequest,
    ModelResponse,
    ToolCall,
)
from triagelite.settings import Settings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_bedrock_runtime.type_defs import (
        ConverseResponseTypeDef,
        ToolConfigurationTypeDef,
    )

FIRST_SERVER_ERROR_STATUS = 500


def runtime_client(settings: Settings, timeout_seconds: float) -> "BedrockRuntimeClient":
    """bedrock-runtime with botocore retries off: every attempt is recorded, backoff is ours."""
    config = Config(
        retries={"total_max_attempts": 1},
        read_timeout=timeout_seconds,
        connect_timeout=timeout_seconds,
    )
    return boto3.client("bedrock-runtime", region_name=settings.aws_region, config=config)


class _BotoErrorMap:
    """Maps bedrock-runtime exceptions to domain errors by type, never by message."""

    def __init__(self, runtime: "BedrockRuntimeClient") -> None:
        errors = runtime.exceptions
        self.throttled = (errors.ThrottlingException, errors.ServiceQuotaExceededException)
        self.transient = (
            errors.InternalServerException,
            errors.ServiceUnavailableException,
            errors.ModelNotReadyException,
            errors.ModelTimeoutException,
        )

    def to_domain(self, error: Exception) -> TriageError:
        """Throttling, retryable failure or permanent failure."""
        if isinstance(error, self.throttled):
            return LLMRateLimitError(str(error))
        if isinstance(error, (*self.transient, BotoConnectionError, HTTPClientError)):
            return LLMProviderError(str(error), retryable=True)
        return LLMProviderError(str(error), retryable=False)


class AnthropicMessagesClient:
    """`LLMClient` for Claude via `AnthropicBedrock` (Messages API on bedrock-runtime)."""

    def __init__(self, sdk: AnthropicBedrock) -> None:
        self._sdk = sdk

    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        """Build a client using the standard AWS credential chain (SSO locally, a role in Lambda).

        `max_retries=0`: every attempt must produce an `LLMCallRecord`, and availability
        retries belong to Step Functions.
        """
        return cls(AnthropicBedrock(aws_region=settings.aws_region, max_retries=0))

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Send one request; map SDK errors to domain errors by type, never by message."""
        input_schema: dict[str, object] = dict(request.tool.input_schema)
        tool: ToolParam = {
            "name": request.tool.name,
            "description": request.tool.description,
            "input_schema": input_schema,
        }
        user_message: MessageParam = {"role": "user", "content": request.user}
        thinking: ThinkingConfigDisabledParam | anthropic.Omit = (
            {"type": request.thinking} if request.thinking else anthropic.omit
        )
        output_config: OutputConfigParam | anthropic.Omit = (
            {"effort": request.effort} if request.effort else anthropic.omit
        )
        try:
            message = self._sdk.messages.create(
                model=request.model_id,
                max_tokens=request.max_tokens,
                system=request.system,
                messages=[user_message],
                tools=[tool],
                tool_choice={"type": "auto"},
                thinking=thinking,
                output_config=output_config,
                timeout=request.timeout_seconds,
            )
        except anthropic.AnthropicError as error:
            raise to_domain_error(error) from error
        return to_model_response(message)


class ConverseLLMClient:
    """`LLMClient` for non-Claude models via the Bedrock Converse API."""

    def __init__(self, runtime: "BedrockRuntimeClient") -> None:
        self._runtime = runtime
        self._errors = _BotoErrorMap(runtime)

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Send one request with the tool offered on `auto`, as the Messages client does."""
        tool_config: ToolConfigurationTypeDef = {
            "tools": [
                {
                    "toolSpec": {
                        "name": request.tool.name,
                        "description": request.tool.description,
                        "inputSchema": {"json": dict(request.tool.input_schema)},
                    }
                }
            ],
            "toolChoice": {"auto": {}},
        }
        extra: dict[str, Any] = {}
        if request.effort:
            extra["additionalModelRequestFields"] = {"reasoning_effort": request.effort}
        try:
            response = self._runtime.converse(
                modelId=request.model_id,
                system=[{"text": request.system}],
                messages=[{"role": "user", "content": [{"text": request.user}]}],
                inferenceConfig={"maxTokens": request.max_tokens},
                toolConfig=tool_config,
                **extra,
            )
        except (ClientError, BotoCoreError) as error:
            raise self._errors.to_domain(error) from error
        return converse_to_model_response(response)


def converse_to_model_response(response: "ConverseResponseTypeDef") -> ModelResponse:
    """Tool calls from `toolUse` blocks; reasoning and text blocks are dropped."""
    content = response["output"].get("message", {}).get("content", [])
    calls: list[ToolCall] = []
    for block in content:
        if "toolUse" in block:
            tool_input: JsonValue = block["toolUse"]["input"]
            calls.append(ToolCall(name=block["toolUse"]["name"], input=tool_input))
    return ModelResponse(
        stop_reason=response["stopReason"],
        tool_calls=tuple(calls),
        input_tokens=response["usage"]["inputTokens"],
        output_tokens=response["usage"]["outputTokens"],
    )


class BedrockLLMClient:
    """`LLMClient` that sends each request to the API its stage is configured for."""

    def __init__(self, messages: LLMClient, converse: LLMClient) -> None:
        self._clients: dict[ModelApi, LLMClient] = {"messages": messages, "converse": converse}

    @classmethod
    def from_settings(cls, settings: Settings, timeout_seconds: float) -> Self:
        """Both transports with SDK retries off."""
        return cls(
            AnthropicMessagesClient.from_settings(settings),
            ConverseLLMClient(runtime_client(settings, timeout_seconds)),
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Route by `request.api`."""
        return self._clients[request.api].complete(request)


def to_domain_error(error: anthropic.AnthropicError) -> TriageError:
    """Classify an SDK exception as throttling, retryable failure or permanent failure."""
    if isinstance(error, anthropic.RateLimitError):
        return LLMRateLimitError(str(error))
    if isinstance(error, anthropic.APIConnectionError):
        return LLMProviderError(str(error), retryable=True)
    if isinstance(error, anthropic.APIStatusError):
        retryable = error.status_code >= FIRST_SERVER_ERROR_STATUS
        return LLMProviderError(str(error), retryable=retryable)
    return LLMProviderError(str(error), retryable=False)


def to_model_response(message: Message) -> ModelResponse:
    """Keep only what the pipeline uses: stop reason, tool calls and token usage."""
    return ModelResponse(
        stop_reason=message.stop_reason,
        tool_calls=tuple(
            ToolCall.model_validate({"name": block.name, "input": block.input})
            for block in message.content
            if block.type == "tool_use"
        ),
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )


class TitanEmbeddingBody(BaseModel):
    """The fields we use from a Titan embeddings response; the provider may add others."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    embedding: list[float]
    input_text_token_count: int = Field(alias="inputTextTokenCount", ge=0)


class BedrockEmbeddingClient:
    """`EmbeddingClient` for Titan Text Embeddings via boto3 `invoke_model`."""

    def __init__(self, runtime: "BedrockRuntimeClient") -> None:
        self._runtime = runtime
        self._errors = _BotoErrorMap(runtime)

    @classmethod
    def from_settings(cls, settings: Settings, timeout_seconds: float) -> Self:
        """Client with botocore retries off: every attempt is recorded, backoff is ours."""
        return cls(runtime_client(settings, timeout_seconds))

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed one text; map errors by exception type, never by message."""
        body = {
            "inputText": request.text,
            "dimensions": request.dimensions,
            "normalize": request.normalize,
        }
        try:
            response = self._runtime.invoke_model(
                modelId=request.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
        except (ClientError, BotoCoreError) as error:
            raise self._errors.to_domain(error) from error
        parsed = TitanEmbeddingBody.model_validate_json(response["body"].read())
        if len(parsed.embedding) != request.dimensions:
            msg = f"expected {request.dimensions} dimensions, got {len(parsed.embedding)}"
            raise LLMProviderError(msg, retryable=False)
        return EmbeddingResponse(
            vector=tuple(parsed.embedding), input_tokens=parsed.input_text_token_count
        )
