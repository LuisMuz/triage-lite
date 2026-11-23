"""`python -m evals.summarize --run runs/<batch_id>`: how often each report language falls back.

Re-runs only the summarize stage on a finished local run, so the facts stay fixed and the
differences between repeats come from the model and the prompt.
"""

import argparse
import re
import sys
import time
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field, NonNegativeFloat, NonNegativeInt, PositiveInt

from evals.dataset import read_jsonl, write_json
from evals.harness import RESULTS_DIR, EvalError, model_slug, parse_prompt_id
from triagelite.cli import CLASSIFICATIONS_FILE, CLUSTERS_FILE, INCIDENTS_FILE, ROW_ERRORS_FILE
from triagelite.domain.enums import ReportSource, Stage
from triagelite.domain.models import (
    DuplicateCluster,
    Incident,
    IncidentClassification,
    Language,
    LLMCallRecord,
    NonEmptyStr,
    ReportSection,
    RowError,
    StrictModel,
)
from triagelite.llm.bedrock import BedrockLLMClient
from triagelite.llm.client import LLMClient
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.aggregates import ReportFacts, compute_facts
from triagelite.pipeline.backoff import Sleep
from triagelite.pipeline.stages import REPORT_LANGUAGES, render_draft, summarize_with_backoff
from triagelite.pipeline.summarize import ReportDraft
from triagelite.settings import (
    Settings,
    get_settings,
    load_llm_config,
    load_pipeline_config,
    load_stage_prompt,
)

REVIEW_REPORTS = 3
BROKEN_SENTENCES = 20
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")
QUOTED = re.compile(r"^[a-z ]+ '([^']*)'")
BRACED = re.compile(r"\{\{([^}]*)\}\}")
PROBLEM_KINDS = {
    "number word": re.compile(r"^number word "),
    "bare number": re.compile(r"^bare number "),
    "unknown placeholder": re.compile(r"^unknown placeholder "),
    "malformed placeholder": re.compile(r"^malformed placeholder "),
    "unknown incident": re.compile(r" is not an incident in "),
    "wrong language": re.compile(r"^lang must be "),
    "schema": re.compile(r"^model output failed validation"),
}


class Trial(StrictModel):
    """One language written once: who wrote the kept text and why model drafts were rejected."""

    repeat: PositiveInt
    lang: Language
    source: ReportSource
    drafts: NonNegativeInt
    problems: list[list[NonEmptyStr]]
    fallback_reason: list[NonEmptyStr]
    rejected: list[list[ReportSection]] = Field(default_factory=list)
    calls: NonNegativeInt
    cost_usd: NonNegativeFloat
    report: str


class SummarizeEvalResult(StrictModel):
    """Every trial of one prompt on one run's facts."""

    created_at: NonEmptyStr
    batch_id: NonEmptyStr
    prompt: NonEmptyStr
    model_id: NonEmptyStr
    repeat: PositiveInt
    trials: list[Trial]

    @property
    def cost_usd(self) -> float:
        """Total spent on model calls."""
        return sum(trial.cost_usd for trial in self.trials)


def load_facts(run_dir: Path, settings: Settings) -> ReportFacts:
    """Recompute the report facts of a finished local run with the current code."""
    for name in (INCIDENTS_FILE, CLASSIFICATIONS_FILE, CLUSTERS_FILE):
        if not (run_dir / name).is_file():
            raise EvalError(f"{run_dir} has no {name}; run `make run` first")
    row_errors = run_dir / ROW_ERRORS_FILE
    return compute_facts(
        read_jsonl(run_dir / INCIDENTS_FILE, Incident),
        read_jsonl(run_dir / CLASSIFICATIONS_FILE, IncidentClassification),
        read_jsonl(run_dir / CLUSTERS_FILE, DuplicateCluster),
        len(read_jsonl(row_errors, RowError)) if row_errors.is_file() else 0,
        load_pipeline_config(settings).report,
    )


def problem_kind(problem: str) -> str:
    """The grounding rule a problem broke, or `other`."""
    return next(
        (kind for kind, pattern in PROBLEM_KINDS.items() if pattern.search(problem)), "other"
    )


