from pathlib import Path

import pytest
from pydantic import ValidationError

from triagelite.domain.enums import Category, Severity
from triagelite.domain.taxonomy import Taxonomy

REPO_TAXONOMY = Path(__file__).parents[2] / "config" / "taxonomy.toml"

SEVERITIES = "\n".join(f'{s.value} = "def"' for s in Severity)
CATEGORIES = "\n".join(f'{c.value} = "def"' for c in Category)


def toml_text(*, severity: str = SEVERITIES, component: str = 'cart = "def"') -> str:
    return f"[severity]\n{severity}\n[category]\n{CATEGORIES}\n[component]\n{component}\n"


def test_repo_taxonomy_is_valid() -> None:
    taxonomy = Taxonomy.from_toml(REPO_TAXONOMY.read_text(encoding="utf-8"))

    assert taxonomy.has_component("payments")
    assert set(taxonomy.severity) == set(Severity)


def test_missing_severity_definition_is_rejected() -> None:
    without_low = "\n".join(f'{s.value} = "def"' for s in Severity if s is not Severity.LOW)

    with pytest.raises(ValidationError, match="no definition for: low"):
        Taxonomy.from_toml(toml_text(severity=without_low))


def test_unknown_severity_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="severity"):
        Taxonomy.from_toml(toml_text(severity=SEVERITIES + '\nblocker = "def"'))


def test_component_key_must_be_a_slug() -> None:
    with pytest.raises(ValidationError, match="component"):
        Taxonomy.from_toml(toml_text(component='"Check Out" = "def"'))


def test_empty_component_table_is_rejected() -> None:
    with pytest.raises(ValidationError, match="component"):
        Taxonomy.from_toml(toml_text(component=""))


def test_has_component_rejects_unknown_name() -> None:
    taxonomy = Taxonomy.from_toml(toml_text())

    assert taxonomy.has_component("cart")
    assert not taxonomy.has_component("billing")
