import csv
from pathlib import Path

import pytest

from evals.build import BuildError, assign_splits, build, load_reviewed
from evals.dataset import (
    INCIDENTS_FILE,
    LABELS_FILE,
    MANIFEST_FILE,
    DatasetSpec,
    EvalLabel,
    Split,
    check_dataset,
    read_jsonl,
)
from evals.validate import main as validate_main
from evals.validate import validate
from triagelite.domain.models import RawIncident
from triagelite.domain.taxonomy import Taxonomy

REPO = Path(__file__).parents[2]
SPEC = """total = 12
per_split = 6
min_per_cell = 1
min_duplicate_groups = 1
min_cross_language_groups = 1
min_hand_written = 1
"""
HEADER = [
    "candidate_id",
    "review",
    "review_notes",
    "source",
    "lang",
    "severity",
    "category",
    "component",
    "duplicate_group",
    "near_miss_of",
    "title",
    "description",
    "steps",
    "environment",
    "reported_at",
]


@pytest.fixture
def taxonomy() -> Taxonomy:
    return Taxonomy.from_toml((REPO / "config" / "taxonomy.toml").read_text(encoding="utf-8"))


def row(
    number: int,
    lang: str,
    severity: str,
    *,
    group: str = "",
    near: str = "",
    review: str = "keep",
    source: str = "synthetic",
    component: str = "checkout",
) -> list[str]:
    return [
        f"cand-{number:03d}",
        review,
        "",
        source,
        lang,
        severity,
        "functional",
        component,
        group,
        near,
        f"Title {number}",
        f"Description {number}",
        "",
        "",
        "2026-09-01T08:00:00Z",
    ]


def base_rows() -> list[list[str]]:
    rows = [
        row(n, lang, severity)
        for n, (severity, lang) in enumerate(
            [(s, lang) for s in ("critical", "high", "medium", "low") for lang in ("es", "en")],
            start=1,
        )
    ]
    rows += [
        row(9, "es", "high", group="dg-01"),
        row(10, "en", "high", group="dg-01"),
        row(11, "en", "low", near="dg-01", source="hand_written"),
        row(12, "es", "medium"),
        row(13, "en", "medium", review="drop"),
    ]
    return rows


