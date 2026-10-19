"""Business-region DOM extraction. Spans reference physical cells; scores are never filled."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from services.api.source_profiles import SourceProfile
from services.data.parsers.common import classify, folded, observation, relevant
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef

VERSION = "html/1.0.1"


def locator(node: Tag) -> str:
    parts = []
    current: Tag | None = node
    while current is not None and current.name != "[document]":
        index = 1 + sum(
            isinstance(n, Tag) and n.name == current.name for n in current.previous_siblings
        )
        parts.append(f"{current.name}:nth-of-type({index})")
        current = current.parent if isinstance(current.parent, Tag) else None
    return "html:" + " > ".join(reversed(parts))


def locate(soup: BeautifulSoup, value: str) -> Tag:
    if not value.startswith("html:"):
        raise ValueError("Not an HTML locator")
    node = soup.select_one(value[5:])
    if node is None:
        raise ValueError("Locator not found in snapshot")
    return node


def text(node: Tag) -> str:
    return node.get_text(" ", strip=True)


def context(node: Tag, root: Tag, title: str) -> list[dict[str, str]]:
    section = node.find_parent("section")
    scope = (
        section if section is not None and (section is root or root in section.parents) else root
    )
    headings: list[tuple[int, dict[str, str]]] = []
    for prior in scope.descendants:
        if prior is node:
            break
        if (
            not isinstance(prior, Tag)
            or prior.name not in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}
            or any(prior is p for p in node.parents)
        ):
            continue
        if prior.find_parent("table"):
            continue
        value = text(prior)
        level = int(prior.name[1]) if prior.name.startswith("h") else 7
        marked = (
            prior.name.startswith("h")
            or len(value) <= 400
            and (
                prior.find(["strong", "b"]) is not None
                or re.match(r"^(?:[IVX]+\.|[a-z]\)|\d+\.)", value)
            )
        )
        if marked:
            # Publishers sometimes use h4 for 2.5 and h5 for chapter 11.
            # Explicit numbered chapters reset obsolete numeric context, regardless of styling.
            ordinal = re.match(r"^(\d+(?:\.\d+)*)\.\s", prior.get_text().strip())
            if ordinal:
                current_number = tuple(int(n) for n in ordinal[1].split("."))
                kept = []
                for item in headings:
                    old = re.match(
                        r"^(\d+(?:\.\d+)*)\.\s", item[1].get("raw_text", item[1]["text"]).strip()
                    )
                    old_number = tuple(int(n) for n in old[1].split(".")) if old else None
                    if old_number is None or (
                        len(old_number) < len(current_number)
                        and current_number[: len(old_number)] == old_number
                    ):
                        kept.append(item)
                headings = kept
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append(
                (level, {"text": value, "raw_text": prior.get_text(), "locator": locator(prior)})
            )
    title_node = root.find("h1") or root.find_previous("h1")
    title_context = (
        [{"text": title, "locator": locator(title_node)}] if title_node is not None else []
    )
    return title_context + [entry for _, entry in headings]


def footnotes(table: Tag) -> list[dict[str, str]]:
    result = []
    for node in table.next_elements:
        if not isinstance(node, Tag) or table in node.parents:
            continue
        if node.name == "table" or node.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            break
        if node.name in ("p", "small") and node.find_parent("table") is None:
            value = text(node)
            if re.match(r"^(?:\(?\*|ghi chu|luu y|chu thich|footnote|note)", folded(value)):
                result.append(
                    {"text": value, "raw_text": node.get_text(), "locator": locator(node)}
                )
    return result


def table_rows(
    table: Tag,
    ref: SnapshotRef,
    result: ParseResult,
    ctx: list[dict[str, str]],
    budget: int,
    version: str,
    header_row_count: int = 0,
    score_columns: frozenset[int] = frozenset(),
) -> int:
    loc = locator(table)
    if table.find("table"):
        result.issue("nested_table", loc, "Nested tables need a source-specific layout adapter")
        return 0
    rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
    grid: dict[tuple[int, int], str] = {}
    origins: dict[str, dict[str, Any]] = {}
    header_rows = []
    count = 0
    for r, row in enumerate(rows):
        cells = row.find_all(["td", "th"], recursive=False)
        is_header = (
            r < header_row_count
            or row.find_parent("thead") is not None
            or bool(cells)
            and all(c.name == "th" for c in cells)
        )
        if r == 0 and cells and all(c.find(["strong", "b"]) is not None for c in cells):
            is_header = True
        if is_header:
            header_rows.append(r)
        col = 0
        for cell in cells:
            while (r, col) in grid:
                col += 1
            try:
                rs = int(str(cell.get("rowspan", "1")))
                cs = int(str(cell.get("colspan", "1")))
                if rs == 0:
                    rs = len(rows) - r
                if rs < 1 or cs < 1:
                    raise ValueError()
            except ValueError:
                result.issue("invalid_span", locator(cell), "Invalid cell span")
                return count
            if rs * cs > budget - count or (r + rs) > len(rows) or col + cs > budget:
                result.issue(
                    "table_cell_limit", loc, "Span/table exceeds bounded cell grid", "error"
                )
                return count
            origin = locator(cell)
            origins[origin] = {
                "text": cell.get_text().strip(),
                "raw_text": cell.get_text(),
                "row": r,
                "column": col,
                "rowspan": rs,
                "colspan": cs,
                "locator": origin,
            }
            for rr in range(r, r + rs):
                for cc in range(col, col + cs):
                    if (rr, cc) in grid:
                        result.issue("overlapping_spans", loc, "Conflicting physical cell spans")
                        return count
                    grid[rr, cc] = origin
                    count += 1
            col += cs
    width = max((c + 1 for _, c in grid), default=0)
    if width * len(rows) > budget:
        result.issue("table_cell_limit", loc, "Ragged table expansion exceeds budget", "error")
        return count
    headers = []
    for col in range(width):
        ids = list(dict.fromkeys(grid[r, col] for r in header_rows if (r, col) in grid))
        headers.append([{"text": origins[i]["text"], "locator": i} for i in ids])
    header_text = " ".join(h["text"] for path in headers for h in path)
    caption_node = table.find("caption")
    caption = text(caption_node) if caption_node else ""
    # Local header evidence wins; do not let an unrelated earlier heading label bonus points as cutoffs.
    kind, codes = classify(header_text + " " + caption, table=True)
    if kind == "catalog" and (
        "ambiguous_table_kind" in codes
        or re.search(r"diem|score|thpt|hsa|tsa", folded(header_text))
    ):
        kind, codes = classify(
            " ".join(v["text"] for v in ctx[-2:]) + " " + header_text + " " + caption, table=True
        )
    for code in codes:
        result.issue(code, loc, "Table semantics require review; raw values retained")
    notes = footnotes(table)
    group = None
    for r, row in enumerate(rows):
        if r in header_rows:
            continue
        own = [o for o in origins.values() if o["row"] == r]
        if (
            own
            and any(o["colspan"] >= max(2, width - 2) for o in own)
            and re.fullmatch(r"[IVX]+", str(own[0]["text"]))
        ):
            group = {"text": text(row), "locator": locator(row)}
            continue
        if not own or not any(o["text"] for o in own):
            continue
        values: list[dict[str, Any]] = []
        for col in range(width):
            origin_id = grid.get((r, col))
            origin_data = origins.get(origin_id or "")
            reference = bool(
                origin_data and (origin_data["row"] != r or origin_data["column"] != col)
            )
            values.append(
                {
                    "column": col,
                    "origin": origin_id,
                    "text": None if reference else origin_data["text"] if origin_data else "",
                    "raw_text": None
                    if reference
                    else origin_data["raw_text"]
                    if origin_data
                    else "",
                    "span_reference": reference,
                }
            )
        row_issues = []
        for slot, path in zip(values, headers):
            is_score = slot["column"] in score_columns or any(
                re.search(r"diem|score", folded(h["text"])) for h in path
            )
            if kind == "cutoff" and is_score and slot["text"] == "":
                result.issue(
                    "empty_score_cell",
                    locator(row),
                    "Blank score retained as blank; no forward fill",
                )
        row_kind = kind
        if kind == "cutoff" and not any(
            isinstance(v["text"], str)
            and re.search(r"\d", v["text"])
            and (
                index in score_columns
                or any(
                    re.search(r"diem|score|thpt|hsa|tsa", folded(h["text"])) for h in headers[index]
                )
            )
            for index, v in enumerate(values)
        ):
            row_kind = "catalog"
            result.issue(
                "cutoff_row_without_value",
                locator(row),
                "No original cutoff value; retain catalog context only",
            )
        selected = {i: origins[i] for i in dict.fromkeys(v["origin"] for v in values) if i}
        fields = {
            "kind": "table_row",
            "raw_text": row.get_text(),
            "context": ctx,
            "group": group,
            "table_locator": loc,
            "caption": caption,
            "caption_locator": locator(caption_node) if caption_node else None,
            "headers": headers,
            "cells": values,
            "origin_cells": selected,
            "footnotes": notes,
        }
        obs = observation(ref, row_kind, locator(row), version, "html_dom", fields)
        row_issues = [i for i in result.issues if i.locator in (loc, locator(row))]
        result.observations.append(obs.model_copy(update={"issues": row_issues}))
    return width * len(rows)


def parse_html(
    ref: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits | None = None,
    version: str = VERSION,
) -> ParseResult:
    limits = limits or ParseLimits()
    result = ParseResult()
    if len(data) > limits.max_bytes:
        result.issue("body_limit", "document", "Snapshot exceeds parser byte budget", "error")
        return result
    soup = BeautifulSoup(data, "html.parser")
    root = None
    for selector in profile.parser_options.html_content_selectors:
        matches = soup.select(selector)
        if len(matches) == 1:
            root = matches[0]
            break
        if len(matches) > 1:
            result.issue("ambiguous_business_region", "document", "Selector matches multiple roots")
            return result
    if root is None:
        result.issue(
            "business_region_missing",
            "document",
            "No configured business root; footer/nav not used",
        )
        return result
    excluded = {
        id(n)
        for selector in profile.parser_options.html_exclude_selectors
        for n in root.select(selector)
    }

    def allowed(n: Tag) -> bool:
        return id(n) not in excluded and not any(id(p) in excluded for p in n.parents)

    title_node = root.find("h1") or soup.find("h1")
    title = text(title_node) if title_node else ""
    result.metadata = {"business_root": locator(root), "document_title": title}
    for node in root.find_all(["img", "iframe", "embed", "object"]):
        if allowed(node):
            result.issue(
                "image_requires_review" if node.name == "img" else "attachment_not_embedded_text",
                locator(node),
                "Local image/attachment is not OCRed or downloaded",
            )
    remaining = limits.max_cells
    for table in root.find_all("table"):
        if not allowed(table) or table.find_parent("table"):
            continue
        consumed = table_rows(table, ref, result, context(table, root, title), remaining, version)
        remaining -= consumed
        if remaining <= 0:
            break
    for node in root.find_all(["p", "li"]):
        if not allowed(node) or node.find_parent("table") or node.find(["p", "li"]):
            continue
        value = text(node)
        if not value or not relevant(value):
            continue
        kind, codes = classify(value)
        # Narrative mentions alone do not establish a cutoff record.
        if kind == "cutoff":
            kind = "catalog"
            codes.append("narrative_cutoff_requires_structured_evidence")
        for code in codes:
            result.issue(code, locator(node), "Preserve narrative; no published cutoff inferred")
        result.observations.append(
            observation(
                ref,
                kind,
                locator(node),
                version,
                "html_dom",
                {
                    "kind": "text_block",
                    "text": value,
                    "raw_text": node.get_text(),
                    "context": context(node, root, title),
                },
                "0.6000",
            )
        )
    if any(i.severity == "error" for i in result.issues):
        result.observations = []
    return result
