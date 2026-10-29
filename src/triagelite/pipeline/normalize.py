"""CSV rows to scrubbed, language-tagged incidents. Deterministic; no model calls."""

import csv
import io
import re
from collections import Counter
from collections.abc import Callable, Sequence
from functools import cache

from lingua import Language as LinguaLanguage
from lingua import LanguageDetector, LanguageDetectorBuilder
from pydantic import ValidationError

from triagelite.domain.enums import PiiKind
from triagelite.domain.errors import InputValidationError
from triagelite.domain.models import Incident, Language, RawIncident, RowError, StrictModel
from triagelite.domain.validation import format_validation_errors
from triagelite.pipeline.config import NormalizeConfig

BYTE_ORDER_MARK = "﻿"
REQUIRED_COLUMNS = frozenset({"external_id", "title", "description"})
KNOWN_COLUMNS = frozenset(RawIncident.model_fields)
INCIDENT_ID_FORMAT = "inc-{:04d}"

PLACEHOLDERS = {PiiKind.EMAIL: "[EMAIL]", PiiKind.PHONE: "[PHONE]", PiiKind.CREDENTIAL: "[TOKEN]"}
PHONE_MIN_DIGITS = 10
PHONE_MAX_DIGITS = 15
TOKEN_MIN_LENGTH = 32
CONFIDENCE_DECIMALS = 4

CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token)(\s*[:=]\s*)\S+"
)
BEARER_TOKEN = re.compile(r"(?i)\b(bearer\s+)\S+")
TOKEN_LIKE = re.compile(
    r"\b(?:eyJ[\w-]+\.[\w-]+\.[\w-]+"
    r"|AKIA[0-9A-Z]{16}"
    rf"|(?=[\w-]*\d)(?=[\w-]*[A-Za-z])[\w-]{{{TOKEN_MIN_LENGTH},}})"
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_CANDIDATE = re.compile(r"(?<![\w.])\+?\(?\d[\d\s()-]{6,}\d(?!\w|\.\d)")

LINGUA_TO_CODE: dict[LinguaLanguage, Language] = {
    LinguaLanguage.ENGLISH: "en",
    LinguaLanguage.SPANISH: "es",
}


class NormalizeResult(StrictModel):
    """Incidents ready to classify, plus rows that were rejected and what was redacted."""

    incidents: list[Incident]
    row_errors: list[RowError]
    pii_redactions: dict[PiiKind, int]


def normalize(csv_text: str, config: NormalizeConfig) -> NormalizeResult:
    """Parse, validate, scrub and language-tag a CSV of incidents.

    Raises:
        InputValidationError: the file as a whole is unusable (bad header, no rows).
    """
    rows, row_errors = parse_csv(csv_text)
    result = normalize_rows(rows, config)
    return result.model_copy(update={"row_errors": row_errors})


def normalize_rows(rows: Sequence[RawIncident], config: NormalizeConfig) -> NormalizeResult:
    """Scrub and language-tag rows that are already validated; IDs follow the given order."""
    redactions: Counter[PiiKind] = Counter()

    def scrub(value: str) -> str:
        clean, counts = scrub_pii(value)
        redactions.update(counts)
        return clean

    def scrub_optional(value: str | None) -> str | None:
        return None if value is None else scrub(value)

    scrubbed = [
        (
            scrub(row.title),
            scrub(row.description),
            scrub_optional(row.steps),
            scrub_optional(row.environment),
        )
        for row in rows
    ]
    detections = [detect_language(f"{title}\n{description}") for title, description, *_ in scrubbed]
    languages = resolve_languages(detections, config.min_language_confidence)

    incidents = [
        Incident(
            incident_id=INCIDENT_ID_FORMAT.format(position),
            external_id=row.external_id,
            lang=lang,
            lang_confidence=confidence,
            title=title,
            description=description,
            steps=steps,
            environment=environment,
            reported_at=row.reported_at,
        )
        for position, (
            row,
            (title, description, steps, environment),
            (lang, confidence),
        ) in enumerate(zip(rows, scrubbed, languages, strict=True), start=1)
    ]
    return NormalizeResult(
        incidents=incidents,
        row_errors=[],
        pii_redactions={kind: redactions[kind] for kind in PiiKind},
    )


def parse_csv(text: str) -> tuple[list[RawIncident], list[RowError]]:
    """Validate each row on its own: a bad row becomes a `RowError`, never a failed batch.

    Raises:
        InputValidationError: the header is wrong, the CSV can't be read, or no rows exist.
    """
    reader = csv.DictReader(io.StringIO(text.removeprefix(BYTE_ORDER_MARK)), strict=True)
    _check_header(reader.fieldnames)
    rows: list[RawIncident] = []
    errors: list[RowError] = []
    seen_ids: set[str] = set()
    try:
        for raw in reader:
            row_or_error = _parse_row(raw, reader.line_num, seen_ids)
            if isinstance(row_or_error, RowError):
                errors.append(row_or_error)
            else:
                rows.append(row_or_error)
                seen_ids.add(row_or_error.external_id)
    except csv.Error as error:
        msg = f"unreadable CSV at line {reader.line_num}: {error}"
        raise InputValidationError(msg) from error
    if not rows and not errors:
        raise InputValidationError("CSV has a header but no incident rows")
    return rows, errors


def _check_header(fieldnames: Sequence[str] | None) -> None:
    columns = {name.strip() for name in fieldnames or []}
    missing, unknown = REQUIRED_COLUMNS - columns, columns - KNOWN_COLUMNS
    if missing or unknown:
        msg = f"bad CSV header: missing {sorted(missing)}, unknown {sorted(unknown)}"
        raise InputValidationError(msg)


def _parse_row(
    raw: dict[str | None, object], line: int, seen_ids: set[str]
) -> RawIncident | RowError:
    external_id = str(raw.get("external_id") or "").strip() or None
    if None in raw:
        return RowError(line=line, external_id=external_id, errors=["more cells than columns"])
    try:
        row = RawIncident.model_validate({str(k).strip(): v for k, v in raw.items()})
    except ValidationError as error:
        return RowError(line=line, external_id=external_id, errors=format_validation_errors(error))
    if row.external_id in seen_ids:
        return RowError(line=line, external_id=external_id, errors=["duplicate external_id"])
    return row


def scrub_pii(text: str) -> tuple[str, Counter[PiiKind]]:
    """Replace emails, phone numbers and credentials with placeholders; count each kind."""
    counts: Counter[PiiKind] = Counter()

    def keep_prefix(kind: PiiKind) -> Callable[[re.Match[str]], str]:
        def replace(match: re.Match[str]) -> str:
            counts[kind] += 1
            return "".join(match.groups()) + PLACEHOLDERS[kind]

        return replace

    def whole(kind: PiiKind) -> Callable[[re.Match[str]], str]:
        def replace(match: re.Match[str]) -> str:
            counts[kind] += 1
            return PLACEHOLDERS[kind]

        return replace

    def phone(match: re.Match[str]) -> str:
        digits = sum(char.isdigit() for char in match.group())
        if not PHONE_MIN_DIGITS <= digits <= PHONE_MAX_DIGITS:
            return match.group()
        counts[PiiKind.PHONE] += 1
        return PLACEHOLDERS[PiiKind.PHONE]

    text = CREDENTIAL_ASSIGNMENT.sub(keep_prefix(PiiKind.CREDENTIAL), text)
    text = BEARER_TOKEN.sub(keep_prefix(PiiKind.CREDENTIAL), text)
    text = TOKEN_LIKE.sub(whole(PiiKind.CREDENTIAL), text)
    text = EMAIL.sub(whole(PiiKind.EMAIL), text)
    text = PHONE_CANDIDATE.sub(phone, text)
    return text, counts


@cache
def _detector() -> LanguageDetector:
    return LanguageDetectorBuilder.from_languages(*LINGUA_TO_CODE).build()


def detect_language(text: str) -> tuple[Language, float]:
    """Most likely language and its confidence; text without letters gets confidence 0.

    The confidence is rounded.
    """
    best = _detector().compute_language_confidence_values(text)[0]
    return LINGUA_TO_CODE[best.language], round(best.value, CONFIDENCE_DECIMALS)


def resolve_languages(
    detections: Sequence[tuple[Language, float]], min_confidence: float
) -> list[tuple[Language, float]]:
    """Replace low-confidence guesses with the batch's majority language.

    The original confidence is kept, so a low value still shows the label was a fallback.
    The majority counts confident detections only, or every guess if none is confident;
    ties go to the alphabetically first code.
    """
    confident = [lang for lang, score in detections if score >= min_confidence]
    pool = confident or [lang for lang, _ in detections]
    if not pool:
        return []
    majority = max(sorted(set(pool)), key=pool.count)
    return [(lang if score >= min_confidence else majority, score) for lang, score in detections]


def chunked[T](items: Sequence[T], size: int) -> list[list[T]]:
    """Split `items` into consecutive lists of at most `size`."""
    if size < 1:
        msg = f"chunk size must be positive, got {size}"
        raise ValueError(msg)
    return [list(items[start : start + size]) for start in range(0, len(items), size)]
