from pathlib import Path

import pytest
from pydantic import ValidationError

from triagelite.domain.enums import Stage
from triagelite.domain.errors import ConfigError
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.settings import Settings, load_llm_config

REPO_CONFIG = Path(__file__).parents[2] / "config"


def test_repo_config_loads_and_every_model_is_priced() -> None:
    models, prices = load_llm_config(Settings(config_dir=REPO_CONFIG))

    classify = models.for_stage(Stage.CLASSIFY)
    assert classify.model_id.startswith("global.anthropic.")
    assert classify.thinking is None
    assert prices.price_for(classify.model_id).output_per_mtok > 0


def test_unpriced_model_fails_at_startup(tmp_path: Path) -> None:
    (tmp_path / "models.toml").write_text(
        (REPO_CONFIG / "models.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "pricing.toml").write_text(
        '[models."other"]\ninput_per_mtok = 1\noutput_per_mtok = 1\n'
    )

    with pytest.raises(ConfigError, match="no price for model"):
        load_llm_config(Settings(config_dir=tmp_path))


def test_cost_is_per_million_tokens() -> None:
    prices = PriceTable.model_validate(
        {"models": {"m": {"input_per_mtok": 1, "output_per_mtok": 5}}}
    )

    assert prices.cost_usd("m", 1_000_000, 200_000) == pytest.approx(2.0)


@pytest.mark.parametrize(
    "stage",
    [
        {"model_id": "m", "max_tokens": 0},
        {"model_id": "m", "max_tokens": 10, "thinking": "enabled"},
        {"model_id": "m", "max_tokens": 10, "effort": "extreme"},
        {"model_id": "m", "max_tokens": 10, "temperature": 0.2},
    ],
    ids=["zero-max-tokens", "thinking-enabled", "unknown-effort", "extra-field"],
)
def test_invalid_stage_config_is_rejected(stage: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ModelsConfig.model_validate(
            {"client": {"timeout_seconds": 5}, "stages": {"classify": stage}}
        )


def test_negative_price_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PriceTable.model_validate({"models": {"m": {"input_per_mtok": -1, "output_per_mtok": 1}}})
