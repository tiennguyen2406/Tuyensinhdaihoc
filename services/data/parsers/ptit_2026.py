"""PTIT2026 original HTML score cells; nominal scales are evidence, never rules."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from services.api.source_profiles import SourceProfile
from services.data.normalization.values import number
from services.data.parsers.common import folded
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locator, table_rows, text

VERSION = "html-ptit-2026-multimethod/1.0.1"
URL = "https://tuyensinh.ptit.edu.vn/thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2026/"
TITLE = "Thông báo Điểm chuẩn trúng tuyển vào đại học hệ chính quy năm 2026"
METHODS = {
    "THPT": (
        "THPT",
        "thpt_examination",
        None,
        "30",
        "Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2026 (thang 30)",
    ),
    "TALENT": (
        "Hồ sơ năng lực (tài năng)",
        "capability_portfolio",
        None,
        "100",
        "Phương thức xét tuyển dựa vào hồ sơ năng lực (xét tuyển tài năng) (thang 100)",
    ),
    "SAT": ("SAT", "international_certificate", "SAT", "1600", "Chứng chỉ SAT (thang 1600)"),
    "ACT": ("ACT", "international_certificate", "ACT", "36", "Chứng chỉ ACT (thang 36)"),
    "TSA": ("TSA", "aptitude_thinking_examination", "TSA", "100", "Bài thi TSA (thang 100)"),
    "HSA": ("HSA", "aptitude_thinking_examination", "HSA", "150", "Bài thi HSA (thang 150)"),
    "V-ACT": (
        "V-ACT",
        "aptitude_thinking_examination",
        "V-ACT",
        "1200",
        "Bài thi V-ACT (thang 1200)",
    ),
    "SPT": ("SPT", "aptitude_thinking_examination", "SPT", "30", "Bài thi SPT (thang 30)"),
    "COMBINED": (
        "Kết hợp",
        "combined_admission",
        None,
        "30",
        "Phương thức xét tuyển Kết hợp (thang 30)",
    ),
}


def key(value: str) -> str:
    return " ".join(folded(value).split())


def evidence(node: Tag) -> dict[str, str]:
    return dict(text=text(node), raw_text=node.get_text(), locator=locator(node))


def header_paths() -> list[list[str]]:
    paths = [[h] for h in ["TT", "Tên ngành, chương trình", "Mã xét tuyển"]]
    for _, family, instrument, _, label in METHODS.values():
        parents = (
            ["Xét tuyển dựa vào kết quả Chứng chỉ đánh giá năng lực quốc tế"]
            if family == "international_certificate"
            else ["Xét tuyển dựa vào kết quả trong các kỳ thi ĐGNL, ĐGTD"]
            if instrument
            else []
        )
        paths.append(["Điểm chuẩn trúng tuyển", *parents, label])
    return [[key(h) for h in path] for path in paths]


def cell_reason(f: dict[str, Any], col: int) -> str | None:
    for i in [1, 2, col]:
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
        return "PROGRAM_IDENTITY_REQUIRED"
    n = number(f["cells"][col].get("raw_text") or "")
    if n.status in {"missing", "not_reported", "not_applicable"}:
        return "VALUE_NOT_REPORTED"
    if n.status != "value" or n.operator != "eq" or n.value is None or n.value < 0:
        return "NUMERIC_VALUE_REQUIRED"
    return None


def tie_evidence(slot: dict[str, Any]) -> dict[str, Any]:
    raw = slot.get("raw_text")
    match = re.search(r"(<=|≤|=|<|>=|≥|>)\s*(\d+(?:[.,]\d+)?)", raw or "")
    return dict(
        raw_text=raw,
        locator=slot.get("origin"),
        span_reference=slot.get("span_reference"),
        operator=match[1] if match else None,
        value=match[2] if match else None,
        status="reported_predicate" if match else "unresolved_or_not_reported",
    )


def parse_ptit_2026(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits,
    version: str = VERSION,
) -> ParseResult:
    result = ParseResult(
        metadata=dict(program_row_ledger=[], method_cell_ledger=[], method_not_offered=[])
    )
    if ref.final_url != URL or profile.university_key != "ptit" or len(data) > limits.max_bytes:
        result.issue("PTIT2026_SOURCE", "document", "Exact official source required")
        return result
    soup = BeautifulSoup(data, "html.parser")
    roots = soup.select("article.post-wrap")
    if len(roots) != 1:
        result.issue("PTIT2026_ROOT", "document", "Unique business article required")
        return result
    root = roots[0]
    titles = [h for h in root.find_all("h1") if key(text(h)) == key(TITLE)]
    dates = [n for n in root.select("ul li span") if text(n) == "10/08/2026"]
    pubs = [
        p
        for p in root.find_all("p")
        if key(text(p)).startswith(
            "hoc vien cong nghe buu chinh vien thong thong bao diem chuan trung tuyen nam 2026 "
        )
    ]
    notes = [
        p
        for p in root.find_all("p")
        if text(p).startswith("(*)")
        and "diem cong" in key(text(p))
        and "nguyen vong" in key(text(p))
    ]
    if len(titles) != 1 or len(dates) != 1 or len(pubs) != 1 or len(notes) != 1:
        result.issue(
            "PTIT2026_CONTEXT", locator(root), "Explicit2026 cutoff/title/date/tie note required"
        )
        return result
    common: dict[str, Any] = dict(
        snapshot_id=str(ref.snapshot_id),
        snapshot_sha256=ref.raw_hash,
        source_url=ref.final_url,
        title=evidence(titles[0]),
        publication=evidence(pubs[0]),
        publication_date=evidence(dates[0]) | dict(value="2026-08-10", precision="date"),
        tie_note=evidence(notes[0]),
    )
    remaining = limits.max_cells
    for table in root.find_all("table"):
        heading = table.find_previous_sibling("ol")
        campus = next(
            (
                c
                for c, region in [("BVH", "bac"), ("BVS", "nam")]
                if heading and key(text(heading)) == f"co so dao tao phia {region} (ma {c.lower()})"
            ),
            None,
        )
        extracted = ParseResult()
        remaining -= table_rows(
            table,
            ref,
            extracted,
            [common["publication"]],
            remaining,
            version,
            header_row_count=3,
            score_columns=frozenset(range(3, 12)),
        )
        result.issues.extend(extracted.issues)
        if any(i.severity == "error" for i in extracted.issues):
            result.observations = []
            for entry in result.metadata["method_cell_ledger"]:
                if entry["status"] == "eligible_source_cell":
                    entry.update(status="blocked_or_needs_review", reason="DOCUMENT_RESOURCE_ERROR")
            return result
        byrow = {o.record_locator: o for o in extracted.observations}
        section = None
        for row in table.find_all("tr")[3:]:
            own = row.find_all(["td", "th"], recursive=False)
            if own and text(own[0]) in {"I", "II", "III", "IV"}:
                section = evidence(row)
                result.metadata["program_row_ledger"].append(
                    dict(
                        row_locator=locator(row),
                        campus=campus,
                        status="not_a_cutoff_value",
                        reason="SECTION_HEADING",
                        section=section,
                    )
                )
                continue
            obs = byrow.get(locator(row))
            if obs is None:
                result.metadata["program_row_ledger"].append(
                    dict(
                        row_locator=locator(row),
                        campus=campus,
                        status="blocked_or_needs_review",
                        reason="PHYSICAL_GRID_UNAVAILABLE",
                    )
                )
                continue
            f = obs.raw_fields
            valid = (
                campus
                and section
                and len(f["headers"]) == len(f["cells"]) == 14
                and [[key(h["text"]) for h in p] for p in f["headers"][:12]] == header_paths()
                and "diem cong" in key(f["headers"][12][-1]["text"])
                and key(f["headers"][13][-1]["text"]) == "ttnv"
            )
            entries = []
            for col, method in enumerate(METHODS, 3):
                slot = f["cells"][col] if col < len(f["cells"]) else {}
                reason = cell_reason(f, col) if valid else "HEADER_CAMPUS_SECTION_REQUIRED"
                status = (
                    "eligible_source_cell"
                    if reason is None
                    else "not_a_cutoff_value"
                    if reason == "VALUE_NOT_REPORTED"
                    else "blocked_or_needs_review"
                )
                entry = dict(
                    row_locator=locator(row),
                    campus=campus,
                    section=section,
                    method=method,
                    column=col,
                    code=f["cells"][2].get("raw_text") if len(f["cells"]) > 2 else None,
                    program=f["cells"][1].get("raw_text") if len(f["cells"]) > 1 else None,
                    score_locator=slot.get("origin"),
                    raw_score=slot.get("raw_text"),
                    status=status,
                    reason=reason,
                )
                entries.append(entry)
            result.metadata["method_cell_ledger"] += entries
            result.metadata["program_row_ledger"].append(
                dict(
                    row_locator=locator(row),
                    campus=campus,
                    section=section,
                    code=entries[0]["code"],
                    program=entries[0]["program"],
                    status="mapped" if valid else "blocked_or_needs_review",
                )
            )
            if not valid:
                result.issue(
                    "PTIT2026_ROW_BINDING",
                    locator(row),
                    "Header/campus/section mismatch, cells retained in ledger",
                )
                continue
            assert heading is not None
            mapping = common | dict(
                campus=campus,
                campus_evidence=evidence(heading),
                section=section,
                table_locator=locator(table),
                cells=entries,
                tie_break=dict(
                    bonus=tie_evidence(f["cells"][12]),
                    TTNV=tie_evidence(f["cells"][13]),
                    note=common["tie_note"],
                    executable=False,
                ),
            )
            result.observations.append(
                obs.model_copy(
                    update=dict(
                        fact_kind="cutoff",
                        issues=[],
                        raw_fields=f
                        | dict(
                            context=[common["publication"], mapping["campus_evidence"], section],
                            footnotes=[common["tie_note"]],
                            ptit_2026=mapping,
                        ),
                    )
                )
            )
    return result
