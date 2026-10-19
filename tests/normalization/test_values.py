"""Synthetic golden values; literals derived from the T06 contract, no source content."""

from decimal import Decimal

import pytest

from services.data.normalization.values import money, number, temporal, text


def test_unicode_nfc_entities_search_and_program_discriminators():
    value = text("  Đại&nbsp;học\u00a0Quốc tế\u200b — Phân hiệu\r\nTiếng Anh  ")
    assert value.display == "Đại học Quốc tế — Phân hiệu Tiếng Anh"
    assert value.search_key == "dai hoc quoc te — phan hieu tieng anh"
    assert value.raw == "  Đại&nbsp;học\u00a0Quốc tế\u200b — Phân hiệu\r\nTiếng Anh  "


@pytest.mark.parametrize(
    "raw,want",
    [("24,50", "24.50"), ("24.50", "24.50"), ("0", "0"), ("24.123456789", "24.123456789")],
)
def test_decimal_without_rounding(raw, want):
    value = number(raw)
    assert value.status == "value"
    assert value.value == Decimal(want)
    assert value.model_dump(mode="json")["value"] == want


@pytest.mark.parametrize(
    "raw,status",
    [
        ("", "missing"),
        ("  ", "missing"),
        ("—", "not_reported"),
        ("-", "not_reported"),
        ("N/A", "not_applicable"),
    ],
)
def test_null_never_zero(raw, status):
    value = number(raw)
    assert value.value is None and value.status == status


def test_numeric_ambiguity_needs_explicit_grammar_evidence():
    value = number("1.200")
    assert value.status == "ambiguous" and value.value is None
    assert value.issue == "NUMERIC_AMBIGUOUS"
    assert number("1.200", grouping=".", evidence="fixture:header-locale").value == Decimal("1200")
    with pytest.raises(ValueError):
        number("1.200", grouping=".")
    assert number("1,200").status == "ambiguous"
    assert number("NaN").value is None


@pytest.mark.parametrize(
    "raw,op", [("≥ 24", "gte"), (">= 24", "gte"), ("<24", "lt"), ("≤24", "lte")]
)
def test_operator_is_not_discarded(raw, op):
    value = number(raw)
    assert value.operator == op and value.value == Decimal("24")


def test_money_keeps_range_currency_and_billing_unit():
    value = money("25–30 triệu/năm")
    assert value.minimum == Decimal("25000000")
    assert value.maximum == Decimal("30000000")
    assert value.value is None and value.currency == "VND" and value.unit == "academic_year"
    value = money("1,2 triệu/tín chỉ")
    assert value.value == Decimal("1200000") and value.unit == "credit"
    assert money("25.000.000 đồng/năm").value == Decimal("25000000")
    assert money("1.200 đồng/tín chỉ").issue == "NUMERIC_AMBIGUOUS"
    assert money("100 USD/học kỳ").currency == "USD"
    assert money("100 USD/học kỳ").unit == "semester"
    assert money("100").status == "ambiguous"
    assert money("30–25 triệu/năm").status == "ambiguous"


def test_time_precision_and_timezone_are_not_invented():
    assert temporal("03/09/2025").value == "2025-09-03"
    assert temporal("03/09/2025").precision == "date"
    assert temporal("2026").precision == "year"
    assert temporal("2025-09").precision == "month"
    assert temporal("2025-09-03T10:30:00+07:00").value == "2025-09-03T03:30:00+00:00"
    assert temporal("2025-09-03T10:30").issue == "TIMEZONE_MISSING"
    assert temporal("31/02/2025").status == "ambiguous"


def test_score_range_units_and_mixed_money_context():
    value = number("24,50–25.75 điểm")
    assert value.minimum == Decimal("24.50") and value.maximum == Decimal("25.75")
    assert value.operator == "range" and value.unit == "point" and value.value is None
    assert number("24,50 điểm").value == Decimal("24.50")
    assert number("25–24").status == "ambiguous"
    assert money("25-30 triệu/năm").maximum == Decimal("30000000")
    assert money("100 USD hoặc VND/năm").status == "ambiguous"
    assert money("100 đồng/tín chỉ hoặc /năm").status == "ambiguous"


def test_fractional_timestamp_does_not_truncate_or_invent_precision():
    value = temporal("2025-09-03T10:30:00.123456789+07:00")
    assert value.value == "2025-09-03T03:30:00.123456789+00:00"
    assert value.fraction_digits == 9
    assert temporal("2025-09-03T10:30:00.1200+07:00").value == "2025-09-03T03:30:00.1200+00:00"
    assert temporal("2025-09-03T10:30+07:00").value == "2025-09-03T03:30+00:00"
    assert temporal("2025-09-03T10+07:00").value is None
