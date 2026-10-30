"""Scripted stand-in for Claude, so tests and dry runs never touch the network."""

import hashlib
from collections.abc import Callable, Iterable

import numpy as np
from pydantic import JsonValue

from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.llm.types import (
    EmbeddingRequest,
    EmbeddingResponse,
    ModelRequest,
    ModelResponse,
    ToolCall,
)

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


class FakeEmbeddingClient:
    """`EmbeddingClient` with deterministic vectors: a seeded random unit vector per text.

    `fixed` pins chosen texts to given vectors, so a test can control which pairs are close.
    """

    def __init__(
        self,
        fixed: dict[str, tuple[float, ...]] | None = None,
        failures: Iterable[LLMRateLimitError | LLMProviderError] = (),
    ) -> None:
        self._fixed = fixed or {}
        self._failures = list(failures)
        self.requests: list[EmbeddingRequest] = []

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Raise the next scripted failure, else return the pinned or seeded vector."""
        self.requests.append(request)
        if self._failures:
            raise self._failures.pop(0)
        vector = self._fixed.get(request.text) or _seeded_unit_vector(
            request.text, request.dimensions
        )
        return EmbeddingResponse(vector=vector, input_tokens=len(request.text.split()))


def _seeded_unit_vector(text: str, dimensions: int) -> tuple[float, ...]:
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
    raw = np.random.default_rng(seed).normal(size=dimensions)
    return tuple(float(x) for x in raw / np.linalg.norm(raw))
