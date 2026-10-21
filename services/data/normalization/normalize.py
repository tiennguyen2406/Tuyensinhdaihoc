"""Conservative physical-cell mapping; header-local years/methods only."""

import hashlib
import re
from typing import Any, Literal

from services.data.normalization.contract import (
    Blocked,
    Candidate,
    Issue,
    Lineage,
    NormalizationContext,
    NormalizedObservation,
    RawObservation,
)
from services.data.normalization.values import TextValue, money, number, text
from services.data.parsers.contract import TRANSFORM_VERSION


def issue(
    code: str,
    locator: str,
    detail: str,
    *,
    level: Literal["document", "row", "cell", "field"] = "field",
    field: str | None = None,
    blocks: bool = True,
) -> Issue:
    return Issue(
        code=code, locator=locator, detail=detail, level=level, field=field, blocks_candidate=blocks
    )


def strings(value: Any, path: str = "") -> dict[str, TextValue]:
    result: dict[str, TextValue] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"text", "raw_text", "caption"} and isinstance(item, str):
                result[path + "/" + key] = text(item)
            elif isinstance(item, (dict, list)) and not key.startswith("_"):
                result.update(strings(item, path + "/" + key.replace("~", "~0").replace("/", "~1")))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.update(strings(item, path + "/" + str(index)))
    return result


def scope_of(obs: RawObservation) -> tuple[dict[str, Any], dict[str, Any], int | None]:
    fields = obs.raw_fields
    context = fields.get("context", [])
    scope: dict[str, Any] = {
        "campus": None,
        "training_mode": None,
        "program_name": None,
        "offering_code": None,
    }
    evidence: dict[str, Any] = {}
    doc_year = None
    for entry in context:
        value = text(entry.get("raw_text", entry.get("text", "")))
        key = value.search_key
        # Only a title h1 can supply document year. Never used as admission year.
        if doc_year is None and (
            "h1:" in entry.get("locator", "") or "> h1" in entry.get("locator", "")
        ):
            years = re.findall(r"(?<!\d)(20\d{2})(?!\d)", key)
            if len(set(years)) == 1:
                doc_year = int(years[0])
        campuses = re.findall(r"\b(BVH|BVS)\b", value.display)
        if len(set(campuses)) > 1:
            scope["campus"] = None
            evidence["campus_ambiguous"] = entry
        elif len(set(campuses)) == 1:
            scope["campus"] = text(campuses[0]).model_dump()
            evidence["campus"] = entry
        # Section headings override the document title. Method headings cannot supply scope.
        if re.match(r"^(?:[ivx]+\.|thong tin tuyen sinh)", key) and re.search(
            r"chinh quy|thuong xuyen|vua (?:lam vua hoc|hoc vua lam)|tu xa", key
        ):
            forms = [
                label
                for pattern, label in [
                    ("chinh quy", "Chính quy"),
                    ("thuong xuyen", "Thường xuyên"),
                    ("vua lam vua hoc|vua hoc vua lam", "Vừa làm vừa học"),
                    ("tu xa", "Từ xa"),
                ]
                if re.search(pattern, key)
            ]
            scope["training_mode"] = text(forms[0]).model_dump() if len(forms) == 1 else None
            evidence["training_mode"] = entry
    headers = fields.get("headers", [])
    origins = fields.get("origin_cells", {})
    for cell in fields.get("cells", []):
        col = cell.get("column", -1)
        if col < 0 or col >= len(headers):
            continue
        header = " ".join(text(h["text"]).search_key for h in headers[col])
        origin = origins.get(cell.get("origin"), {})
        raw = origin.get("raw_text", cell.get("raw_text") or cell.get("text"))
        if not isinstance(raw, str):
            continue
        name = (
            "program_name"
            if re.search(r"ten.*(?:chuong trinh|nganh|program)|program name", header)
            else "offering_code"
            if re.search(r"ma.*(?:chuong trinh|nganh)|program code", header)
            else None
        )
        if name:
            program_value = text(raw).model_dump()
            if scope[name] is not None and scope[name]["display"] != program_value["display"]:
                evidence["program_ambiguous"] = {
                    "field": name,
                    "previous": evidence.get(name),
                    "current_locator": cell.get("origin"),
                }
            scope[name] = program_value
            evidence[name] = {
                "locator": cell.get("origin"),
                "header_path": headers[col],
                "raw_value": raw,
            }
    return scope, evidence, doc_year


