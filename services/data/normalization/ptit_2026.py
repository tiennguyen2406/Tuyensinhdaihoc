"""Published PTIT2026 values, not applicant-comparable or canonical scales/rules."""

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
from services.data.parsers.ptit_2026 import (
    METHODS,
    TITLE,
    URL,
    VERSION,
    cell_reason,
    header_paths,
    key,
)


def normalize_ptit_2026(obs: RawObservation, ctx: NormalizationContext) -> NormalizedObservation:
    out = NormalizedObservation(
        input_observation_id=obs.id,
        snapshot_id=obs.snapshot_id,
        normalizer_version=ctx.version,
        transform_version=ctx.transform_version,
        display_fields=strings(obs.raw_fields),
    )
    f = obs.raw_fields
    m = f.get("ptit_2026", {})
    campus = m.get("campus")
    if (
        not obs.parser_version.startswith(VERSION + "+")
        or obs.fact_kind != "cutoff"
        or m.get("source_url") != URL
        or m.get("snapshot_id") != str(obs.snapshot_id)
        or campus not in {"BVH", "BVS"}
        or m.get("table_locator") != f.get("table_locator")
        or m.get("publication_date", {}).get("value") != "2026-08-10"
        or 2026 not in ctx.target_years
        or "Chính quy" not in ctx.training_modes
        or key(m.get("title", {}).get("raw_text", "")) != key(TITLE)
        or "diem chuan trung tuyen nam 2026"
        not in key(m.get("publication", {}).get("raw_text", ""))
        or not m.get("section")
        or campus.lower() not in key(m.get("campus_evidence", {}).get("raw_text", ""))
        or len(f.get("cells", [])) != 14
        or [[key(h["text"]) for h in p] for p in f.get("headers", [])[:12]] != header_paths()
    ):
        out.issues.append(
            issue(
                "PTIT2026_BINDING",
                obs.record_locator,
                "Explicit source/year/method/campus/section/header binding required",
            )
        )
        return out
    for col, (method, (name, family, instrument, scale, _)) in enumerate(METHODS.items(), 3):
        slot = f["cells"][col]
        loc = slot.get("origin") or obs.record_locator
        raw = slot.get("raw_text") or ""
        v = number(raw)
        reason = cell_reason(f, col)
        if reason:
            out.blocked.append(
                Blocked(
                    value=v,
                    cell_locator=loc,
                    raw_value=raw,
                    header_path=f["headers"][col],
                    admission_year=2026,
                    method=method,
                    issues=[
                        issue(
                            reason,
                            loc,
                            "Original cell missing, not reported or invalid; never zero",
                        )
                    ],
                )
            )
            continue
        scope = {
            k: {
                "locator": f["cells"][i]["origin"],
                "raw_value": f["cells"][i]["raw_text"],
                "header_path": f["headers"][i],
            }
            for i, k in [(1, "program_name"), (2, "offering_code")]
        }
        scope.update(
            ptit_2026={
                k: m[k]
                for k in [
                    "snapshot_id",
                    "snapshot_sha256",
                    "source_url",
                    "title",
                    "publication",
                    "publication_date",
                    "campus",
                    "campus_evidence",
                    "section",
                    "table_locator",
                ]
            },
            score_method=dict(
                key=method,
                family=family,
                instrument=instrument,
                nominal_scale=scale,
                header_evidence=f["headers"][col],
                possible_converted_equivalent_threshold=True,
                score_basis="unresolved_published_basis",
                automatic_applicant_comparison=False,
            ),
            tie_break=m["tie_break"],
        )
        out.candidates.append(
            Candidate(
                candidate_key=hashlib.sha256(
                    f"{obs.id}|{loc}|{method}|{ctx.transform_version}".encode()
                ).hexdigest(),
                fact_kind="cutoff",
                admission_year=2026,
                method=text("PTIT 2026 — " + name),
                value=v,
                scope=dict(
                    campus=text(campus).model_dump(),
                    training_mode=text("Chính quy").model_dump(),
                    program_name=text(f["cells"][1]["raw_text"]).model_dump(),
                    offering_code=text(f["cells"][2]["raw_text"]).model_dump(),
                    track=text(m["section"]["text"]).model_dump(),
                    language=None,
                ),
                lineage=lineage(obs, ctx, slot, f["headers"][col], raw, scope),
                issues=[
                    issue(c, loc, d, blocks=False)
                    for c, d in [
                        (
                            "PTIT2026_BASIS_SCOPE_REVIEW",
                            "Published nominal scale is not approved score basis, conversion or applicant comparability",
                        ),
                        (
                            "PTIT2026_AUTHORITY_IDENTITY_REVIEW",
                            "2026 source rights/authority, entities, method instrument, round/population/conditions require review",
                        ),
                    ]
                ],
            )
        )
    return out
