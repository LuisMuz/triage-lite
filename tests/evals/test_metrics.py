import pytest

from evals.dataset import EvalLabel
from evals.metrics import (
    ItemPrediction,
    bootstrap_interval,
    calibration_table,
    compute_metrics,
    confusion_matrix,
    connected_pair_groups,
    dedupe_metrics,
    first_try_rate,
    implied_pairs,
    macro_f1,
    pair_precision,
    pair_recall,
    per_class_metrics,
)
from triagelite.domain.enums import CallStatus, Severity, Stage
from triagelite.domain.models import LLMCallRecord

C, H, M, L = Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW


def record(
    attempt: int = 1, status: CallStatus = CallStatus.OK, latency: int = 100
) -> LLMCallRecord:
    return LLMCallRecord(
        call_id="c",
        stage=Stage.CLASSIFY,
        model_id="m",
        prompt_version="classify/v1",
        input_tokens=1000,
        output_tokens=100,
        cost_usd=0.01,
        latency_ms=latency,
        stop_reason="tool_use",
        attempt=attempt,
        status=status,
        error_type=None if status is CallStatus.OK else "LLMOutputValidationError",
    )


def gold(external_id: str, severity: Severity, lang: str = "en") -> EvalLabel:
    return EvalLabel.model_validate(
        {
            "external_id": external_id,
            "lang": lang,
            "severity": severity,
            "category": "functional",
            "component": "cart",
            "source": "synthetic",
            "split": "tuning",
        }
    )


def predict(
    external_id: str,
    severity: Severity | None,
    *,
    confidence: float | None = 0.9,
    repeat: int = 0,
    component: str = "cart",
    lang: str = "en",
) -> ItemPrediction:
    return ItemPrediction.model_validate(
        {
            "external_id": external_id,
            "repeat": repeat,
            "title": "t",
            "detected_lang": lang,
            "severity": severity,
            "category": "functional" if severity else None,
            "component": component if severity else None,
            "confidence": confidence if severity else None,
        }
    )


class TestF1:
    def test_per_class_by_hand(self) -> None:
        pairs = [(C, C), (C, H), (H, H), (H, H), (M, None)]

        metrics = per_class_metrics(pairs)

        assert metrics[C].precision == 1.0
        assert metrics[C].recall == 0.5
        assert metrics[C].f1 == pytest.approx(2 / 3)
        assert metrics[H].precision == pytest.approx(2 / 3)
        assert metrics[H].recall == 1.0
        assert metrics[M].f1 == 0.0
        assert metrics[M].support == 1
        assert metrics[L].support == 0

    def test_macro_averages_only_classes_present_in_gold(self) -> None:
        pairs = [(C, C), (H, H)]

        assert macro_f1(pairs) == 1.0

    def test_macro_f1_punishes_a_missed_rare_class(self) -> None:
        pairs = [(H, H)] * 9 + [(C, H)]

        assert macro_f1(pairs) == pytest.approx((0.0 + 2 * 0.9 / 1.9) / 2)

    def test_empty(self) -> None:
        assert macro_f1([]) == 0.0


class TestBootstrap:
    def test_is_reproducible_and_brackets_the_estimate(self) -> None:
        groups = [[value] for value in [1, 0, 1, 1, 0, 1, 1, 1, 0, 1]]

        def mean(rows: list[int]) -> float:
            return sum(rows) / len(rows)

        first = bootstrap_interval(groups, mean)
        second = bootstrap_interval(groups, mean)

        assert first == second
        assert first.value == pytest.approx(0.7)
        assert first.low < 0.7 < first.high

    def test_constant_data_has_zero_width(self) -> None:
        interval = bootstrap_interval([[1], [1], [1]], lambda rows: float(sum(rows) / len(rows)))

        assert interval.low == interval.high == 1.0

    def test_no_groups(self) -> None:
        interval = bootstrap_interval([], lambda rows: 0.5)

        assert (interval.value, interval.low, interval.high) == (0.5, 0.5, 0.5)


