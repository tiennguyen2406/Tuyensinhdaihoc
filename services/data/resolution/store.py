"""Insert-only T07 envelopes and frozen manifests on existing PostgreSQL tables."""

import hashlib
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from services.api.db.models import ingest_jobs, metadata, observations, source_snapshots
from services.api.db.session import ROOT
from services.data.normalization.contract import NormalizationContext, NormalizedObservation
from services.data.normalization.store import NormalizationStore, digest
from services.data.resolution.contract import VERSION, ResolutionInput
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.resolve import propose_registry, resolve

CONFIG = {
    "fuzzy_auto_link": False,
    "top_k": 10,
    "weights": [0.60, 0.25, 0.15],
    "similarity": "stdlib-token-sort-sequencematcher/1",
    "unknown_metadata": "not_a_mismatch",
}


def implementation_hash() -> str:
    h = hashlib.sha256()
    for folder in [Path(__file__).parent, ROOT / "services/data/normalization"]:
        for path in sorted(folder.glob("*.py")):
            h.update(str(path.relative_to(ROOT)).replace("\\", "/").encode())
            h.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [c for r in results for c in r["candidates"]]
    by_type = {
        k: dict(Counter(c["entities"][k]["status"] for c in candidates))
        for k in ["university", "major", "program", "offering", "method", "scope"]
    }
    suggestions = {k: sum(bool(c["entities"][k]["options"]) for c in candidates) for k in by_type}
    return dict(
        input_envelopes=len(results),
        candidates=len(candidates),
        states=dict(Counter(c["status"] for c in candidates)),
        by_entity_type=by_type,
        with_suggestions_by_entity_type=suggestions,
        publication_eligible=sum(c["publication_eligible"] for c in candidates),
        blocked_t06_attempts=sum(r["blocked_input_attempts"] for r in results),
        original_issue_occurrences=sum(r["input_issue_count"] for r in results),
    )


def validate_targets(c: Connection, registry: EntityRegistry) -> None:
    if registry.classification == "synthetic":
        raise ValueError("Synthetic registry cannot run against the project database")
    tables = {
        "university": "universities",
        "major": "majors",
        "program": "programs",
        "offering": "program_years",
        "method": "admission_methods",
        "scope": "program_admissions",
    }
    for e in registry.entities:
        if e.review.status != "approved":
            continue
        table = metadata.tables[tables[e.kind]]
        row = (
            c.execute(sa.select(table).where(table.c.id == e.canonical_id)).mappings().one_or_none()
        )
        if row is None:
            raise ValueError("Approved canonical registry target does not exist")
        if e.kind == "university" and row["verification_status"] != "verified":
            raise ValueError("Canonical university not verified")
        if e.kind in {"program", "offering"}:
            if row["university_id"] != registry.entry(e.university_key or "").canonical_id:
                raise ValueError("Canonical parent university mismatch")
        if e.kind == "offering":
            if row["program_id"] != registry.entry(e.program_key or "").canonical_id:
                raise ValueError("Canonical offering/program mismatch")
            for field, column in [
                ("admission_year", "admission_year"),
                ("campus", "campus_code"),
                ("track", "track_code"),
                ("language", "language_code"),
            ]:
                expected = e.attributes.get(field)
                if (expected is None and row[column] != "UNSPECIFIED") or (
                    expected is not None and expected != row[column]
                ):
                    raise ValueError("Canonical offering key mismatch")
        if e.kind == "major" and not any(
            x.system == row["code_system"] and x.value == row["major_code"] for x in e.codes
        ):
            raise ValueError("Canonical major taxonomy/code mismatch")
        if e.kind == "method" and (
            e.attributes.get("input_kind") != row["input_kind"]
            or not any(
                x.system == "admission_methods.code" and x.value == row["code"] for x in e.codes
            )
        ):
            raise ValueError("Canonical method semantics/code unconfirmed")
        if e.kind == "scope":
            offering = metadata.tables["program_years"]
            owner: UUID = c.execute(
                sa.select(offering.c.university_id).where(offering.c.id == row["program_year_id"])
            ).scalar_one()
            if owner != registry.entry(e.university_key or "").canonical_id or any(
                e.attributes.get(k) is None or str(e.attributes[k]) != str(row[k])
                for k in ["round_key", "population_key", "condition_key", "score_scale_id"]
            ):
                raise ValueError("Canonical admission scope/basis not confirmed")


