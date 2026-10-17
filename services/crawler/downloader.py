"""Raw-only standalone worker. All HTTP adapters go through request()."""

import hashlib
import http.client
import re
import time
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import sqlalchemy as sa
from protego import Protego
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from services.api.db.models import crawl_fetches as fetches
from services.api.db.models import crawl_runs as runs
from services.api.db.models import crawl_schedules as schedules
from services.api.db.models import source_snapshots as snapshots
from services.api.db.models import sources
from services.api.source_profiles import SourceProfile
from services.crawler.raw import RawStorage
from services.crawler.state import Store, Task
from services.crawler.transport import USER_AGENT, Response, Transport
from services.crawler.urls import URLPolicy, canonicalize


class Deferred(Exception):
    def __init__(self, delay: float, code: str = "host_wait") -> None:
        self.delay, self.code = delay, code


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("a", "link", "iframe", "embed", "object"):
            for key, value in attrs:
                if key in ("href", "src", "data") and value:
                    self.links.append(value)


def links(body: bytes, base: str) -> list[tuple[str, str]]:
    parser = LinkParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    result = []
    for href in parser.links:
        try:
            url = canonicalize(href, base)
            suffix = urlsplit(url).path.lower()
            kind = (
                "attachment"
                if suffix.endswith((".pdf", ".xlsx", ".xls", ".csv", ".json"))
                else "html"
            )
            result.append((url, kind))
        except ValueError:
            continue
    return result


def challenged(response: Response) -> bool:
    sample = response.body[:131072].lower()
    return any(
        mark in sample
        for mark in (b"cf-chl-", b"cf-chl ", b"g-recaptcha", b"h-captcha", b"verify you are human")
    )


def media_type(response: Response) -> str:
    mime = (
        response.headers.get("content-type", "application/octet-stream")
        .split(";", 1)[0]
        .strip()
        .lower()
    )
    # Never relabel an HTML error as a PDF or spreadsheet.
    if mime == "application/pdf" and not response.body.lstrip().startswith(b"%PDF-"):
        raise ValueError("pdf_signature_mismatch")
    if (
        mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        and not response.body.startswith(b"PK")
    ):
        raise ValueError("xlsx_signature_mismatch")
    if mime not in {
        "text/html",
        "application/xhtml+xml",
        "application/pdf",
        "text/plain",
        "text/csv",
        "application/json",
        "application/octet-stream",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/xml",
        "text/xml",
    }:
        raise ValueError("unsupported_media_type")
    return mime


