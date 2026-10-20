"""Read-only, packet-supported pending proposal integration into an exact registry head."""

from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy.engine import Connection

from services.api.db.validators import record
from services.data.normalization.store import digest
from services.data.publication.contract import (
    Binding,
    BootstrapOperation,
    ProposalIntegration,
    ReviewCommand,
)
from services.data.publication.packets import binding_for, checked_packets
from services.data.resolution.matching import exact
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.resolve import table_program_code_system
from services.data.resolution.store import validate_targets


def supported_keys(packet: dict[str, Any], registry: EntityRegistry) -> set[str]:
    """Exact source context only; resolver fuzzy suggestions are never import evidence."""
    candidate = packet["candidate"]
    host = urlsplit(packet["evidence"]["final_url"]).hostname
    owners = [e for e in registry.entities if e.kind == "university" and host in e.domains]
    if len(owners) != 1:
        raise ValueError("Integration requires one exact source owner")
    owner = owners[0]
    system = table_program_code_system(owner)
    if system is None:
        raise ValueError("Integration source-specific code system missing")
    scope = candidate["scope"]
    year = candidate.get("admission_year")
    if type(year) is not int:
        raise ValueError("Integration requires explicit admission year")
    attrs = {
        k: (scope.get(k) or {}).get("display")
        for k in ["campus", "track", "language", "training_mode"]
    }
    attrs["admission_year"] = year
    code = (scope.get("offering_code") or {}).get("display")
    name = (scope.get("program_name") or {}).get("display")
    keys = {owner.key}
    methods = [
        e
        for e in registry.entities
        if e.kind == "method"
        and e.university_key == owner.key
        and candidate.get("method")
        and exact(e.name) == exact(candidate["method"]["display"])
    ]
    if len(methods) != 1:
        raise ValueError("Integration requires exact source method semantics")
    keys.add(methods[0].key)
    offerings = [
        e
        for e in registry.entities
        if e.kind == "offering"
        and e.university_key == owner.key
        and name
        and exact(e.name) == exact(name)
        and all(e.attributes.get(k) == v for k, v in attrs.items())
        and any(
            x.system == system
            and x.value == code
            and (x.from_year is None or x.from_year <= year)
            and (x.to_year is None or x.to_year >= year)
            for x in e.codes
        )
    ]
    if len(offerings) != 1:
        raise ValueError("Integration requires exact code/system/year/campus/name Offering")
    offering = offerings[0]
    program = registry.entry(offering.program_key or "")
    if program.university_key != owner.key or not name or exact(program.name) != exact(name):
        raise ValueError("Integration Program owner/name conflict")
    keys.update([offering.key, program.key])
    return keys


