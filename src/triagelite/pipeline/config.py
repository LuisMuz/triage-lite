import tomllib
from typing import Annotated, Self

from pydantic import Field, PositiveFloat, PositiveInt

from triagelite.domain.models import Probability, StrictModel


class NormalizeConfig(StrictModel):
    """How incidents are prepared before any model call."""

    chunk_size: PositiveInt
    min_language_confidence: Probability


class PromptVersions(StrictModel):
    """Which prompt version each LLM stage uses."""

    classify: PositiveInt


class LocalRetryConfig(StrictModel):
    """Backoff for throttled chunks in local runs, mirroring the Step Functions Retry policy."""

    max_attempts: PositiveInt
    initial_delay_seconds: PositiveFloat
    backoff_rate: Annotated[float, Field(ge=1.0)]


class PipelineConfig(StrictModel):
    """Contents of config/pipeline.toml."""

    normalize: NormalizeConfig
    prompts: PromptVersions
    local_retry: LocalRetryConfig

    @classmethod
    def from_toml(cls, text: str) -> Self:
        """Parse and validate pipeline TOML text."""
        return cls.model_validate(tomllib.loads(text))
