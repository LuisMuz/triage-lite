"""Report text: grounding checks, placeholder substitution per locale, and the fallback template."""

import re
from collections.abc import Iterable, Mapping, Sequence

from triagelite.domain.enums import ReportSource, Severity
from triagelite.domain.models import Language, ReportSection, SummaryOutput
from triagelite.pipeline.aggregates import Aggregate, ReportFacts

PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_]+(?:\.[a-z0-9_]+)*)\s*\}\}")
BRACES = re.compile(r"\{\{|\}\}")
INCIDENT_REF = re.compile(r"\binc-\d+\b", re.IGNORECASE)
VERSION = re.compile(r"^(?:v\d+(?:\.\d+)*|\d+\.\d+\.\d+)$", re.IGNORECASE)
DIGIT_TOKEN = re.compile(r"\S*\d\S*")
WORD = re.compile(r"[^\W\d_]+")
WRAPPING_PUNCTUATION = "()[]{}<>.,;:!?¡¿\"'`*_«»"
NBSP = "\u00a0"

NUMBER_WORDS: dict[Language, dict[str, int | None]] = {
    "es": {
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
        "doce": 12,
        "quince": 15,
        "veinte": 20,
        "treinta": 30,
        "cien": 100,
        "ciento": None,
        "cientos": None,
        "mil": 1000,
        "docena": 12,
        "docenas": None,
    },
    "en": {
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "fifteen": 15,
        "twenty": 20,
        "thirty": 30,
        "hundred": 100,
        "hundreds": None,
        "thousand": 1000,
        "thousands": None,
        "dozen": 12,
        "dozens": None,
    },
}
ALL_NUMBER_WORDS = NUMBER_WORDS["es"].keys() | NUMBER_WORDS["en"].keys()
TITLES: dict[Language, str] = {"es": "Informe de triage QA", "en": "QA triage report"}
SEVERITY_NAMES: dict[Language, dict[Severity, str]] = {
    "es": {
        Severity.CRITICAL: "Crítica",
        Severity.HIGH: "Alta",
        Severity.MEDIUM: "Media",
        Severity.LOW: "Baja",
    },
    "en": {
        Severity.CRITICAL: "Critical",
        Severity.HIGH: "High",
        Severity.MEDIUM: "Medium",
        Severity.LOW: "Low",
    },
}
TEMPLATE_TEXT: dict[Language, dict[str, str]] = {
    "es": {
        "overview": "Resumen",
        "overview_body": (
            "Se recibieron {{total.incidents}} incidentes ({{total.row_errors}} filas del CSV "
            "rechazadas). {{total.classified}} se clasificaron automáticamente y "
            "{{total.needs_manual}} requieren revisión manual. Tras agrupar duplicados quedan "
            "{{clusters.unique_bugs}} errores distintos."
        ),
        "severity": "Severidad",
        "components": "Componentes más afectados",
        "none": "Ninguno.",
        "duplicates": "Duplicados",
        "duplicates_body": (
            "{{clusters.duplicate_groups}} errores se reportaron más de una vez, con "
            "{{clusters.duplicate_reports}} reportes repetidos."
        ),
        "model": "redactado por el modelo {model} con el prompt {prompt}",
        "template": "plantilla determinista: el texto del modelo no pasó la validación",
        "batch": "Lote",
    },
    "en": {
        "overview": "Overview",
        "overview_body": (
            "{{total.incidents}} incidents were received ({{total.row_errors}} CSV rows "
            "rejected). {{total.classified}} were classified automatically and "
            "{{total.needs_manual}} need manual review. After merging duplicates there are "
            "{{clusters.unique_bugs}} distinct bugs."
        ),
        "severity": "Severity",
        "components": "Most affected components",
        "none": "None.",
        "duplicates": "Duplicates",
        "duplicates_body": (
            "{{clusters.duplicate_groups}} bugs were reported more than once, with "
            "{{clusters.duplicate_reports}} repeated reports."
        ),
        "model": "written by model {model} with prompt {prompt}",
        "template": "deterministic template: the model's text failed validation",
        "batch": "Batch",
    },
}


def format_value(aggregate: Aggregate, lang: Language, percent_decimals: int) -> str:
    """`1,234` / `13.3%` in English, `1.234` / `13,3 %` in Spanish."""
    if aggregate.kind == "count":
        text = f"{round(aggregate.value):,}"
    else:
        text = f"{aggregate.value:,.{percent_decimals}f}"
    if lang == "es":
        text = text.replace(",", "\0").replace(".", ",").replace("\0", ".")
    if aggregate.kind == "percent":
        text += f"{NBSP}%" if lang == "es" else "%"
    return text


def render_placeholders(
    text: str, aggregates: Mapping[str, Aggregate], lang: Language, percent_decimals: int
) -> str:
    """Replace every `{{key}}` with its value; `grounding_problems` checked the keys."""
    return PLACEHOLDER.sub(
        lambda match: format_value(aggregates[match[1]], lang, percent_decimals), text
    )


def _bare_tokens(text: str) -> Iterable[str]:
    for token in DIGIT_TOKEN.findall(text):
        yield token.strip(WRAPPING_PUNCTUATION)


