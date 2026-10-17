import re
import unicodedata
from decimal import Decimal
from typing import Any, Literal

from services.data.parsers.contract import ExtractedObservation, FactKind, SnapshotRef


def folded(value: str) -> str:
    # Keyword matching only. Never used to replace raw data or resolve entities.
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
        if unicodedata.category(c) != "Mn"
    )


def classify(text: str, *, table: bool = False) -> tuple[FactKind, list[str]]:
    value = folded(text)
    threshold = any(
        x in value for x in ["nguong dau vao", "diem san", "dieu kien nop", "entry threshold"]
    )
    cutoff = any(
        x in value for x in ["diem trung tuyen", "diem chuan trung tuyen", "admission cutoff"]
    )
    if threshold and not cutoff:
        return "catalog", ["entry_threshold_not_cutoff"]
    if cutoff and not threshold:
        return "cutoff", []
    if cutoff and threshold:
        return "catalog", ["mixed_threshold_cutoff_context"]
    policy_topics = sum(
        bool(re.search(pattern, value))
        for pattern in [
            r"hoc phi|tuition",
            r"hoc bong|scholarship",
            r"diem thuong|diem cong|scoring",
        ]
    )
    if not table and policy_topics > 1 and len(re.findall(r"\b\d+\.\s+\D", value)) > 1:
        return "catalog", ["mixed_narrative_fact_kinds"]
    if "hoc bong" in value or "scholarship" in value:
        return "scholarship", []
    if "hoc phi" in value or "tuition" in value:
        return "tuition", []
    if any(
        x in value
        for x in ["diem thuong", "diem xet thuong", "diem kk", "cong thuc tinh", "diem xet tuyen ="]
    ):
        return "scoring_rule", []
    if any(x in value for x in ["quy doi", "conversion rule"]):
        return "conversion_rule", []
    if table and re.search(r"diem\s*tt\b", value):
        return "catalog", ["ambiguous_abbreviated_cutoff_header"]
    if table and not any(
        x in value for x in ["nganh", "phuong thuc", "chi tieu", "so luong du kien", "program"]
    ):
        return "catalog", ["ambiguous_table_kind"]
    return "catalog", []


def observation(
    ref: SnapshotRef,
    kind: FactKind,
    locator: str,
    version: str,
    method: Literal["html_dom", "pdf_text", "pdf_table"],
    fields: dict[str, Any],
    confidence: str = "0.7000",
) -> ExtractedObservation:
    return ExtractedObservation(
        snapshot_id=ref.snapshot_id,
        source_id=ref.source_id,
        fact_kind=kind,
        record_locator=locator,
        parser_version=version,
        extraction_method=method,
        raw_fields=fields,
        extraction_confidence=Decimal(confidence),
    )


def relevant(text: str) -> bool:
    return bool(
        re.search(
            r"tuyen sinh|phuong thuc|nguong|diem san|hoc phi|hoc bong|quy doi|diem thuong|diem trung tuyen|chi tieu|admission|tuition|scholarship|cutoff",
            folded(text),
        )
    )
