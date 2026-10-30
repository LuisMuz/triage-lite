"""`triagelite run data/sample.csv`: the whole local pipeline, with real Bedrock calls."""

import argparse
import hashlib
import logging
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from triagelite.domain.enums import ReportSource, Stage, TriageStatus
from triagelite.domain.errors import TriageError
from triagelite.domain.models import (
    CandidatePair,
    DuplicateCluster,
    Incident,
    IncidentClassification,
    Language,
    LLMCallRecord,
    PairVerdict,
    RunSummary,
)
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.bedrock import BedrockEmbeddingClient, BedrockLLMClient
from triagelite.llm.client import CallRecorder, EmbeddingClient, LLMClient
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import configure_logging, log_fields
from triagelite.metrics import log_call_record
from triagelite.pipeline.aggregates import ReportFacts, compute_facts
from triagelite.pipeline.backoff import AvailabilityError, Sleep, with_backoff
from triagelite.pipeline.classify import classify_chunk
from triagelite.pipeline.config import DedupeConfig, LocalRetryConfig, ReportConfig
from triagelite.pipeline.dedupe import (
    CandidateSet,
    candidate_pairs,
    judge_chunk,
    report_order,
    star_clusters,
    unjudged,
)
from triagelite.pipeline.embed import EmbeddingMatrix, embed_incidents
from triagelite.pipeline.normalize import NormalizeResult, chunked, normalize
from triagelite.pipeline.render import render_report
from triagelite.pipeline.summarize import ReportDraft, summarize_report, template_draft
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
PAIRS_FILE = "pairs.jsonl"
CLUSTERS_FILE = "clusters.jsonl"
FACTS_FILE = "report_facts.json"
DRAFTS_FILE = "report_drafts.jsonl"
REPORT_FILE = "report.{lang}.md"
REPORT_LANGUAGES: tuple[Language, ...] = ("es", "en")
SUMMARY_FILE = "summary.json"
PER_HUNDRED = 100
EXIT_OK = 0
EXIT_FAILED = 1


@dataclass(frozen=True)
class DedupeResult:
    """Everything the dedupe stage produced for one batch."""

    matrix: EmbeddingMatrix
    order: list[str]
    candidates: CandidateSet
    verdicts: list[PairVerdict]
    clusters: list[DuplicateCluster]


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the `triagelite` command."""
    args = build_parser().parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        models, _ = load_llm_config(settings)
        embedder = BedrockEmbeddingClient.from_settings(settings, models.client.timeout_seconds)
        summary, run_dir = run_batch(
            args.csv, args.out, settings, BedrockLLMClient.from_settings(settings), embedder
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
            llm, prompt, taxonomy, chunk, batch_id=batch_id, retry=pipeline.local_retry, sleep=sleep
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
        retry=pipeline.local_retry,
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
            retry=pipeline.local_retry,
            sleep=sleep,
        )
        for lang in REPORT_LANGUAGES
    ]
    store.write_jsonl(DRAFTS_FILE, drafts)
    for draft in drafts:
        store.write_text(
            REPORT_FILE.format(lang=draft.lang),
            render_report(
                draft.sections,
                facts,
                draft.lang,
                batch_id=batch_id,
                source=draft.source,
                model_id=models.for_stage(Stage.SUMMARIZE).model_id,
                prompt_id=summary_prompt.id,
                percent_decimals=pipeline.report.percent_decimals,
            ),
        )

    summary = summarize(batch_id, normalized, results, records, dedupe, drafts)
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
    """Classify a chunk, backing off on availability errors; exhausted chunks need a human."""

    def exhausted(attempts: int, error: AvailabilityError) -> list[IncidentClassification]:
        reason = _unavailable(Stage.CLASSIFY, batch_id, attempts, error)
        return [
            IncidentClassification(
                incident_id=incident.incident_id, status=TriageStatus.NEEDS_MANUAL, reason=reason
            )
            for incident in chunk
        ]

    return with_backoff(
        lambda: classify_chunk(llm, prompt, taxonomy, chunk, batch_id=batch_id),
        retry=retry,
        sleep=sleep,
        exhausted=exhausted,
    )


def judge_with_backoff(
    llm: StructuredLLM,
    prompt: PromptFile,
    pairs: Sequence[CandidatePair],
    incidents: Mapping[str, Incident],
    *,
    batch_id: str,
    retry: LocalRetryConfig,
    sleep: Sleep,
) -> list[PairVerdict]:
    """Judge a chunk of pairs, backing off on availability errors; exhausted pairs stay apart."""

    def exhausted(attempts: int, error: AvailabilityError) -> list[PairVerdict]:
        return unjudged(pairs, _unavailable(Stage.DEDUPE_JUDGE, batch_id, attempts, error))

    return with_backoff(
        lambda: judge_chunk(llm, prompt, pairs, incidents, batch_id=batch_id),
        retry=retry,
        sleep=sleep,
        exhausted=exhausted,
    )


def summarize_with_backoff(
    llm: StructuredLLM,
    prompt: PromptFile,
    facts: ReportFacts,
    lang: Language,
    config: ReportConfig,
    *,
    batch_id: str,
    retry: LocalRetryConfig,
    sleep: Sleep,
) -> ReportDraft:
    """Write one language's report with backoff; when retries run out, use the template."""

    def exhausted(attempts: int, error: AvailabilityError) -> ReportDraft:
        return template_draft(
            facts, lang, [_unavailable(Stage.SUMMARIZE, batch_id, attempts, error)]
        )

    return with_backoff(
        lambda: summarize_report(llm, prompt, facts, lang, config, batch_id=batch_id),
        retry=retry,
        sleep=sleep,
        exhausted=exhausted,
    )


