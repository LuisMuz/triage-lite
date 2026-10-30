"""Exponential backoff with full jitter for local runs, mirroring the Step Functions Retry."""

from collections.abc import Callable
from random import SystemRandom

from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.pipeline.config import LocalRetryConfig

type Sleep = Callable[[float], None]
type AvailabilityError = LLMRateLimitError | LLMProviderError

_JITTER = SystemRandom()


def with_backoff[T](
    operation: Callable[[], T],
    *,
    retry: LocalRetryConfig,
    sleep: Sleep,
    exhausted: Callable[[int, AvailabilityError], T],
) -> T:
    """Run `operation`, retrying throttling and retryable provider errors.

    After `max_attempts` the result of `exhausted(attempts, last_error)` is returned, so the
    batch continues; a non-retryable provider error propagates and stops the run.
    """
    attempt = 1
    while True:
        try:
            return operation()
        except (LLMRateLimitError, LLMProviderError) as error:
            if isinstance(error, LLMProviderError) and not error.retryable:
                raise
            if attempt >= retry.max_attempts:
                return exhausted(attempt, error)
            ceiling = retry.initial_delay_seconds * retry.backoff_rate ** (attempt - 1)
            sleep(_JITTER.uniform(0, ceiling))
            attempt += 1
