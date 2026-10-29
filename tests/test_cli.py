import json
import shutil
from pathlib import Path

import pytest

from tests.pipeline.conftest import CLASSIFY_TOOL, answer_all, classification_item, make_incident
from triagelite.cli import (
    DEFAULT_RUNS_DIR,
    batch_id_for,
    build_parser,
    classify_with_backoff,
    run_batch,
)
from triagelite.domain.enums import PiiKind, Stage, TriageStatus
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.domain.models import IncidentClassification, LLMCallRecord
from triagelite.llm.fake import FakeLLMClient, ScriptStep, tool_response
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.config import LocalRetryConfig
from triagelite.settings import Settings, load_llm_config, load_stage_prompt, load_taxonomy

REPO = Path(__file__).parents[1]
SAMPLE = REPO / "data" / "sample.csv"
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")
RETRY = LocalRetryConfig(max_attempts=3, initial_delay_seconds=2.0, backoff_rate=2.0)


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TestRunBatch:
    def test_sample_csv_runs_end_to_end(self, tmp_path: Path) -> None:
        client = FakeLLMClient([answer_all(), answer_all()])

        summary, run_dir = run_batch(SAMPLE, tmp_path, SETTINGS, client, sleep=lambda _: None)

        assert run_dir == tmp_path
        assert (summary.incidents, summary.classified, summary.needs_manual) == (20, 20, 0)
        assert summary.llm_calls == 2
        assert summary.cost_usd > 0
        assert summary.pii_redactions[PiiKind.PHONE] == 1
        assert summary.pii_redactions[PiiKind.CREDENTIAL] == 2
        assert len(read_jsonl(run_dir / "incidents.jsonl")) == 20
        assert len(read_jsonl(run_dir / "classifications.jsonl")) == 20
        assert read_jsonl(run_dir / "row_errors.jsonl") == []
        calls = read_jsonl(run_dir / "llm_calls.jsonl")
        assert [call["batch_id"] for call in calls] == [summary.batch_id] * 2
        assert json.loads((run_dir / "summary.json").read_text())["batch_id"] == summary.batch_id

    def test_no_pii_reaches_the_outputs_or_the_model(self, tmp_path: Path) -> None:
        client = FakeLLMClient([answer_all(), answer_all()])

        _, run_dir = run_batch(SAMPLE, tmp_path, SETTINGS, client, sleep=lambda _: None)

        sent = "\n".join(request.user for request in client.requests)
        written = "\n".join(path.read_text() for path in run_dir.iterdir())
        for secret in ("+52 55 1234 5678", "Hunter2024!", "eyJhbGciOiJIUzI1NiJ9", "@example.com"):
            assert secret not in sent
            assert secret not in written

    def test_re_running_the_same_csv_overwrites(self, tmp_path: Path) -> None:
        for _ in range(2):
            run_batch(
                SAMPLE,
                tmp_path,
                SETTINGS,
                FakeLLMClient([answer_all(), answer_all()]),
                sleep=lambda _: None,
            )

        assert len(read_jsonl(tmp_path / "llm_calls.jsonl")) == 2
        assert len(read_jsonl(tmp_path / "classifications.jsonl")) == 20

    def test_default_run_dir_is_named_after_the_batch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        csv_path = tmp_path / "My Batch.csv"
        shutil.copy(SAMPLE, csv_path)

        summary, run_dir = run_batch(
            csv_path,
            None,
            SETTINGS,
            FakeLLMClient([answer_all(), answer_all()]),
            sleep=lambda _: None,
        )

        assert run_dir == DEFAULT_RUNS_DIR / summary.batch_id
        assert summary.batch_id.startswith("my-batch-")


class TestBackoff:
    def classify(
        self, script: list[ScriptStep], delays: list[float]
    ) -> tuple[list[IncidentClassification], FakeLLMClient]:
        client = FakeLLMClient(script)
        records: list[LLMCallRecord] = []
        llm = StructuredLLM(client, *load_llm_config(SETTINGS), recorder=records.append)
        prompt = load_stage_prompt(SETTINGS, Stage.CLASSIFY, 1)
        results = classify_with_backoff(
            llm,
            prompt,
            load_taxonomy(SETTINGS),
            [make_incident(1)],
            batch_id="b",
            retry=RETRY,
            sleep=delays.append,
        )
        return results, client

    def test_throttled_chunk_is_retried_with_growing_jittered_delays(self) -> None:
        delays: list[float] = []
        good = tool_response(CLASSIFY_TOOL, {"items": [classification_item("inc-0001")]})

        results, client = self.classify(
            [LLMRateLimitError("429"), LLMProviderError("503", retryable=True), good], delays
        )

        assert results[0].status is TriageStatus.CLASSIFIED
        assert len(client.requests) == 3
        assert len(delays) == 2
        assert 0 <= delays[0] <= 2.0
        assert 0 <= delays[1] <= 4.0

    def test_exhausted_retries_mark_chunk_needs_manual(self) -> None:
        delays: list[float] = []

        results, client = self.classify([LLMRateLimitError("429")] * 3, delays)

        assert len(client.requests) == 3
        assert len(delays) == 2
        assert results[0].status is TriageStatus.NEEDS_MANUAL
        assert results[0].reason == "model unavailable after 3 attempts (LLMRateLimitError)"

    def test_non_retryable_error_stops_the_run(self) -> None:
        with pytest.raises(LLMProviderError):
            self.classify([LLMProviderError("403", retryable=False)], [])


def test_batch_id_is_stable_and_content_sensitive() -> None:
    first = batch_id_for(Path("data/Sample CSV.csv"), "a,b\n")

    assert first == batch_id_for(Path("other/Sample CSV.csv"), "a,b\n")
    assert first.startswith("sample-csv-")
    assert first != batch_id_for(Path("data/Sample CSV.csv"), "a,c\n")
    assert batch_id_for(Path("___.csv"), "x").startswith("batch-")


def test_parser_requires_a_command() -> None:
    args = build_parser().parse_args(["run", "data/sample.csv", "--out", "x"])

    assert (args.command, args.csv, args.out) == ("run", Path("data/sample.csv"), Path("x"))
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