def write_work(root: Path, rows: list[list[str]], spec: str = SPEC) -> Path:
    work = root / "work" / "seed-test"
    work.mkdir(parents=True)
    (work / "spec.toml").write_text(spec, encoding="utf-8")
    with (work / "candidates.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(rows)
    return root


def build_ok(tmp_path: Path, taxonomy: Taxonomy) -> Path:
    root = write_work(tmp_path, base_rows())
    (root / "work" / "seed-test" / "README.md").write_text("# seed-test\n", encoding="utf-8")
    build("seed-test", root / "work", root / "datasets", taxonomy)
    return root / "datasets" / "seed-test"


class TestBuild:
    def test_freezes_kept_rows_with_hashes(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        dataset = build_ok(tmp_path, taxonomy)

        labels = read_jsonl(dataset / LABELS_FILE, EvalLabel)
        incidents = read_jsonl(dataset / INCIDENTS_FILE, RawIncident)
        assert len(labels) == len(incidents) == 12
        assert "cand-013" not in {label.external_id for label in labels}
        assert (dataset / MANIFEST_FILE).exists()
        assert (dataset / "README.md").read_text() == "# seed-test\n"
        assert validate(dataset, taxonomy) == []

    def test_duplicate_group_lands_in_one_split(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        labels = read_jsonl(build_ok(tmp_path, taxonomy) / LABELS_FILE, EvalLabel)

        group_splits = {label.split for label in labels if label.duplicate_group == "dg-01"}
        assert len(group_splits) == 1

    def test_refuses_to_overwrite_a_frozen_dataset(
        self, tmp_path: Path, taxonomy: Taxonomy
    ) -> None:
        build_ok(tmp_path, taxonomy)

        with pytest.raises(BuildError, match="never rebuilt"):
            build("seed-test", tmp_path / "work", tmp_path / "datasets", taxonomy)

    def test_every_row_must_be_reviewed(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        rows = base_rows()
        rows[0][1] = ""
        root = write_work(tmp_path, rows)

        with pytest.raises(BuildError, match="cand-001: review must be"):
            build("seed-test", root / "work", root / "datasets", taxonomy)

    def test_rule_failures_block_the_freeze(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        rows = base_rows()
        rows[10][1] = "drop"
        root = write_work(tmp_path, rows)

        with pytest.raises(BuildError, match="expected 12 items"):
            build("seed-test", root / "work", root / "datasets", taxonomy)
        assert not (root / "datasets" / "seed-test").exists()

    def test_invalid_kept_row_is_reported(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        rows = base_rows()
        rows[0][10] = ""
        root = write_work(tmp_path, rows)

        with pytest.raises(BuildError, match="cand-001: title"):
            load_reviewed(root / "work" / "seed-test" / "candidates.csv")

    def test_invalid_label_is_reported_not_raised(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        rows = base_rows()
        rows[3][6] = "notifications"
        root = write_work(tmp_path, rows)

        with pytest.raises(BuildError, match="cand-004: category: Input should be"):
            build("seed-test", root / "work", root / "datasets", taxonomy)

    def test_groups_that_cannot_fit_are_rejected(self, tmp_path: Path) -> None:
        rows = [row(n, "es", "high", group="dg-01") for n in range(1, 5)]
        root = write_work(tmp_path, rows)

        with pytest.raises(BuildError, match="don't fit"):
            assign_splits(load_reviewed(root / "work" / "seed-test" / "candidates.csv"), 3)


class TestValidate:
    def test_edited_file_fails_the_hash_check(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        dataset = build_ok(tmp_path, taxonomy)
        labels = dataset / LABELS_FILE
        labels.write_text(labels.read_text().replace('"high"', '"low"', 1), encoding="utf-8")

        assert any("sha256 mismatch" in failure for failure in validate(dataset, taxonomy))

    def test_missing_manifest(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        assert validate(tmp_path, taxonomy) == [f"{tmp_path / MANIFEST_FILE} not found"]

    def test_unparseable_files(self, tmp_path: Path, taxonomy: Taxonomy) -> None:
        dataset = build_ok(tmp_path, taxonomy)
        (dataset / LABELS_FILE).write_text('{"external_id": "x"}\n', encoding="utf-8")

        assert any("unparseable" in failure for failure in validate(dataset, taxonomy))

    def test_cli_reports_failure_for_unknown_dataset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)

        assert validate_main(["does-not-exist"]) == 1


def label(
    external_id: str,
    *,
    split: Split = Split.TUNING,
    group: str | None = None,
    severity: str = "high",
    lang: str = "es",
    near: str | None = None,
    component: str = "cart",
) -> EvalLabel:
    return EvalLabel.model_validate(
        {
            "external_id": external_id,
            "lang": lang,
            "severity": severity,
            "category": "functional",
            "component": component,
            "duplicate_group": group,
            "near_miss_of": near,
            "source": "synthetic",
            "split": split,
        }
    )


def incident(external_id: str) -> RawIncident:
    return RawIncident(external_id=external_id, title="t", description="d")


LOOSE = DatasetSpec(
    total=2,
    per_split=1,
    min_per_cell=1,
    min_duplicate_groups=0,
    min_cross_language_groups=0,
    min_hand_written=0,
)


@pytest.mark.parametrize(
    ("labels", "expected"),
    [
        (
            [label("a", group="dg-01"), label("b", group="dg-01", split=Split.HOLDOUT)],
            "dg-01 is split across tuning and holdout",
        ),
        (
            [label("a", group="dg-01"), label("b", split=Split.HOLDOUT)],
            "dg-01 has a single member",
        ),
        (
            [label("a", group="dg-01"), label("b", group="dg-01", severity="low")],
            "dg-01 members disagree",
        ),
        (
            [label("a", near="dg-07"), label("b", split=Split.HOLDOUT)],
            "a: near_miss_of dg-07 not found",
        ),
        (
            [label("a", group="dg-01", near="dg-01"), label("b", group="dg-01")],
            "a: cannot be both a duplicate and a near-miss",
        ),
        (
            [label("a", component="billing"), label("b", split=Split.HOLDOUT)],
            "a: unknown component 'billing'",
        ),
        (
            [label("a"), label("a", split=Split.HOLDOUT)],
            "external_id values are not unique",
        ),
    ],
    ids=["split-group", "lonely", "disagree", "bad-near-miss", "dup-and-near", "component", "ids"],
)
def test_content_rules(labels: list[EvalLabel], expected: str, taxonomy: Taxonomy) -> None:
    incidents = [incident(lb.external_id) for lb in labels]

    assert any(expected in failure for failure in check_dataset(incidents, labels, LOOSE, taxonomy))


def test_coverage_minimums(taxonomy: Taxonomy) -> None:
    strict = LOOSE.model_copy(
        update={"min_duplicate_groups": 1, "min_cross_language_groups": 1, "min_hand_written": 1}
    )
    labels = [label("a", group="dg-01"), label("b", group="dg-01")]

    failures = check_dataset([incident("a"), incident("c")], labels, strict, taxonomy)

    assert "incidents and labels have different external_id sets" in failures
    assert "split holdout has 0 items, expected 1" in failures
    assert "cell critical/es has 0 items, minimum 1" in failures
    assert "0 cross-language groups, minimum 1" in failures
    assert "0 hand-written items, minimum 1" in failures
    strict_groups = strict.model_copy(update={"min_duplicate_groups": 2})
    assert "1 duplicate groups, minimum 2" in check_dataset([], labels, strict_groups, taxonomy)
