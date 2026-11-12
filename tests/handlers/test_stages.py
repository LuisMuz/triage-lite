from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
import pytest
from moto import mock_aws

from tests.pipeline.conftest import answer_all, write_report
from triagelite.domain.enums import BatchStatus, Stage, TriageStatus
from triagelite.domain.errors import (
    InputValidationError,
    LLMRateLimitError,
    LLMTransientError,
    NotFoundError,
)
from triagelite.domain.models import Incident, LLMCallRecord
from triagelite.handlers import classify_chunk, dedupe, finalize, normalize, summarize
from triagelite.handlers.events import BatchEvent, ChunkEvent, NormalizeEvent, parse_event
from triagelite.handlers.runtime import CallLog
from triagelite.handlers.work import CHUNK_FAILED_REASON, calls_key, chunk_calls_name
from triagelite.llm.fake import FakeEmbeddingClient, FakeLLMClient, ScriptStep
from triagelite.llm.structured import StructuredLLM
from triagelite.settings import (
    Settings,
    load_llm_config,
    load_pipeline_config,
    load_stage_prompt,
    load_taxonomy,
)
from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store, report_key, work_key

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

BUCKET = "test-bucket"
TABLE = "test-table"
REGION = "us-east-1"
REPO = Path(__file__).parents[2]
SAMPLE = REPO / "data" / "sample.csv"
SOURCE_KEY = "incoming/sample.csv"
SETTINGS = Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts")
MODELS, PRICES = load_llm_config(SETTINGS)
PIPELINE = load_pipeline_config(SETTINGS)
NOW = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
SAMPLE_INCIDENTS = 20


@pytest.fixture
def s3() -> Iterator["S3Client"]:
    with mock_aws():
        client = boto3.client("s3", region_name=REGION)
        client.create_bucket(Bucket=BUCKET)
        yield client


@pytest.fixture
def store(s3: "S3Client") -> S3Store:
    store = S3Store(s3, BUCKET)
    store.write_text(SOURCE_KEY, SAMPLE.read_text(encoding="utf-8"))
    return store


@pytest.fixture
def table(s3: "S3Client") -> BatchTable:
    resource = boto3.resource("dynamodb", region_name=REGION)
    created = resource.create_table(
        TableName=TABLE,
        BillingMode="PAY_PER_REQUEST",
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
    )
    return BatchTable(created)


def run_normalize(store: S3Store, table: BatchTable) -> BatchEvent:
    return normalize.run(
        NormalizeEvent(source_key=SOURCE_KEY), store, table, PIPELINE.normalize, NOW
    )


def run_classify(store: S3Store, batch: BatchEvent, key: str, script: list[ScriptStep]) -> None:
    calls = CallLog()
    classify_chunk.run(
        ChunkEvent(batch_id=batch.batch_id, chunk_key=key),
        store,
        StructuredLLM(FakeLLMClient(script), MODELS, PRICES, recorder=calls),
        load_stage_prompt(SETTINGS, Stage.CLASSIFY, PIPELINE.prompts.classify),
        load_taxonomy(SETTINGS),
        calls,
    )


def run_after_classify(store: S3Store, table: BatchTable, batch: BatchEvent) -> None:
    dedupe.run(
        batch,
        store,
        FakeLLMClient([]),
        FakeEmbeddingClient(),
        load_stage_prompt(SETTINGS, Stage.DEDUPE_JUDGE, PIPELINE.prompts.dedupe_judge),
        MODELS,
        PRICES,
        PIPELINE,
        sleep=lambda _: None,
    )
    summarize.run(
        batch,
        store,
        FakeLLMClient([write_report(), write_report()]),
        load_stage_prompt(SETTINGS, Stage.SUMMARIZE, PIPELINE.prompts.summarize),
        MODELS,
        PRICES,
        PIPELINE,
        sleep=lambda _: None,
    )
    finalize.run(batch, store, table, NOW)


def test_a_batch_goes_from_csv_to_done(store: S3Store, table: BatchTable) -> None:
    batch = run_normalize(store, table)

    assert table.get_batch(batch.batch_id).status is BatchStatus.RUNNING
    assert len(batch.chunk_keys) == 2
    for key in batch.chunk_keys:
        run_classify(store, batch, key, [answer_all()])
    run_after_classify(store, table, batch)

    meta = table.get_batch(batch.batch_id)
    assert meta.status is BatchStatus.DONE
    assert meta.summary is not None
    assert meta.summary.classified == SAMPLE_INCIDENTS
    assert meta.summary.cost_usd > 0
    assert meta.summary.llm_calls == 2 + SAMPLE_INCIDENTS + 2
    assert meta.report_keys == {
        "es": report_key(batch.batch_id, "es"),
        "en": report_key(batch.batch_id, "en"),
    }
    assert store.read_text(report_key(batch.batch_id, "es")).startswith("# Informe de triage QA")
    assert store.read_text(report_key(batch.batch_id, "en")).startswith("# QA triage report")
    assert len(table.list_incidents(batch.batch_id)) == SAMPLE_INCIDENTS


