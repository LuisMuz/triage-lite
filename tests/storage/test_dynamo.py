from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

import boto3
import pytest
from moto import mock_aws
from pydantic import ValidationError

from triagelite.domain.enums import BatchStatus, Category, PiiKind, Severity, TriageStatus
from triagelite.domain.errors import InputValidationError, NotFoundError
from triagelite.domain.models import (
    BatchMeta,
    Classification,
    DuplicateCluster,
    IncidentRecord,
    RunSummary,
)
from triagelite.storage.dynamo import BatchTable

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

TABLE = "test-table"
REGION = "us-east-1"
T0 = datetime(2026, 11, 3, 10, 0, tzinfo=UTC)
T1 = T0 + timedelta(hours=1)
T2 = T0 + timedelta(hours=2)


@pytest.fixture
def raw_table() -> Iterator["Table"]:
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name=REGION)
        yield resource.create_table(
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


@pytest.fixture
def table(raw_table: "Table") -> BatchTable:
    return BatchTable(raw_table)


def summary(batch_id: str = "b-1") -> RunSummary:
    return RunSummary(
        batch_id=batch_id,
        incidents=2,
        row_errors=0,
        classified=2,
        needs_manual=0,
        llm_calls=3,
        cost_usd=0.1,
        cost_per_100_incidents_usd=0.2134,
        pii_redactions=dict.fromkeys(PiiKind, 1),
        candidate_pairs=1,
        pairs_dropped_by_cap=0,
        confirmed_pairs=1,
        unjudged_pairs=0,
        clusters=1,
        duplicate_incidents=1,
        reports_from_template=["es"],
    )


def classified(incident_id: str, confidence: float = 0.1, title: str = "t") -> IncidentRecord:
    return IncidentRecord(
        incident_id=incident_id,
        status=TriageStatus.CLASSIFIED,
        classification=Classification(
            incident_id=incident_id,
            rationale="r",
            severity=Severity.HIGH,
            category=Category.CRASH,
            component="checkout",
            confidence=confidence,
        ),
        external_id=f"ext-{incident_id}",
        title=title,
        lang="es",
    )


def needs_manual(incident_id: str) -> IncidentRecord:
    return IncidentRecord(
        incident_id=incident_id,
        status=TriageStatus.NEEDS_MANUAL,
        reason="model unavailable",
        external_id=f"ext-{incident_id}",
        title="t",
        lang="en",
    )


def cluster(cluster_id: str, *members: str) -> DuplicateCluster:
    return DuplicateCluster(
        cluster_id=cluster_id, canonical_id=members[0], member_ids=list(members)
    )


class TestBatch:
    def test_start_creates_a_running_batch(self, table: BatchTable) -> None:
        meta = table.start_batch("b-1", "incoming/a.csv", T0)

        assert meta.status is BatchStatus.RUNNING
        assert table.get_batch("b-1") == meta
        assert meta.created_at == T0

    def test_unknown_batch_is_a_typed_error(self, table: BatchTable) -> None:
        with pytest.raises(NotFoundError, match="b-404"):
            table.get_batch("b-404")

    def test_restart_keeps_created_at_and_one_listing(self, table: BatchTable) -> None:
        table.start_batch("b-1", "incoming/a.csv", T0)
        table.finish_batch("b-1", summary(), {"es": "reports/b-1/report.es.md"}, T1)

        restarted = table.start_batch("b-1", "incoming/a.csv", T2)

        assert restarted.created_at == T0
        assert restarted.updated_at == T2
        assert restarted.status is BatchStatus.RUNNING
        assert restarted.summary is None
        assert restarted.report_keys == {}
        assert [b.batch_id for b in table.list_batches(10)] == ["b-1"]

    def test_finish_stores_totals_and_exact_decimals(self, table: BatchTable) -> None:
        table.start_batch("b-1", "incoming/a.csv", T0)

        done = table.finish_batch("b-1", summary(), {"es": "k-es", "en": "k-en"}, T1)

        stored = table.get_batch("b-1")
        assert stored == done
        assert stored.status is BatchStatus.DONE
        assert stored.summary is not None
        assert stored.summary.cost_usd == 0.1
        assert stored.summary.pii_redactions[PiiKind.EMAIL] == 1
        assert stored.report_keys == {"es": "k-es", "en": "k-en"}

    def test_fail_records_the_reason(self, table: BatchTable) -> None:
        table.start_batch("b-1", "incoming/a.csv", T0)

        table.fail_batch("b-1", "Normalize failed", T1)

        stored = table.get_batch("b-1")
        assert (stored.status, stored.error) == (BatchStatus.FAILED, "Normalize failed")

    def test_finishing_an_unknown_batch_is_a_typed_error(self, table: BatchTable) -> None:
        with pytest.raises(NotFoundError):
            table.finish_batch("b-404", summary("b-404"), {}, T1)

    def test_listing_shows_the_latest_status(self, table: BatchTable) -> None:
        table.start_batch("b-1", "incoming/a.csv", T0)
        table.fail_batch("b-1", "boom", T1)

        assert [b.status for b in table.list_batches(10)] == [BatchStatus.FAILED]

    def test_listing_is_newest_first_and_limited(self, table: BatchTable) -> None:
        for index, moment in enumerate([T0, T2, T1]):
            table.start_batch(f"b-{index}", "incoming/a.csv", moment)

        assert [b.batch_id for b in table.list_batches(2)] == ["b-1", "b-2"]

    def test_listing_sorts_by_instant_across_time_zones(self, table: BatchTable) -> None:
        mexico = timezone(timedelta(hours=-6))
        table.start_batch("later", "incoming/a.csv", T0.astimezone(mexico) + timedelta(minutes=1))
        table.start_batch("earlier", "incoming/a.csv", T0)

        assert [b.batch_id for b in table.list_batches(10)] == ["later", "earlier"]

    def test_empty_listing(self, table: BatchTable) -> None:
        assert table.list_batches(10) == []

    def test_corrupt_item_is_a_typed_error(self, table: BatchTable, raw_table: "Table") -> None:
        raw_table.put_item(Item={"PK": "BATCH#b-1", "SK": "META", "status": "nonsense"})

        with pytest.raises(InputValidationError, match="BATCH#b-1"):
            table.get_batch("b-1")


class TestBatchMetaRules:
    @pytest.mark.parametrize(
        ("status", "payload"),
        [
            (BatchStatus.DONE, {}),
            (BatchStatus.FAILED, {}),
            (BatchStatus.RUNNING, {"error": "x"}),
            (BatchStatus.DONE, {"summary": summary(), "error": "x"}),
            (BatchStatus.FAILED, {"summary": summary(), "error": "x"}),
        ],
    )
    def test_inconsistent_states_are_rejected(
        self, status: BatchStatus, payload: dict[str, object]
    ) -> None:
        with pytest.raises(ValidationError, match="inconsistent"):
            BatchMeta.model_validate(
                {
                    "batch_id": "b",
                    "status": status,
                    "source_key": "k",
                    "created_at": T0,
                    "updated_at": T0,
                    **payload,
                }
            )

    def test_naive_timestamps_are_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BatchMeta.model_validate(
                {
                    "batch_id": "b",
                    "status": BatchStatus.RUNNING,
                    "source_key": "k",
                    "created_at": "2026-11-03T10:00:00",
                    "updated_at": T0,
                }
            )


class TestIncidents:
    def test_round_trip_keeps_float_values_exact(self, table: BatchTable) -> None:
        record = classified("inc-0001", confidence=0.1)

        table.put_incidents("b-1", [record])

        assert table.list_incidents("b-1") == [record]

    def test_more_than_one_write_batch(self, table: BatchTable) -> None:
        records = [classified(f"inc-{i:04d}") for i in range(60)]

        table.put_incidents("b-1", records)

        assert [r.incident_id for r in table.list_incidents("b-1")] == [
            r.incident_id for r in records
        ]

    def test_reads_every_page(self, table: BatchTable) -> None:
        big_title = "x" * 60_000
        records = [classified(f"inc-{i:04d}", title=big_title) for i in range(40)]

        table.put_incidents("b-1", records)

        assert len(table.list_incidents("b-1")) == 40

    def test_writing_again_overwrites(self, table: BatchTable) -> None:
        table.put_incidents("b-1", [classified("inc-0001")])

        table.put_incidents("b-1", [needs_manual("inc-0001")])

        assert table.list_incidents("b-1") == [needs_manual("inc-0001")]

    def test_needs_manual_filter(self, table: BatchTable) -> None:
        table.put_incidents("b-1", [classified("inc-0001"), needs_manual("inc-0002")])

        assert [r.incident_id for r in table.list_incidents("b-1", needs_manual=True)] == [
            "inc-0002"
        ]
        assert [r.incident_id for r in table.list_incidents("b-1", needs_manual=False)] == [
            "inc-0001"
        ]

    def test_only_this_batchs_incidents(self, table: BatchTable) -> None:
        table.start_batch("b-1", "incoming/a.csv", T0)
        table.put_incidents("b-1", [classified("inc-0001")])
        table.put_incidents("b-2", [classified("inc-0002")])
        table.replace_clusters("b-1", [cluster("c-1", "inc-0001")])

        assert [r.incident_id for r in table.list_incidents("b-1")] == ["inc-0001"]

    def test_no_incidents(self, table: BatchTable) -> None:
        table.put_incidents("b-1", [])

        assert table.list_incidents("b-1") == []


class TestClusters:
    def test_members_get_their_cluster_id(self, table: BatchTable) -> None:
        table.put_incidents("b-1", [classified("inc-0001"), classified("inc-0002")])
        duplicates = cluster("c-1", "inc-0002", "inc-0001")

        table.replace_clusters("b-1", [duplicates])

        assert table.list_clusters("b-1") == [duplicates]
        assert {r.cluster_id for r in table.list_incidents("b-1")} == {"c-1"}

    def test_a_rerun_removes_stale_clusters_and_links(self, table: BatchTable) -> None:
        table.put_incidents(
            "b-1", [classified("inc-0001"), classified("inc-0002"), classified("inc-0003")]
        )
        table.replace_clusters("b-1", [cluster("c-old", "inc-0001", "inc-0002")])

        table.replace_clusters("b-1", [cluster("c-new", "inc-0001", "inc-0003")])

        assert [c.cluster_id for c in table.list_clusters("b-1")] == ["c-new"]
        links = {r.incident_id: r.cluster_id for r in table.list_incidents("b-1")}
        assert links == {"inc-0001": "c-new", "inc-0002": None, "inc-0003": "c-new"}

    def test_a_rerun_can_change_the_members_of_the_same_cluster(self, table: BatchTable) -> None:
        table.put_incidents(
            "b-1", [classified("inc-0001"), classified("inc-0002"), classified("inc-0003")]
        )
        table.replace_clusters("b-1", [cluster("c-1", "inc-0001", "inc-0002")])

        table.replace_clusters("b-1", [cluster("c-1", "inc-0001", "inc-0003")])

        assert table.list_clusters("b-1") == [cluster("c-1", "inc-0001", "inc-0003")]
        links = {r.incident_id: r.cluster_id for r in table.list_incidents("b-1")}
        assert links == {"inc-0001": "c-1", "inc-0002": None, "inc-0003": "c-1"}

    def test_no_clusters_clears_everything(self, table: BatchTable) -> None:
        table.put_incidents("b-1", [classified("inc-0001"), classified("inc-0002")])
        table.replace_clusters("b-1", [cluster("c-1", "inc-0001", "inc-0002")])

        table.replace_clusters("b-1", [])

        assert table.list_clusters("b-1") == []
        assert {r.cluster_id for r in table.list_incidents("b-1")} == {None}

    def test_a_member_without_an_incident_item_is_skipped(self, table: BatchTable) -> None:
        table.put_incidents("b-1", [classified("inc-0001")])

        table.replace_clusters("b-1", [cluster("c-1", "inc-0001", "inc-0404")])

        records = table.list_incidents("b-1")
        assert [(r.incident_id, r.cluster_id) for r in records] == [("inc-0001", "c-1")]
        assert table.list_clusters("b-1")[0].member_ids == ["inc-0001", "inc-0404"]
