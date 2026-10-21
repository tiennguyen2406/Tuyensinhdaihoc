"""Explicit source layouts, retaining original DOM cells and unapproved scope."""

import re
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from services.api.source_profiles import SourceProfile
from services.data.normalization.values import text as value_text
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.html import locator, table_rows, text

VERSION = "html-hcm-intake/1.0.0"
OU_2024 = "/thong-bao-diem-chuan-trung-tuyen-phuong-thuc-su-dung-kq-thi-tn-thpt-2024"
OU_2025 = "/thong-bao-diem-chuan-trung-tuyen-dot-1-nam-2025"
OU_2025_R2 = "/diem-chuan-xet-tuyen-dai-hoc-chinh-quy-dot-2-nam-2025"
OU_2026 = "/thong-bao-diem-chuan-trung-tuyen-va-ket-qua-trung-tuyen-vao-dai-hoc-chinh-quy-nam-2026"
UEH_2025 = "/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-khoa-51-dai-hoc-chinh-quy-nam-2025-va-doi-moi-quy-trinh-nhap-hoc-voi-hinh-thuc-truc-tuyen-hoan-toan/"
UEH_2026 = "/bai-viet/ueh-cong-bo-ket-qua-xet-tuyen-khoa-52-dai-hoc-chinh-quy-nam-2026-gia-tang-co-hoi-hoc-tap-quoc-te/"


def key(raw: str) -> str:
    return value_text(raw).search_key