def integrate(
    c: Connection, base: EntityRegistry, bindings: list[Binding], keys: list[str], version: str
) -> dict[str, Any]:
    if not keys or len(set(keys)) != len(keys) or len(keys) > 5000:
        raise ValueError("Unique bounded integration proposal keys required")
    if not version or version == base.version:
        raise ValueError("Integration requires a distinct proposed version")
    validate_targets(c, base)
    bindings = sorted(bindings, key=lambda b: (str(b.resolution_id), b.candidate_key))
    packets = checked_packets(c, bindings)
    available: dict[str, dict[str, Any]] = {}
    proof: dict[str, list[dict[str, Any]]] = defaultdict(list)
    jobs: dict[str, dict[str, Any]] = {}
    for packet in packets:
        jid = packet["resolution_job_id"]
        if jid not in jobs:
            job = dict(record(c, "ingest_jobs", UUID(jid)))
            payload = job["payload"]
            frozen = payload["registry"]
            if (
                job["job_type"] != "resolve_entities"
                or digest(frozen) != payload["registry_sha256"]
                or digest(frozen["entities"]) != payload["registry_entities_sha256"]
                or digest(frozen["aliases"]) != payload["alias_entries_sha256"]
            ):
                raise ValueError("Integration frozen registry manifest changed")
            jobs[jid] = payload
        reg = EntityRegistry.model_validate(jobs[jid]["registry"])
        for k in supported_keys(packet, reg):
            entity = reg.entry(k).model_dump(mode="json")
            if k in available and available[k] != entity:
                raise ValueError(
                    "Conflicting integration key/owner/parent/attributes/evidence: " + k
                )
            available[k] = entity
            proof[k].append(binding_for(packet).model_dump(mode="json"))
    old = {e.key: e.model_dump(mode="json") for e in base.entities}
    additions = []
    for k in sorted(keys):
        if k not in available:
            raise ValueError("Integration key lacks legitimate packet lineage: " + k)
        entity = available[k]
        if k in old:
            if old[k] != entity:
                raise ValueError("Integration cannot replace an existing registry entity: " + k)
            continue
        if entity["review"]["status"] != "pending" or entity["canonical_id"] is not None:
            raise ValueError("Integration imports pending proposals only")
        additions.append(entity)
    value = base.frozen()
    value.update(version=version, entities=value["entities"] + additions)
    integrated = EntityRegistry.model_validate(value)
    domains: dict[str, str] = {}
    for e in integrated.entities:
        if e.kind != "university":
            continue
        for host in e.domains:
            if host in domains and domains[host] != e.key:
                raise ValueError("Integration source domain has conflicting owners")
            domains[host] = e.key
    # Detect same-context code alternatives, retain both pending keys for human review.
    codes: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for e in integrated.entities:
        if e.kind != "offering":
            continue
        for code in e.codes:
            codes[
                (
                    e.university_key,
                    code.system,
                    code.value,
                    code.from_year,
                    code.to_year,
                    *(
                        e.attributes.get(k)
                        for k in ["campus", "track", "language", "training_mode"]
                    ),
                )
            ].append(e.key)
    conflicts = [
        dict(code_scope=list(k), proposal_keys=sorted(v), status="unresolved_requires_review")
        for k, v in sorted(codes.items(), key=lambda v: str(v[0]))
        if len(v) > 1
    ]
    spec = ProposalIntegration(
        version=version,
        base_sha256=digest(base.frozen()),
        bindings=bindings,
        proposal_keys=sorted(keys),
        registry_sha256=digest(integrated.frozen()),
    )
    result = dict(
        schema_version="proposal-integration/1",
        proposal_only=True,
        execution_ready=False,
        expected_registry_version=base.version,
        expected_alias_version=base.alias_version,
        spec=spec.model_dump(mode="json"),
        registry=integrated.frozen(),
        added_keys=[e["key"] for e in additions],
        preserved_entity_keys=list(old),
        aliases_unchanged=True,
        key_bindings={k: proof[k] for k in sorted(keys)},
        parent_manifests={
            j: {
                k: p[k]
                for k in [
                    "registry_version",
                    "alias_version",
                    "registry_sha256",
                    "registry_entities_sha256",
                    "alias_entries_sha256",
                    "input_sha256",
                ]
            }
            for j, p in sorted(jobs.items())
        },
        identity_conflicts=conflicts,
    )
    return result | {"manifest_sha256": digest(result)}


def prepare_integration(
    c: Connection, bindings: list[Binding], keys: list[str], version: str
) -> dict[str, Any]:
    from services.data.publication.review import ReviewService

    packets = checked_packets(c, bindings[:1])
    base = ReviewService(c).registry(packets[0])
    return integrate(c, base, bindings, keys, version)


def checked_integration(
    c: Connection, base: EntityRegistry, spec: ProposalIntegration
) -> EntityRegistry:
    if digest(base.frozen()) != spec.base_sha256:
        raise ValueError("Stale/tampered integration base")
    result = integrate(c, base, spec.bindings, spec.proposal_keys, spec.version)
    if result["spec"] != spec.model_dump(mode="json"):
        raise ValueError("Integration digest or canonical order changed")
    return EntityRegistry.model_validate(result["registry"])


