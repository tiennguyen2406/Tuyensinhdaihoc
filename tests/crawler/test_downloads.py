import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text

from services.api.db.models import crawl_fetches, crawl_schedules, source_snapshots, sources
from services.crawler.downloader import Crawler
from services.crawler.raw import RawStorage
from services.crawler.state import Store
from services.crawler.urls import URLPolicy
from tests.crawler.helpers import profile


@contextmanager
def fake_site(routes):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            seen.append((self.path, dict(self.headers)))
            status, headers, body = routes(self.path, self.headers)
            self.send_response(status)
            for k, v in headers.items():
                self.send_header(k, v)
            if "Content-Length" not in headers:
                self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = f"fixture-{uuid4().hex}.edu.vn"
    base = f"http://{host}:{server.server_port}"
    prof = profile(allowed_hosts=[host], seed_urls=[f"https://{host}/"])
    # Deliberate test-only bypass of the production HTTPS seed validator.
    prof = prof.model_copy(update={"seed_urls": [HttpUrl(base + "/")]})

    def resolver(*args):
        return [(2, 1, 6, "", ("127.0.0.1", server.server_port))]

    policy = URLPolicy(prof, resolver=resolver, test_local=True)
    try:
        yield prof, policy, seen
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def make_crawler(engine, tmp_path, prof, policy):
    return Crawler(Store(engine, test_local=True), RawStorage(tmp_path), prof, policy=policy)


def test_attachment_conditional_get_and_a_b_a_reuses_snapshots(migrated_engine, tmp_path):
    version = [b"%PDF-1.7 A"]

    def routes(path, headers):
        if path == "/robots.txt":
            return 200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /"
        if path == "/":
            if headers.get("If-None-Match") == '"root"':
                return 304, {"ETag": '"root"'}, b""
            return (
                200,
                {"Content-Type": "text/html", "ETag": '"root"'},
                b'<a href="/file.pdf">attachment</a><a href="/#loop">loop</a>',
            )
        etag = '"' + version[0].decode()[-1] + '"'
        if headers.get("If-None-Match") == etag:
            return 304, {"ETag": etag}, b""
        return (
            200,
            {
                "Content-Type": "application/pdf",
                "ETag": etag,
                "Last-Modified": "Wed, 01 Jan 2025 00:00:00 GMT",
            },
            version[0],
        )

    with fake_site(routes) as (prof, policy, seen):
        crawler = make_crawler(migrated_engine, tmp_path, prof, policy)
        snapshots = []
        for content in [b"%PDF-1.7 A", b"%PDF-1.7 A", b"%PDF-1.7 B", b"%PDF-1.7 A"]:
            version[0] = content
            run = crawler.store.start(prof, 10)
            crawler.work(run)
            with migrated_engine.connect() as c:
                source_id = c.execute(
                    select(sources.c.id).where(
                        sources.c.canonical_url == str(prof.seed_urls[0]) + "file.pdf"
                    )
                ).scalar_one()
                snapshots.append(
                    c.execute(
                        select(crawl_fetches.c.snapshot_id)
                        .where(crawl_fetches.c.source_id == source_id)
                        .order_by(crawl_fetches.c.id.desc())
                        .limit(1)
                    ).scalar_one()
                )
                assert (
                    c.execute(
                        select(crawl_schedules.c.resource_kind).where(
                            crawl_schedules.c.source_id == source_id
                        )
                    ).scalar_one()
                    == "attachment"
                )
        assert snapshots[0] == snapshots[1] == snapshots[3] != snapshots[2]
        with migrated_engine.connect() as c:
            assert (
                c.execute(
                    select(func.count())
                    .select_from(source_snapshots)
                    .where(source_snapshots.c.source_id == source_id)
                ).scalar_one()
                == 2
            )
            assert c.execute(
                select(crawl_fetches.c.http_status)
                .where(crawl_fetches.c.source_id == source_id)
                .order_by(crawl_fetches.c.id)
            ).scalars().all() == [200, 304, 200, 200]
        assert any(headers.get("If-None-Match") for path, headers in seen if path == "/file.pdf")
        assert len([path for path, _ in seen if path == "/robots.txt"]) == 1
        assert len([path for path, _ in seen if path == "/"]) == 4
        count = len(seen)
        crawler.work(run)
        assert len(seen) == count  # Completed run cannot download again.
        # Even an incorrect unchanged ETag must not suppress the periodic unconditional check.
        with migrated_engine.begin() as c:
            c.execute(
                crawl_schedules.update()
                .where(crawl_schedules.c.source_id == source_id)
                .values(last_unconditional_at=text("now()-interval '8 days'"))
            )
        version[0] = b"%PDF-1.7 C"
        run = crawler.store.start(prof, 10)
        crawler.work(run)
        last_headers = [headers for path, headers in seen if path == "/file.pdf"][-1]
        assert "If-None-Match" not in last_headers
        assert "If-Modified-Since" not in last_headers


def test_robots_redirect_loop_and_off_allowlist(migrated_engine, tmp_path):
    def routes(path, headers):
        if path == "/robots.txt":
            return (
                200,
                {"Content-Type": "text/plain"},
                b"User-agent: *\nDisallow: /private*\nAllow: /private-ok$",
            )
        if path == "/":
            return (
                200,
                {"Content-Type": "text/html"},
                b'<a href="/private/secret">no</a><a href="/jump">jump</a><a href="/loop">loop</a>',
            )
        if path == "/jump":
            return 302, {"Location": "http://169.254.169.254/latest/meta-data/"}, b""
        return 302, {"Location": "/loop"}, b""

    with fake_site(routes) as (prof, policy, seen):
        crawler = make_crawler(migrated_engine, tmp_path, prof, policy)
        run = crawler.store.start(prof, 10)
        crawler.work(run)
        assert "/private/secret" not in [path for path, _ in seen]
        assert [path for path, _ in seen].count("/loop") == 1
        assert crawler.store.stats(run)["jobs"]["failed"] == 3


