import logging

from triagelite.domain.models import LLMCallRecord

CALL_LOGGER = logging.getLogger("triagelite.llm_calls")


def log_call_record(record: LLMCallRecord) -> None:
    """Emit one LLM call record as a single JSON log line (the default `CallRecorder`)."""
    CALL_LOGGER.info(record.model_dump_json())
