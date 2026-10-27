from typing import Protocol

from triagelite.domain.models import LLMCallRecord
from triagelite.llm.types import ModelRequest, ModelResponse


class LLMClient(Protocol):
    """Transport for one raw model call (TL-15); no retries, no validation."""

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Send `request`.

        Raises:
            LLMRateLimitError: the provider throttled the call.
            LLMProviderError: the provider failed; `retryable` says whether backoff can help.
        """
        ...


class CallRecorder(Protocol):
    """Receives one `LLMCallRecord` per attempt, including failed attempts."""

    def __call__(self, record: LLMCallRecord, /) -> None:
        """Store or emit `record`."""
        ...
