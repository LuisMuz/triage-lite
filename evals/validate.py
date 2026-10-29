"""`python -m evals.validate seed-v1`: prove a frozen dataset is intact and well-formed."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from evals.dataset import (
    DATASETS_DIR,
    HASHED_FILES,
    INCIDENTS_FILE,
    LABELS_FILE,
    MANIFEST_FILE,
    EvalLabel,
    Manifest,
    check_dataset,
    read_jsonl,
    sha256_of,
)
from triagelite.domain.models import RawIncident
from triagelite.domain.taxonomy import Taxonomy

TAXONOMY_PATH = Path("config") / "taxonomy.toml"


def validate(dataset_dir: Path, taxonomy: Taxonomy) -> list[str]:
    """Hash check first (an edited file is a different dataset), then every content rule."""
    manifest_path = dataset_dir / MANIFEST_FILE
    if not manifest_path.exists():
        return [f"{manifest_path} not found"]
    manifest = Manifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    failures = [
        f"{file}: sha256 mismatch, the frozen file was edited"
        for file in HASHED_FILES
        if sha256_of(dataset_dir / file) != manifest.sha256.get(file)
    ]
    try:
        incidents = read_jsonl(dataset_dir / INCIDENTS_FILE, RawIncident)
        labels = read_jsonl(dataset_dir / LABELS_FILE, EvalLabel)
    except ValidationError as error:
        return [*failures, f"unparseable dataset: {error}"]
    return failures + check_dataset(incidents, labels, manifest.spec, taxonomy)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.validate <name>`."""
    parser = argparse.ArgumentParser(prog="python -m evals.validate", description=__doc__)
    parser.add_argument("name", help="dataset name, e.g. seed-v1")
    args = parser.parse_args(argv)
    taxonomy = Taxonomy.from_toml(TAXONOMY_PATH.read_text(encoding="utf-8"))
    failures = validate(DATASETS_DIR / args.name, taxonomy)
    if failures:
        sys.stderr.write("".join(f"FAIL {failure}\n" for failure in failures))
        return 1
    sys.stdout.write(f"OK {args.name}: hashes, counts, cells, groups and labels all valid\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
