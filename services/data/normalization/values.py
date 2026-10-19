"""Loss-aware lexical values. Decimal is always constructed from a string."""

import html
import re
import unicodedata
from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TextValue(BaseModel):
    model_config = ConfigDict(frozen=True)
    raw: str
    display: str
    search_key: str


def text(raw: str) -> TextValue:
    display = unicodedata.normalize("NFC", html.unescape(raw))
    display = re.sub(r"[\u200b\ufeff]", "", display)
    display = " ".join(display.split())
    key = unicodedata.normalize("NFD", display.casefold().replace("đ", "d"))
    key = "".join(c for c in key if not unicodedata.combining(c))
    return TextValue(raw=raw, display=display, search_key=key)


class NumericValue(BaseModel):
    model_config = ConfigDict(frozen=True)
    raw: str
    status: Literal["value", "missing", "not_reported", "not_applicable", "ambiguous"]
    value: Decimal | None = None
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    operator: Literal["eq", "gte", "gt", "lte", "lt", "range"] = "eq"
    currency: str | None = None
    unit: str | None = None
    issue: str | None = None
    evidence: str | None = None
    approximate: bool = False
    rule_version: str = "lexical/1.0.0"


def number(raw: str, *, grouping: str | None = None, evidence: str | None = None) -> NumericValue:
    if grouping and (grouping not in {".", ","} or not evidence):
        raise ValueError("Grouping grammar requires explicit evidence")
    value = text(raw).display
    if not value:
        return NumericValue(raw=raw, status="missing")
    if value in {"-", "—", "–"}:
        return NumericValue(raw=raw, status="not_reported")
    if value.casefold() in {"n/a", "na"}:
        return NumericValue(raw=raw, status="not_applicable")
    unit = "point" if re.search(r"\s*(?:điểm|points?)$", value, re.I) else None
    if unit:
        value = re.sub(r"\s*(?:điểm|points?)$", "", value, flags=re.I)
    ranges = re.split(r"\s*[–—]\s*|(?<=\d)\s*-\s*(?=\d)", value)
    if len(ranges) == 2:
        low, high = (number(v, grouping=grouping, evidence=evidence) for v in ranges)
        if (
            low.value is not None
            and high.value is not None
            and low.operator == high.operator == "eq"
            and low.value <= high.value
        ):
            return NumericValue(
                raw=raw,
                status="value",
                minimum=low.value,
                maximum=high.value,
                operator="range",
                unit=unit,
                evidence=evidence,
            )
        return NumericValue(raw=raw, status="ambiguous", unit=unit, issue="NUMERIC_AMBIGUOUS")
    operator: Literal["eq", "gte", "gt", "lte", "lt", "range"] = "eq"
    match = re.match(r"^(>=|<=|≥|≤|>|<|=)\s*", value)
    if match:
        operator = {
            ">=": "gte",
            "≥": "gte",
            "<=": "lte",
            "≤": "lte",
            ">": "gt",
            "<": "lt",
            "=": "eq",
        }[match[1]]  # type: ignore[assignment]
        value = value[match.end() :]
    canonical = value
    if grouping:
        other = "," if grouping == "." else "."
        grammar = rf"[+-]?\d{{1,3}}(?:{re.escape(grouping)}\d{{3}})+(?:{re.escape(other)}\d+)?"
        if re.fullmatch(grammar, value):
            canonical = value.replace(grouping, "").replace(other, ".")
        elif re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", value) and grouping not in value:
            canonical = value.replace(other, ".")
        else:
            return NumericValue(raw=raw, status="ambiguous", issue="NUMERIC_AMBIGUOUS")
    elif re.fullmatch(r"[+-]?\d+[.,]\d{3}", value):
        return NumericValue(raw=raw, status="ambiguous", issue="NUMERIC_AMBIGUOUS")
    elif re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", value):
        canonical = value.replace(",", ".")
    else:
        return NumericValue(raw=raw, status="ambiguous", issue="NUMERIC_AMBIGUOUS")
    return NumericValue(
        raw=raw,
        status="value",
        value=Decimal(canonical),
        operator=operator,
        unit=unit,
        evidence=evidence,
    )


