"""Durable T05 parse jobs on the existing ingest_jobs table; no crawler run updates."""

import hashlib
import json
import threading
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from services.api.db.models import ingest_jobs, source_snapshots
from services.api.source_profiles import SourceProfile
from services.crawler.raw import RawStorage
from services.data.parsers.contract import TRANSFORM_VERSION, ParseLimits, ParseResult, SnapshotRef
from services.data.parsers.persistence import ObservationStore
from services.data.parsers.registry import parser_version, profile_hash
from services.data.parsers.runner import replay


def implementation_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


class ParserJobs:
    def __init__(self, engine: Engine, raw: RawStorage) -> None:
        self.engine, self.raw = engine, raw

    def snapshot(self, identifier: UUID) -> SnapshotRef:
        with self.engine.connect() as c:
            row = (
                c.execute(sa.select(source_snapshots).where(source_snapshots.c.id == identifier))
                .mappings()
                .one()
            )
        return SnapshotRef(
            snapshot_id=row["id"],
            **{
                key: row[key]
                for key in [
                    "source_id",
                    "raw_hash",
                    "raw_uri",
                    "media_type",
                    "byte_size",
                    "final_url",
                ]
            },
        )

    def enqueue(
        self,
        identifier: UUID,
        profile: SourceProfile,
        *,
        revision: str = "1",
        limits: ParseLimits | None = None,
    ) -> UUID:
        ref = self.snapshot(identifier)
        version = parser_version(ref, revision)
        limits = limits or ParseLimits()
        config_hash = hashlib.sha256(
            json.dumps(
                {
                    "profile": profile_hash(profile),
                    "implementation": implementation_hash(),
                    "limits": limits.model_dump(),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        key = (
            f"parse:{identifier}:"
            + hashlib.sha256((version + "\n" + TRANSFORM_VERSION).encode()).hexdigest()
        )
        payload = {
            "snapshot_id": str(identifier),
            "profile": profile.model_dump(mode="json"),
            "revision": revision,
            "parser_version": version,
            "transform_version": TRANSFORM_VERSION,
            "limits": limits.model_dump(),
            "configuration_sha256": config_hash,
            "implementation_sha256": implementation_hash(),
            "lock_sha256": hashlib.sha256(
                (Path(__file__).resolve().parents[3] / "uv.lock").read_bytes()
            ).hexdigest(),
        }
        with self.engine.begin() as c:
            result: UUID | None = c.execute(
                insert(ingest_jobs)
                .values(
                    job_type="parse_snapshot", idempotency_key=key, status="queued", payload=payload
                )
                .on_conflict_do_nothing(index_elements=[ingest_jobs.c.idempotency_key])
                .returning(ingest_jobs.c.id)
            ).scalar_one_or_none()
            if result is not None:
                return result
            row = (
                c.execute(
                    sa.select(ingest_jobs.c.id, ingest_jobs.c.payload).where(
                        ingest_jobs.c.idempotency_key == key
                    )
                )
                .mappings()
                .one()
            )
            if row["payload"].get("configuration_sha256") != config_hash:
                raise ValueError("Profile/parser configuration changed; use a new revision")
            return row["id"]

    def status(self, job: UUID) -> dict[str, Any]:
        with self.engine.connect() as c:
            row = (
                c.execute(
                    sa.select(ingest_jobs).where(
                        ingest_jobs.c.id == job, ingest_jobs.c.job_type == "parse_snapshot"
                    )
                )
                .mappings()
                .one()
            )
            return {
                "job_id": str(job),
                "status": row["status"],
                "attempts": row["attempts"],
                "snapshot_id": row["payload"]["snapshot_id"],
                "result": row["payload"].get("result"),
                "last_error": row["last_error"],
            }

    def run(self, job: UUID) -> dict[str, Any]:
        token = str(uuid4())
        now = datetime.now(UTC)
        with self.engine.begin() as c:
            row = (
                c.execute(
                    sa.select(ingest_jobs)
                    .where(ingest_jobs.c.id == job, ingest_jobs.c.job_type == "parse_snapshot")
                    .with_for_update()
                )
                .mappings()
                .one()
            )
            payload = row["payload"]
            if row["status"] in ("succeeded", "quarantined"):
                return payload["result"] | {"cached": True}
            if row["status"] == "leased" and row["lease_until"] and row["lease_until"] > now:
                return {"job_id": str(job), "status": "busy", "cached": False}
            if row["attempts"] >= 4:
                c.execute(
                    ingest_jobs.update()
                    .where(ingest_jobs.c.id == job)
                    .values(status="failed", last_error={"code": "parse_retry_exhausted"})
                )
                return {
                    "job_id": str(job),
                    "status": "failed",
                    "inserted": 0,
                    "issues": ["parse_retry_exhausted"],
                }
            if payload["implementation_sha256"] != implementation_hash():
                raise ValueError("Parser code changed; use a new revision")
            payload = payload | {"lease_token": token}
            c.execute(
                ingest_jobs.update()
                .where(ingest_jobs.c.id == job)
                .values(
                    status="leased",
                    worker_id=f"parse-{token}",
                    payload=payload,
                    lease_until=now + timedelta(minutes=5),
                    attempts=row["attempts"] + 1,
                )
            )
        stopped = threading.Event()

        def heartbeat() -> None:
            while not stopped.wait(30):
                try:
                    with self.engine.begin() as c:
                        c.execute(
                            ingest_jobs.update()
                            .where(
                                ingest_jobs.c.id == job,
                                ingest_jobs.c.status == "leased",
                                ingest_jobs.c.payload["lease_token"].astext == token,
                            )
                            .values(lease_until=datetime.now(UTC) + timedelta(minutes=5))
                        )
                except Exception:
                    return  # Completion must still pass lease fencing; never log credential-bearing exceptions.

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            result = replay(
                self.snapshot(UUID(payload["snapshot_id"])),
                SourceProfile.model_validate(payload["profile"]),
                raw=self.raw,
                limits=ParseLimits.model_validate(payload["limits"]),
                revision=payload["revision"],
            )
        except (OSError, ValueError):
            result = ParseResult()
            result.issue(
                "snapshot_integrity_or_parse_error",
                "document",
                "Unable to verify raw snapshot; no facts emitted",
                "error",
            )
        finally:
            stopped.set()
            thread.join(timeout=1)
        result.metadata |= {
            "parse_job_id": str(job),
            "implementation_sha256": payload["implementation_sha256"],
            "lock_sha256": payload["lock_sha256"],
        }
        with self.engine.begin() as c:
            current = (
                c.execute(sa.select(ingest_jobs).where(ingest_jobs.c.id == job).with_for_update())
                .mappings()
                .one()
            )
            if (
                current["status"] != "leased"
                or current["payload"].get("lease_token") != token
                or current["lease_until"] <= datetime.now(UTC)
            ):
                raise ValueError("Parse lease lost; stale output not persisted")
            if any(
                str(obs.snapshot_id) != payload["snapshot_id"]
                or obs.parser_version != payload["parser_version"]
                or obs.transform_version != payload["transform_version"]
                for obs in result.observations
            ):
                raise ValueError("Parser output contract mismatch with leased snapshot/version")
            inserted = ObservationStore(c).save(result)
            status = "quarantined" if result.needs_review else "succeeded"
            counts = dict(Counter(o.fact_kind for o in result.observations))
            issue_counts = dict(Counter(i.code for i in result.issues))
            summary = {
                "job_id": str(job),
                "snapshot_id": payload["snapshot_id"],
                "status": status,
                "inserted": inserted,
                "observations": len(result.observations),
                "fact_kinds": counts,
                "issues": issue_counts,
                "parser_version": payload["parser_version"],
                "transform_version": TRANSFORM_VERSION,
                "metadata": result.metadata,
                "cached": False,
            }
            c.execute(
                ingest_jobs.update()
                .where(ingest_jobs.c.id == job)
                .values(
                    status=status,
                    lease_until=None,
                    payload=current["payload"] | {"result": summary},
                    last_error={
                        "code": "parse_needs_review",
                        "issues": [i.model_dump() for i in result.issues],
                    }
                    if result.needs_review
                    else None,
                )
            )
        return summary
