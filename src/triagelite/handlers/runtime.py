"""What every handler needs, built once per Lambda container and reused by warm invocations."""

from datetime import UTC, datetime
from functools import lru_cache
from typing import TYPE_CHECKING

import boto3

from triagelite.domain.models import LLMCallRecord, NonEmptyStr
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.logs import configure_logging
from triagelite.metrics import call_metrics, emit_metrics, log_call_record
from triagelite.pipeline.config import PipelineConfig
from triagelite.settings import Settings, load_llm_config, load_pipeline_config
from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource
    from mypy_boto3_s3 import S3Client


class LambdaSettings(Settings):
    """Settings plus where the data lives, which only deployed functions need."""

    data_bucket: NonEmptyStr
    table_name: NonEmptyStr
    metrics_namespace: NonEmptyStr


class CallLog:
    """A `CallRecorder` that logs each call, publishes its metrics and keeps it for the batch."""

    def __init__(self, metrics_namespace: str) -> None:
        self.metrics_namespace = metrics_namespace
        self.records: list[LLMCallRecord] = []

    def __call__(self, record: LLMCallRecord, /) -> None:
        """Log `record`, publish its usage and keep it for the batch's cost total."""
        self.records.append(record)
        log_call_record(record)
        emit_metrics(
            self.metrics_namespace,
            call_metrics(record),
            datetime.now(UTC),
            batch_id=record.batch_id,
            stage=record.stage,
            call_id=record.call_id,
            model_id=record.model_id,
        )


@lru_cache(maxsize=1)
def lambda_settings() -> LambdaSettings:
    """Read the settings once and start JSON logging; invalid settings fail the cold start."""
    settings = LambdaSettings()
    configure_logging(settings.log_level)
    return settings


@lru_cache(maxsize=1)
def data_store() -> S3Store:
    """The data bucket."""
    settings = lambda_settings()
    client: S3Client = boto3.client("s3", region_name=settings.aws_region)
    return S3Store(client, settings.data_bucket)


@lru_cache(maxsize=1)
def batch_table() -> BatchTable:
    """The DynamoDB table."""
    settings = lambda_settings()
    resource: DynamoDBServiceResource = boto3.resource("dynamodb", region_name=settings.aws_region)
    return BatchTable(resource.Table(settings.table_name))


@lru_cache(maxsize=1)
def llm_config() -> tuple[ModelsConfig, PriceTable]:
    """Models and prices from the packaged config."""
    return load_llm_config(lambda_settings())


@lru_cache(maxsize=1)
def pipeline_config() -> PipelineConfig:
    """Pipeline settings from the packaged config."""
    return load_pipeline_config(lambda_settings())
