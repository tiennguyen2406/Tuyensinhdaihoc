"""UEH early-method cells using the frozen August table/grid adapter unchanged."""

import hashlib
import json
import re
from typing import Any

from bs4 import BeautifulSoup

from services.api.source_profiles import SourceProfile
from services.data.normalization.values import number
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locate, text
from services.data.parsers.ueh import evidence
from services.data.parsers.ueh_batch import key, parse_batch

VERSION = "html-ueh-2024-pt345/1.0.0"
METHODS = {
    "PT3": "UEH PT3 — Xét tuyển học sinh Giỏi",
    "PT4": "UEH PT4 — Xét tuyển quá trình học tập theo tổ hợp môn",
    "PT5": "UEH PT5 — ĐGNL ĐHQG TP.HCM đợt 1 năm 2024",
}
DEFINITIONS = {
    "PT3": "phuong thuc xet tuyen hoc sinh gioi.",
    "PT4": "phuong thuc xet tuyen qua trinh hoc tap theo to hop mon.",
    "PT5": "phuong thuc xet tuyen dua vao ket qua thi danh gia nang luc cua dai hoc quoc gia tp.hcm to chuc dot 1 nam 2024.",
}


def method_columns(group: str) -> dict[str, int]:
    return {"PT3": 4, "PT4": 5} | ({} if group == "ksa_isb" else {"PT5": 6})


def logical_id(ref: SnapshotRef, cell: str, code: str, campus: str, method: str) -> str:
    value = [
        "ueh:physical-method/1",
        str(ref.snapshot_id),
        ref.raw_hash,
        cell,
        code,
        campus,
        2024,
        method,
        "early-admission-2024-republished-2024-08-17",
    ]
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


def cell_reason(fields: dict[str, Any], col: int) -> str | None:
    cells = fields["cells"]
    for index in [1, 2, col]:
        slot = cells[index]
        origin = fields["origin_cells"].get(slot.get("origin"), {})
        if (
            slot.get("span_reference")
            or slot.get("column") != index
            or origin.get("column") != index
            or origin.get("row")
            != fields["origin_cells"].get(cells[1].get("origin"), {}).get("row")
            or origin.get("rowspan") != 1
            or origin.get("colspan") != 1
            or origin.get("raw_text") != slot.get("raw_text")
        ):
            return "PHYSICAL_CELL_REQUIRED"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", cells[1].get("text") or "") or not cells[
        2
    ].get("raw_text"):
        return "PROGRAM_CODE_NAME_REQUIRED"
    value = number(cells[col].get("raw_text") or "")
    if value.status != "value" or value.operator != "eq" or value.value is None or value.value < 0:
        return "SCORE_NOT_VALUE"
    return None


def parse_pt345(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits,
    version: str = VERSION,
) -> ParseResult:
    # Reuse source/date/section/full-header and physical-origin validation. Nothing
    # is persisted from this internal PT6-shaped result; old adapter is immutable.
    base = parse_batch(ref, profile, data, limits=limits, version=version)
    result = ParseResult(
        metadata={
            "method_cell_ledger": [],
            "method_not_offered": [],
            "groups": {
                g: {
                    k: v
                    for k, v in info.items()
                    if k
                    in {
                        "campus",
                        "table_locator",
                        "heading",
                        "campus_evidence",
                        "header_rows",
                        "physical_data_rows",
                        "blocked",
                    }
                }
                | {"method_columns": method_columns(g)}
                for g, info in base.metadata["groups"].items()
            },
            "non_cutoff_rows": [],
        }
    )
    soup = BeautifulSoup(data, "html.parser")
    roots = soup.select(".elementor-widget-theme-post-content > .elementor-widget-container")
    if len(roots) != 1 or not base.metadata["row_ledger"]:
        result.issues = base.issues
        return result
    paragraphs = roots[0].find_all("p", recursive=False)
    definitions = {}
    for method, expected in DEFINITIONS.items():
        matches = [
            p
            for p in paragraphs
            if key(text(p)) == f"– phuong thuc {method[-1]} ({method.lower()}): {expected}"
        ]
        if len(matches) == 1:
            definitions[method] = evidence(matches[0])
    earlier = [
        p
        for p in paragraphs
        if key(text(p)).startswith("– cac phuong thuc xet tuyen som (")
        and "20/6/2024" in text(p)
        and "09/7/2024" in text(p)
    ]
    early = evidence(earlier[0]) if len(earlier) == 1 else None
    byrow = {o.record_locator: o for o in base.observations}
    for row in base.metadata["row_ledger"]:
        if row["status"] == "non_cutoff_row":
            result.metadata["non_cutoff_rows"].append(row)
            continue
        group = row["group"]
        if group == "unmapped":
            result.issue(
                "UEH_PT345_SECTION", row["row_locator"], "Unmapped table retained for review"
            )
        obs = byrow.get(row["row_locator"])
        fields = obs.raw_fields if obs else None
        mappings = []
        selected_columns = method_columns(group)
        if group == "unmapped":
            node = locate(soup, row["row_locator"])
            table = node.find_parent("table") if node else None
            heading = " ".join(text(tr) for tr in table.find_all("tr")[:2]) if table else ""
            selected_columns = {
                m: col
                for m, col in selected_columns.items()
                if re.search(r"\b" + m + r"\b", heading)
            }
        for method, col in selected_columns.items():
            slot = fields["cells"][col] if fields else {}
            reason = (
                "TABLE_LAYOUT"
                if fields is None
                else "METHOD_CONTEXT_REQUIRED"
                if method not in definitions or early is None
                else cell_reason(fields, col)
            )
            entry = {
                "group": group,
                "campus": row.get("campus"),
                "row_locator": row["row_locator"],
                "method": method,
                "column": col,
                "code": fields["cells"][1].get("text") if fields else None,
                "program": fields["cells"][2].get("raw_text") if fields else None,
                "score_locator": slot.get("origin"),
                "raw_score": slot.get("raw_text"),
                "reason": reason,
                "status": "eligible_source_cell" if reason is None else "blocked_or_needs_review",
            }
            if fields:
                entry["logical_id"] = logical_id(
                    ref,
                    slot.get("origin") or row["row_locator"],
                    entry["code"] or "",
                    row.get("campus") or "",
                    method,
                )
            result.metadata["method_cell_ledger"].append(entry)
            mappings.append(entry)
        if group == "ksa_isb":
            result.metadata["method_not_offered"].append(
                {"row_locator": row["row_locator"], "method": "PT5", "status": "method_not_offered"}
            )
        if obs is None:
            continue
        assert fields is not None
        original = fields["ueh_batch_2024"]
        mapping = {
            k: original[k]
            for k in [
                "snapshot_id",
                "snapshot_sha256",
                "source_url",
                "publication_date",
                "publication",
                "cutoff",
                "group",
                "campus",
                "campus_evidence",
                "section",
                "table_locator",
            ]
        }
        mapping.update(
            method_definitions=definitions, early_admission_context=early, cells=mappings
        )
        context = (
            [mapping["publication"], mapping["cutoff"], mapping["campus_evidence"]]
            + list(definitions.values())
            + ([early] if early else [])
        )
        clean = {
            k: v for k, v in fields.items() if k not in {"ueh_batch_2024", "footnotes", "context"}
        }
        result.observations.append(
            obs.model_copy(
                update={
                    "issues": [],
                    "raw_fields": clean
                    | {"context": context, "footnotes": [], "ueh_pt345_2024": mapping},
                }
            )
        )
    return result
