"""PostgreSQL coordination; network I/O never holds a transaction open."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection, Engine

from services.api.db.models import crawl_host_states as hosts
from services.api.db.models import crawl_runs as runs
from services.api.db.models import ingest_jobs as jobs
from services.api.source_profiles import SourceProfile
from services.crawler.urls import URLPolicy, canonicalize, retry_after


@dataclass(frozen=True)
class Task:
    id: UUID
    run: UUID
    token: UUID
    url: str
    depth: int
    kind: str
    attempts: int


class Store:
    def __init__(self, engine: Engine, *, test_local: bool = False) -> None:
        self.engine = engine
        self.test_local = test_local

    def start(self, profile: SourceProfile, budget: int, *, preflight: bool = False) -> UUID:
        if budget < 1 or budget > 1000:
            raise ValueError("Budget must be 1..1000 (all wire requests including robots)")
        if profile.render_js or profile.parser != "raw_http":
            raise ValueError("Only raw HTTP adapter implemented")
        if profile.review_status != "eligible" and not preflight:
            raise ValueError("Profile not eligible; perform source/robots review first")
        with self.engine.begin() as c:
            run: UUID = c.execute(
                runs.insert()
                .values(
                    profile_id=profile.profile_id,
                    profile=profile.model_dump(mode="json"),
                    url_budget=budget,
                )
                .returning(runs.c.id)
            ).scalar_one()
        if not preflight:
            for url in profile.seed_urls:
                self.enqueue(run, str(url), 0)
        return run

    def stats(self, run: UUID) -> dict[str, Any]:
        with self.engine.connect() as c:
            row = dict(c.execute(sa.select(runs).where(runs.c.id == run)).mappings().one())
            row["jobs"] = dict(
                c.execute(
                    sa.select(jobs.c.status, sa.func.count())
                    .where(
                        jobs.c.job_type == "raw_fetch", jobs.c.payload["run_id"].astext == str(run)
                    )
                    .group_by(jobs.c.status)
                ).all()
            )
            return row

    def stop(self, run: UUID, reason: str = "operator") -> None:
        with self.engine.begin() as c:
            c.execute(
                runs.update()
                .where(runs.c.id == run, runs.c.status != "needs_review")
                .values(status="paused", stop_reason=reason)
            )

    def resume(self, run: UUID, additional_budget: int = 0) -> None:
        with self.engine.begin() as c:
            row = (
                c.execute(sa.select(runs).where(runs.c.id == run).with_for_update())
                .mappings()
                .one()
            )
            if row["status"] == "needs_review":
                raise ValueError("Source requires operator review before a new run")
            if additional_budget < 0 or row["url_budget"] + additional_budget > 1000:
                raise ValueError("Budget out of range")
            c.execute(
                runs.update()
                .where(runs.c.id == run)
                .values(
                    status="running",
                    stop_reason=None,
                    url_budget=row["url_budget"] + additional_budget,
                )
            )

    def enqueue(
        self,
        run: UUID,
        url: str,
        depth: int,
        kind: str = "html",
        *,
        connection: Connection | None = None,
        test_local: bool = False,
    ) -> bool:
        if connection is None:
            with self.engine.begin() as c:
                return self.enqueue(run, url, depth, kind, connection=c, test_local=test_local)
        c = connection
        row = c.execute(sa.select(runs).where(runs.c.id == run).with_for_update()).mappings().one()
        profile_data = row["profile"]
        if self.test_local:
            profile_data = profile_data | {
                "seed_urls": [f"https://{profile_data['allowed_hosts'][0]}/"]
            }
        profile = SourceProfile.model_validate(profile_data)
        url = canonicalize(url)
        if not URLPolicy(profile, test_local=test_local or self.test_local).discoverable(
            url, depth, document=kind == "attachment"
        ):
            return False
        existing: list[dict[str, Any]] = list(
            c.execute(
                sa.select(jobs.c.payload).where(
                    jobs.c.job_type == "raw_fetch", jobs.c.payload["run_id"].astext == str(run)
                )
            )
            .scalars()
            .all()
        )
        if len(existing) >= profile.max_discovery_urls:
            return False
        path = urlsplit(url)._replace(query="", fragment="").geturl()
        if (
            sum(
                urlsplit(p["url"])._replace(query="", fragment="").geturl() == path
                for p in existing
            )
            >= profile.max_query_variants_per_path
        ):
            return False
        result = c.execute(
            insert(jobs)
            .values(
                job_type="raw_fetch",
                status="queued",
                idempotency_key=f"fetch:{run}:{sha256(url.encode()).hexdigest()}",
                payload={"run_id": str(run), "url": url, "depth": depth, "kind": kind},
                priority=-depth,
            )
            .on_conflict_do_nothing(index_elements=[jobs.c.idempotency_key])
            .returning(jobs.c.id)
        )
        return result.scalar_one_or_none() is not None

    def lease(self, run: UUID, worker: str) -> Task | None:
        now = datetime.now(UTC)
        with self.engine.begin() as c:
            if (
                c.execute(sa.select(runs.c.status).where(runs.c.id == run)).scalar_one()
                != "running"
            ):
                return None
            while True:
                row = (
                    c.execute(
                        sa.select(jobs)
                        .where(
                            jobs.c.job_type == "raw_fetch",
                            jobs.c.payload["run_id"].astext == str(run),
                            jobs.c.available_at <= now,
                            sa.or_(
                                jobs.c.status.in_(["queued", "retry_wait"]),
                                sa.and_(jobs.c.status == "leased", jobs.c.lease_until < now),
                            ),
                        )
                        .order_by(jobs.c.priority.desc(), jobs.c.created_at, jobs.c.id)
                        .with_for_update(skip_locked=True)
                        .limit(1)
                    )
                    .mappings()
                    .first()
                )
                if row is None:
                    return None
                token = uuid4()
                payload = row["payload"] | {"lease_token": str(token)}
                attempts = row["attempts"] + 1
                if attempts > 4:
                    c.execute(
                        jobs.update()
                        .where(jobs.c.id == row["id"])
                        .values(status="failed", last_error={"code": "retry_exhausted"})
                    )
                    continue
                c.execute(
                    jobs.update()
                    .where(jobs.c.id == row["id"])
                    .values(
                        status="leased",
                        worker_id=worker,
                        lease_until=now + timedelta(minutes=5),
                        attempts=attempts,
                        payload=payload,
                    )
                )
                return Task(
                    row["id"],
                    run,
                    token,
                    payload["url"],
                    payload["depth"],
                    payload["kind"],
                    attempts,
                )

    def _owned(self, c: Connection, task: Task) -> bool:
        row = (
            c.execute(
                sa.select(jobs.c.payload, jobs.c.lease_until, jobs.c.status)
                .where(jobs.c.id == task.id)
                .with_for_update()
            )
            .mappings()
            .one()
        )
        return bool(
            row["status"] == "leased"
            and row["lease_until"] > datetime.now(UTC)
            and row["payload"].get("lease_token") == str(task.token)
        )

    def heartbeat(self, task: Task) -> bool:
        with self.engine.begin() as c:
            if not self._owned(c, task):
                return False
            c.execute(
                jobs.update()
                .where(jobs.c.id == task.id)
                .values(lease_until=datetime.now(UTC) + timedelta(minutes=5))
            )
            return True

    def finish(
        self,
        task: Task,
        *,
        status: str = "succeeded",
        error: str | None = None,
        delay: float = 0,
        persist: Callable[[Connection], None] | None = None,
    ) -> bool:
        with self.engine.begin() as c:
            if not self._owned(c, task):
                return False
            if persist:
                persist(c)
            if status == "retry_wait" and error == "host_wait":
                c.execute(
                    jobs.update()
                    .where(jobs.c.id == task.id)
                    .values(attempts=sa.func.greatest(jobs.c.attempts - 1, 0))
                )
            c.execute(
                jobs.update()
                .where(jobs.c.id == task.id)
                .values(
                    status=status,
                    lease_until=None,
                    last_error={"code": error} if error else None,
                    available_at=datetime.now(UTC) + timedelta(seconds=delay),
                )
            )
            return True

    def host(self, host: str) -> dict[str, Any]:
        with self.engine.begin() as c:
            c.execute(insert(hosts).values(host=host).on_conflict_do_nothing())
            return dict(c.execute(sa.select(hosts).where(hosts.c.host == host)).mappings().one())

    def acquire(
        self, host: str, run: UUID, token: UUID, *, interval: float = 2, now: datetime | None = None
    ) -> bool:
        now = now or datetime.now(UTC)
        with self.engine.begin() as c:
            c.execute(insert(hosts).values(host=host, next_allowed_at=now).on_conflict_do_nothing())
            h = (
                c.execute(sa.select(hosts).where(hosts.c.host == host).with_for_update())
                .mappings()
                .one()
            )
            if h["needs_review"] or any(
                h[key] and h[key] > now
                for key in ("busy_until", "next_allowed_at", "blocked_until")
            ):
                return False
            r = (
                c.execute(sa.select(runs).where(runs.c.id == run).with_for_update())
                .mappings()
                .one()
            )
            if r["status"] != "running":
                return False
            if r["requests_used"] >= r["url_budget"]:
                c.execute(
                    runs.update()
                    .where(runs.c.id == run)
                    .values(status="paused", stop_reason="budget_exhausted")
                )
                return False
            c.execute(
                runs.update().where(runs.c.id == run).values(requests_used=r["requests_used"] + 1)
            )
            # Hard transport deadline 30 s; host lease 90 s. Space from release as well.
            c.execute(
                hosts.update()
                .where(hosts.c.host == host)
                .values(
                    owner_token=token,
                    busy_until=now + timedelta(seconds=90),
                    next_allowed_at=now + timedelta(seconds=max(2, interval)),
                )
            )
            return True

    def release(
        self,
        host: str,
        token: UUID,
        *,
        status: int = 0,
        retry: str | None = None,
        challenge: bool = False,
        interval: float = 2,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(UTC)
        with self.engine.begin() as c:
            row = (
                c.execute(sa.select(hosts).where(hosts.c.host == host).with_for_update())
                .mappings()
                .one()
            )
            if row["owner_token"] != token:
                return
            failures = row["failures"] + 1 if status == 0 or status >= 500 else 0
            blocked = row["blocked_until"]
            until = retry_after(retry, now) if status in (429, 503) else None
            if failures >= 5:
                until = max(until or now, now + timedelta(minutes=15))
            if until:
                blocked = max(blocked or now, until)
            c.execute(
                hosts.update()
                .where(hosts.c.host == host)
                .values(
                    owner_token=None,
                    busy_until=None,
                    next_allowed_at=max(
                        row["next_allowed_at"], now + timedelta(seconds=max(2, interval))
                    ),
                    blocked_until=blocked,
                    failures=failures,
                    needs_review=row["needs_review"] or status == 403 or challenge,
                )
            )

    def cache_robots(self, host: str, origin: str, data: dict[str, Any]) -> None:
        with self.engine.begin() as c:
            row = (
                c.execute(sa.select(hosts).where(hosts.c.host == host).with_for_update())
                .mappings()
                .one()
            )
            c.execute(
                hosts.update()
                .where(hosts.c.host == host)
                .values(robots_cache=row["robots_cache"] | {origin: data})
            )

    def mark_review(self, run: UUID, reason: str) -> None:
        with self.engine.begin() as c:
            c.execute(
                runs.update()
                .where(runs.c.id == run)
                .values(status="needs_review", stop_reason=reason)
            )

    def honor_delay(self, host: str, seconds: float) -> None:
        with self.engine.begin() as c:
            c.execute(
                hosts.update()
                .where(hosts.c.host == host)
                .values(
                    next_allowed_at=sa.func.greatest(
                        hosts.c.next_allowed_at,
                        datetime.now(UTC) + timedelta(seconds=max(2, seconds)),
                    )
                )
            )
