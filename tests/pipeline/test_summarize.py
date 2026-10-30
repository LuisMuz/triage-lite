import pytest

from tests.pipeline.conftest import REPO, REPORT_TOOL, report_payload, write_report
from tests.pipeline.test_aggregates import CLUSTERS, CONFIG, INCIDENTS, RESULTS
from triagelite.domain.enums import ReportSource
from triagelite.llm.config import ModelsConfig
from triagelite.llm.fake import FakeLLMClient, ScriptStep, text_only, tool_response
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile, load_prompt
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.aggregates import ReportFacts, compute_facts
from triagelite.pipeline.render import template_sections
from triagelite.pipeline.summarize import ReportDraft, summarize_report, summary_variables

FACTS = compute_facts(INCIDENTS, RESULTS, CLUSTERS, 0, CONFIG)


@pytest.fixture
def summary_prompt() -> PromptFile:
    return load_prompt(REPO / "prompts" / "summarize" / "v1.md")


def summarize(
    script: list[ScriptStep],
    prompt: PromptFile,
    llm_config: tuple[ModelsConfig, PriceTable],
    facts: ReportFacts = FACTS,
) -> tuple[ReportDraft, FakeLLMClient]:
    client = FakeLLMClient(script)
    llm = StructuredLLM(client, *llm_config, recorder=lambda _: None)
    return summarize_report(llm, prompt, facts, "es", CONFIG, batch_id="b"), client


def bare_digit() -> ScriptStep:
    return tool_response(REPORT_TOOL, report_payload("es", "Hay 13 incidentes críticos."))


def test_grounded_draft_is_used(
    summary_prompt: PromptFile, llm_config: tuple[ModelsConfig, PriceTable]
) -> None:
    draft, client = summarize([write_report()], summary_prompt, llm_config)

    assert draft.source is ReportSource.MODEL
    assert draft.sections[0].body == "{{total.incidents}} incidents."
    assert draft.problems == []
    assert 'set lang to "es"' in client.requests[0].system
    assert "Spanish" in client.requests[0].system


def test_bare_digit_triggers_one_re_ask_with_the_problem(
    summary_prompt: PromptFile, llm_config: tuple[ModelsConfig, PriceTable]
) -> None:
    draft, client = summarize([bare_digit(), write_report()], summary_prompt, llm_config)

    assert len(client.requests) == 2
    assert "bare number '13'" in client.requests[1].user
    assert client.requests[1].system == client.requests[0].system
    assert draft.source is ReportSource.MODEL
    assert "bare number '13'" in draft.problems[0]


def test_failing_grounding_twice_falls_back_to_the_template(
    summary_prompt: PromptFile, llm_config: tuple[ModelsConfig, PriceTable]
) -> None:
    draft, client = summarize([bare_digit(), bare_digit()], summary_prompt, llm_config)

    assert len(client.requests) == 2
    assert draft.source is ReportSource.TEMPLATE
    assert draft.sections == template_sections(FACTS, "es")
    assert "bare number '13'" in draft.problems[0]


def test_invalid_output_twice_falls_back_to_the_template(
    summary_prompt: PromptFile, llm_config: tuple[ModelsConfig, PriceTable]
) -> None:
    draft, client = summarize([text_only(), text_only()], summary_prompt, llm_config)

    assert len(client.requests) == 2
    assert draft.source is ReportSource.TEMPLATE
    assert "failed validation twice" in draft.problems[0]


def test_the_model_sees_keys_and_descriptions_never_values() -> None:
    variables = summary_variables(FACTS, "en")

    assert (
        "- severity.critical.pct: share of classified incidents that are critical (percent)"
        in (variables["aggregates"])
    )
    assert "50.0" not in variables["aggregates"]
    assert 'reports="{{reports.inc_0002}}"' in variables["incidents"]
    assert variables["top_components"] == "checkout, cart"
    assert (variables["language"], variables["lang"]) == ("English", "en")


def test_empty_batch_still_fills_every_variable() -> None:
    empty = ReportFacts(aggregates=FACTS.aggregates, top_components=[], representatives=[])

    variables = summary_variables(empty, "es")

    assert (variables["top_components"], variables["incidents"]) == ("none", "none")
