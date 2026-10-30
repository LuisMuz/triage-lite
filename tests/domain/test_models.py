from typing import Any

import pytest
from pydantic import ValidationError

from triagelite.domain.enums import CallStatus, Category, Severity, Stage, TriageStatus
from triagelite.domain.models import (
    RATIONALE_MAX_CHARS,
    CandidatePair,
    Classification,
    ClassifyOutput,
    DuplicateCluster,
    Incident,
    IncidentClassification,
    JudgeOutput,
    LLMCallRecord,
    PairJudgement,
    PairVerdict,
    RawIncident,
    RowError,
)


def classification_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "incident_id": "inc-001",
        "rationale": "Payment is charged twice with no workaround.",
        "severity": "critical",
        "category": "functional",
        "component": "payments",
        "confidence": 0.9,
    }
    return data | overrides


def call_record_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "call_id": "call-1",
        "stage": "classify",
        "model_id": "test-model",
        "prompt_version": "classify/v1",
        "input_tokens": 1200,
        "output_tokens": 300,
        "cost_usd": 0.0027,
        "latency_ms": 850,
        "stop_reason": "tool_use",
        "attempt": 1,
        "status": "ok",
    }
    return data | overrides


class TestClassification:
    def test_valid_classification_parses_into_enums(self) -> None:
        result = Classification.model_validate(classification_data())

        assert result.severity is Severity.CRITICAL
        assert result.category is Category.FUNCTIONAL

    def test_extra_field_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            Classification.model_validate(classification_data(priority="P1"))

    @pytest.mark.parametrize("severity", ["blocker", "CRITICAL", ""])
    def test_unknown_severity_is_rejected(self, severity: str) -> None:
        with pytest.raises(ValidationError, match="severity"):
            Classification.model_validate(classification_data(severity=severity))

    @pytest.mark.parametrize("confidence", [1.2, -0.1])
    def test_confidence_outside_unit_interval_is_rejected(self, confidence: float) -> None:
        with pytest.raises(ValidationError, match="confidence"):
            Classification.model_validate(classification_data(confidence=confidence))

    def test_rationale_over_limit_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="rationale"):
            Classification.model_validate(
                classification_data(rationale="x" * (RATIONALE_MAX_CHARS + 1))
            )

    @pytest.mark.parametrize("component", ["Payments", "pay ments", "", "1cart"])
    def test_component_must_be_a_slug(self, component: str) -> None:
        with pytest.raises(ValidationError, match="component"):
            Classification.model_validate(classification_data(component=component))

    def test_schema_lists_rationale_before_labels(self) -> None:
        fields = list(Classification.model_json_schema()["properties"])

        assert fields.index("rationale") < fields.index("severity")

    def test_is_immutable(self) -> None:
        result = Classification.model_validate(classification_data())

        with pytest.raises(ValidationError, match="frozen"):
            result.severity = Severity.LOW  # type: ignore[misc]  # asserting the runtime guard


class TestClassifyOutput:
    def test_empty_items_are_rejected(self) -> None:
        with pytest.raises(ValidationError, match="items"):
            ClassifyOutput.model_validate({"items": []})

    def test_one_bad_item_fails_the_whole_output(self) -> None:
        payload = {"items": [classification_data(), classification_data(confidence=2)]}

        with pytest.raises(ValidationError, match=r"items\.1\.confidence"):
            ClassifyOutput.model_validate(payload)


class TestRawIncident:
    def test_blank_optional_cells_become_none(self) -> None:
        row = RawIncident.model_validate(
            {
                "external_id": "QA-1",
                "title": "  Login fails  ",
                "description": "500 on submit",
                "steps": "",
                "environment": "   ",
                "reported_at": "",
                "reporter": "",
            }
        )

        assert row.title == "Login fails"
        assert row.steps is None
        assert row.environment is None
        assert row.reported_at is None
        assert row.reporter is None

    @pytest.mark.parametrize("field", ["external_id", "title", "description"])
    def test_required_text_cannot_be_blank(self, field: str) -> None:
        data = {"external_id": "QA-1", "title": "t", "description": "d"} | {field: "  "}

        with pytest.raises(ValidationError, match=field):
            RawIncident.model_validate(data)

    def test_reported_at_parses_iso_timestamp(self) -> None:
        row = RawIncident.model_validate(
            {
                "external_id": "QA-1",
                "title": "t",
                "description": "d",
                "reported_at": "2026-10-20T14:30:00Z",
            }
        )

        assert row.reported_at is not None
        assert row.reported_at.year == 2026


