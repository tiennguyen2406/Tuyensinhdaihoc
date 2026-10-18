"""Build files first, then atomically register and finalize fenced refresh leases."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import url2pathname
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine

from services.api.db.models import dataset_releases, ingest_jobs
from services.api.db.session import schema_is_current
from services.data.publication.bootstrap import audit
from services.data.releases.artifacts import store, verify_bundle
from services.data.releases.roles import require
from services.data.releases.snapshot import capture

LOCK = "T09:canonical-release-builder/1"


def local_path(uri: str) -> Path:
    parts = urlsplit(uri)
    if parts.scheme != "file" or parts.netloc:
        raise ValueError("Integrity conflict: release URI must be local file")
    return Path(url2pathname(parts.path))


def verify(c: Connection, version: int) -> dict[str, Any]:
    row = (
        c.execute(sa.select(dataset_releases).where(dataset_releases.c.version == version))
        .mappings()
        .one_or_none()
    )
    if not row:
        raise ValueError("No registered release for requested version")
    bundle = verify_bundle(local_path(row["manifest_uri"]), row["manifest_sha256"])
    m = bundle["manifest"]
    if (
        row["version"] != m["catalog_version"]
        or row["cutoff_count"] != bundle["cutoff_count"]
        or row["metadata"] != m
    ):
        raise ValueError("Integrity conflict: database/manifest binding")
    return dict(
        release_id=str(row["id"]),
        version=version,
        manifest_uri=row["manifest_uri"],
        manifest_sha256=row["manifest_sha256"],
        cutoff_count=row["cutoff_count"],
        coverage=bundle["coverage"],
        verified=True,
        cached=True,
    )


def json_row(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: json_row(v) for k, v in value.items()}
    return value


def transition(c: Connection, actor: str, old: dict[str, Any], changes: dict[str, Any]) -> None:
    after = old | changes
    audit(
        c,
        actor,
        "refresh_" + after["status"],
        "refresh_job",
        old["id"],
        json_row(old),
        dict(
            row=json_row(after),
            transaction_id=c.scalar(sa.text("SELECT pg_current_xact_id()::text")),
        ),
        "T09 verified internal release lease/finalization",
        str(old["id"]),
    )
    c.execute(ingest_jobs.update().where(ingest_jobs.c.id == old["id"]).values(**changes))


def claim(c: Connection, actor: str, version: int) -> list[tuple[UUID, str]]:
    now = datetime.now(timezone.utc)
    jobs = (
        c.execute(
            sa.select(ingest_jobs)
            .where(
                ingest_jobs.c.job_type == "refresh_serving",
                sa.cast(ingest_jobs.c.payload["dataset_version"].astext, sa.BigInteger) <= version,
                sa.or_(
                    sa.and_(
                        ingest_jobs.c.status.in_(["queued", "retry_wait"]),
                        ingest_jobs.c.available_at <= now,
                    ),
                    sa.and_(ingest_jobs.c.status == "leased", ingest_jobs.c.lease_until <= now),
                ),
            )
            .order_by(ingest_jobs.c.id)
            .with_for_update(skip_locked=True)
        )
        .mappings()
        .all()
    )
    leases = []
    for row in jobs:
        token = str(uuid4())
        transition(
            c,
            actor,
            dict(row),
            dict(
                status="leased",
                attempts=row["attempts"] + 1,
                lease_until=now + timedelta(minutes=5),
                worker_id=actor,
                payload=row["payload"] | {"release_lease_token": token},
                last_error=None,
            ),
        )
        leases.append((row["id"], token))
    return leases


def finalize(
    c: Connection, actor: str, leases: list[tuple[UUID, str]], result: dict[str, Any]
) -> None:
    for ident, token in leases:
        row = dict(
            c.execute(sa.select(ingest_jobs).where(ingest_jobs.c.id == ident).with_for_update())
            .mappings()
            .one()
        )
        if (
            row["status"] != "leased"
            or row["payload"].get("release_lease_token") != token
            or row["lease_until"] <= datetime.now(timezone.utc)
        ):
            raise ValueError("Refresh lease lost; retry after recovery")
        requested = row["payload"]["dataset_version"]
        payload = row["payload"] | {
            "release_result": dict(
                requested_version=requested,
                actual_version=result["version"],
                release_id=result["release_id"],
                manifest_sha256=result["manifest_sha256"],
                outcome="built" if requested == result["version"] else "coalesced",
            )
        }
        transition(
            c,
            actor,
            row,
            dict(status="succeeded", lease_until=None, last_error=None, payload=payload),
        )


def register(c: Connection, actor: str, bundle: dict[str, Any]) -> dict[str, Any]:
    manifest = bundle["manifest"]
    version = manifest["catalog_version"]
    existing = c.scalar(
        sa.select(dataset_releases.c.id).where(dataset_releases.c.version == version)
    )
    if existing:
        result = verify(c, version)
        if result["manifest_sha256"] != bundle["manifest_sha256"]:
            raise ValueError("Integrity conflict: version already registered with another manifest")
        return result
    values = dict(
        id=uuid4(),
        version=version,
        manifest_uri=bundle["manifest_uri"],
        manifest_sha256=bundle["manifest_sha256"],
        cutoff_count=bundle["cutoff_count"],
        metadata=manifest,
        published_at=datetime.now(timezone.utc),
    )
    audit(
        c,
        actor,
        "register_release",
        "dataset_release",
        values["id"],
        None,
        dict(
            row=json_row(values),
            transaction_id=c.scalar(sa.text("SELECT pg_current_xact_id()::text")),
        ),
        "Verified internal DEV snapshot; no public redistribution",
        "release:" + str(version),
    )
    c.execute(dataset_releases.insert().values(**values))
    return verify(c, version) | {"cached": False}


def build(db: Engine, root: Path, version: int | None = None) -> dict[str, Any]:
    with db.connect() as c:
        with c.begin():
            actor = require(c)
            if not schema_is_current(c):
                raise ValueError("Schema is not current; release CLI never migrates")
            c.exec_driver_sql("SET LOCAL lock_timeout='10s'")
            # ponytail: one DEV builder at a time; partition locks only for measured throughput.
            c.execute(sa.select(sa.func.pg_advisory_lock(sa.func.hashtext(LOCK))))
        try:
            with c.begin():
                current = c.scalar(sa.text("SELECT dataset_version FROM catalog_state"))
                selected = current if version is None else version
                if selected > current:
                    raise ValueError("Cannot build a future catalog version")
                existing = c.scalar(
                    sa.select(dataset_releases.c.id).where(dataset_releases.c.version == selected)
                )
                if existing:
                    # Replay keeps the original manifest/code/time, independent of live labels.
                    registered = verify(c, selected)
                    bundle = verify_bundle(
                        local_path(registered["manifest_uri"]), registered["manifest_sha256"]
                    )
            if existing:
                pass  # Still recover due/expired refresh leases against this verified release.
            elif selected < current:
                # Only a completed, verifiable orphan can recover an old version; never query is_current to reconstruct it.
                bundle = verify_bundle(root.resolve() / f"version-{selected}" / "manifest.json")
                if bundle["manifest"]["catalog_version"] != selected:
                    raise ValueError("Integrity conflict: orphan version mismatch")
            else:
                c.execution_options(isolation_level="REPEATABLE READ")
                with c.begin():
                    c.exec_driver_sql("SET TRANSACTION READ ONLY")
                    snapshot = capture(c)
                    # Publication may have committed before our first RR read. Its real version wins.
                    if version is not None and snapshot["catalog_version"] != version:
                        raise ValueError("Catalog advanced before snapshot; retry explicit version")
                    bundle = store(root, snapshot)
                c.execution_options(isolation_level="READ COMMITTED")
            with c.begin():
                leases = claim(c, actor, bundle["manifest"]["catalog_version"])
            try:
                with c.begin():
                    checked = verify_bundle(
                        local_path(bundle["manifest_uri"]), bundle["manifest_sha256"]
                    )
                    result = register(c, actor, checked)
                    finalize(c, actor, leases, result)
                return result
            except Exception:
                # Releasable errors retry immediately. Process death leaves durable leases to expire.
                with c.begin():
                    for ident, token in leases:
                        row = dict(
                            c.execute(
                                sa.select(ingest_jobs)
                                .where(ingest_jobs.c.id == ident)
                                .with_for_update()
                            )
                            .mappings()
                            .one()
                        )
                        if (
                            row["status"] == "leased"
                            and row["payload"].get("release_lease_token") == token
                            and row["lease_until"] > datetime.now(timezone.utc)
                        ):
                            transition(
                                c,
                                actor,
                                row,
                                dict(
                                    status="retry_wait",
                                    lease_until=None,
                                    available_at=datetime.now(timezone.utc),
                                    last_error={
                                        "code": "release_registration_or_finalization_failed"
                                    },
                                ),
                            )
                raise
        finally:
            c.rollback()
            c.execution_options(isolation_level="READ COMMITTED")
            with c.begin():
                c.execute(sa.select(sa.func.pg_advisory_unlock(sa.func.hashtext(LOCK))))
