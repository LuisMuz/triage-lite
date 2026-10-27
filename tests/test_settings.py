from pathlib import Path

import pytest
from pydantic import ValidationError

from triagelite.settings import Settings, load_taxonomy

REPO_CONFIG = Path(__file__).parents[1] / "config"


def test_env_vars_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRIAGELITE_CONFIG_DIR", str(REPO_CONFIG))
    monkeypatch.setenv("TRIAGELITE_LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.config_dir == REPO_CONFIG
    assert settings.log_level == "DEBUG"


def test_missing_config_dir_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TRIAGELITE_CONFIG_DIR", str(tmp_path / "nope"))

    with pytest.raises(ValidationError, match="config_dir"):
        Settings()


def test_invalid_log_level_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRIAGELITE_LOG_LEVEL", "LOUD")

    with pytest.raises(ValidationError, match="log_level"):
        Settings(config_dir=REPO_CONFIG)


def test_load_taxonomy_reads_the_config_dir() -> None:
    taxonomy = load_taxonomy(Settings(config_dir=REPO_CONFIG))

    assert taxonomy.has_component("checkout")
