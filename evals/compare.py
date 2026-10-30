"""`python -m evals.compare BASE.json CANDIDATE.json`: paired bootstrap between two harness runs."""

import argparse
import sys
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

from pydantic import NonNegativeInt

from evals.dataset import EvalLabel
from evals.harness import RESULTS_DIR, EvalResult, result_stem
from evals.metrics import Interval, ItemPrediction, bootstrap_interval, macro_f1
from triagelite.domain.models import NonEmptyStr, StrictModel

REGRESSION_DROP = 0.05
COST_INCREASE_LIMIT = 0.15
MAJORITY = 0.5
LABEL_FIELDS = ("severity", "component", "category")


class CompareError(Exception):
    """The two runs can't be compared; the message says why."""


class Verdict(StrEnum):
    """TL-08 decision on severity macro-F1."""

    IMPROVEMENT = "improvement"
    REGRESSION = "regression"
    NO_SIGNIFICANT_DIFFERENCE = "no significant difference"


class PairedDelta(StrictModel):
    """A metric for both runs and the paired bootstrap interval of candidate minus base."""

    base: float
    candidate: float
    delta: Interval


class Unpaired(StrictModel):
    """A run-level number with no per-item breakdown (cost, latency)."""

    base: float
    candidate: float


class ItemChange(StrictModel):
    """An item whose majority answer for one label flipped between the runs."""

    external_id: NonEmptyStr
    field: NonEmptyStr
    title: str
    gold: NonEmptyStr
    base_correct: float
    candidate_correct: float


class Comparison(StrictModel):
    """Everything `evals.compare` reports for one base/candidate pair."""

    base: NonEmptyStr
    candidate: NonEmptyStr
    dataset: NonEmptyStr
    split: NonEmptyStr
    items: NonNegativeInt
    severity_macro_f1: PairedDelta
    severity_accuracy: PairedDelta
    component_accuracy: PairedDelta
    category_accuracy: PairedDelta
    cost_per_100_incidents_usd: Unpaired
    latency_p95_ms: Unpaired
    schema_valid_first_try: Unpaired
    confident_share: Unpaired
    fixed: list[ItemChange]
    broken: list[ItemChange]
    verdict: Verdict
    cost_gate_failed: bool


class Row(NamedTuple):
    """One prediction tagged with the run it came from."""

    candidate: bool
    prediction: ItemPrediction


type ItemMetric = Callable[[Sequence[ItemPrediction]], float]


def check_comparable(base: EvalResult, candidate: EvalResult) -> None:
    """Paired comparison needs the same frozen labels and the same items."""
    if (base.dataset, base.split) != (candidate.dataset, candidate.split):
        raise CompareError(
            f"different data: {base.dataset}/{base.split} vs {candidate.dataset}/{candidate.split}"
        )
    if base.dataset_labels_sha256 != candidate.dataset_labels_sha256:
        raise CompareError("the runs used different versions of the labels")
    base_items = {p.external_id for p in base.predictions}
    candidate_items = {p.external_id for p in candidate.predictions}
    if base_items != candidate_items:
        raise CompareError(
            f"different items: {len(base_items ^ candidate_items)} appear in only one run"
        )


def label_correct(prediction: ItemPrediction, gold: EvalLabel, field: str) -> bool:
    """Whether one label of a prediction matches gold; needs_manual is wrong."""
    return bool(getattr(prediction, field) == getattr(gold, field))


def paired_delta(groups: Sequence[Sequence[Row]], metric: ItemMetric) -> PairedDelta:
    """Resample items once per round and score both runs on the same items."""

    def split(rows: Sequence[Row], candidate: bool) -> list[ItemPrediction]:
        return [row.prediction for row in rows if row.candidate is candidate]

    rows = [row for group in groups for row in group]
    return PairedDelta(
        base=metric(split(rows, candidate=False)),
        candidate=metric(split(rows, candidate=True)),
        delta=bootstrap_interval(
            groups, lambda sample: metric(split(sample, True)) - metric(split(sample, False))
        ),
    )


def verdict(f1: PairedDelta) -> Verdict:
    """Regression on a significant drop or a drop of at least five points; else CI decides."""
    if f1.delta.high < 0 or f1.delta.value <= -REGRESSION_DROP:
        return Verdict.REGRESSION
    if f1.delta.low > 0:
        return Verdict.IMPROVEMENT
    return Verdict.NO_SIGNIFICANT_DIFFERENCE


def item_changes(
    base: EvalResult, candidate: EvalResult, labels: Mapping[str, EvalLabel]
) -> tuple[list[ItemChange], list[ItemChange]]:
    """Labels right in most candidate repeats but not base ones (fixed), and the reverse."""

    def shares(result: EvalResult, field: str) -> dict[str, float]:
        hits: dict[str, list[bool]] = defaultdict(list)
        for p in result.predictions:
            hits[p.external_id].append(label_correct(p, labels[p.external_id], field))
        return {external_id: sum(ok) / len(ok) for external_id, ok in hits.items()}

    titles = {p.external_id: p.title for p in base.predictions}
    fixed: list[ItemChange] = []
    broken: list[ItemChange] = []
    for field in LABEL_FIELDS:
        before, after = shares(base, field), shares(candidate, field)
        for external_id in sorted(before):
            change = ItemChange(
                external_id=external_id,
                field=field,
                title=titles[external_id],
                gold=str(getattr(labels[external_id], field)),
                base_correct=before[external_id],
                candidate_correct=after[external_id],
            )
            was_right, is_right = before[external_id] > MAJORITY, after[external_id] > MAJORITY
            if is_right and not was_right:
                fixed.append(change)
            elif was_right and not is_right:
                broken.append(change)
    return fixed, broken


