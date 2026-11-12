"""`python -m evals.dedupe`: dedupe quality on a split, threshold only vs. threshold + judge."""

import argparse
import hashlib
import sys
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import NonNegativeInt

from evals.dataset import DATASETS_DIR, LABELS_FILE, EvalLabel, Split
from evals.harness import (
    CACHE_DIR,
    RESULTS_DIR,
    EvalError,
    load_split,
    model_slug,
    parse_prompt_id,
)
from evals.metrics import (
    PER_HUNDRED,
    CalibrationBin,
    DedupeMetrics,
    calibration_table,
    dedupe_metrics,
    first_try_rate,
)
from evals.similarity import CachingEmbeddingClient, PairKind, pair_kind
from triagelite.domain.enums import Stage
from triagelite.domain.models import LLMCallRecord, NonEmptyStr, PairVerdict, StrictModel
from triagelite.llm.bedrock import BedrockEmbeddingClient, BedrockLLMClient
from triagelite.llm.client import EmbeddingClient, LLMClient
from triagelite.llm.structured import StructuredLLM
from triagelite.llm.types import ModelRequest, ModelResponse
from triagelite.pipeline.backoff import Sleep
from triagelite.pipeline.config import DedupeConfig
from triagelite.pipeline.dedupe import star_clusters
from triagelite.pipeline.normalize import normalize_rows
from triagelite.pipeline.stages import dedupe_batch
from triagelite.settings import (
    Settings,
    get_settings,
    load_llm_config,
    load_pipeline_config,
    load_stage_prompt,
    load_taxonomy,
)


class Arm(StrEnum):
    """The two ablation arms: every candidate merges, or only judge-confirmed ones."""

    THRESHOLD_ONLY = "threshold_only"
    THRESHOLD_JUDGE = "threshold_judge"


ARM_TITLES = {
    Arm.THRESHOLD_ONLY: "Threshold + top-k only",
    Arm.THRESHOLD_JUDGE: "Threshold + top-k + judge",
}


class JudgedPair(StrictModel):
    """One candidate pair with its gold kind and the judge's answer (`None` if unjudged)."""

    pair_id: NonEmptyStr
    a: NonEmptyStr
    b: NonEmptyStr
    kind: PairKind
    similarity: float
    is_duplicate: bool | None
    confidence: float | None
    rationale: str | None
    reason: str | None


class KindVerdicts(StrictModel):
    """How the judge answered the candidate pairs of one gold kind."""

    pairs: NonNegativeInt
    said_duplicate: NonNegativeInt
    unjudged: NonNegativeInt


class JudgeMetrics(StrictModel):
    """The judge as a classifier over candidate pairs, against gold pair kinds."""

    judged: NonNegativeInt
    unjudged: NonNegativeInt
    precision: float
    recall: float
    by_kind: dict[PairKind, KindVerdicts]
    calibration: list[CalibrationBin]


class DedupeEvalResult(StrictModel):
    """One dedupe eval run: config, both ablation arms, the judge, and every pair and cluster."""

    created_at: NonEmptyStr
    dataset: NonEmptyStr
    dataset_labels_sha256: NonEmptyStr
    split: Split
    prompt: NonEmptyStr
    model_id: NonEmptyStr
    embedding_model_id: NonEmptyStr
    dimensions: int
    config: DedupeConfig
    incidents: NonNegativeInt
    candidates: NonNegativeInt
    dropped_by_cap: NonNegativeInt
    arms: dict[Arm, DedupeMetrics]
    judge: JudgeMetrics
    never_proposed: list[tuple[str, str]]
    pairs: list[JudgedPair]
    clusters: dict[Arm, list[list[str]]]
    titles: dict[str, str]
    llm_calls: NonNegativeInt
    judge_valid_first_try: float
    fresh_llm_calls: NonNegativeInt
    fresh_embed_calls: NonNegativeInt
    judge_cost_usd: float
    cost_usd: float
    cost_per_100_incidents_usd: float


