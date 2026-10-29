import pytest

from triagelite.domain.enums import PiiKind
from triagelite.domain.errors import InputValidationError
from triagelite.pipeline.config import NormalizeConfig
from triagelite.pipeline.normalize import (
    chunked,
    detect_language,
    normalize,
    parse_csv,
    resolve_languages,
    scrub_pii,
)

HEADER = "external_id,title,description,steps,environment,reported_at,reporter\n"


def csv_of(*rows: str, header: str = HEADER) -> str:
    return header + "".join(f"{row}\n" for row in rows)


class TestParseCsv:
    def test_valid_rows_parse(self) -> None:
        rows, errors = parse_csv(csv_of("QA-1,Login falla,Error 500,,,,", "QA-2,Cart,Empty,,,,"))

        assert [row.external_id for row in rows] == ["QA-1", "QA-2"]
        assert errors == []

    def test_byte_order_mark_is_tolerated(self) -> None:
        rows, _ = parse_csv("﻿" + csv_of("QA-1,t,d,,,,"))

        assert rows[0].external_id == "QA-1"

    def test_minimal_header_is_enough(self) -> None:
        rows, _ = parse_csv(csv_of("QA-1,t,d", header="external_id,title,description\n"))

        assert rows[0].steps is None

    def test_bad_rows_become_row_errors_and_batch_continues(self) -> None:
        rows, errors = parse_csv(
            csv_of(
                "QA-1,t,d,,,,", "QA-2,,missing title,,,,", "QA-3,t,d,,,not-a-date,", "QA-4,t,d,,,,"
            )
        )

        assert [row.external_id for row in rows] == ["QA-1", "QA-4"]
        assert [(e.line, e.external_id) for e in errors] == [(3, "QA-2"), (4, "QA-3")]
        assert any("title" in message for message in errors[0].errors)

    def test_row_with_extra_cells_is_rejected(self) -> None:
        rows, errors = parse_csv(csv_of("QA-1,t,d,,,,,surplus"))

        assert rows == []
        assert errors[0].errors == ["more cells than columns"]

    def test_duplicate_external_id_is_rejected(self) -> None:
        rows, errors = parse_csv(csv_of("QA-1,t,d,,,,", "QA-1,other,d,,,,"))

        assert len(rows) == 1
        assert errors[0].errors == ["duplicate external_id"]

    def test_row_errors_do_not_echo_incident_text(self) -> None:
        _, errors = parse_csv(csv_of("QA-1,,secret text ana@example.com,,,,"))

        assert "ana@example.com" not in errors[0].model_dump_json()

    @pytest.mark.parametrize(
        ("header", "match"),
        [
            ("external_id,title\n", r"missing \['description'\]"),
            ("external_id,title,description,priority\n", r"unknown \['priority'\]"),
            ("", "missing"),
        ],
    )
    def test_bad_header_fails_the_batch(self, header: str, match: str) -> None:
        with pytest.raises(InputValidationError, match=match):
            parse_csv(header + "QA-1,t,d\n")

    def test_header_only_file_fails_the_batch(self) -> None:
        with pytest.raises(InputValidationError, match="no incident rows"):
            parse_csv(HEADER)

    def test_unreadable_csv_fails_the_batch(self) -> None:
        with pytest.raises(InputValidationError, match="unreadable CSV"):
            parse_csv(csv_of('QA-1,"unclosed quote,d,,,,'))


