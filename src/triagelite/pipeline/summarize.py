"""Report prose in one language: model draft, grounding check, one re-ask, then the template."""

from html import escape

from triagelite.domain.enums import ReportSource
from triagelite.domain.errors import LLMOutputValidationError
from triagelite.domain.models import (
    Language,
    NonEmptyStr,
    ReportSection,
    StrictModel,
    SummaryOutput,
)
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.aggregates import ReportFacts
from triagelite.pipeline.config import ReportConfig
from triagelite.pipeline.render import data_tokens, grounding_problems, template_sections

GROUNDING_ATTEMPTS = 2
LANGUAGE_NAMES: dict[Language, str] = {"es": "Spanish", "en": "English"}


class ReportDraft(StrictModel):
    """The sections chosen for one language, who wrote them, and why the model's were rejected."""

    lang: Language
    source: ReportSource
    sections: list[ReportSection]
    problems: list[NonEmptyStr]


def summarize_report(
    llm: StructuredLLM,
    prompt: PromptFile,
    facts: ReportFacts,
    lang: Language,
    config: ReportConfig,
    *,
    batch_id: str,
) -> ReportDraft:
    """Ask for the report; a draft that fails grounding is re-asked once, then templated.

    Availability errors propagate so the orchestrator can back off.
    """
    variables = summary_variables(facts, lang)
    incident_ids = {r.incident_id for r in facts.representatives}
    allowed = data_tokens((r.title for r in facts.representatives), config.min_data_token_digits)
    problems: list[str] = []
    for _ in range(GROUNDING_ATTEMPTS):
        try:
            result = llm.generate_structured(
                prompt, variables, SummaryOutput, batch_id=batch_id, feedback=problems
            )
        except LLMOutputValidationError as error:
            return template_draft(facts, lang, [f"model output failed validation twice ({error})"])
        problems = grounding_problems(result.output, lang, facts.aggregates, incident_ids, allowed)
        if not problems:
            return ReportDraft(
                lang=lang, source=ReportSource.MODEL, sections=result.output.sections, problems=[]
            )
    return template_draft(facts, lang, problems)


def template_draft(facts: ReportFacts, lang: Language, problems: list[str]) -> ReportDraft:
    """The deterministic fallback, carrying the reasons the model's draft was not used."""
    return ReportDraft(
        lang=lang,
        source=ReportSource.TEMPLATE,
        sections=template_sections(facts, lang),
        problems=problems,
    )


def summary_variables(facts: ReportFacts, lang: Language) -> dict[str, str]:
    """Aggregate keys with descriptions (never values), top components and incidents."""
    aggregates = "\n".join(
        f"- {key}: {aggregate.description}" + (" (percent)" if aggregate.kind == "percent" else "")
        for key, aggregate in facts.aggregates.items()
    )
    incidents = "\n".join(
        f'<incident id="{escape(r.incident_id)}" severity="{r.severity}" '
        f'category="{r.category}" component="{escape(r.component)}"'
        + (f' reports="{{{{{r.reports_key}}}}}"' if r.reports_key else "")
        + f">{escape(r.title, quote=False)}</incident>"
        for r in facts.representatives
    )
    return {
        "language": LANGUAGE_NAMES[lang],
        "lang": lang,
        "aggregates": aggregates,
        "top_components": ", ".join(facts.top_components) or "none",
        "incidents": incidents or "none",
    }
