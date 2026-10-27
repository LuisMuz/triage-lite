from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict

from triagelite.domain.taxonomy import Taxonomy

TAXONOMY_FILE = "taxonomy.toml"


class Settings(BaseSettings):
    """Process-wide settings, read once from `TRIAGELITE_*` environment variables."""

    model_config = SettingsConfigDict(env_prefix="TRIAGELITE_", extra="forbid", frozen=True)

    config_dir: DirectoryPath = Path("config")
    aws_region: str = "us-east-1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the validated settings, failing fast at startup if they are invalid."""
    return Settings()


def load_taxonomy(settings: Settings) -> Taxonomy:
    """Read and validate the taxonomy file from the config directory."""
    return Taxonomy.from_toml((settings.config_dir / TAXONOMY_FILE).read_text(encoding="utf-8"))
