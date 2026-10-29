"""`triagelite run data/sample.csv`: the whole local pipeline, with real Bedrock calls."""

import argparse
import hashlib
import logging
import re
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from random import SystemRandom

from triagelite.domain.enums import Stage, TriageStatus
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError, TriageError
from triagelite.domain.models import Incident, IncidentClassification, LLMCallRecord, RunSummary
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.bedrock import BedrockLLMClient
from triagelite.llm.client import LLMClient
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import configure_logging, log_fields
from triagelite.metrics import log_call_record
from triagelite.pipeline.classify import classify_chunk
from triagelite.pipeline.config import LocalRetryConfig
from triagelite.pipeline.normalize import NormalizeResult, chunked, normalize
from triagelite.settings import (
    Settings,
    get_settings,
    load_llm_config,
    load_pipeline_config,
    load_stage_prompt,
    load_taxonomy,
)
from triagelite.storage.local import LocalRunStore

LOGGER = logging.getLogger("triagelite.cli")
DEFAULT_RUNS_DIR = Path("runs")
BATCH_HASH_CHARS = 8
INCIDENTS_FILE = "incidents.jsonl"
CLASSIFICATIONS_FILE = "classifications.jsonl"
ROW_ERRORS_FILE = "row_errors.jsonl"
LLM_CALLS_FILE = "llm_calls.jsonl"
SUMMARY_FILE = "summary.json"
PER_HUNDRED = 100
EXIT_OK = 0
EXIT_FAILED = 1

type Sleep = Callable[[float], None]

_JITTER = SystemRandom()


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the `triagelite` command."""
    args = build_parser().parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        summary, run_dir = run_batch(
            args.csv, args.out, settings, BedrockLLMClient.from_settings(settings)
        )
    except TriageError as error:
        LOGGER.error(
            "run failed", extra=log_fields(error_type=type(error).__name__, error=str(error))
        )
        return EXIT_FAILED
    LOGGER.info(
        "run complete", extra=log_fields(out_dir=str(run_dir), **summary.model_dump(mode="json"))
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Command-line interface: `triagelite run <csv> [--out DIR]`."""
    parser = argparse.ArgumentParser(prog="triagelite", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="classify a CSV of incidents")
    run.add_argument("csv", type=Path, help="CSV with external_id,title,description,...")
    run.add_argument("--out", type=Path, default=None, help="output folder (default runs/<batch>)")
    return parser


def run_batch(
    csv_path: Path,
    out_dir: Path | None,
    settings: Settings,
    client: LLMClient,
    *,
    sleep: Sleep = time.sleep,
) -> tuple[RunSummary, Path]:
    """Normalize and classify one CSV, writing every output under the run folder."""
    content = csv_path.read_text(encoding="utf-8")
    batch_id = batch_id_for(csv_path, content)
    store = LocalRunStore(out_dir or DEFAULT_RUNS_DIR / batch_id)
    taxonomy = load_taxonomy(settings)
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    prompt = load_stage_prompt(settings, Stage.CLASSIFY, pipeline.prompts.classify)

    calls_file = store.call_recorder(LLM_CALLS_FILE)
    records: list[LLMCallRecord] = []

    def record(call: LLMCallRecord, /) -> None:
        records.append(call)
        calls_file(call)
        log_call_record(call)

    llm = StructuredLLM(client, models, prices, recorder=record)

    normalized = normalize(content, pipeline.normalize)
    LOGGER.info(
        "normalized",
        extra=log_fields(
            batch_id=batch_id,
            stage="normalize",
            incidents=len(normalized.incidents),
            row_errors=len(normalized.row_errors),
        ),
    )
    store.write_jsonl(INCIDENTS_FILE, normalized.incidents)
    store.write_jsonl(ROW_ERRORS_FILE, normalized.row_errors)

    results: list[IncidentClassification] = []
    for chunk in chunked(normalized.incidents, pipeline.normalize.chunk_size):
        results += classify_with_backoff(
            llm, prompt, taxonomy, chunk, batch_id=batch_id, retry=pipeline.local_retry, sleep=sleep
        )
    store.write_jsonl(CLASSIFICATIONS_FILE, results)

    summary = summarize(batch_id, normalized, results, records)
    store.write_json(SUMMARY_FILE, summary)
    return summary, store.run_dir


def classify_with_backoff(
    llm: StructuredLLM,
    prompt: PromptFile,
    taxonomy: Taxonomy,
    chunk: Sequence[Incident],
    *,
    batch_id: str,
    retry: LocalRetryConfig,
    sleep: Sleep,
) -> list[IncidentClassification]:
    """Retry a throttled or failing chunk with exponential backoff and full jitter.

    Mirrors the Step Functions policy: retryable errors back off up to `max_attempts`, after
    which the chunk is marked `needs_manual` and the batch continues; a non-retryable
    provider error (bad credentials, bad request) stops the run.
    """
    attempt = 1
    while True:
        try:
            return classify_chunk(llm, prompt, taxonomy, chunk, batch_id=batch_id)
        except (LLMRateLimitError, LLMProviderError) as error:
            if isinstance(error, LLMProviderError) and not error.retryable:
                raise
            if attempt >= retry.max_attempts:
                LOGGER.warning(
                    "chunk failed",
                    extra=log_fields(
                        batch_id=batch_id,
                        stage=Stage.CLASSIFY,
                        attempts=attempt,
                        error_type=type(error).__name__,
                    ),
                )
                reason = f"model unavailable after {attempt} attempts ({type(error).__name__})"
                return [
                    IncidentClassification(
                        incident_id=incident.incident_id,
                        status=TriageStatus.NEEDS_MANUAL,
                        reason=reason,
                    )
                    for incident in chunk
                ]
            ceiling = retry.initial_delay_seconds * retry.backoff_rate ** (attempt - 1)
            sleep(_JITTER.uniform(0, ceiling))
            attempt += 1


def batch_id_for(csv_path: Path, content: str) -> str:
    """Stable ID from the file name and content: re-running the same CSV overwrites its run."""
    stem = re.sub(r"[^a-z0-9]+", "-", csv_path.stem.lower()).strip("-") or "batch"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:BATCH_HASH_CHARS]
    return f"{stem}-{digest}"


def summarize(
    batch_id: str,
    normalized: NormalizeResult,
    results: Sequence[IncidentClassification],
    records: Sequence[LLMCallRecord],
) -> RunSummary:
    """Counts and cost for one run; cost per 100 incidents is the README's headline number."""
    cost = sum(record.cost_usd for record in records)
    classified = sum(result.status is TriageStatus.CLASSIFIED for result in results)
    return RunSummary(
        batch_id=batch_id,
        incidents=len(normalized.incidents),
        row_errors=len(normalized.row_errors),
        classified=classified,
        needs_manual=len(results) - classified,
        llm_calls=len(records),
        cost_usd=cost,
        cost_per_100_incidents_usd=(
            cost / len(normalized.incidents) * PER_HUNDRED if normalized.incidents else 0.0
        ),
        pii_redactions=normalized.pii_redactions,
    )
