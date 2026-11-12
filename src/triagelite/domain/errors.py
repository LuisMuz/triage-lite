"""Typed exceptions.

Step Functions `Retry`/`Catch` match on the exception *class name* raised by a Lambda,
so renaming a class here is a breaking change for the state machine definition.
"""


class TriageError(Exception):
    """Base class for every error this package raises on purpose."""


class ConfigError(TriageError):
    """Configuration or prompt files are inconsistent (missing price, unknown variable…)."""


class InputValidationError(TriageError):
    """Input data (CSV, event, config) failed validation at a boundary."""


class RequestValidationError(InputValidationError):
    """An API request has a path or query parameter the API does not accept."""


class NotFoundError(TriageError):
    """A stored object or item that should exist does not."""


class LLMOutputValidationError(TriageError):
    """The model answered, but the answer is unusable (truncated, no tool call, bad schema).

    Handled by the validation retry chain: one retry with `errors` appended to the prompt.
    """

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors: list[str] = errors or []


class LLMRateLimitError(TriageError):
    """The provider throttled the call; retried with backoff by Step Functions."""


class LLMProviderError(TriageError):
    """The provider failed (5xx, timeout, 4xx); `retryable` says whether backoff can help."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMTransientError(LLMProviderError):
    """A provider failure backoff can fix (5xx, timeout, connection).

    A class of its own because Step Functions `Retry` matches class names, not attributes.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=True)
