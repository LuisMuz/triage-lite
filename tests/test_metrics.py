import json
import logging
from datetime import UTC, datetime

import pytest

from triagelite.domain.enums import CallStatus, PiiKind, Stage
from triagelite.domain.models import LLMCallRecord, RunSummary
from triagelite.logs import configure_logging
from triagelite.metrics import (
    UNITS,
    Metric,
    batch_metrics,
    call_metrics,
    emf_fields,
    emit_metrics,
)

NAMESPACE = "TriageLiteTest"
WHEN = datetime(2026, 11, 19, 10, 30, 15, 250000, tzinfo=UTC)


def call(status: CallStatus = CallStatus.OK) -> LLMCallRecord:
    return LLMCallRecord(
        call_id="c1",
        stage=Stage.CLASSIFY,
        model_id="m",
        prompt_version="classify/v1",
        input_tokens=1200,
        output_tokens=300,
        cost_usd=0.0027,
        latency_ms=1840,
        stop_reason="tool_use" if status is CallStatus.OK else None,
        attempt=1,
        status=status,
        error_type=None if status is CallStatus.OK else "LLMOutputValidationError",
        batch_id="b1",
    )


def summary(needs_manual: int, redactions: dict[PiiKind, int]) -> RunSummary:
    return RunSummary(
        batch_id="b1",
        incidents=20,
        row_errors=0,
        classified=20 - needs_manual,
        needs_manual=needs_manual,
        llm_calls=24,
        cost_usd=0.05,
        cost_per_100_incidents_usd=0.25,
        pii_redactions=redactions,
        candidate_pairs=11,
        pairs_dropped_by_cap=0,
        confirmed_pairs=3,
        unjudged_pairs=0,
        clusters=17,
        duplicate_incidents=3,
        reports_from_template=[],
    )


def test_a_call_publishes_its_usage() -> None:
    assert call_metrics(call()) == {
        Metric.INPUT_TOKENS: 1200,
        Metric.OUTPUT_TOKENS: 300,
        Metric.COST_USD: 0.0027,
        Metric.LATENCY_MS: 1840,
        Metric.VALIDATION_ERRORS: 0,
    }


def test_a_call_the_model_answered_badly_counts_as_a_validation_error() -> None:
    assert call_metrics(call(CallStatus.VALIDATION_ERROR))[Metric.VALIDATION_ERRORS] == 1


def test_a_throttled_call_is_not_a_validation_error() -> None:
    assert call_metrics(call(CallStatus.RATE_LIMITED))[Metric.VALIDATION_ERRORS] == 0


def test_a_batch_publishes_its_manual_incidents_and_all_redactions() -> None:
    redactions = {PiiKind.EMAIL: 2, PiiKind.PHONE: 1, PiiKind.CREDENTIAL: 0}

    assert batch_metrics(summary(4, redactions)) == {
        Metric.NEEDS_MANUAL: 4,
        Metric.PII_REDACTIONS: 3,
    }


def test_every_metric_has_a_unit() -> None:
    assert set(UNITS) == set(Metric)


def test_the_emf_directive_names_each_value_without_dimensions() -> None:
    fields = emf_fields(NAMESPACE, call_metrics(call()), WHEN)

    assert fields["_aws"] == {
        "Timestamp": 1795084215250,
        "CloudWatchMetrics": [
            {
                "Namespace": NAMESPACE,
                "Dimensions": [[]],
                "Metrics": [
                    {"Name": "InputTokens", "Unit": "Count"},
                    {"Name": "OutputTokens", "Unit": "Count"},
                    {"Name": "CostUSD", "Unit": "None"},
                    {"Name": "LatencyMs", "Unit": "Milliseconds"},
                    {"Name": "ValidationErrors", "Unit": "Count"},
                ],
            }
        ],
    }
    assert fields["CostUSD"] == 0.0027


def test_metrics_are_one_json_line_even_when_info_logs_are_off(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("WARNING")
    logging.getLogger("triagelite.handlers").info("hidden")

    emit_metrics(NAMESPACE, call_metrics(call()), WHEN, batch_id="b1", stage=Stage.CLASSIFY)

    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 1
    line = json.loads(lines[0])
    assert line["message"] == "metrics"
    assert (line["batch_id"], line["stage"], line["InputTokens"]) == ("b1", "classify", 1200)
    for metric in line["_aws"]["CloudWatchMetrics"][0]["Metrics"]:
        assert isinstance(line[metric["Name"]], int | float)
