"""Filesystem storage for local runs: one folder per batch, JSON Lines per output."""

from collections.abc import Iterable
from pathlib import Path

import numpy as np
from pydantic import BaseModel

from triagelite.domain.models import LLMCallRecord, NonEmptyStr, StrictModel
from triagelite.pipeline.embed import EmbeddingMatrix

VECTORS_FILE = "vectors.npy"
VECTORS_META_FILE = "vectors.json"


class VectorsMeta(StrictModel):
    """What produced a vectors file; vectors from different models or sizes don't compare."""

    model_id: NonEmptyStr
    dimensions: int
    incident_ids: list[str]


class LocalRunStore:
    """Writes a batch's outputs under `run_dir`, overwriting earlier runs of the same batch."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        run_dir.mkdir(parents=True, exist_ok=True)

    def write_jsonl(self, name: str, items: Iterable[BaseModel]) -> Path:
        """Write one JSON object per line and return the file path."""
        path = self.run_dir / name
        with path.open("w", encoding="utf-8") as file:
            for item in items:
                file.write(item.model_dump_json() + "\n")
        return path

    def write_json(self, name: str, item: BaseModel) -> Path:
        """Write one indented JSON document and return the file path."""
        path = self.run_dir / name
        path.write_text(item.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return path

    def write_text(self, name: str, text: str) -> Path:
        """Write a text file such as a rendered report and return its path."""
        path = self.run_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_vectors(self, matrix: EmbeddingMatrix) -> Path:
        """Save vectors as `.npy` with their model, dimensions and row order alongside."""
        np.save(self.run_dir / VECTORS_FILE, matrix.vectors)
        meta = VectorsMeta(
            model_id=matrix.model_id,
            dimensions=matrix.dimensions,
            incident_ids=list(matrix.incident_ids),
        )
        return self.write_json(VECTORS_META_FILE, meta)

    def read_vectors(self) -> EmbeddingMatrix:
        """Load vectors written by `write_vectors`."""
        meta = VectorsMeta.model_validate_json(
            (self.run_dir / VECTORS_META_FILE).read_text("utf-8")
        )
        vectors = np.load(self.run_dir / VECTORS_FILE).astype(np.float32)
        return EmbeddingMatrix(
            model_id=meta.model_id,
            dimensions=meta.dimensions,
            incident_ids=tuple(meta.incident_ids),
            vectors=vectors,
        )

    def call_recorder(self, name: str) -> "JsonlRecorder":
        """A `CallRecorder` that appends to `name`, emptied first so re-runs don't duplicate."""
        return JsonlRecorder(self.run_dir / name)


class JsonlRecorder:
    """Appends each `LLMCallRecord` as it happens, so a crash still leaves the calls made."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.write_text("", encoding="utf-8")

    def __call__(self, record: LLMCallRecord, /) -> None:
        """Append `record` as one line."""
        with self.path.open("a", encoding="utf-8") as file:
            file.write(record.model_dump_json() + "\n")
