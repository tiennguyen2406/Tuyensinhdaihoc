"""Evidence-bound UEH PT6 draft mapping; leaves canonical scale, basis and scope unknown."""

import hashlib

from services.data.normalization.contract import (
    Blocked,
    Candidate,
    NormalizationContext,
    NormalizedObservation,
    RawObservation,
)
from services.data.normalization.normalize import inherited, issue, lineage, strings
from services.data.normalization.values import number, text
from services.data.parsers.ueh import URL, VERSION


def normalize_ueh(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    result = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
        issues=inherited(obs, ctx),
    )
    # The source table's total row has no cutoff. Keep its diagnostic, without
    # letting that different physical row suppress independently mapped PT6 cells.
    result.issues = [
        i.model_copy(update={"blocks_candidate": False})
        if i.level == "document"
        and i.code == "cutoff_row_without_value"
        and i.locator != obs.record_locator
        and not obs.record_locator.startswith(i.locator + " > ")
        else i
        for i in result.issues
    ]
    fields = obs.raw_fields
    mapping = fields.get("ueh_2024", {})
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or obs.fact_kind != "cutoff"
        or mapping.get("snapshot_id") != str(obs.snapshot_id)
        or mapping.get("source_url") != URL
        or mapping.get("table_locator") != fields.get("table_locator")
        or not mapping.get("publication")
        or not mapping.get("method")
        or not mapping.get("campus")
        or 2024 not in ctx.target_years
        or "Chính quy" not in ctx.training_modes
    ):
        result.issues.append(
            issue(
                "UEH_MAPPING_BINDING_REQUIRED",
                obs.record_locator,
                "Requires the source-specific T05 snapshot/table/section binding",
                level="row",
            )
        )
        return result
    cells = fields.get("cells", [])
    headers = fields.get("headers", [])
    if len(cells) <= 8 or len(headers) <= 8:
        result.issues.append(
            issue("UEH_HEADER_ALIGNMENT", obs.record_locator, "PT6 column missing")
        )
        return result
    cell = cells[8]
    path = headers[8]
    loc = cell.get("origin") or obs.record_locator
    expected_headers = {
        1: ["ma dang ky xet tuyen"],
        2: ["chuong trinh dao tao"],
        7: ["pt6", "to hop xet tuyen"],
    }
    if any(
        [text(h["text"]).search_key for h in headers[col]] != expected
        for col, expected in expected_headers.items()
    ):
        result.issues.append(
            issue(
                "UEH_SCOPE_HEADER_REQUIRED",
                loc,
                "Exact program/code/PT6 combination paths required",
            )
        )
        return result
    if [text(h["text"]).search_key for h in path] != ["pt6", "diem trung tuyen"]:
        result.issues.append(
            issue("UEH_PT6_HEADER_REQUIRED", loc, "Exact PT6 cutoff path required")
        )
        return result
    if cell.get("span_reference"):
        result.issues.append(issue("SPAN_REFERENCE_NOT_EMITTED", loc, "Reference is not a value"))
        return result
    raw = cell.get("raw_text") or ""
    numeric = number(raw)
    origin = fields.get("origin_cells", {}).get(loc, {})
    problems = [i for i in result.issues if i.blocks_candidate]
    if (
        origin.get("raw_text") != raw
        or origin.get("rowspan") != 1
        or origin.get("colspan") != 1
        or numeric.status != "value"
        or numeric.value is None
        or numeric.value < 0
    ):
        problems.append(
            issue(
                "UEH_PHYSICAL_SCORE_REQUIRED",
                loc,
                "Original nonblank unspanned PT6 Decimal required",
            )
        )
    for col in (1, 2, 7):
        if cells[col].get("span_reference") or not cells[col].get("raw_text"):
            problems.append(
                issue(
                    "UEH_ROW_SCOPE_REQUIRED",
                    loc,
                    "Physical program/code/combination cells required",
                )
            )
    if problems:
        result.blocked.append(
            Blocked(
                value=numeric,
                cell_locator=loc,
                raw_value=raw,
                header_path=path,
                admission_year=2024,
                method="UEH PT6",
                issues=problems,
            )
        )
        return result
    evidence = {
        "ueh_2024": mapping,
        "combinations": {
            "raw_value": cells[7]["raw_text"],
            "locator": cells[7]["origin"],
            "header_path": headers[7],
        },
        "program_name": {"raw_value": cells[2]["raw_text"], "locator": cells[2]["origin"]},
        "offering_code": {"raw_value": cells[1]["raw_text"], "locator": cells[1]["origin"]},
    }
    result.candidates.append(
        Candidate(
            candidate_key=hashlib.sha256(
                f"{obs.id}|{loc}|{ctx.transform_version}".encode()
            ).hexdigest(),
            fact_kind="cutoff",
            admission_year=2024,
            method=text("UEH PT6 — Thi tốt nghiệp THPT năm 2024"),
            value=numeric,
            scope={
                "campus": text("KSV").model_dump(),
                "training_mode": text("Chính quy").model_dump(),
                "program_name": text(cells[2]["raw_text"]).model_dump(),
                "offering_code": text(cells[1]["raw_text"]).model_dump(),
                "track": None,
                "language": None,
            },
            lineage=lineage(obs, ctx, cell, path, raw, evidence),
            issues=[
                issue(code, loc, detail, blocks=False)
                for code, detail in [
                    (
                        "UEH_AUTHORITY_IDENTITY_REVIEW",
                        "UEH, Program, Offering and source authority are pending",
                    ),
                    (
                        "SCORE_SCALE_BASIS_UNCONFIRMED",
                        "Documented 30-point note is evidence, not approved scale/basis/formula",
                    ),
                    (
                        "SCOPE_COMPONENTS_UNRESOLVED",
                        "Round/population/conditions and aggregate applicability require review",
                    ),
                    (
                        "WEIGHTED_SUBJECT_RULE_UNRESOLVED",
                        "Retain source footnote; specific subjects/formula not established by fallback",
                    ),
                ]
            ],
        )
    )
    return result
