"""Classify and dedupe quality, calibration, cost and latency for one eval run. Pure functions."""

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Annotated

import numpy as np
from pydantic import Field, NonNegativeInt

from evals.dataset import EvalLabel
from triagelite.domain.enums import CallStatus, Category, Severity
from triagelite.domain.models import Language, LLMCallRecord, NonEmptyStr, StrictModel

CONFIDENCE_THRESHOLD = 0.7
CALIBRATION_BINS = 5
BOOTSTRAP_RESAMPLES = 1000
CONFIDENCE_LEVEL = 0.95
BOOTSTRAP_SEED = 20261029
PER_HUNDRED = 100
P50, P95 = 50, 95

Rate = Annotated[float, Field(ge=0.0, le=1.0)]


class ItemPrediction(StrictModel):
    """What the pipeline produced for one eval item in one repeat; `None` means needs_manual."""

    external_id: NonEmptyStr
    repeat: NonNegativeInt
    title: str
    detected_lang: Language
    severity: Severity | None = None
    category: Category | None = None
    component: str | None = None
    confidence: Rate | None = None
    rationale: str | None = None
    reason: str | None = None


class Interval(StrictModel):
    """A point estimate with a bootstrap confidence interval."""

    value: float
    low: float
    high: float


class ClassMetrics(StrictModel):
    """Precision, recall and F1 for one severity class."""

    precision: float
    recall: float
    f1: float
    support: NonNegativeInt


class CalibrationBin(StrictModel):
    """Predictions whose confidence falls in [lower, upper), and how often they were right."""

    lower: float
    upper: float
    count: NonNegativeInt
    mean_confidence: float | None
    accuracy: float | None


class ClassifyMetrics(StrictModel):
    """Every number the eval reports for the classify stage."""

    items: NonNegativeInt
    predictions: NonNegativeInt
    severity_macro_f1: Interval
    severity_accuracy: Rate
    per_class: dict[Severity, ClassMetrics]
    confusion: dict[str, dict[str, int]]
    category_accuracy: Rate
    component_accuracy: Rate
    language_accuracy: Rate
    confident_share: Rate
    confident_accuracy: Rate | None
    calibration: list[CalibrationBin]
    needs_manual_rate: Rate
    schema_valid_first_try: Rate
    llm_calls: NonNegativeInt
    cost_usd: float
    cost_per_100_incidents_usd: float
    latency_p50_ms: float
    latency_p95_ms: float


type SeverityPair = tuple[Severity, Severity | None]


def per_class_metrics(pairs: Sequence[SeverityPair]) -> dict[Severity, ClassMetrics]:
    """One-vs-rest precision/recall/F1; a needs_manual prediction is a miss for its gold class."""
    result: dict[Severity, ClassMetrics] = {}
    for severity in Severity:
        true_pos = sum(gold is severity and pred is severity for gold, pred in pairs)
        predicted = sum(pred is severity for _, pred in pairs)
        support = sum(gold is severity for gold, _ in pairs)
        precision = true_pos / predicted if predicted else 0.0
        recall = true_pos / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        result[severity] = ClassMetrics(precision=precision, recall=recall, f1=f1, support=support)
    return result


def macro_f1(pairs: Sequence[SeverityPair]) -> float:
    """Unweighted mean F1 over the classes present in the gold labels."""
    present = {gold for gold, _ in pairs}
    scores = [m.f1 for severity, m in per_class_metrics(pairs).items() if severity in present]
    return sum(scores) / len(scores) if scores else 0.0


def bootstrap_interval[T](
    groups: Sequence[Sequence[T]],
    statistic: Callable[[list[T]], float],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    level: float = CONFIDENCE_LEVEL,
    seed: int = BOOTSTRAP_SEED,
) -> Interval:
    """Percentile bootstrap over groups (one group per eval item, holding all its repeats).

    Resampling whole items, not rows, keeps repeats of one item together: they are not
    independent evidence. The seed makes the interval reproducible.
    """
    flat = [row for group in groups for row in group]
    value = statistic(flat)
    if not groups:
        return Interval(value=value, low=value, high=value)
    rng = np.random.default_rng(seed)
    estimates = [
        statistic([row for index in picks for row in groups[index]])
        for picks in rng.integers(0, len(groups), size=(resamples, len(groups)))
    ]
    tail = (1 - level) / 2 * 100
    low, high = np.percentile(estimates, [tail, 100 - tail])
    return Interval(value=value, low=float(low), high=float(high))


def calibration_table(
    rows: Sequence[tuple[float, bool]], bins: int = CALIBRATION_BINS
) -> list[CalibrationBin]:
    """Equal-width confidence bins; the last bin includes 1.0."""
    table: list[CalibrationBin] = []
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        inside = [
            (conf, ok)
            for conf, ok in rows
            if lower <= conf < upper or (index == bins - 1 and conf == upper)
        ]
        table.append(
            CalibrationBin(
                lower=lower,
                upper=upper,
                count=len(inside),
                mean_confidence=sum(c for c, _ in inside) / len(inside) if inside else None,
                accuracy=sum(ok for _, ok in inside) / len(inside) if inside else None,
            )
        )
    return table


def confusion_matrix(pairs: Sequence[SeverityPair]) -> dict[str, dict[str, int]]:
    """Gold severity (rows) by predicted severity or `needs_manual` (columns)."""
    columns = [*(s.value for s in Severity), "needs_manual"]
    matrix = {gold.value: dict.fromkeys(columns, 0) for gold in Severity}
    for gold, pred in pairs:
        matrix[gold.value][pred.value if pred else "needs_manual"] += 1
    return matrix