def offending(problem: str) -> str | None:
    """The word, number or key a grounding problem is about."""
    kind = problem_kind(problem)
    if kind == "unknown placeholder":
        match = BRACED.search(problem)
    elif kind in {"number word", "bare number"}:
        match = QUOTED.search(problem)
    else:
        match = None
    return match[1] if match else None


def sentences_with(text: str, token: str) -> list[str]:
    """The sentences of `text` that contain `token` as a whole word, ignoring case."""
    word = re.compile(rf"(?<!\w){re.escape(token)}(?!\w)", re.IGNORECASE)
    return [
        sentence.strip()
        for sentence in SENTENCE_END.split(text)
        if sentence.strip() and word.search(sentence)
    ]


def broken_sentences(trial: Trial) -> list[str]:
    """`<lang>, repeat <n>, '<token>': <sentence>` for every number a rejected draft wrote."""
    found: list[str] = []
    for sections, problems in zip(trial.rejected, trial.problems, strict=False):
        tokens = dict.fromkeys(
            token
            for problem in problems
            if problem_kind(problem) in {"number word", "bare number"}
            and (token := offending(problem)) is not None
        )
        for token in tokens:
            for section in sections:
                for text in (section.heading, section.body):
                    found += [
                        f"{trial.lang}, repeat {trial.repeat}, '{token}': {sentence}"
                        for sentence in sentences_with(text, token)
                    ]
    return list(dict.fromkeys(found))


def drafts_of(draft: ReportDraft) -> int:
    """Model drafts that passed schema validation, kept or rejected."""
    return len(draft.rejected) + (draft.source is ReportSource.MODEL)


def run_summarize_eval(
    *,
    run_dir: Path,
    settings: Settings,
    client: LLMClient,
    version: int | None,
    repeat: int,
    sleep: Sleep = time.sleep,
) -> SummarizeEvalResult:
    """Write both languages `repeat` times from the same facts."""
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    prompt = load_stage_prompt(settings, Stage.SUMMARIZE, version or pipeline.prompts.summarize)
    facts = load_facts(run_dir, settings)
    batch_id = run_dir.name
    records: list[LLMCallRecord] = []
    llm = StructuredLLM(client, models, prices, recorder=records.append)
    trials = []
    for index in range(1, repeat + 1):
        for lang in REPORT_LANGUAGES:
            first = len(records)
            draft = summarize_with_backoff(
                llm,
                prompt,
                facts,
                lang,
                pipeline.report,
                batch_id=batch_id,
                retry=pipeline.chunk_retry,
                sleep=sleep,
            )
            made = records[first:]
            trials.append(
                Trial(
                    repeat=index,
                    lang=lang,
                    source=draft.source,
                    drafts=drafts_of(draft),
                    problems=[rejected.problems for rejected in draft.rejected],
                    fallback_reason=draft.problems if draft.source is ReportSource.TEMPLATE else [],
                    rejected=[rejected.sections for rejected in draft.rejected],
                    calls=len(made),
                    cost_usd=sum(record.cost_usd for record in made),
                    report=render_draft(
                        draft,
                        facts,
                        batch_id=batch_id,
                        models=models,
                        prompt=prompt,
                        config=pipeline.report,
                    ),
                )
            )
    return SummarizeEvalResult(
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        batch_id=batch_id,
        prompt=prompt.id,
        model_id=models.for_stage(Stage.SUMMARIZE).model_id,
        repeat=repeat,
        trials=trials,
    )


def _rate(part: int, whole: int) -> str:
    return f"{part}/{whole} ({part / whole:.0%})" if whole else "0/0"


