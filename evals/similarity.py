"""`python -m evals.similarity`: how close are duplicates vs. non-duplicates as vectors?"""

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import numpy as np
from pydantic import NonNegativeInt

from evals.dataset import DATASETS_DIR, EvalLabel, Split
from evals.harness import CACHE_DIR, RESULTS_DIR, EvalError, load_split
from triagelite.domain.models import LLMCallRecord, NonEmptyStr, StrictModel
from triagelite.llm.bedrock import BedrockEmbeddingClient
from triagelite.llm.client import EmbeddingClient
from triagelite.llm.config import EmbeddingConfig
from triagelite.llm.types import EmbeddingRequest, EmbeddingResponse
from triagelite.pipeline.dedupe import top_k_pairs
from triagelite.pipeline.embed import Matrix, embed_incidents, similarity_matrix
from triagelite.pipeline.normalize import normalize_rows
from triagelite.settings import (
    Settings,
    get_settings,
    load_llm_config,
    load_pipeline_config,
    load_taxonomy,
)

RECALL_TARGET = 0.95
THRESHOLD_MIN, THRESHOLD_MAX, THRESHOLD_STEP = 0.20, 0.95, 0.025
HISTOGRAM_BIN_WIDTH = 0.025
QUANTILES = (0, 10, 50, 90, 100)
PLOT_DPI = 200

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e6e4df"
DUPLICATE_FILL = "#2a78d6"
OTHER_FILL = "#a3a19b"


class PairKind(StrEnum):
    """What a pair of eval incidents is, according to the gold labels."""

    DUPLICATE_SAME_LANGUAGE = "duplicate_same_language"
    DUPLICATE_CROSS_LANGUAGE = "duplicate_cross_language"
    NEAR_MISS = "near_miss"
    UNRELATED = "unrelated"

    @property
    def is_duplicate(self) -> bool:
        """Both duplicate kinds count as true pairs."""
        return self in (PairKind.DUPLICATE_SAME_LANGUAGE, PairKind.DUPLICATE_CROSS_LANGUAGE)


PANEL_TITLES = {
    PairKind.DUPLICATE_SAME_LANGUAGE: "Duplicates, same language",
    PairKind.DUPLICATE_CROSS_LANGUAGE: "Duplicates, Spanish vs English",
    PairKind.NEAR_MISS: "Near-misses (same component, different bug)",
    PairKind.UNRELATED: "Unrelated pairs",
}


class Pair(StrictModel):
    """Two incidents, their gold relationship, similarity, and whether top-k keeps them."""

    a: NonEmptyStr
    b: NonEmptyStr
    kind: PairKind
    similarity: float
    in_top_k: bool


class KindStats(StrictModel):
    """Similarity quantiles for one kind of pair."""

    count: NonNegativeInt
    quantiles: dict[str, float]


class SweepRow(StrictModel):
    """What a threshold would let through, with or without the top-k filter."""

    threshold: float
    top_k: bool
    candidates: NonNegativeInt
    duplicates_found: NonNegativeInt
    recall: float
    cross_language_recall: float
    precision: float
    near_misses_flagged: NonNegativeInt


class SimilarityReport(StrictModel):
    """Everything the threshold decision is based on."""

    created_at: NonEmptyStr
    dataset: NonEmptyStr
    split: Split
    model_id: NonEmptyStr
    dimensions: int
    top_k: int
    recall_target: float
    recommended_threshold: float | None
    stats: dict[PairKind, KindStats]
    sweep: list[SweepRow]
    pairs: list[Pair]
    fresh_calls: NonNegativeInt
    cost_usd: float


