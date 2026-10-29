import json
import logging
import sys

import pytest

from triagelite.domain.enums import CallStatus, Stage
from triagelite.domain.models import LLMCallRecord
from triagelite.logs import JsonFormatter, configure_logging, log_fields
from triagelite.metrics import CALL_LOGGER, log_call_record


def format_record(message: str, **extra: object) -> dict[str, object]:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, message, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    parsed: dict[str, object] = json.loads(JsonFormatter().format(record))
    return parsed


def test_fields_are_merged_into_the_top_level() -> None:
    line = format_record("normalized", **log_fields(batch_id="b1", stage="normalize"))

    assert line["message"] == "normalized"
    assert line["batch_id"] == "b1"
    assert line["level"] == "INFO"


def test_exceptions_are_included() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "x", None, None)
        record.exc_info = sys.exc_info()

    assert "ValueError: boom" in json.loads(JsonFormatter().format(record))["exception"]


def test_configure_logging_installs_the_json_formatter() -> None:
    configure_logging("WARNING")

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert isinstance(root.handlers[0].formatter, JsonFormatter)


def test_call_records_are_logged_as_fields(caplog: pytest.LogCaptureFixture) -> None:
    record = LLMCallRecord(
        call_id="c1",
        stage=Stage.CLASSIFY,
        model_id="m",
        prompt_version="classify/v1",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
        latency_ms=1,
        stop_reason="tool_use",
        attempt=1,
        status=CallStatus.OK,
        batch_id="b1",
    )

    with caplog.at_level(logging.INFO, logger=CALL_LOGGER.name):
        log_call_record(record)

    fields = vars(caplog.records[0])["fields"]
    assert fields["call_id"] == "c1"
    assert fields["batch_id"] == "b1"
