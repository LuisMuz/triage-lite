"""Markdown report for one eval run: headline row, breakdowns, and every error to review."""

from collections.abc import Mapping, Sequence

from evals.dataset import EvalLabel
from evals.metrics import ClassifyMetrics, ItemPrediction

LABEL_FIELDS = ("severity", "category", "component")


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def headline_row(prompt: str, model_id: str, split: str, m: ClassifyMetrics) -> str:
    """The one-line summary that goes into `evals/results/SUMMARY.md`."""
    f1 = m.severity_macro_f1
    return (
        f"| {prompt} | {model_id} | {split} "
        f"| **{f1.value:.3f}** [{f1.low:.3f}-{f1.high:.3f}] | {_pct(m.severity_accuracy)} "
        f"| {_pct(m.component_accuracy)} | {_pct(m.category_accuracy)} "
        f"| {_pct(m.confident_accuracy)} ({_pct(m.confident_share)}) "
        f"| {_pct(m.schema_valid_first_try)} | {_pct(m.needs_manual_rate)} "
        f"| ${m.cost_per_100_incidents_usd:.3f} | {m.latency_p50_ms:.0f} / {m.latency_p95_ms:.0f} |"
    )


HEADLINE_HEADER = (
    "| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc "
    "| conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|"
)


def error_lines(
    predictions: Sequence[ItemPrediction], labels: Mapping[str, EvalLabel]
) -> list[str]:
    """One bullet per prediction with any wrong label, with the model's own rationale."""
    lines: list[str] = []
    for p in predictions:
        gold = labels[p.external_id]
        wrong = [
            f"{field} {getattr(gold, field)}→{getattr(p, field) or 'none'}"
            for field in LABEL_FIELDS
            if getattr(p, field) != getattr(gold, field)
        ]
        if wrong:
            lines += [
                f"- **{p.external_id}** ({gold.lang}, r{p.repeat}) {p.title} — "
                f"{'; '.join(wrong)} · conf {_num(p.confidence)}",
                f"  - {p.rationale or p.reason or ''}",
            ]
    return lines or ["None."]


def render_markdown(
    *,
    title: str,
    subtitle: str,
    prompt: str,
    model_id: str,
    split: str,
    metrics: ClassifyMetrics,
    predictions: Sequence[ItemPrediction],
    labels: Mapping[str, EvalLabel],
) -> str:
    """Human-readable report; the JSON next to it is the source of truth."""
    m = metrics
    columns = list(next(iter(m.confusion.values())))
    lines = [
        f"# {title}",
        "",
        subtitle,
        "",
        HEADLINE_HEADER,
        headline_row(prompt, model_id, split, m),
        "",
        f"Language detection accuracy: {_pct(m.language_accuracy)}.",
        "",
        "## Severity per class",
        "",
        "| class | precision | recall | F1 | support |",
        "|---|---|---|---|---|",
        *(
            f"| {s} | {c.precision:.2f} | {c.recall:.2f} | {c.f1:.2f} | {c.support} |"
            for s, c in m.per_class.items()
        ),
        "",
        "## Confusion (rows = gold, columns = predicted)",
        "",
        "| gold \\ pred | " + " | ".join(columns) + " |",
        "|---" * (len(columns) + 1) + "|",
        *(
            f"| {gold} | " + " | ".join(map(str, row.values())) + " |"
            for gold, row in m.confusion.items()
        ),
        "",
        "## Calibration (severity correct, by stated confidence)",
        "",
        "| confidence | count | mean confidence | accuracy |",
        "|---|---|---|---|",
        *(
            f"| {b.lower:.1f}-{b.upper:.1f} | {b.count} | {_num(b.mean_confidence)} "
            f"| {_pct(b.accuracy)} |"
            for b in m.calibration
        ),
        "",
        "## Errors (any label wrong, or needs_manual)",
        "",
        *error_lines(predictions, labels),
    ]
    return "\n".join(lines) + "\n"
