import csv
import json
import shutil
from pathlib import Path

import pytest

from tests.pipeline.conftest import (
    CLASSIFY_TOOL,
    answer_all,
    classification_item,
    judge_all,
    make_incident,
    write_report,
)
from triagelite.cli import (
    DEFAULT_RUNS_DIR,
    batch_id_for,
    build_parser,
    classify_with_backoff,
    dedupe_batch,
    judge_with_backoff,
    run_batch,
    summarize_with_backoff,
)
from triagelite.domain.enums import PiiKind, ReportSource, Stage, TriageStatus
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.domain.models import (
    CandidatePair,
    IncidentClassification,
    LLMCallRecord,
    PairVerdict,
)
from triagelite.llm.fake import FakeEmbeddingClient, FakeLLMClient, ScriptStep, tool_response
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.aggregates import ReportFacts
from triagelite.pipeline.config import LocalRetryConfig
from triagelite.pipeline.embed import embedding_text
from triagelite.settings import (
    Settings,
    load_llm_config,
    load_pipeline_config,
    load_stage_prompt,
    load_taxonomy,
)
from triagelite.storage.local import LocalRunStore

REPO = Path(__file__).parents[1]
SAMPLE = REPO / "data" / "sample.csv"
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")
RETRY = LocalRetryConfig(max_attempts=3, initial_delay_seconds=2.0, backoff_rate=2.0)
SAMPLE_INCIDENTS = 20
DUPLICATE_ROWS = [
    ("QA-1", "Checkout returns error 500", "Any order fails with a server error.", "2026-10-02"),
    (
        "QA-2",
        "Cannot place orders",
        "The order button errors and no order is made.",
        "2026-10-01",
    ),
    ("QA-3", "Footer link typo", "The privacy link in the footer is misspelled.", "2026-10-03"),
]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TestRunBatch:
    def test_sample_csv_runs_end_to_end(self, tmp_path: Path) -> None:
        client = FakeLLMClient([answer_all(), answer_all(), write_report(), write_report()])

        summary, run_dir = run_batch(
            SAMPLE, tmp_path, SETTINGS, client, FakeEmbeddingClient(), sleep=lambda _: None
        )

        assert run_dir == tmp_path
        assert (summary.incidents, summary.classified, summary.needs_manual) == (20, 20, 0)
        assert summary.llm_calls == 4 + SAMPLE_INCIDENTS
        assert summary.reports_from_template == []
        assert (summary.candidate_pairs, summary.clusters) == (0, SAMPLE_INCIDENTS)
        assert summary.cost_usd > 0
        assert summary.pii_redactions[PiiKind.PHONE] == 1
        assert summary.pii_redactions[PiiKind.CREDENTIAL] == 2
        assert len(read_jsonl(run_dir / "incidents.jsonl")) == 20
        assert len(read_jsonl(run_dir / "classifications.jsonl")) == 20
        assert read_jsonl(run_dir / "row_errors.jsonl") == []
        calls = read_jsonl(run_dir / "llm_calls.jsonl")
        assert [call["batch_id"] for call in calls] == [summary.batch_id] * summary.llm_calls
        assert len(read_jsonl(run_dir / "clusters.jsonl")) == SAMPLE_INCIDENTS
        assert read_jsonl(run_dir / "pairs.jsonl") == []
        assert (run_dir / "vectors.npy").exists()
        report_es = (run_dir / "report.es.md").read_text()
        assert report_es.startswith("# Informe de triage QA")
        assert "20 incidents." in report_es
        assert "redactado por el modelo" in report_es
        assert "# QA triage report" in (run_dir / "report.en.md").read_text()
        assert len(read_jsonl(run_dir / "report_drafts.jsonl")) == 2
        facts = json.loads((run_dir / "report_facts.json").read_text())
        assert facts["aggregates"]["total.incidents"]["value"] == SAMPLE_INCIDENTS
        assert json.loads((run_dir / "summary.json").read_text())["batch_id"] == summary.batch_id

    def test_no_pii_reaches_the_outputs_or_the_model(self, tmp_path: Path) -> None:
        client = FakeLLMClient([answer_all(), answer_all(), write_report(), write_report()])

        _, run_dir = run_batch(
            SAMPLE, tmp_path, SETTINGS, client, FakeEmbeddingClient(), sleep=lambda _: None
        )

        sent = "\n".join(request.user for request in client.requests)
        written = "\n".join(path.read_text() for path in run_dir.iterdir() if path.suffix != ".npy")
        for secret in ("+52 55 1234 5678", "Hunter2024!", "eyJhbGciOiJIUzI1NiJ9", "@example.com"):
            assert secret not in sent
            assert secret not in written

    def test_re_running_the_same_csv_overwrites(self, tmp_path: Path) -> None:
        for _ in range(2):
            run_batch(
                SAMPLE,
                tmp_path,
                SETTINGS,
                FakeLLMClient([answer_all(), answer_all(), write_report(), write_report()]),
                FakeEmbeddingClient(),
                sleep=lambda _: None,
            )

        assert len(read_jsonl(tmp_path / "llm_calls.jsonl")) == 4 + SAMPLE_INCIDENTS
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
            FakeLLMClient([answer_all(), answer_all(), write_report(), write_report()]),
            FakeEmbeddingClient(),
            sleep=lambda _: None,
        )

        assert run_dir == DEFAULT_RUNS_DIR / summary.batch_id
        assert summary.batch_id.startswith("my-batch-")

    def test_confirmed_duplicates_are_clustered_under_the_earliest_report(
        self, tmp_path: Path
    ) -> None:
        csv_path = tmp_path / "dupes.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["external_id", "title", "description", "reported_at"])
            writer.writerows((*row[:3], f"{row[3]}T09:00:00Z") for row in DUPLICATE_ROWS)
        store = tmp_path / "run"
        same = (1.0,) + (0.0,) * 1023
        embedder = FakeEmbeddingClient(
            fixed={
                embedding_text(
                    make_incident(1).model_copy(update={"title": title, "description": text}), 500
                ): same
                for _, title, text, _ in DUPLICATE_ROWS[:2]
            }
        )
        client = FakeLLMClient([answer_all(), judge_all(), write_report(), write_report()])

        summary, run_dir = run_batch(
            csv_path, store, SETTINGS, client, embedder, sleep=lambda _: None
        )

        assert (summary.candidate_pairs, summary.confirmed_pairs) == (1, 1)
        assert (summary.clusters, summary.duplicate_incidents) == (2, 1)
        clusters = read_jsonl(run_dir / "clusters.jsonl")
        assert clusters[0]["member_ids"] == ["inc-0002", "inc-0001"]
        pairs = [
            PairVerdict.model_validate_json(line)
            for line in (run_dir / "pairs.jsonl").read_text().splitlines()
        ]
        assert pairs[0].pair.first_id == "inc-0002"
        assert LocalRunStore(run_dir).read_vectors().incident_ids == (
            "inc-0001",
            "inc-0002",
            "inc-0003",
        )


