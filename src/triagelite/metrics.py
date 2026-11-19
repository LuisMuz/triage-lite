"""Structured call logs, and CloudWatch metrics written as Embedded Metric Format (EMF) lines."""

import logging
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Literal

from triagelite.domain.enums import CallStatus
from triagelite.domain.models import LLMCallRecord, RunSummary
from triagelite.logs import log_fields

CALL_LOGGER = logging.getLogger("triagelite.llm_calls")
METRICS_LOGGER = logging.getLogger("triagelite.metrics")
METRICS_LOGGER.setLevel(logging.INFO)
METRICS_MESSAGE = "metrics"

type Unit = Literal["Count", "Milliseconds", "None"]


class Metric(StrEnum):
    """Every metric TriageLite publishes; all without dimensions, so each name is one metric."""

    INPUT_TOKENS = "InputTokens"
    OUTPUT_TOKENS = "OutputTokens"
    COST_USD = "CostUSD"
    LATENCY_MS = "LatencyMs"
    VALIDATION_ERRORS = "ValidationErrors"
    NEEDS_MANUAL = "NeedsManual"
    PII_REDACTIONS = "PIIRedactions"


UNITS: Mapping[Metric, Unit] = {
    Metric.INPUT_TOKENS: "Count",
    Metric.OUTPUT_TOKENS: "Count",
    Metric.COST_USD: "None",
    Metric.LATENCY_MS: "Milliseconds",
    Metric.VALIDATION_ERRORS: "Count",
    Metric.NEEDS_MANUAL: "Count",
    Metric.PII_REDACTIONS: "Count",
}


def log_call_record(record: LLMCallRecord) -> None:
    """Emit one LLM call record as structured log fields (the default `CallRecorder`)."""
    CALL_LOGGER.info("llm_call", extra=log_fields(**record.model_dump(mode="json")))


def call_metrics(record: LLMCallRecord) -> dict[Metric, float]:
    """Usage of one model call attempt; a failed attempt still counts its tokens and time."""
    return {
        Metric.INPUT_TOKENS: record.input_tokens,
        Metric.OUTPUT_TOKENS: record.output_tokens,
        Metric.COST_USD: record.cost_usd,
        Metric.LATENCY_MS: record.latency_ms,
        Metric.VALIDATION_ERRORS: int(record.status is CallStatus.VALIDATION_ERROR),
    }


def batch_metrics(summary: RunSummary) -> dict[Metric, float]:
    """Outcomes of one finished batch."""
    return {
        Metric.NEEDS_MANUAL: summary.needs_manual,
        Metric.PII_REDACTIONS: sum(summary.pii_redactions.values()),
    }


def emf_fields(
    namespace: str, values: Mapping[Metric, float], timestamp: datetime
) -> dict[str, object]:
    """The `_aws` directive and metric values CloudWatch Logs turns into metrics."""
    return {
        "_aws": {
            "Timestamp": round(timestamp.timestamp() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": namespace,
                    "Dimensions": [[]],
                    "Metrics": [{"Name": metric.value, "Unit": UNITS[metric]} for metric in values],
                }
            ],
        },
        **{metric.value: value for metric, value in values.items()},
    }


def emit_metrics(
    namespace: str,
    values: Mapping[Metric, float],
    timestamp: datetime,
    **properties: object,
) -> None:
    """Write one EMF line; `properties` stay searchable in Logs Insights but are not dimensions."""
    METRICS_LOGGER.info(
        METRICS_MESSAGE,
        extra=log_fields(**properties, **emf_fields(namespace, values, timestamp)),
    )
