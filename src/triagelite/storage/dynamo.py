"""The single DynamoDB table: batches, their incidents and clusters, and the batch listing."""

import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from boto3.dynamodb.conditions import Attr, Key
from pydantic import ValidationError

from triagelite.domain.enums import BatchStatus, TriageStatus
from triagelite.domain.errors import InputValidationError, NotFoundError
from triagelite.domain.models import (
    BatchMeta,
    DuplicateCluster,
    IncidentRecord,
    Language,
    RunSummary,
    StrictModel,
)
from triagelite.domain.validation import format_validation_errors
from triagelite.logs import log_fields

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

LOGGER = logging.getLogger("triagelite.storage.dynamo")
PARTITION_KEY = "PK"
SORT_KEY = "SK"
KEY_ATTRIBUTES = frozenset({PARTITION_KEY, SORT_KEY})
BATCH_PARTITION = "BATCH#{}"
LISTING_PARTITION = "BATCHES"
META_SORT = "META"
INCIDENT_PREFIX = "INC#"
CLUSTER_PREFIX = "CLUSTER#"
LISTING_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class BatchTable:
    """Typed access to the table; every key follows from `batch_id` and the item's own ID."""

    def __init__(self, table: "Table") -> None:
        self.table = table

    def start_batch(self, batch_id: str, source_key: str, now: datetime) -> BatchMeta:
        """Mark a batch as running; a re-run keeps its `created_at`, so its listing stays single."""
        meta = BatchMeta(
            batch_id=batch_id,
            status=BatchStatus.RUNNING,
            source_key=source_key,
            created_at=now,
            updated_at=now,
        )
        try:
            self.table.put_item(
                Item=_item(_batch_partition(batch_id), META_SORT, meta),
                ConditionExpression=Attr(PARTITION_KEY).not_exists(),
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            created_at = self.get_batch(batch_id).created_at
            meta = meta.model_copy(update={"created_at": created_at})
        self._save(meta)
        return meta

    def finish_batch(
        self,
        batch_id: str,
        summary: RunSummary,
        report_keys: Mapping[Language, str],
        now: datetime,
    ) -> BatchMeta:
        """Mark a batch as done, with its totals and report locations.

        Raises:
            NotFoundError: the batch was never started.
        """
        current = self.get_batch(batch_id)
        meta = BatchMeta(
            batch_id=batch_id,
            status=BatchStatus.DONE,
            source_key=current.source_key,
            created_at=current.created_at,
            updated_at=now,
            summary=summary,
            report_keys=dict(report_keys),
        )
        self._save(meta)
        return meta

    def fail_batch(self, batch_id: str, error: str, now: datetime) -> BatchMeta:
        """Mark a batch as failed, with a reason that must not contain incident text.

        Raises:
            NotFoundError: the batch was never started.
        """
        current = self.get_batch(batch_id)
        meta = BatchMeta(
            batch_id=batch_id,
            status=BatchStatus.FAILED,
            source_key=current.source_key,
            created_at=current.created_at,
            updated_at=now,
            error=error,
        )
        self._save(meta)
        return meta

    def get_batch(self, batch_id: str) -> BatchMeta:
        """Read one batch.

        Raises:
            NotFoundError: the batch does not exist.
            InputValidationError: the stored item is not a valid batch.
        """
        partition = _batch_partition(batch_id)
        response = self.table.get_item(Key={PARTITION_KEY: partition, SORT_KEY: META_SORT})
        item = response.get("Item")
        if item is None:
            msg = f"batch {batch_id} does not exist"
            raise NotFoundError(msg)
        return _parse(item, BatchMeta)

    def list_batches(self, limit: int) -> list[BatchMeta]:
        """Latest batches, newest first."""
        response = self.table.query(
            KeyConditionExpression=Key(PARTITION_KEY).eq(LISTING_PARTITION),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [_parse(item, BatchMeta) for item in response["Items"]]

    def put_incidents(self, batch_id: str, records: Iterable[IncidentRecord]) -> None:
        """Write incidents; writing one again overwrites it, including its cluster link."""
        partition = _batch_partition(batch_id)
        with self.table.batch_writer(overwrite_by_pkeys=[PARTITION_KEY, SORT_KEY]) as batch:
            for record in records:
                batch.put_item(
                    Item=_item(partition, f"{INCIDENT_PREFIX}{record.incident_id}", record)
                )

    def list_incidents(
        self, batch_id: str, *, needs_manual: bool | None = None
    ) -> list[IncidentRecord]:
        """A batch's incidents in ID order, optionally only those that do or don't need a human."""
        status = Attr("status")
        manual = TriageStatus.NEEDS_MANUAL.value
        condition = (
            None
            if needs_manual is None
            else (status.eq(manual) if needs_manual else status.ne(manual))
        )
        return [
            _parse(item, IncidentRecord)
            for item in self._query_prefix(batch_id, INCIDENT_PREFIX, condition)
        ]

    def replace_clusters(self, batch_id: str, clusters: Sequence[DuplicateCluster]) -> None:
        """Make `clusters` the batch's only clusters and point each member's incident at its own.

        The judge isn't deterministic, so a re-run can drop a cluster or move a member; leftovers
        from an earlier run are removed rather than left to contradict the new result.
        """
        partition = _batch_partition(batch_id)
        previous = self.list_clusters(batch_id)
        current_ids = {cluster.cluster_id for cluster in clusters}
        links = {member: c.cluster_id for c in clusters for member in c.member_ids}
        with self.table.batch_writer(overwrite_by_pkeys=[PARTITION_KEY, SORT_KEY]) as batch:
            for old in previous:
                if old.cluster_id not in current_ids:
                    batch.delete_item(
                        Key={
                            PARTITION_KEY: partition,
                            SORT_KEY: f"{CLUSTER_PREFIX}{old.cluster_id}",
                        }
                    )
            for cluster in clusters:
                batch.put_item(
                    Item=_item(partition, f"{CLUSTER_PREFIX}{cluster.cluster_id}", cluster)
                )
        for old in previous:
            for member in old.member_ids:
                if member not in links:
                    self._update_incident(batch_id, member, "REMOVE cluster_id", None)
        for member, cluster_id in links.items():
            self._update_incident(
                batch_id, member, "SET cluster_id = :cluster", {":cluster": cluster_id}
            )

    def list_clusters(self, batch_id: str) -> list[DuplicateCluster]:
        """A batch's clusters in ID order."""
        return [
            _parse(item, DuplicateCluster)
            for item in self._query_prefix(batch_id, CLUSTER_PREFIX, None)
        ]

    def _save(self, meta: BatchMeta) -> None:
        with self.table.batch_writer(overwrite_by_pkeys=[PARTITION_KEY, SORT_KEY]) as batch:
            batch.put_item(Item=_item(_batch_partition(meta.batch_id), META_SORT, meta))
            batch.put_item(Item=_item(LISTING_PARTITION, _listing_sort(meta), meta))

    def _update_incident(
        self, batch_id: str, incident_id: str, update: str, values: dict[str, Any] | None
    ) -> None:
        extra: dict[str, Any] = {"ExpressionAttributeValues": values} if values else {}
        try:
            self.table.update_item(
                Key={
                    PARTITION_KEY: _batch_partition(batch_id),
                    SORT_KEY: f"{INCIDENT_PREFIX}{incident_id}",
                },
                UpdateExpression=update,
                ConditionExpression=Attr(PARTITION_KEY).exists(),
                **extra,
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            LOGGER.warning(
                "cluster member has no incident item",
                extra=log_fields(batch_id=batch_id, incident_id=incident_id),
            )

    def _query_prefix(
        self, batch_id: str, prefix: str, condition: Any | None
    ) -> list[dict[str, Any]]:
        partition = Key(PARTITION_KEY).eq(_batch_partition(batch_id))
        arguments: dict[str, Any] = {
            "TableName": self.table.name,
            "KeyConditionExpression": partition & Key(SORT_KEY).begins_with(prefix),
        }
        if condition is not None:
            arguments["FilterExpression"] = condition
        paginator = self.table.meta.client.get_paginator("query")
        return [item for page in paginator.paginate(**arguments) for item in page["Items"]]


def _batch_partition(batch_id: str) -> str:
    return BATCH_PARTITION.format(batch_id)


def _listing_sort(meta: BatchMeta) -> str:
    created = meta.created_at.astimezone(UTC).strftime(LISTING_TIME_FORMAT)
    return f"{created}#{meta.batch_id}"


def _item(partition: str, sort: str, model: StrictModel) -> dict[str, Any]:
    """A model as a table item; floats become Decimals, the only fraction DynamoDB accepts."""
    attributes = json.loads(model.model_dump_json(exclude_none=True), parse_float=Decimal)
    return {PARTITION_KEY: partition, SORT_KEY: sort, **attributes}


def _parse[T: StrictModel](item: Mapping[str, Any], model: type[T]) -> T:
    attributes = {name: value for name, value in item.items() if name not in KEY_ATTRIBUTES}
    try:
        return model.model_validate(attributes)
    except ValidationError as error:
        msg = (
            f"item {item[PARTITION_KEY]}/{item[SORT_KEY]} is not a valid {model.__name__}: "
            f"{format_validation_errors(error)}"
        )
        raise InputValidationError(msg) from error
