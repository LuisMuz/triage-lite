import pytest

from triagelite.domain.enums import ReportSource
from triagelite.domain.models import Language, ReportSection, SummaryOutput
from triagelite.pipeline.aggregates import Aggregate, ReportFacts
from triagelite.pipeline.render import (
    NBSP,
    data_tokens,
    format_value,
    grounding_problems,
    render_placeholders,
    render_report,
    template_sections,
)


def count(value: float) -> Aggregate:
    return Aggregate(value=value, kind="count", description="d")


def percent(value: float) -> Aggregate:
    return Aggregate(value=value, kind="percent", description="d")


AGGREGATES = {
    key: count(1)
    for key in (
        "total.incidents",
        "total.row_errors",
        "total.classified",
        "total.needs_manual",
        "clusters.unique_bugs",
        "clusters.duplicate_groups",
        "clusters.duplicate_reports",
        "component.checkout.count",
    )
} | {
    f"severity.{level}.{kind}": (count(1) if kind == "count" else percent(25.0))
    for level in ("critical", "high", "medium", "low")
    for kind in ("count", "pct")
}
FACTS = ReportFacts(aggregates=AGGREGATES, top_components=["checkout"], representatives=[])


@pytest.mark.parametrize(
    ("aggregate", "lang", "expected"),
    [
        (count(1234), "en", "1,234"),
        (count(1234), "es", "1.234"),
        (count(7), "es", "7"),
        (percent(13.333), "en", "13.3%"),
        (percent(13.333), "es", f"13,3{NBSP}%"),
        (percent(1234.5), "es", f"1.234,5{NBSP}%"),
    ],
)
def test_format_value_per_locale(aggregate: Aggregate, lang: Language, expected: str) -> None:
    assert format_value(aggregate, lang, 1) == expected


def test_render_placeholders_substitutes_every_key() -> None:
    text = "{{total.incidents}} items, {{ severity.critical.pct }} critical"

    assert render_placeholders(text, AGGREGATES, "en", 0) == "1 items, 25% critical"


def check(body: str, heading: str = "Overview", lang: Language = "en") -> list[str]:
    output = SummaryOutput(lang=lang, sections=[ReportSection(heading=heading, body=body)])
    allowed = data_tokens(["Error 500 al pagar", "Slow on 3G", "Checkout v2 fails 3 times"], 3)
    return grounding_problems(output, "en", AGGREGATES, {"inc-0003"}, allowed)


class TestGrounding:
    def test_placeholders_ids_versions_and_data_tokens_pass(self) -> None:
        body = (
            "{{total.incidents}} reports; inc-0003 (HTTP 500, slow on 3G) since 4.2.0 and v2. "
            "{{severity.critical.pct}} are critical."
        )

        assert check(body) == []

    def test_bare_digit_is_rejected(self) -> None:
        assert check("13 incidents are critical.") == [
            "bare number '13' in section 'Overview': write every number as a placeholder "
            "from <aggregates>"
        ]

    def test_short_numbers_from_titles_are_still_rejected(self) -> None:
        assert "bare number '3'" in check("Checkout fails 3 times.")[0]

    def test_decimal_number_is_not_a_version(self) -> None:
        assert "bare number '13.3%'" in check("About 13.3% are critical.")[0]

    def test_digit_in_heading_is_rejected(self) -> None:
        assert "bare number '5'" in check("{{total.incidents}}", heading="Top 5")[0]

    def test_unknown_placeholder_is_rejected(self) -> None:
        assert check("{{severity.blocker.count}} blockers.") == [
            "unknown placeholder {{severity.blocker.count}} in section 'Overview': "
            "use only keys from <aggregates>"
        ]

    def test_malformed_placeholder_is_rejected(self) -> None:
        assert "malformed placeholder" in check("{{Total Incidents}} reports.")[0]

    def test_unknown_incident_is_rejected(self) -> None:
        assert check("See inc-0999.") == [
            "inc-0999 in section 'Overview' is not an incident in <incidents>"
        ]

    def test_wrong_language_is_rejected(self) -> None:
        assert check("{{total.incidents}}", lang="es") == ["lang must be 'en', got 'es'"]

    def test_repeated_problems_are_listed_once(self) -> None:
        assert len(check("13 and 13.")) == 1


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("components", [["checkout"], []])
def test_template_always_passes_grounding(lang: Language, components: list[str]) -> None:
    facts = FACTS.model_copy(update={"top_components": components})
    output = SummaryOutput(lang=lang, sections=template_sections(facts, lang))

    assert grounding_problems(output, lang, AGGREGATES, set(), set()) == []


def test_render_report_states_who_wrote_it() -> None:
    sections = [ReportSection(heading="Resumen", body="{{severity.critical.pct}} críticos.")]

    model = render_report(
        sections,
        FACTS,
        "es",
        batch_id="b-1",
        source=ReportSource.MODEL,
        model_id="m",
        prompt_id="summarize/v1",
        percent_decimals=1,
    )
    template = render_report(
        sections,
        FACTS,
        "en",
        batch_id="b-1",
        source=ReportSource.TEMPLATE,
        model_id="m",
        prompt_id="summarize/v1",
        percent_decimals=1,
    )

    assert model.startswith("# Informe de triage QA\n\nLote `b-1` · redactado por el modelo m")
    assert f"## Resumen\n\n25,0{NBSP}% críticos." in model
    assert "deterministic template" in template
