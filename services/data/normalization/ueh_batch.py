"""Evidence-bound full UEH August PT6 batch; canonical identities/scope remain unknown."""

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
from services.data.parsers.ueh import URL
from services.data.parsers.ueh_batch import GROUPS, VERSION, columns, header_paths, key


def normalize_batch(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    result = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
        issues=inherited(obs, ctx),
    )
    # The batch keeps table-local failures/totals in the job, while independently
    # validated physical cells in other rows/groups remain usable as draft evidence.
    result.issues = [
        i.model_copy(update={"blocks_candidate": False})
        if i.origin == "parser"
        and (
            i.code == "UEH_BATCH_TABLE_BLOCKED"
            or i.code == "cutoff_row_without_value"
            and i.locator != obs.record_locator
        )
        else i
        for i in result.issues
    ]
    fields = obs.raw_fields
    mapping = fields.get("ueh_batch_2024", {})
    group = mapping.get("group")
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or obs.fact_kind != "cutoff"
        or group not in GROUPS
        or mapping.get("campus") != GROUPS[group]
        or mapping.get("snapshot_id") != str(obs.snapshot_id)
        or mapping.get("source_url") != URL
        or mapping.get("table_locator") != fields.get("table_locator")
        or mapping.get("publication_date", {}).get("value") != "2024-08-17"
        or 2024 not in ctx.target_years
        or "Chính quy" not in ctx.training_modes
        or not all(
            mapping.get(k)
            for k in (
                "publication",
                "method",
                "cutoff",
                "campus_evidence",
                "section",
                "combination_applicability",
            )
        )
    ):
        result.issues.append(
            issue(
                "UEH_BATCH_BINDING",
                obs.record_locator,
                "Exact August snapshot/table/group/year/method/campus evidence required",
            )
        )
        return result
    headers = fields.get("headers", [])
    cells = fields.get("cells", [])
    if len(cells) != len(header_paths(group)) or [
        [key(h["text"]) for h in p] for p in headers
    ] != header_paths(group):
        result.issues.append(
            issue(
                "UEH_BATCH_HEADER",
                obs.record_locator,
                "Exact group-specific PT6 and identity headers required",
            )
        )
        return result
    combo, col = columns(group)
    cell = cells[col]
    raw = cell.get("raw_text") or ""
    loc = cell.get("origin") or obs.record_locator
    value = number(raw)
    problems = [i for i in result.issues if i.blocks_candidate]
    if mapping.get("row_blocker"):
        problems.append(issue(mapping["row_blocker"], loc, "Source row requires review"))
    for index in (1, 2, combo, col):
        slot = cells[index]
        original = fields.get("origin_cells", {}).get(slot.get("origin"), {})
        if (
            slot.get("span_reference")
            or not original
            or original.get("rowspan") != 1
            or original.get("colspan") != 1
            or original.get("raw_text") != slot.get("raw_text")
            or not slot.get("raw_text")
        ):
            problems.append(
                issue(
                    "UEH_BATCH_PHYSICAL_CELL",
                    loc,
                    "Unspanned original code/name/combination/score required",
                )
            )
    if value.status != "value" or value.operator != "eq" or value.value is None or value.value < 0:
        problems.append(issue("UEH_BATCH_VALUE", loc, "Exact nonnegative PT6 Decimal required"))
    if problems:
        result.blocked.append(
            Blocked(
                value=value,
                cell_locator=loc,
                raw_value=raw,
                header_path=headers[col],
                admission_year=2024,
                method="UEH PT6",
                issues=problems,
            )
        )
        return result
    scope_evidence = {"ueh_batch_2024": mapping}
    for index, name in ((1, "offering_code"), (2, "program_name"), (combo, "combinations")):
        scope_evidence[name] = {
            "raw_value": cells[index]["raw_text"],
            "locator": cells[index]["origin"],
            "header_path": headers[index],
        }
    if group != "ksa_isb":
        scope_evidence["language_availability"] = [
            {
                "raw_value": s["raw_text"],
                "locator": s["origin"],
                "header_path": headers[s["column"]],
            }
            for s in cells[9:]
        ]
    result.candidates.append(
        Candidate(
            candidate_key=hashlib.sha256(
                f"{obs.id}|{loc}|{ctx.transform_version}".encode()
            ).hexdigest(),
            fact_kind="cutoff",
            admission_year=2024,
            method=text("UEH PT6 — Thi tốt nghiệp THPT năm 2024"),
            value=value,
            scope={
                "campus": text(mapping["campus"]).model_dump(),
                "training_mode": text("Chính quy").model_dump(),
                "program_name": text(cells[2]["raw_text"]).model_dump(),
                "offering_code": text(cells[1]["raw_text"]).model_dump(),
                "track": None,
                "language": None,
            },
            lineage=lineage(obs, ctx, cell, headers[col], raw, scope_evidence),
            issues=[
                issue(code, loc, detail, blocks=False)
                for code, detail in [
                    (
                        "UEH_AUTHORITY_IDENTITY_REVIEW",
                        "UEH source authority/rights and Program/Offering/PT6 identities remain unapproved",
                    ),
                    (
                        "SCORE_SCALE_BASIS_UNCONFIRMED",
                        "Source notes are evidence, not canonical scale/basis or an executable formula",
                    ),
                    (
                        "SCOPE_COMPONENTS_UNRESOLVED",
                        "August notice is not inferred Round1; population/conditions/combination aggregate remain unresolved",
                    ),
                ]
            ],
        )
    )
    return result
