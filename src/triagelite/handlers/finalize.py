"""Stage 5: publish the batch to DynamoDB, in one place so no stage overwrites another's links."""

import logging
from collections.abc import Mapping
from datetime import UTC, datetime

from triagelite.handlers.events import BatchEvent, StageResult, parse_event
from triagelite.handlers.runtime import batch_table, data_store, lambda_settings
from triagelite.handlers.work import (
    DEDUPE_FILE,
    DRAFTS_FILE,
    NORMALIZED_FILE,
    SUMMARY_FILE,
    load_calls,
    load_results,
)
from triagelite.logs import log_fields
from triagelite.metrics import batch_metrics, emit_metrics
from triagelite.pipeline.classify import incident_records
from triagelite.pipeline.normalize import NormalizeResult
from triagelite.pipeline.stages import REPORT_LANGUAGES, DedupeOutcome, summarize
from triagelite.pipeline.summarize import ReportDraft
from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store, report_key, work_key

LOGGER = logging.getLogger("triagelite.handlers.finalize")
STAGE = "finalize"


def run(
    event: BatchEvent,
    store: S3Store,
    table: BatchTable,
    now: datetime,
    metrics_namespace: str,
) -> StageResult:
    """Write the incidents, clusters and totals, mark the batch done and publish its outcomes."""
    batch_id = event.batch_id
    normalized = store.read_json(work_key(batch_id, NORMALIZED_FILE), NormalizeResult)
    dedupe = store.read_json(work_key(batch_id, DEDUPE_FILE), DedupeOutcome)
    drafts = store.read_jsonl(work_key(batch_id, DRAFTS_FILE), ReportDraft)
    results = load_results(store, batch_id, event.chunk_keys, normalized.incidents)
    records = load_calls(store, batch_id, event.chunk_keys)
    table.put_incidents(batch_id, incident_records(normalized.incidents, results))
    table.replace_clusters(batch_id, dedupe.clusters)
    summary = summarize(batch_id, normalized, results, records, dedupe, drafts)
    key = work_key(batch_id, SUMMARY_FILE)
    store.write_json(key, summary)
    report_keys = {lang: report_key(batch_id, lang) for lang in REPORT_LANGUAGES}
    table.finish_batch(batch_id, summary, report_keys, now)
    LOGGER.info("batch done", extra=log_fields(stage=STAGE, **summary.model_dump(mode="json")))
    emit_metrics(metrics_namespace, batch_metrics(summary), now, batch_id=batch_id, stage=STAGE)
    return StageResult(batch_id=batch_id, keys=[key, *report_keys.values()])


def handler(event: Mapping[str, object], _context: object) -> dict[str, object]:
    """Lambda entry point."""
    return run(
        parse_event(BatchEvent, event),
        data_store(),
        batch_table(),
        datetime.now(UTC),
        lambda_settings().metrics_namespace,
    ).model_dump(mode="json")
