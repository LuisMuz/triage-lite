"""Classify one chunk of incidents: model call, business checks, one targeted re-ask."""

from collections.abc import Mapping, Sequence
from html import escape

from triagelite.domain.enums import TriageStatus
from triagelite.domain.errors import LLMOutputValidationError
from triagelite.domain.models import (
    Classification,
    ClassifyOutput,
    Incident,
    IncidentClassification,
    IncidentRecord,
)
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.checks import AnswerCheck, check_answer_ids

INCIDENTS_VARIABLE = "incidents"


def classify_chunk(
    llm: StructuredLLM,
    prompt: PromptFile,
    taxonomy: Taxonomy,
    incidents: Sequence[Incident],
    *,
    batch_id: str,
) -> list[IncidentClassification]:
    """Return one result per incident, in input order: classified or `needs_manual`.

    Items that fail the business rules are re-asked once, alone, with the reasons attached;
    whatever still fails is marked `needs_manual`. Availability errors propagate so the
    orchestrator can back off and retry the whole chunk.
    """
    first = _ask(llm, prompt, taxonomy, incidents, batch_id=batch_id, feedback=())
    valid, problems = dict(first.valid), first.problems
    if problems:
        retry_incidents = [incident for incident in incidents if incident.incident_id in problems]
        feedback = [f"{incident_id}: {reason}" for incident_id, reason in problems.items()]
        second = _ask(llm, prompt, taxonomy, retry_incidents, batch_id=batch_id, feedback=feedback)
        valid |= second.valid
        problems = second.problems
    return [_outcome(incident.incident_id, valid, problems) for incident in incidents]


def with_missing_as_manual(
    incidents: Sequence[Incident], results: Sequence[IncidentClassification], reason: str
) -> list[IncidentClassification]:
    """One result per incident, in order; incidents whose chunk produced nothing need a human."""
    by_id = {result.incident_id: result for result in results}
    return [
        by_id.get(incident.incident_id)
        or IncidentClassification(
            incident_id=incident.incident_id, status=TriageStatus.NEEDS_MANUAL, reason=reason
        )
        for incident in incidents
    ]


def incident_records(
    incidents: Sequence[Incident], results: Sequence[IncidentClassification]
) -> list[IncidentRecord]:
    """Pair each incident with its result, in the shape the read API lists."""
    by_id = {result.incident_id: result for result in results}
    return [
        IncidentRecord(
            incident_id=incident.incident_id,
            status=by_id[incident.incident_id].status,
            classification=by_id[incident.incident_id].classification,
            reason=by_id[incident.incident_id].reason,
            external_id=incident.external_id,
            title=incident.title,
            lang=incident.lang,
        )
        for incident in incidents
    ]


def _ask(
    llm: StructuredLLM,
    prompt: PromptFile,
    taxonomy: Taxonomy,
    incidents: Sequence[Incident],
    *,
    batch_id: str,
    feedback: Sequence[str],
) -> AnswerCheck[Classification]:
    expected = {incident.incident_id for incident in incidents}
    variables = taxonomy_variables(taxonomy) | {INCIDENTS_VARIABLE: render_incidents(incidents)}
    try:
        result = llm.generate_structured(
            prompt, variables, ClassifyOutput, batch_id=batch_id, feedback=feedback
        )
    except LLMOutputValidationError as error:
        reason = f"model output failed validation twice ({error})"
        return AnswerCheck(valid={}, problems=dict.fromkeys(sorted(expected), reason))
    return check_business_rules(result.output, expected, taxonomy)


def check_business_rules(
    output: ClassifyOutput, expected_ids: set[str], taxonomy: Taxonomy
) -> AnswerCheck[Classification]:
    """Keep items whose ID was asked for exactly once and whose component exists."""
    check = check_answer_ids(output.items, lambda item: item.incident_id, expected_ids)
    valid: dict[str, Classification] = {}
    problems = dict(check.problems)
    for incident_id, item in check.valid.items():
        if taxonomy.has_component(item.component):
            valid[incident_id] = item
        else:
            problems[incident_id] = f"component {item.component!r} is not in the list of components"
    return AnswerCheck(valid=valid, problems=problems)


def _outcome(
    incident_id: str, valid: dict[str, Classification], problems: dict[str, str]
) -> IncidentClassification:
    if incident_id in valid:
        return IncidentClassification(
            incident_id=incident_id,
            status=TriageStatus.CLASSIFIED,
            classification=valid[incident_id],
        )
    return IncidentClassification(
        incident_id=incident_id,
        status=TriageStatus.NEEDS_MANUAL,
        reason=problems.get(incident_id, "not classified"),
    )


def taxonomy_variables(taxonomy: Taxonomy) -> dict[str, str]:
    """Label definitions as bullet lists, one prompt variable per label set."""
    return {
        "severity": _bullets(taxonomy.severity),
        "category": _bullets(taxonomy.category),
        "component": _bullets(taxonomy.component),
    }


def _bullets[K: str](definitions: Mapping[K, str]) -> str:
    return "\n".join(f"- {name}: {text}" for name, text in definitions.items())


def render_incidents(incidents: Sequence[Incident]) -> str:
    """Incidents as `<incident id="...">` blocks; text is escaped so it can't close a tag."""
    return "\n".join(render_incident(incident) for incident in incidents)


def render_incident(incident: Incident) -> str:
    """One incident as an `<incident>` block with escaped text."""
    parts = [
        f'<incident id="{escape(incident.incident_id)}" lang="{incident.lang}">',
        f"<title>{escape(incident.title, quote=False)}</title>",
        f"<description>{escape(incident.description, quote=False)}</description>",
    ]
    if incident.steps:
        parts.append(f"<steps>{escape(incident.steps, quote=False)}</steps>")
    if incident.environment:
        parts.append(f"<environment>{escape(incident.environment, quote=False)}</environment>")
    parts.append("</incident>")
    return "\n".join(parts)
