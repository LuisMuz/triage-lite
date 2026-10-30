"""Every number the report may mention, computed by code; the model only sees the keys (TL-07)."""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Literal

from triagelite.domain.enums import Category, Severity, TriageStatus
from triagelite.domain.models import (
    Classification,
    DuplicateCluster,
    Incident,
    IncidentClassification,
    NonEmptyStr,
    StrictModel,
)
from triagelite.pipeline.config import ReportConfig

PERCENT = 100
SEVERITY_RANK = {severity: rank for rank, severity in enumerate(Severity)}

type AggregateKind = Literal["count", "percent"]


class Aggregate(StrictModel):
    """One number, what kind it is, and what it means (the description is shown to the model)."""

    value: float
    kind: AggregateKind
    description: NonEmptyStr


class Representative(StrictModel):
    """A canonical incident the report may describe, with the key holding its report count."""

    incident_id: NonEmptyStr
    title: NonEmptyStr
    severity: Severity
    category: Category
    component: NonEmptyStr
    reports_key: str | None = None


class ReportFacts(StrictModel):
    """Everything the summary is allowed to state about one batch."""

    aggregates: dict[str, Aggregate]
    top_components: list[str]
    representatives: list[Representative]


def _count(value: int, description: str) -> Aggregate:
    return Aggregate(value=value, kind="count", description=description)


def _percent(part: int, whole: int, description: str) -> Aggregate:
    return Aggregate(
        value=part / whole * PERCENT if whole else 0.0, kind="percent", description=description
    )


def reports_key(incident_id: str) -> str:
    """Aggregate key for the number of reports of the bug `incident_id` is canonical for."""
    return f"reports.{incident_id.replace('-', '_')}"


def compute_facts(
    incidents: Sequence[Incident],
    results: Sequence[IncidentClassification],
    clusters: Sequence[DuplicateCluster],
    row_errors: int,
    config: ReportConfig,
) -> ReportFacts:
    """Counts by severity, category and component, duplicates, and the incidents worth naming.

    The top components also get their severity mix, so the report can ground claims about it.
    """
    labels = {r.incident_id: r.classification for r in results if r.classification}
    classified = len(labels)
    severities = Counter(label.severity for label in labels.values())
    categories = Counter(label.category for label in labels.values())
    components = Counter(label.component for label in labels.values())
    duplicate_groups = [cluster for cluster in clusters if len(cluster.member_ids) > 1]

    aggregates: dict[str, Aggregate] = {
        "total.incidents": _count(len(incidents), "incidents in the batch"),
        "total.row_errors": _count(row_errors, "CSV rows rejected before triage"),
        "total.classified": _count(classified, "incidents the model classified"),
        "total.needs_manual": _count(
            sum(r.status is TriageStatus.NEEDS_MANUAL for r in results),
            "incidents a person must classify by hand",
        ),
        "clusters.unique_bugs": _count(
            len(clusters), "distinct bugs after merging duplicate reports"
        ),
        "clusters.duplicate_groups": _count(
            len(duplicate_groups), "bugs that were reported more than once"
        ),
        "clusters.duplicate_reports": _count(
            sum(len(cluster.member_ids) - 1 for cluster in duplicate_groups),
            "reports that repeat a bug someone already reported",
        ),
    }
    for severity in Severity:
        aggregates[f"severity.{severity}.count"] = _count(
            severities[severity], f"incidents classified as {severity}"
        )
        aggregates[f"severity.{severity}.pct"] = _percent(
            severities[severity], classified, f"share of classified incidents that are {severity}"
        )
    for category, count in sorted(categories.items()):
        aggregates[f"category.{category}.count"] = _count(
            count, f"incidents in the {category} category"
        )
    for component, count in sorted(components.items()):
        aggregates[f"component.{component}.count"] = _count(
            count, f"incidents in the {component} component"
        )

    representatives = _representatives(incidents, labels, clusters, config)
    sizes = {cluster.canonical_id: len(cluster.member_ids) for cluster in clusters}
    for representative in representatives:
        if representative.reports_key:
            aggregates[representative.reports_key] = _count(
                sizes[representative.incident_id],
                f"reports of the bug {representative.incident_id}, duplicates included",
            )
    top = sorted(components.items(), key=lambda item: (-item[1], item[0]))
    top_components = [component for component, _ in top[: config.top_components]]
    mix = Counter((label.component, label.severity) for label in labels.values())
    for component in top_components:
        for severity in Severity:
            if mix[component, severity]:
                aggregates[f"component.{component}.severity.{severity}.count"] = _count(
                    mix[component, severity],
                    f"incidents in the {component} component classified as {severity}",
                )
    return ReportFacts(
        aggregates=aggregates,
        top_components=top_components,
        representatives=representatives,
    )


def _representatives(
    incidents: Sequence[Incident],
    labels: Mapping[str, Classification],
    clusters: Sequence[DuplicateCluster],
    config: ReportConfig,
) -> list[Representative]:
    """Classified canonical incidents: most severe first, then most reported, then earliest."""
    by_id = {incident.incident_id: incident for incident in incidents}
    position = {incident.incident_id: index for index, incident in enumerate(incidents)}
    ranked = sorted(
        (cluster for cluster in clusters if cluster.canonical_id in labels),
        key=lambda c: (
            SEVERITY_RANK[labels[c.canonical_id].severity],
            -len(c.member_ids),
            position[c.canonical_id],
        ),
    )
    return [
        Representative(
            incident_id=cluster.canonical_id,
            title=by_id[cluster.canonical_id].title,
            severity=labels[cluster.canonical_id].severity,
            category=labels[cluster.canonical_id].category,
            component=labels[cluster.canonical_id].component,
            reports_key=reports_key(cluster.canonical_id) if len(cluster.member_ids) > 1 else None,
        )
        for cluster in ranked[: config.max_representative_incidents]
    ]
