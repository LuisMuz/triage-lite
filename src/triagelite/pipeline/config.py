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
    dedupe_judge: PositiveInt
    summarize: PositiveInt


class LocalRetryConfig(StrictModel):
    """Backoff for throttled chunks in local runs, mirroring the Step Functions Retry policy."""

    max_attempts: PositiveInt
    initial_delay_seconds: PositiveFloat
    backoff_rate: Annotated[float, Field(ge=1.0)]


class DedupeConfig(StrictModel):
    """Candidate pairs, judge batching and cluster limits for duplicate detection (TL-06)."""

    top_k: PositiveInt
    similarity_threshold: Probability
    max_pairs: PositiveInt
    judge_chunk_size: PositiveInt
    max_cluster_size: Annotated[int, Field(ge=2)]


class ReportConfig(StrictModel):
    """What the summary prompt sees and how its numbers are formatted."""

    max_representative_incidents: PositiveInt
    top_components: PositiveInt
    percent_decimals: Annotated[int, Field(ge=0, le=3)]
    min_data_token_digits: PositiveInt


class PipelineConfig(StrictModel):
    """Contents of config/pipeline.toml."""

    normalize: NormalizeConfig
    prompts: PromptVersions
    local_retry: LocalRetryConfig
    dedupe: DedupeConfig
    report: ReportConfig

    @classmethod
    def from_toml(cls, text: str) -> Self:
        """Parse and validate pipeline TOML text."""
        return cls.model_validate(tomllib.loads(text))