def operation_packets(c: Connection, cmd: ReviewCommand) -> dict[str, list[dict[str, Any]]] | None:
    if not cmd.operation_bindings and cmd.proposal_integration is None:
        return None  # Exact legacy single-packet contract.
    if cmd.action != "bootstrap" or set(cmd.operation_bindings) != {o.key for o in cmd.operations}:
        raise ValueError("Every batch bootstrap operation requires its own packet bindings")
    bindings: dict[tuple[UUID, str], Binding] = {}
    for group in cmd.operation_bindings.values():
        if not group:
            raise ValueError("Operation packet bindings cannot be empty")
        for b in group:
            k = (b.resolution_id, b.candidate_key)
            if k in bindings and bindings[k] != b:
                raise ValueError("Conflicting operation packet binding hashes")
            bindings[k] = b
    if cmd.proposal_integration:
        allowed = {
            (b.resolution_id, b.candidate_key, b.packet_sha256)
            for b in cmd.proposal_integration.bindings
        }
        if any(
            (b.resolution_id, b.candidate_key, b.packet_sha256) not in allowed
            for b in [cmd.binding, *bindings.values()]
        ):
            raise ValueError("Operation packet outside reviewed integration batch")
    packets = checked_packets(c, list(bindings.values()))
    index = {(p["resolution_id"], p["candidate_key"]): p for p in packets}
    return {
        k: [index[(str(b.resolution_id), b.candidate_key)] for b in bs]
        for k, bs in cmd.operation_bindings.items()
    }


