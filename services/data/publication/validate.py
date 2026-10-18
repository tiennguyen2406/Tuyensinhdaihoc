"""Cutoff-specific publication gates, independent from aggregate T07 resolution status."""

from decimal import Decimal
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from services.api.db.models import audit_events
from services.api.db.validators import decimal_value, record, validate_admission, validate_source
from services.data.normalization.store import digest
from services.data.publication.contract import (
    ReviewCommand,
    ValidatedDraft,
    fingerprint,
    json_value,
)
from services.data.resolution.store import validate_targets


def environment_digest(c: Connection, cmd: ReviewCommand, packet: dict[str, Any]) -> str:
    f = cmd.fact
    if f is None or f.score_scale_id is None:
        raise ValueError("Cutoff and scale required")
    offering = record(c, "program_years", f.program_year_id)
    scale = record(c, "score_scales", f.score_scale_id)
    rows = [
        record(c, "universities", f.university_id),
        offering,
        record(c, "programs", offering["program_id"]),
        record(c, "admission_methods", f.method_id),
        scale,
        record(c, "sources", UUID(packet["source_id"])),
    ]
    snap = record(c, "source_snapshots", scale["primary_snapshot_id"])
    rows.append(record(c, "sources", snap["source_id"]))
    if f.scoring_rule_id:
        rows.append(record(c, "scoring_rules", f.scoring_rule_id))
    # Freeze every supporting evidence authority, not just primary/basis authority.
    for source_id in sorted(
        {
            record(c, "source_snapshots", UUID(ref[9:].split("#", 1)[0]))["source_id"]
            for refs in f.evidence.values()
            for ref in refs
        },
        key=str,
    ):
        rows.append(record(c, "sources", source_id))
    return digest(rows)


def active_source_review(c: Connection, source_id: UUID) -> None:
    from services.data.publication.review import ReviewService

    source = record(c, "sources", source_id)
    events = c.execute(
        sa.select(audit_events).where(
            audit_events.c.entity_kind == "source",
            audit_events.c.entity_id == source_id,
            audit_events.c.action == "bootstrap_link",
        )
    ).mappings()
    for event in events:
        after = event["after_data"]
        decision = UUID(after["decision_id"])
        job = record(c, "ingest_jobs", decision)
        if (
            job["status"] == "succeeded"
            and not ReviewService(c).revoked(decision)
            and all(json_value(source[k]) == v for k, v in after["row"].items())
        ):
            return
    raise ValueError("Active reviewed source authority required")


