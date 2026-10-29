"""Classify one chunk of incidents: model call, business checks, one targeted re-ask."""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape

from triagelite.domain.enums import TriageStatus
from triagelite.domain.errors import LLMOutputValidationError
from triagelite.domain.models import (
    Classification,
    ClassifyOutput,
    Incident,
    IncidentClassification,
)
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM

INCIDENTS_VARIABLE = "incidents"


@dataclass(frozen=True)
class BusinessCheck:
    """Items that passed the business rules, and a reason for every expected ID that didn't."""

    valid: dict[str, Classification]
    problems: dict[str, str]


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


def _ask(
    llm: StructuredLLM,
    prompt: PromptFile,
    taxonomy: Taxonomy,
    incidents: Sequence[Incident],
    *,
    batch_id: str,
    feedback: Sequence[str],
) -> BusinessCheck:
    expected = {incident.incident_id for incident in incidents}
    variables = taxonomy_variables(taxonomy) | {INCIDENTS_VARIABLE: render_incidents(incidents)}
    try:
        result = llm.generate_structured(
            prompt, variables, ClassifyOutput, batch_id=batch_id, feedback=feedback
        )
    except LLMOutputValidationError as error:
        reason = f"model output failed validation twice ({error})"
        return BusinessCheck(valid={}, problems=dict.fromkeys(sorted(expected), reason))
    return check_business_rules(result.output, expected, taxonomy)


def check_business_rules(
    output: ClassifyOutput, expected_ids: set[str], taxonomy: Taxonomy
) -> BusinessCheck:
    """Keep items whose ID was asked for exactly once and whose component exists."""
    counts = Counter(item.incident_id for item in output.items)
    valid: dict[str, Classification] = {}
    problems: dict[str, str] = {}
    for item in output.items:
        if item.incident_id not in expected_ids:
            continue
        if counts[item.incident_id] > 1:
            problems[item.incident_id] = "answered more than once; answer exactly once"
        elif not taxonomy.has_component(item.component):
            problems[item.incident_id] = (
                f"component {item.component!r} is not in the list of components"
            )
        else:
            valid[item.incident_id] = item
    for missing in sorted(expected_ids - counts.keys()):
        problems[missing] = "missing from your answer"
    return BusinessCheck(valid=valid, problems=problems)


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
    return "\n".join(_render_incident(incident) for incident in incidents)


def _render_incident(incident: Incident) -> str:
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
