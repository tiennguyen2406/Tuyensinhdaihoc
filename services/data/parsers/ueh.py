"""Narrow UEH 2024 fallback adapter. Original DOM/cells; no additional-round inference."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from services.api.source_profiles import SourceProfile
from services.data.parsers.common import folded
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locator, table_rows, text

VERSION = "html-ueh-2024/1.0.0"
URL = "https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/"
PILOT_CODES = {"7220201", "7340201_03", "7480201", "7480107", "7620114", "7810201"}


def evidence(node: Tag) -> dict[str, str]:
    return {"text": text(node), "raw_text": node.get_text(), "locator": locator(node)}


def parse_ueh(
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
            "ueh_source_mismatch", "document", "Only the bounded UEH fallback is supported"
        )
        return result
    soup = BeautifulSoup(data, "html.parser")
    roots = soup.select(".elementor-widget-theme-post-content > .elementor-widget-container")
    if len(roots) != 1:
        result.issue("ueh_business_region_missing", "document", "Unique UEH article required")
        return result
    root = roots[0]
    # These are explicit local source statements, never the URL/date or narrative score ranges.
    patterns = {
        "publication": r"^hoi dong tuyen sinh .*\(ueh\) cong bo ket qua trung tuyen .*dai hoc chinh quy, nam 2024",
        "method": r"^– phuong thuc 6 \(pt6\): .*ket qua thi tot nghiep thpt nam 2024\.$",
        "cutoff": r"^2\. diem trung tuyen$",
        "campus": r"^2\.2\. dao tao tai vinh long \(ma truong ksv\):$",
        "combination_applicability": r"^– phuong thuc .*nam 2024 \(pt6\): diem trung tuyen .*bang nhau giua cac to hop xet tuyen va bang nhau giua cac nguyen vong\.$",
    }
    nodes: dict[str, Tag] = {}
    for key, pattern in patterns.items():
        matches = [
            p for p in root.find_all("p", recursive=False) if re.search(pattern, folded(text(p)))
        ]
        if len(matches) != 1:
            result.issue(
                "ueh_context_missing", locator(root), f"Unique explicit {key} evidence required"
            )
            return result
        nodes[key] = matches[0]
    table = nodes["campus"].find_next_sibling()
    if not isinstance(table, Tag) or table.name != "table":
        result.issue(
            "ueh_table_missing", locator(nodes["campus"]), "KSV table must follow its section"
        )
        return result
    preceding = list(table.previous_siblings)
    if any(node not in preceding for node in nodes.values()):
        result.issue("ueh_context_order", locator(table), "Context must precede the KSV table")
        return result
    # Explicit two-row TD/strong header in this source. Do not rewrite DOM into a synthetic THEAD.
    headers = table.find_all("tr")[:2]
    if len(headers) != 2 or not all(
        row.find_all(["td", "th"])
        and all(c.find(["strong", "b"]) for c in row.find_all(["td", "th"]))
        for row in headers
    ):
        result.issue("ueh_header_layout", locator(table), "Expected two physical bold header rows")
        return result
    ctx = [evidence(nodes[k]) for k in patterns]
    table_rows(table, ref, result, ctx, limits.max_cells, version, header_row_count=2)
    notes = []
    for node in table.next_siblings:
        if isinstance(node, Tag):
            if node.name != "p" or not folded(text(node)).startswith("chuong trinh dao tao (*)"):
                break
            notes.append(evidence(node))
    scale = next((n for n in notes if "quy ve thang diem 30" in folded(n["text"])), None)
    mapping: dict[str, Any] = {
        "snapshot_id": str(ref.snapshot_id),
        "snapshot_sha256": ref.raw_hash,
        "source_url": ref.final_url,
        "table_locator": locator(table),
        **{k: evidence(v) for k, v in nodes.items()},
        "round": {
            "value": None,
            "evidence": evidence(nodes["publication"]),
            "reason": "Fallback publication; no additional round or ordinal assigned",
        },
        "population": None,
        "conditions": None,
        "scale": scale,
        "weighted_subjects": None,
        "weighted_formula": None,
    }
    selected = []
    for obs in result.observations:
        fields = obs.raw_fields
        cells = fields["cells"]
        if len(cells) <= 8 or cells[1].get("text") not in PILOT_CODES:
            continue
        fields = fields | {"footnotes": notes, "ueh_2024": mapping}
        selected.append(obs.model_copy(update={"raw_fields": fields}))
    result.observations = selected
    result.metadata = {
        "business_root": locator(root),
        "table_locator": locator(table),
        "selected_rows": len(selected),
        "pilot_codes": sorted(PILOT_CODES),
    }
    return result
