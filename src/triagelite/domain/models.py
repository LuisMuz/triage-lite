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


class CandidatePair(StrictModel):
    """Two incidents close enough as vectors to be judged; `first_id` was reported earlier."""

    pair_id: NonEmptyStr
    first_id: NonEmptyStr
    second_id: NonEmptyStr
    similarity: float


class PairJudgement(StrictModel):
    """The judge's decision on one pair; `rationale` comes first so the answer follows it."""

    pair_id: NonEmptyStr
    rationale: Annotated[str, Field(min_length=1, max_length=RATIONALE_MAX_CHARS)]
    is_duplicate: bool
    confidence: Probability


class JudgeOutput(StrictModel):
    """Tool input for `submit_judgements`: one item per pair in the chunk."""

    items: Annotated[list[PairJudgement], Field(min_length=1)]


class PairVerdict(StrictModel):
    """Outcome of judging one candidate pair: a judgement, or why there is none."""

    pair: CandidatePair
    judgement: PairJudgement | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _judgement_or_reason(self) -> Self:
        """Judged pairs carry their own judgement; unjudged pairs carry only a reason."""
        if self.judgement is not None:
            ok = self.judgement.pair_id == self.pair.pair_id and self.reason is None
        else:
            ok = bool(self.reason)
        if not ok:
            msg = f"inconsistent verdict for {self.pair.pair_id}"
            raise ValueError(msg)
        return self

    @property
    def is_duplicate(self) -> bool:
        """Only a judged `true` merges; an unjudged pair stays apart."""
        return self.judgement is not None and self.judgement.is_duplicate


class DuplicateCluster(StrictModel):
    """A canonical incident and every incident confirmed as its duplicate (canonical first)."""

    cluster_id: NonEmptyStr
    canonical_id: NonEmptyStr
    member_ids: Annotated[list[NonEmptyStr], Field(min_length=1)]

    @model_validator(mode="after")
    def _canonical_leads(self) -> Self:
        """The canonical is the first member and nobody appears twice."""
        if self.member_ids[0] != self.canonical_id or len(set(self.member_ids)) != len(
            self.member_ids
        ):
            msg = f"cluster {self.cluster_id} must start with its canonical and have unique members"
            raise ValueError(msg)
        return self


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
    candidate_pairs: NonNegativeInt
    pairs_dropped_by_cap: NonNegativeInt
    confirmed_pairs: NonNegativeInt
    unjudged_pairs: NonNegativeInt
    clusters: NonNegativeInt
    duplicate_incidents: NonNegativeInt
