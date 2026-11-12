import zipfile
from pathlib import Path

import pytest

from scripts.build_lambda import (
    AARCH64_MACHINE,
    ELF_MACHINE_OFFSET,
    ELF_MAGIC,
    BuildError,
    check_architecture,
    code_entries,
    package_files,
    write_zip,
)

REPO = Path(__file__).parents[1]
X86_64_MACHINE = b"\x3e\x00"


def elf(machine: bytes) -> bytes:
    return ELF_MAGIC + bytes(ELF_MACHINE_OFFSET - len(ELF_MAGIC)) + machine


def test_bytecode_stubs_and_test_suites_are_left_out(tmp_path: Path) -> None:
    for name in ("pkg/a.py", "pkg/a.pyi", "pkg/__pycache__/a.pyc", "pkg/tests/test_a.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")

    assert package_files(tmp_path) == [tmp_path / "pkg" / "a.py"]


def test_arm64_libraries_and_plain_files_pass(tmp_path: Path) -> None:
    library = tmp_path / "ok.so"
    library.write_bytes(elf(AARCH64_MACHINE))
    text = tmp_path / "a.py"
    text.write_text("x = 1")

    check_architecture([library, text])


def test_a_library_for_another_cpu_fails_the_build(tmp_path: Path) -> None:
    library = tmp_path / "bad.so"
    library.write_bytes(elf(X86_64_MACHINE))

    with pytest.raises(BuildError, match=r"bad\.so"):
        check_architecture([library])


def test_the_same_files_give_byte_identical_zips(tmp_path: Path) -> None:
    source = tmp_path / "a.txt"
    source.write_text("same")
    first, second = tmp_path / "1.zip", tmp_path / "2.zip"

    write_zip(first, [("a.txt", source)])
    source.touch()
    write_zip(second, [("a.txt", source)])

    assert first.read_bytes() == second.read_bytes()


def test_the_zip_reports_its_unzipped_size_and_contents(tmp_path: Path) -> None:
    source = tmp_path / "a.txt"
    source.write_text("12345")
    target = tmp_path / "out.zip"

    assert write_zip(target, [("dir/a.txt", source)]) == 5
    with zipfile.ZipFile(target) as archive:
        assert archive.read("dir/a.txt") == b"12345"


def test_the_code_bundle_has_what_lambda_loads() -> None:
    names = {name for name, _ in code_entries(REPO)}

    assert "triagelite/handlers/classify_chunk.py" in names
    assert "config/models.toml" in names
    assert "prompts/classify/v3.md" in names