def _unavailable(stage: Stage, batch_id: str, attempts: int, error: AvailabilityError) -> str:
    LOGGER.warning(
        "chunk failed",
        extra=log_fields(
            batch_id=batch_id, stage=stage, attempts=attempts, error_type=type(error).__name__
        ),
    )
    return f"model unavailable after {attempts} attempts ({type(error).__name__})"


def dedupe_batch(
    llm: StructuredLLM,
    prompt: PromptFile,
    embedder: EmbeddingClient,
    incidents: Sequence[Incident],
    *,
    models: ModelsConfig,
    prices: PriceTable,
    config: DedupeConfig,
    retry: LocalRetryConfig,
    recorder: CallRecorder,
    batch_id: str,
    sleep: Sleep,
) -> DedupeResult:
    """Embed, pick candidate pairs, judge them in chunks, and build star clusters."""
    matrix = embed_incidents(
        embedder, incidents, models.embedding, prices, recorder, batch_id=batch_id
    )
    order = report_order(incidents)
    candidates = candidate_pairs(matrix, order, config)
    if candidates.dropped:
        LOGGER.warning(
            "pair cap hit",
            extra=log_fields(
                batch_id=batch_id,
                stage=Stage.DEDUPE_JUDGE,
                max_pairs=config.max_pairs,
                dropped=candidates.dropped,
            ),
        )
    by_id = {incident.incident_id: incident for incident in incidents}
    verdicts: list[PairVerdict] = []
    for chunk in chunked(candidates.pairs, config.judge_chunk_size):
        verdicts += judge_with_backoff(
            llm, prompt, chunk, by_id, batch_id=batch_id, retry=retry, sleep=sleep
        )
    confirmed = [verdict.pair for verdict in verdicts if verdict.is_duplicate]
    return DedupeResult(
        matrix=matrix,
        order=order,
        candidates=candidates,
        verdicts=verdicts,
        clusters=star_clusters(order, confirmed, config.max_cluster_size),
    )


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
    dedupe: DedupeResult,
    drafts: Sequence[ReportDraft],
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
        candidate_pairs=len(dedupe.candidates.pairs),
        pairs_dropped_by_cap=dedupe.candidates.dropped,
        confirmed_pairs=sum(verdict.is_duplicate for verdict in dedupe.verdicts),
        unjudged_pairs=sum(verdict.judgement is None for verdict in dedupe.verdicts),
        clusters=len(dedupe.clusters),
        duplicate_incidents=sum(len(cluster.member_ids) - 1 for cluster in dedupe.clusters),
        reports_from_template=[d.lang for d in drafts if d.source is ReportSource.TEMPLATE],
    )
