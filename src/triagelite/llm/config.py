import tomllib
from typing import Literal, Self

from pydantic import PositiveFloat, PositiveInt, model_validator

from triagelite.domain.enums import Stage
from triagelite.domain.errors import ConfigError
from triagelite.domain.models import NonEmptyStr, StrictModel

Effort = Literal["low", "medium", "high", "xhigh", "max"]
Thinking = Literal["disabled"]
ModelApi = Literal["messages", "converse"]
EmbeddingDimensions = Literal[256, 512, 1024]


class ClientConfig(StrictModel):
    """Settings shared by every model call."""

    timeout_seconds: PositiveFloat


class StageModelConfig(StrictModel):
    """Which model a stage calls, through which Bedrock API, and with which limits.

    `messages` is the Anthropic Messages API (Claude only); `converse` is Bedrock's
    provider-neutral API for every other model, where `effort` becomes `reasoning_effort`.
    """

    model_id: NonEmptyStr
    api: ModelApi
    max_tokens: PositiveInt
    thinking: Thinking | None = None
    effort: Effort | None = None

    @model_validator(mode="after")
    def _thinking_needs_messages(self) -> Self:
        if self.thinking and self.api != "messages":
            msg = "`thinking` is only supported with api = 'messages'"
            raise ValueError(msg)
        return self


class EmbeddingConfig(StrictModel):
    """Embedding model and how incident text is turned into its input."""

    model_id: NonEmptyStr
    dimensions: EmbeddingDimensions
    normalize: bool
    max_description_chars: PositiveInt


class ModelsConfig(StrictModel):
    """Contents of config/models.toml."""

    client: ClientConfig
    stages: dict[Stage, StageModelConfig]
    embedding: EmbeddingConfig

    @classmethod
    def from_toml(cls, text: str) -> Self:
        """Parse and validate models TOML text."""
        return cls.model_validate(tomllib.loads(text))

    def for_stage(self, stage: Stage) -> StageModelConfig:
        """Return the model config for `stage`, or raise if the stage isn't configured."""
        try:
            return self.stages[stage]
        except KeyError:
            msg = f"config/models.toml has no [stages.{stage}] section"
            raise ConfigError(msg) from None
