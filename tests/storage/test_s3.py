from collections.abc import Iterator
from typing import TYPE_CHECKING

import boto3
import pytest
from moto import mock_aws

from triagelite.domain.errors import InputValidationError, NotFoundError
from triagelite.domain.models import RowError
from triagelite.storage.s3 import S3Store, report_key, work_key

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

BUCKET = "test-bucket"
REGION = "us-east-1"


@pytest.fixture
def client() -> Iterator["S3Client"]:
    with mock_aws():
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(Bucket=BUCKET)
        yield s3


@pytest.fixture
def store(client: "S3Client") -> S3Store:
    return S3Store(client, BUCKET)


def test_keys_follow_the_bucket_prefixes() -> None:
    assert work_key("b-1", "incidents.jsonl") == "work/b-1/incidents.jsonl"
    assert report_key("b-1", "es") == "reports/b-1/report.es.md"


def test_text_round_trips_with_accents(store: S3Store) -> None:
    store.write_text("reports/b/report.es.md", "El botón falló")

    assert store.read_text("reports/b/report.es.md") == "El botón falló"


def test_markdown_gets_a_utf8_content_type(store: S3Store, client: "S3Client") -> None:
    store.write_text("reports/b/report.es.md", "# Hola")

    head = client.head_object(Bucket=BUCKET, Key="reports/b/report.es.md")
    assert head["ContentType"] == "text/markdown; charset=utf-8"


def test_json_round_trips(store: S3Store) -> None:
    error = RowError(line=2, external_id="x", errors=["bad"])

    store.write_json("work/b/one.json", error)

    assert store.read_json("work/b/one.json", RowError) == error


def test_jsonl_round_trips_in_order(store: S3Store) -> None:
    errors = [RowError(line=5, errors=["a"]), RowError(line=2, errors=["b"])]

    store.write_jsonl("work/b/many.jsonl", errors)

    assert store.read_jsonl("work/b/many.jsonl", RowError) == errors


def test_empty_jsonl_reads_as_an_empty_list(store: S3Store) -> None:
    store.write_jsonl("work/b/none.jsonl", [])

    assert store.read_jsonl("work/b/none.jsonl", RowError) == []


def test_writing_again_overwrites(store: S3Store) -> None:
    store.write_jsonl("work/b/many.jsonl", [RowError(line=1, errors=["a"])] * 2)
    store.write_jsonl("work/b/many.jsonl", [RowError(line=9, errors=["b"])])

    assert [e.line for e in store.read_jsonl("work/b/many.jsonl", RowError)] == [9]


def test_missing_object_is_a_typed_error(store: S3Store) -> None:
    with pytest.raises(NotFoundError, match=r"work/b/missing\.json"):
        store.read_text("work/b/missing.json")


def test_malformed_json_is_a_typed_error(store: S3Store) -> None:
    store.write_text("work/b/bad.json", '{"line": "not a number", "errors": []}')

    with pytest.raises(InputValidationError, match=r"work/b/bad\.json"):
        store.read_json("work/b/bad.json", RowError)


def test_malformed_jsonl_names_the_line(store: S3Store) -> None:
    store.write_text("work/b/bad.jsonl", '{"line": 1, "errors": ["a"]}\nnot json\n')

    with pytest.raises(InputValidationError, match=r"work/b/bad\.jsonl line 2"):
        store.read_jsonl("work/b/bad.jsonl", RowError)


def test_text_that_is_not_utf8_is_a_typed_error(store: S3Store, client: "S3Client") -> None:
    client.put_object(Bucket=BUCKET, Key="incoming/latin1.csv", Body="botón".encode("latin-1"))

    with pytest.raises(InputValidationError, match=r"incoming/latin1\.csv"):
        store.read_text("incoming/latin1.csv")