class ResolutionStore:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def inputs(
        self, normalization_job: str | UUID
    ) -> tuple[list[ResolutionInput], list[dict[str, Any]], dict[str, Any]]:
        c = self.connection
        job = (
            c.execute(
                sa.select(ingest_jobs).where(
                    ingest_jobs.c.id == UUID(str(normalization_job)),
                    ingest_jobs.c.job_type == "normalize_observations",
                )
            )
            .mappings()
            .one_or_none()
        )
        if job is None:
            raise ValueError("Input must be a frozen normalization job, not raw/resolution output")
        p = job["payload"]
        raw, _, sha = NormalizationStore(c)._inputs(
            [UUID(i) for i in p["input_ids"]], NormalizationContext.model_validate(p["context"])
        )
        if sha != p["input_sha256"]:
            raise ValueError("Frozen normalization raw input changed")
        parents = {str(r.id): r for r in raw}
        rows = [
            dict(r)
            for r in c.execute(
                sa.select(observations)
                .where(
                    observations.c.transform_version == p["transform_version"],
                    observations.c.normalized_fields["input_observation_id"].astext.in_(
                        list(parents)
                    ),
                )
                .order_by(observations.c.id)
            ).mappings()
        ]
        if len(rows) != len(raw):
            raise ValueError("Normalization output set missing/duplicated")
        if len({r["normalized_fields"]["input_observation_id"] for r in rows}) != len(raw):
            raise ValueError("Normalization lineage duplicated")
        signature = {
            k: p[k] for k in ["configuration_sha256", "implementation_sha256", "lock_sha256"]
        }
        result = []
        for row in rows:
            parent = parents[row["normalized_fields"]["input_observation_id"]]
            expected = digest(
                {
                    "input": parent.model_dump(mode="json"),
                    "normalized_fields": row["normalized_fields"],
                    "input_parser": parent.parser_version,
                    "signature": signature,
                }
            )
            if (
                row["payload_hash"] != expected
                or row["raw_fields"] != parent.raw_fields
                or row["snapshot_id"] != parent.snapshot_id
                or row["record_locator"] != parent.record_locator
                or row["parser_version"] != parent.parser_version
            ):
                raise ValueError("Normalization payload/lineage integrity mismatch")
            env = NormalizedObservation.model_validate(row["normalized_fields"])
            if (
                env.transform_version != p["transform_version"]
                or env.normalizer_version != p["normalizer_version"]
            ):
                raise ValueError("Normalization namespace mismatch")
            s = (
                c.execute(
                    sa.select(source_snapshots).where(source_snapshots.c.id == row["snapshot_id"])
                )
                .mappings()
                .one()
            )
            result.append(
                ResolutionInput(
                    envelope_id=row["id"],
                    envelope=env,
                    final_url=s["final_url"],
                    source_id=s["source_id"],
                )
            )
        return result, rows, dict(job)

    def preview(self, normalization_job: str | UUID, seed: EntityRegistry) -> dict[str, Any]:
        inputs, rows, job = self.inputs(normalization_job)
        registry = propose_registry(seed, inputs)
        validate_targets(self.connection, registry)
        results = [resolve(i, registry).model_dump(mode="json") for i in inputs]
        return {
            "normalization_job_id": str(job["id"]),
            "input_sha256": digest(rows),
            "normalizer_namespace": job["payload"]["transform_version"],
            "registry": registry.frozen(),
            "registry_sha256": digest(registry.frozen()),
            "results": results,
            "summary": summary(results),
            "persisted": False,
        }

    def run(self, normalization_job: str | UUID, seed: EntityRegistry) -> dict[str, Any]:
        c = self.connection
        # ponytail: serialize pilot resolutions; shard only after measured throughput testing.
        c.execute(sa.select(sa.func.pg_advisory_xact_lock(sa.func.hashtext("T07:resolution"))))
        preview = self.preview(normalization_job, seed)
        reg = preview["registry"]
        signature = dict(
            resolver_version=VERSION,
            registry_version=reg["version"],
            alias_version=reg["alias_version"],
            registry_entities_sha256=digest(reg["entities"]),
            alias_entries_sha256=digest(reg["aliases"]),
            registry_sha256=preview["registry_sha256"],
            implementation_sha256=implementation_hash(),
            configuration_sha256=digest(CONFIG),
            lock_sha256=hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        )
        oldjobs: Any = (
            c.execute(
                sa.select(ingest_jobs.c.payload).where(ingest_jobs.c.job_type == "resolve_entities")
            )
            .scalars()
            .all()
        )
        for p in oldjobs:
            for version, hashes in [
                (
                    "resolver_version",
                    ["implementation_sha256", "configuration_sha256", "lock_sha256"],
                ),
                ("registry_version", ["registry_entities_sha256"]),
                ("alias_version", ["alias_entries_sha256"]),
            ]:
                if p[version] == signature[version] and any(p[k] != signature[k] for k in hashes):
                    raise ValueError(
                        "Changed logic/config/registry/alias requires a new corresponding version"
                    )
        namespace = (
            "resolution/1;"
            + VERSION
            + ";"
            + reg["version"]
            + ";"
            + reg["alias_version"]
            + ";"
            + "input="
            + digest(preview["normalizer_namespace"])
        )
        key = "resolve:" + digest([str(normalization_job), namespace])
        old = (
            c.execute(sa.select(ingest_jobs).where(ingest_jobs.c.idempotency_key == key))
            .mappings()
            .one_or_none()
        )
        if old and old["payload"]["input_sha256"] != preview["input_sha256"]:
            raise ValueError("Frozen resolution input changed")
        _, rows, job = self.inputs(normalization_job)
        if digest(rows) != preview["input_sha256"]:
            raise ValueError("Normalization input changed during resolution")
        inserted = 0
        for parent, result in zip(rows, preview["results"]):
            raw = {
                "input_normalization_envelope_id": str(parent["id"]),
                "normalization_job_id": str(normalization_job),
            }
            payload_hash = digest(
                {"input_row": parent, "resolution": result, "signature": signature}
            )
            values = dict(
                snapshot_id=parent["snapshot_id"],
                fact_kind=parent["fact_kind"],
                record_locator=parent["record_locator"],
                parser_version=parent["parser_version"],
                transform_version=namespace,
                raw_fields=raw,
                normalized_fields=result,
                payload_hash=payload_hash,
                extraction_method="entity_resolution",
                extraction_confidence=None,
                verification_status="unverified",
            )
            identifier = c.execute(
                insert(observations)
                .values(**values)
                .on_conflict_do_nothing(
                    index_elements=[
                        observations.c.snapshot_id,
                        observations.c.record_locator,
                        observations.c.parser_version,
                        observations.c.transform_version,
                    ]
                )
                .returning(observations.c.id)
            ).scalar_one_or_none()
            if identifier is not None:
                inserted += 1
            else:
                prior = (
                    c.execute(
                        sa.select(observations).where(
                            observations.c.snapshot_id == parent["snapshot_id"],
                            observations.c.record_locator == parent["record_locator"],
                            observations.c.parser_version == parent["parser_version"],
                            observations.c.transform_version == namespace,
                        )
                    )
                    .mappings()
                    .one()
                )
                if (
                    prior["payload_hash"] != payload_hash
                    or prior["normalized_fields"] != result
                    or prior["raw_fields"] != raw
                ):
                    raise ValueError("Resolution payload differs under frozen namespace")
        if old:
            return old["payload"]["result"] | {"inserted": inserted, "cached": True}
        git = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        payload = {
            **signature,
            "configuration": CONFIG,
            "registry": reg,
            "input_sha256": preview["input_sha256"],
            "input_envelope_ids": [str(r["id"]) for r in rows],
            "normalizer_namespace": preview["normalizer_namespace"],
            "normalization_job_id": str(normalization_job),
            "legacy_t06_lock_sha256": job["payload"]["lock_sha256"],
            "git_commit_at_execution": git.stdout.strip(),
            "working_tree_dirty": bool(dirty.stdout.strip()),
        }
        job_id: UUID = c.execute(
            insert(ingest_jobs)
            .values(
                job_type="resolve_entities",
                idempotency_key=key,
                payload=payload,
                status="quarantined",
                attempts=1,
                last_error={"code": "entity_resolution_review_required"},
            )
            .returning(ingest_jobs.c.id)
        ).scalar_one()
        answer = preview["summary"] | dict(
            job_id=str(job_id),
            resolver_version=VERSION,
            registry_version=reg["version"],
            alias_version=reg["alias_version"],
            inserted=inserted,
            cached=False,
            status="quarantined",
        )
        c.execute(
            ingest_jobs.update()
            .where(ingest_jobs.c.id == job_id)
            .values(payload=payload | {"result": answer})
        )
        return answer

    def replay(self, job_id: str | UUID) -> dict[str, Any]:
        p: dict[str, Any] = self.connection.execute(
            sa.select(ingest_jobs.c.payload).where(
                ingest_jobs.c.id == UUID(str(job_id)), ingest_jobs.c.job_type == "resolve_entities"
            )
        ).scalar_one()
        return self.run(p["normalization_job_id"], EntityRegistry.model_validate(p["registry"]))

    def affected(self, entry: str, registry: EntityRegistry | None = None) -> list[dict[str, Any]]:
        # New aliases cannot appear in historical dependencies. Conservatively include
        # all old candidate outputs for a supplied registry change; never claim no impact.
        potential = registry is not None and (
            any(e.key == entry for e in registry.entities)
            or any(a.key == entry for a in registry.aliases)
        )
        rows = self.connection.execute(
            sa.select(observations.c.id, observations.c.normalized_fields).where(
                observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1"
            )
        ).mappings()
        hits = []
        for row in rows:
            for candidate in row["normalized_fields"]["candidates"]:
                direct = entry in candidate["dependencies"]
                if direct or potential:
                    hits.append(
                        {
                            "impact_kind": "historical_dependency"
                            if direct
                            else "potential_registry_change",
                            "resolution_envelope_id": str(row["id"]),
                            "input_envelope_id": candidate["input_envelope_id"],
                            "candidate_key": candidate["candidate_key"],
                            "resolver_version": row["normalized_fields"]["resolver_version"],
                            "registry_version": row["normalized_fields"]["registry_version"],
                            "alias_version": row["normalized_fields"]["alias_version"],
                        }
                    )
        return hits
