"""Envelope adapter. Source-specific proposals never become canonical by generation."""

from urllib.parse import urlsplit

from services.data.normalization.store import digest
from services.data.resolution.contract import (
    CandidateResolution,
    EntityMatch,
    EntityQuery,
    EntityResolution,
    ResolutionInput,
    State,
)
from services.data.resolution.matching import match
from services.data.resolution.registry import EntityRegistry


def propose_registry(seed: EntityRegistry, inputs: list[ResolutionInput]) -> EntityRegistry:
    if seed.classification != "pilot_pending":
        return seed
    value = seed.frozen()
    existing = {e.key for e in seed.entities}
    for source in inputs:
        owners = [
            e
            for e in seed.entities
            if e.kind == "university" and urlsplit(source.final_url).hostname in e.domains
        ]
        if len(owners) != 1:
            continue
        owner = owners[0]
        for c in source.envelope.candidates:
            if c.fact_kind != "cutoff" or c.admission_year is None:
                continue
            name = (c.scope.get("program_name") or {}).get("display")
            code = (c.scope.get("offering_code") or {}).get("display")
            if not name or not code:
                continue
            attrs = {
                k: (c.scope.get(k) or {}).get("display")
                for k in ["campus", "language", "track", "training_mode"]
            }
            attrs["admission_year"] = c.admission_year
            token = digest([owner.key, name, code, attrs])[:24]
            pk = "proposal:program:" + token
            ok = "proposal:offering:" + token
            evidence = [
                f"envelope:{source.envelope_id}/candidate:{c.candidate_key}",
                f"snapshot:{c.lineage.snapshot_id}#{c.lineage.cell_locator}",
                f"raw-observation:{c.lineage.observation_id}",
            ]
            review = {"status": "pending", "evidence": evidence}
            if pk not in existing:
                value["entities"].append(
                    dict(
                        key=pk,
                        kind="program",
                        name=name,
                        university_key=owner.key,
                        attributes=attrs,
                        review=review,
                    )
                )
                value["entities"].append(
                    dict(
                        key=ok,
                        kind="offering",
                        name=name,
                        university_key=owner.key,
                        program_key=pk,
                        attributes=attrs,
                        codes=[
                            {
                                "system": "ptit:table-program-label",
                                "value": code,
                                "from_year": c.admission_year,
                                "to_year": c.admission_year,
                                "evidence": evidence,
                            }
                        ],
                        review=review,
                    )
                )
                existing.update([pk, ok])
    return EntityRegistry.model_validate(value)


def suggestion(result: EntityMatch) -> str | None:
    if result.entity_key:
        return result.entity_key
    # A unique strongest deterministic suggestion restricts review candidates only.
    # A fuzzy parent or ambiguous identity never authorizes a downstream auto-link.
    if result.status == "ambiguous":
        return None
    eligible = [o for o in result.options if o.eligible]
    if not eligible or eligible[0].method == "fuzzy_suggestion":
        return None
    best = eligible[0].method
    peers = [o for o in eligible if o.method == best]
    return peers[0].entity_key if len(peers) == 1 else None


