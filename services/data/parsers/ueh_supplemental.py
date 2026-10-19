"""Exact UEH supplemental announcement; physical PT6 rows and unexecuted source evidence."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from services.api.source_profiles import SourceProfile
from services.data.parsers.common import folded
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locator, table_rows, text
from services.data.parsers.ueh import PILOT_CODES, evidence

VERSION = "html-ueh-supplemental-2024/1.0.0"
URL = "https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-trung-tuyen-dot-xet-tuyen-bo-sung-khoa-50-dai-hoc-chinh-quy-tai-phan-hieu-vinh-long-ma-truong-ksv/"
HEADERS = ["stt", "ma dkxt", "chuong trinh dao tao", "to hop xet tuyen", "pt4", "pt6"]


def source_key(value: str) -> str:
    return " ".join(folded(value).split())


def parse_supplemental(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits,
    version: str = VERSION,
) -> ParseResult:
    result = ParseResult()
    if ref.final_url != URL or profile.university_key != "ueh" or len(data) > limits.max_bytes:
        result.issue(
            "ueh_supplemental_source_mismatch", "document", "Exact supplemental source required"
        )
        return result
    soup = BeautifulSoup(data, "html.parser")
    roots = soup.select(".elementor-widget-theme-post-content > .elementor-widget-container")
    titles = soup.select(".elementor-widget-theme-post-title h2")
    dates = soup.select('.elementor-widget-post-info [itemprop="datePublished"] time')
    if (
        len(roots) != 1
        or len(titles) != 1
        or len(dates) != 1
        or text(dates[0]) != "30/09/2024"
        or not re.fullmatch(
            r"ueh cong bo diem trung tuyen dot xet tuyen bo sung khoa 50 .*tai phan hieu vinh long \(ma truong ksv\)",
            source_key(text(titles[0])),
        )
    ):
        result.issue(
            "ueh_supplemental_article_context", "document", "Unique title/date/KSV article required"
        )
        return result
    root = roots[0]
    patterns = {
        "publication": r"^hoi dong tuyen sinh .*\(ueh\) cong bo ket qua trung tuyen .*dai hoc chinh quy, nam 2024 dot xet tuyen bo sung",
        "method": r"^– phuong thuc xet tuyen dua vao ket qua thi tot nghiep thpt nam 2024 \(pt6\)\.$",
        "cutoff": r"^2\. diem trung tuyen$",
        "combination_applicability": r"^– diem chuan trung tuyen cua tung chuong trinh bang nhau giua cac to hop xet tuyen va bang nhau giua cac nguyen vong\.$",
        "math_note": r"^\(\*\): toan nhan he so 2 .*pt6 .*2024.*quy ve thang diem 30\.$",
        "english_note": r"^\(\*\*\): tieng anh he so 2 .*pt6 .*2024.*quy ve thang diem 30\.$",
        "dual_program_note": r"^\(s\) chuong trinh song nganh tich hop:",
        "general_formula": r"^diem xet tuyen = tong diem 3 mon theo to hop xet tuyen",
        "scoring_section": r"^3\.1\.2\. phuong thuc xet diem thi thpt\.$",
        "english_formula": r"^diem xet tuyen chuong trinh tieng anh thuong mai =",
        "math_formula": r"^diem xet tuyen chuong trinh cong nghe doi moi sang tao =",
        "method_preference": r"^– truong hop thi sinh trung tuyen 01 .*02 phuong thuc,",
        "eligibility": r"^– thi sinh trung tuyen khi thoa ca hai dieu kien sau:",
        "priority": r"^3\.2\.1\.2 muc diem uu tien .*thang diem 30 \(pt6\)$",
        "priority_end": r"^4\. huong dan xac nhan nhap hoc$",
    }
    nodes: dict[str, Tag] = {}
    for key, pattern in patterns.items():
        matches = [
            p
            for p in root.find_all("p", recursive=False)
            if re.search(pattern, source_key(text(p)))
        ]
        if len(matches) != 1:
            result.issue(
                "ueh_supplemental_evidence_missing",
                locator(root),
                f"Unique {key} evidence required",
            )
            return result
        nodes[key] = matches[0]
    table = nodes["combination_applicability"].find_next_sibling()
    if not isinstance(table, Tag) or table.name != "table":
        result.issue(
            "ueh_supplemental_table_missing",
            locator(root),
            "Table must follow cutoff applicability",
        )
        return result
    preceding = list(table.previous_siblings)
    if any(nodes[k] not in preceding for k in ("publication", "method", "cutoff")):
        result.issue(
            "ueh_supplemental_context_order", locator(table), "Scope must precede the table"
        )
        return result
    first = table.find("tr")
    if (
        first is None
        or [source_key(text(c)) for c in first.find_all(["th", "td"], recursive=False)] != HEADERS
    ):
        result.issue(
            "ueh_supplemental_headers", locator(table), "Exact six-column PT4/PT6 header required"
        )
        return result
    following = list(table.next_siblings)
    if any(nodes[k] not in following for k in ("math_note", "english_note", "dual_program_note")):
        result.issue(
            "ueh_supplemental_note_order", locator(table), "Footnotes must follow the same table"
        )
        return result
    blocks = {}
    for key in ("method_preference", "eligibility"):
        node = nodes[key].find_next_sibling()
        if not isinstance(node, Tag) or node.name != "ul":
            result.issue(
                "ueh_supplemental_conditions_missing",
                locator(nodes[key]),
                "Adjacent condition list required",
            )
            return result
        blocks[key] = [evidence(nodes[key]), evidence(node)]
    priority = [evidence(nodes["priority"])]
    if nodes["priority_end"] not in list(nodes["priority"].next_siblings):
        result.issue(
            "ueh_supplemental_priority_order", locator(root), "PT6 priority boundary required"
        )
        return result
    for item in nodes["priority"].next_siblings:
        if not isinstance(item, Tag):
            continue
        if item is nodes["priority_end"]:
            break
        if item.name in ("p", "table"):
            priority.append(evidence(item))
    ctx = [
        evidence(nodes[k]) for k in ("publication", "method", "cutoff", "combination_applicability")
    ]
    table_rows(table, ref, result, ctx, limits.max_cells, version, score_columns=frozenset({5}))
    if any(i.severity == "error" for i in result.issues):
        result.observations = []
        return result
    common: dict[str, Any] = {
        "snapshot_id": str(ref.snapshot_id),
        "snapshot_sha256": ref.raw_hash,
        "source_url": ref.final_url,
        "table_locator": locator(table),
        **{
            k: evidence(nodes[k])
            for k in ("publication", "method", "cutoff", "combination_applicability")
        },
        "campus": evidence(titles[0]),
        "publication_date": {"value": "2024-09-30", **evidence(dates[0])},
        "round": {
            "proposed_key": "ueh:ksv:2024:supplemental:notice-20240930",
            "ordinal": None,
            "approved": False,
            "evidence": evidence(nodes["publication"]),
        },
        "priority": {"pt6": priority},
        **blocks,
        "general_formula": evidence(nodes["general_formula"]),
        "scoring_section": evidence(nodes["scoring_section"]),
    }
    selected = []
    for obs in result.observations:
        fields = obs.raw_fields
        if len(fields["headers"]) != 6 or [
            [source_key(h["text"]) for h in p] for p in fields["headers"]
        ] != [[h] for h in HEADERS]:
            result.issue(
                "ueh_supplemental_grid_mismatch",
                locator(table),
                "Expanded grid changed; no positional mapping",
            )
            result.observations = []
            return result
        if fields["cells"][1].get("text") not in PILOT_CODES:
            continue
        label = fields["cells"][2].get("text") or ""
        markers = re.findall(r"\(\*\*?\)|\(S\)", label)
        if "(*)" in markers and "(**)" in markers:
            result.issue(
                "ueh_supplemental_weight_marker_conflict",
                obs.record_locator,
                "Conflicting weighting markers require source review",
            )
            result.observations = []
            return result
        weight = None
        notes = []
        expected_weight = {
            "7220201": ("(**)", "tieng anh thuong mai", "english"),
            "7480201": ("(*)", "cong nghe va doi moi sang tao", "math"),
        }.get(fields["cells"][1].get("text"))
        weight_markers = [m for m in markers if m in ("(*)", "(**)")]
        base_name = source_key(re.sub(r"\(\*\*?\)|\(S\)", "", label))
        if (
            expected_weight
            and (weight_markers != [expected_weight[0]] or base_name != expected_weight[1])
        ) or (not expected_weight and weight_markers):
            result.issue(
                "ueh_supplemental_formula_program_mismatch",
                obs.record_locator,
                "Named formula requires the source-specific program code, name and marker",
            )
            result.observations = []
            return result
        if "(*)" in markers or "(**)" in markers:
            marker = "(**)" if "(**)" in markers else "(*)"
            key = "english" if marker == "(**)" else "math"
            note = evidence(nodes[key + "_note"])
            weight = {
                "marker": marker,
                "subject": "Tiếng Anh" if key == "english" else "Toán",
                "factor": "2",
                "note": note,
                "formula": evidence(nodes[key + "_formula"]),
                "normalization_scale_evidence": note,
            }
            notes.append(note)
        if "(S)" in markers:
            notes.append(evidence(nodes["dual_program_note"]))
        selected.append(
            obs.model_copy(
                update={
                    "raw_fields": fields
                    | {
                        "footnotes": notes,
                        "ueh_supplemental_2024": common
                        | {"program_markers": markers, "weighting": weight},
                    }
                }
            )
        )
    result.observations = selected
    result.metadata = {
        "business_root": locator(root),
        "table_locator": locator(table),
        "selected_rows": len(selected),
    }
    return result
