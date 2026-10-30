import json
from pathlib import Path

import numpy as np

from triagelite.domain.enums import CallStatus, Stage
from triagelite.domain.models import LLMCallRecord, RowError
from triagelite.pipeline.embed import EmbeddingMatrix
from triagelite.storage.local import LocalRunStore

RECORD = LLMCallRecord(
    call_id="c1",
    stage=Stage.CLASSIFY,
    model_id="m",
    prompt_version="classify/v1",
    input_tokens=10,
    output_tokens=2,
    cost_usd=0.0,
    latency_ms=5,
    stop_reason="tool_use",
    attempt=1,
    status=CallStatus.OK,
)


def test_creates_the_run_folder(tmp_path: Path) -> None:
    store = LocalRunStore(tmp_path / "runs" / "batch-1")

    assert store.run_dir.is_dir()


def test_write_jsonl_overwrites_previous_content(tmp_path: Path) -> None:
    store = LocalRunStore(tmp_path)
    errors = [RowError(line=2, errors=["bad"]), RowError(line=5, errors=["worse"])]

    store.write_jsonl("e.jsonl", errors)
    path = store.write_jsonl("e.jsonl", errors[:1])

    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["line"] for line in lines] == [2]


def test_write_json_is_readable_back(tmp_path: Path) -> None:
    path = LocalRunStore(tmp_path).write_json("r.json", RECORD)

    assert LLMCallRecord.model_validate_json(path.read_text(encoding="utf-8")) == RECORD


def test_call_recorder_appends_and_starts_empty(tmp_path: Path) -> None:
    store = LocalRunStore(tmp_path)
    store.call_recorder("calls.jsonl")(RECORD)

    recorder = store.call_recorder("calls.jsonl")
    recorder(RECORD)
    recorder(RECORD.model_copy(update={"attempt": 2}))

    lines = (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["attempt"] for line in lines] == [1, 2]


def test_vectors_round_trip_with_their_metadata(tmp_path: Path) -> None:
    store = LocalRunStore(tmp_path)
    matrix = EmbeddingMatrix(
        model_id="titan",
        dimensions=3,
        incident_ids=("inc-0001", "inc-0002"),
        vectors=np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32),
    )

    store.write_vectors(matrix)
    loaded = store.read_vectors()

    assert (loaded.model_id, loaded.dimensions, loaded.incident_ids) == (
        "titan",
        3,
        ("inc-0001", "inc-0002"),
    )
    assert np.array_equal(loaded.vectors, matrix.vectors)