def money(raw: str) -> NumericValue:
    value = text(raw).display
    key = text(raw).search_key
    currency = (
        "USD"
        if re.search(r"\busd\b|\$", key)
        else "VND"
        if re.search(r"dong|vnd|trieu|nghin|₫", key)
        else None
    )
    unit = next(
        (
            unit
            for pattern, unit in [
                (r"/\s*(?:tin chi|credit)", "credit"),
                (r"/\s*(?:hoc ky|semester)", "semester"),
                (r"/\s*(?:nam(?: hoc)?|year)", "academic_year"),
            ]
            if re.search(pattern, key)
        ),
        None,
    )
    currencies = sum(
        bool(re.search(pattern, key)) for pattern in [r"\busd\b|\$", r"dong|vnd|trieu|nghin|₫"]
    )
    billing_units = sum(
        bool(re.search(pattern, key))
        for pattern in [
            r"/\s*(?:tin chi|credit)",
            r"/\s*(?:hoc ky|semester)",
            r"/\s*(?:nam(?: hoc)?|year)",
        ]
    )
    if currencies > 1 or billing_units > 1:
        return NumericValue(raw=raw, status="ambiguous", issue="MONEY_CONTEXT_AMBIGUOUS")
    missing = number(value)
    if missing.status in {"missing", "not_reported", "not_applicable"}:
        return missing
    if currency is None or unit is None:
        return NumericValue(
            raw=raw, status="ambiguous", currency=currency, unit=unit, issue="MONEY_CONTEXT_MISSING"
        )
    multiplier = (
        Decimal("1000000")
        if "trieu" in key
        else Decimal("1000")
        if "nghin" in key
        else Decimal("1")
    )
    # Accept a lexical amount, not a whole paragraph containing percentages/citations.
    amount = re.sub(r"/\s*(?:tin chi|credit|hoc ky|semester|nam(?: hoc)?|year)", "", key)
    amount = re.sub(r"\b(?:trieu|nghin|dong|vnd|usd)\b|[₫$]", "", amount).strip()
    approximate = bool(re.search(r"\bkhoang\b", amount))
    amount = re.sub(r"^(?:khoang)\s*", "", amount)
    tokens = re.split(r"\s*[–—]\s*|(?<=\d)\s*-\s*(?=\d)", amount)
    if len(tokens) > 2:
        return NumericValue(raw=raw, status="ambiguous", issue="NUMERIC_AMBIGUOUS")
    parsed = []
    for token in tokens:
        token = token.strip()
        # Multiple groups plus an explicit currency are unambiguous; one group remains ambiguous.
        grouped = bool(re.fullmatch(r"\d{1,3}(?:\.\d{3}){2,}", token))
        item = number(
            token,
            grouping="." if grouped else None,
            evidence="lexical:VND-multi-group" if grouped else None,
        )
        if item.status != "value" or item.value is None or item.value < 0:
            return NumericValue(
                raw=raw, status="ambiguous", currency=currency, unit=unit, issue="NUMERIC_AMBIGUOUS"
            )
        with localcontext() as numeric_context:
            numeric_context.prec = max(28, len(item.value.as_tuple().digits) + 8)
            parsed.append(item.value * multiplier)
    if len(parsed) == 2:
        if parsed[0] > parsed[1]:
            return NumericValue(raw=raw, status="ambiguous", issue="NUMERIC_AMBIGUOUS")
        return NumericValue(
            raw=raw,
            status="value",
            minimum=parsed[0],
            maximum=parsed[1],
            operator="range",
            currency=currency,
            unit=unit,
            approximate=approximate,
        )
    return NumericValue(
        raw=raw,
        status="value",
        value=parsed[0],
        operator=number(tokens[0].strip()).operator,
        currency=currency,
        unit=unit,
        approximate=approximate,
    )


class TimeValue(BaseModel):
    model_config = ConfigDict(frozen=True)
    raw: str
    value: str | None = None
    fraction_digits: int | None = None
    precision: Literal["year", "month", "date", "minute", "second", "fraction", "unknown"] = (
        "unknown"
    )
    status: Literal["value", "missing", "ambiguous"]
    issue: str | None = None


def temporal(raw: str) -> TimeValue:
    value = text(raw).display
    if not value:
        return TimeValue(raw=raw, status="missing")
    try:
        if re.fullmatch(r"\d{4}", value):
            date(int(value), 1, 1)
            return TimeValue(raw=raw, value=value, precision="year", status="value")
        if re.fullmatch(r"\d{4}-\d{2}", value):
            date.fromisoformat(value + "-01")
            return TimeValue(raw=raw, value=value, precision="month", status="value")
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
            result = datetime.strptime(value, "%d/%m/%Y").date()
            return TimeValue(raw=raw, value=result.isoformat(), precision="date", status="value")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return TimeValue(
                raw=raw,
                value=date.fromisoformat(value).isoformat(),
                precision="date",
                status="value",
            )
        timestamp = re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?P<seconds>:\d{2})?(?:\.(?P<fraction>\d+))?(?P<zone>Z|[+-]\d{2}:\d{2})?",
            value,
        )
        if timestamp is None or (timestamp["fraction"] and not timestamp["seconds"]):
            return TimeValue(raw=raw, status="ambiguous", issue="TIME_PRECISION_UNSUPPORTED")
        result_dt = datetime.fromisoformat(value)
        if result_dt.tzinfo is None:
            return TimeValue(raw=raw, status="ambiguous", issue="TIMEZONE_MISSING")
        utc = result_dt.astimezone(UTC)
        # datetime truncates fractions beyond microseconds. Offset grammar is whole minutes,
        # so retain the original fractional string independently of whole-second conversion.
        if timestamp["fraction"]:
            exact = utc.strftime("%Y-%m-%dT%H:%M:%S") + "." + timestamp["fraction"] + "+00:00"
            return TimeValue(
                raw=raw,
                value=exact,
                precision="fraction",
                fraction_digits=len(timestamp["fraction"]),
                status="value",
            )
        precision: Literal["minute", "second"] = "second" if timestamp["seconds"] else "minute"
        return TimeValue(
            raw=raw,
            value=utc.isoformat(timespec="minutes" if precision == "minute" else "seconds"),
            precision=precision,
            status="value",
        )
    except ValueError:
        return TimeValue(raw=raw, status="ambiguous", issue="TIME_AMBIGUOUS")
