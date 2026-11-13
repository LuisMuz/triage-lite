import json
from http import HTTPStatus

import pytest

from tests.handlers.test_stages import (
    NOW,
    PIPELINE,
    run_after_classify,
    run_classify,
    run_normalize,
)
from tests.pipeline.conftest import answer_all
from triagelite.domain.enums import BatchStatus, TriageStatus
from triagelite.domain.models import Language
from triagelite.handlers import api, mark_failed
from triagelite.handlers.events import BatchEvent, FailedEvent
from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store, report_key

CONFIG = PIPELINE.api


def request(
    route: str, batch_id: str | None = None, query: dict[str, str] | None = None
) -> dict[str, object]:
    event: dict[str, object] = {
        "version": "2.0",
        "routeKey": route,
        "rawPath": route.split(" ")[1],
        "requestContext": {"http": {"method": "GET"}},
    }
    if batch_id is not None:
        event["pathParameters"] = {"id": batch_id}
    if query is not None:
        event["queryStringParameters"] = query
    return event


def call(
    table: BatchTable, store: S3Store, event: dict[str, object]
) -> tuple[int, dict[str, object]]:
    response = api.to_http(api.dispatch(event, table, store, CONFIG))
    body = response["body"]
    assert isinstance(body, str)
    assert response["headers"] == {"content-type": "application/json"}
    status = response["statusCode"]
    assert isinstance(status, int)
    parsed: dict[str, object] = json.loads(body)
    return status, parsed


def done_batch(store: S3Store, table: BatchTable) -> BatchEvent:
    batch = run_normalize(store, table)
    run_classify(store, batch, batch.chunk_keys[0], [answer_all()])
    run_after_classify(store, table, batch)
    return batch


def error_of(body: dict[str, object]) -> object:
    error = body["error"]
    assert isinstance(error, dict)
    assert set(error) == {"code", "message"}
    return error["code"]


def test_batches_are_listed_newest_first(store: S3Store, table: BatchTable) -> None:
    batch = done_batch(store, table)

    status, body = call(table, store, request("GET /batches"))

    assert status == HTTPStatus.OK
    batches = body["batches"]
    assert isinstance(batches, list)
    assert [(b["batch_id"], b["status"]) for b in batches] == [
        (batch.batch_id, BatchStatus.DONE.value)
    ]


def test_a_batch_shows_its_totals_and_report_keys(store: S3Store, table: BatchTable) -> None:
    batch = done_batch(store, table)

    status, body = call(table, store, request("GET /batches/{id}", batch.batch_id))

    assert status == HTTPStatus.OK
    assert body["status"] == BatchStatus.DONE.value
    assert body["report_keys"] == {
        "es": report_key(batch.batch_id, "es"),
        "en": report_key(batch.batch_id, "en"),
    }


def test_incidents_can_be_filtered_to_those_needing_a_human(
    store: S3Store, table: BatchTable
) -> None:
    batch = done_batch(store, table)

    _, everything = call(table, store, request("GET /batches/{id}/incidents", batch.batch_id))
    status, manual = call(
        table,
        store,
        request("GET /batches/{id}/incidents", batch.batch_id, {"needs_manual": "true"}),
    )

    assert status == HTTPStatus.OK
    all_incidents = everything["incidents"]
    manual_incidents = manual["incidents"]
    assert isinstance(all_incidents, list)
    assert isinstance(manual_incidents, list)
    assert len(manual_incidents) == len(batch.chunk_keys[1:]) * PIPELINE.normalize.chunk_size
    assert {i["status"] for i in manual_incidents} == {TriageStatus.NEEDS_MANUAL.value}
    assert len(all_incidents) > len(manual_incidents)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_a_report_comes_back_inline(store: S3Store, table: BatchTable, lang: Language) -> None:
    batch = done_batch(store, table)

    status, body = call(
        table, store, request("GET /batches/{id}/report", batch.batch_id, {"lang": lang})
    )

    assert status == HTTPStatus.OK
    assert body["lang"] == lang
    assert body["markdown"] == store.read_text(report_key(batch.batch_id, lang))


def test_a_running_batch_has_no_report_yet(store: S3Store, table: BatchTable) -> None:
    batch = run_normalize(store, table)

    status, body = call(
        table, store, request("GET /batches/{id}/report", batch.batch_id, {"lang": "en"})
    )

    assert status == HTTPStatus.NOT_FOUND
    assert error_of(body) == "not_found"
    assert "status running" in str(body)


def test_a_failed_batch_shows_its_reason(store: S3Store, table: BatchTable) -> None:
    batch = run_normalize(store, table)
    event = FailedEvent(batch_id=batch.batch_id, failed_state="Dedupe", error="States.Timeout")
    mark_failed.run(event, table, NOW)

    _, body = call(table, store, request("GET /batches/{id}", batch.batch_id))

    assert (body["status"], body["error"]) == ("failed", "Dedupe failed with States.Timeout")


@pytest.mark.parametrize(
    "route",
    ["GET /batches/{id}", "GET /batches/{id}/incidents", "GET /batches/{id}/report"],
)
def test_an_unknown_batch_is_not_found(store: S3Store, table: BatchTable, route: str) -> None:
    query = {"lang": "es"} if route.endswith("report") else None

    status, body = call(table, store, request(route, "nope-1234", query))

    assert status == HTTPStatus.NOT_FOUND
    assert error_of(body) == "not_found"


@pytest.mark.parametrize(
    ("route", "batch_id", "query"),
    [
        ("GET /batches/{id}", "../etc", None),
        ("GET /batches/{id}/incidents", "b-1", {"needs_manual": "maybe"}),
        ("GET /batches/{id}/incidents", "b-1", {"limit": "5"}),
        ("GET /batches/{id}/report", "b-1", {"lang": "fr"}),
        ("GET /batches/{id}/report", "b-1", None),
    ],
)
def test_bad_parameters_are_a_400_in_the_error_shape(
    store: S3Store,
    table: BatchTable,
    route: str,
    batch_id: str,
    query: dict[str, str] | None,
) -> None:
    status, body = call(table, store, request(route, batch_id, query))

    assert status == HTTPStatus.BAD_REQUEST
    assert error_of(body) == "bad_request"


def test_a_bad_parameter_is_named_in_plain_text(store: S3Store, table: BatchTable) -> None:
    _, body = call(table, store, request("GET /batches/{id}/report", "b-1", {"lang": "fr"}))

    assert body["error"] == {
        "code": "bad_request",
        "message": "lang: Input should be 'es' or 'en'",
    }


def test_a_route_the_api_does_not_serve_is_not_found(store: S3Store, table: BatchTable) -> None:
    status, body = call(table, store, request("DELETE /batches/{id}", "b-1"))

    assert status == HTTPStatus.NOT_FOUND
    assert error_of(body) == "not_found"


def test_an_event_that_is_not_an_http_request_is_rejected(
    store: S3Store, table: BatchTable
) -> None:
    status, body = call(table, store, {"source_key": "incoming/a.csv"})

    assert status == HTTPStatus.BAD_REQUEST
    assert error_of(body) == "bad_request"


def test_an_unexpected_failure_is_a_500_without_details(
    store: S3Store, table: BatchTable, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(_limit: int) -> list[object]:
        raise RuntimeError("s3://secret-bucket exploded")

    monkeypatch.setattr(table, "list_batches", broken)

    status, body = call(table, store, request("GET /batches"))

    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert error_of(body) == "internal"
    assert "secret-bucket" not in json.dumps(body)