class CachingEmbeddingClient:
    """Wraps an `EmbeddingClient`; identical (model, dims, normalize, text) is embedded once."""

    def __init__(self, inner: EmbeddingClient, cache_dir: Path) -> None:
        self._inner = inner
        self._cache_dir = cache_dir
        self.fresh_calls = 0

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Return the cached vector, or embed and cache it."""
        key = hashlib.sha256(request.model_dump_json().encode("utf-8")).hexdigest()
        path = self._cache_dir / f"embed-{key}.json"
        if path.exists():
            return EmbeddingResponse.model_validate_json(path.read_text("utf-8"))
        response = self._inner.embed(request)
        self.fresh_calls += 1
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(response.model_dump_json(), encoding="utf-8")
        return response


def pair_kind(first: EvalLabel, second: EvalLabel) -> PairKind:
    """Gold relationship between two items."""
    if first.duplicate_group and first.duplicate_group == second.duplicate_group:
        if first.lang == second.lang:
            return PairKind.DUPLICATE_SAME_LANGUAGE
        return PairKind.DUPLICATE_CROSS_LANGUAGE
    if (first.near_miss_of and first.near_miss_of == second.duplicate_group) or (
        second.near_miss_of and second.near_miss_of == first.duplicate_group
    ):
        return PairKind.NEAR_MISS
    return PairKind.UNRELATED


def labelled_pairs(
    external_ids: Sequence[str], labels: Mapping[str, EvalLabel], similarity: Matrix, k: int
) -> list[Pair]:
    """Every unordered pair with its gold kind, similarity and top-k membership."""
    neighbours = top_k_pairs(similarity, k)
    return [
        Pair(
            a=external_ids[i],
            b=external_ids[j],
            kind=pair_kind(labels[external_ids[i]], labels[external_ids[j]]),
            similarity=round(float(similarity[i, j]), 4),
            in_top_k=(i, j) in neighbours,
        )
        for i in range(len(external_ids))
        for j in range(i + 1, len(external_ids))
    ]


def sweep(pairs: Sequence[Pair], thresholds: Sequence[float]) -> list[SweepRow]:
    """Recall, precision and candidate counts per threshold, without and with top-k."""
    duplicates = [p for p in pairs if p.kind.is_duplicate]
    cross = [p for p in pairs if p.kind is PairKind.DUPLICATE_CROSS_LANGUAGE]
    rows: list[SweepRow] = []
    for use_top_k in (False, True):
        for threshold in thresholds:

            def kept(p: Pair, t: float = threshold, gate: bool = use_top_k) -> bool:
                return p.similarity >= t and (p.in_top_k or not gate)

            candidates = [p for p in pairs if kept(p)]
            found = [p for p in candidates if p.kind.is_duplicate]
            rows.append(
                SweepRow(
                    threshold=round(threshold, 3),
                    top_k=use_top_k,
                    candidates=len(candidates),
                    duplicates_found=len(found),
                    recall=len(found) / len(duplicates) if duplicates else 0.0,
                    cross_language_recall=(
                        sum(kept(p) for p in cross) / len(cross) if cross else 0.0
                    ),
                    precision=len(found) / len(candidates) if candidates else 0.0,
                    near_misses_flagged=sum(p.kind is PairKind.NEAR_MISS for p in candidates),
                )
            )
    return rows


def recommend_threshold(rows: Sequence[SweepRow], recall_target: float) -> float | None:
    """Highest top-k threshold that still keeps at least `recall_target` of true pairs."""
    passing = [r.threshold for r in rows if r.top_k and r.recall >= recall_target]
    return max(passing) if passing else None


def kind_stats(pairs: Sequence[Pair]) -> dict[PairKind, KindStats]:
    """Similarity quantiles per pair kind."""
    stats: dict[PairKind, KindStats] = {}
    for kind in PairKind:
        values = [p.similarity for p in pairs if p.kind is kind]
        quantiles = (
            {f"p{q}": round(float(np.percentile(values, q)), 4) for q in QUANTILES}
            if values
            else {}
        )
        stats[kind] = KindStats(count=len(values), quantiles=quantiles)
    return stats


def thresholds() -> list[float]:
    """The sweep grid."""
    steps = round((THRESHOLD_MAX - THRESHOLD_MIN) / THRESHOLD_STEP)
    return [round(THRESHOLD_MIN + i * THRESHOLD_STEP, 3) for i in range(steps + 1)]


def run_similarity(
    *,
    dataset: str,
    split: Split,
    settings: Settings,
    client: EmbeddingClient,
    embedding: EmbeddingConfig | None = None,
    datasets_dir: Path = DATASETS_DIR,
    cache_dir: Path = CACHE_DIR,
) -> SimilarityReport:
    """Embed a split, label every pair, and sweep thresholds."""
    taxonomy = load_taxonomy(settings)
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    config = embedding or models.embedding
    raw, labels, _ = load_split(datasets_dir / dataset, split, taxonomy)
    incidents = normalize_rows(raw, pipeline.normalize).incidents
    cached = CachingEmbeddingClient(client, cache_dir)
    records: list[LLMCallRecord] = []
    matrix = embed_incidents(
        cached, incidents, config, prices, records.append, batch_id=f"eval-{dataset}-{split}"
    )
    external_ids = [incident.external_id for incident in incidents]
    pairs = labelled_pairs(
        external_ids, labels, similarity_matrix(matrix.vectors), pipeline.dedupe.top_k
    )
    rows = sweep(pairs, thresholds())
    return SimilarityReport(
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        dataset=dataset,
        split=split,
        model_id=config.model_id,
        dimensions=config.dimensions,
        top_k=pipeline.dedupe.top_k,
        recall_target=RECALL_TARGET,
        recommended_threshold=recommend_threshold(rows, RECALL_TARGET),
        stats=kind_stats(pairs),
        sweep=rows,
        pairs=pairs,
        fresh_calls=cached.fresh_calls,
        cost_usd=sum(record.cost_usd for record in records),
    )


def render_markdown(report: SimilarityReport) -> str:
    """Table view of the plot plus the threshold sweep."""
    lines = [
        f"# Embedding similarity · {report.model_id} · {report.dimensions} dims · "
        f"{report.dataset}/{report.split}",
        "",
        f"Run {report.created_at} · top-k {report.top_k} · {report.fresh_calls} fresh calls · "
        f"${report.cost_usd:.6f}",
        "",
        f"Recommended threshold (highest with top-k recall ≥ {report.recall_target:.0%}): "
        f"**{report.recommended_threshold}**",
        "",
        "## Similarity by pair kind",
        "",
        "| kind | pairs | min | p10 | median | p90 | max |",
        "|---|---|---|---|---|---|---|",
    ]
    for kind, stats in report.stats.items():
        q = stats.quantiles
        cells = " | ".join(f"{q[f'p{v}']:.3f}" if q else "n/a" for v in QUANTILES)
        lines.append(f"| {PANEL_TITLES[kind]} | {stats.count} | {cells} |")
    lines += [
        "",
        "## Threshold sweep",
        "",
        "| threshold | top-k | candidates | duplicates found | recall | cross-language recall "
        "| precision | near-misses flagged |",
        "|---|---|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {r.threshold:.3f} | {'yes' if r.top_k else 'no'} | {r.candidates} "
        f"| {r.duplicates_found} | {r.recall:.1%} | {r.cross_language_recall:.1%} "
        f"| {r.precision:.1%} | {r.near_misses_flagged} |"
        for r in report.sweep
    ]
    missed = [
        p
        for p in report.pairs
        if p.kind.is_duplicate
        and report.recommended_threshold is not None
        and not (p.similarity >= report.recommended_threshold and p.in_top_k)
    ]
    lines += ["", "## Duplicate pairs the recommended threshold misses", ""]
    lines += [
        f"- {p.a} ~ {p.b} ({p.kind}): similarity {p.similarity:.3f}, top-k {p.in_top_k}"
        for p in missed
    ] or ["None."]
    return "\n".join(lines) + "\n"


def render_plot(report: SimilarityReport, path: Path) -> None:
    """Small multiples: one histogram per pair kind, shared similarity axis, threshold line."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    bins = np.arange(0.0, 1.0 + HISTOGRAM_BIN_WIDTH, HISTOGRAM_BIN_WIDTH)
    figure, axes = plt.subplots(len(PairKind), 1, figsize=(8, 7.5), sharex=True)
    figure.patch.set_facecolor(SURFACE)
    for axis, kind in zip(axes, PairKind, strict=True):
        values = [p.similarity for p in report.pairs if p.kind is kind]
        axis.set_facecolor(SURFACE)
        axis.hist(
            values,
            bins=bins,
            color=DUPLICATE_FILL if kind.is_duplicate else OTHER_FILL,
            rwidth=0.82,
        )
        axis.set_title(
            f"{PANEL_TITLES[kind]} · {len(values)} pairs",
            loc="left",
            fontsize=10,
            color=TEXT_PRIMARY,
        )
        axis.grid(axis="y", color=GRID, linewidth=0.8)
        axis.set_axisbelow(True)
        axis.tick_params(colors=TEXT_SECONDARY, labelsize=8, length=0)
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(GRID)
        if report.recommended_threshold is not None:
            axis.axvline(
                report.recommended_threshold, color=TEXT_SECONDARY, linestyle="--", linewidth=1.2
            )
    if report.recommended_threshold is not None:
        axes[0].annotate(
            f"threshold {report.recommended_threshold:.3f}",
            xy=(report.recommended_threshold, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(4, -12),
            textcoords="offset points",
            fontsize=8,
            color=TEXT_SECONDARY,
        )
    axes[-1].set_xlabel(
        f"Cosine similarity ({report.model_id}, {report.dimensions} dims)",
        color=TEXT_SECONDARY,
        fontsize=9,
    )
    figure.suptitle(
        f"Duplicate vs. non-duplicate pairs, {report.dataset} {report.split} split",
        x=0.01,
        ha="left",
        fontsize=12,
        color=TEXT_PRIMARY,
    )
    figure.tight_layout()
    figure.savefig(path, dpi=PLOT_DPI, facecolor=SURFACE)
    plt.close(figure)


def write_report(report: SimilarityReport, results_dir: Path = RESULTS_DIR) -> list[Path]:
    """Write `<date>-embed-<model>-<dims>-<split>.{json,md,png}`."""
    short = report.model_id.split(":")[0].replace(".", "-")
    stem = f"{report.created_at[:10]}-embed-{short}-{report.dimensions}-{report.split}"
    results_dir.mkdir(parents=True, exist_ok=True)
    paths = [results_dir / f"{stem}.{ext}" for ext in ("json", "md", "png")]
    paths[0].write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    paths[1].write_text(render_markdown(report), encoding="utf-8")
    render_plot(report, paths[2])
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.similarity [--dimensions 512]`."""
    parser = argparse.ArgumentParser(prog="python -m evals.similarity", description=__doc__)
    parser.add_argument("--dataset", default="seed-v1")
    parser.add_argument("--dimensions", type=int, choices=(256, 512, 1024), default=None)
    args = parser.parse_args(argv)
    settings = get_settings()
    models, _ = load_llm_config(settings)
    embedding = (
        models.embedding.model_copy(update={"dimensions": args.dimensions})
        if args.dimensions
        else None
    )
    client = BedrockEmbeddingClient.from_settings(settings, models.client.timeout_seconds)
    try:
        report = run_similarity(
            dataset=args.dataset,
            split=Split.TUNING,
            settings=settings,
            client=client,
            embedding=embedding,
        )
    except EvalError as error:
        sys.stderr.write(f"similarity failed: {error}\n")
        return 1
    paths = write_report(report)
    summary = {
        "recommended_threshold": report.recommended_threshold,
        "stats": {k.value: v.quantiles.get("p50") for k, v in report.stats.items()},
        "fresh_calls": report.fresh_calls,
        "cost_usd": round(report.cost_usd, 6),
    }
    sys.stdout.write(json.dumps(summary) + "\n" + "\n".join(map(str, paths)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
