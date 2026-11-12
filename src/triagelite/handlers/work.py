"""The files stages leave for each other under `work/<batch_id>/`."""

from collections.abc import Sequence
from pathlib import PurePosixPath

from triagelite.domain.errors import NotFoundError
from triagelite.domain.models import Incident, IncidentClassification, LLMCallRecord
from triagelite.pipeline.classify import with_missing_as_manual
from triagelite.storage.s3 import S3Store, work_key

NORMALIZED_FILE = "normalized.json"
DEDUPE_FILE = "dedupe.json"
FACTS_FILE = "report_facts.json"
DRAFTS_FILE = "report_drafts.jsonl"
SUMMARY_FILE = "summary.json"
DEDUPE_CALLS = "dedupe"
SUMMARIZE_CALLS = "summarize"
CHUNK_NAME = "{:04d}.jsonl"
CHUNK_FAILED_REASON = "classification failed for this incident's chunk"


def chunks_prefix(batch_id: str) -> str:
    """Prefix shared by a batch's chunks."""
    return work_key(batch_id, "chunks/")


def chunk_key(batch_id: str, index: int) -> str:
    """Key of the incidents in one chunk."""
    return f"{chunks_prefix(batch_id)}{CHUNK_NAME.format(index)}"


def classified_key(batch_id: str, source_chunk: str) -> str:
    """Key of the results for the chunk stored at `source_chunk`."""
    return work_key(batch_id, f"classified/{PurePosixPath(source_chunk).name}")


def calls_key(batch_id: str, name: str) -> str:
    """Key of the model calls one invocation made."""
    return work_key(batch_id, f"calls/{name}.jsonl")


def chunk_calls_name(source_chunk: str) -> str:
    """Name for `calls_key` of the invocation that classified the chunk at `source_chunk`."""
    return f"classify-{PurePosixPath(source_chunk).stem}"


def load_results(
    store: S3Store, batch_id: str, chunk_keys: Sequence[str], incidents: Sequence[Incident]
) -> list[IncidentClassification]:
    """Every incident's result; a chunk that exhausted its retries left no file behind."""
    results: list[IncidentClassification] = []
    for key in chunk_keys:
        try:
            results += store.read_jsonl(classified_key(batch_id, key), IncidentClassification)
        except NotFoundError:
            continue
    return with_missing_as_manual(incidents, results, CHUNK_FAILED_REASON)


def load_calls(store: S3Store, batch_id: str, chunk_keys: Sequence[str]) -> list[LLMCallRecord]:
    """Every call recorded for a batch; an invocation that timed out recorded none."""
    names = [chunk_calls_name(key) for key in chunk_keys] + [DEDUPE_CALLS, SUMMARIZE_CALLS]
    records: list[LLMCallRecord] = []
    for name in names:
        try:
            records += store.read_jsonl(calls_key(batch_id, name), LLMCallRecord)
        except NotFoundError:
            continue
    return records
