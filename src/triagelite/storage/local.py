"""Filesystem storage for local runs: one folder per batch, JSON Lines per output."""

from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from triagelite.domain.models import LLMCallRecord


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