def check_operation(
    op: BootstrapOperation,
    packets: list[dict[str, Any]],
    seed: EntityRegistry,
    ids: dict[str, UUID],
    values: dict[str, Any],
    cmd: ReviewCommand,
) -> None:
    """Fail closed for explicit batch operations; legacy command rules remain unchanged."""
    if op.kind not in {"university", "program", "offering", "method", "source", "year", "scale"}:
        raise ValueError("Operation kind lacks batch evidence binding support")
    bykey = {e.key: e for e in seed.entities}
    if op.key in bykey and bykey[op.key].review.status != "pending":
        raise ValueError("Batch operation cannot change an approved/revoked entity")
    if op.key in bykey:
        original = bykey[op.key].model_dump(mode="json")
        for field, value in op.registry_fields.items():
            if field == "codes" and op.kind == "method":
                additions = [v for v in value if v not in original["codes"]]
                if any(v not in value for v in original["codes"]) or any(
                    v.get("system") != "admission_methods.code"
                    or v.get("value") != values.get("code")
                    or not set(v.get("evidence", [])) <= set(op.evidence)
                    for v in additions
                ):
                    raise ValueError("Method code metadata conflicts with reviewed operation")
            elif field not in original or value != original[field]:
                raise ValueError("Batch cannot replace frozen proposal identity metadata")
    allowed_refs: set[str] = set()

    def locators(value: Any) -> set[str]:
        found = set()
        if isinstance(value, dict):
            for k, v in value.items():
                if k.endswith("locator") and isinstance(v, str):
                    found.add(v)
                found.update(locators(v))
        elif isinstance(value, list):
            for v in value:
                found.update(locators(v))
        return found

    for p in packets:
        keys = supported_keys(p, seed)
        owner = next(seed.entry(k) for k in keys if seed.entry(k).kind == "university")
        method = next(seed.entry(k) for k in keys if seed.entry(k).kind == "method")
        cv = p["candidate"]
        scope = cv["scope"]
        if op.kind in {"university", "method", "program", "offering"} and op.key not in keys:
            raise ValueError("Operation key is not supported by its own packet evidence")
        if op.kind in {"program", "offering", "source", "year"} and values.get(
            "university_id"
        ) != ids.get(owner.key):
            raise ValueError("Operation University parent conflicts with packet evidence")
        if (
            op.key in bykey
            and op.registry_fields.get("university_key", bykey[op.key].university_key)
            != bykey[op.key].university_key
        ):
            raise ValueError("Operation cannot silently change proposal owner")
        if op.kind == "offering":
            e = seed.entry(op.key)
            parent = op.registry_fields.get("program_key", e.program_key)
            if (
                parent != e.program_key
                or parent not in bykey
                or bykey[parent].university_key != owner.key
                or values.get("program_id") != ids.get(parent)
            ):
                raise ValueError("Offering Program parent conflicts with reviewed reference")
            if str(values.get("primary_snapshot_id")) != p["snapshot_id"]:
                raise ValueError("Offering primary snapshot conflicts with packet evidence")
            expected = dict(
                admission_year=cv["admission_year"],
                offering_code=scope["offering_code"]["display"],
                campus_code=(scope.get("campus") or {}).get("display") or "UNSPECIFIED",
                track_code=(scope.get("track") or {}).get("display") or "UNSPECIFIED",
                language_code=(scope.get("language") or {}).get("display") or "UNSPECIFIED",
            )
            if any(values.get(k) != v for k, v in expected.items()):
                raise ValueError("Offering context conflicts with its own packet evidence")
            attrs = op.registry_fields.get("attributes", {})
            if (
                any(
                    attrs.get(k) != (scope.get(k) or {}).get("display")
                    for k in ["campus", "track", "language", "training_mode"]
                )
                or attrs.get("admission_year") != cv["admission_year"]
            ):
                raise ValueError("Offering registry attributes conflict with packet evidence")
        if op.kind in {"scale", "year"}:
            if (
                values.get("admission_year") != cv["admission_year"]
                or str(values.get("primary_snapshot_id")) != p["snapshot_id"]
            ):
                raise ValueError("Operation year/snapshot conflicts with packet evidence")
            if op.kind == "scale" and values.get("method_id") != ids.get(method.key):
                raise ValueError("Scale method conflicts with packet evidence")
        if op.kind == "source":
            if str(op.canonical_id) != p["source_id"]:
                raise ValueError("Source operation requires its own packet binding")
        allowed_refs.update(
            "snapshot:" + p["snapshot_id"] + "#" + loc for loc in locators(cv["lineage"])
        )
    if not set(op.evidence) <= allowed_refs:
        raise ValueError("Operation evidence outside bound packet locators")
    if op.kind == "source":
        scope = values.get("authority_scope", {})
        owners = {str(values.get("university_id"))}
        if (
            set(scope) - {"years", "fact_kinds", "universities", "publication_bindings"}
            or not set(scope.get("universities", [])) <= owners
            or set(scope.get("years", [])) != {p["candidate"]["admission_year"] for p in packets}
            or not scope.get("fact_kinds")
            or not set(scope["fact_kinds"]) <= {"cutoff", "scoring_rule"}
        ):
            raise ValueError("Authority scope outside bound owner/year/fact-kind evidence")
        if not scope.get("publication_bindings"):
            raise ValueError("Batch authority requires narrow publication bindings")
        for b in scope["publication_bindings"]:
            for sid in b["snapshot_ids"]:
                matches = [
                    p
                    for p in packets
                    if p["snapshot_id"] == sid
                    and p["candidate"]["admission_year"] == b["admission_year"]
                    and p["candidate"]["scope"]["offering_code"]["display"] == b["offering_code"]
                    and p["candidate"]["scope"]["campus"]["display"] == b["campus_code"]
                ]
                if not matches:
                    raise ValueError("Authority scope outside operation packet coverage")
                methods = [
                    seed.entry(k)
                    for k in supported_keys(matches[0], seed)
                    if seed.entry(k).kind == "method"
                ]
                method_codes = {
                    x.value
                    for m in methods
                    for x in m.codes
                    if x.system == "admission_methods.code"
                }
                method_codes.update(
                    o.values["code"]
                    for o in cmd.operations
                    if o.kind == "method"
                    and o.key in {m.key for m in methods}
                    and "code" in o.values
                )
                if b["method_code"] not in method_codes:
                    raise ValueError("Authority method code outside reviewed packet method")