def test_calibration_bins_include_one_in_the_top_bin() -> None:
    table = calibration_table([(0.95, True), (1.0, False), (0.1, True)])

    assert [b.count for b in table] == [1, 0, 0, 0, 2]
    assert table[4].accuracy == 0.5
    assert table[1].mean_confidence is None


def test_confusion_counts_needs_manual_as_its_own_column() -> None:
    matrix = confusion_matrix([(C, C), (C, None), (L, H)])

    assert matrix["critical"]["critical"] == 1
    assert matrix["critical"]["needs_manual"] == 1
    assert matrix["low"]["high"] == 1


def test_first_try_rate_looks_only_at_first_attempts() -> None:
    records = [record(1), record(1, CallStatus.VALIDATION_ERROR), record(2), record(1)]

    assert first_try_rate(records) == pytest.approx(2 / 3)
    assert first_try_rate([]) == 0.0


def test_compute_metrics_end_to_end() -> None:
    labels = {"a": gold("a", C), "b": gold("b", H, lang="es"), "c": gold("c", L)}
    predictions = [
        predict("a", C, confidence=0.95),
        predict("b", H, confidence=0.6, lang="en"),
        predict("c", None),
        predict("a", H, confidence=0.8, repeat=1, component="checkout"),
    ]

    metrics = compute_metrics(labels, predictions, [record(latency=100), record(latency=300)])

    assert (metrics.items, metrics.predictions) == (3, 4)
    assert metrics.severity_accuracy == 0.5
    assert metrics.needs_manual_rate == 0.25
    assert metrics.component_accuracy == 0.5
    assert metrics.language_accuracy == 0.75
    assert metrics.confident_share == 0.5
    assert metrics.confident_accuracy == 0.5
    assert metrics.cost_per_100_incidents_usd == pytest.approx(0.02 / 4 * 100)
    assert metrics.latency_p50_ms == 200
    assert metrics.severity_macro_f1.low <= metrics.severity_macro_f1.value
    assert metrics.confusion["low"]["needs_manual"] == 1


def fs(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


class TestDedupeMetrics:
    def test_a_cluster_implies_every_pair_inside_it(self) -> None:
        assert implied_pairs([["a", "b", "c"], ["d"]]) == {fs("a", "b"), fs("a", "c"), fs("b", "c")}

    def test_precision_and_recall_on_implied_pairs(self) -> None:
        metrics = dedupe_metrics([["a", "b", "c"], ["d"], ["e"]], [["a", "b"], ["d", "e"]])

        assert (metrics.predicted_pairs, metrics.gold_pairs, metrics.true_pairs) == (3, 2, 1)
        assert metrics.precision.value == pytest.approx(1 / 3)
        assert metrics.recall.value == pytest.approx(1 / 2)
        assert (metrics.clusters, metrics.largest_cluster) == (1, 3)
        assert metrics.precision.low <= metrics.precision.value <= metrics.precision.high

    def test_nothing_predicted_or_gold_is_all_zero(self) -> None:
        metrics = dedupe_metrics([["a"], ["b"]], [])

        assert (metrics.predicted_pairs, metrics.clusters, metrics.largest_cluster) == (0, 0, 0)
        assert metrics.precision.value == metrics.recall.value == 0.0

    def test_pairs_sharing_incidents_are_resampled_together(self) -> None:
        predicted = {fs("a", "b"), fs("b", "c"), fs("x", "y")}
        gold = {fs("a", "b"), fs("p", "q")}

        groups = connected_pair_groups(predicted, gold)

        assert sorted(map(len, groups)) == [1, 1, 2]
        assert [(True, True), (True, False)] in groups

    def test_pair_rates_handle_empty_denominators(self) -> None:
        assert pair_precision([(False, True)]) == 0.0
        assert pair_recall([(True, False)]) == 0.0
