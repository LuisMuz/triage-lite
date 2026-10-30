from typing import Any

import pytest

from triagelite.domain.models import LLMCallRecord
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile

MODEL_ID = "test-model"
EMBED_MODEL_ID = "test-embed"
EMBEDDING: dict[str, object] = {
    "model_id": EMBED_MODEL_ID,
    "dimensions": 1024,
    "normalize": True,
    "max_description_chars": 500,
}
TOOL = "submit_classifications"

PROMPT_TEXT = f"""+++
stage = "classify"
version = 1
schema = "ClassifyOutput"
tool = "{TOOL}"
tool_description = "Submit one classification per incident."
+++
## system
You label bug reports.
<severity>${{severity}}</severity>
Answer only by calling `{TOOL}`.
## user
<incidents>${{incidents}}</incidents>
"""

VARIABLES = {"severity": "critical = outage", "incidents": '<incident id="inc-1">x</incident>'}


@pytest.fixture
def prompt() -> PromptFile:
    return PromptFile.parse(PROMPT_TEXT)


@pytest.fixture
def models() -> ModelsConfig:
    return ModelsConfig.model_validate(
        {
            "client": {"timeout_seconds": 30},
            "stages": {"classify": {"model_id": MODEL_ID, "api": "messages", "max_tokens": 4096}},
            "embedding": EMBEDDING,
        }
    )


@pytest.fixture
def prices() -> PriceTable:
    return PriceTable.model_validate(
        {"models": {MODEL_ID: {"input_per_mtok": 1.0, "output_per_mtok": 5.0}}}
    )


@pytest.fixture
def recorded() -> list[LLMCallRecord]:
    return []


def valid_payload(**overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "incident_id": "inc-1",
        "rationale": "Checkout returns 500 for everyone; no workaround.",
        "severity": "critical",
        "category": "crash",
        "component": "checkout",
        "confidence": 0.8,
    }
    return {"items": [item | overrides]}
