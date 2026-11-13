"""Read API behind the HTTP API: batches, their incidents and their reports, as JSON."""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from triagelite.domain.enums import BatchStatus
from triagelite.domain.errors import NotFoundError, RequestValidationError
from triagelite.domain.models import BatchMeta, IncidentRecord, Language, StrictModel
from triagelite.domain.validation import format_validation_errors
from triagelite.handlers.runtime import batch_table, data_store, pipeline_config
from triagelite.logs import log_fields
from triagelite.pipeline.config import ApiConfig
from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store

LOGGER = logging.getLogger("triagelite.handlers.api")
STAGE = "api"
JSON_HEADERS = {"content-type": "application/json"}

VerbatimText = Annotated[str, StringConstraints(strip_whitespace=False)]
BatchId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{0,99}$")]


class HttpEvent(BaseModel):
    """The parts of an HTTP API (payload 2.0) event the API reads; API Gateway adds many more."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    route_key: str = Field(alias="routeKey")
    path_parameters: dict[str, str] | None = Field(default=None, alias="pathParameters")
    query_string_parameters: dict[str, str] | None = Field(
        default=None, alias="queryStringParameters"
    )


class BatchPath(StrictModel):
    """`/batches/{id}`."""

    id: BatchId


class IncidentsQuery(StrictModel):
    """`?needs_manual=true|false`, or nothing for every incident."""

    needs_manual: bool | None = None


class ReportQuery(StrictModel):
    """`?lang=es|en`."""

    lang: Language


class BatchList(StrictModel):
    """`GET /batches`: newest first."""

    batches: list[BatchMeta]


class IncidentList(StrictModel):
    """`GET /batches/{id}/incidents`."""

    batch_id: str
    incidents: list[IncidentRecord]


class Report(StrictModel):
    """`GET /batches/{id}/report`: the Markdown report, inline."""

    batch_id: str
    lang: Language
    markdown: VerbatimText


class ErrorDetail(StrictModel):
    """A machine-readable code and a message safe to show the caller."""

    code: str
    message: str


class ErrorBody(StrictModel):
    """The one shape every error response has."""

    error: ErrorDetail


@dataclass(frozen=True)
class Response:
    """What a route returns: a status and a body model."""

    status: HTTPStatus
    body: StrictModel


type Route = Callable[[HttpEvent, BatchTable, S3Store, ApiConfig], Response]


def _params[T: StrictModel](model: type[T], values: Mapping[str, str] | None) -> T:
    try:
        return model.model_validate(values or {})
    except ValidationError as error:
        raise RequestValidationError("; ".join(format_validation_errors(error))) from error


def list_batches(
    _event: HttpEvent, table: BatchTable, _store: S3Store, config: ApiConfig
) -> Response:
    """The latest batches, newest first."""
    return Response(
        status=HTTPStatus.OK, body=BatchList(batches=table.list_batches(config.batch_list_limit))
    )


def get_batch(event: HttpEvent, table: BatchTable, _store: S3Store, _config: ApiConfig) -> Response:
    """One batch: status, totals and report keys."""
    path = _params(BatchPath, event.path_parameters)
    return Response(status=HTTPStatus.OK, body=table.get_batch(path.id))


def list_incidents(
    event: HttpEvent, table: BatchTable, _store: S3Store, _config: ApiConfig
) -> Response:
    """A batch's incidents, optionally only those that do or don't need a human."""
    path = _params(BatchPath, event.path_parameters)
    query = _params(IncidentsQuery, event.query_string_parameters)
    table.get_batch(path.id)
    incidents = table.list_incidents(path.id, needs_manual=query.needs_manual)
    return Response(status=HTTPStatus.OK, body=IncidentList(batch_id=path.id, incidents=incidents))


def get_report(event: HttpEvent, table: BatchTable, store: S3Store, _config: ApiConfig) -> Response:
    """A finished batch's report in one language."""
    path = _params(BatchPath, event.path_parameters)
    query = _params(ReportQuery, event.query_string_parameters)
    meta = table.get_batch(path.id)
    key = meta.report_keys.get(query.lang)
    if meta.status is not BatchStatus.DONE or key is None:
        msg = f"batch {path.id} has no report yet (status {meta.status})"
        raise NotFoundError(msg)
    try:
        markdown = store.read_text(key)
    except NotFoundError:
        msg = f"the {query.lang} report of batch {path.id} is missing"
        raise NotFoundError(msg) from None
    return Response(
        status=HTTPStatus.OK, body=Report(batch_id=path.id, lang=query.lang, markdown=markdown)
    )


ROUTES: dict[str, Route] = {
    "GET /batches": list_batches,
    "GET /batches/{id}": get_batch,
    "GET /batches/{id}/incidents": list_incidents,
    "GET /batches/{id}/report": get_report,
}


def _error(status: HTTPStatus, code: str, message: str) -> Response:
    return Response(status=status, body=ErrorBody(error=ErrorDetail(code=code, message=message)))


def dispatch(
    event: Mapping[str, object], table: BatchTable, store: S3Store, config: ApiConfig
) -> Response:
    """Run the route API Gateway matched; known failures become 4xx, anything else a 500."""
    try:
        request = HttpEvent.model_validate(event)
    except ValidationError:
        return _error(HTTPStatus.BAD_REQUEST, "bad_request", "not an HTTP API request")
    route = ROUTES.get(request.route_key)
    if route is None:
        return _error(HTTPStatus.NOT_FOUND, "not_found", f"no route {request.route_key}")
    try:
        return route(request, table, store, config)
    except RequestValidationError as error:
        return _error(HTTPStatus.BAD_REQUEST, "bad_request", str(error))
    except NotFoundError as error:
        return _error(HTTPStatus.NOT_FOUND, "not_found", str(error))
    except Exception:
        LOGGER.exception("request failed", extra=log_fields(stage=STAGE, route=request.route_key))
        return _error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal", "the request failed")


def to_http(response: Response) -> dict[str, object]:
    """Lambda proxy response for HTTP API payload 2.0."""
    return {
        "statusCode": int(response.status),
        "headers": JSON_HEADERS,
        "body": response.body.model_dump_json(),
    }


def handler(event: Mapping[str, object], _context: object) -> dict[str, object]:
    """Lambda entry point."""
    response = dispatch(event, batch_table(), data_store(), pipeline_config().api)
    LOGGER.info(
        "request",
        extra=log_fields(
            stage=STAGE, route=event.get("routeKey"), status_code=int(response.status)
        ),
    )
    return to_http(response)
