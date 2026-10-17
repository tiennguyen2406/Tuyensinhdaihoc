from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, text

from services.api.db.models import metadata
from services.crawler.state import Store
from tests.crawler.helpers import profile


def test_frontier_dedup_depth_lease_expiry_and_fencing(migrated_engine):
    store = Store(migrated_engine)
    run = store.start(profile(), budget=10)
    assert not store.enqueue(run, "https://example.edu.vn/#loop", 1)
    assert not store.enqueue(run, "https://example.edu.vn/deep", 5)
    one = store.lease(run, "one")
    assert one is not None
    assert store.lease(run, "two") is None
    with migrated_engine.begin() as c:
        c.execute(
            text("UPDATE ingest_jobs SET lease_until=now()-interval '1 second' WHERE id=:id"),
            {"id": one.id},
        )
    two = store.lease(run, "two")
    assert two is not None and two.id == one.id and two.token != one.token
    assert not store.finish(one)
    assert store.finish(two)
    assert store.lease(run, "three") is None


def test_shared_host_budget_across_runs_and_adapters(migrated_engine):
    store = Store(migrated_engine)
    a, b = store.start(profile(), 10), store.start(profile(), 10)
    host = f"{uuid4().hex}.edu.vn"
    now = datetime.now(UTC)
    token = uuid4()
    assert store.acquire(host, a, token, now=now)
    assert not Store(migrated_engine).acquire(host, b, uuid4(), now=now)
    store.release(host, token, now=now)
    assert not store.acquire(host, b, uuid4(), now=now + timedelta(seconds=1))
    assert store.acquire(host, b, uuid4(), now=now + timedelta(seconds=2))


def test_retry_after_and_review_block_all_workers(migrated_engine):
    store = Store(migrated_engine)
    run = store.start(profile(), 10)
    host = f"{uuid4().hex}.edu.vn"
    now, token = datetime.now(UTC), uuid4()
    assert store.acquire(host, run, token, now=now)
    store.release(host, token, status=429, retry="7200", now=now)
    assert not store.acquire(host, run, uuid4(), now=now + timedelta(hours=1))
    assert store.acquire(host, run, token, now=now + timedelta(hours=2))
    store.release(host, token, status=403, now=now + timedelta(hours=2))
    assert store.host(host)["needs_review"]
    assert not store.acquire(host, run, uuid4(), now=now + timedelta(days=1))


def test_request_budget_is_atomic_and_stop_is_persistent(migrated_engine):
    store = Store(migrated_engine)
    run = store.start(profile(), 1)
    assert store.acquire(f"{uuid4().hex}.edu.vn", run, uuid4())
    assert not store.acquire(f"{uuid4().hex}.edu.vn", run, uuid4())
    store.stop(run)
    assert store.lease(run, "worker") is None
    assert store.stats(run)["requests_used"] == 1


def test_0001_to_new_head_preserves_existing_rows(database_factory):
    from alembic import command

    from services.api.db.session import alembic_config, required_schema_heads

    engine = database_factory("crawler_upgrade")
    try:
        with engine.connect() as c:
            cfg = alembic_config()
            cfg.attributes["connection"] = c
            command.upgrade(cfg, "0001_core")
            c.execute(
                metadata.tables["sources"]
                .insert()
                .values(
                    canonical_url="https://fixture.invalid/",
                    domain="fixture.invalid",
                    publisher="TEST ONLY",
                    source_type="university",
                )
            )
            c.commit()
            command.upgrade(cfg, "head")
            assert (
                c.execute(select(metadata.tables["sources"].c.publisher)).scalar_one()
                == "TEST ONLY"
            )
            assert (
                c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                in required_schema_heads()
            )
    finally:
        engine.dispose()


def test_two_actual_workers_cannot_lease_same_task(migrated_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    store = Store(migrated_engine)
    run = store.start(profile(), 10)
    barrier = Barrier(2)

    def claim(worker):
        barrier.wait(timeout=5)
        return Store(migrated_engine).lease(run, worker)

    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = list(pool.map(claim, ["one", "two"]))
    assert sum(task is not None for task in tasks) == 1


def test_parallel_host_claim_and_expired_owner_cannot_release_new_owner(migrated_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    store = Store(migrated_engine)
    run = store.start(profile(), 10)
    host = f"{uuid4().hex}.edu.vn"
    barrier = Barrier(2)
    now = datetime.now(UTC)
    tokens = [uuid4(), uuid4()]

    def claim(token):
        barrier.wait(timeout=5)
        return Store(migrated_engine).acquire(host, run, token, now=now)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, tokens))
    assert sum(results) == 1
    old = tokens[results.index(True)]
    new = uuid4()
    assert store.acquire(host, run, new, now=now + timedelta(seconds=91))
    store.release(host, old, now=now + timedelta(seconds=92))
    assert store.host(host)["owner_token"] == new


def test_host_wait_does_not_exhaust_task_attempts(migrated_engine):
    store = Store(migrated_engine)
    run = store.start(profile(), 10)
    for _ in range(7):
        task = store.lease(run, "worker")
        assert task is not None and task.attempts == 1
        assert store.finish(task, status="retry_wait", error="host_wait")
    task = store.lease(run, "worker")
    assert task is not None
    assert store.finish(task)


def test_exhausted_lease_does_not_hide_remaining_ready_jobs(migrated_engine):
    store = Store(migrated_engine)
    run = store.start(profile(), 10)
    first = store.lease(run, "crashed")
    assert store.enqueue(run, "https://example.edu.vn/next", 1)
    with migrated_engine.begin() as c:
        c.execute(
            text(
                "UPDATE ingest_jobs SET attempts=4, lease_until=now()-interval '1 second' WHERE id=:id"
            ),
            {"id": first.id},
        )
    next_task = store.lease(run, "recovery")
    assert next_task is not None
    assert next_task.url == "https://example.edu.vn/next"
    assert store.stats(run)["jobs"] == {"failed": 1, "leased": 1}