def inherited(obs: RawObservation, ctx: NormalizationContext) -> list[Issue]:
    result = []
    own = obs.raw_fields.get("_extraction", {}).get("issues", [])
    for document, entries in [(True, ctx.document_issues), (False, own)]:
        for item in entries:
            loc = item.get("locator", "document")
            code = item.get("code", "UNKNOWN_PARSER_ISSUE")
            # Image/scan elsewhere remains open, without tainting explicit HTML table cells.
            unrelated = not (
                obs.record_locator == loc
                or obs.record_locator.startswith(loc + ":")
                or obs.record_locator.startswith(loc + " > ")
            )
            harmless = code in {
                "image_requires_review",
                "attachment_not_embedded_text",
                "empty_score_cell",
                "narrative_cutoff_requires_structured_evidence",
            }
            blocks = not harmless and not (
                document
                and unrelated
                and code
                in {
                    "ocr_required",
                    "ambiguous_abbreviated_cutoff_header",
                    "entry_threshold_not_cutoff",
                    "mixed_threshold_cutoff_context",
                    "mixed_narrative_fact_kinds",
                }
            )
            result.append(
                Issue(
                    code=code,
                    locator=loc,
                    level="document" if document else "row",
                    detail=item.get("detail", "Parser issue remains open"),
                    blocks_candidate=blocks,
                    origin="parser",
                )
            )
    return result


def lineage(
    obs: RawObservation,
    ctx: NormalizationContext,
    cell: dict[str, Any],
    path: list[dict[str, Any]],
    value: str,
    evidence: dict[str, Any],
) -> Lineage:
    return Lineage(
        observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        source_id=obs.source_id,
        parser_version=obs.parser_version,
        input_transform_version=obs.transform_version,
        normalizer_version=ctx.version,
        row_locator=obs.record_locator,
        cell_locator=cell.get("origin") or obs.record_locator,
        column=cell.get("column"),
        header_path=path,
        raw_value=value,
        bbox=cell.get("bbox"),
        context=obs.raw_fields.get("context", []),
        footnotes=obs.raw_fields.get("footnotes", []),
        scope_evidence=evidence,
    )


