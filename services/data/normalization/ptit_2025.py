"""Historical published value with nullable method; supporting notices remain separate."""

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
from services.data.parsers.ptit_2025 import HEADERS, URL, VERSION, key, score_reason, ttnv


def normalize_ptit_2025(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    out = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
    )
    f = obs.raw_fields
    m = f.get("ptit_2025", {})
    campus = m.get("campus")
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or obs.fact_kind != "cutoff"
        or m.get("source_url") != URL
        or m.get("snapshot_id") != str(obs.snapshot_id)
        or m.get("admission_year") != 2025
        or 2025 not in ctx.target_years
        or key(m.get("title", {}).get("raw_text", "")) != "diem trung tuyen 2025"
        or m.get("source_context") != "historical_archive_not_contemporaneous_notice"
        or m.get("publication_date", {}).get("precision") != "unknown"
        or campus not in {"BVH", "BVS"}
        or not m.get("section")
        or campus.lower() not in key(m.get("campus_evidence", {}).get("raw_text", ""))
        or m.get("table_locator") != f.get("table_locator")
        or len(f.get("cells", [])) != 5
        or [[key(h["text"]) for h in p] for p in f.get("headers", [])]
        != [[key(h)] for h in HEADERS]
    ):
        out.issues.append(
            issue(
                "PTIT2025_BINDING",
                obs.record_locator,
                "Explicit archive/year/campus/section/header required",
            )
        )
        return out
    slot = f["cells"][3]
    loc = slot.get("origin") or obs.record_locator
    raw = slot.get("raw_text") or ""
    value = number(raw)
    reason = score_reason(f)
    if reason:
        out.blocked.append(
            Blocked(
                value=value,
                cell_locator=loc,
                raw_value=raw,
                header_path=f["headers"][3],
                admission_year=2025,
                method=None,
                issues=[issue(reason, loc, "Original physical numeric value required")],
            )
        )
        return out
    predicate = ttnv(f["cells"][4], f["headers"][4])
    scope = {
        name: dict(
            raw_value=f["cells"][col]["raw_text"],
            locator=f["cells"][col]["origin"],
            header_path=f["headers"][col],
        )
        for name, col in [("program_name", 1), ("offering_code", 2)]
    }
    scope.update(
        archive={
            k: m[k]
            for k in [
                "snapshot_id",
                "snapshot_sha256",
                "source_url",
                "title",
                "admission_year",
                "publication_date",
                "source_context",
                "campus",
                "campus_evidence",
                "section",
                "table_locator",
            ]
        },
        TTNV=predicate,
        method_applicability=dict(
            status="unresolved",
            reason="Archive has one published score column without method identity; no image-backed notice row match verified",
            automatic_applicant_comparison=False,
        ),
        score_basis=dict(
            status="unresolved", canonical_scale_id=None, basis_version=None, rule_id=None
        ),
    )
    issues = [
        issue(c, loc, d, blocks=False)
        for c, d in [
            (
                "PTIT2025_METHOD_UNRESOLVED",
                "Single published archive cutoff is not nine method-specific facts or automatically raw THPT",
            ),
            (
                "PTIT2025_AUTHORITY_BASIS_SCOPE_REVIEW",
                "Source rights/authority, canonical identity, score basis, training mode and admission scope require review",
            ),
        ]
    ]
    if predicate["status"] != "source_predicate":
        issues.append(
            issue(
                "PTIT2025_TTNV_REVIEW",
                f["cells"][4].get("origin") or obs.record_locator,
                "Missing/unusual TTNV remains unresolved",
                blocks=False,
            )
        )
    out.candidates.append(
        Candidate(
            candidate_key=hashlib.sha256(
                f"{obs.id}|{loc}|published-archive-score|{ctx.transform_version}".encode()
            ).hexdigest(),
            fact_kind="cutoff",
            admission_year=2025,
            method=None,
            value=value,
            scope=dict(
                campus=text(campus).model_dump(),
                program_name=text(f["cells"][1]["raw_text"]).model_dump(),
                offering_code=text(f["cells"][2]["raw_text"]).model_dump(),
                track=text(m["section"]["text"]).model_dump(),
                language=None,
                training_mode=None,
            ),
            lineage=lineage(obs, ctx, slot, f["headers"][3], raw, scope),
            issues=issues,
        )
    )
    return out
