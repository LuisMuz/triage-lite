import re
from pathlib import Path

import pytest
from pydantic import JsonValue

from triagelite.domain.models import Incident
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.config import ModelsConfig
from triagelite.llm.fake import Responder, tool_response
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile, load_prompt
from triagelite.llm.types import ModelRequest, ModelResponse
from triagelite.pipeline.config import NormalizeConfig, PipelineConfig
from triagelite.settings import Settings, load_llm_config

REPO = Path(__file__).parents[2]
CLASSIFY_TOOL = "submit_classifications"
INCIDENT_ID = re.compile(r'<incident id="(inc-\d+)"')


@pytest.fixture
def pipeline_config() -> PipelineConfig:
    return PipelineConfig.from_toml((REPO / "config" / "pipeline.toml").read_text(encoding="utf-8"))


@pytest.fixture
def normalize_config(pipeline_config: PipelineConfig) -> NormalizeConfig:
    return pipeline_config.normalize


@pytest.fixture
def taxonomy() -> Taxonomy:
    return Taxonomy.from_toml((REPO / "config" / "taxonomy.toml").read_text(encoding="utf-8"))


@pytest.fixture
def classify_prompt() -> PromptFile:
    return load_prompt(REPO / "prompts" / "classify" / "v1.md")


@pytest.fixture
def llm_config() -> tuple[ModelsConfig, PriceTable]:
    return load_llm_config(Settings(config_dir=REPO / "config", prompts_dir=REPO / "prompts"))


def make_incident(number: int, lang: str = "en") -> Incident:
    return Incident.model_validate(
        {
            "incident_id": f"inc-{number:04d}",
            "external_id": f"QA-{number}",
            "lang": lang,
            "lang_confidence": 0.99,
            "title": f"Checkout fails {number}",
            "description": "Place order returns 500",
        }
    )


def classification_item(incident_id: str, component: str = "checkout") -> dict[str, JsonValue]:
    return {
        "incident_id": incident_id,
        "rationale": "Orders cannot be placed and there is no workaround.",
        "severity": "critical",
        "category": "crash",
        "component": component,
        "confidence": 0.9,
    }


def answer_all(component: str = "checkout") -> Responder:
    def respond(request: ModelRequest) -> ModelResponse:
        ids = INCIDENT_ID.findall(request.user)
        items: list[JsonValue] = [classification_item(i, component) for i in ids]
        return tool_response(CLASSIFY_TOOL, {"items": items})

    return respond


JUDGE_TOOL = "submit_judgements"
PAIR_ID = re.compile(r'<pair id="(p-\d+)"')


def judgement_item(pair_id: str, is_duplicate: bool = True) -> dict[str, JsonValue]:
    return {
        "pair_id": pair_id,
        "rationale": "Both report the same 500 when placing an order.",
        "is_duplicate": is_duplicate,
        "confidence": 0.8,
    }


def judge_all(is_duplicate: bool = True) -> Responder:
    def respond(request: ModelRequest) -> ModelResponse:
        items: list[JsonValue] = [
            judgement_item(pair_id, is_duplicate) for pair_id in PAIR_ID.findall(request.user)
        ]
        return tool_response(JUDGE_TOOL, {"items": items})

    return respond


REPORT_TOOL = "submit_report"
REPORT_LANG = re.compile(r'set lang to "(es|en)"')


def report_payload(lang: str, body: str = "{{total.incidents}} incidents.") -> JsonValue:
    return {"lang": lang, "sections": [{"heading": "Overview", "body": body}]}


def write_report(body: str = "{{total.incidents}} incidents.") -> Responder:
    def respond(request: ModelRequest) -> ModelResponse:
        match = REPORT_LANG.search(request.system)
        lang = match[1] if match else "en"
        return tool_response(REPORT_TOOL, report_payload(lang, body))

    return respond