class CachingLLMClient:
    """Wraps an `LLMClient`; an identical request is sent to the model once."""

    def __init__(self, inner: LLMClient, cache_dir: Path) -> None:
        self._inner = inner
        self._cache_dir = cache_dir
        self.fresh_calls = 0

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return the cached response, or call the model and cache it."""
        key = hashlib.sha256(request.model_dump_json().encode("utf-8")).hexdigest()
        path = self._cache_dir / f"llm-{key}.json"
        if path.exists():
            return ModelResponse.model_validate_json(path.read_text("utf-8"))
        response = self._inner.complete(request)
        self.fresh_calls += 1
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(response.model_dump_json(), encoding="utf-8")
        return response


def gold_groups(labels: Mapping[str, EvalLabel]) -> list[list[str]]:
    """External IDs per duplicate group, sorted for stable output."""
    groups: dict[str, list[str]] = defaultdict(list)
    for external_id in sorted(labels):
        group = labels[external_id].duplicate_group
        if group:
            groups[group].append(external_id)
    return [groups[group] for group in sorted(groups)]


def judged_pairs(
    verdicts: Sequence[PairVerdict],
    external: Mapping[str, str],
    labels: Mapping[str, EvalLabel],
) -> list[JudgedPair]:
    """Candidate pairs in external IDs, with gold kind and the judge's answer."""
    rows = []
    for verdict in verdicts:
        a, b = external[verdict.pair.first_id], external[verdict.pair.second_id]
        judgement = verdict.judgement
        rows.append(
            JudgedPair(
                pair_id=verdict.pair.pair_id,
                a=a,
                b=b,
                kind=pair_kind(labels[a], labels[b]),
                similarity=verdict.pair.similarity,
                is_duplicate=judgement.is_duplicate if judgement else None,
                confidence=judgement.confidence if judgement else None,
                rationale=judgement.rationale if judgement else None,
                reason=verdict.reason,
            )
        )
    return rows


def judge_metrics(pairs: Sequence[JudgedPair]) -> JudgeMetrics:
    """Judge precision/recall over candidate pairs; unjudged pairs count as 'not duplicate'."""
    said = [p for p in pairs if p.is_duplicate]
    true_pos = sum(p.kind.is_duplicate for p in said)
    gold = sum(p.kind.is_duplicate for p in pairs)
    judged = [p for p in pairs if p.is_duplicate is not None]
    return JudgeMetrics(
        judged=len(judged),
        unjudged=len(pairs) - len(judged),
        precision=true_pos / len(said) if said else 0.0,
        recall=true_pos / gold if gold else 0.0,
        by_kind={
            kind: KindVerdicts(
                pairs=sum(p.kind is kind for p in pairs),
                said_duplicate=sum(p.kind is kind for p in said),
                unjudged=sum(p.kind is kind and p.is_duplicate is None for p in pairs),
            )
            for kind in PairKind
        },
        calibration=calibration_table(
            [(p.confidence or 0.0, p.is_duplicate == p.kind.is_duplicate) for p in judged]
        ),
    )


def run_dedupe_eval(
    *,
    dataset: str,
    split: Split,
    settings: Settings,
    client: LLMClient,
    embedder: EmbeddingClient,
    judge_version: int | None = None,
    datasets_dir: Path = DATASETS_DIR,
    cache_dir: Path = CACHE_DIR,
    sleep: Sleep = time.sleep,
) -> DedupeEvalResult:
    """Run the production dedupe stage over `split`, then score both ablation arms.

    `judge_version` overrides the configured `dedupe_judge` prompt version.
    """
    taxonomy = load_taxonomy(settings)
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    prompt = load_stage_prompt(
        settings, Stage.DEDUPE_JUDGE, judge_version or pipeline.prompts.dedupe_judge
    )
    raw, labels, manifest = load_split(datasets_dir / dataset, split, taxonomy)
    incidents = normalize_rows(raw, pipeline.normalize).incidents
    external = {incident.incident_id: incident.external_id for incident in incidents}

    records: list[LLMCallRecord] = []
    cached_llm = CachingLLMClient(client, cache_dir)
    cached_embedder = CachingEmbeddingClient(embedder, cache_dir)
    result = dedupe_batch(
        StructuredLLM(cached_llm, models, prices, recorder=records.append),
        prompt,
        cached_embedder,
        incidents,
        models=models,
        prices=prices,
        config=pipeline.dedupe,
        retry=pipeline.chunk_retry,
        recorder=records.append,
        batch_id=f"eval-{dataset}-{split}",
        sleep=sleep,
    )

    threshold_only = star_clusters(
        result.order, result.candidates.pairs, pipeline.dedupe.max_cluster_size
    )
    clusters = {
        arm: [[external[member] for member in cluster.member_ids] for cluster in found]
        for arm, found in (
            (Arm.THRESHOLD_ONLY, threshold_only),
            (Arm.THRESHOLD_JUDGE, result.clusters),
        )
    }
    gold = gold_groups(labels)
    pairs = judged_pairs(result.verdicts, external, labels)
    proposed = {frozenset((p.a, p.b)) for p in pairs}
    judge_records = [r for r in records if r.stage is Stage.DEDUPE_JUDGE]
    judge_cost = sum(r.cost_usd for r in judge_records)
    cost = sum(r.cost_usd for r in records)
    return DedupeEvalResult(
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        dataset=dataset,
        dataset_labels_sha256=manifest.sha256[LABELS_FILE],
        split=split,
        prompt=prompt.id,
        model_id=models.for_stage(Stage.DEDUPE_JUDGE).model_id,
        embedding_model_id=models.embedding.model_id,
        dimensions=models.embedding.dimensions,
        config=pipeline.dedupe,
        incidents=len(incidents),
        candidates=len(result.candidates.pairs),
        dropped_by_cap=result.candidates.dropped,
        arms={arm: dedupe_metrics(found, gold) for arm, found in clusters.items()},
        judge=judge_metrics(pairs),
        never_proposed=[
            (group[i], group[j])
            for group in gold
            for i in range(len(group))
            for j in range(i + 1, len(group))
            if frozenset((group[i], group[j])) not in proposed
        ],
        pairs=pairs,
        clusters={arm: [c for c in found if len(c) > 1] for arm, found in clusters.items()},
        titles={incident.external_id: incident.title for incident in incidents},
        llm_calls=len(judge_records),
        judge_valid_first_try=first_try_rate(judge_records),
        fresh_llm_calls=cached_llm.fresh_calls,
        fresh_embed_calls=cached_embedder.fresh_calls,
        judge_cost_usd=judge_cost,
        cost_usd=cost,
        cost_per_100_incidents_usd=cost / len(incidents) * PER_HUNDRED if incidents else 0.0,
    )


