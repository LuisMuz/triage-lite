import tomllib
from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from triagelite.domain.enums import Category, Severity
from triagelite.domain.models import COMPONENT_SLUG_PATTERN, NonEmptyStr, StrictModel

ComponentSlug = Annotated[str, StringConstraints(pattern=COMPONENT_SLUG_PATTERN)]


class Taxonomy(StrictModel):
    """Label sets and their definitions, loaded from config/taxonomy.toml."""

    severity: dict[Severity, NonEmptyStr]
    category: dict[Category, NonEmptyStr]
    component: Annotated[dict[ComponentSlug, NonEmptyStr], Field(min_length=1)]

    @model_validator(mode="after")
    def _every_label_is_defined(self) -> Self:
        """The prompt shows only defined labels, so a missing definition hides a valid label."""
        missing = [s.value for s in Severity if s not in self.severity]
        missing += [c.value for c in Category if c not in self.category]
        if missing:
            msg = f"taxonomy has no definition for: {', '.join(missing)}"
            raise ValueError(msg)
        return self

    @classmethod
    def from_toml(cls, text: str) -> Self:
        """Parse and validate taxonomy TOML text."""
        return cls.model_validate(tomllib.loads(text))

    def has_component(self, name: str) -> bool:
        """Return whether `name` is a known component."""
        return name in self.component
