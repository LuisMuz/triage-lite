"""`python -m evals.build seed-v1`: reviewed candidates CSV to a frozen, hashed dataset."""

import argparse
import csv
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from evals.dataset import (
    DATASETS_DIR,
    HASHED_FILES,
    INCIDENTS_FILE,
    LABELS_FILE,
    MANIFEST_FILE,
    SPEC_FILE,
    WORK_DIR,
    DatasetSpec,
    EvalLabel,
    Manifest,
    Source,
    Split,
    check_dataset,
    sha256_of,
    write_json,
    write_jsonl,
)
from triagelite.domain.models import RawIncident
from triagelite.domain.taxonomy import Taxonomy
from triagelite.domain.validation import format_validation_errors

CANDIDATES_FILE = "candidates.csv"
README_FILE = "README.md"
KEEP = "keep"
DROP = "drop"
TAXONOMY_PATH = Path("config") / "taxonomy.toml"


class BuildError(Exception):
    """The reviewed candidates can't be frozen yet; the message lists what to fix."""


def load_reviewed(path: Path) -> list[tuple[RawIncident, dict[str, str]]]:
    """Kept rows as (incident, label fields); every row must be reviewed and valid."""
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    problems: list[str] = []
    kept: list[tuple[RawIncident, dict[str, str]]] = []
    for row in rows:
        review = row["review"].strip().lower()
        if review not in (KEEP, DROP):
            problems.append(f"{row['candidate_id']}: review must be 'keep' or 'drop'")
            continue
        if review == DROP:
            continue
        try:
            incident = RawIncident.model_validate(
                {
                    "external_id": row["candidate_id"],
                    "title": row["title"],
                    "description": row["description"],
                    "steps": row["steps"],
                    "environment": row["environment"],
                    "reported_at": row["reported_at"],
                }
            )
        except ValidationError as error:
            problems += [f"{row['candidate_id']}: {e}" for e in format_validation_errors(error)]
            continue
        kept.append((incident, row))
    if problems:
        raise BuildError("\n".join(problems))
    return kept


def assign_splits(
    rows: Sequence[tuple[RawIncident, dict[str, str]]], per_split: int
) -> dict[str, Split]:
    """Group-safe, roughly stratified split: whole duplicate groups go to one side.

    Units (a duplicate group, or a single incident) are placed largest first, each into the
    split that has seen fewer items of the unit's severity/language cells and has room.
    """
    units: dict[str, list[dict[str, str]]] = defaultdict(list)
    for incident, row in rows:
        units[row["duplicate_group"] or incident.external_id].append(row)
    ordered = sorted(units.items(), key=lambda item: (-len(item[1]), item[0]))
    sizes: Counter[Split] = Counter()
    cells: dict[Split, Counter[tuple[str, str]]] = {split: Counter() for split in Split}
    assignment: dict[str, Split] = {}
    for _, members in ordered:
        keys = [(member["severity"], member["lang"]) for member in members]
        candidates = [split for split in Split if sizes[split] + len(members) <= per_split]
        if not candidates:
            raise BuildError("duplicate groups don't fit the split sizes; adjust the drops")
        split = min(
            candidates, key=lambda s: (sum(cells[s][key] for key in keys), sizes[s], s.value)
        )
        sizes[split] += len(members)
        cells[split].update(keys)
        for member in members:
            assignment[member["candidate_id"]] = split
    return assignment


def parse_labels(
    rows: Sequence[tuple[RawIncident, dict[str, str]]], splits: dict[str, Split]
) -> tuple[list[EvalLabel], list[str]]:
    """Gold labels from kept rows, collecting every invalid value instead of stopping at one."""
    labels: list[EvalLabel] = []
    problems: list[str] = []
    for incident, row in rows:
        try:
            labels.append(
                EvalLabel.model_validate(
                    {
                        "external_id": incident.external_id,
                        "lang": row["lang"],
                        "severity": row["severity"],
                        "category": row["category"],
                        "component": row["component"],
                        "duplicate_group": row["duplicate_group"] or None,
                        "near_miss_of": row["near_miss_of"] or None,
                        "source": row["source"],
                        "split": splits[incident.external_id],
                    }
                )
            )
        except ValidationError as error:
            problems += [f"{incident.external_id}: {e}" for e in format_validation_errors(error)]
    return labels, problems


def build(name: str, work_dir: Path, out_root: Path, taxonomy: Taxonomy) -> Manifest:
    """Freeze `work_dir/<name>` into `out_root/<name>`; refuses to overwrite an existing set."""
    source_dir, out_dir = work_dir / name, out_root / name
    if out_dir.exists():
        raise BuildError(f"{out_dir} already exists; frozen datasets are never rebuilt")
    spec = DatasetSpec.from_toml((source_dir / SPEC_FILE).read_text(encoding="utf-8"))
    rows = load_reviewed(source_dir / CANDIDATES_FILE)
    splits = assign_splits(rows, spec.per_split)
    incidents = [incident for incident, _ in rows]
    labels, problems = parse_labels(rows, splits)
    if problems:
        raise BuildError("\n".join(problems))
    failures = check_dataset(incidents, labels, spec, taxonomy)
    if failures:
        raise BuildError("\n".join(failures))

    out_dir.mkdir(parents=True)
    write_jsonl(out_dir / INCIDENTS_FILE, incidents)
    write_jsonl(out_dir / LABELS_FILE, labels)
    manifest = Manifest(
        name=name,
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        spec=spec,
        sha256={file: sha256_of(out_dir / file) for file in HASHED_FILES},
        counts={
            "items": len(labels),
            **{f"split.{s}": sum(lb.split is s for lb in labels) for s in Split},
            **{f"source.{s}": sum(lb.source is s for lb in labels) for s in Source},
        },
    )
    write_json(out_dir / MANIFEST_FILE, manifest)
    if (source_dir / README_FILE).exists():
        (out_dir / README_FILE).write_text(
            (source_dir / README_FILE).read_text(encoding="utf-8"), encoding="utf-8"
        )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.build <name>`."""
    parser = argparse.ArgumentParser(prog="python -m evals.build", description=__doc__)
    parser.add_argument("name", help="dataset name, e.g. seed-v1")
    args = parser.parse_args(argv)
    taxonomy = Taxonomy.from_toml(TAXONOMY_PATH.read_text(encoding="utf-8"))
    try:
        manifest = build(args.name, WORK_DIR, DATASETS_DIR, taxonomy)
    except BuildError as error:
        sys.stderr.write(f"build failed:\n{error}\n")
        return 1
    sys.stdout.write(f"froze {manifest.name}: {manifest.counts}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
