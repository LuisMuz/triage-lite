from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
import pytest
from moto import mock_aws

from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

BUCKET = "test-bucket"
TABLE = "test-table"
REGION = "us-east-1"
REPO = Path(__file__).parents[2]
SAMPLE = REPO / "data" / "sample.csv"
SOURCE_KEY = "incoming/sample.csv"


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
