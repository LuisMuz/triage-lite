from pathlib import Path

import pytest

from evals.build import build
from evals.dataset import Split
from evals.dedupe import (
    Arm,
    CachingLLMClient,
    DedupeEvalResult,
    JudgedPair,
    gold_groups,
    judge_metrics,
    main,
    run_dedupe_eval,
    write_result,
)
from evals.similarity import PairKind
from tests.evals.test_dataset import base_rows, write_work
from tests.evals.test_similarity import label
from tests.pipeline.conftest import judge_all
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.fake import FakeLLMClient, tool_response
from triagelite.llm.types import EmbeddingRequest, EmbeddingResponse, ModelRequest, ToolSpec
from triagelite.settings import Settings

REPO = Path(__file__).parents[2]
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")


class SameVector:
    def __init__(self) -> None:
        self.requests: list[EmbeddingRequest] = []

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.requests.append(request)
        vector = (1.0,) + (0.0,) * (request.dimensions - 1)
        return EmbeddingResponse(vector=vector, input_tokens=5)


@pytest.fixture
def datasets(tmp_path: Path) -> Path:
    taxonomy = Taxonomy.from_toml((REPO / "config" / "taxonomy.toml").read_text(encoding="utf-8"))
    root = write_work(tmp_path, base_rows())
    build("seed-test", root / "work", root / "datasets", taxonomy)
    return root / "datasets"


def run(datasets: Path, cache: Path, client: FakeLLMClient) -> DedupeEvalResult:
    return run_dedupe_eval(
        dataset="seed-test",
        split=Split.TUNING,
        settings=SETTINGS,
        client=client,
        embedder=SameVector(),
        datasets_dir=datasets,
        cache_dir=cache,
        sleep=lambda _: None,
    )


def test_judge_saying_no_keeps_every_report_apart(datasets: Path, tmp_path: Path) -> None:
    client = FakeLLMClient([judge_all(is_duplicate=False)] * 10)

    result = run(datasets, tmp_path / "cache", client)

    pairs = result.incidents * (result.incidents - 1) // 2
    assert result.candidates == len(result.pairs) == pairs
    assert result.judge.judged == pairs
    assert result.arms[Arm.THRESHOLD_JUDGE].predicted_pairs == 0
    assert result.arms[Arm.THRESHOLD_ONLY].clusters == 1
    assert result.clusters[Arm.THRESHOLD_JUDGE] == []
    assert result.fresh_llm_calls == len(client.requests) == result.llm_calls
    assert result.judge_valid_first_try == 1.0
    assert result.fresh_embed_calls == result.incidents
    assert result.never_proposed == []
    assert result.judge_cost_usd > 0
    assert result.cost_usd > result.judge_cost_usd


def test_second_run_is_served_from_cache(datasets: Path, tmp_path: Path) -> None:
    first = run(datasets, tmp_path / "cache", FakeLLMClient([judge_all()] * 10))
    client = FakeLLMClient([])

    second = run(datasets, tmp_path / "cache", client)

    assert client.requests == []
    assert (second.fresh_llm_calls, second.fresh_embed_calls) == (0, 0)
    assert second.arms == first.arms
    assert second.cost_usd == first.cost_usd


def test_writes_json_and_markdown(datasets: Path, tmp_path: Path) -> None:
    result = run(datasets, tmp_path / "cache", FakeLLMClient([judge_all()] * 10))

    json_path, md_path = write_result(result, tmp_path / "results")

    assert json_path.name.endswith("dedupe_judge-v1-claude-haiku-4-5-tuning.json")
    assert DedupeEvalResult.model_validate_json(json_path.read_text()) == result
    report = md_path.read_text()
    assert "## Ablation" in report
    assert "Threshold + top-k + judge" in report
    assert "## Judge false positives" in report


def test_gold_groups_collect_members_by_group() -> None:
    labels = {
        "b": label("b", group="dg-02"),
        "a": label("a", group="dg-02"),
        "c": label("c", group="dg-01"),
        "d": label("d"),
    }

    assert gold_groups(labels) == [["c"], ["a", "b"]]


def judged(kind: PairKind, answer: bool | None, confidence: float = 0.9) -> JudgedPair:
    return JudgedPair(
        pair_id="p",
        a="a",
        b="b",
        kind=kind,
        similarity=0.5,
        is_duplicate=answer,
        confidence=None if answer is None else confidence,
        rationale=None if answer is None else "r",
        reason="unavailable" if answer is None else None,
    )


def test_judge_metrics_count_unjudged_as_not_duplicate() -> None:
    pairs = [
        judged(PairKind.DUPLICATE_SAME_LANGUAGE, True),
        judged(PairKind.DUPLICATE_CROSS_LANGUAGE, None),
        judged(PairKind.NEAR_MISS, True, 0.5),
        judged(PairKind.UNRELATED, False),
    ]

    metrics = judge_metrics(pairs)

    assert (metrics.judged, metrics.unjudged) == (3, 1)
    assert metrics.precision == pytest.approx(1 / 2)
    assert metrics.recall == pytest.approx(1 / 2)
    assert metrics.by_kind[PairKind.NEAR_MISS].said_duplicate == 1
    assert metrics.by_kind[PairKind.DUPLICATE_CROSS_LANGUAGE].unjudged == 1
    assert sum(b.count for b in metrics.calibration) == 3


def test_caching_llm_client_calls_the_model_once_per_request(tmp_path: Path) -> None:
    inner = FakeLLMClient([tool_response("t", {"items": []})])
    client = CachingLLMClient(inner, tmp_path)
    request = ModelRequest(
        model_id="m",
        max_tokens=10,
        system="s",
        user="u",
        tool=ToolSpec(name="t", description="d", input_schema={}),
        timeout_seconds=1.0,
    )

    assert client.complete(request) == client.complete(request)
    assert (client.fresh_calls, len(inner.requests)) == (1, 1)


def test_holdout_needs_confirmation(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--split", "holdout"]) == 1
    assert "--confirm-holdout" in capsys.readouterr().err
