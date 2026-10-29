from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
    field_validator,
    model_validator,
)

from triagelite.domain.enums import CallStatus, Category, PiiKind, Severity, Stage, TriageStatus

RATIONALE_MAX_CHARS = 300
COMPONENT_SLUG_PATTERN = r"^[a-z][a-z0-9_]*$"

NonEmptyStr = Annotated[str, Field(min_length=1)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
Language = Literal["es", "en"]


class StrictModel(BaseModel):
    """Base for every boundary model: unknown fields are errors, instances are immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class RawIncident(StrictModel):
    """One CSV row as uploaded, before normalization."""

    external_id: NonEmptyStr
    title: NonEmptyStr
    description: NonEmptyStr
    steps: str | None = None
    environment: str | None = None
    reported_at: datetime | None = None
    reporter: str | None = None

    @field_validator("steps", "environment", "reported_at", "reporter", mode="before")
    @classmethod
    def _blank_is_missing(cls, value: object) -> object:
        """CSV writes a missing optional cell as an empty string; treat it as absent."""
        if isinstance(value, str) and not value.strip():
            return None
        return value


class Incident(StrictModel):
    """A normalized incident: PII scrubbed, reporter dropped, language detected."""

    incident_id: NonEmptyStr
    external_id: NonEmptyStr
    lang: Language
    lang_confidence: Probability
    title: NonEmptyStr
    description: NonEmptyStr
    steps: str | None = None
    environment: str | None = None
    reported_at: datetime | None = None


class Classification(StrictModel):
    """The model's labels for one incident.

    Field order is deliberate: the JSON schema lists `rationale` before the labels, so
    the model writes its reasoning first and the labels follow from it.
    """

    incident_id: NonEmptyStr
    rationale: Annotated[str, Field(min_length=1, max_length=RATIONALE_MAX_CHARS)]
    severity: Severity
    category: Category
    component: Annotated[str, Field(pattern=COMPONENT_SLUG_PATTERN)]
    confidence: Probability


class ClassifyOutput(StrictModel):
    """Tool input for `submit_classifications`: one item per incident in the chunk."""

    items: Annotated[list[Classification], Field(min_length=1)]


class LLMCallRecord(StrictModel):
    """One structured log record per model call attempt, including failed ones."""

    call_id: NonEmptyStr
    stage: Stage
    model_id: NonEmptyStr
    prompt_version: str | None
    input_tokens: Annotated[int, Field(ge=0)]
    output_tokens: Annotated[int, Field(ge=0)]
    cost_usd: Annotated[float, Field(ge=0.0)]
    latency_ms: Annotated[int, Field(ge=0)]
    stop_reason: str | None
    attempt: Annotated[int, Field(ge=1)]
    status: CallStatus
    error_type: str | None = None
    batch_id: str | None = None

    @model_validator(mode="after")
    def _error_type_matches_status(self) -> Self:
        """A failed call must say which error it hit; a successful one must not."""
        failed = self.status is not CallStatus.OK
        if failed != (self.error_type is not None):
            msg = "error_type is required when status is not 'ok', and forbidden when it is"
            raise ValueError(msg)
        return self


class RowError(StrictModel):
    """A CSV row that could not become an incident; the rest of the batch continues."""

    line: PositiveInt
    external_id: str | None = None
    errors: Annotated[list[NonEmptyStr], Field(min_length=1)]


class IncidentClassification(StrictModel):
    """Outcome of the classify stage for one incident: labels, or a reason it needs a human."""

    incident_id: NonEmptyStr
    status: TriageStatus
    classification: Classification | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _status_matches_payload(self) -> Self:
        """Classified items carry their own labels; needs_manual items carry only a reason."""
        if self.status is TriageStatus.CLASSIFIED:
            ok = (
                self.classification is not None
                and self.classification.incident_id == self.incident_id
                and self.reason is None
            )
        else:
            ok = self.classification is None and bool(self.reason)
        if not ok:
            msg = f"inconsistent {self.status} result for {self.incident_id}"
            raise ValueError(msg)
        return self


class RunSummary(StrictModel):
    """Totals for one batch run, written next to its outputs."""

    batch_id: NonEmptyStr
    incidents: NonNegativeInt
    row_errors: NonNegativeInt
    classified: NonNegativeInt
    needs_manual: NonNegativeInt
    llm_calls: NonNegativeInt
    cost_usd: Annotated[float, Field(ge=0.0)]
    cost_per_100_incidents_usd: Annotated[float, Field(ge=0.0)]
    pii_redactions: dict[PiiKind, NonNegativeInt]
