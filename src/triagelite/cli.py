"""`triagelite run data/sample.csv`: the whole local pipeline, with real Bedrock calls."""

import argparse
import logging
import time
from collections.abc import Sequence
from pathlib import Path

from triagelite.domain.enums import Stage
from triagelite.domain.errors import TriageError
from triagelite.domain.models import IncidentClassification, LLMCallRecord, RunSummary
from triagelite.llm.bedrock import BedrockEmbeddingClient, BedrockLLMClient
from triagelite.llm.client import EmbeddingClient, LLMClient
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import configure_logging, log_fields
from triagelite.metrics import log_call_record
from triagelite.pipeline.aggregates import compute_facts
from triagelite.pipeline.backoff import Sleep
from triagelite.pipeline.normalize import chunked, normalize
from triagelite.pipeline.stages import (
    REPORT_LANGUAGES,
    batch_id_for,
    classify_with_backoff,
    dedupe_batch,
    render_draft,
    summarize,
    summarize_with_backoff,
)
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
INCIDENTS_FILE = "incidents.jsonl"
CLASSIFICATIONS_FILE = "classifications.jsonl"
ROW_ERRORS_FILE = "row_errors.jsonl"
LLM_CALLS_FILE = "llm_calls.jsonl"
PAIRS_FILE = "pairs.jsonl"
CLUSTERS_FILE = "clusters.jsonl"
FACTS_FILE = "report_facts.json"
DRAFTS_FILE = "report_drafts.jsonl"
REPORT_FILE = "report.{lang}.md"
SUMMARY_FILE = "summary.json"
EXIT_OK = 0
EXIT_FAILED = 1


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the `triagelite` command."""
    args = build_parser().parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        models, _ = load_llm_config(settings)
        timeout = models.client.timeout_seconds
        embedder = BedrockEmbeddingClient.from_settings(settings, timeout)
        llm = BedrockLLMClient.from_settings(settings, timeout)
        summary, run_dir = run_batch(args.csv, args.out, settings, llm, embedder)
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
    run = commands.add_parser("run", help="triage a CSV of incidents into ES/EN reports")
    run.add_argument("csv", type=Path, help="CSV with external_id,title,description,...")
    run.add_argument("--out", type=Path, default=None, help="output folder (default runs/<batch>)")
    return parser


def run_batch(
    csv_path: Path,
    out_dir: Path | None,
    settings: Settings,
    client: LLMClient,
    embedder: EmbeddingClient,
    *,
    sleep: Sleep = time.sleep,
) -> tuple[RunSummary, Path]:
    """Normalize, classify, deduplicate and summarize one CSV; every output goes to its folder."""
    content = csv_path.read_text(encoding="utf-8")
    batch_id = batch_id_for(csv_path, content)
    store = LocalRunStore(out_dir or DEFAULT_RUNS_DIR / batch_id)
    taxonomy = load_taxonomy(settings)
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    prompt = load_stage_prompt(settings, Stage.CLASSIFY, pipeline.prompts.classify)
    judge_prompt = load_stage_prompt(settings, Stage.DEDUPE_JUDGE, pipeline.prompts.dedupe_judge)
    summary_prompt = load_stage_prompt(settings, Stage.SUMMARIZE, pipeline.prompts.summarize)

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
            llm, prompt, taxonomy, chunk, batch_id=batch_id, retry=pipeline.chunk_retry, sleep=sleep
        )
    store.write_jsonl(CLASSIFICATIONS_FILE, results)

    dedupe = dedupe_batch(
        llm,
        judge_prompt,
        embedder,
        normalized.incidents,
        models=models,
        prices=prices,
        config=pipeline.dedupe,
        retry=pipeline.chunk_retry,
        recorder=record,
        batch_id=batch_id,
        sleep=sleep,
    )
    store.write_vectors(dedupe.matrix)
    store.write_jsonl(PAIRS_FILE, dedupe.verdicts)
    store.write_jsonl(CLUSTERS_FILE, dedupe.clusters)

    facts = compute_facts(
        normalized.incidents,
        results,
        dedupe.clusters,
        len(normalized.row_errors),
        pipeline.report,
    )
    store.write_json(FACTS_FILE, facts)
    drafts = [
        summarize_with_backoff(
            llm,
            summary_prompt,
            facts,
            lang,
            pipeline.report,
            batch_id=batch_id,
            retry=pipeline.chunk_retry,
            sleep=sleep,
        )
        for lang in REPORT_LANGUAGES
    ]
    store.write_jsonl(DRAFTS_FILE, drafts)
    for draft in drafts:
        store.write_text(
            REPORT_FILE.format(lang=draft.lang),
            render_draft(
                draft,
                facts,
                batch_id=batch_id,
                models=models,
                prompt=summary_prompt,
                config=pipeline.report,
            ),
        )

    summary = summarize(batch_id, normalized, results, records, dedupe.outcome(), drafts)
    store.write_json(SUMMARY_FILE, summary)
    return summary, store.run_dir
