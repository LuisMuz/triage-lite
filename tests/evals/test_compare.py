from collections.abc import Sequence
from pathlib import Path

import pytest

from evals.compare import (
    EXIT_REGRESSION,
    CompareError,
    PairedDelta,
    Verdict,
    compare,
    main,
    render_markdown,
    verdict,
    write_comparison,
)
from evals.dataset import EvalLabel, Source, Split
from evals.harness import EvalResult
from evals.metrics import Interval, ItemPrediction, compute_metrics
from tests.evals.test_metrics import record
from triagelite.domain.enums import Category, Severity
from triagelite.llm.config import StageModelConfig

C, H, M, L = Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW
GOLD = [C, H, M, L] * 5
MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


def labels(golds: Sequence[Severity] = GOLD) -> list[EvalLabel]:
    return [
        EvalLabel(
            external_id=f"item-{index:02d}",
            lang="en",
            severity=severity,
            category=Category.FUNCTIONAL,
            component="checkout",
            source=Source.HAND_WRITTEN,
            split=Split.TUNING,
        )
        for index, severity in enumerate(golds)
    ]


def result(
    runs: Sequence[Sequence[Severity | None]],
    *,
    prompt: str = "classify/v1",
    cost: float = 0.01,
    sha: str = "abc",
    split: Split = Split.TUNING,
    component: str = "checkout",
) -> EvalResult:
    gold = labels()
    predictions = [
        ItemPrediction(
            external_id=label.external_id,
            repeat=repeat,
            title=f"title {label.external_id}",
            detected_lang="en",
            severity=severity,
            category=Category.FUNCTIONAL if severity else None,
            component=component if severity else None,
            confidence=0.9 if severity else None,
        )
        for repeat, severities in enumerate(runs)
        for label, severity in zip(gold, severities, strict=True)
    ]
    records = [record().model_copy(update={"cost_usd": cost})]
    return EvalResult(
        created_at="2026-10-29T10:00:00+00:00",
        dataset="seed-test",
        dataset_labels_sha256=sha,
        split=split,
        prompt=prompt,
        model_id=MODEL,
        model=StageModelConfig(model_id=MODEL, api="messages", max_tokens=4096),
        repeat=len(runs),
        chunk_size=10,
        fresh_calls=1,
        cached_chunks=0,
        metrics=compute_metrics({lb.external_id: lb for lb in gold}, predictions, records),
        labels=gold,
        predictions=predictions,
    )


def with_errors(wrong: int) -> list[Severity | None]:
    """Gold severities with the first `wrong` medium items predicted high."""
    out: list[Severity | None] = list(GOLD)
    flipped = 0
    for index, severity in enumerate(GOLD):
        if severity is M and flipped < wrong:
            out[index] = H
            flipped += 1
    return out


def test_identical_runs_have_zero_delta() -> None:
    base = result([with_errors(2)] * 3)

    comparison = compare(base, result([with_errors(2)] * 3, prompt="classify/v2"))

    assert comparison.severity_macro_f1.delta == Interval(value=0.0, low=0.0, high=0.0)
    assert comparison.verdict is Verdict.NO_SIGNIFICANT_DIFFERENCE
    assert comparison.fixed == comparison.broken == []
    assert comparison.items == 20


def test_fixing_every_medium_item_is_an_improvement() -> None:
    comparison = compare(
        result([with_errors(5)] * 3), result([with_errors(0)] * 3, prompt="classify/v2")
    )

    assert comparison.severity_macro_f1.delta.low > 0
    assert comparison.severity_accuracy.delta.value == pytest.approx(5 / 20)
    assert comparison.verdict is Verdict.IMPROVEMENT
    assert [(c.external_id, c.field) for c in comparison.fixed] == [
        (f"item-{i:02d}", "severity") for i in (2, 6, 10, 14, 18)
    ]
    assert comparison.broken == []


def test_breaking_items_is_a_regression_and_lists_them() -> None:
    comparison = compare(
        result([with_errors(0)] * 3), result([with_errors(5)] * 3, prompt="classify/v2")
    )

    assert comparison.verdict is Verdict.REGRESSION
    assert len(comparison.broken) == 5
    assert comparison.broken[0].gold == "medium"
    assert comparison.broken[0].base_correct == 1.0
    assert comparison.broken[0].candidate_correct == 0.0


def test_majority_of_repeats_decides_fixed_or_broken() -> None:
    base = result([with_errors(1), with_errors(1), with_errors(0)])
    candidate = result([with_errors(0), with_errors(0), with_errors(1)], prompt="classify/v2")

    comparison = compare(base, candidate)

    assert [c.external_id for c in comparison.fixed] == ["item-02"]
    assert comparison.fixed[0].base_correct == pytest.approx(1 / 3)
    assert comparison.fixed[0].candidate_correct == pytest.approx(2 / 3)


def test_component_changes_are_reported_per_field() -> None:
    comparison = compare(result([GOLD], component="payments"), result([GOLD], prompt="classify/v2"))

    assert comparison.component_accuracy.delta.value == 1.0
    assert {c.field for c in comparison.fixed} == {"component"}


