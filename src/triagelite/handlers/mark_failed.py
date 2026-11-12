"""When the state machine gives up: mark the batch failed, in both copies of its status."""

import logging
from collections.abc import Mapping
from datetime import UTC, datetime

from triagelite.handlers.events import FailedEvent, parse_event
from triagelite.handlers.runtime import batch_table
from triagelite.logs import log_fields
from triagelite.storage.dynamo import BatchTable

LOGGER = logging.getLogger("triagelite.handlers.mark_failed")
STAGE = "mark_failed"


def failure_reason(event: FailedEvent) -> str:
    """The reason stored on the batch: where it stopped and the error's class name."""
    return f"{event.failed_state} failed with {event.error}"


def run(event: FailedEvent, table: BatchTable, now: datetime) -> dict[str, str]:
    """Mark the batch failed.

    Raises:
        NotFoundError: the batch was never started.
    """
    reason = failure_reason(event)
    table.fail_batch(event.batch_id, reason, now)
    LOGGER.warning(
        "batch failed",
        extra=log_fields(batch_id=event.batch_id, stage=STAGE, reason=reason),
    )
    return {"batch_id": event.batch_id, "reason": reason}


def handler(event: Mapping[str, object], _context: object) -> dict[str, str]:
    """Lambda entry point."""
    return run(parse_event(FailedEvent, event), batch_table(), datetime.now(UTC))