class TestIncident:
    def test_unsupported_language_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="lang"):
            Incident.model_validate(
                {
                    "incident_id": "inc-001",
                    "external_id": "QA-1",
                    "lang": "pt",
                    "lang_confidence": 0.8,
                    "title": "t",
                    "description": "d",
                }
            )

    def test_reporter_is_not_a_field(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            Incident.model_validate(
                {
                    "incident_id": "inc-001",
                    "external_id": "QA-1",
                    "lang": "es",
                    "lang_confidence": 0.8,
                    "title": "t",
                    "description": "d",
                    "reporter": "ana@example.com",
                }
            )


class TestLLMCallRecord:
    def test_successful_call_parses(self) -> None:
        record = LLMCallRecord.model_validate(call_record_data())

        assert record.stage is Stage.CLASSIFY
        assert record.status is CallStatus.OK

    def test_failed_call_requires_error_type(self) -> None:
        with pytest.raises(ValidationError, match="error_type"):
            LLMCallRecord.model_validate(call_record_data(status="rate_limited"))

    def test_failed_call_with_error_type_parses(self) -> None:
        record = LLMCallRecord.model_validate(
            call_record_data(status="rate_limited", error_type="LLMRateLimitError")
        )

        assert record.error_type == "LLMRateLimitError"

    def test_successful_call_rejects_error_type(self) -> None:
        with pytest.raises(ValidationError, match="error_type"):
            LLMCallRecord.model_validate(call_record_data(error_type="LLMRateLimitError"))

    @pytest.mark.parametrize(
        ("field", "value"),
        [("input_tokens", -1), ("cost_usd", -0.01), ("latency_ms", -5), ("attempt", 0)],
    )
    def test_counters_cannot_be_negative(self, field: str, value: float) -> None:
        with pytest.raises(ValidationError, match=field):
            LLMCallRecord.model_validate(call_record_data(**{field: value}))


class TestIncidentClassification:
    def test_classified_needs_matching_labels(self) -> None:
        result = IncidentClassification.model_validate(
            {
                "incident_id": "inc-001",
                "status": "classified",
                "classification": classification_data(),
            }
        )

        assert result.status is TriageStatus.CLASSIFIED

    @pytest.mark.parametrize(
        "data",
        [
            {"incident_id": "inc-001", "status": "classified"},
            {
                "incident_id": "inc-002",
                "status": "classified",
                "classification": classification_data(),
            },
            {
                "incident_id": "inc-001",
                "status": "classified",
                "classification": classification_data(),
                "reason": "x",
            },
            {"incident_id": "inc-001", "status": "needs_manual"},
            {
                "incident_id": "inc-001",
                "status": "needs_manual",
                "reason": "x",
                "classification": classification_data(),
            },
        ],
        ids=["no-labels", "wrong-id", "reason-on-success", "no-reason", "labels-on-manual"],
    )
    def test_inconsistent_results_are_rejected(self, data: dict[str, Any]) -> None:
        with pytest.raises(ValidationError, match="inconsistent"):
            IncidentClassification.model_validate(data)


def test_row_error_needs_at_least_one_message() -> None:
    with pytest.raises(ValidationError, match="errors"):
        RowError(line=2, errors=[])


PAIR = CandidatePair(pair_id="p-0001", first_id="inc-1", second_id="inc-2", similarity=0.8)


def judgement(pair_id: str = "p-0001", is_duplicate: bool = True) -> PairJudgement:
    return PairJudgement(
        pair_id=pair_id,
        rationale="Same 500 on checkout.",
        is_duplicate=is_duplicate,
        confidence=0.9,
    )


class TestJudgeModels:
    def test_schema_lists_rationale_before_the_answer(self) -> None:
        fields = list(PairJudgement.model_json_schema()["properties"])

        assert fields.index("rationale") < fields.index("is_duplicate")

    def test_empty_judge_output_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            JudgeOutput(items=[])

    def test_judged_verdict_merges_only_when_true(self) -> None:
        assert PairVerdict(pair=PAIR, judgement=judgement()).is_duplicate
        assert not PairVerdict(pair=PAIR, judgement=judgement(is_duplicate=False)).is_duplicate
        assert not PairVerdict(pair=PAIR, reason="model unavailable").is_duplicate

    @pytest.mark.parametrize(
        "data",
        [
            {"judgement": judgement(pair_id="p-0002")},
            {"judgement": judgement(), "reason": "both"},
            {},
        ],
    )
    def test_inconsistent_verdict_is_rejected(self, data: dict[str, Any]) -> None:
        with pytest.raises(ValidationError, match="inconsistent verdict"):
            PairVerdict(pair=PAIR, **data)

    @pytest.mark.parametrize("members", [["inc-2", "inc-1"], ["inc-1", "inc-1"]])
    def test_cluster_starts_with_its_canonical_and_has_unique_members(
        self, members: list[str]
    ) -> None:
        with pytest.raises(ValidationError, match="must start with its canonical"):
            DuplicateCluster(cluster_id="cl-0001", canonical_id="inc-1", member_ids=members)
