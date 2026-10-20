"""One August UEH PT6 appendix adapter, sharing the existing physical-cell grid."""

import hashlib
import json
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from services.api.source_profiles import SourceProfile
from services.data.normalization.values import number
from services.data.parsers.common import folded
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locator, table_rows, text
from services.data.parsers.ueh import URL, evidence

VERSION = "html-ueh-2024-pt6-batch/1.0.0"
GROUPS = {"ksa_main": "KSA", "ksa_isb": "KSA", "ksv": "KSV"}


def key(value: str) -> str:
    return " ".join(folded(value).split())


def columns(group: str) -> tuple[int, int]:
    return (6, 7) if group == "ksa_isb" else (7, 8)


def header_paths(group: str) -> list[list[str]]:
    methods = ["pt3", "pt4"] + ([] if group == "ksa_isb" else ["pt5"])
    paths = [
        [h]
        for h in (
            "stt",
            "ma dkxt" if group == "ksa_isb" else "ma dang ky xet tuyen",
            "chuong trinh dao tao",
            "tong chi tieu",
        )
    ]
    paths += [[m, "diem trung tuyen"] for m in methods]
    paths += [["pt6", "to hop xet tuyen"], ["pt6", "diem trung tuyen"]]
    if group != "ksa_isb":
        paths += [
            ["chuong trinh hoc", h]
            for h in (
                "tieng anh toan phan",
                "tieng anh ban phan",
                "chuong trinh tieng viet" if group == "ksv" else "tieng viet",
            )
        ]
    return paths