def test_needs_manual_counts_as_wrong() -> None:
    missing: list[Severity | None] = [None, *GOLD[1:]]

    comparison = compare(result([GOLD]), result([missing], prompt="classify/v2"))

    assert comparison.severity_accuracy.delta.value == pytest.approx(-1 / 20)
    assert [c.external_id for c in comparison.broken if c.field == "severity"] == ["item-00"]


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (Interval(value=0.04, low=0.01, high=0.08), Verdict.IMPROVEMENT),
        (Interval(value=-0.02, low=-0.04, high=-0.001), Verdict.REGRESSION),
        (Interval(value=-0.05, low=-0.12, high=0.02), Verdict.REGRESSION),
        (Interval(value=-0.04, low=-0.11, high=0.03), Verdict.NO_SIGNIFICANT_DIFFERENCE),
        (Interval(value=0.03, low=-0.02, high=0.08), Verdict.NO_SIGNIFICANT_DIFFERENCE),
    ],
)
def test_verdict_follows_tl08(delta: Interval, expected: Verdict) -> None:
    assert verdict(PairedDelta(base=0.7, candidate=0.7 + delta.value, delta=delta)) is expected


def test_cost_gate_fails_above_fifteen_percent() -> None:
    base = result([GOLD], cost=0.010)

    assert not compare(base, result([GOLD], cost=0.0115)).cost_gate_failed
    assert compare(base, result([GOLD], cost=0.0116)).cost_gate_failed


def test_different_labels_are_refused() -> None:
    with pytest.raises(CompareError, match="versions of the labels"):
        compare(result([GOLD]), result([GOLD], sha="def"))


def test_different_split_is_refused() -> None:
    with pytest.raises(CompareError, match="different data"):
        compare(result([GOLD]), result([GOLD], split=Split.HOLDOUT))


def test_different_items_are_refused() -> None:
    candidate = result([GOLD])
    candidate = candidate.model_copy(update={"predictions": candidate.predictions[1:]})

    with pytest.raises(CompareError, match="1 appear in only one run"):
        compare(result([GOLD]), candidate)


def test_markdown_shows_deltas_and_changes(tmp_path: Path) -> None:
    comparison = compare(
        result([with_errors(5)] * 3), result([with_errors(0)] * 3, prompt="classify/v2")
    )

    report = render_markdown(comparison)
    path = write_comparison(comparison, tmp_path)

    assert path.name == (
        "compare-classify-v2-claude-haiku-4-5-tuning-c10-x3-vs-"
        "classify-v1-claude-haiku-4-5-tuning-c10-x3.md"
    )
    assert path.read_text() == report
    assert "Verdict (severity macro-F1, TL-08): improvement" in report
    assert "## Fixed (5)" in report
    assert "## Broken (0)\n\nNone." in report
    assert "| severity accuracy | 0.750 | 1.000 | **+0.250**" in report


def test_markdown_flags_the_cost_gate() -> None:
    report = render_markdown(compare(result([GOLD]), result([GOLD], cost=0.02)))

    assert "Cost gate failed" in report


def test_main_writes_the_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base, candidate = tmp_path / "base.json", tmp_path / "candidate.json"
    base.write_text(result([with_errors(5)]).model_dump_json(), encoding="utf-8")
    candidate.write_text(
        result([with_errors(0)], prompt="classify/v2").model_dump_json(), encoding="utf-8"
    )

    assert main([str(base), str(candidate), "--results-dir", str(tmp_path / "out")]) == 0

    assert "improvement" in capsys.readouterr().out
    assert len(list((tmp_path / "out").glob("compare-*.md"))) == 1


def test_main_reports_incomparable_runs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base, candidate = tmp_path / "base.json", tmp_path / "candidate.json"
    base.write_text(result([GOLD]).model_dump_json(), encoding="utf-8")
    candidate.write_text(result([GOLD], sha="def").model_dump_json(), encoding="utf-8")

    assert main([str(base), str(candidate), "--results-dir", str(tmp_path)]) == 1

    assert "compare failed" in capsys.readouterr().err


def write_pair(tmp_path: Path, base: EvalResult, candidate: EvalResult) -> list[str]:
    base_path, candidate_path = tmp_path / "base.json", tmp_path / "candidate.json"
    base_path.write_text(base.model_dump_json(), encoding="utf-8")
    candidate_path.write_text(candidate.model_dump_json(), encoding="utf-8")
    return [str(base_path), str(candidate_path), "--results-dir", str(tmp_path / "out")]


@pytest.mark.parametrize(
    ("candidate", "code"),
    [
        (result([with_errors(0)], prompt="classify/v2"), 0),
        (result([with_errors(5)], prompt="classify/v2"), EXIT_REGRESSION),
        (result([with_errors(0)], prompt="classify/v2", cost=0.02), EXIT_REGRESSION),
    ],
)
def test_the_gate_fails_on_a_regression_or_a_cost_increase(
    tmp_path: Path, candidate: EvalResult, code: int
) -> None:
    args = write_pair(tmp_path, result([with_errors(0)]), candidate)

    assert main(args) == 0
    assert main([*args, "--fail-on-regression"]) == code
