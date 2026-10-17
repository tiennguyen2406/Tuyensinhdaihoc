"""Atomic, insert-only normalization envelopes using the existing observations unique key."""

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from services.api.db.models import ingest_jobs, observations, source_snapshots
from services.api.db.session import ROOT
from services.data.normalization.contract import NormalizationContext, RawObservation
from services.data.normalization.normalize import normalize
from services.data.parsers.contract import TRANSFORM_VERSION


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode()
    ).hexdigest()


def implementation_hash() -> str:
    h = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [c for r in results for c in r["candidates"]]
    blocked = [b for r in results for b in r["blocked"]]
    unique_issues = {
        (r["snapshot_id"], i["code"], i["level"], i["locator"], i["field"], i["blocks_candidate"])
        for r in results
        for i in r["issues"]
    }
    groups = Counter(
        (
            c["fact_kind"],
            c["admission_year"],
            c["academic_year"],
            c["method"]["display"] if c["method"] else None,
            c["scope"]["campus"]["display"] if c["scope"].get("campus") else None,
        )
        for c in candidates
    )
    return {
        "inputs": len(results),
        "candidates": len(candidates),
        "blocked_attempts": len(blocked),
        "inputs_with_candidates": sum(bool(r["candidates"]) for r in results),
        "inputs_without_candidates": sum(not r["candidates"] for r in results),
        "fact_kinds": dict(Counter(c["fact_kind"] for c in candidates)),
        "groups": [
            dict(
                fact_kind=k[0],
                admission_year=k[1],
                academic_year=k[2],
                method=k[3],
                campus=k[4],
                count=v,
            )
            for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))
        ],
        "blocked_reasons": dict(
            Counter(i["code"] for b in blocked for i in b["issues"] if i["blocks_candidate"])
        ),
        "open_input_issues_deduplicated": dict(Counter(k[1] for k in unique_issues)),
        "candidate_review_issues": dict(
            Counter(i["code"] for c in candidates for i in c["issues"])
        ),
        "canonical_writes": 0,
    }


