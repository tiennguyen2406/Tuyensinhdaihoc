"""PTIT2025 historical archive: one published value, unresolved method, raw TTNV."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from services.api.source_profiles import SourceProfile
from services.data.normalization.values import number
from services.data.parsers.common import folded
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locator, table_rows, text

VERSION = "html-ptit-2025-historical/1.0.0"
URL = "https://tuyensinh.ptit.edu.vn/gioi-thieu/xem-diem-cac-nam-truoc/diem-trung-tuyen-nam-2025/"
ROOT = ".elementor-5168 .elementor-widget-text-editor > .elementor-widget-container"
HEADERS = [
    "TT",
    "Tên ngành, chương trình",
    "Mã ngành, chương trình",
    "Điểm chuẩn trúng tuyển",
    "Thứ tự nguyện vọng (TTNV) trúng tuyển khi thí sinh có điểm xét tuyển bằng mức điểm trúng tuyển (*)",
]


def key(value: str) -> str:
    return " ".join(folded(value).split())


def evidence(node: Tag) -> dict[str, str]:
    return dict(text=text(node), raw_text=node.get_text(), locator=locator(node))


def score_reason(f: dict[str, Any]) -> str | None:
    for i in [1, 2, 3]:
        slot = f["cells"][i]
        origin = f["origin_cells"].get(slot.get("origin"), {})
        if (
            slot.get("span_reference")
            or slot.get("column") != i
            or origin.get("column") != i
            or origin.get("row")
            != f["origin_cells"].get(f["cells"][2].get("origin"), {}).get("row")
            or origin.get("rowspan") != 1
            or origin.get("colspan") != 1
            or origin.get("raw_text") != slot.get("raw_text")
        ):
            return "ORIGINAL_UNSPANNED_CELL_REQUIRED"
    if not all(f["cells"][i].get("text") for i in [1, 2]):
        return "PROGRAM_CODE_NAME_REQUIRED"
    n = number(f["cells"][3].get("raw_text") or "")
    if n.status in {"missing", "not_reported", "not_applicable"}:
        return "VALUE_NOT_REPORTED"
    if n.status != "value" or n.operator != "eq" or n.value is None or n.value < 0:
        return "NUMERIC_VALUE_REQUIRED"
    return None


def ttnv(slot: dict[str, Any], headers: list[dict[str, Any]]) -> dict[str, Any]:
    raw = slot.get("raw_text")
    match = re.fullmatch(r"\s*TTNV\s*(<=|≤|=)\s*([0-9]+)\s*", raw or "")
    valid = bool(match and int(match[2]) > 0 and not slot.get("span_reference"))
    return dict(
        raw_text=raw,
        locator=slot.get("origin"),
        header_path=headers,
        operator=match[1] if valid and match else None,
        bound=int(match[2]) if valid and match else None,
        status="source_predicate" if valid else "needs_review",
        span_reference=slot.get("span_reference"),
        executable=False,
    )


def parse_ptit_2025(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits,
    version: str = VERSION,
) -> ParseResult:
    result = ParseResult(metadata=dict(physical_row_ledger=[], score_cell_ledger=[]))
    if ref.final_url != URL or profile.university_key != "ptit" or len(data) > limits.max_bytes:
        result.issue("PTIT2025_SOURCE", "document", "Exact archive URL required")
        return result
    soup = BeautifulSoup(data, "html.parser")
    roots = soup.select(ROOT)
    titles = [h for h in soup.find_all("h1") if key(text(h)) == "diem trung tuyen 2025"]
    if len(roots) != 1 or len(titles) != 1:
        result.issue(
            "PTIT2025_ARCHIVE_CONTEXT", "document", "Unique archive and explicit2025 title required"
        )
        return result
    root = roots[0]
    common: dict[str, Any] = dict(
        snapshot_id=str(ref.snapshot_id),
        snapshot_sha256=ref.raw_hash,
        source_url=ref.final_url,
        title=evidence(titles[0]),
        admission_year=2025,
        publication_date=dict(value=None, precision="unknown"),
        source_context="historical_archive_not_contemporaneous_notice",
    )
    groups = []
    # Enumerate all rows before grid extraction so a resource error retains a full ledger.
    for table in root.find_all("table", recursive=False):
        heading = table.find_previous_sibling("ol")
        campus = next(
            (
                c
                for c, region in [("BVH", "bac"), ("BVS", "nam")]
                if heading and key(text(heading)) == f"co so dao tao phia {region} (ma {c.lower()})"
            ),
            None,
        )
        rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
        is_cutoff = bool(
            rows
            and any(
                key(text(c)) == key(HEADERS[3])
                for c in rows[0].find_all(["td", "th"], recursive=False)
            )
        )
        section = None
        entries = []
        for index, row in enumerate(rows):
            own = row.find_all(["td", "th"], recursive=False)
            kind = (
                "header"
                if index == 0
                else "section"
                if own and text(own[0]) in {"I", "II", "III", "IV"}
                else "program"
                if is_cutoff
                else "unrelated"
            )
            if kind == "section":
                section = evidence(row)
            entry = dict(
                row_locator=locator(row),
                campus=campus,
                section=section,
                classification=kind,
                status="blocked_or_needs_review" if kind == "program" else "not_a_cutoff_row",
                reason="GRID_UNAVAILABLE" if kind == "program" else kind.upper(),
            )
            result.metadata["physical_row_ledger"].append(entry)
            if kind == "program":
                cell = dict(
                    row_locator=locator(row),
                    campus=campus,
                    section=section,
                    score_locator=None,
                    raw_score=None,
                    code=None,
                    program=None,
                    status="blocked_or_needs_review",
                    reason="GRID_UNAVAILABLE",
                )
                result.metadata["score_cell_ledger"].append(cell)
                entries.append((row, entry, cell))
        if is_cutoff:
            groups.append((table, heading, campus, entries))
    if not groups:
        result.issue(
            "PTIT2025_TABLES_MISSING", locator(root), "No recognized archive cutoff tables"
        )
    remaining = limits.max_cells
    for table, heading, campus, entries in groups:
        extracted = ParseResult()
        remaining -= table_rows(
            table,
            ref,
            extracted,
            [common["title"]],
            remaining,
            version,
            header_row_count=1,
            score_columns=frozenset({3}),
        )
        result.issues.extend(extracted.issues)
        if any(i.severity == "error" for i in extracted.issues):
            result.observations = []
            for e in [
                *result.metadata["physical_row_ledger"],
                *result.metadata["score_cell_ledger"],
            ]:
                if e["status"] == "eligible_source_cell":
                    e.update(status="blocked_or_needs_review", reason="DOCUMENT_RESOURCE_ERROR")
            return result
        byrow = {o.record_locator: o for o in extracted.observations}
        for row, entry, cell in entries:
            obs = byrow.get(locator(row))
            if obs is None:
                continue
            f = obs.raw_fields
            valid = (
                campus
                and entry["section"]
                and len(f["cells"]) == len(f["headers"]) == 5
                and [[key(h["text"]) for h in path] for path in f["headers"]]
                == [[key(h)] for h in HEADERS]
            )
            slot = f["cells"][3] if len(f["cells"]) > 3 else {}
            reason = score_reason(f) if valid else "HEADER_CAMPUS_SECTION_REQUIRED"
            status = (
                "eligible_source_cell"
                if reason is None
                else "not_a_cutoff_row"
                if reason == "VALUE_NOT_REPORTED"
                else "blocked_or_needs_review"
            )
            values = dict(
                score_locator=slot.get("origin"),
                raw_score=slot.get("raw_text"),
                code=f["cells"][2].get("raw_text") if len(f["cells"]) > 2 else None,
                program=f["cells"][1].get("raw_text") if len(f["cells"]) > 1 else None,
                status=status,
                reason=reason,
            )
            cell.update(values)
            entry.update(values)
            if not valid:
                result.issue(
                    "PTIT2025_ROW_BINDING",
                    locator(row),
                    "Strict archive header/campus/section required",
                )
                continue
            assert heading is not None
            mapping = common | dict(
                campus=campus,
                campus_evidence=evidence(heading),
                section=entry["section"],
                table_locator=locator(table),
                TTNV=ttnv(f["cells"][4], f["headers"][4]),
            )
            result.observations.append(
                obs.model_copy(
                    update=dict(
                        fact_kind="cutoff",
                        issues=[],
                        raw_fields=f
                        | dict(
                            context=[
                                common["title"],
                                mapping["campus_evidence"],
                                mapping["section"],
                            ],
                            footnotes=[],
                            ptit_2025=mapping,
                        ),
                    )
                )
            )
    return result