def _interval(metrics: DedupeMetrics, name: str) -> str:
    value = getattr(metrics, name)
    return f"**{value.value:.1%}** [{value.low:.1%}-{value.high:.1%}]"


def _pair_line(pair: JudgedPair, titles: Mapping[str, str]) -> str:
    answer = "unjudged" if pair.is_duplicate is None else f"said {pair.is_duplicate}"
    detail = pair.rationale or pair.reason or ""
    confidence = f", confidence {pair.confidence:.2f}" if pair.confidence is not None else ""
    return (
        f"- `{pair.a}` {titles[pair.a]!r} ~ `{pair.b}` {titles[pair.b]!r} "
        f"({pair.kind}, similarity {pair.similarity:.3f}): {answer}{confidence}. {detail}"
    )


def render_markdown(result: DedupeEvalResult) -> str:
    """Ablation table, judge breakdown, and every dedupe error to review."""
    judge = result.judge
    config = result.config
    lines = [
        f"# Dedupe · {result.prompt} · {result.model_id} · {result.dataset}/{result.split}",
        "",
        f"Run {result.created_at} · {result.incidents} incidents · "
        f"{result.embedding_model_id} ({result.dimensions} dims) · threshold "
        f"{config.similarity_threshold} · top-k {config.top_k} · {result.candidates} candidate "
        f"pairs ({result.dropped_by_cap} dropped by the cap of {config.max_pairs}) · "
        f"{result.llm_calls} judge calls ({result.fresh_llm_calls} fresh, "
        f"{result.judge_valid_first_try:.0%} valid first try) · "
        f"judge ${result.judge_cost_usd:.4f} · total ${result.cost_per_100_incidents_usd:.3f} "
        "per 100 incidents",
        "",
        "## Ablation (cluster-implied pairs vs. gold groups, 95% CI)",
        "",
        "| arm | precision | recall | predicted pairs | true pairs | gold pairs | clusters "
        "| largest |",
        "|---|---|---|---|---|---|---|---|",
        *(
            f"| {ARM_TITLES[arm]} | {_interval(m, 'precision')} | {_interval(m, 'recall')} "
            f"| {m.predicted_pairs} | {m.true_pairs} | {m.gold_pairs} | {m.clusters} "
            f"| {m.largest_cluster} |"
            for arm, m in result.arms.items()
        ),
        "",
        "## Judge on candidate pairs",
        "",
        f"Precision {judge.precision:.1%} · recall {judge.recall:.1%} · {judge.judged} judged · "
        f"{judge.unjudged} unjudged",
        "",
        "| gold kind | candidates | judged duplicate | unjudged |",
        "|---|---|---|---|",
        *(
            f"| {kind} | {v.pairs} | {v.said_duplicate} | {v.unjudged} |"
            for kind, v in judge.by_kind.items()
        ),
        "",
        "## Judge calibration (answer correct, by stated confidence)",
        "",
        "| confidence | count | mean confidence | accuracy |",
        "|---|---|---|---|",
        *(
            f"| {b.lower:.1f}-{b.upper:.1f} | {b.count} | "
            f"{'n/a' if b.mean_confidence is None else f'{b.mean_confidence:.2f}'} | "
            f"{'n/a' if b.accuracy is None else f'{b.accuracy:.1%}'} |"
            for b in judge.calibration
        ),
        "",
        "## Judge false positives (merged, but not the same bug)",
        "",
        *(
            [
                _pair_line(p, result.titles)
                for p in result.pairs
                if p.is_duplicate and not p.kind.is_duplicate
            ]
            or ["None."]
        ),
        "",
        "## Judge false negatives (same bug, not merged)",
        "",
        *(
            [
                _pair_line(p, result.titles)
                for p in result.pairs
                if p.kind.is_duplicate and not p.is_duplicate
            ]
            or ["None."]
        ),
        "",
        "## Gold pairs never proposed by the embedding stage",
        "",
        *(
            [
                f"- `{a}` {result.titles[a]!r} ~ `{b}` {result.titles[b]!r}"
                for a, b in result.never_proposed
            ]
            or ["None."]
        ),
        "",
        "## Clusters with the judge",
        "",
        *(
            [
                "- " + " · ".join(f"`{m}` {result.titles[m]!r}" for m in cluster)
                for cluster in result.clusters[Arm.THRESHOLD_JUDGE]
            ]
            or ["None."]
        ),
    ]
    return "\n".join(lines) + "\n"


