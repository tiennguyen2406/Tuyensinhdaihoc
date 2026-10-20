"""Read-only T07 packet construction; digests bind original rows, not summaries."""

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from services.api.db.models import ingest_jobs, observations
from services.api.db.validators import record
from services.data.normalization.store import digest
from services.data.publication.contract import Binding
from services.data.resolution.store import ResolutionStore


def list_packets(c: Connection) -> list[dict[str, Any]]:
    rows = c.execute(
        sa.select(observations.c.id, observations.c.normalized_fields).where(
            observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1"
        )
    ).mappings()
    return [
        dict(
            resolution_id=str(r["id"]),
            candidate_key=v["candidate_key"],
            fact_kind=v["fact_kind"],
            admission_year=v["admission_year"],
            status=v["status"],
            registry_version=r["normalized_fields"]["registry_version"],
        )
        for r in rows
        for v in r["normalized_fields"]["candidates"]
    ]


def inspect_packet(
    c: Connection,
    resolution_id: UUID,
    candidate_key: str,
    *,
    _parents: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    row = dict(record(c, "observations", resolution_id))
    out = row["normalized_fields"]
    if out.get("schema_version") != "entity-resolution/1":
        raise ValueError("Requires T07 output")
    parent_id = UUID(out["input_envelope_id"])
    job_rows = c.execute(
        sa.select(ingest_jobs).where(ingest_jobs.c.job_type == "resolve_entities")
    ).mappings()
    jobs = [
        j
        for j in job_rows
        if j["payload"]["registry_version"] == out["registry_version"]
        and j["payload"]["alias_version"] == out["alias_version"]
        and str(parent_id) in j["payload"]["input_envelope_ids"]
    ]
    if len(jobs) != 1:
        raise ValueError("Unique frozen T07 job required")
    job = jobs[0]
    p = job["payload"]
    registry = p["registry"]
    if (
        digest(registry) != p["registry_sha256"]
        or digest(registry["entities"]) != p["registry_entities_sha256"]
        or digest(registry["aliases"]) != p["alias_entries_sha256"]
    ):
        raise ValueError("Frozen T07 registry manifest mismatch")
    cache = _parents if _parents is not None else {}
    normal_job = p["normalization_job_id"]
    if normal_job not in cache:
        _, cache[normal_job], _ = ResolutionStore(c).inputs(normal_job)
    parents = cache[normal_job]
    if digest(parents) != p["input_sha256"] or sorted(str(r["id"]) for r in parents) != sorted(
        p["input_envelope_ids"]
    ):
        raise ValueError("Frozen T07 parent manifest mismatch")
    parent = next(r for r in parents if r["id"] == parent_id)
    signature = {
        k: p[k]
        for k in [
            "resolver_version",
            "registry_version",
            "alias_version",
            "registry_entities_sha256",
            "alias_entries_sha256",
            "registry_sha256",
            "implementation_sha256",
            "configuration_sha256",
            "lock_sha256",
        ]
    }
    if row["payload_hash"] != digest(dict(input_row=parent, resolution=out, signature=signature)):
        raise ValueError("Resolution payload integrity mismatch")
    selected = [v for v in out["candidates"] if v["candidate_key"] == candidate_key]
    if len(selected) != 1:
        raise ValueError("Unique input candidate required")
    result = selected[0]
    raw = dict(record(c, "observations", UUID(result["raw_observation_id"])))
    snap = dict(record(c, "source_snapshots", row["snapshot_id"]))
    source = record(c, "sources", snap["source_id"])
    normalized = next(
        v for v in parent["normalized_fields"]["candidates"] if v["candidate_key"] == candidate_key
    )
    value = dict(
        resolution_id=str(resolution_id),
        candidate_key=candidate_key,
        resolution_job_id=str(job["id"]),
        normalization_job_id=p["normalization_job_id"],
        normalization_envelope_id=str(parent_id),
        raw_observation_id=str(raw["id"]),
        snapshot_id=str(snap["id"]),
        source_id=str(snap["source_id"]),
        row_digests={
            "raw": digest(raw),
            "normalization": digest(parent),
            "resolution": digest(row),
            "snapshot": digest(snap),
        },
        source_identity={
            k: str(source[k]) for k in ["id", "canonical_url", "domain", "publisher", "source_type"]
        },
        registry_version=out["registry_version"],
        alias_version=out["alias_version"],
        resolver_version=out["resolver_version"],
        normalizer_namespace=out["normalizer_namespace"],
        candidate=normalized,
        resolution=result,
        evidence=dict(
            raw_hash=snap["raw_hash"],
            final_url=snap["final_url"],
            locator=normalized["lineage"]["cell_locator"],
            header_path=normalized["lineage"]["header_path"],
            raw_value=normalized["lineage"]["raw_value"],
        ),
    )
    return value | {"packet_sha256": digest(value)}


def binding_for(packet: dict[str, Any]) -> Binding:
    return Binding(**{k: packet[k] for k in ["resolution_id", "candidate_key", "packet_sha256"]})


def checked_packet(c: Connection, binding: Binding) -> dict[str, Any]:
    value = inspect_packet(c, binding.resolution_id, binding.candidate_key)
    if value["packet_sha256"] != binding.packet_sha256:
        raise ValueError("Review input digest changed")
    return value


def checked_packets(c: Connection, bindings: list[Binding]) -> list[dict[str, Any]]:
    """Bounded batch inspection; parent validation cached only within this call."""
    if not bindings or len(bindings) > 1000:
        raise ValueError("Nonempty bounded packet batch required")
    keys = [(b.resolution_id, b.candidate_key) for b in bindings]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate candidate binding")
    parents: dict[str, list[dict[str, Any]]] = {}
    packets = []
    for b in bindings:
        p = inspect_packet(c, b.resolution_id, b.candidate_key, _parents=parents)
        if p["packet_sha256"] != b.packet_sha256:
            raise ValueError("Review input digest changed")
        packets.append(p)
    return packets
