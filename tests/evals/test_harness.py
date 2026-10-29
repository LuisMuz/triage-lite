import json
from pathlib import Path

import pytest

from evals.build import build
from evals.dataset import Split
from evals.harness import (
    EvalError,
    EvalResult,
    main,
    model_slug,
    parse_prompt_id,
    run_eval,
    write_result,
)
from tests.evals.test_dataset import base_rows, write_work
from tests.pipeline.conftest import answer_all
from triagelite.domain.enums import Stage
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.fake import FakeLLMClient
from triagelite.settings import Settings

REPO = Path(__file__).parents[2]
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")


@pytest.fixture
def datasets(tmp_path: Path) -> Path:
    taxonomy = Taxonomy.from_toml((REPO / "config" / "taxonomy.toml").read_text(encoding="utf-8"))
    root = write_work(tmp_path, base_rows())
    build("seed-test", root / "work", root / "datasets", taxonomy)
    return root / "datasets"


def run(datasets: Path, cache: Path, client: FakeLLMClient, repeat: int = 1) -> EvalResult:
    return run_eval(
        dataset="seed-test",
        split=Split.TUNING,
        prompt_id="classify/v1",
        repeat=repeat,
        settings=SETTINGS,
        client=client,
        datasets_dir=datasets,
        cache_dir=cache,
        sleep=lambda _: None,
    )


def test_runs_the_tuning_split_through_the_real_pipeline(datasets: Path, tmp_path: Path) -> None:
    client = FakeLLMClient([answer_all()])

    result = run(datasets, tmp_path / "cache", client)

    assert result.metrics.items == 6
    assert {p.external_id for p in result.predictions} == {lb.external_id for lb in result.labels}
    assert all(label.split is Split.TUNING for label in result.labels)
    assert result.fresh_calls == 1
    assert result.cached_chunks == 0
    assert result.metrics.llm_calls == 1
    assert len(client.requests) == 1


def test_second_run_is_served_from_cache(datasets: Path, tmp_path: Path) -> None:
    first = run(datasets, tmp_path / "cache", FakeLLMClient([answer_all()]))
    client = FakeLLMClient([])

    second = run(datasets, tmp_path / "cache", client)

    assert client.requests == []
    assert second.fresh_calls == 0
    assert second.cached_chunks == 1
    assert second.metrics == first.metrics


def test_each_repeat_is_a_separate_call(datasets: Path, tmp_path: Path) -> None:
    client = FakeLLMClient([answer_all(), answer_all()])

    result = run(datasets, tmp_path / "cache", client, repeat=2)

    assert len(client.requests) == 2
    assert result.metrics.predictions == 12
    assert result.metrics.items == 6


def test_tampered_dataset_is_refused(datasets: Path, tmp_path: Path) -> None:
    labels = datasets / "seed-test" / "labels.jsonl"
    labels.write_text(labels.read_text() + "\n", encoding="utf-8")

    with pytest.raises(EvalError, match="sha256 mismatch"):
        run(datasets, tmp_path / "cache", FakeLLMClient([]))


def test_write_result_produces_json_and_markdown(datasets: Path, tmp_path: Path) -> None:
    result = run(datasets, tmp_path / "cache", FakeLLMClient([answer_all()]))

    json_path, md_path = write_result(result, tmp_path / "results")

    assert json_path.name.endswith("-classify-v1-claude-haiku-4-5-tuning.json")
    assert json.loads(json_path.read_text())["metrics"]["items"] == 6
    report = md_path.read_text()
    assert "severity macro-F1 [95% CI]" in report
    assert "## Errors" in report
    assert "severity" in report


def test_prompt_id_parsing() -> None:
    assert parse_prompt_id("classify/v12") == (Stage.CLASSIFY, 12)
    with pytest.raises(EvalError, match="classify/v1"):
        parse_prompt_id("classify-v1")


@pytest.mark.parametrize(
    ("model_id", "slug"),
    [
        ("global.anthropic.claude-haiku-4-5-20251001-v1:0", "claude-haiku-4-5"),
        ("global.anthropic.claude-haiku-5-5", "claude-haiku-5-5"),
        ("amazon.nova-lite-v1:0", "amazon-nova-lite-v1-0"),
    ],
)
def test_model_slug(model_id: str, slug: str) -> None:
    assert model_slug(model_id) == slug


def test_holdout_needs_explicit_confirmation() -> None:
    assert main(["--split", "holdout"]) == 1


def test_repeat_must_be_positive() -> None:
    assert main(["--repeat", "0"]) == 1
