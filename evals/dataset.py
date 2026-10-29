"""Eval dataset files, models and checks shared by `evals.build` and `evals.validate`."""

import hashlib
import json
import tomllib
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, NonNegativeInt, PositiveInt

from triagelite.domain.enums import Category, Severity
from triagelite.domain.models import (
    COMPONENT_SLUG_PATTERN,
    Language,
    NonEmptyStr,
    RawIncident,
    StrictModel,
)
from triagelite.domain.taxonomy import Taxonomy

EVALS_DIR = Path(__file__).parent
DATASETS_DIR = EVALS_DIR / "datasets"
WORK_DIR = EVALS_DIR / "work"
INCIDENTS_FILE = "incidents.jsonl"
LABELS_FILE = "labels.jsonl"
MANIFEST_FILE = "MANIFEST.json"
SPEC_FILE = "spec.toml"
HASHED_FILES = (INCIDENTS_FILE, LABELS_FILE)
GROUP_PATTERN = r"^dg-\d{2,}$"

GroupId = Annotated[str, Field(pattern=GROUP_PATTERN)]


class Split(StrEnum):
    """Tune prompts on `tuning`; report `holdout` once."""

    TUNING = "tuning"
    HOLDOUT = "holdout"


class Source(StrEnum):
    """Who wrote the incident text."""

    SYNTHETIC = "synthetic"
    HAND_WRITTEN = "hand_written"


class EvalLabel(StrictModel):
    """Gold labels for one eval incident."""

    external_id: NonEmptyStr
    lang: Language
    severity: Severity
    category: Category
    component: Annotated[str, Field(pattern=COMPONENT_SLUG_PATTERN)]
    duplicate_group: GroupId | None = None
    near_miss_of: GroupId | None = None
    source: Source
    split: Split


class DatasetSpec(StrictModel):
    """Size and coverage rules a frozen dataset must meet."""

    total: PositiveInt
    per_split: PositiveInt
    min_per_cell: PositiveInt
    min_duplicate_groups: NonNegativeInt
    min_cross_language_groups: NonNegativeInt
    min_hand_written: NonNegativeInt

    @classmethod
    def from_toml(cls, text: str) -> Self:
        """Parse and validate spec TOML text."""
        return cls.model_validate(tomllib.loads(text))


class Manifest(StrictModel):
    """Identity of a frozen dataset: its rules, file hashes and counts."""

    name: NonEmptyStr
    created_at: NonEmptyStr
    spec: DatasetSpec
    sha256: dict[str, NonEmptyStr]
    counts: dict[str, int]


def sha256_of(path: Path) -> str:
    """Hex SHA-256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl[T: StrictModel](path: Path, model: type[T]) -> list[T]:
    """Parse every line of a JSON Lines file as `model`."""
    return [model.model_validate_json(line) for line in path.read_text("utf-8").splitlines()]


def write_jsonl(path: Path, items: Iterable[StrictModel]) -> None:
    """Write one compact JSON object per line, in the given order."""
    path.write_text("".join(item.model_dump_json() + "\n" for item in items), encoding="utf-8")


def write_json(path: Path, item: StrictModel) -> None:
    """Write an indented JSON document."""
    path.write_text(json.dumps(item.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")


def check_dataset(
    incidents: Sequence[RawIncident],
    labels: Sequence[EvalLabel],
    spec: DatasetSpec,
    taxonomy: Taxonomy,
) -> list[str]:
    """Every rule a frozen dataset must satisfy; returns human-readable failures."""
    failures: list[str] = []
    incident_ids = [incident.external_id for incident in incidents]
    label_ids = [label.external_id for label in labels]
    if len(set(incident_ids)) != len(incident_ids) or len(set(label_ids)) != len(label_ids):
        failures.append("external_id values are not unique")
    if set(incident_ids) != set(label_ids):
        failures.append("incidents and labels have different external_id sets")
    if len(labels) != spec.total:
        failures.append(f"expected {spec.total} items, found {len(labels)}")

    splits = Counter(label.split for label in labels)
    for split in Split:
        if splits[split] != spec.per_split:
            failures.append(f"split {split} has {splits[split]} items, expected {spec.per_split}")

    cells = Counter((label.severity, label.lang) for label in labels)
    for severity in Severity:
        for lang in ("es", "en"):
            if cells[(severity, lang)] < spec.min_per_cell:
                failures.append(
                    f"cell {severity}/{lang} has {cells[(severity, lang)]} items, "
                    f"minimum {spec.min_per_cell}"
                )

    for label in labels:
        if not taxonomy.has_component(label.component):
            failures.append(f"{label.external_id}: unknown component {label.component!r}")

    failures += _check_groups(labels, spec)

    hand_written = sum(label.source is Source.HAND_WRITTEN for label in labels)
    if hand_written < spec.min_hand_written:
        failures.append(f"{hand_written} hand-written items, minimum {spec.min_hand_written}")
    return failures


def _check_groups(labels: Sequence[EvalLabel], spec: DatasetSpec) -> list[str]:
    failures: list[str] = []
    groups: dict[str, list[EvalLabel]] = defaultdict(list)
    for label in labels:
        if label.duplicate_group:
            groups[label.duplicate_group].append(label)
    for group_id, members in sorted(groups.items()):
        if len(members) < 2:
            failures.append(f"{group_id} has a single member; drop its label or add a duplicate")
        if len({member.split for member in members}) > 1:
            failures.append(f"{group_id} is split across tuning and holdout")
        if len({(m.severity, m.category, m.component) for m in members}) > 1:
            failures.append(f"{group_id} members disagree on severity/category/component")
    if len(groups) < spec.min_duplicate_groups:
        failures.append(f"{len(groups)} duplicate groups, minimum {spec.min_duplicate_groups}")
    cross = sum(len({member.lang for member in members}) > 1 for members in groups.values())
    if cross < spec.min_cross_language_groups:
        failures.append(f"{cross} cross-language groups, minimum {spec.min_cross_language_groups}")
    for label in labels:
        if label.near_miss_of and label.near_miss_of not in groups:
            failures.append(f"{label.external_id}: near_miss_of {label.near_miss_of} not found")
        if label.near_miss_of and label.duplicate_group:
            failures.append(f"{label.external_id}: cannot be both a duplicate and a near-miss")
    return failures
