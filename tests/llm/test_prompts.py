from pathlib import Path

import pytest

from tests.llm.conftest import PROMPT_TEXT, TOOL, VARIABLES
from triagelite.domain.enums import Stage
from triagelite.domain.errors import ConfigError
from triagelite.llm.prompts import PromptFile, load_prompt


def test_parses_front_matter_and_sections(prompt: PromptFile) -> None:
    assert prompt.stage is Stage.CLASSIFY
    assert prompt.id == "classify/v1"
    assert prompt.schema_name == "ClassifyOutput"
    assert prompt.tool_name == TOOL
    assert prompt.system.startswith("You label bug reports.")
    assert prompt.user_template == "<incidents>${incidents}</incidents>"


def test_render_fills_both_sections(prompt: PromptFile) -> None:
    rendered = prompt.render(VARIABLES)

    assert "<severity>critical = outage</severity>" in rendered.system
    assert rendered.user == '<incidents><incident id="inc-1">x</incident></incidents>'


def test_missing_variable_is_an_error(prompt: PromptFile) -> None:
    with pytest.raises(ConfigError, match=r"missing variables \['incidents'\]"):
        prompt.render({"severity": "x"})


def test_unused_variable_is_an_error(prompt: PromptFile) -> None:
    with pytest.raises(ConfigError, match=r"unused \['typo'\]"):
        prompt.render(VARIABLES | {"typo": "x"})


def test_report_placeholders_are_left_alone() -> None:
    text = PROMPT_TEXT.replace("You label bug reports.", "Write {{count.critical}} for numbers.")

    rendered = PromptFile.parse(text).render(VARIABLES)

    assert "{{count.critical}}" in rendered.system


def test_stray_dollar_sign_is_rejected_at_parse_time() -> None:
    with pytest.raises(ConfigError, match=r"\$\$"):
        PromptFile.parse(PROMPT_TEXT.replace("You label", "Refunds over $ 5. You label"))


@pytest.mark.parametrize(
    ("broken", "match"),
    [
        (PROMPT_TEXT.removeprefix("+++\n"), "must start with"),
        ("+++\nstage = 'classify'\n## system\nx\n## user\ny\n", "no closing"),
        (PROMPT_TEXT.replace("## user", "## usr"), "exactly one"),
        (
            PROMPT_TEXT.replace("## system", "## user", 1).replace(
                "## user\n<inc", "## system\n<inc"
            ),
            "followed by",
        ),
        (PROMPT_TEXT.replace('stage = "classify"', 'stage = "translate"'), "stage"),
        (PROMPT_TEXT.replace(f'tool = "{TOOL}"', 'tool = "submit classifications"'), "tool_name"),
        (PROMPT_TEXT.replace("version = 1", "version = 1 1"), "invalid prompt file"),
    ],
    ids=[
        "no-front-matter",
        "unclosed",
        "missing-user",
        "wrong-order",
        "bad-stage",
        "bad-tool",
        "bad-toml",
    ],
)
def test_malformed_files_are_config_errors(broken: str, match: str) -> None:
    with pytest.raises(ConfigError, match=match):
        PromptFile.parse(broken)


def test_load_prompt_reads_file(tmp_path: Path) -> None:
    path = tmp_path / "v1.md"
    path.write_text(PROMPT_TEXT, encoding="utf-8")

    assert load_prompt(path).id == "classify/v1"