def normalize(obs: RawObservation, context: NormalizationContext) -> NormalizedObservation:
    if obs.transform_version != TRANSFORM_VERSION or obs.normalized_fields:
        raise ValueError("Normalization input must be raw-only, never normalizer output")
    if context.version in {"normalizer/hcm-intake/1.0.0", "normalizer/hcm-intake/1.0.1"}:
        from services.data.normalization.hcm_intake import normalize_hcm

        return normalize_hcm(obs, context)
    if context.version == "normalizer/ptit-2025-historical/1.0.0":
        from services.data.normalization.ptit_2025 import normalize_ptit_2025

        return normalize_ptit_2025(obs, context)
    if context.version in {
        "normalizer/ptit-2026-multimethod/1.0.0",
        "normalizer/ptit-2026-multimethod/1.0.1",
    }:
        from services.data.normalization.ptit_2026 import normalize_ptit_2026

        return normalize_ptit_2026(obs, context)
    if context.version == "normalizer/ueh-2024-pt345/1.0.0":
        from services.data.normalization.ueh_pt345 import normalize_pt345

        return normalize_pt345(obs, context)
    if context.version == "normalizer/ueh-2024-pt6-batch/1.0.0":
        from services.data.normalization.ueh_batch import normalize_batch

        return normalize_batch(obs, context)
    if context.version == "normalizer/ueh-2024-ksv/1.0.0":
        from services.data.normalization.ueh import normalize_ueh

        return normalize_ueh(obs, context)
    if context.version == "normalizer/ueh-supplemental-2024/1.0.0":
        from services.data.normalization.ueh_supplemental import normalize_supplemental

        return normalize_supplemental(obs, context)
    result = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=context.version,
        transform_version=context.transform_version,
        display_fields=strings(obs.raw_fields),
        issues=inherited(obs, context),
    )
    scope, evidence, doc_year = scope_of(obs)
    if obs.fact_kind == "tuition" and obs.raw_fields.get("kind") == "text_block":
        tuition(obs, context, result, scope, evidence, doc_year)
        return result
    if obs.fact_kind != "cutoff" or obs.raw_fields.get("kind") != "table_row":
        result.issues.append(
            issue(
                "STRUCTURED_MAPPING_REQUIRED",
                obs.record_locator,
                "Text display normalized; typed fact mapping requires reviewed adapter",
                level="row",
            )
        )
        return result
    headers = obs.raw_fields.get("headers", [])
    origins = obs.raw_fields.get("origin_cells", {})
    seen = set()
    for cell in obs.raw_fields.get("cells", []):
        col = cell.get("column", -1)
        if col < 0 or col >= len(headers):
            result.issues.append(
                issue(
                    "HEADER_ALIGNMENT_MISSING",
                    obs.record_locator,
                    "No aligned header for column",
                    level="row",
                )
            )
            continue
        path = headers[col]
        key = " ".join(text(h["text"]).search_key for h in path)
        if not re.search(r"diem|score|cutoff", key):
            continue
        origin_id = cell.get("origin")
        if cell.get("span_reference") or origin_id in seen:
            result.issues.append(
                issue(
                    "SPAN_REFERENCE_NOT_EMITTED",
                    str(origin_id),
                    "Reference slot is not a physical value",
                    level="cell",
                    blocks=False,
                )
            )
            continue
        seen.add(origin_id)
        raw = cell.get("raw_text", cell.get("text"))
        loc = origin_id or obs.record_locator
        problems = [i for i in result.issues if i.blocks_candidate]

        def block(code: str, detail: str, field: str = "value") -> None:
            problems.append(issue(code, loc, detail, field=field))

        if not re.search(
            r"diem trung tuyen|diem chuan|admission cutoff|cutoff score", key
        ) or re.search(r"diem san|nguong|nop ho so", key):
            block(
                "CUTOFF_HEADER_AMBIGUOUS",
                "Header does not explicitly establish an admission cutoff",
                "header",
            )
        origin = origins.get(origin_id, {})
        if origin.get("rowspan", 1) > 1 or origin.get("colspan", 1) > 1:
            block("SCORE_SPAN_AMBIGUOUS", "Physical score spans scopes; applicability not inferred")
        if not origin_id or not isinstance(raw, str):
            block("PHYSICAL_VALUE_MISSING", "No physical value at this slot")
            raw = ""
        if origin and origin.get("raw_text", raw) != raw:
            block("CELL_ORIGIN_MISMATCH", "Slot differs from retained physical origin")
        years: set[int] = set()
        for header in path:
            h = text(header["text"]).search_key
            # Explicit admission-year label, or a whole year header; school-year ranges never qualify.
            if "nam hoc" not in h and (
                re.fullmatch(r"20\d{2}", h) or "nam tuyen sinh" in h or "admission year" in h
            ):
                years.update(int(y) for y in re.findall(r"(?<!\d)20\d{2}(?!\d)", h))
        year = next(iter(years)) if len(years) == 1 else None
        if year is None:
            block(
                "ADMISSION_YEAR_MISSING" if not years else "ADMISSION_YEAR_AMBIGUOUS",
                "Exactly one header-local admission year required",
                "admission_year",
            )
        elif year not in context.target_years:
            block(
                "YEAR_OUT_OF_SCOPE",
                "Historical year preserved outside target 2024–2026",
                "admission_year",
            )
        method_value = None
        method_entries = [
            h
            for h in path
            if re.search(
                r"thpt|tai nang|ket hop|hoc ba|dgnl|dgtd|v-act|hsa|tsa|thi |xet tuyen",
                text(h["text"]).search_key,
            )
            and not re.search(r"diem trung tuyen|nam tuyen sinh", text(h["text"]).search_key)
        ]
        if not method_entries:
            block(
                "METHOD_MISSING",
                "No method in this column; surrounding 2026 method is not inherited",
                "method",
            )
        elif len(method_entries) != 1:
            block("METHOD_AMBIGUOUS", "Multiple method headers need explicit mapping", "method")
        else:
            method_value = text(method_entries[0]["text"])
            mk = method_value.search_key
            if ("dgnl" in mk and "dgtd" in mk) or re.search(r"diem tt|/|[,;]|\bhoac\b", mk):
                block(
                    "METHOD_AMBIGUOUS",
                    "Combined/abbreviated method cannot be split or resolved",
                    "method",
                )
        if any("diem tt" in text(h["text"]).search_key for h in path):
            block("METHOD_AMBIGUOUS", "Abbreviation remains unresolved", "method")
        if not scope["training_mode"]:
            block("TRAINING_MODE_MISSING", "Explicit training scope required", "scope")
        elif scope["training_mode"]["display"] not in context.training_modes:
            block("TRAINING_MODE_OUT_OF_SCOPE", "Training form outside configured pilot", "scope")
        if evidence.get("campus_ambiguous"):
            block(
                "CAMPUS_AMBIGUOUS",
                "Context names multiple campuses; no precise campus assigned",
                "scope",
            )
        elif context.require_campus and not scope["campus"]:
            block("CAMPUS_MISSING", "BVH/BVS campus requires explicit evidence", "scope")
        if evidence.get("program_ambiguous"):
            block(
                "PROGRAM_SCOPE_AMBIGUOUS",
                "Conflicting source programme columns need cell-local mapping",
                "scope",
            )
        if not scope["offering_code"] or not scope["program_name"]:
            block(
                "PROGRAM_SCOPE_MISSING",
                "Source program name/code required without canonical resolution",
                "scope",
            )
        numeric = number(raw)
        if numeric.status != "value":
            block(
                numeric.issue or "VALUE_" + numeric.status.upper(),
                "Value not safely mapped; raw/null status retained",
            )
        elif numeric.value is not None and numeric.value < 0:
            block("NEGATIVE_SCORE", "Negative score needs source review")
        if problems:
            result.blocked.append(
                Blocked(
                    value=numeric,
                    cell_locator=loc,
                    raw_value=raw,
                    header_path=path,
                    admission_year=year,
                    method=method_value.display if method_value else None,
                    issues=problems,
                )
            )
            continue
        warnings = [
            issue(
                "SCOPE_COMPONENTS_UNRESOLVED",
                loc,
                "Round/population/conditions/combination remain unknown; T07/reviewer required",
                blocks=False,
            ),
            issue(
                "SCORE_SCALE_UNCONFIRMED",
                loc,
                "No scale/rule inferred from score magnitude or method",
                blocks=False,
            ),
        ]
        if obs.raw_fields.get("footnotes"):
            warnings.append(
                issue(
                    "CONDITIONS_REQUIRE_REVIEW",
                    loc,
                    "Footnotes preserved; not executed or expanded",
                    blocks=False,
                )
            )
        warnings.append(
            issue(
                "CONTEXT_METHOD_NOT_INHERITED",
                obs.record_locator,
                "Only column-local method used; heading stack retained as raw context",
                level="row",
                blocks=False,
            )
        )
        result.candidates.append(
            Candidate(
                candidate_key=hashlib.sha256(
                    f"{obs.id}|{loc}|{context.transform_version}".encode()
                ).hexdigest(),
                fact_kind="cutoff",
                admission_year=year,
                document_year=doc_year,
                method=method_value,
                value=numeric,
                scope=scope,
                lineage=lineage(obs, context, cell, path, raw, evidence),
                issues=warnings,
            )
        )
    return result