@pytest.mark.parametrize(
    "status,body", [(403, b"Forbidden"), (200, b"<html>verify you are human cf-chl CAPTCHA</html>")]
)
def test_forbidden_or_captcha_pauses_host(migrated_engine, tmp_path, status, body):
    def routes(path, headers):
        if path == "/robots.txt":
            return 200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /"
        return status, {"Content-Type": "text/html"}, body

    with fake_site(routes) as (prof, policy, seen):
        crawler = make_crawler(migrated_engine, tmp_path, prof, policy)
        run = crawler.store.start(prof, 5)
        crawler.work(run)
        assert crawler.store.stats(run)["status"] == "needs_review"
        assert crawler.store.host(prof.allowed_hosts[0])["needs_review"]
        assert len(seen) == 2


def test_429_persists_delay_without_sleeping_worker(migrated_engine, tmp_path):
    def routes(path, headers):
        if path == "/robots.txt":
            return 200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /"
        return 429, {"Retry-After": "7200", "Content-Type": "text/plain"}, b"slow down"

    with fake_site(routes) as (prof, policy, seen):
        crawler = make_crawler(migrated_engine, tmp_path, prof, policy)
        run = crawler.store.start(prof, 5)
        crawler.work(run)
        assert crawler.store.stats(run)["jobs"]["retry_wait"] == 1
        assert len(seen) == 2


def test_raw_storage_immutable_and_detects_corruption(tmp_path):
    raw = RawStorage(tmp_path)
    digest, uri = raw.put(b"A")
    assert raw.put(b"A") == (digest, uri)
    assert raw.read(digest) == b"A"
    raw.path(digest).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash"):
        raw.read(digest)
    with pytest.raises(ValueError):
        raw.put(b"A")


def test_retry_recovery_after_snapshot_commit_creates_no_duplicate_snapshot_or_jobs(
    migrated_engine, tmp_path
):
    def routes(path, headers):
        if path == "/robots.txt":
            return 200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /"
        return 200, {"Content-Type": "text/html"}, b'<a href="/#self">self</a>'

    with fake_site(routes) as (prof, policy, seen):
        crawler = make_crawler(migrated_engine, tmp_path, prof, policy)
        run = crawler.store.start(prof, 5)
        # Inject a crash at task completion, after raw/snapshot persistence.
        original = crawler.store.finish

        def crash(*args, **kwargs):
            raise RuntimeError("Simulated process crash")

        crawler.store.finish = crash
        with pytest.raises(RuntimeError):
            crawler.work(run)
        crawler.store.finish = original
        with migrated_engine.begin() as c:
            from services.api.db.models import ingest_jobs

            c.execute(
                ingest_jobs.update()
                .where(ingest_jobs.c.payload["run_id"].astext == str(run))
                .values(lease_until=text("now()-interval '1 second'"))
            )
        crawler.work(run)
        assert crawler.store.stats(run)["jobs"] == {"succeeded": 1}
        with migrated_engine.connect() as c:
            count = c.execute(
                select(func.count())
                .select_from(source_snapshots)
                .join(sources)
                .where(sources.c.canonical_url == str(prof.seed_urls[0]))
            ).scalar_one()
            assert count == 1


def test_body_limit_signature_and_same_host_redirect_chain(migrated_engine, tmp_path):
    def routes(path, headers):
        if path == "/robots.txt":
            return 200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /"
        if path == "/":
            return 302, {"Location": "/final"}, b""
        return 200, {"Content-Type": "application/pdf"}, b"<html>this is not a PDF</html>"

    with fake_site(routes) as (prof, policy, seen):
        crawler = make_crawler(migrated_engine, tmp_path, prof, policy)
        run = crawler.store.start(prof, 5)
        crawler.work(run)
        assert [path for path, _ in seen] == ["/robots.txt", "/", "/final"]
        assert crawler.store.stats(run)["jobs"] == {"failed": 1}
        with migrated_engine.connect() as c:
            assert (
                c.execute(
                    select(func.count())
                    .select_from(source_snapshots)
                    .join(sources)
                    .where(sources.c.canonical_url == str(prof.seed_urls[0]))
                ).scalar_one()
                == 0
            )
    with fake_site(lambda p, h: (200, {"Content-Type": "text/plain"}, b"X" * 50)) as (
        prof,
        policy,
        seen,
    ):
        from services.crawler.transport import Transport

        with pytest.raises(ValueError, match="body_too_large"):
            Transport(policy, max_bytes=10).get(str(prof.seed_urls[0]), {})


def test_truncated_body_and_deadline_never_produce_snapshot(tmp_path):
    import time

    from services.crawler.transport import Transport

    def routes(path, headers):
        time.sleep(0.3)
        return 200, {"Content-Type": "text/plain"}, b"too late"

    with fake_site(routes) as (prof, policy, seen):
        with pytest.raises((OSError, TimeoutError)):
            Transport(policy, timeout=0.1).get(str(prof.seed_urls[0]), {})


def test_truncated_content_length_is_rejected():
    from services.crawler.transport import Transport

    with fake_site(
        lambda p, h: (200, {"Content-Type": "text/plain", "Content-Length": "100"}, b"partial")
    ) as (prof, policy, seen):
        with pytest.raises(OSError, match="incomplete_body"):
            Transport(policy).get(str(prof.seed_urls[0]), {})


def test_raw_storage_refuses_source_directory():
    from services.api.db.session import ROOT

    with pytest.raises(ValueError, match="ignored"):
        RawStorage(ROOT / "services" / "raw")