def test_a_chunk_that_never_finished_needs_a_human(store: S3Store, table: BatchTable) -> None:
    batch = run_normalize(store, table)
    run_classify(store, batch, batch.chunk_keys[0], [answer_all()])

    run_after_classify(store, table, batch)

    manual = table.list_incidents(batch.batch_id, needs_manual=True)
    assert len(manual) == PIPELINE.normalize.chunk_size
    assert {incident.reason for incident in manual} == {CHUNK_FAILED_REASON}
    meta = table.get_batch(batch.batch_id)
    assert meta.status is BatchStatus.DONE
    assert meta.summary is not None
    assert meta.summary.needs_manual == PIPELINE.normalize.chunk_size


def test_re_running_a_batch_keeps_one_of_everything(store: S3Store, table: BatchTable) -> None:
    for _ in range(2):
        batch = run_normalize(store, table)
        for key in batch.chunk_keys:
            run_classify(store, batch, key, [answer_all()])
        run_after_classify(store, table, batch)

    assert len(table.list_batches(10)) == 1
    assert len(table.list_incidents(batch.batch_id)) == SAMPLE_INCIDENTS
    meta = table.get_batch(batch.batch_id)
    assert meta.summary is not None
    assert meta.summary.llm_calls == 2 + SAMPLE_INCIDENTS + 2


@pytest.mark.parametrize(
    "error", [LLMRateLimitError("429"), LLMTransientError("503")], ids=["throttled", "transient"]
)
def test_availability_errors_reach_step_functions_with_the_calls_saved(
    store: S3Store, table: BatchTable, error: LLMRateLimitError | LLMTransientError
) -> None:
    batch = run_normalize(store, table)
    key = batch.chunk_keys[0]

    with pytest.raises(type(error)):
        run_classify(store, batch, key, [error])

    calls = store.read_jsonl(calls_key(batch.batch_id, chunk_calls_name(key)), LLMCallRecord)
    assert [call.error_type for call in calls] == [type(error).__name__]


def test_a_csv_with_no_usable_header_marks_the_batch_failed(
    store: S3Store, table: BatchTable
) -> None:
    store.write_text(SOURCE_KEY, "wrong,columns\n1,2\n")

    with pytest.raises(InputValidationError):
        run_normalize(store, table)

    batches = table.list_batches(10)
    assert [batch.status for batch in batches] == [BatchStatus.FAILED]


def test_a_batch_with_only_bad_rows_finishes_empty(store: S3Store, table: BatchTable) -> None:
    store.write_text(
        SOURCE_KEY,
        "external_id,title,description,steps,environment,reported_at,reporter\nQA-1,,,,,,\n",
    )

    batch = run_normalize(store, table)

    assert batch.chunk_keys == []
    run_after_classify(store, table, batch)
    meta = table.get_batch(batch.batch_id)
    assert meta.summary is not None
    assert (meta.summary.incidents, meta.summary.row_errors) == (0, 1)


def test_chunks_hold_the_scrubbed_incidents(store: S3Store, table: BatchTable) -> None:
    batch = run_normalize(store, table)

    incidents = [i for key in batch.chunk_keys for i in store.read_jsonl(key, Incident)]

    assert len(incidents) == SAMPLE_INCIDENTS
    assert "reporter" not in store.read_text(batch.chunk_keys[0])


def test_a_missing_upload_is_a_typed_error(store: S3Store, table: BatchTable) -> None:
    with pytest.raises(NotFoundError):
        normalize.run(
            NormalizeEvent(source_key="incoming/none.csv"), store, table, PIPELINE.normalize, NOW
        )


def test_results_file_lands_next_to_the_batch(store: S3Store, table: BatchTable) -> None:
    batch = run_normalize(store, table)

    run_classify(store, batch, batch.chunk_keys[0], [answer_all()])

    results = store.read_text(work_key(batch.batch_id, "classified/0001.jsonl"))
    assert TriageStatus.CLASSIFIED in results


def test_a_chunk_of_another_batch_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="not a chunk of batch b-1"):
        parse_event(ChunkEvent, {"batch_id": "b-1", "chunk_key": "work/b-2/chunks/0001.jsonl"})


def test_an_event_with_unknown_fields_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="NormalizeEvent"):
        parse_event(NormalizeEvent, {"source_key": "incoming/a.csv", "extra": 1})