class TestDedupeBatch:
    def test_pair_cap_is_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        models, prices = load_llm_config(SETTINGS)
        pipeline = load_pipeline_config(SETTINGS)
        incidents = [make_incident(n) for n in range(1, 4)]
        same = (1.0,) + (0.0,) * 1023
        embedder = FakeEmbeddingClient(
            fixed={
                embedding_text(i, models.embedding.max_description_chars): same for i in incidents
            }
        )
        llm = StructuredLLM(FakeLLMClient([judge_all()]), models, prices, recorder=lambda _: None)

        result = dedupe_batch(
            llm,
            load_stage_prompt(SETTINGS, Stage.DEDUPE_JUDGE, 1),
            embedder,
            incidents,
            models=models,
            prices=prices,
            config=pipeline.dedupe.model_copy(update={"max_pairs": 2}),
            retry=RETRY,
            recorder=lambda _: None,
            batch_id="b",
            sleep=lambda _: None,
        )

        assert (len(result.candidates.pairs), result.candidates.dropped) == (2, 1)
        assert "pair cap hit" in caplog.text
        assert [c.member_ids for c in result.clusters] == [["inc-0001", "inc-0002", "inc-0003"]]


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

    def test_exhausted_judge_chunk_leaves_pairs_unjudged(self) -> None:
        client = FakeLLMClient([LLMRateLimitError("429")] * 3)
        llm = StructuredLLM(client, *load_llm_config(SETTINGS), recorder=lambda _: None)
        pair = CandidatePair(
            pair_id="p-0001", first_id="inc-0001", second_id="inc-0002", similarity=0.9
        )

        verdicts = judge_with_backoff(
            llm,
            load_stage_prompt(SETTINGS, Stage.DEDUPE_JUDGE, 1),
            [pair],
            {i.incident_id: i for i in (make_incident(1), make_incident(2))},
            batch_id="b",
            retry=RETRY,
            sleep=lambda _: None,
        )

        assert len(client.requests) == 3
        assert verdicts[0].judgement is None
        assert verdicts[0].reason == "model unavailable after 3 attempts (LLMRateLimitError)"


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


def test_unavailable_model_gives_a_template_report() -> None:
    client = FakeLLMClient([LLMRateLimitError("429")] * 3)
    llm = StructuredLLM(client, *load_llm_config(SETTINGS), recorder=lambda _: None)
    pipeline = load_pipeline_config(SETTINGS)
    facts = ReportFacts(aggregates={}, top_components=[], representatives=[])

    draft = summarize_with_backoff(
        llm,
        load_stage_prompt(SETTINGS, Stage.SUMMARIZE, 1),
        facts,
        "en",
        pipeline.report,
        batch_id="b",
        retry=RETRY,
        sleep=lambda _: None,
    )

    assert len(client.requests) == 3
    assert draft.source is ReportSource.TEMPLATE
    assert draft.problems == ["model unavailable after 3 attempts (LLMRateLimitError)"]
