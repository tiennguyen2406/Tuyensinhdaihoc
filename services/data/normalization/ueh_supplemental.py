"""UEH supplemental drafts. Source calculations stay evidence; canonical scope is blocked."""

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
from services.data.parsers.ueh_supplemental import HEADERS, URL, VERSION


def normalize_supplemental(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    result = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
        issues=inherited(obs, ctx),
    )
    fields = obs.raw_fields
    mapping = fields.get("ueh_supplemental_2024", {})
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or obs.fact_kind != "cutoff"
        or mapping.get("snapshot_id") != str(obs.snapshot_id)
        or mapping.get("source_url") != URL
        or mapping.get("table_locator") != fields.get("table_locator")
        or mapping.get("publication_date", {}).get("value") != "2024-09-30"
        or not all(
            mapping.get(k)
            for k in ("publication", "method", "campus", "round", "priority", "eligibility")
        )
        or 2024 not in ctx.target_years
        or "Chính quy" not in ctx.training_modes
    ):
        result.issues.append(
            issue(
                "UEH_SUPPLEMENTAL_BINDING_REQUIRED",
                obs.record_locator,
                "Source-specific snapshot/table/year/method/campus/round evidence required",
            )
        )
        return result
    cells = fields.get("cells", [])
    headers = fields.get("headers", [])
    if len(cells) != 6 or [[text(h["text"]).search_key for h in p] for p in headers] != [
        [h] for h in HEADERS
    ]:
        result.issues.append(
            issue(
                "UEH_SUPPLEMENTAL_HEADER_REQUIRED",
                obs.record_locator,
                "Exact code/program/combination/PT6 paths required",
            )
        )
        return result
    cell = cells[5]
    loc = cell.get("origin") or obs.record_locator
    raw = cell.get("raw_text") or ""
    numeric = number(raw)
    problems = [i for i in result.issues if i.blocks_candidate]
    for col in (1, 2, 3, 5):
        slot = cells[col]
        origin = fields.get("origin_cells", {}).get(slot.get("origin"), {})
        if (
            slot.get("span_reference")
            or not origin
            or origin.get("rowspan") != 1
            or origin.get("colspan") != 1
            or origin.get("raw_text") != slot.get("raw_text")
            or not slot.get("raw_text")
        ):
            problems.append(
                issue(
                    "UEH_SUPPLEMENTAL_PHYSICAL_CELL_REQUIRED",
                    loc,
                    "Original unspanned code/program/combination/value required",
                )
            )
    if numeric.status != "value" or numeric.value is None or numeric.value < 0:
        problems.append(
            issue("UEH_SUPPLEMENTAL_VALUE_REQUIRED", loc, "Nonblank PT6 Decimal required")
        )
    if problems:
        result.blocked.append(
            Blocked(
                value=numeric,
                cell_locator=loc,
                raw_value=raw,
                header_path=headers[5],
                admission_year=2024,
                method="UEH PT6",
                issues=problems,
            )
        )
        return result
    evidence = {"ueh_supplemental_2024": mapping}
    for col, key in ((1, "offering_code"), (2, "program_name"), (3, "combinations")):
        evidence[key] = {
            "raw_value": cells[col]["raw_text"],
            "locator": cells[col]["origin"],
            "header_path": headers[col],
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
                "program_markers": mapping["program_markers"],
                "round_proposal": mapping["round"],
            },
            lineage=lineage(obs, ctx, cell, headers[5], raw, evidence),
            issues=[
                issue(code, loc, detail, blocks=False)
                for code, detail in [
                    (
                        "UEH_AUTHORITY_IDENTITY_REVIEW",
                        "Source authority and University/Program/Offering/PT6 are unapproved",
                    ),
                    (
                        "SCORE_SCALE_BASIS_UNCONFIRMED",
                        "Documented30/formulas/priority are evidence, not approved rules",
                    ),
                    (
                        "SCOPE_COMPONENTS_UNRESOLVED",
                        "Supplemental notice is a round proposal; population/conditions/aggregate require review",
                    ),
                    (
                        "WEIGHTING_RULE_REVIEW_REQUIRED",
                        "Marker-specific source evidence retained without calculation or rule approval",
                    ),
                ]
            ],
        )
    )
    return result
