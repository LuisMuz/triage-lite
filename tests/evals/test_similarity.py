from pathlib import Path

import numpy as np
import pytest

from evals.build import build
from evals.dataset import EvalLabel, Split
from evals.similarity import (
    CachingEmbeddingClient,
    Pair,
    PairKind,
    SweepRow,
    kind_stats,
    pair_kind,
    recommend_threshold,
    run_similarity,
    sweep,
    thresholds,
    top_k_pairs,
    write_report,
)
from tests.evals.test_dataset import base_rows, write_work
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.fake import FakeEmbeddingClient
from triagelite.llm.types import EmbeddingRequest
from triagelite.settings import Settings

REPO = Path(__file__).parents[2]
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")


def label(
    external_id: str, lang: str = "es", group: str | None = None, near: str | None = None
) -> EvalLabel:
    return EvalLabel.model_validate(
        {
            "external_id": external_id,
            "lang": lang,
            "severity": "high",
            "category": "functional",
            "component": "cart",
            "duplicate_group": group,
            "near_miss_of": near,
            "source": "synthetic",
            "split": "tuning",
        }
    )


@pytest.mark.parametrize(
    ("first", "second", "kind"),
    [
        (label("a", group="dg-01"), label("b", group="dg-01"), PairKind.DUPLICATE_SAME_LANGUAGE),
        (
            label("a", group="dg-01"),
            label("b", "en", group="dg-01"),
            PairKind.DUPLICATE_CROSS_LANGUAGE,
        ),
        (label("a", group="dg-01"), label("b", near="dg-01"), PairKind.NEAR_MISS),
        (label("a", near="dg-01"), label("b", group="dg-01"), PairKind.NEAR_MISS),
        (label("a", group="dg-01"), label("b", group="dg-02"), PairKind.UNRELATED),
        (label("a"), label("b"), PairKind.UNRELATED),
    ],
)
def test_pair_kind(first: EvalLabel, second: EvalLabel, kind: PairKind) -> None:
    assert pair_kind(first, second) is kind


def test_top_k_keeps_each_items_nearest_neighbours() -> None:
    similarity = np.array(
        [[1.0, 0.9, 0.1, 0.2], [0.9, 1.0, 0.3, 0.1], [0.1, 0.3, 1.0, 0.8], [0.2, 0.1, 0.8, 1.0]],
        dtype=np.float32,
    )

    assert top_k_pairs(similarity, 1) == {(0, 1), (2, 3)}
    assert (1, 2) in top_k_pairs(similarity, 2)
    assert top_k_pairs(np.ones((1, 1), dtype=np.float32), 5) == set()


def pair(kind: PairKind, similarity: float, in_top_k: bool = True) -> Pair:
    return Pair(a="a", b="b", kind=kind, similarity=similarity, in_top_k=in_top_k)


PAIRS = [
    pair(PairKind.DUPLICATE_SAME_LANGUAGE, 0.9),
    pair(PairKind.DUPLICATE_CROSS_LANGUAGE, 0.6),
    pair(PairKind.DUPLICATE_CROSS_LANGUAGE, 0.5, in_top_k=False),
    pair(PairKind.NEAR_MISS, 0.7),
    pair(PairKind.UNRELATED, 0.65, in_top_k=False),
    pair(PairKind.UNRELATED, 0.2),
]


def test_sweep_counts_by_hand() -> None:
    rows = {(r.threshold, r.top_k): r for r in sweep(PAIRS, [0.55, 0.45])}

    plain = rows[(0.55, False)]
    assert (plain.candidates, plain.duplicates_found, plain.near_misses_flagged) == (4, 2, 1)
    assert plain.recall == pytest.approx(2 / 3)
    assert plain.cross_language_recall == pytest.approx(1 / 2)
    assert plain.precision == pytest.approx(2 / 4)
    gated = rows[(0.45, True)]
    assert (gated.candidates, gated.duplicates_found) == (3, 2)
    assert gated.cross_language_recall == pytest.approx(1 / 2)


def test_recommend_picks_highest_top_k_threshold_meeting_recall() -> None:
    def row(threshold: float, recall: float, top_k: bool = True) -> SweepRow:
        return SweepRow(
            threshold=threshold,
            top_k=top_k,
            candidates=1,
            duplicates_found=1,
            recall=recall,
            cross_language_recall=recall,
            precision=1.0,
            near_misses_flagged=0,
        )

    rows = [row(0.5, 1.0), row(0.6, 0.96), row(0.7, 0.8), row(0.9, 1.0, top_k=False)]

    assert recommend_threshold(rows, 0.95) == 0.6
    assert recommend_threshold(rows, 1.01) is None


def test_stats_and_grid() -> None:
    stats = kind_stats(PAIRS)

    assert stats[PairKind.DUPLICATE_CROSS_LANGUAGE].count == 2
    assert stats[PairKind.DUPLICATE_SAME_LANGUAGE].quantiles["p50"] == 0.9
    assert kind_stats([])[PairKind.UNRELATED].quantiles == {}
    grid = thresholds()
    assert (grid[0], grid[-1], len(grid)) == (0.2, 0.95, 31)


def test_cache_embeds_identical_requests_once(tmp_path: Path) -> None:
    inner = FakeEmbeddingClient()
    cached = CachingEmbeddingClient(inner, tmp_path)
    request = EmbeddingRequest(model_id="m", text="t", dimensions=256, normalize=True)

    first, second = cached.embed(request), cached.embed(request)
    other = cached.embed(request.model_copy(update={"dimensions": 512}))

    assert first == second
    assert len(other.vector) == 512
    assert len(inner.requests) == 2
    assert cached.fresh_calls == 2


def test_end_to_end_report_files(tmp_path: Path) -> None:
    taxonomy = Taxonomy.from_toml((REPO / "config" / "taxonomy.toml").read_text(encoding="utf-8"))
    root = write_work(tmp_path, base_rows())
    build("seed-test", root / "work", root / "datasets", taxonomy)

    report = run_similarity(
        dataset="seed-test",
        split=Split.TUNING,
        settings=SETTINGS,
        client=FakeEmbeddingClient(),
        datasets_dir=root / "datasets",
        cache_dir=tmp_path / "cache",
    )
    paths = write_report(report, tmp_path / "results")

    assert len(report.pairs) == 6 * 5 // 2
    assert report.fresh_calls == 6
    assert report.cost_usd > 0
    assert sum(s.count for s in report.stats.values()) == 15
    assert [p.suffix for p in paths] == [".json", ".md", ".png"]
    assert paths[2].stat().st_size > 10_000
    markdown = paths[1].read_text()
    assert "## Threshold sweep" in markdown
    assert "## Duplicate pairs the recommended threshold misses" in markdown
