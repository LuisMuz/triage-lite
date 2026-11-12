import pytest

from triagelite.domain.errors import (
    InputValidationError,
    LLMOutputValidationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTransientError,
    TriageError,
)


@pytest.mark.parametrize(
    "error",
    [
        InputValidationError("bad row"),
        LLMOutputValidationError("truncated"),
        LLMRateLimitError("429"),
        LLMProviderError("503", retryable=True),
    ],
)
def test_every_error_is_a_triage_error(error: TriageError) -> None:
    assert isinstance(error, TriageError)


def test_class_names_match_step_functions_error_names() -> None:
    assert LLMRateLimitError.__name__ == "LLMRateLimitError"
    assert LLMProviderError.__name__ == "LLMProviderError"


def test_output_validation_error_keeps_errors_for_the_retry_prompt() -> None:
    error = LLMOutputValidationError("schema", errors=["items.0.severity: invalid"])

    assert error.errors == ["items.0.severity: invalid"]
    assert LLMOutputValidationError("truncated").errors == []


@pytest.mark.parametrize("retryable", [True, False])
def test_provider_error_records_retryability(retryable: bool) -> None:
    assert LLMProviderError("boom", retryable=retryable).retryable is retryable


def test_transient_error_is_a_retryable_provider_error_with_its_own_name() -> None:
    error = LLMTransientError("503")

    assert isinstance(error, LLMProviderError)
    assert error.retryable is True
    assert type(error).__name__ == "LLMTransientError"
