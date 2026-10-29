import logging

from triagelite.domain.models import LLMCallRecord
from triagelite.logs import log_fields

CALL_LOGGER = logging.getLogger("triagelite.llm_calls")


def log_call_record(record: LLMCallRecord) -> None:
    """Emit one LLM call record as structured log fields (the default `CallRecorder`)."""
    CALL_LOGGER.info("llm_call", extra=log_fields(**record.model_dump(mode="json")))