def logical_id(ref: SnapshotRef, cell: str, code: str, campus: str, notice: str) -> str:
    """Reporting identity only; independent of parser namespace, never canonical identity."""
    payload = [
        "ueh:physical-pt6/1",
        str(ref.snapshot_id),
        ref.raw_hash,
        cell,
        code,
        campus,
        2024,
        "UEH PT6",
        notice,
    ]
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def parse_batch(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits,
    version: str = VERSION,
) -> ParseResult:
    result = ParseResult(metadata={"row_ledger": [], "groups": {}})
    if ref.final_url != URL or profile.university_key != "ueh" or len(data) > limits.max_bytes:
        result.issue("UEH_BATCH_SOURCE", "document", "Exact August source required")
        return result
    soup = BeautifulSoup(data, "html.parser")
    roots = soup.select(".elementor-widget-theme-post-content > .elementor-widget-container")
    dates = soup.select('.elementor-widget-post-info [itemprop="datePublished"] time')
    if len(roots) != 1 or len(dates) != 1 or text(dates[0]) != "17/08/2024":
        result.issue(
            "UEH_BATCH_CONTEXT", "document", "Unique article and August notice date required"
        )
        return result
    root = roots[0]
    patterns = {
        "publication": r"^hoi dong tuyen sinh .*\(ueh\) cong bo ket qua trung tuyen .*dai hoc chinh quy, nam 2024 cua cac phuong thuc:",
        "method": r"^– phuong thuc 6 \(pt6\): .*ket qua thi tot nghiep thpt nam 2024\.$",
        "cutoff": r"^2\. diem trung tuyen$",
        "combination_applicability": r"^– phuong thuc .*nam 2024 \(pt6\): diem trung tuyen .*bang nhau giua cac to hop xet tuyen va bang nhau giua cac nguyen vong\.$",
    }
    common = {}
    for name, pattern in patterns.items():
        found = [p for p in root.find_all("p", recursive=False) if re.search(pattern, key(text(p)))]
        if len(found) != 1:
            result.issue("UEH_BATCH_CONTEXT", locator(root), f"Unique explicit {name} required")
            return result
        common[name] = evidence(found[0])
    shared = {
        "snapshot_id": str(ref.snapshot_id),
        "snapshot_sha256": ref.raw_hash,
        "source_url": ref.final_url,
        "publication_date": {"value": "2024-08-17", **evidence(dates[0])},
        **common,
    }
    remaining = limits.max_cells
    for group, campus in GROUPS.items():
        campus_pattern = (
            r"^2\.1\. dao tao tai tp\. ho chi minh \(ma truong ksa\):$"
            if campus == "KSA"
            else r"^2\.2\. dao tao tai vinh long \(ma truong ksv\):$"
        )
        heads = [
            p
            for p in root.find_all("p", recursive=False)
            if re.fullmatch(campus_pattern, key(text(p)))
        ]
        section_pattern = (
            r"^1\. chuong trinh tieng viet, chuong trinh tieng anh toan phan, tieng anh ban phan$"
            if group == "ksa_main"
            else r"^chuong trinh cu nhan tai nang, asean co-op$"
        )
        anchors = (
            heads
            if group == "ksv"
            else [
                p
                for p in root.find_all("p" if group == "ksa_main" else "ol", recursive=False)
                if re.fullmatch(section_pattern, key(text(p)))
            ]
        )
        table = anchors[0].find_next_sibling() if len(anchors) == 1 else None
        if (
            len(heads) != 1
            or not isinstance(table, Tag)
            or table.name != "table"
            or heads[0] not in list(table.previous_siblings)
        ):
            result.issue(
                "UEH_BATCH_TABLE_BLOCKED", locator(root), f"Missing unique {group} section/table"
            )
            result.metadata["groups"][group] = {"blocked": "SECTION_TABLE_MISSING"}
            continue
        # KSA tables must precede the KSV boundary, never inherit it retroactively.
        if campus == "KSA" and any(
            re.fullmatch(r"2\.2\. dao tao tai vinh long \(ma truong ksv\):", key(text(p)))
            for p in table.previous_siblings
            if isinstance(p, Tag) and p.name == "p"
        ):
            result.issue(
                "UEH_BATCH_TABLE_BLOCKED", locator(table), "KSA table crosses KSV boundary"
            )
            continue
        local = ParseResult()
        ctx = [common[k] for k in patterns] + [evidence(heads[0])]
        consumed = table_rows(table, ref, local, ctx, remaining, version, header_row_count=2)
        remaining -= consumed
        rows = [r for r in table.find_all("tr") if r.find_parent("table") is table][2:]
        byrow = {o.record_locator: o for o in local.observations}
        layout_bad = (
            not local.observations
            or any(
                i.severity == "error"
                or i.code in {"invalid_span", "overlapping_spans", "nested_table"}
                for i in local.issues
            )
            or any(
                [[key(h["text"]) for h in p] for p in o.raw_fields["headers"]]
                != header_paths(group)
                for o in local.observations
            )
        )
        combo_col, score_col = columns(group)
        note_node = table.find_next_sibling()
        section_note = (
            evidence(note_node)
            if group != "ksa_isb"
            and isinstance(note_node, Tag)
            and note_node.name == "p"
            and re.match(r"^chuong trinh dao tao \(\s*\*\s*\):", key(text(note_node)))
            else None
        )
        factor_two = bool(
            section_note
            and re.search(r"thi tot nghiep thpt nam 2024", key(section_note["text"]))
            and re.search(r"nhan he so 2\b", key(section_note["text"]))
            and re.search(r"(?:quy ve|quy doi ve) thang diem 30\b", key(section_note["text"]))
        )
        info: dict[str, Any] = {
            "campus": campus,
            "table_locator": locator(table),
            "heading": evidence(anchors[0]),
            "campus_evidence": evidence(heads[0]),
            "header_rows": 2,
            "physical_data_rows": len(rows),
            "combination_column": combo_col,
            "score_column": score_col,
            "section_note": section_note,
            "diagnostics": [i.model_dump() for i in local.issues],
        }
        result.metadata["groups"][group] = info
        if layout_bad:
            result.issue(
                "UEH_BATCH_TABLE_BLOCKED",
                locator(table),
                f"Unsupported {group} physical/header grid",
            )
        else:
            result.issues.extend(local.issues)
        for row in rows:
            loc = locator(row)
            own = row.find_all(["td", "th"], recursive=False)
            total = len(own) > 2 and not text(own[1]) and key(text(own[2])) == "cong:"
            empty = not text(row)
            group_row = len(own) == 1 and bool(re.fullmatch(r"[IVX]+", text(own[0])))
            entry: dict[str, Any] = {
                "group": group,
                "campus": campus,
                "row_locator": loc,
                "status": "non_cutoff_row"
                if total or empty or group_row
                else "needs_review_or_blocked",
                "reason": "TOTAL_ROW"
                if total
                else "EMPTY_ROW"
                if empty
                else "GROUP_ROW"
                if group_row
                else "TABLE_LAYOUT"
                if layout_bad
                else "PHYSICAL_ROW_MISSING",
            }
            if entry["status"] == "non_cutoff_row":
                result.metadata["row_ledger"].append(entry)
                continue
            obs = byrow.get(loc)
            if layout_bad or obs is None:
                result.metadata["row_ledger"].append(entry)
                continue
            fields = obs.raw_fields
            cells = fields["cells"]
            code = cells[1].get("text") or ""
            name = cells[2].get("text") or ""
            score = cells[score_col]
            numeric = number(score.get("raw_text") or "")
            physical = all(
                not cells[col]["span_reference"]
                and cells[col]["origin"]
                and fields["origin_cells"][cells[col]["origin"]]["rowspan"]
                == fields["origin_cells"][cells[col]["origin"]]["colspan"]
                == 1
                for col in (1, 2, combo_col, score_col)
            )
            reason = (
                "PHYSICAL_CELL_REQUIRED"
                if not physical
                else "PROGRAM_CODE_NAME_REQUIRED"
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", code) or not name
                else "PT6_SCORE_NOT_VALUE"
                if numeric.status != "value"
                or numeric.operator != "eq"
                or numeric.value is None
                or numeric.value < 0
                else None
            )
            entry.update(
                code=code,
                name=name,
                score_locator=score.get("origin"),
                raw_score=score.get("raw_text"),
                reason=reason,
            )
            entry["status"] = "needs_review_or_blocked" if reason else "eligible_source_row"
            mapping = shared | {
                "group": group,
                "campus": campus,
                "campus_evidence": evidence(heads[0]),
                "section": evidence(anchors[0]),
                "table_locator": locator(table),
                "section_note": section_note,
                "weighting": {
                    "factor": "2" if factor_two else None,
                    "subject": None,
                    "formula": None,
                    "note": section_note,
                }
                if "(*)" in name and section_note
                else None,
                "row_blocker": reason,
            }
            if score.get("origin"):
                mapping["logical_id"] = logical_id(ref, score["origin"], code, campus, "2024-08-17")
                entry["logical_id"] = mapping["logical_id"]
            result.observations.append(
                obs.model_copy(
                    update={
                        "fact_kind": "cutoff",
                        "raw_fields": fields
                        | {
                            "ueh_batch_2024": mapping,
                            "footnotes": [section_note] if mapping["weighting"] else [],
                        },
                    }
                )
            )
            result.metadata["row_ledger"].append(entry)
    # Retain an explicit disposition if a PT6 table loses its section anchor.
    # Its layout alone can identify review work, never campus/year facts.
    accounted = {r["row_locator"] for r in result.metadata["row_ledger"]}
    for table in root.find_all("table", recursive=False):
        rows = table.find_all("tr")
        if len(rows) < 2 or not re.search(r"\bpt6\b", key(text(rows[0]))):
            continue
        for row in rows[2:]:
            loc = locator(row)
            if loc in accounted:
                continue
            own = row.find_all(["td", "th"], recursive=False)
            total = len(own) > 2 and not text(own[1]) and key(text(own[2])) == "cong:"
            result.metadata["row_ledger"].append(
                {
                    "group": "unmapped",
                    "campus": None,
                    "row_locator": loc,
                    "status": "non_cutoff_row" if total else "needs_review_or_blocked",
                    "reason": "TOTAL_ROW" if total else "SECTION_TABLE_MISSING",
                }
            )
    return result