def first_try_rate(records: Sequence[LLMCallRecord]) -> float:
    """Share of logical calls whose first attempt returned valid output."""
    first = [record for record in records if record.attempt == 1]
    return sum(r.status is CallStatus.OK for r in first) / len(first) if first else 0.0


def compute_metrics(
    labels: Mapping[str, EvalLabel],
    predictions: Sequence[ItemPrediction],
    records: Sequence[LLMCallRecord],
) -> ClassifyMetrics:
    """All classify metrics for predictions over `labels` (possibly several repeats each)."""
    by_item: dict[str, list[ItemPrediction]] = defaultdict(list)
    for prediction in predictions:
        by_item[prediction.external_id].append(prediction)
    groups = [by_item[external_id] for external_id in sorted(by_item)]
    pairs = [(labels[p.external_id].severity, p.severity) for p in predictions]

    def rate(hit: Callable[[ItemPrediction], bool]) -> float:
        return sum(hit(p) for p in predictions) / len(predictions) if predictions else 0.0

    def severity_ok(p: ItemPrediction) -> bool:
        return p.severity is labels[p.external_id].severity

    confident = [p for p in predictions if p.confidence is not None]
    above = [p for p in confident if (p.confidence or 0.0) >= CONFIDENCE_THRESHOLD]
    latencies = [record.latency_ms for record in records] or [0]
    cost = sum(record.cost_usd for record in records)
    return ClassifyMetrics(
        items=len(groups),
        predictions=len(predictions),
        severity_macro_f1=bootstrap_interval(
            groups,
            lambda rows: macro_f1([(labels[r.external_id].severity, r.severity) for r in rows]),
        ),
        severity_accuracy=rate(severity_ok),
        per_class=per_class_metrics(pairs),
        confusion=confusion_matrix(pairs),
        category_accuracy=rate(lambda p: p.category is labels[p.external_id].category),
        component_accuracy=rate(lambda p: p.component == labels[p.external_id].component),
        language_accuracy=rate(lambda p: p.detected_lang == labels[p.external_id].lang),
        confident_share=len(above) / len(predictions) if predictions else 0.0,
        confident_accuracy=sum(map(severity_ok, above)) / len(above) if above else None,
        calibration=calibration_table([(p.confidence or 0.0, severity_ok(p)) for p in confident]),
        needs_manual_rate=rate(lambda p: p.severity is None),
        schema_valid_first_try=first_try_rate(records),
        llm_calls=len(records),
        cost_usd=cost,
        cost_per_100_incidents_usd=cost / len(predictions) * PER_HUNDRED if predictions else 0.0,
        latency_p50_ms=float(np.percentile(latencies, P50)),
        latency_p95_ms=float(np.percentile(latencies, P95)),
    )


type UnorderedPair = frozenset[str]


class DedupeMetrics(StrictModel):
    """Dedupe quality on cluster-implied pairs: every pair inside a cluster is a claim."""

    clusters: NonNegativeInt
    largest_cluster: NonNegativeInt
    predicted_pairs: NonNegativeInt
    gold_pairs: NonNegativeInt
    true_pairs: NonNegativeInt
    precision: Interval
    recall: Interval


def implied_pairs(groups: Iterable[Sequence[str]]) -> set[UnorderedPair]:
    """Every unordered pair of members inside each group."""
    return {
        frozenset((group[i], group[j]))
        for group in groups
        for i in range(len(group))
        for j in range(i + 1, len(group))
    }


def connected_pair_groups(
    predicted: set[UnorderedPair], gold: set[UnorderedPair]
) -> list[list[tuple[bool, bool]]]:
    """`(predicted, gold)` flags per pair, grouped by connected incidents.

    Pairs that share incidents are not independent evidence (one wrong merge creates several
    wrong pairs), so the bootstrap resamples these groups, not single pairs.
    """
    neighbours: dict[str, set[str]] = defaultdict(set)
    for pair in predicted | gold:
        first, second = sorted(pair)
        neighbours[first].add(second)
        neighbours[second].add(first)
    seen: set[str] = set()
    groups: list[list[tuple[bool, bool]]] = []
    for start in sorted(neighbours):
        if start in seen:
            continue
        component, frontier = {start}, [start]
        while frontier:
            for nxt in neighbours[frontier.pop()] - component:
                component.add(nxt)
                frontier.append(nxt)
        seen |= component
        pairs = sorted((p for p in predicted | gold if p <= component), key=lambda p: sorted(p))
        groups.append([(p in predicted, p in gold) for p in pairs])
    return groups


def pair_precision(rows: Sequence[tuple[bool, bool]]) -> float:
    """Share of predicted pairs that are gold pairs."""
    predicted = sum(pred for pred, _ in rows)
    return sum(pred and gold for pred, gold in rows) / predicted if predicted else 0.0


def pair_recall(rows: Sequence[tuple[bool, bool]]) -> float:
    """Share of gold pairs that were predicted."""
    gold = sum(g for _, g in rows)
    return sum(pred and g for pred, g in rows) / gold if gold else 0.0


def dedupe_metrics(
    clusters: Sequence[Sequence[str]], gold_groups: Sequence[Sequence[str]]
) -> DedupeMetrics:
    """Precision and recall of cluster-implied pairs against gold-group pairs, with CIs."""
    predicted, gold = implied_pairs(clusters), implied_pairs(gold_groups)
    groups = connected_pair_groups(predicted, gold)
    multi = [cluster for cluster in clusters if len(cluster) > 1]
    return DedupeMetrics(
        clusters=len(multi),
        largest_cluster=max((len(cluster) for cluster in multi), default=0),
        predicted_pairs=len(predicted),
        gold_pairs=len(gold),
        true_pairs=len(predicted & gold),
        precision=bootstrap_interval(groups, pair_precision),
        recall=bootstrap_interval(groups, pair_recall),
    )
