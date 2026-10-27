"""Versioned prompt files.

Layout of `prompts/<stage>/v<N>.md`::

    +++
    stage = "classify"
    version = 1
    schema = "ClassifyOutput"
    tool = "submit_classifications"
    tool_description = "Submit one classification per incident."
    +++
    ## system
    ...text with ${variables}...
    ## user
    ...text with ${variables}...
"""

import tomllib
from collections.abc import Mapping
from pathlib import Path
from string import Template
from typing import Annotated, Self

from pydantic import Field, PositiveInt, ValidationError, model_validator

from triagelite.domain.enums import Stage
from triagelite.domain.errors import ConfigError
from triagelite.domain.models import NonEmptyStr, StrictModel

FRONT_MATTER_FENCE = "+++"
SYSTEM_HEADING = "## system"
USER_HEADING = "## user"
# Anthropic's limit on tool names.
TOOL_NAME_PATTERN = r"^[a-zA-Z0-9_-]{1,64}$"


class RenderedPrompt(StrictModel):
    """System and user text ready to send."""

    system: NonEmptyStr
    user: NonEmptyStr


class PromptFile(StrictModel):
    """One immutable prompt version: metadata, tool definition and templates."""

    stage: Stage
    version: PositiveInt
    schema_name: NonEmptyStr
    tool_name: Annotated[str, Field(pattern=TOOL_NAME_PATTERN)]
    tool_description: NonEmptyStr
    system: NonEmptyStr
    user_template: NonEmptyStr

    @property
    def id(self) -> str:
        """Version label used in logs and results, e.g. `classify/v1`."""
        return f"{self.stage}/v{self.version}"

    @model_validator(mode="after")
    def _templates_are_well_formed(self) -> Self:
        """A stray `$` would only fail at render time; catch it when the file is loaded."""
        for name, text in (("system", self.system), ("user", self.user_template)):
            if not Template(text).is_valid():
                msg = f"invalid placeholder in the {name} section (write a literal $ as $$)"
                raise ValueError(msg)
        return self

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse prompt file text; raise `ConfigError` if it doesn't follow the layout."""
        front_matter, body = _split_front_matter(text)
        system, user = _split_sections(body)
        try:
            meta = tomllib.loads(front_matter)
            return cls.model_validate(
                {
                    "stage": meta.get("stage"),
                    "version": meta.get("version"),
                    "schema_name": meta.get("schema"),
                    "tool_name": meta.get("tool"),
                    "tool_description": meta.get("tool_description"),
                    "system": system,
                    "user_template": user,
                }
            )
        except (tomllib.TOMLDecodeError, ValidationError) as error:
            raise ConfigError(f"invalid prompt file: {error}") from error

    def render(self, variables: Mapping[str, str]) -> RenderedPrompt:
        """Fill both sections; every placeholder must be given and every variable used."""
        system, user = Template(self.system), Template(self.user_template)
        expected = set(system.get_identifiers()) | set(user.get_identifiers())
        missing, unused = expected - variables.keys(), variables.keys() - expected
        if missing or unused:
            msg = f"{self.id}: missing variables {sorted(missing)}, unused {sorted(unused)}"
            raise ConfigError(msg)
        return RenderedPrompt(system=system.substitute(variables), user=user.substitute(variables))


def load_prompt(path: Path) -> PromptFile:
    """Read and parse a prompt file."""
    return PromptFile.parse(path.read_text(encoding="utf-8"))


def _split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        raise ConfigError(f"prompt file must start with a {FRONT_MATTER_FENCE} line")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == FRONT_MATTER_FENCE)
    except StopIteration:
        raise ConfigError(f"prompt front matter has no closing {FRONT_MATTER_FENCE}") from None
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1 :])


def _split_sections(body: str) -> tuple[str, str]:
    lines = [line.strip() for line in body.splitlines()]
    if lines.count(SYSTEM_HEADING) != 1 or lines.count(USER_HEADING) != 1:
        raise ConfigError(f"prompt needs exactly one {SYSTEM_HEADING!r} and one {USER_HEADING!r}")
    system_at, user_at = lines.index(SYSTEM_HEADING), lines.index(USER_HEADING)
    if user_at < system_at or any(lines[:system_at]):
        raise ConfigError(f"prompt body must be {SYSTEM_HEADING!r} followed by {USER_HEADING!r}")
    raw = body.splitlines()
    return "\n".join(raw[system_at + 1 : user_at]), "\n".join(raw[user_at + 1 :])