def tuition(
    obs: RawObservation,
    ctx: NormalizationContext,
    result: NormalizedObservation,
    scope: dict[str, Any],
    evidence: dict[str, Any],
    doc_year: int | None,
) -> None:
    raw = obs.raw_fields.get("raw_text", "")
    display = text(raw).display
    key = text(raw).search_key
    academic = re.search(r"nam hoc (20\d{2})\s*[-–]\s*(20\d{2})", key)
    # Restrict to explicit paragraph-local range. Keep original programme group and qualifications.
    matches = list(
        re.finditer(
            r"(\d+(?:[.,]\d+)?)\s*triệu đồng(?:\s*/\s*năm(?: học)?)?\s*đến\s*(\d+(?:[.,]\d+)?)\s*triệu đồng\s*/\s*năm(?: học)?",
            display,
            re.I,
        )
    )
    match = matches[0] if len(matches) == 1 else None
    problems = [i for i in result.issues if i.blocks_candidate]
    if len(matches) > 1:
        problems.append(
            issue(
                "TUITION_MULTIPLE_RANGES",
                obs.record_locator,
                "Multiple prices require explicit local group/range evidence; no first-match selection",
                level="row",
            )
        )
    if not academic or not match or int(academic[2]) != int(academic[1]) + 1:
        problems.append(
            issue(
                "TUITION_MAPPING_REQUIRES_REVIEW",
                obs.record_locator,
                "No single explicit academic-year range with billing unit; narrative preserved",
                level="row",
            )
        )
    if not scope["training_mode"]:
        problems.append(
            issue(
                "TRAINING_MODE_MISSING",
                obs.record_locator,
                "Explicit fee training scope required",
                field="scope",
            )
        )
    if scope["training_mode"] and scope["training_mode"]["display"] not in ctx.training_modes:
        problems.append(
            issue(
                "TRAINING_MODE_OUT_OF_SCOPE",
                obs.record_locator,
                "Outside pilot training scope",
                field="scope",
            )
        )
    if problems:
        result.blocked.append(
            Blocked(cell_locator=obs.record_locator, raw_value=raw, header_path=[], issues=problems)
        )
        return
    assert match is not None and academic is not None
    value = money(f"{match[1]}–{match[2]} triệu/năm").model_copy(
        update={
            "raw": match[0],
            "approximate": "khoang" in key or "du kien" in key or "trung binh" in key,
        }
    )
    if value.status != "value":
        result.blocked.append(
            Blocked(
                cell_locator=obs.record_locator,
                raw_value=raw,
                header_path=[],
                issues=[
                    issue(
                        value.issue or "NUMERIC_AMBIGUOUS",
                        obs.record_locator,
                        "Fee range ambiguous",
                    )
                ],
            )
        )
        return
    scope = scope | {"programme_group_statement": text(raw).model_dump()}
    result.candidates.append(
        Candidate(
            candidate_key=hashlib.sha256(
                f"{obs.id}|tuition|{ctx.transform_version}".encode()
            ).hexdigest(),
            fact_kind="tuition",
            document_year=doc_year,
            academic_year=f"{academic[1]}–{academic[2]}",
            value=value,
            scope=scope,
            lineage=lineage(obs, ctx, {}, [], raw, evidence),
            issues=[
                issue(
                    "TUITION_GROUP_SCOPE_REQUIRES_REVIEW",
                    obs.record_locator,
                    "Aggregate programme group and average/provisional qualifiers retained; no per-program expansion",
                    blocks=False,
                )
            ],
        )
    )
