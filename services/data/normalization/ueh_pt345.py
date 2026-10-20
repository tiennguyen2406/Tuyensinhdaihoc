"""Independent PT3/PT4/PT5 cells. No inferred scales, PT6 combinations or rules."""

import hashlib

from services.data.normalization.contract import (
    Blocked,
    Candidate,
    NormalizationContext,
    NormalizedObservation,
    RawObservation,
)
from services.data.normalization.normalize import issue, lineage, strings
from services.data.normalization.values import number, text
from services.data.parsers.ueh import URL
from services.data.parsers.ueh_batch import GROUPS, header_paths, key
from services.data.parsers.ueh_pt345 import (
    DEFINITIONS,
    METHODS,
    VERSION,
    cell_reason,
    method_columns,
)


def normalize_pt345(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    result = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
    )
    f = obs.raw_fields
    m = f.get("ueh_pt345_2024", {})
    group = m.get("group")
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or obs.fact_kind != "cutoff"
        or group not in GROUPS
        or m.get("campus") != GROUPS[group]
        or m.get("snapshot_id") != str(obs.snapshot_id)
        or m.get("source_url") != URL
        or m.get("table_locator") != f.get("table_locator")
        or m.get("publication_date", {}).get("value") != "2024-08-17"
        or 2024 not in ctx.target_years
        or "Chính quy" not in ctx.training_modes
        or not all(
            m.get(k)
            for k in [
                "publication",
                "cutoff",
                "campus_evidence",
                "section",
                "early_admission_context",
            ]
        )
    ):
        result.issues.append(
            issue(
                "UEH_PT345_BINDING",
                obs.record_locator,
                "Explicit August2024 source/section/campus/early-method evidence required",
            )
        )
        return result
    headers, cells = f.get("headers", []), f.get("cells", [])
    if len(cells) != len(header_paths(group)) or [
        [key(h["text"]) for h in p] for p in headers
    ] != header_paths(group):
        result.issues.append(
            issue(
                "UEH_PT345_HEADER", obs.record_locator, "Exact method and identity headers required"
            )
        )
        return result
    early_text = m["early_admission_context"].get("raw_text", "")
    if (
        not key(m["publication"]["raw_text"]).endswith("nam 2024 cua cac phuong thuc:")
        or not key(early_text).startswith("– cac phuong thuc xet tuyen som (")
        or "20/6/2024" not in early_text
        or "09/7/2024" not in early_text
    ):
        result.issues.append(
            issue("UEH_PT345_YEAR", obs.record_locator, "Explicit source2024 required")
        )
        return result
    for method, col in method_columns(group).items():
        slot = cells[col]
        loc, raw = slot.get("origin") or obs.record_locator, slot.get("raw_text") or ""
        value = number(raw)
        definition = m.get("method_definitions", {}).get(method)
        expected = f"– phuong thuc {method[-1]} ({method.lower()}): {DEFINITIONS[method]}"
        reason = (
            "METHOD_CONTEXT_REQUIRED"
            if not definition or key(definition["raw_text"]) != expected
            else cell_reason(f, col)
        )
        if reason:
            result.blocked.append(
                Blocked(
                    value=value,
                    cell_locator=loc,
                    raw_value=raw,
                    header_path=headers[col],
                    admission_year=2024,
                    method=method,
                    issues=[issue(reason, loc, "Independent method-score cell requires review")],
                )
            )
            continue
        scope_evidence = {
            "ueh_pt345_2024": {
                k: m[k]
                for k in [
                    "snapshot_id",
                    "snapshot_sha256",
                    "source_url",
                    "publication_date",
                    "publication",
                    "group",
                    "campus",
                    "campus_evidence",
                    "section",
                    "table_locator",
                ]
            },
            "method_definition": definition,
            "early_admission_context": m["early_admission_context"],
        }
        for index, name in [(1, "offering_code"), (2, "program_name")]:
            scope_evidence[name] = {
                "raw_value": cells[index]["raw_text"],
                "locator": cells[index]["origin"],
                "header_path": headers[index],
            }
        scoped = obs.model_copy(
            update={
                "raw_fields": f
                | {
                    "context": [
                        m["publication"],
                        definition,
                        m["cutoff"],
                        m["campus_evidence"],
                        m["early_admission_context"],
                    ],
                    "footnotes": [],
                }
            }
        )
        result.candidates.append(
            Candidate(
                candidate_key=hashlib.sha256(
                    f"{obs.id}|{loc}|{method}|{ctx.transform_version}".encode()
                ).hexdigest(),
                fact_kind="cutoff",
                admission_year=2024,
                method=text(METHODS[method]),
                value=value,
                scope={
                    "campus": text(m["campus"]).model_dump(),
                    "training_mode": text("Chính quy").model_dump(),
                    "program_name": text(cells[2]["raw_text"]).model_dump(),
                    "offering_code": text(cells[1]["raw_text"]).model_dump(),
                    "track": None,
                    "language": None,
                },
                lineage=lineage(scoped, ctx, slot, headers[col], raw, scope_evidence),
                issues=[
                    issue(code, loc, detail, blocks=False)
                    for code, detail in [
                        (
                            "UEH_IDENTITY_AUTHORITY_REVIEW",
                            "Source authority/rights and canonical entities remain unapproved",
                        ),
                        (
                            "SCORE_SCALE_BASIS_UNCONFIRMED",
                            "Method-specific published numeric basis, no conversion or approved scale inferred",
                        ),
                        (
                            "EARLY_ADMISSION_SCOPE_REVIEW",
                            "Earlier results republished in August; round/population/conditions unresolved, no new round inferred",
                        ),
                    ]
                ],
            )
        )
    return result
