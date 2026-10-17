"""Digital PDF extraction only. Scans yield OCR issues; no image-to-fact path exists."""

import re
from io import BytesIO
from typing import Any

import pdfplumber

from services.api.source_profiles import SourceProfile
from services.data.parsers.common import classify, folded, observation, relevant
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef

VERSION = "pdf/1.0.0"


def bbox_list(box: Any) -> list[float]:
    return [float(v) for v in box]


def parse_pdf(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits | None = None,
    version: str = VERSION,
) -> ParseResult:
    limits = limits or ParseLimits()
    result = ParseResult()
    if len(data) > limits.max_bytes or not data.lstrip().startswith(b"%PDF-"):
        result.issue("pdf_body_or_signature", "document", "Invalid/oversized PDF", "error")
        return result
    used = 0
    previous = None
    repeated: dict[str, int] = {}
    try:
        with pdfplumber.open(BytesIO(data), unicode_norm=None) as pdf:
            if len(pdf.pages) > limits.max_pages:
                result.issue("pdf_page_limit", "document", "PDF exceeds page budget", "error")
                return result
            result.metadata = {"pages": len(pdf.pages), "page_char_counts": [], "scanned_pages": []}
            for page in pdf.pages:
                page_no = page.page_number
                ploc = f"pdf:p{page_no}"
                result.metadata["page_char_counts"].append(len(page.chars))
                image_area = sum(
                    max(0, img["x1"] - img["x0"]) * max(0, img["bottom"] - img["top"])
                    for img in page.images
                )
                if (
                    not page.chars
                    or len(page.chars) < 40
                    and image_area > page.width * page.height * 0.5
                ):
                    code = "ocr_required" if page.images else "empty_pdf_page"
                    result.issue(
                        code,
                        ploc,
                        "No usable digital text; requires OCR/manual review; no facts emitted",
                    )
                    if page.images:
                        result.metadata["scanned_pages"].append(page_no)
                    previous = None
                    continue
                page_text = page.extract_text() or ""
                if "(cid:" in page_text or "\ufffd" in page_text:
                    result.issue(
                        "pdf_font_mapping", ploc, "Unreliable font mapping requires review"
                    )
                lines = page.extract_text_lines(return_chars=False)
                tables = page.find_tables()
                table_boxes = [t.bbox for t in tables]
                for index, table in enumerate(tables):
                    tloc = f"{ploc}:table{index}"
                    values = table.extract(x_tolerance=2, y_tolerance=3)
                    if not values:
                        continue
                    width = max(map(len, values), default=0)
                    used += width * len(values)
                    if used > limits.max_cells:
                        result.issue("table_cell_limit", tloc, "PDF cell budget exceeded", "error")
                        result.observations = []
                        return result
                    header_count = 1
                    # Additional explicit label rows only; otherwise keep ambiguous data untouched.
                    while header_count < min(5, len(values)):
                        words = " ".join(c or "" for c in values[header_count])
                        candidate = values[header_count]
                        year_row = bool(
                            candidate
                            and not (candidate[0] or "").strip()
                            and any(re.fullmatch(r"20\d{2}", (v or "").strip()) for v in candidate)
                            and all(not v or re.fullmatch(r"20\d{2}", v.strip()) for v in candidate)
                        )
                        if year_row:
                            header_count += 1
                            result.issue(
                                "pdf_year_header_inferred",
                                tloc,
                                "Year-only label row retained in header paths; verify source layout",
                            )
                            continue
                        if re.search(
                            r"diem|score|phuong thuc|method|nam tuyen sinh|year", folded(words)
                        ) and not re.search(r"\d+[.,]\d+", words):
                            header_count += 1
                        else:
                            break
                    headers = [
                        [
                            {"text": values[r][c] or "", "locator": f"{tloc}:r{r}:c{c}"}
                            for r in range(header_count)
                            if c < len(values[r])
                        ]
                        for c in range(width)
                    ]
                    header_text = " ".join(c or "" for row in values[:header_count] for c in row)
                    preceding = [line for line in lines if line["bottom"] <= table.bbox[1]]
                    ctx = [
                        {
                            "text": line["text"],
                            "locator": f"{ploc}:line{n}",
                            "bbox": bbox_list(
                                (line["x0"], line["top"], line["x1"], line["bottom"])
                            ),
                        }
                        for n, line in enumerate(lines)
                        if line["bottom"] <= table.bbox[1]
                    ][-6:]
                    kind, codes = classify(header_text, table=True)
                    if kind == "catalog" and codes:
                        kind, codes = classify(
                            " ".join(x["text"] for x in ctx) + " " + header_text, table=True
                        )
                    for code in codes:
                        result.issue(code, tloc, "Table semantics not confirmed")
                    signature = tuple(tuple(row) for row in values[:header_count])
                    continuation = None
                    if (
                        previous
                        and previous["page"] == page_no - 1
                        and signature == previous["signature"]
                    ):
                        same_columns = len(previous["columns"]) == width and all(
                            abs(a - b) < 3
                            for a, b in zip(
                                previous["columns"],
                                [c[0] if c else -1 for c in table.rows[0].cells],
                            )
                        )
                        if same_columns:
                            if re.search(
                                r"continued|tiep theo|tiep tuc",
                                folded(" ".join(line["text"] for line in preceding)),
                            ):
                                continuation = previous["locator"]
                            else:
                                result.issue(
                                    "possible_table_continuation",
                                    tloc,
                                    "Repeated header, but continuation not explicit; tables not merged",
                                )
                    notes = [
                        {
                            "text": line["text"],
                            "locator": f"{ploc}:line{n}",
                            "bbox": bbox_list(
                                (line["x0"], line["top"], line["x1"], line["bottom"])
                            ),
                        }
                        for n, line in enumerate(lines)
                        if line["top"] >= table.bbox[3]
                        and re.match(
                            r"^(?:\(?\*|ghi chu|luu y|note|footnote)", folded(line["text"])
                        )
                    ]
                    for r, row in enumerate(values[header_count:], start=header_count):
                        if not any(v for v in row):
                            continue
                        cells = []
                        physical = table.rows[r].cells
                        for col in range(width):
                            box = physical[col] if col < len(physical) else None
                            value = row[col] if col < len(row) else None
                            cells.append(
                                {
                                    "column": col,
                                    "origin": f"{tloc}:r{r}:c{col}" if box else None,
                                    "text": value,
                                    "raw_text": value,
                                    "bbox": bbox_list(box) if box else None,
                                }
                            )
                            if box is None:
                                result.issue(
                                    "pdf_merged_or_missing_cell",
                                    f"{tloc}:r{r}",
                                    "Missing cell boundary; no forward fill or assignment",
                                )
                            if (
                                kind == "cutoff"
                                and value == ""
                                and any(
                                    re.search(r"diem|score", folded(h["text"]))
                                    for h in headers[col]
                                )
                            ):
                                result.issue(
                                    "empty_score_cell", f"{tloc}:r{r}", "Blank score retained"
                                )
                            if value and re.search(r"\d[.,]\d{3}(?:\D|$)", value):
                                result.issue(
                                    "ambiguous_numeric_token",
                                    f"{tloc}:r{r}",
                                    "Locale/scale ambiguity retained; T06 review required",
                                )
                        fields = {
                            "kind": "table_row",
                            "page": page_no,
                            "bbox": bbox_list(table.rows[r].bbox),
                            "table_bbox": bbox_list(table.bbox),
                            "table_index": index,
                            "row_index": r,
                            "headers": headers,
                            "cells": cells,
                            "context": ctx,
                            "footnotes": notes,
                            "continuation_of": continuation,
                            "raw_text": " | ".join(v or "" for v in row),
                        }
                        row_kind = kind
                        if kind == "cutoff" and not any(
                            isinstance(cell["text"], str)
                            and re.search(r"\d", cell["text"])
                            and any(
                                re.search(r"diem|score", folded(h["text"])) for h in headers[column]
                            )
                            for column, cell in enumerate(cells)
                        ):
                            row_kind = "catalog"
                            result.issue(
                                "cutoff_row_without_value",
                                f"{tloc}:r{r}",
                                "No original score value; retain catalog context only",
                            )
                        obs = observation(
                            ref, row_kind, f"{tloc}:r{r}", version, "pdf_table", fields
                        )
                        result.observations.append(
                            obs.model_copy(
                                update={
                                    "issues": [
                                        i
                                        for i in result.issues
                                        if i.locator in (tloc, obs.record_locator)
                                    ]
                                }
                            )
                        )
                    previous = {
                        "page": page_no,
                        "signature": signature,
                        "locator": tloc,
                        "columns": [c[0] if c else -1 for c in table.rows[0].cells],
                    }
                for n, line in enumerate(lines):
                    box = (line["x0"], line["top"], line["x1"], line["bottom"])
                    if any(
                        box[0] < t[2] and box[2] > t[0] and box[1] < t[3] and box[3] > t[1]
                        for t in table_boxes
                    ):
                        continue
                    value = line["text"]
                    if not relevant(value):
                        continue
                    key = value
                    if (line["top"] < 80 or line["bottom"] > page.height - 50) and key in repeated:
                        result.issue(
                            "repeated_page_header",
                            f"{ploc}:line{n}",
                            "Repeated header kept as context, not duplicated observation",
                        )
                        continue
                    repeated[key] = page_no
                    kind, codes = classify(value)
                    if kind == "cutoff":
                        kind = "catalog"
                        codes.append("narrative_cutoff_requires_structured_evidence")
                    for code in codes:
                        result.issue(code, f"{ploc}:line{n}", "Narrative not a verified cutoff")
                    result.observations.append(
                        observation(
                            ref,
                            kind,
                            f"{ploc}:line{n}",
                            version,
                            "pdf_text",
                            {
                                "kind": "text_block",
                                "text": value,
                                "raw_text": value,
                                "page": page_no,
                                "line_index": n,
                                "bbox": bbox_list(box),
                            },
                            "0.6000",
                        )
                    )
    except Exception as exc:
        code = "encrypted_pdf" if "Password" in type(exc).__name__ else "pdf_parse_error"
        result.observations = []
        result.issue(code, "document", "PDF cannot be safely extracted; review original", "error")
    return result