def build_draft(
    c: Connection, cmd: ReviewCommand, decision_id: UUID, actor: str, packet: dict[str, Any]
) -> ValidatedDraft:
    from services.data.publication.review import ReviewService

    svc = ReviewService(c)
    reg = svc.versions(cmd, packet)
    validate_targets(c, reg)
    if (packet["registry_version"], packet["alias_version"]) != (reg.version, reg.alias_version):
        raise ValueError("Run new resolution after registry bootstrap before fact review")
    if packet["candidate"]["fact_kind"] != "cutoff" or cmd.fact is None:
        raise ValueError(
            "Only reviewed cutoff publication supported; tuition academic year is not admission year"
        )
    f = cmd.fact
    candidate = packet["candidate"]
    if f.score_scale_id is None or not f.basis_version or not f.round_key or not f.population_key:
        raise ValueError("Known scale/basis/round/population required")
    if (
        not f.conditions
        or f.conditions.get("schema_version") != "conditions/1"
        or f.conditions.get("kind") not in {"none", "predicate"}
        or not f.condition_text
    ):
        raise ValueError("Explicit reviewed conditions required; unknown is not none")
    keys = {"schema_version", "kind"}
    if f.conditions["kind"] == "predicate":
        keys.add("expression")
        expression = f.conditions.get("expression")
        if not isinstance(expression, dict) or not expression:
            raise ValueError("Reviewed canonical predicate expression required")
    if set(f.conditions) != keys:
        raise ValueError("Unsupported canonical condition fields/version")
    if f.combination_status == "unknown" or (f.combination_status == "specified") != (
        f.combination_id is not None
    ):
        raise ValueError("Combination or explicit confirmed-none evidence required")
    required = {
        "year",
        "program",
        "method",
        "scale",
        "basis",
        "combination",
        "round",
        "population",
        "conditions",
        "publication",
        "score",
    }
    if f.combination_status == "source_aggregate":
        required.add("combination_aggregation")
        if f.scoring_rule_id is not None:
            raise ValueError("Aggregate scope cannot use a combination-specific scoring rule")
    if f.supersedes_cutoff_id or f.replaces_scope_id:
        required.add("correction")
    if not required.issubset(f.evidence) or any(not f.evidence[k] for k in required):
        raise ValueError("Reviewed field-level evidence required")
    exact = "snapshot:" + packet["snapshot_id"] + "#" + packet["evidence"]["locator"]
    if exact not in f.evidence["score"]:
        raise ValueError("Score requires the original cell locator")
    offering = record(c, "program_years", f.program_year_id)
    if (
        offering["university_id"] != f.university_id
        or offering["admission_year"] != f.admission_year
        or f.admission_year != candidate["admission_year"]
    ):
        raise ValueError("University/offering/year mismatch")
    for kind, identifier in [
        ("university", f.university_id),
        ("offering", f.program_year_id),
        ("method", f.method_id),
    ]:
        matched = [
            e
            for e in reg.entities
            if e.kind == kind and e.canonical_id == identifier and e.review.status == "approved"
        ]
        if len(matched) != 1:
            raise ValueError("Approved registry identity required")
        if any(
            svc.revoked(UUID(v[9:]))
            for v in matched[0].review.evidence
            if v.startswith("decision:")
        ):
            raise ValueError("Registry identity approval revoked")
    entry = next(e for e in reg.entities if e.canonical_id == f.program_year_id)
    for key in ["campus", "language", "track", "training_mode"]:
        known = (candidate["scope"].get(key) or {}).get("display")
        if known is not None and entry.attributes.get(key) != known:
            raise ValueError("Offering context mismatch")
    if offering["offering_code"] != (candidate["scope"].get("offering_code") or {}).get("display"):
        raise ValueError("Offering code system/scope not confirmed")
    method = next(e for e in reg.entities if e.kind == "method" and e.canonical_id == f.method_id)
    label = (candidate.get("method") or {}).get("display")
    if not label or method.name != label:
        aliases = [
            a
            for a in reg.aliases
            if a.target == method.key
            and a.value == label
            and a.review.status == "approved"
            and (a.from_year is None or a.from_year <= f.admission_year)
            and (a.to_year is None or a.to_year >= f.admission_year)
        ]
        if not aliases:
            raise ValueError("Source method semantics not approved")
    if method.attributes.get("admission_year") not in {None, f.admission_year}:
        raise ValueError("Method year mismatch")
    score = decimal_value(f.score, 5)
    value = candidate["value"]
    if (
        value["status"] != "value"
        or value["operator"] != "eq"
        or value["value"] is None
        or score != Decimal(value["value"])
    ):
        raise ValueError("Score differs from normalized cell; repair upstream with evidence first")
    scale = record(c, "score_scales", f.score_scale_id)
    if (
        scale["admission_year"] != f.admission_year
        or scale["method_id"] != f.method_id
        or not scale["min_score"] <= score <= scale["max_score"]
    ):
        raise ValueError("Scale/year/method/bounds mismatch")
    scale_audits = (
        c.execute(
            sa.select(audit_events).where(
                audit_events.c.entity_kind == "scale",
                audit_events.c.entity_id == f.score_scale_id,
                audit_events.c.action.in_(["bootstrap_create", "bootstrap_link"]),
            )
        )
        .mappings()
        .all()
    )
    approved = False
    for a in scale_audits:
        decision = UUID(a["after_data"]["decision_id"])
        row = record(c, "ingest_jobs", decision)
        if (
            row["status"] == "succeeded"
            and not svc.revoked(decision)
            and all(json_value(scale[k]) == v for k, v in a["after_data"]["row"].items())
        ):
            approved = True
    if not approved:
        raise ValueError("Verified scale/basis review required")
    source_ids = {UUID(packet["source_id"])}
    for field in sorted(required):
        for evidence in f.evidence[field]:
            if not evidence.startswith("snapshot:") or "#" not in evidence:
                raise ValueError("Snapshot/locator evidence required")
            sid, locator = evidence[9:].split("#", 1)
            if not locator.strip():
                raise ValueError("Evidence locator required")
            snapshot = record(c, "source_snapshots", UUID(sid))
            source = record(c, "sources", snapshot["source_id"])
            permitted = (
                ["cutoff"]
                if field in {"score", "publication", "correction"}
                else ["cutoff", "scoring_rule"]
                if field in {"scale", "basis", "combination_aggregation"}
                else ["cutoff", "catalog"]
            )
            evidence_kind = next(
                (k for k in permitted if k in source["authority_scope"].get("fact_kinds", [])), None
            )
            if evidence_kind is None:
                raise ValueError("Source authority does not cover this evidence field")
            validate_source(c, UUID(sid), offering, evidence_kind, method_id=f.method_id)
            source_ids.add(snapshot["source_id"])
    validate_source(c, UUID(packet["snapshot_id"]), offering, "cutoff", method_id=f.method_id)
    validate_source(
        c, scale["primary_snapshot_id"], offering, "scoring_rule", method_id=f.method_id
    )
    source_ids.add(record(c, "source_snapshots", scale["primary_snapshot_id"])["source_id"])
    for source_id in source_ids:
        active_source_review(c, source_id)
    dsl = dict(
        schema_version="publication-scope/1",
        conditions=f.conditions,
        combination_status=f.combination_status,
        basis_version=f.basis_version,
        score_scale_id=str(f.score_scale_id),
    )
    if f.combination_status == "source_aggregate":
        dsl["aggregation_basis"] = "same_cutoff_across_offering_admissible_combinations"
    scope = dict(
        program_year_id=f.program_year_id,
        method_id=f.method_id,
        combination_id=f.combination_id,
        round_key=f.round_key,
        population_key=f.population_key,
        condition_key=fingerprint(dsl),
        condition_text=f.condition_text,
        condition_dsl=dsl,
        score_scale_id=f.score_scale_id,
        scoring_rule_id=f.scoring_rule_id,
        data_status="published",
        primary_snapshot_id=UUID(packet["snapshot_id"]),
    )
    validate_admission(c, scope)
    identity = json_value(
        dict(
            schema_version="admission-identity/1",
            university_id=f.university_id,
            admission_year=f.admission_year,
            **{
                k: scope[k]
                for k in [
                    "program_year_id",
                    "method_id",
                    "combination_id",
                    "round_key",
                    "population_key",
                    "condition_key",
                ]
            },
        )
    )
    payload = json_value(
        dict(
            schema_version="canonical-cutoff/1",
            identity=identity,
            score=score,
            scale_id=f.score_scale_id,
            scale_code=scale["code"],
            exam_version=scale["exam_version"],
            max_score=scale["max_score"],
            min_score=scale["min_score"],
            basis_version=f.basis_version,
            conditions=dsl,
            scoring_rule_id=f.scoring_rule_id,
            publication_status="published",
        )
    )
    return ValidatedDraft(
        decision_id=decision_id,
        decision_sha256=digest(cmd.model_dump(mode="json")),
        actor_id=actor,
        packet_sha256=packet["packet_sha256"],
        scope=scope,
        identity=identity,
        payload=payload,
        fact=f,
        snapshot_id=UUID(packet["snapshot_id"]),
        primary_observation_id=UUID(packet["raw_observation_id"]),
        computation_status="unavailable_aggregate_scope"
        if f.combination_status == "source_aggregate"
        else "rule_available_not_evaluated"
        if f.scoring_rule_id
        else "unavailable_rule",
    )
