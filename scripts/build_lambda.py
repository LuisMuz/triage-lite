"""Zip the installed dependencies and the package into a Lambda layer and a code bundle."""

import sys
import zipfile
from collections.abc import Iterable
from pathlib import Path

REPO = Path(__file__).parents[1]
BUILD = REPO / "build" / "lambda"
DEPS = BUILD / "deps"
LAYER_ZIP = BUILD / "layer.zip"
CODE_ZIP = BUILD / "code.zip"
LAYER_ROOT = "python"
CODE_DIRS = ("src/triagelite", "config", "prompts")
SKIPPED_DIRS = frozenset({"__pycache__", "tests"})
SKIPPED_SUFFIXES = frozenset({".pyc", ".pyi"})
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o644 << 16
ELF_MAGIC = b"\x7fELF"
ELF_MACHINE_OFFSET = 18
AARCH64_MACHINE = b"\xb7\x00"
LAMBDA_UNZIPPED_LIMIT_BYTES = 250 * 1024 * 1024
BYTES_PER_MB = 1024 * 1024


class BuildError(Exception):
    """The package would not work on Lambda."""


def package_files(root: Path) -> list[Path]:
    """Files under `root` worth shipping: no bytecode, type stubs or bundled test suites."""
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix not in SKIPPED_SUFFIXES
        and not SKIPPED_DIRS.intersection(path.relative_to(root).parts)
    )


def check_architecture(paths: Iterable[Path]) -> None:
    """Fail on a native library built for another CPU, which would only crash once deployed."""
    for path in paths:
        with path.open("rb") as file:
            header = file.read(ELF_MACHINE_OFFSET + len(AARCH64_MACHINE))
        if header.startswith(ELF_MAGIC) and header[ELF_MACHINE_OFFSET:] != AARCH64_MACHINE:
            msg = f"{path} is not an ARM64 binary"
            raise BuildError(msg)


def write_zip(target: Path, entries: Iterable[tuple[str, Path]]) -> int:
    """Write sorted entries with fixed timestamps and return the unzipped size.

    Identical input gives an identical zip, so Terraform only redeploys what really changed.
    """
    unzipped = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = FILE_MODE
            content = path.read_bytes()
            archive.writestr(info, content)
            unzipped += len(content)
    return unzipped


def code_entries(repo: Path) -> list[tuple[str, Path]]:
    """The package at the zip's root, beside the config and prompts it reads at startup."""
    entries = []
    for directory in CODE_DIRS:
        root = repo / directory
        entries += [
            (f"{root.name}/{path.relative_to(root).as_posix()}", path)
            for path in package_files(root)
        ]
    return entries


def main() -> int:
    """Build both zips and report their sizes against the Lambda limit."""
    dependencies = package_files(DEPS)
    try:
        check_architecture(dependencies)
    except BuildError as error:
        print(error, file=sys.stderr)
        return 1
    layer_size = write_zip(
        LAYER_ZIP,
        [(f"{LAYER_ROOT}/{path.relative_to(DEPS).as_posix()}", path) for path in dependencies],
    )
    code_size = write_zip(CODE_ZIP, code_entries(REPO))
    total = layer_size + code_size
    for path, size in ((LAYER_ZIP, layer_size), (CODE_ZIP, code_size)):
        print(
            f"{path.name}: {path.stat().st_size / BYTES_PER_MB:.1f} MB zipped, "
            f"{size / BYTES_PER_MB:.1f} MB unzipped"
        )
    if total > LAMBDA_UNZIPPED_LIMIT_BYTES:
        print(f"{total / BYTES_PER_MB:.1f} MB exceeds the Lambda limit", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