class Crawler:
    def __init__(
        self,
        store: Store,
        raw: RawStorage,
        profile: SourceProfile,
        *,
        policy: URLPolicy | None = None,
    ) -> None:
        self.store, self.raw, self.profile = store, raw, profile
        self.policy = policy or URLPolicy(profile)
        self.transport = Transport(self.policy)

    def _source(self, c: Connection, url: str) -> UUID:
        c.execute(
            insert(sources)
            .values(
                canonical_url=url,
                domain=urlsplit(url).hostname,
                publisher=self.profile.university_key,
                source_type="admission_office",
                authority_scope=self.profile.authority_scope,
                verification_status="unverified",
            )
            .on_conflict_do_nothing(index_elements=[sources.c.canonical_url])
        )
        return c.execute(sa.select(sources.c.id).where(sources.c.canonical_url == url)).scalar_one()

    def latest(self, url: str) -> dict[str, Any] | None:
        with self.store.engine.connect() as c:
            row = (
                c.execute(
                    sa.select(snapshots, sources.c.etag, sources.c.last_modified)
                    .select_from(
                        sources.join(fetches, fetches.c.source_id == sources.c.id).join(
                            snapshots, snapshots.c.id == fetches.c.snapshot_id
                        )
                    )
                    .where(sources.c.canonical_url == url)
                    .order_by(fetches.c.id.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None

    def record(
        self,
        response: Response,
        *,
        requested_url: str | None = None,
        kind: str = "html",
        task: Task | None = None,
        outcome: str = "fetched",
    ) -> UUID | None:
        url = requested_url or response.url
        previous = self.latest(url)
        digest_uri = None
        mime = response.headers.get("content-type", "application/octet-stream").split(";", 1)[0]
        if response.status == 200:
            mime = media_type(response)
            digest_uri = self.raw.put(response.body)
        elif response.status == 304 and previous is None:
            raise ValueError("304_without_snapshot")
        validators = {k: v for k, v in response.headers.items() if k in ("etag", "last-modified")}
        validators |= {
            "final_url": response.url,
            "media_type": mime,
            "byte_size": str(len(response.body)),
        }
        snapshot_id: UUID | None = None
        with self.store.engine.begin() as c:
            if task and not self.store._owned(c, task):
                raise ValueError("lease_lost")
            source_id = self._source(c, url)
            if digest_uri:
                digest, uri = digest_uri
                c.execute(
                    insert(snapshots)
                    .values(
                        source_id=source_id,
                        raw_hash=digest,
                        raw_uri=uri,
                        final_url=response.url,
                        media_type=mime,
                        byte_size=len(response.body),
                    )
                    .on_conflict_do_nothing(
                        index_elements=[snapshots.c.source_id, snapshots.c.raw_hash]
                    )
                )
                snapshot_id = c.execute(
                    sa.select(snapshots.c.id).where(
                        snapshots.c.source_id == source_id, snapshots.c.raw_hash == digest
                    )
                ).scalar_one()
            elif response.status == 304 and previous:
                snapshot_id = previous["id"]
            c.execute(
                fetches.insert().values(
                    source_id=source_id,
                    snapshot_id=snapshot_id,
                    http_status=response.status,
                    outcome=outcome,
                    elapsed_ms=response.elapsed_ms,
                    response_validators=validators,
                )
            )
            updates: dict[str, Any] = {"last_checked_at": datetime.now(UTC)}
            if response.status in (200, 304):
                updates |= {
                    "etag": response.headers.get(
                        "etag",
                        previous.get("etag") if previous and response.status == 304 else None,
                    ),
                    "last_modified": response.headers.get(
                        "last-modified",
                        previous.get("last_modified")
                        if previous and response.status == 304
                        else None,
                    ),
                }
                interval = (
                    self.profile.attachment_interval_seconds
                    if kind == "attachment"
                    else self.profile.html_interval_seconds
                )
                now = datetime.now(UTC)
                schedule_values = dict(
                    profile_id=self.profile.profile_id,
                    resource_kind=kind,
                    interval_seconds=interval,
                    due_at=now + timedelta(seconds=interval),
                )
                # A 200 response to a conditional request is still a server-validated representation;
                # last_unconditional is set separately only when no validators were sent.
                c.execute(
                    insert(schedules)
                    .values(source_id=source_id, **schedule_values)
                    .on_conflict_do_update(
                        index_elements=[schedules.c.source_id], set_=schedule_values
                    )
                )
            c.execute(sources.update().where(sources.c.id == source_id).values(**updates))
        return snapshot_id

    def request(
        self,
        run: UUID,
        url: str,
        headers: dict[str, str],
        *,
        task: Task | None = None,
        document: bool = False,
        interval: float = 2,
        robots: bool = False,
    ) -> Response:
        self.policy.check(url, document=document)
        host = urlsplit(url).hostname or ""
        token = uuid4()
        if task and not self.store.heartbeat(task):
            raise ValueError("lease_lost")
        while True:
            h = self.store.host(host)
            if h["needs_review"]:
                self.store.mark_review(run, "host_needs_review")
                raise Deferred(0, "host_needs_review")
            if self.store.acquire(host, run, token, interval=interval):
                break
            now = datetime.now(UTC)
            due = max(h[k] or now for k in ("busy_until", "next_allowed_at", "blocked_until"))
            delay = max(0.25, (due - now).total_seconds())
            if delay > 5 or self.store.stats(run)["status"] != "running":
                raise Deferred(delay)
            time.sleep(delay)
            if task and not self.store.heartbeat(task):
                raise ValueError("lease_lost")
        response = None
        try:
            response = self.transport.get(
                url, headers, document=document, max_bytes=512000 if robots else None
            )
            return response
        except (OSError, ValueError, http.client.HTTPException):
            with self.store.engine.begin() as c:
                if task is None or self.store._owned(c, task):
                    c.execute(
                        fetches.insert().values(
                            source_id=self._source(c, url),
                            outcome="request_error",
                            error_code="network_or_body_policy",
                            response_validators={"requested_url": url},
                        )
                    )
            raise
        finally:
            self.store.release(
                host,
                token,
                status=response.status if response else 0,
                retry=response.headers.get("retry-after") if response else None,
                challenge=challenged(response) if response else False,
                interval=interval,
            )
            if response and (response.status == 403 or challenged(response)):
                self.store.mark_review(run, "403_or_captcha")

    def robots(
        self, run: UUID, url: str, *, task: Task | None = None, document: bool = False
    ) -> tuple[Protego, float]:
        parsed = urlsplit(self.policy.check(url, document=document))
        origin = f"{parsed.scheme}://{parsed.netloc}"
        host = parsed.hostname or ""
        cached = self.store.host(host)["robots_cache"].get(origin)
        now = datetime.now(UTC)
        fresh = False
        if not cached or datetime.fromisoformat(cached["expires_at"]) <= now:
            robot_url = origin + "/robots.txt"
            seen: set[str] = set()
            while True:
                if robot_url in seen or len(seen) >= 6:
                    raise ValueError("robots_redirect_loop")
                seen.add(robot_url)
                response = self.request(
                    run, robot_url, {}, task=task, document=document, robots=True
                )
                self.record(response, kind="robots", task=task, outcome="robots")
                if response.status in (301, 302, 303, 307, 308):
                    robot_url = canonicalize(response.headers.get("location", ""), robot_url)
                    # Conservative: robots must remain on its original origin, no cross-host bootstrap.
                    if (
                        urlsplit(robot_url).netloc != parsed.netloc
                        or urlsplit(robot_url).scheme != parsed.scheme
                    ):
                        raise ValueError("robots_cross_origin_redirect_requires_review")
                    continue
                break
            if response.status == 200 and not challenged(response):
                text = response.body.decode("utf-8", errors="replace")
                if "html" in response.headers.get("content-type", "").lower() or any(
                    marker in text[:2048].lower() for marker in ("<!doctype html", "<html")
                ):
                    self.store.mark_review(run, "robots_html_requires_review")
                    raise ValueError("robots_html_requires_review")
            elif response.status in (404, 410):
                text = ""
            elif response.status in (429, 503) or response.status >= 500:
                raise Deferred(60, "robots_unavailable")
            else:
                self.store.mark_review(run, "robots_unavailable_or_denied")
                raise ValueError("robots_unavailable_or_denied")
            cached = {
                "text": text,
                "status": response.status,
                "url": response.url,
                "sha256": hashlib.sha256(response.body).hexdigest(),
                "checked_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=24)).isoformat(),
            }
            self.store.cache_robots(host, origin, cached)
            fresh = True
        parser = Protego.parse(cached["text"])
        delay = max(2, 1 / self.profile.requests_per_second, parser.crawl_delay(USER_AGENT) or 0)
        rate = parser.request_rate(USER_AGENT)
        if rate:
            delay = max(delay, rate.seconds / rate.requests)
        if fresh:
            self.store.honor_delay(host, delay)
        if parser.visit_time(USER_AGENT):
            raise ValueError("robots_visit_time_requires_review")
        return parser, delay

    def download(self, task: Task) -> None:
        current = task.url
        seen: set[str] = set()
        previous = self.latest(task.url)
        headers: dict[str, str] = {}
        unconditional = True
        if previous:
            with self.store.engine.connect() as c:
                last = c.execute(
                    sa.select(schedules.c.last_unconditional_at).where(
                        schedules.c.source_id == previous["source_id"]
                    )
                ).scalar_one_or_none()
            if last and last > datetime.now(UTC) - timedelta(days=7):
                headers = {
                    k: v
                    for k, v in {
                        "If-None-Match": previous["etag"],
                        "If-Modified-Since": previous["last_modified"],
                    }.items()
                    if v
                }
                unconditional = not headers
        while True:
            if current in seen or len(seen) >= 6:
                raise ValueError("redirect_loop_or_limit")
            seen.add(current)
            parser, interval = self.robots(
                task.run, current, task=task, document=task.kind == "attachment"
            )
            if not parser.can_fetch(current, USER_AGENT):
                raise ValueError("robots_disallowed")
            response = self.request(
                task.run,
                current,
                headers if current == task.url else {},
                task=task,
                document=task.kind == "attachment",
                interval=interval,
            )
            if response.status in (301, 302, 303, 307, 308):
                self.record(response, task=task, outcome="redirect")
                target = canonicalize(response.headers.get("location", ""), current)
                self.policy.check(target, document=task.kind == "attachment")
                if urlsplit(current).scheme == "https" and urlsplit(target).scheme != "https":
                    raise ValueError("https_downgrade_redirect")
                current = target
                continue
            self.record(
                response,
                requested_url=task.url,
                kind=task.kind,
                task=task,
                outcome="not_modified" if response.status == 304 else "fetched",
            )
            if response.status == 403 or challenged(response):
                self.store.finish(task, status="quarantined", error="403_or_captcha")
                return
            if response.status == 429 or response.status >= 500:
                h = self.store.host(urlsplit(current).hostname or "")
                delay = max(
                    2**task.attempts,
                    ((h["blocked_until"] or datetime.now(UTC)) - datetime.now(UTC)).total_seconds(),
                )
                raise Deferred(delay, "http_retry")
            if response.status not in (200, 304):
                raise ValueError("http_non_success")
            latest = self.latest(task.url)
            if latest is None:
                raise ValueError("missing_snapshot")
            if unconditional and response.status == 200:
                with self.store.engine.begin() as c:
                    c.execute(
                        schedules.update()
                        .where(schedules.c.source_id == latest["source_id"])
                        .values(last_unconditional_at=datetime.now(UTC))
                    )
            body = self.raw.read(latest["raw_hash"])
            found = (
                links(body, current)
                if latest["media_type"] in ("text/html", "application/xhtml+xml")
                else []
            )

            def persist(c: Connection) -> None:
                for url, kind in found:
                    self.store.enqueue(task.run, url, task.depth + 1, kind, connection=c)

            self.store.finish(task, persist=persist)
            return

    def work(self, run: UUID, *, worker: str = "cli") -> None:
        while self.store.stats(run)["status"] == "running":
            task = self.store.lease(run, worker)
            if task is None:
                stats = self.store.stats(run)
                if not any(stats["jobs"].get(k, 0) for k in ("queued", "retry_wait", "leased")):
                    with self.store.engine.begin() as c:
                        c.execute(
                            runs.update()
                            .where(runs.c.id == run, runs.c.status == "running")
                            .values(status="completed")
                        )
                return
            try:
                self.download(task)
            except Deferred as exc:
                self.store.finish(task, status="retry_wait", error=exc.code, delay=exc.delay)
                return
            except ValueError as exc:
                code = str(exc)
                if not re.fullmatch(r"[a-z0-9_]+", code):
                    code = "url_or_content_policy"
                self.store.finish(task, status="failed", error=code)
            except (OSError, TimeoutError, http.client.HTTPException):
                self.store.finish(
                    task, status="retry_wait", error="network_error", delay=2**task.attempts
                )
                return