class NormalizationStore:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def raw_ids(self, snapshot_id: UUID | None = None) -> list[UUID]:
        query = sa.select(observations.c.id).where(
            observations.c.transform_version == TRANSFORM_VERSION,
            observations.c.normalized_fields == {},
        )
        if snapshot_id:
            query = query.where(observations.c.snapshot_id == snapshot_id)
        return list(self.connection.execute(query.order_by(observations.c.id)).scalars())

    def _inputs(
        self, identifiers: list[UUID], ctx: NormalizationContext
    ) -> tuple[list[RawObservation], list[NormalizationContext], str]:
        if not identifiers or len(identifiers) != len(set(identifiers)):
            raise ValueError("Unique nonempty raw input identifiers required")
        records = (
            self.connection.execute(
                sa.select(observations, source_snapshots.c.source_id)
                .join(source_snapshots, observations.c.snapshot_id == source_snapshots.c.id)
                .where(observations.c.id.in_(identifiers))
                .order_by(observations.c.id)
            )
            .mappings()
            .all()
        )
        if len(records) != len(identifiers):
            raise ValueError("Requested input not found; refusing partial subset")
        rows = [RawObservation.model_validate(dict(row)) for row in records]
        if any(r.transform_version != TRANSFORM_VERSION or r.normalized_fields for r in rows):
            raise ValueError("All inputs must be raw-only observations")
        contexts = []
        for row in rows:
            job = row.raw_fields.get("_extraction", {}).get("parse_job_id")
            issues = list(ctx.document_issues)
            if job:
                old = (
                    self.connection.execute(
                        sa.select(ingest_jobs.c.payload, ingest_jobs.c.last_error).where(
                            ingest_jobs.c.id == UUID(job),
                            ingest_jobs.c.job_type == "parse_snapshot",
                        )
                    )
                    .mappings()
                    .one()
                )
                if str(row.snapshot_id) != old["payload"].get("snapshot_id"):
                    raise ValueError("Input parse job snapshot lineage mismatch")
                issues.extend((old["last_error"] or {}).get("issues", []))
            contexts.append(ctx.model_copy(update={"document_issues": issues}))
        fingerprint = digest(
            [
                {"input": r.model_dump(mode="json"), "document_issues": c.document_issues}
                for r, c in zip(rows, contexts)
            ]
        )
        return rows, contexts, fingerprint

    def preview(
        self, identifiers: list[UUID], context: NormalizationContext | None = None
    ) -> dict[str, Any]:
        context = context or NormalizationContext()
        rows, contexts, fingerprint = self._inputs(identifiers, context)
        results = [normalize(row, ctx).model_dump(mode="json") for row, ctx in zip(rows, contexts)]
        return {
            "input_sha256": fingerprint,
            "normalizer_version": context.version,
            "transform_version": context.transform_version,
            "summary": summarize(results),
            "results": results,
            "persisted": False,
        }

    def run(
        self, identifiers: list[UUID], context: NormalizationContext | None = None
    ) -> dict[str, Any]:
        """Caller must use engine.begin(); failure rolls back the entire batch, no partial run."""
        context = context or NormalizationContext()
        c = self.connection
        # ponytail: serialize pilot batches per version; partition only after throughput testing.
        c.execute(
            sa.select(sa.func.pg_advisory_xact_lock(sa.func.hashtext("T06:" + context.version)))
        )
        config = context.model_dump(mode="json")
        signature = {
            "configuration_sha256": digest(config),
            "implementation_sha256": implementation_hash(),
            "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        }
        previous: Any = (
            c.execute(
                sa.select(ingest_jobs.c.payload).where(
                    ingest_jobs.c.job_type == "normalize_observations",
                    ingest_jobs.c.payload["normalizer_version"].astext == context.version,
                )
            )
            .scalars()
            .all()
        )
        if any(any(p.get(k) != v for k, v in signature.items()) for p in previous):
            raise ValueError(
                "Normalizer code/config/lock changed; use a new version, never overwrite"
            )
        preview = self.preview(identifiers, context)
        key = "normalize:" + digest(
            {"version": context.transform_version, "inputs": sorted(str(i) for i in identifiers)}
        )
        existing = (
            c.execute(sa.select(ingest_jobs).where(ingest_jobs.c.idempotency_key == key))
            .mappings()
            .one_or_none()
        )
        if existing and existing["payload"]["input_sha256"] != preview["input_sha256"]:
            raise ValueError("Frozen raw input changed; review input integrity")
        rows, _, _ = self._inputs(identifiers, context)
        inserted = 0
        for row, result in zip(rows, preview["results"]):
            payload_hash = digest(
                {
                    "input": row.model_dump(mode="json"),
                    "normalized_fields": result,
                    "input_parser": row.parser_version,
                    "signature": signature,
                }
            )
            values = dict(
                snapshot_id=row.snapshot_id,
                fact_kind=row.fact_kind,
                record_locator=row.record_locator,
                parser_version=row.parser_version,
                transform_version=context.transform_version,
                raw_fields=row.raw_fields,
                normalized_fields=result,
                payload_hash=payload_hash,
                extraction_method=row.extraction_method,
                extraction_confidence=row.extraction_confidence,
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
                old = (
                    c.execute(
                        sa.select(
                            observations.c.payload_hash,
                            observations.c.normalized_fields,
                            observations.c.raw_fields,
                        ).where(
                            observations.c.snapshot_id == row.snapshot_id,
                            observations.c.record_locator == row.record_locator,
                            observations.c.parser_version == row.parser_version,
                            observations.c.transform_version == context.transform_version,
                        )
                    )
                    .mappings()
                    .one()
                )
                if (
                    old["payload_hash"] != payload_hash
                    or old["normalized_fields"] != result
                    or old["raw_fields"] != row.raw_fields
                ):
                    raise ValueError(
                        "Existing normalization payload differs; use a new version, never overwrite"
                    )
        if existing:
            return existing["payload"]["result"] | {"cached": True, "inserted": inserted}
        git = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
        )
        git_state = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = {
            "working_tree_dirty": bool(git_state.stdout.strip())
            if git_state.returncode == 0
            else None,
            "normalizer_version": context.version,
            "transform_version": context.transform_version,
            "context": config,
            "input_ids": [str(r.id) for r in rows],
            "input_sha256": preview["input_sha256"],
            "git_commit": git.stdout.strip() if git.returncode == 0 else None,
            **signature,
        }
        job_id: UUID = c.execute(
            insert(ingest_jobs)
            .values(
                job_type="normalize_observations",
                idempotency_key=key,
                status="quarantined",
                attempts=1,
                payload=payload,
                last_error={"code": "normalization_requires_review"},
            )
            .returning(ingest_jobs.c.id)
        ).scalar_one()
        summary = preview["summary"] | {
            "job_id": str(job_id),
            "normalizer_version": context.version,
            "transform_version": context.transform_version,
            "input_sha256": preview["input_sha256"],
            "inserted": inserted,
            "cached": False,
            "status": "quarantined",
        }
        c.execute(
            ingest_jobs.update()
            .where(ingest_jobs.c.id == job_id)
            .values(payload=payload | {"result": summary})
        )
        return summary

    def replay(self, job_id: UUID) -> dict[str, Any]:
        payload: dict[str, Any] = self.connection.execute(
            sa.select(ingest_jobs.c.payload).where(
                ingest_jobs.c.id == job_id, ingest_jobs.c.job_type == "normalize_observations"
            )
        ).scalar_one()
        return self.run(
            [UUID(i) for i in payload["input_ids"]],
            NormalizationContext.model_validate(payload["context"]),
        )
