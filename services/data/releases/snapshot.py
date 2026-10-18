"""All release inputs are read in one caller-owned REPEATABLE READ snapshot."""

from collections import Counter
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from services.api.db.models import metadata
from services.api.db.validators import TARGET_YEARS, count_canonical_cutoffs, record
from services.data.publication.contract import json_value

SCHEMA = "canonical-release/1"
BUILDER = "release-builder/1.0.0"
FILTER = {
    "years": list(TARGET_YEARS),
    "is_current": True,
    "verification_status": "verified",
    "scope_data_status": "published",
}


def coverage(records: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = {
        "university": lambda r: (r["university"]["id"], r["university"]["name"]),
        "year": lambda r: (r["offering"]["admission_year"], None),
        "method": lambda r: (r["method"]["id"], r["method"]["code"]),
        "campus": lambda r: (r["offering"]["campus_code"], None),
        "program": lambda r: (r["program"]["id"], r["program"]["program_name"]),
        "offering": lambda r: (r["offering"]["id"], r["offering"]["offering_name"]),
    }
    counts = {
        key: [
            dict(key=k, label=label, cutoff_count=n)
            for (k, label), n in sorted(Counter(fn(r) for r in records).items(), key=str)
        ]
        for key, fn in dimensions.items()
    }
    return dict(
        canonical_cutoffs=len(records),
        publication_groups=len({r["cutoff"]["publication_group_key"] for r in records}),
        revisions=len({(r["cutoff"]["id"], r["cutoff"]["revision"]) for r in records}),
        evidence_count=sum(len(r["evidence"]) for r in records),
        by=counts,
        entities={
            k: len(v)
            for k, v in counts.items()
            if k in {"university", "program", "offering", "method"}
        },
        missing_fact_counts={
            "major": sum(r["major"] is None for r in records),
            "track": sum(r["unknown"]["track"] is None for r in records),
            "language": sum(r["unknown"]["language"] is None for r in records),
            "scoring_rule": sum(r["scoring_rule"] is None for r in records),
        },
        computation=dict(sorted(Counter(r["computation_status"] for r in records).items())),
        years_without_verified_data=[
            y
            for y in TARGET_YEARS
            if not any(r["offering"]["admission_year"] == y for r in records)
        ],
        missing_year_meaning="not_collected_or_not_verified; not evidence of no admissions",
        quota=dict(target=20000, achieved=len(records), remaining=max(0, 20000 - len(records))),
        limitations=[
            "internal_smoke_release",
            "incomplete_source_and_scope_coverage",
            "source_aggregate_not_expanded",
            "no_score_or_conversion_evaluation",
            "no_admission_guarantee",
            "not_phase1_or_multisource_acceptance",
        ],
    )


def capture(c: Connection) -> dict[str, Any]:
    if c.get_isolation_level() != "REPEATABLE READ":
        raise ValueError("Release capture requires REPEATABLE READ")
    if c.scalar(sa.text("SHOW transaction_read_only")) != "on":
        raise ValueError("Release capture requires read-only transaction")
    cat = dict(c.execute(sa.select(metadata.tables["catalog_state"])).mappings().one())
    sql_count = count_canonical_cutoffs(c)
    t = metadata.tables
    cut, scope, off = (t[n] for n in ("cutoff_scores", "program_admissions", "program_years"))
    selected = (
        c.execute(
            sa.select(cut)
            .select_from(cut.join(scope).join(off))
            .where(
                cut.c.is_current.is_(True),
                cut.c.verification_status == "verified",
                scope.c.data_status == "published",
                off.c.admission_year.in_(TARGET_YEARS),
            )
            .order_by(cut.c.id)
        )
        .mappings()
        .all()
    )
    cache: dict[tuple[str, str], dict[str, Any]] = {}

    def get(table: str, ident: Any) -> dict[str, Any]:
        key = table, str(ident)
        if key not in cache:
            cache[key] = dict(record(c, table, ident))
        return cache[key]

    records = []
    for row in selected:
        cutoff = {k: v for k, v in row.items() if k not in {"reviewed_by", "review_reason"}}
        admission = get("program_admissions", row["program_admission_id"])
        offering = get("program_years", admission["program_year_id"])
        program = get("programs", offering["program_id"])
        scale = get("score_scales", row["score_scale_id"])
        rule = (
            get("scoring_rules", admission["scoring_rule_id"])
            if admission["scoring_rule_id"]
            else None
        )
        refs: set[UUID] = {
            row["primary_snapshot_id"],
            offering["primary_snapshot_id"],
            scale["primary_snapshot_id"],
        }
        if rule:
            refs.add(rule["primary_snapshot_id"])
        evidence = []
        lineage: dict[str, Any] = {}
        decisions: dict[str, Any] = {}
        jobs: dict[str, Any] = {}

        def trace(ident: Any) -> None:
            if str(ident) in lineage:
                return
            obs = get("observations", ident)
            refs.add(obs["snapshot_id"])
            lineage[str(ident)] = {
                k: obs[k]
                for k in [
                    "id",
                    "snapshot_id",
                    "record_locator",
                    "parser_version",
                    "transform_version",
                    "payload_hash",
                    "extraction_method",
                    "verification_status",
                ]
            }
            norm, raw = obs["normalized_fields"], obs["raw_fields"]
            extraction = raw.get("_extraction", {})
            if extraction:
                lineage[str(ident)]["parser_provenance"] = {
                    k: extraction[k]
                    for k in [
                        "parse_job_id",
                        "implementation_sha256",
                        "implementation_version",
                        "profile_sha256",
                        "lock_sha256",
                        "source_id",
                    ]
                    if k in extraction
                }
            for field in ["raw_observation_id", "input_envelope_id"]:
                parent = norm.get(field) or raw.get(field)
                if parent:
                    lineage[str(ident)][field] = parent
                    trace(UUID(parent))
            decision_id = norm.get("review_decision_id")
            if decision_id:
                payload = get("ingest_jobs", UUID(decision_id))["payload"]
                cmd = payload["command"]
                evidence_refs = cmd["fact"]["evidence"]
                decisions[decision_id] = dict(
                    id=decision_id,
                    command_sha256=payload["command_sha256"],
                    environment_sha256=payload["environment_sha256"],
                    binding=cmd["binding"],
                    registry_version=cmd["expected_registry_version"],
                    alias_version=cmd["expected_alias_version"],
                    field_evidence=evidence_refs,
                )
                for values in evidence_refs.values():
                    for value in values:
                        if value.startswith("snapshot:"):
                            refs.add(UUID(value.removeprefix("snapshot:").split("#", 1)[0]))
                trace(UUID(cmd["binding"]["resolution_id"]))
            normalization_job = raw.get("normalization_job_id")
            if normalization_job:
                job = get("ingest_jobs", UUID(normalization_job))
                jobs[str(job["id"])] = job_provenance(job)
                if norm.get("registry_version"):
                    manifest_jobs = (
                        c.execute(
                            sa.select(t["ingest_jobs"]).where(
                                t["ingest_jobs"].c.job_type == "resolve_entities",
                                t["ingest_jobs"].c.payload["normalization_job_id"].astext
                                == normalization_job,
                                t["ingest_jobs"].c.payload["registry_version"].astext
                                == norm["registry_version"],
                                t["ingest_jobs"].c.payload["alias_version"].astext
                                == norm["alias_version"],
                            )
                        )
                        .mappings()
                        .all()
                    )
                    if len(manifest_jobs) != 1:
                        raise ValueError("Unique frozen resolution provenance required")
                    jobs[str(manifest_jobs[0]["id"])] = job_provenance(dict(manifest_jobs[0]))

        ev = t["cutoff_evidence"]
        for e in c.execute(
            sa.select(ev).where(ev.c.cutoff_id == row["id"]).order_by(ev.c.observation_id)
        ).mappings():
            evidence.append(dict(e))
            trace(e["observation_id"])
        snapshots = []
        for sid in sorted(refs, key=str):
            snap = get("source_snapshots", sid)
            source = get("sources", snap["source_id"])
            snapshots.append(
                dict(
                    snapshot={k: v for k, v in snap.items() if k != "raw_uri"},
                    source={
                        k: source[k]
                        for k in [
                            "id",
                            "canonical_url",
                            "publisher",
                            "domain",
                            "source_type",
                            "authority_scope",
                            "verification_status",
                        ]
                    },
                )
            )
        combination = (
            get("combinations", admission["combination_id"])
            if admission["combination_id"]
            else None
        )
        subjects = []
        if combination:
            cs = t["combination_subjects"]
            for s in c.execute(
                sa.select(cs)
                .where(cs.c.combination_id == combination["id"])
                .order_by(cs.c.subject_id)
            ).mappings():
                subjects.append(dict(s) | {"subject": get("subjects", s["subject_id"])})
        aggregate = admission["condition_dsl"].get("combination_status") == "source_aggregate"
        records.append(
            dict(
                cutoff=cutoff,
                scope=admission,
                offering=offering,
                program=program,
                university=get("universities", offering["university_id"]),
                major=get("majors", program["major_id"]) if program["major_id"] else None,
                method=get("admission_methods", admission["method_id"]),
                scale=scale,
                scoring_rule=rule,
                combination=combination,
                combination_subjects=subjects,
                unknown={
                    k: None
                    if offering[f"{k}_code"] in (None, "UNSPECIFIED")
                    else offering[f"{k}_code"]
                    for k in ["track", "language"]
                },
                computation_status="unavailable_aggregate_scope"
                if aggregate
                else "rule_available_not_evaluated"
                if rule
                else "unavailable_rule",
                evidence=evidence,
                source_references=snapshots,
                lineage=dict(
                    observations=[lineage[k] for k in sorted(lineage)],
                    decisions=[decisions[k] for k in sorted(decisions)],
                    jobs=[jobs[k] for k in sorted(jobs)],
                ),
            )
        )
    frozen = json_value(records)
    if sql_count != len({r["cutoff"]["id"] for r in frozen}):
        raise ValueError("SQL/export canonical count mismatch")
    return dict(
        schema_version=SCHEMA,
        catalog_version=cat["dataset_version"],
        catalog_changed_at=json_value(cat["changed_at"]),
        filters=FILTER,
        records=frozen,
        coverage=coverage(frozen),
    )


def job_provenance(job: dict[str, Any]) -> dict[str, Any]:
    p = job["payload"]
    return dict(
        id=str(job["id"]),
        job_type=job["job_type"],
        signature={
            k: v
            for k, v in p.items()
            if k.endswith(("sha256", "version", "namespace"))
            or k in {"git_commit", "git_commit_at_execution", "working_tree_dirty"}
        },
    )