def data_tokens(texts: Iterable[str], min_digits: int) -> set[str]:
    """Words from incident titles that may be quoted: `3G`, `iOS17`, `500`, `Two`-factor.

    Short pure numbers (`3`, `13`) are excluded because they look exactly like a count.
    """
    allowed: set[str] = set()
    for text in texts:
        for token in _bare_tokens(text):
            if any(c.isalpha() for c in token) or sum(c.isdigit() for c in token) >= min_digits:
                allowed.add(token.casefold())
        allowed |= {word for word in WORD.findall(text.casefold()) if word in ALL_NUMBER_WORDS}
    return allowed


def grounding_problems(
    output: SummaryOutput,
    lang: Language,
    aggregates: Mapping[str, Aggregate],
    incident_ids: set[str],
    allowed_tokens: set[str],
) -> list[str]:
    """Every reason the draft can't be trusted, phrased for the model to fix."""
    problems: list[str] = []
    if output.lang != lang:
        problems.append(f"lang must be '{lang}', got '{output.lang}'")
    for section in output.sections:
        where = f"section '{section.heading}'"
        for text in (section.heading, section.body):
            problems += _text_problems(text, where, lang, aggregates, incident_ids, allowed_tokens)
    return list(dict.fromkeys(problems))


def _text_problems(
    text: str,
    where: str,
    lang: Language,
    aggregates: Mapping[str, Aggregate],
    incident_ids: set[str],
    allowed_tokens: set[str],
) -> list[str]:
    problems = [
        f"unknown placeholder {{{{{key}}}}} in {where}: use only keys from <aggregates>"
        for key in PLACEHOLDER.findall(text)
        if key not in aggregates
    ]
    prose = PLACEHOLDER.sub(" ", text)
    if BRACES.search(prose):
        problems.append(f"malformed placeholder in {where}: write exactly {{{{key}}}}")
    problems += [
        f"{ref} in {where} is not an incident in <incidents>"
        for ref in INCIDENT_REF.findall(prose)
        if ref.lower() not in incident_ids
    ]
    problems += [
        f"bare number '{token}' in {where}: "
        + number_hint(
            int(token) if token.isdecimal() else None,
            aggregates,
            "write every number as a placeholder from <aggregates>",
        )
        for token in _bare_tokens(INCIDENT_REF.sub(" ", prose))
        if not VERSION.match(token) and token.casefold() not in allowed_tokens
    ]
    problems += [
        f"number word '{word}' in {where}: "
        + number_hint(
            NUMBER_WORDS[lang][word],
            aggregates,
            "use a placeholder from <aggregates>, or say it without a number",
        )
        for word in WORD.findall(prose.casefold())
        if word in NUMBER_WORDS[lang] and word not in allowed_tokens
    ]
    return problems


def number_hint(value: int | None, aggregates: Mapping[str, Aggregate], general: str) -> str:
    """How to replace a number the model wrote: the count keys holding that value, if any.

    The keys are matched against a number the draft already contains, so no value leaks.
    """
    if value is None:
        return general
    keys = [
        f"{{{{{key}}}}} ({aggregate.description})"
        for key, aggregate in aggregates.items()
        if aggregate.kind == "count" and aggregate.value == value
    ]
    if not keys:
        return (
            "no key in <aggregates> has this value; name the incidents by id instead of "
            "counting them, or say it without a number"
        )
    return (
        f"keys with this value are {', '.join(keys)}; "
        "write the one you mean, or say it without a number"
    )


def template_sections(facts: ReportFacts, lang: Language) -> list[ReportSection]:
    """The fallback report: same facts and placeholders, fixed wording."""
    text = TEMPLATE_TEXT[lang]
    severity = "\n".join(
        f"- {name}: {{{{severity.{level}.count}}}} ({{{{severity.{level}.pct}}}})"
        for level, name in SEVERITY_NAMES[lang].items()
    )
    components = "\n".join(
        f"- {component}: {{{{component.{component}.count}}}}" for component in facts.top_components
    )
    return [
        ReportSection(heading=text["overview"], body=text["overview_body"]),
        ReportSection(heading=text["severity"], body=severity),
        ReportSection(heading=text["components"], body=components or text["none"]),
        ReportSection(heading=text["duplicates"], body=text["duplicates_body"]),
    ]


def render_report(
    sections: Sequence[ReportSection],
    facts: ReportFacts,
    lang: Language,
    *,
    batch_id: str,
    source: ReportSource,
    model_id: str,
    prompt_id: str,
    percent_decimals: int,
) -> str:
    """The final Markdown report with every placeholder replaced."""
    text = TEMPLATE_TEXT[lang]
    origin = (
        text["model"].format(model=model_id, prompt=prompt_id)
        if source is ReportSource.MODEL
        else text["template"]
    )
    lines = [f"# {TITLES[lang]}", "", f"{text['batch']} `{batch_id}` · {origin}"]
    for section in sections:
        heading = render_placeholders(section.heading, facts.aggregates, lang, percent_decimals)
        body = render_placeholders(section.body, facts.aggregates, lang, percent_decimals)
        lines += ["", f"## {heading}", "", body]
    return "\n".join(lines) + "\n"