def compare(base: EvalResult, candidate: EvalResult) -> Comparison:
    """Paired deltas for quality, unpaired cost and latency, flipped items and the verdict."""
    check_comparable(base, candidate)
    labels = {label.external_id: label for label in base.labels}
    by_item: dict[str, list[Row]] = defaultdict(list)
    for tagged, result in ((False, base), (True, candidate)):
        for p in result.predictions:
            by_item[p.external_id].append(Row(tagged, p))
    groups = [by_item[external_id] for external_id in sorted(by_item)]

    def accuracy(field: str) -> ItemMetric:
        def metric(predictions: Sequence[ItemPrediction]) -> float:
            hits = [label_correct(p, labels[p.external_id], field) for p in predictions]
            return sum(hits) / len(hits) if hits else 0.0

        return metric

    def severity_f1(predictions: Sequence[ItemPrediction]) -> float:
        return macro_f1([(labels[p.external_id].severity, p.severity) for p in predictions])

    def unpaired(field: str) -> Unpaired:
        return Unpaired(
            base=float(getattr(base.metrics, field) or 0.0),
            candidate=float(getattr(candidate.metrics, field) or 0.0),
        )

    f1 = paired_delta(groups, severity_f1)
    cost = unpaired("cost_per_100_incidents_usd")
    fixed, broken = item_changes(base, candidate, labels)
    return Comparison(
        base=result_stem(base),
        candidate=result_stem(candidate),
        dataset=base.dataset,
        split=base.split.value,
        items=len(groups),
        severity_macro_f1=f1,
        severity_accuracy=paired_delta(groups, accuracy("severity")),
        component_accuracy=paired_delta(groups, accuracy("component")),
        category_accuracy=paired_delta(groups, accuracy("category")),
        cost_per_100_incidents_usd=cost,
        latency_p95_ms=unpaired("latency_p95_ms"),
        schema_valid_first_try=unpaired("schema_valid_first_try"),
        confident_share=unpaired("confident_share"),
        fixed=fixed,
        broken=broken,
        verdict=verdict(f1),
        cost_gate_failed=cost.candidate > cost.base * (1 + COST_INCREASE_LIMIT),
    )


def _delta_row(name: str, metric: PairedDelta) -> str:
    d = metric.delta
    return (
        f"| {name} | {metric.base:.3f} | {metric.candidate:.3f} "
        f"| **{d.value:+.3f}** [{d.low:+.3f}, {d.high:+.3f}] |"
    )


def _change_line(change: ItemChange) -> str:
    return (
        f"- **{change.external_id}** {change.field} (gold {change.gold}): "
        f"{change.base_correct:.0%} → {change.candidate_correct:.0%} of repeats right · "
        f"{change.title}"
    )


def render_markdown(c: Comparison) -> str:
    """The comparison as a Markdown report."""
    cost, latency = c.cost_per_100_incidents_usd, c.latency_p95_ms
    lines = [
        f"# {c.candidate} vs {c.base}",
        "",
        f"{c.dataset}/{c.split} · {c.items} items · paired bootstrap over items "
        "(repeats stay together), 95% CI of candidate minus base.",
        "",
        f"**Verdict (severity macro-F1, TL-08): {c.verdict}.**"
        + (" **Cost gate failed (> +15%).**" if c.cost_gate_failed else ""),
        "",
        "| metric | base | candidate | Δ [95% CI] |",
        "|---|---|---|---|",
        _delta_row("severity macro-F1", c.severity_macro_f1),
        _delta_row("severity accuracy", c.severity_accuracy),
        _delta_row("component accuracy", c.component_accuracy),
        _delta_row("category accuracy", c.category_accuracy),
        "",
        "| run-level | base | candidate |",
        "|---|---|---|",
        f"| $ per 100 incidents | ${cost.base:.3f} | ${cost.candidate:.3f} |",
        f"| p95 latency ms | {latency.base:.0f} | {latency.candidate:.0f} |",
        f"| schema-valid first try | {c.schema_valid_first_try.base:.1%} "
        f"| {c.schema_valid_first_try.candidate:.1%} |",
        f"| confidence ≥ 0.7 share | {c.confident_share.base:.1%} "
        f"| {c.confident_share.candidate:.1%} |",
        "",
        f"## Fixed ({len(c.fixed)})",
        "",
        *([_change_line(change) for change in c.fixed] or ["None."]),
        "",
        f"## Broken ({len(c.broken)})",
        "",
        *([_change_line(change) for change in c.broken] or ["None."]),
    ]
    return "\n".join(lines) + "\n"


def write_comparison(comparison: Comparison, results_dir: Path = RESULTS_DIR) -> Path:
    """Write `compare-<candidate>-vs-<base>.md`; it is fully determined by the two inputs."""
    path = results_dir / f"compare-{comparison.candidate}-vs-{comparison.base}.md"
    results_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(comparison), encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.compare <base.json> <candidate.json>`."""
    parser = argparse.ArgumentParser(prog="python -m evals.compare", description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args(argv)
    try:
        base, candidate = (
            EvalResult.model_validate_json(path.read_text("utf-8"))
            for path in (args.base, args.candidate)
        )
        comparison = compare(base, candidate)
    except CompareError as error:
        sys.stderr.write(f"compare failed: {error}\n")
        return 1
    path = write_comparison(comparison, args.results_dir)
    d = comparison.severity_macro_f1.delta
    sys.stdout.write(
        f"{comparison.candidate} vs {comparison.base}: macro-F1 Δ {d.value:+.3f} "
        f"[{d.low:+.3f}, {d.high:+.3f}] · {comparison.verdict} · "
        f"{len(comparison.fixed)} fixed, {len(comparison.broken)} broken\nwrote {path}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
