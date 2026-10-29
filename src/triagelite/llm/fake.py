"""Scripted stand-in for Claude, so tests and dry runs never touch the network."""

from collections.abc import Callable, Iterable

from pydantic import JsonValue

from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.llm.types import ModelRequest, ModelResponse, ToolCall

type Responder = Callable[[ModelRequest], ModelResponse]
type ScriptStep = ModelResponse | Responder | LLMRateLimitError | LLMProviderError

DEFAULT_INPUT_TOKENS = 1_000
DEFAULT_OUTPUT_TOKENS = 200


class FakeLLMClient:
    """`LLMClient` that replays a script: each call returns, raises or computes the next step."""

    def __init__(self, script: Iterable[ScriptStep]) -> None:
        self._script = list(script)
        self.requests: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Record the request, then return or raise the next scripted step."""
        self.requests.append(request)
        if not self._script:
            msg = f"FakeLLMClient script exhausted after {len(self.requests) - 1} calls"
            raise LookupError(msg)
        step = self._script.pop(0)
        if isinstance(step, LLMRateLimitError | LLMProviderError):
            raise step
        if isinstance(step, ModelResponse):
            return step
        return step(request)


def tool_response(tool_name: str, payload: JsonValue) -> ModelResponse:
    """A well-formed answer: one call to `tool_name` with `payload` as its input."""
    return ModelResponse(
        stop_reason="tool_use",
        tool_calls=(ToolCall(name=tool_name, input=payload),),
        input_tokens=DEFAULT_INPUT_TOKENS,
        output_tokens=DEFAULT_OUTPUT_TOKENS,
    )


def truncated(tool_name: str, payload: JsonValue) -> ModelResponse:
    """An answer cut off by `max_tokens`: the partial tool call must not be trusted."""
    return tool_response(tool_name, payload).model_copy(update={"stop_reason": "max_tokens"})


def text_only() -> ModelResponse:
    """The model replied in prose and never called the tool."""
    return ModelResponse(
        stop_reason="end_turn",
        input_tokens=DEFAULT_INPUT_TOKENS,
        output_tokens=DEFAULT_OUTPUT_TOKENS,
    )