def write_result(result: DedupeEvalResult, results_dir: Path = RESULTS_DIR) -> tuple[Path, Path]:
    """Write `<date>-<prompt>-<model>-<split>.{json,md}`."""
    stem = "-".join(
        [
            result.created_at[:10],
            result.prompt.replace("/", "-"),
            model_slug(result.model_id),
            result.split.value,
        ]
    )
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = results_dir / f"{stem}.json", results_dir / f"{stem}.md"
    json_path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return json_path, md_path


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.dedupe --split tuning`."""
    parser = argparse.ArgumentParser(prog="python -m evals.dedupe", description=__doc__)
    parser.add_argument("--dataset", default="seed-v1")
    parser.add_argument("--split", type=Split, choices=list(Split), default=Split.TUNING)
    parser.add_argument("--prompt", default=None, help="e.g. dedupe_judge/v2 (default: config)")
    parser.add_argument(
        "--confirm-holdout",
        action="store_true",
        help="required for --split holdout: the holdout is run once, for the reported number",
    )
    args = parser.parse_args(argv)
    if args.split is Split.HOLDOUT and not args.confirm_holdout:
        sys.stderr.write("refusing to run holdout without --confirm-holdout\n")
        return 1
    settings = get_settings()
    models, _ = load_llm_config(settings)
    try:
        judge_version = None
        if args.prompt:
            stage, judge_version = parse_prompt_id(args.prompt)
            if stage is not Stage.DEDUPE_JUDGE:
                raise EvalError(f"--prompt must be a dedupe_judge prompt, got {args.prompt!r}")
        result = run_dedupe_eval(
            dataset=args.dataset,
            split=args.split,
            settings=settings,
            client=BedrockLLMClient.from_settings(settings, models.client.timeout_seconds),
            embedder=BedrockEmbeddingClient.from_settings(settings, models.client.timeout_seconds),
            judge_version=judge_version,
        )
    except EvalError as error:
        sys.stderr.write(f"dedupe eval failed: {error}\n")
        return 1
    json_path, md_path = write_result(result)
    lines = [
        f"{ARM_TITLES[arm]}: precision {m.precision.value:.1%} "
        f"[{m.precision.low:.1%}-{m.precision.high:.1%}], recall {m.recall.value:.1%} "
        f"[{m.recall.low:.1%}-{m.recall.high:.1%}]"
        for arm, m in result.arms.items()
    ]
    sys.stdout.write(
        "\n".join(lines) + f"\n{result.fresh_llm_calls} fresh judge calls · "
        f"${result.cost_per_100_incidents_usd:.3f}/100\nwrote {json_path} and {md_path}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