def resolve(
    normalized_observation: ResolutionInput, entity_registry: EntityRegistry
) -> EntityResolution:
    source = normalized_observation
    env = source.envelope
    if (
        env.schema_version != "normalization-envelope/1"
        or not env.transform_version.startswith("normalization/1;")
        or ";resolver=none;" not in env.transform_version
    ):
        raise ValueError(
            "Resolver requires original normalization envelope, not raw/resolver output"
        )
    if len({c.candidate_key for c in env.candidates}) != len(env.candidates):
        raise ValueError("Duplicate input candidate key")
    results = []
    for c in env.candidates:
        if (
            c.lineage.observation_id != env.input_observation_id
            or c.lineage.snapshot_id != env.snapshot_id
            or c.lineage.source_id != source.source_id
            or c.lineage.normalizer_version != env.normalizer_version
        ):
            raise ValueError("Candidate lineage mismatch")
        attrs = {
            k: (c.scope.get(k) or {}).get("display")
            for k in ["campus", "language", "track", "training_mode"]
        }
        attrs["admission_year"] = c.admission_year
        host = urlsplit(source.final_url).hostname
        has_campus_code = any(
            e.kind == "university"
            and host in e.domains
            and any(code.system == "ptit:campus-admission-label" for code in e.codes)
            for e in entity_registry.entities
        )
        queries = {
            "university": EntityQuery(
                kind="university",
                domain=host,
                code=attrs["campus"] if has_campus_code else None,
                code_system="ptit:campus-admission-label" if has_campus_code else None,
                attributes=attrs,
            )
        }
        matches = {"university": match(queries["university"], entity_registry)}
        owner = suggestion(matches["university"])
        name = (c.scope.get("program_name") or {}).get("display")
        queries["program"] = EntityQuery(
            kind="program", name=name, university_key=owner, attributes=attrs
        )
        matches["program"] = (
            match(
                queries["program"],
                entity_registry,
                allow_link=matches["university"].status == "resolved",
            )
            if c.fact_kind == "cutoff"
            else EntityMatch(kind="program", reasons=["TUITION_GROUP_NOT_A_PROGRAM"])
        )
        pk = suggestion(matches["program"])
        queries["offering"] = EntityQuery(
            kind="offering",
            name=name,
            code=(c.scope.get("offering_code") or {}).get("display"),
            code_system="ptit:table-program-label",
            university_key=owner,
            program_key=pk,
            attributes=attrs,
        )
        matches["offering"] = (
            match(
                queries["offering"],
                entity_registry,
                allow_link=matches["university"].status == matches["program"].status == "resolved",
            )
            if c.fact_kind == "cutoff"
            else EntityMatch(kind="offering", reasons=["TUITION_GROUP_NOT_OFFERING"])
        )
        queries["method"] = EntityQuery(
            kind="method",
            name=c.method.display if c.method else None,
            university_key=owner,
            attributes=attrs,
        )
        matches["method"] = (
            match(
                queries["method"],
                entity_registry,
                allow_link=matches["university"].status == "resolved",
            )
            if c.method
            else EntityMatch(kind="method", reasons=["METHOD_NOT_STATED"])
        )
        # Source programme/admission code is NOT a major taxonomy code.
        queries["major"] = EntityQuery(kind="major")
        matches["major"] = EntityMatch(kind="major", reasons=["TAXONOMY_CODE_SYSTEM_NOT_EVIDENCED"])
        queries["scope"] = EntityQuery(
            kind="scope", university_key=owner, program_key=pk, attributes=attrs
        )
        matches["scope"] = EntityMatch(
            kind="scope", reasons=["ROUND_POPULATION_CONDITIONS_BASIS_UNRESOLVED"]
        )
        states = [m.status for m in matches.values()]
        state: State = (
            "ambiguous"
            if "ambiguous" in states
            else "resolved"
            if all(s == "resolved" for s in states)
            else "partial"
            if "resolved" in states
            else "unresolved"
        )
        deps = sorted(
            {d for m in matches.values() for o in m.options for d in [o.entity_key, *o.alias_keys]}
        )
        deps = sorted(set(deps) | {key for m in matches.values() for key in m.blocked_entities})
        blockers = [
            "T07_NOT_PUBLICATION",
            "FACT_UNVERIFIED",
            "SCALE_RULE_PRIORITY_UNRESOLVED",
            "SCOPE_COMPONENTS_UNRESOLVED",
        ] + [i.code for i in c.issues]
        if c.fact_kind == "tuition":
            blockers.append("TUITION_GROUP_NOT_OFFERING")
        results.append(
            CandidateResolution(
                candidate_key=c.candidate_key,
                input_envelope_id=source.envelope_id,
                raw_observation_id=c.lineage.observation_id,
                snapshot_id=c.lineage.snapshot_id,
                lineage=c.lineage.model_dump(mode="json"),
                fact_kind=c.fact_kind,
                admission_year=c.admission_year,
                academic_year=c.academic_year,
                status=state,
                entities=matches,
                dependencies=deps,
                preserved_input_issues=[i.model_dump(mode="json") for i in c.issues],
                queries=queries,
                unresolved_fields={
                    k: getattr(c, k, None)
                    for k in [
                        "score_scale",
                        "round",
                        "population",
                        "conditions",
                        "combinations",
                        "scoring_rule",
                        "priority",
                        "basis",
                    ]
                },
                publication_blockers=sorted(set(blockers)),
            )
        )
    return EntityResolution(
        input_envelope_id=source.envelope_id,
        normalizer_namespace=env.transform_version,
        registry_version=entity_registry.version,
        alias_version=entity_registry.alias_version,
        candidates=results,
        blocked_input_attempts=len(env.blocked),
        input_issue_count=len(env.issues),
    )