def parse_hcm(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits,
    version: str = VERSION,
) -> ParseResult:
    result = ParseResult()
    url = urlsplit(ref.final_url)
    school = profile.university_key
    article = parse_qs(url.query).get("id", [""])[0].split(":")[0]
    layout = (
        "ou2024"
        if school == "ou" and url.hostname == "tuyensinh.ou.edu.vn" and url.path == OU_2024
        else "ou2026"
        if school == "ou" and url.hostname == "tuyensinh.ou.edu.vn" and url.path == OU_2026
        else "ou2025"
        if school == "ou" and url.hostname == "tuyensinh.ou.edu.vn" and url.path == OU_2025
        else "ou2025r2"
        if school == "ou" and url.hostname == "tuyensinh.ou.edu.vn" and url.path == OU_2025_R2
        else "history"
        if school == "hcmue" and url.hostname == "tuyensinh.hcmue.edu.vn" and article == "27810"
        else "hcmue2026"
        if school == "hcmue" and url.hostname == "tuyensinh.hcmue.edu.vn" and article == "27833"
        else "ueh2025"
        if school == "ueh" and url.hostname == "tuyensinh.ueh.edu.vn" and url.path == UEH_2025
        else "ueh2026"
        if school == "ueh" and url.hostname == "tuyensinh.ueh.edu.vn" and url.path == UEH_2026
        else None
    )
    if layout is None or len(data) > limits.max_bytes:
        result.issue("HCM_SOURCE", "document", "Exact supported first-party source required")
        return result
    soup = BeautifulSoup(data, "html.parser")
    selector = (
        "#component"
        if school == "hcmue"
        else ".elementor-widget-theme-post-content > .elementor-widget-container"
        if school == "ueh"
        else "main"
    )
    roots = soup.select(selector)
    if len(roots) != 1:
        result.issue("HCM_ROOT", "document", "Unique business region required")
        return result
    root = roots[0]
    title_nodes = root.find_all(["h1", "h2"])
    if school == "ueh":
        title_nodes = soup.select(
            ".elementor-widget-theme-post-title h1, .elementor-widget-theme-post-title h2"
        )
    title_node = next(
        (
            n
            for n in title_nodes
            if ("diem" in key(text(n)) or "ket qua xet tuyen" in key(text(n)))
            and (
                "chuan" in key(text(n))
                or "trung tuyen" in key(text(n))
                or "xet tuyen" in key(text(n))
            )
        ),
        None,
    )
    if title_node is None:
        result.issue("HCM_TITLE", "document", "Cutoff publication title required")
        return result
    title_key = key(text(title_node))
    year = (
        2024
        if layout == "ou2024"
        else 2025
        if layout in {"ueh2025", "ou2025", "ou2025r2"}
        else 2026
    )
    if layout != "history" and str(year) not in title_key:
        result.issue("HCM_YEAR", "document", "Year must be explicit in publication title")
        return result
    ctx = [
        {
            "text": text(title_node),
            "raw_text": title_node.get_text(),
            "locator": locator(title_node),
        }
    ]
    remaining = limits.max_cells
    matched = 0
    for table in root.find_all("table"):
        if table.find("table"):
            continue  # HCMUE wraps its actual data table in a layout table.
        rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
        if not rows:
            continue
        head = key(" ".join(text(r) for r in rows[:2]))
        if not re.search(r"ma.*(?:nganh|xet tuyen|tuyen sinh)", head) or "diem" not in head:
            continue
        matched += 1
        headers = 2 if layout == "history" else 1
        scores = (
            {8: (2025, None), 11: (2024, None)}
            if layout == "history"
            else {3: (2026, "THPT"), 4: (2026, "Học tập THPT kết hợp ĐGNLCB")}
            if layout == "hcmue2026"
            else {3: (year, "THPT"), 4: (year, "ĐGNL")}
            if layout in {"ou2026", "ou2025"}
            else {3: (2025, "THPT")}
            if layout == "ou2025r2"
            else {5: (2026, "PT2 tích hợp")}
            if layout == "ueh2026"
            else {4: (2025, "PT2,3,4,5 (source aggregate)")}
            if layout == "ueh2025"
            else {2: (2024, "THPT")}
        )
        code_col, name_col = (0, 1) if layout == "ou2024" else (1, 2)
        if layout == "hcmue2026":
            code_col, name_col = 1, 2  # col0 is the university/campus label, not program code.
        partial = ParseResult()
        consumed = table_rows(
            table,
            ref,
            partial,
            ctx,
            remaining,
            version,
            header_row_count=headers,
            score_columns=frozenset(scores),
        )
        remaining -= consumed
        result.issues.extend(partial.issues)
        valid = bool(partial.observations)
        campus_evidence = None
        if layout in {"ueh2025", "ueh2026"}:
            campus_node = next(
                (
                    n
                    for n in table.find_all_previous(["p", "li", "h2", "h3", "h4"])
                    if n.find_parent("table") is None
                    and re.search(
                        r"ma truong\s*:\s*KS[AV]|^\s*[-–]?\s*ks[av]\s*:", key(text(n)), re.I
                    )
                ),
                None,
            )
            if campus_node is not None:
                campus_evidence = {"text": text(campus_node), "locator": locator(campus_node)}
            if campus_evidence is None:
                result.issue(
                    "HCM_CAMPUS", locator(table), "UEH table requires explicit KSA/KSV heading"
                )
                continue
        method_evidence = None
        if layout == "ueh2026":
            method_node = next(
                (
                    n
                    for n in table.find_all_previous(["p", "h2", "h3", "h4"])
                    if n.find_parent("table") is None
                    and "phuong thuc 2" in key(text(n))
                    and "tich hop" in key(text(n))
                ),
                None,
            )
            if method_node is None:
                result.issue("HCM_METHOD", locator(table), "Integrated method section required")
                continue
            method_evidence = {"text": text(method_node), "locator": locator(method_node)}
        for obs in partial.observations:
            paths = obs.raw_fields["headers"]
            width = (
                12
                if layout == "history"
                else 3
                if layout == "ou2024"
                else 4
                if layout == "ou2025r2"
                else 6
                if layout == "ueh2026"
                else 5
            )
            if (
                len(paths) != width
                or "ma" not in key(" ".join(h["text"] for h in paths[code_col]))
                or not re.search(
                    r"ten|chuong trinh", key(" ".join(h["text"] for h in paths[name_col]))
                )
            ):
                valid = False
                break
            for col, (column_year, _) in scores.items():
                header = key(" ".join(h["text"] for h in paths[col]))
                expected = (
                    "totnghiep"
                    if layout == "hcmue2026" and col == 3
                    else "dgnlcb"
                    if layout == "hcmue2026"
                    else "thpt"
                    if layout in {"ou2026", "ou2025", "ou2025r2"} and col == 3
                    else "dgnl"
                    if layout in {"ou2026", "ou2025"}
                    else "pt2,3,4,5"
                    if layout == "ueh2025"
                    else None
                )
                if (
                    "diem" not in header
                    or layout == "history"
                    and str(column_year) not in header
                    or expected
                    and expected not in header.replace(" ", "")
                ):
                    valid = False
        if not valid:
            result.issue(
                "HCM_HEADERS",
                locator(table),
                "Exact code/name/year/score columns required; table quarantined",
            )
            continue
        for obs in partial.observations:
            fields = obs.raw_fields
            bindings = []
            for col, (column_year, method) in scores.items():
                header_path = fields["headers"][col]
                bindings.append(
                    {
                        "column": col,
                        "year": column_year,
                        "method": method,
                        "header_path": header_path,
                    }
                )
            mapping = {
                "layout": layout,
                "school": school,
                "source_url": ref.final_url,
                "snapshot_id": str(ref.snapshot_id),
                "table_locator": locator(table),
                "code_column": code_col,
                "name_column": name_col,
                "bindings": bindings,
                "title_evidence": ctx[0],
                "campus_evidence": campus_evidence,
                "method_evidence": method_evidence,
            }
            fields = fields | {"hcm_intake": mapping}
            result.observations.append(obs.model_copy(update={"raw_fields": fields}))
        if remaining <= 0:
            result.issue("HCM_LIMIT", locator(table), "Cell budget exhausted", "error")
            break
    if not matched:
        result.issue("HCM_TABLE_MISSING", "document", "Expected cutoff data table missing")
    if any(i.severity == "error" for i in result.issues):
        result.observations = []
    return result
