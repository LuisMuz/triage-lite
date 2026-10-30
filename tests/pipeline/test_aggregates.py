import pytest

from tests.pipeline.conftest import classification_item, make_incident
from triagelite.domain.enums import Severity, TriageStatus
from triagelite.domain.models import DuplicateCluster, IncidentClassification
from triagelite.pipeline.aggregates import compute_facts, reports_key
from triagelite.pipeline.config import ReportConfig

CONFIG = ReportConfig(
    max_representative_incidents=15, top_components=2, percent_decimals=1, min_data_token_digits=3
)


def classified(
    number: int, severity: str = "high", component: str = "checkout"
) -> IncidentClassification:
    item = classification_item(f"inc-{number:04d}", component) | {"severity": severity}
    return IncidentClassification.model_validate(
        {"incident_id": f"inc-{number:04d}", "status": "classified", "classification": item}
    )


def manual(number: int) -> IncidentClassification:
    return IncidentClassification(
        incident_id=f"inc-{number:04d}", status=TriageStatus.NEEDS_MANUAL, reason="no answer"
    )


def cluster(number: int, *members: int) -> DuplicateCluster:
    ids = [f"inc-{n:04d}" for n in members]
    return DuplicateCluster(cluster_id=f"cl-{number:04d}", canonical_id=ids[0], member_ids=ids)


INCIDENTS = [make_incident(n) for n in range(1, 6)]
RESULTS = [
    classified(1, "medium", "cart"),
    classified(2, "critical", "checkout"),
    classified(3, "critical", "checkout"),
    classified(4, "low", "search"),
    manual(5),
]
CLUSTERS = [cluster(1, 1), cluster(2, 2, 3), cluster(3, 4), cluster(4, 5)]


def test_counts_and_percentages_come_from_the_results() -> None:
    facts = compute_facts(INCIDENTS, RESULTS, CLUSTERS, 2, CONFIG)
    values = {key: aggregate.value for key, aggregate in facts.aggregates.items()}

    assert values["total.incidents"] == 5
    assert values["total.row_errors"] == 2
    assert (values["total.classified"], values["total.needs_manual"]) == (4, 1)
    assert values["severity.critical.count"] == 2
    assert values["severity.critical.pct"] == pytest.approx(50.0)
    assert values["severity.high.count"] == 0
    assert values["category.crash.count"] == 4
    assert values["component.checkout.count"] == 2
    assert "component.admin.count" not in values
    assert values["clusters.unique_bugs"] == 4
    assert (values["clusters.duplicate_groups"], values["clusters.duplicate_reports"]) == (1, 1)
    assert facts.aggregates["severity.critical.pct"].kind == "percent"
    assert facts.aggregates["total.incidents"].kind == "count"


def test_top_components_by_count_then_name() -> None:
    facts = compute_facts(INCIDENTS, RESULTS, CLUSTERS, 0, CONFIG)

    assert facts.top_components == ["checkout", "cart"]


def test_representatives_are_canonicals_most_severe_and_most_reported_first() -> None:
    facts = compute_facts(INCIDENTS, RESULTS, CLUSTERS, 0, CONFIG)

    assert [r.incident_id for r in facts.representatives] == ["inc-0002", "inc-0001", "inc-0004"]
    first = facts.representatives[0]
    assert (first.severity, first.component) == (Severity.CRITICAL, "checkout")
    assert first.reports_key == reports_key("inc-0002") == "reports.inc_0002"
    assert facts.aggregates["reports.inc_0002"].value == 2
    assert facts.representatives[1].reports_key is None


def test_representatives_are_capped() -> None:
    config = CONFIG.model_copy(update={"max_representative_incidents": 1})

    facts = compute_facts(INCIDENTS, RESULTS, CLUSTERS, 0, config)

    assert [r.incident_id for r in facts.representatives] == ["inc-0002"]


def test_nothing_classified_gives_zero_percentages() -> None:
    facts = compute_facts(INCIDENTS[:1], [manual(1)], [cluster(1, 1)], 0, CONFIG)

    assert facts.aggregates["severity.critical.pct"].value == 0.0
    assert facts.top_components == []
    assert facts.representatives == []
