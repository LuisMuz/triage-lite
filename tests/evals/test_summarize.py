from pathlib import Path

import pytest

from evals.dataset import write_jsonl
from evals.harness import EvalError
from evals.summarize import (
    SummarizeEvalResult,
    main,
    offending,
    problem_kind,
    render_markdown,
    run_summarize_eval,
    write_result,
)
from tests.pipeline.conftest import write_report
from tests.pipeline.test_aggregates import CLUSTERS, INCIDENTS, RESULTS
from triagelite.domain.enums import ReportSource
from triagelite.domain.errors import LLMRateLimitError
from triagelite.llm.fake import FakeLLMClient, ScriptStep
from triagelite.settings import Settings

REPO = Path(__file__).parents[2]
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")
GOOD = write_report("{{total.incidents}} incidents arrived.")
NUMBER_WORD = write_report("Three incidents arrived, tres incidentes.")


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "sample-0000abcd"
    folder.mkdir()
    write_jsonl(folder / "incidents.jsonl", INCIDENTS)
    write_jsonl(folder / "classifications.jsonl", RESULTS)
    write_jsonl(folder / "clusters.jsonl", CLUSTERS)
    return folder


def evaluate(run_dir: Path, script: list[ScriptStep], repeat: int = 1) -> SummarizeEvalResult:
    return run_summarize_eval(
        run_dir=run_dir,
        settings=SETTINGS,
        client=FakeLLMClient(script),
        version=2,
        repeat=repeat,
        sleep=lambda _: None,
    )


def test_each_repeat_writes_both_languages(run_dir: Path) -> None:
    result = evaluate(run_dir, [GOOD] * 4, repeat=2)

    assert [(t.repeat, t.lang) for t in result.trials] == [
        (1, "es"),
        (1, "en"),
        (2, "es"),
        (2, "en"),
    ]
    assert {t.source for t in result.trials} == {ReportSource.MODEL}
    assert result.prompt == "summarize/v2"
    assert result.cost_usd > 0
    assert "| es | 0/2 (0%) | 2/2 (100%) | 0/2 (0%) |" in render_markdown(result)


def test_a_draft_rejected_twice_is_a_template_fallback(run_dir: Path) -> None:
    result = evaluate(run_dir, [GOOD, NUMBER_WORD, NUMBER_WORD])

    english = result.trials[1]
    assert (english.source, english.drafts, english.calls) == (ReportSource.TEMPLATE, 2, 2)
    assert english.fallback_reason == english.problems[-1]
    report = render_markdown(result)
    assert "| en | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) |" in report
    assert "- number word: 2" in report
    assert "- number word 'three': 2" in report
    assert "Fallbacks not caused by grounding" not in report


def test_a_draft_fixed_on_the_re_ask_counts_as_passed_on_re_ask(run_dir: Path) -> None:
    result = evaluate(run_dir, [NUMBER_WORD, GOOD, GOOD])

    spanish = result.trials[0]
    assert (spanish.source, spanish.drafts, spanish.fallback_reason) == (ReportSource.MODEL, 2, [])
    assert "| es | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) |" in render_markdown(result)


def test_a_fallback_from_throttling_is_listed_apart(run_dir: Path) -> None:
    throttled: list[ScriptStep] = [LLMRateLimitError("429")] * 4

    result = evaluate(run_dir, [*throttled, GOOD])

    assert result.trials[0].problems == []
    assert "Fallbacks not caused by grounding" in render_markdown(result)


def test_the_reports_to_review_have_the_numbers_filled_in(run_dir: Path) -> None:
    result = evaluate(run_dir, [GOOD, GOOD])

    assert "5 incidents arrived." in render_markdown(result)


@pytest.mark.parametrize(
    ("problem", "kind", "token"),
    [
        ("number word 'three' in section 'Overview': use a placeholder", "number word", "three"),
        ("bare number '3' in section 'Overview': write every number", "bare number", "3"),
        (
            "unknown placeholder {{total.bugs}} in section 'Overview': use",
            "unknown placeholder",
            "total.bugs",
        ),
        (
            "malformed placeholder in section 'Overview': write exactly",
            "malformed placeholder",
            None,
        ),
        (
            "inc-0099 in section 'Overview' is not an incident in <incidents>",
            "unknown incident",
            None,
        ),
        ("something new", "other", None),
    ],
)
def test_problems_are_grouped_by_the_rule_they_broke(
    problem: str, kind: str, token: str | None
) -> None:
    assert (problem_kind(problem), offending(problem)) == (kind, token)


def test_a_run_folder_without_its_files_is_refused(tmp_path: Path) -> None:
    with pytest.raises(EvalError, match=r"incidents\.jsonl"):
        evaluate(tmp_path, [])


def test_results_are_named_after_prompt_model_batch_and_repeats(
    run_dir: Path, tmp_path: Path
) -> None:
    result = evaluate(run_dir, [GOOD, GOOD])

    json_path, md_path = write_result(result, tmp_path / "results")

    assert json_path.name.endswith("-summarize-v2-claude-haiku-4-5-sample-0000abcd-x1.json")
    assert SummarizeEvalResult.model_validate_json(json_path.read_text()) == result
    assert md_path.read_text().startswith("# Summarize eval: summarize/v2 on sample-0000abcd")


@pytest.mark.parametrize(
    "argv", [["--prompt", "classify/v3"], ["--repeat", "0"], ["--prompt", "nope"]]
)
def test_bad_arguments_fail_before_any_call(run_dir: Path, argv: list[str]) -> None:
    assert main(["--run", str(run_dir), *argv]) == 1
