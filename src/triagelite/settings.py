from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict

from triagelite.domain.enums import Stage
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile, load_prompt
from triagelite.pipeline.config import PipelineConfig

TAXONOMY_FILE = "taxonomy.toml"
MODELS_FILE = "models.toml"
PRICING_FILE = "pricing.toml"
PIPELINE_FILE = "pipeline.toml"


class Settings(BaseSettings):
    """Process-wide settings, read once from `TRIAGELITE_*` environment variables."""

    model_config = SettingsConfigDict(env_prefix="TRIAGELITE_", extra="forbid", frozen=True)

    config_dir: DirectoryPath = Path("config")
    prompts_dir: DirectoryPath = Path("prompts")
    aws_region: str = "us-east-1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the validated settings, failing fast at startup if they are invalid."""
    return Settings()


def load_taxonomy(settings: Settings) -> Taxonomy:
    """Read and validate the taxonomy file from the config directory."""
    return Taxonomy.from_toml((settings.config_dir / TAXONOMY_FILE).read_text(encoding="utf-8"))


def load_llm_config(settings: Settings) -> tuple[ModelsConfig, PriceTable]:
    """Read models and prices, failing at startup if any configured model has no price."""
    models = ModelsConfig.from_toml((settings.config_dir / MODELS_FILE).read_text(encoding="utf-8"))
    prices = PriceTable.from_toml((settings.config_dir / PRICING_FILE).read_text(encoding="utf-8"))
    for model_id in [stage.model_id for stage in models.stages.values()] + [
        models.embedding.model_id
    ]:
        prices.price_for(model_id)
    return models, prices


def load_pipeline_config(settings: Settings) -> PipelineConfig:
    """Read and validate the pipeline file from the config directory."""
    path = settings.config_dir / PIPELINE_FILE
    return PipelineConfig.from_toml(path.read_text(encoding="utf-8"))


def load_stage_prompt(settings: Settings, stage: Stage, version: int) -> PromptFile:
    """Load `prompts/<stage>/v<version>.md`."""
    return load_prompt(settings.prompts_dir / stage / f"v{version}.md")
