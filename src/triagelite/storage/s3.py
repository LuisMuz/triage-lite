"""Batch files in the data bucket: inputs, work passed between stages, and reports."""

from collections.abc import Iterable
from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from triagelite.domain.errors import InputValidationError, NotFoundError
from triagelite.domain.models import Language, StrictModel
from triagelite.domain.validation import format_validation_errors

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

WORK_PREFIX = "work"
REPORTS_PREFIX = "reports"
TEXT_ENCODING = "utf-8"
MARKDOWN_TYPE = "text/markdown; charset=utf-8"
JSON_TYPE = "application/json"
JSONL_TYPE = "application/x-ndjson"


def work_key(batch_id: str, name: str) -> str:
    """Key of a file passed between stages; these expire with the bucket's lifecycle rule."""
    return f"{WORK_PREFIX}/{batch_id}/{name}"


def report_key(batch_id: str, lang: Language) -> str:
    """Key of a batch's finished report in one language."""
    return f"{REPORTS_PREFIX}/{batch_id}/report.{lang}.md"


class S3Store:
    """Reads and writes one bucket; writing a key again overwrites it."""

    def __init__(self, client: "S3Client", bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    def write_text(self, key: str, text: str, content_type: str = MARKDOWN_TYPE) -> None:
        """Write a text object such as a rendered report."""
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=text.encode(TEXT_ENCODING),
            ContentType=content_type,
        )

    def write_json(self, key: str, item: BaseModel) -> None:
        """Write one JSON document."""
        self.write_text(key, item.model_dump_json(), JSON_TYPE)

    def write_jsonl(self, key: str, items: Iterable[BaseModel]) -> None:
        """Write one JSON object per line."""
        lines = "".join(item.model_dump_json() + "\n" for item in items)
        self.write_text(key, lines, JSONL_TYPE)

    def read_text(self, key: str) -> str:
        """Read a text object.

        Raises:
            NotFoundError: the key does not exist.
            InputValidationError: the content is not UTF-8.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except self.client.exceptions.NoSuchKey:
            msg = f"s3://{self.bucket}/{key} does not exist"
            raise NotFoundError(msg) from None
        with response["Body"] as body:
            content = body.read()
        try:
            return content.decode(TEXT_ENCODING)
        except UnicodeDecodeError as error:
            msg = f"s3://{self.bucket}/{key} is not {TEXT_ENCODING} text"
            raise InputValidationError(msg) from error

    def read_json[T: StrictModel](self, key: str, model: type[T]) -> T:
        """Read and validate one JSON document.

        Raises:
            NotFoundError: the key does not exist.
            InputValidationError: the content does not match `model`.
        """
        return _parse(self.read_text(key), model, key)

    def read_jsonl[T: StrictModel](self, key: str, model: type[T]) -> list[T]:
        """Read and validate one JSON object per line.

        Raises:
            NotFoundError: the key does not exist.
            InputValidationError: a line does not match `model`.
        """
        return [
            _parse(line, model, f"{key} line {number}")
            for number, line in enumerate(self.read_text(key).splitlines(), start=1)
        ]


def _parse[T: StrictModel](text: str, model: type[T], where: str) -> T:
    try:
        return model.model_validate_json(text)
    except ValidationError as error:
        msg = f"{where} is not a valid {model.__name__}: {format_validation_errors(error)}"
        raise InputValidationError(msg) from error