class TestScrubPii:
    @pytest.mark.parametrize(
        ("text", "expected", "kind"),
        [
            ("write to ana.lopez@example.com today", "write to [EMAIL] today", PiiKind.EMAIL),
            ("call +52 55 1234 5678 now", "call [PHONE] now", PiiKind.PHONE),
            ("llamar al 5512345678", "llamar al [PHONE]", PiiKind.PHONE),
            ("call (555) 123-4567", "call [PHONE]", PiiKind.PHONE),
            (
                "llamar al +52 55 1234 5678. Hay que reembolsar.",
                "llamar al [PHONE]. Hay que reembolsar.",
                PiiKind.PHONE,
            ),
            ("Authorization: Bearer abc.def", "Authorization: Bearer [TOKEN]", PiiKind.CREDENTIAL),
            ("password=Hunter2024! failed", "password=[TOKEN] failed", PiiKind.CREDENTIAL),
            ("api_key: sk_live_51Hx", "api_key: [TOKEN]", PiiKind.CREDENTIAL),
            ("jwt eyJhbGciOi.eyJzdWIiOi.c2lnbmF0", "jwt [TOKEN]", PiiKind.CREDENTIAL),
            ("leaked AKIAIOSFODNN7EXAMPLE here", "leaked [TOKEN] here", PiiKind.CREDENTIAL),
            ("id 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b", "id [TOKEN]", PiiKind.CREDENTIAL),
        ],
    )
    def test_personal_and_secret_data_is_replaced(
        self, text: str, expected: str, kind: PiiKind
    ) -> None:
        scrubbed, counts = scrub_pii(text)

        assert scrubbed == expected
        assert counts == {kind: 1}

    @pytest.mark.parametrize(
        "text",
        [
            "since v2.3.1 on 2026-10-20T14:30:00Z",
            "error 500 at Cart.java:42",
            "server 192.168.100.200 down",
            "order 12345 failed after 3 retries",
            "NullPointerException in CheckoutService",
            "ext 555-1234 please",
        ],
    )
    def test_look_alikes_are_kept(self, text: str) -> None:
        assert scrub_pii(text) == (text, {})


class TestLanguage:
    @pytest.mark.parametrize(
        ("text", "lang"),
        [
            ("El botón de pagar no responde en iOS", "es"),
            ("Checkout button does nothing on iOS", "en"),
        ],
    )
    def test_detects_spanish_and_english(self, text: str, lang: str) -> None:
        detected, confidence = detect_language(text)

        assert detected == lang
        assert confidence > 0.7

    def test_text_without_letters_has_zero_confidence(self) -> None:
        assert detect_language("500 404 503")[1] == 0.0

    def test_low_confidence_falls_back_to_majority(self) -> None:
        resolved = resolve_languages([("es", 0.9), ("es", 0.95), ("en", 0.2), ("en", 0.0)], 0.7)

        assert resolved == [("es", 0.9), ("es", 0.95), ("es", 0.2), ("es", 0.0)]

    def test_majority_uses_raw_guesses_when_nothing_is_confident(self) -> None:
        assert resolve_languages([("en", 0.3), ("es", 0.2), ("es", 0.1)], 0.7)[0][0] == "es"

    def test_tie_is_deterministic(self) -> None:
        assert resolve_languages([("es", 0.9), ("en", 0.9), ("es", 0.1)], 0.7)[2][0] == "en"

    def test_empty_batch(self) -> None:
        assert resolve_languages([], 0.7) == []


class TestNormalize:
    def test_builds_scrubbed_incidents_with_stable_ids(
        self, normalize_config: NormalizeConfig
    ) -> None:
        text = csv_of(
            "QA-1,No puedo pagar,Llamar al +52 55 1234 5678 por el cobro doble,"
            ",web,2026-10-01T09:00:00Z,ana@example.com",
            "QA-2,,bad row,,,,",
            "QA-3,Checkout broken,Place order returns 500 for every user,,,,",
        )

        result = normalize(text, normalize_config)

        first, second = result.incidents
        assert (first.incident_id, second.incident_id) == ("inc-0001", "inc-0002")
        assert (first.external_id, first.lang, second.lang) == ("QA-1", "es", "en")
        assert "[PHONE]" in first.description
        assert first.environment == "web"
        assert first.reported_at is not None
        assert len(result.row_errors) == 1
        assert result.pii_redactions == {PiiKind.EMAIL: 0, PiiKind.PHONE: 1, PiiKind.CREDENTIAL: 0}

    def test_reporter_never_reaches_the_incident(self, normalize_config: NormalizeConfig) -> None:
        result = normalize(csv_of("QA-1,t,d,,,,ana@example.com"), normalize_config)

        assert "ana@example.com" not in result.model_dump_json()

    def test_same_csv_gives_same_output(self, normalize_config: NormalizeConfig) -> None:
        text = csv_of("QA-1,Login falla,Error al entrar,,,,", "QA-2,Cart empty,Items vanish,,,,")

        assert normalize(text, normalize_config) == normalize(text, normalize_config)


class TestChunked:
    def test_splits_with_a_short_last_chunk(self) -> None:
        assert chunked(list(range(7)), 3) == [[0, 1, 2], [3, 4, 5], [6]]

    def test_empty_input(self) -> None:
        assert chunked([], 10) == []

    def test_size_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            chunked([1], 0)
