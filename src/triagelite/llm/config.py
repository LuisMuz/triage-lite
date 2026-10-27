import tomllib
from typing import Literal, Self

from pydantic import PositiveFloat, PositiveInt

from triagelite.domain.enums import Stage
from triagelite.domain.errors import ConfigError
from triagelite.domain.models import NonEmptyStr, StrictModel

Effort = Literal["low", "medium", "high", "xhigh", "max"]
Thinking = Literal["disabled"]


class ClientConfig(StrictModel):
    """Settings shared by every model call."""

    timeout_seconds: PositiveFloat


class StageModelConfig(StrictModel):
    """Which model a stage calls and with which generation limits."""

    model_id: NonEmptyStr
    max_tokens: PositiveInt
    thinking: Thinking | None = None
    effort: Effort | None = None


class ModelsConfig(StrictModel):
    """Contents of config/models.toml."""

    client: ClientConfig
    stages: dict[Stage, StageModelConfig]

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
