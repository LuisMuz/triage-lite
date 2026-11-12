"""The pipeline's steps, shared by the local CLI, the eval harness and the Lambda handlers."""

import hashlib
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePath

from triagelite.domain.enums import ReportSource, Stage, TriageStatus
from triagelite.domain.models import (
    CandidatePair,
    DuplicateCluster,
    Incident,
    IncidentClassification,
    Language,
    LLMCallRecord,
    PairVerdict,
    RunSummary,
    StrictModel,
)
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.client import CallRecorder, EmbeddingClient
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import log_fields
from triagelite.pipeline.aggregates import ReportFacts
from triagelite.pipeline.backoff import AvailabilityError, Sleep, with_backoff
from triagelite.pipeline.classify import classify_chunk
from triagelite.pipeline.config import ChunkRetryConfig, DedupeConfig, ReportConfig
from triagelite.pipeline.dedupe import (
    CandidateSet,
    candidate_pairs,
    judge_chunk,
    report_order,
    star_clusters,
    unjudged,
)
from triagelite.pipeline.embed import EmbeddingMatrix, embed_incidents
from triagelite.pipeline.normalize import NormalizeResult, chunked
from triagelite.pipeline.render import render_report
from triagelite.pipeline.summarize import ReportDraft, summarize_report, template_draft

LOGGER = logging.getLogger("triagelite.pipeline.stages")
REPORT_LANGUAGES: tuple[Language, ...] = ("es", "en")
BATCH_HASH_CHARS = 8
PER_HUNDRED = 100


class DedupeOutcome(StrictModel):
    """What later stages need from dedupe; vectors stay behind because nothing reads them again."""

    verdicts: list[PairVerdict]
    clusters: list[DuplicateCluster]
    pairs_dropped_by_cap: int


@dataclass(frozen=True)
class DedupeResult:
    """Everything the dedupe stage produced for one batch."""

    matrix: EmbeddingMatrix
    order: list[str]
    candidates: CandidateSet
    verdicts: list[PairVerdict]
    clusters: list[DuplicateCluster]

    def outcome(self) -> DedupeOutcome:
        """The part of the result that later stages use."""
        return DedupeOutcome(
            verdicts=self.verdicts,
            clusters=self.clusters,
            pairs_dropped_by_cap=self.candidates.dropped,
        )


def classify_with_backoff(
    llm: StructuredLLM,
    prompt: PromptFile,
    taxonomy: Taxonomy,
    chunk: Sequence[Incident],
    *,
    batch_id: str,
    retry: ChunkRetryConfig,
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
    retry: ChunkRetryConfig,
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
    retry: ChunkRetryConfig,
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
    retry: ChunkRetryConfig,
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


def batch_id_for(source: PurePath, content: str) -> str:
    """Stable ID from the file name and content: re-running the same CSV overwrites its run."""
    stem = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-") or "batch"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:BATCH_HASH_CHARS]
    return f"{stem}-{digest}"


def render_draft(
    draft: ReportDraft,
    facts: ReportFacts,
    *,
    batch_id: str,
    models: ModelsConfig,
    prompt: PromptFile,
    config: ReportConfig,
) -> str:
    """One language's finished report, with the code's numbers in place of its placeholders."""
    return render_report(
        draft.sections,
        facts,
        draft.lang,
        batch_id=batch_id,
        source=draft.source,
        model_id=models.for_stage(Stage.SUMMARIZE).model_id,
        prompt_id=prompt.id,
        percent_decimals=config.percent_decimals,
    )


def summarize(
    batch_id: str,
    normalized: NormalizeResult,
    results: Sequence[IncidentClassification],
    records: Sequence[LLMCallRecord],
    dedupe: DedupeOutcome,
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
        candidate_pairs=len(dedupe.verdicts),
        pairs_dropped_by_cap=dedupe.pairs_dropped_by_cap,
        confirmed_pairs=sum(verdict.is_duplicate for verdict in dedupe.verdicts),
        unjudged_pairs=sum(verdict.judgement is None for verdict in dedupe.verdicts),
        clusters=len(dedupe.clusters),
        duplicate_incidents=sum(len(cluster.member_ids) - 1 for cluster in dedupe.clusters),
        reports_from_template=[d.lang for d in drafts if d.source is ReportSource.TEMPLATE],
    )
