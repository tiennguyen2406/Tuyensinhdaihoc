"""Typed unverified drafts. No identity, scale, authority or publication approval."""

import hashlib
import re
from typing import Any

from services.data.normalization.contract import (
    Blocked,
    Candidate,
    NormalizationContext,
    NormalizedObservation,
    RawObservation,
)
from services.data.normalization.normalize import inherited, issue, lineage, strings
from services.data.normalization.values import number, text
from services.data.parsers.hcm_intake import VERSION


def normalize_hcm(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    result = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
        issues=inherited(obs, ctx),
    )
    fields = obs.raw_fields
    binding = fields.get("hcm_intake", {})
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or binding.get("snapshot_id") != str(obs.snapshot_id)
        or binding.get("table_locator") != fields.get("table_locator")
    ):
        result.issues.append(
            issue("HCM_BINDING", obs.record_locator, "Versioned snapshot/table binding required")
        )
        return result

    def physical(col: int) -> tuple[dict[str, Any], dict[str, Any]]:
        cell = fields["cells"][col]
        origin = fields["origin_cells"].get(cell.get("origin"), {})
        return cell, origin

    code_cell, code_origin = physical(binding["code_column"])
    name_cell, name_origin = physical(binding["name_column"])
    code = code_origin.get("raw_text", "")
    name = name_origin.get("raw_text", "")
    if (
        not code.strip()
        or not name.strip()
        or code_origin.get("colspan", 1) != 1
        or name_origin.get("colspan", 1) != 1
    ):
        return result  # headings/totals remain raw, never invented program identities.
    name_key = text(name).search_key
    campus = None
    geo = "unknown"
    for needle, label in [
        ("gia lai", "Gia Lai"),
        ("long an", "Long An"),
        ("vinh long", "Vĩnh Long"),
    ]:
        if needle in name_key:
            campus = text(label).model_dump()
            geo = "outside_hcm"
    if "co so chinh" in name_key or "tru so chinh" in name_key:
        campus = text("cơ sở chính").model_dump()
        geo = "hcm_source_label"
    if binding.get("campus_evidence"):
        campus_key = text(binding["campus_evidence"]["text"]).search_key
        if re.search(r"\bksa\b", campus_key) and not re.search(r"\bksv\b", campus_key):
            campus = text("KSA").model_dump()
            geo = "hcm_source_label"
        elif re.search(r"\bksv\b", campus_key) and not re.search(r"\bksa\b", campus_key):
            campus = text("KSV").model_dump()
            geo = "outside_hcm"
    degree = (
        "college" if "cao dang" in name_key or text(code).display.startswith("5") else "university"
    )
    method_raw = None
    if binding["layout"] == "history":
        _, method_origin = physical(5)
        method_raw = method_origin.get("raw_text", "")
    notes = [
        issue(
            "HCM_REVIEW_REQUIRED",
            obs.record_locator,
            "Authority/rights, offering identity, admission scope and method/scale/basis require independent review",
            blocks=False,
        )
    ]
    for item in binding["bindings"]:
        cell, original = physical(item["column"])
        raw = original.get("raw_text", "")
        loc = cell.get("origin") or obs.record_locator
        # Never carry a score through a rowspan/colspan into another program/method.
        if (
            cell.get("span_reference")
            or original.get("rowspan", 1) != 1
            or original.get("colspan", 1) != 1
        ):
            result.blocked.append(
                Blocked(
                    cell_locator=loc,
                    raw_value=raw,
                    header_path=item["header_path"],
                    admission_year=item["year"],
                    issues=[
                        issue(
                            "HCM_SCORE_SPAN", loc, "Score span requires manual applicability review"
                        )
                    ],
                )
            )
            continue
        match = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*", raw)
        numeric = number(match[1] if match else raw)
        maximum = number(match[2]).value if match else None
        if (
            numeric.status != "value"
            or numeric.operator != "eq"
            or numeric.value is None
            or numeric.value < 0
            or match
            and (maximum is None or numeric.value > maximum)
        ):
            result.blocked.append(
                Blocked(
                    value=numeric,
                    cell_locator=loc,
                    raw_value=raw,
                    header_path=item["header_path"],
                    admission_year=item["year"],
                    issues=[
                        issue(
                            "HCM_NO_EXACT_SCORE",
                            loc,
                            "Blank, marker, range or ambiguous score stays unknown",
                        )
                    ],
                )
            )
            continue
        if item["year"] not in ctx.target_years:
            continue
        method = method_raw if method_raw is not None else item["method"]
        scope = {
            "university_key": binding["school"],
            "offering_code": text(code).model_dump(),
            "program_name": text(name).model_dump(),
            "campus": campus,
            "training_mode": None,
            "degree_level": degree,
            "geo_scope": geo,
            "source_scale_max": match[2] if match else None,
            "method_namespace": f"{binding['school']}:{item['year']}",
            "source_aggregate": binding["layout"] == "ueh2025",
            "source_round": "đợt 2"
            if binding["layout"] in {"ou2025r2", "hcmue2026"}
            else "đợt 1"
            if binding["layout"] == "ou2025"
            else None,
        }
        evidence = {
            "hcm_intake": binding,
            "offering_code": {"raw_value": code, "locator": code_cell["origin"]},
            "program_name": {"raw_value": name, "locator": name_cell["origin"]},
            "source_scale_raw": raw if match else None,
        }
        result.candidates.append(
            Candidate(
                candidate_key=hashlib.sha256(
                    f"{obs.id}|{loc}|{item['year']}|{ctx.version}".encode()
                ).hexdigest(),
                fact_kind="cutoff",
                admission_year=item["year"],
                method=text(method) if method else None,
                value=numeric,
                scope=scope,
                lineage=lineage(obs, ctx, cell, item["header_path"], raw, evidence),
                issues=notes,
            )
        )
    return result
