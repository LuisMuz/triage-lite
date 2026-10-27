import tomllib
from typing import Self

from pydantic import NonNegativeFloat

from triagelite.domain.errors import ConfigError
from triagelite.domain.models import NonEmptyStr, StrictModel

TOKENS_PER_PRICE_UNIT = 1_000_000


class ModelPrice(StrictModel):
    """USD per million tokens for one model."""

    input_per_mtok: NonNegativeFloat
    output_per_mtok: NonNegativeFloat


class PriceTable(StrictModel):
    """Contents of config/pricing.toml."""

    models: dict[NonEmptyStr, ModelPrice]

    @classmethod
    def from_toml(cls, text: str) -> Self:
        """Parse and validate pricing TOML text."""
        return cls.model_validate(tomllib.loads(text))

    def price_for(self, model_id: str) -> ModelPrice:
        """Return the price of `model_id`, or raise: an unpriced call would report $0."""
        try:
            return self.models[model_id]
        except KeyError:
            msg = f"config/pricing.toml has no price for model {model_id!r}"
            raise ConfigError(msg) from None

    def cost_usd(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Cost of one call from its token usage."""
        price = self.price_for(model_id)
        return (
            input_tokens * price.input_per_mtok + output_tokens * price.output_per_mtok
        ) / TOKENS_PER_PRICE_UNIT
