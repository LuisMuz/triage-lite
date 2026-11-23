import json
from pathlib import Path

import pytest

from evals import harness
from evals.build import build
from evals.dataset import Split
from evals.harness import (
    EXIT_UNAVAILABLE,
    EvalError,
    EvalResult,
    EvalUnavailableError,
    code_fingerprint,
    main,
    model_slug,
    parse_prompt_id,
    run_eval,
    write_result,
)
from tests.evals.test_dataset import base_rows, write_work
from tests.pipeline.conftest import answer_all
from triagelite.domain.enums import Stage
from triagelite.domain.errors import LLMRateLimitError
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.fake import FakeLLMClient, ScriptStep
from triagelite.settings import Settings, get_settings, load_pipeline_config

REPO = Path(__file__).parents[2]
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")


@pytest.fixture
def datasets(tmp_path: Path) -> Path:
    taxonomy = Taxonomy.from_toml((REPO / "config" / "taxonomy.toml").read_text(encoding="utf-8"))
    root = write_work(tmp_path, base_rows())
    build("seed-test", root / "work", root / "datasets", taxonomy)
    return root / "datasets"


def run(
    datasets: Path,
    cache: Path,
    client: FakeLLMClient,
    repeat: int = 1,
    chunk_size: int | None = None,
    model_id: str | None = None,
    code_dir: Path | None = None,
) -> EvalResult:
    return run_eval(
        dataset="seed-test",
        split=Split.TUNING,
        prompt_id="classify/v1",
        repeat=repeat,
        settings=SETTINGS,
        client=client,
        chunk_size=chunk_size,
        model_id=model_id,
        api="converse" if model_id else None,
        datasets_dir=datasets,
        cache_dir=cache,
        code_dir=code_dir or harness.PACKAGE_DIR,
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


def test_chunk_size_override_changes_calls_and_file_name(datasets: Path, tmp_path: Path) -> None:
    client = FakeLLMClient([answer_all(), answer_all()])

    result = run(datasets, tmp_path / "cache", client, repeat=1, chunk_size=3)
    json_path, _ = write_result(result, tmp_path / "results")

    assert len(client.requests) == 2
    assert result.chunk_size == 3
    assert json_path.name.endswith("-tuning-c3.json")


def test_model_override_swaps_model_and_api(datasets: Path, tmp_path: Path) -> None:
    client = FakeLLMClient([answer_all()])

    result = run(datasets, tmp_path / "cache", client, model_id="moonshotai.kimi-k2.5")
    json_path, _ = write_result(result, tmp_path / "results")

    assert (client.requests[0].model_id, client.requests[0].api) == (
        "moonshotai.kimi-k2.5",
        "converse",
    )
    assert client.requests[0].max_tokens == 4096
    assert result.model.api == "converse"
    assert "-moonshotai-kimi-k2-5-tuning-c10" in json_path.name


def test_tampered_dataset_is_refused(datasets: Path, tmp_path: Path) -> None:
    labels = datasets / "seed-test" / "labels.jsonl"
    labels.write_text(labels.read_text() + "\n", encoding="utf-8")

    with pytest.raises(EvalError, match="sha256 mismatch"):
        run(datasets, tmp_path / "cache", FakeLLMClient([]))


def test_write_result_produces_json_and_markdown(datasets: Path, tmp_path: Path) -> None:
    result = run(datasets, tmp_path / "cache", FakeLLMClient([answer_all()]))

    json_path, md_path = write_result(result, tmp_path / "results")

    assert json_path.name.endswith("-classify-v1-claude-haiku-4-5-tuning-c10.json")
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


def test_chunk_size_must_be_positive() -> None:
    assert main(["--chunk-size", "0"]) == 1


def test_results_written_before_the_api_field_load_as_messages(
    datasets: Path, tmp_path: Path
) -> None:
    result = run(datasets, tmp_path / "cache", FakeLLMClient([answer_all()]))
    data = json.loads(result.model_dump_json())
    del data["model"]["api"]

    assert EvalResult.model_validate(data).model.api == "messages"


def test_a_chunk_still_throttled_after_backoff_stops_the_run_uncached(
    datasets: Path, tmp_path: Path
) -> None:
    throttled: list[ScriptStep] = [LLMRateLimitError("429")] * 4

    with pytest.raises(EvalUnavailableError, match="4 attempts"):
        run(datasets, tmp_path / "cache", FakeLLMClient(throttled))

    assert not (tmp_path / "cache").exists()


def test_a_chunk_that_recovers_from_throttling_is_scored(datasets: Path, tmp_path: Path) -> None:
    result = run(
        datasets, tmp_path / "cache", FakeLLMClient([LLMRateLimitError("429"), answer_all()])
    )

    assert all(p.severity is not None for p in result.predictions)
    assert result.fresh_calls == 2


def test_changed_code_misses_the_cache(datasets: Path, tmp_path: Path) -> None:
    code = tmp_path / "code"
    code.mkdir()
    (code / "classify.py").write_text("A = 1\n", encoding="utf-8")
    run(datasets, tmp_path / "cache", FakeLLMClient([answer_all()]), code_dir=code)
    (code / "classify.py").write_text("A = 2\n", encoding="utf-8")
    client = FakeLLMClient([answer_all()])

    result = run(datasets, tmp_path / "cache", client, code_dir=code)

    assert (result.fresh_calls, result.cached_chunks) == (1, 0)


def test_code_fingerprint_covers_names_and_contents(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    first = code_fingerprint(tmp_path)
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
    assert code_fingerprint(tmp_path) == first
    (tmp_path / "a.py").rename(tmp_path / "b.py")
    assert code_fingerprint(tmp_path) != first


def test_the_package_fingerprint_is_stable() -> None:
    assert code_fingerprint(harness.PACKAGE_DIR) == code_fingerprint(harness.PACKAGE_DIR)


def test_throttling_exits_with_its_own_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def unavailable(**_: object) -> EvalResult:
        raise EvalUnavailableError("chunk 1 still throttled after 4 attempts")

    monkeypatch.setattr(harness, "run_eval", unavailable)

    assert main([]) == EXIT_UNAVAILABLE
    assert "still throttled" in capsys.readouterr().err


def test_without_prompt_the_configured_one_runs(
    monkeypatch: pytest.MonkeyPatch, datasets: Path, tmp_path: Path
) -> None:
    seen: list[str] = []

    def fake_run(**kwargs: object) -> EvalResult:
        seen.append(str(kwargs["prompt_id"]))
        return run(datasets, tmp_path / "cache", FakeLLMClient([answer_all()]))

    monkeypatch.setattr(harness, "run_eval", fake_run)

    assert main(["--results-dir", str(tmp_path / "out")]) == 0
    configured = load_pipeline_config(get_settings()).prompts.classify
    assert seen == [f"classify/v{configured}"]
    assert len(list((tmp_path / "out").glob("*.json"))) == 1
