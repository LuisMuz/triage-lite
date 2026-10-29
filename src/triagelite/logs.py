import json
import logging
import sys
from collections.abc import Mapping
from datetime import UTC, datetime

FIELDS_ATTR = "fields"


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, logger, message and structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        """Render `record`, merging any `extra={"fields": {...}}` into the top level."""
        payload: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, FIELDS_ATTR, None)
        if isinstance(fields, Mapping):
            payload.update(fields)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Send JSON logs to stderr at `level`, replacing any existing root handlers."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)


def log_fields(**fields: object) -> dict[str, Mapping[str, object]]:
    """Build `extra` for structured fields, e.g. `log.info("msg", extra=log_fields(a=1))`."""
    return {FIELDS_ATTR: fields}