def render_markdown(result: SummarizeEvalResult) -> str:
    """Fallback and first-try rates per language, what broke, and reports to read."""
    lines = [
        f"# Summarize eval: {result.prompt} on {result.batch_id}",
        "",
        f"Model `{result.model_id}`, {result.repeat} repeats per language, "
        f"{sum(t.calls for t in result.trials)} calls, ${result.cost_usd:.3f}. "
        f"Created {result.created_at}.",
        "",
        "| lang | template fallbacks | passed on first draft | passed on re-ask |",
        "|---|---|---|---|",
    ]
    for lang in REPORT_LANGUAGES:
        trials = [t for t in result.trials if t.lang == lang]
        model = [t for t in trials if t.source is ReportSource.MODEL]
        first = sum(t.drafts == 1 and not t.problems for t in model)
        lines.append(
            f"| {lang} | {_rate(len(trials) - len(model), len(trials))} "
            f"| {_rate(first, len(trials))} | {_rate(len(model) - first, len(trials))} |"
        )
    problems = [problem for t in result.trials for draft in t.problems for problem in draft]
    kinds = Counter(problem_kind(problem) for problem in problems)
    tokens = Counter(
        f"{problem_kind(problem)} '{token}'"
        for problem in problems
        if (token := offending(problem)) is not None
    )
    other_fallbacks = [
        reason
        for t in result.trials
        if t.fallback_reason and (not t.problems or t.fallback_reason != t.problems[-1])
        for reason in t.fallback_reason
    ]
    lines += ["", "## Problems in rejected drafts", ""]
    if not problems:
        lines.append("None.")
    lines += [f"- {kind}: {count}" for kind, count in kinds.most_common()]
    if tokens:
        lines += ["", "Most frequent:", ""]
        lines += [f"- {token}: {count}" for token, count in tokens.most_common(10)]
    if other_fallbacks:
        lines += ["", "Fallbacks not caused by grounding:", ""]
        lines += [f"- {reason}" for reason in other_fallbacks]
    broken = [sentence for t in result.trials for sentence in broken_sentences(t)]
    if broken:
        lines += ["", "## Sentences that broke a rule", ""]
        lines += [f"- {sentence}" for sentence in broken[:BROKEN_SENTENCES]]
        if len(broken) > BROKEN_SENTENCES:
            lines.append(f"- … and {len(broken) - BROKEN_SENTENCES} more in the JSON result")
    lines += [
        "",
        "## Reports to review",
        "",
        "Read these for claims the facts don't support; the grounding check only covers numbers "
        "and incident IDs.",
    ]
    for lang in REPORT_LANGUAGES:
        kept = [t for t in result.trials if t.lang == lang and t.source is ReportSource.MODEL]
        for trial in kept[:REVIEW_REPORTS]:
            lines += ["", f"### {lang}, repeat {trial.repeat}", "", "````markdown"]
            lines += [trial.report.rstrip(), "````"]
    return "\n".join(lines) + "\n"


def result_stem(result: SummarizeEvalResult) -> str:
    """`<date>-summarize-v2-<model>-<batch_id>-x10`."""
    return (
        f"{result.created_at[:10]}-{result.prompt.replace('/', '-')}-"
        f"{model_slug(result.model_id)}-{result.batch_id}-x{result.repeat}"
    )


def write_result(result: SummarizeEvalResult, results_dir: Path = RESULTS_DIR) -> tuple[Path, Path]:
    """Write the JSON result and its Markdown report next to each other."""
    results_dir.mkdir(parents=True, exist_ok=True)
    stem = result_stem(result)
    json_path = results_dir / f"{stem}.json"
    md_path = results_dir / f"{stem}.md"
    write_json(json_path, result)
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return json_path, md_path


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.summarize --run runs/sample-497c47c8 --repeat 10`."""
    parser = argparse.ArgumentParser(prog="python -m evals.summarize", description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="a finished local run folder")
    parser.add_argument("--prompt", default=None, help="e.g. summarize/v3 (default: config)")
    parser.add_argument("--repeat", type=int, default=10)
    args = parser.parse_args(argv)
    settings = get_settings()
    models, _ = load_llm_config(settings)
    try:
        version = None
        if args.prompt:
            stage, version = parse_prompt_id(args.prompt)
            if stage is not Stage.SUMMARIZE:
                raise EvalError(f"--prompt must be a summarize prompt, got {args.prompt!r}")
        if args.repeat < 1:
            raise EvalError("--repeat must be at least 1")
        result = run_summarize_eval(
            run_dir=args.run,
            settings=settings,
            client=BedrockLLMClient.from_settings(settings, models.client.timeout_seconds),
            version=version,
            repeat=args.repeat,
        )
    except EvalError as error:
        sys.stderr.write(f"summarize eval failed: {error}\n")
        return 1
    json_path, md_path = write_result(result)
    sys.stdout.write(f"{md_path}\n{json_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
