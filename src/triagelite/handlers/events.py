"""What Step Functions passes to each handler and gets back: IDs and S3 keys, never data."""

from collections.abc import Mapping
from typing import Annotated, Self

from pydantic import StringConstraints, ValidationError, model_validator

from triagelite.domain.errors import InputValidationError
from triagelite.domain.models import NonEmptyStr, StrictModel
from triagelite.domain.validation import format_validation_errors
from triagelite.handlers.work import chunks_prefix

StateName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9]{0,79}$")]
ErrorName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_.]{0,127}$")]


class NormalizeEvent(StrictModel):
    """A CSV that arrived in the bucket."""

    source_key: NonEmptyStr


class BatchEvent(StrictModel):
    """One batch and its chunks; a later stage reads what earlier stages wrote from these."""

    batch_id: NonEmptyStr
    chunk_keys: list[NonEmptyStr]


class ChunkEvent(StrictModel):
    """One chunk of one batch."""

    batch_id: NonEmptyStr
    chunk_key: NonEmptyStr

    @model_validator(mode="after")
    def _chunk_belongs_to_batch(self) -> Self:
        """A key from another batch would mix its incidents into this batch's results."""
        if not self.chunk_key.startswith(chunks_prefix(self.batch_id)):
            msg = f"{self.chunk_key} is not a chunk of batch {self.batch_id}"
            raise ValueError(msg)
        return self


class FailedEvent(StrictModel):
    """A batch the state machine gave up on: the state that failed and the error's name.

    Only the name is accepted, never the cause, which can quote incident text.
    """

    batch_id: NonEmptyStr
    failed_state: StateName
    error: ErrorName


class StageResult(StrictModel):
    """The keys a stage wrote."""

    batch_id: NonEmptyStr
    keys: list[NonEmptyStr]


def parse_event[T: StrictModel](model: type[T], event: Mapping[str, object]) -> T:
    """Validate a Lambda event.

    Raises:
        InputValidationError: the event does not match `model`.
    """
    try:
        return model.model_validate(event)
    except ValidationError as error:
        msg = f"invalid {model.__name__}: {format_validation_errors(error)}"
        raise InputValidationError(msg) from error
