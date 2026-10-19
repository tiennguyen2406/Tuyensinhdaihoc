"""Scale regressions on retained synthetic PostgreSQL DBs, never the pilot."""

from contextlib import contextmanager

import pytest
import sqlalchemy as sa
from alembic import command
from fastapi.testclient import TestClient

from services.api.catalog import queries
from services.api.catalog.router import catalog_snapshot
from services.api.db.session import alembic_config
from services.api.db.validators import count_canonical_cutoffs
from services.api.main import app
from tests.catalog.scale_fixture import seed_catalog


@pytest.fixture(scope="module")
def scale_dbs(database_factory):
    engines = []
    for count in (200, 20_000):
        db = database_factory(f"querycost{count}")
        with db.begin() as c:
            cfg = alembic_config()
            cfg.attributes["connection"] = c
            command.upgrade(cfg, "head")
            seed_catalog(c, count)
            c.exec_driver_sql("ANALYZE")
        engines.append(db)
    yield engines
    for db in engines:
        db.dispose()


@contextmanager
def client_for(db):
    def snapshot():
        with db.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            yield c

    app.dependency_overrides[catalog_snapshot] = snapshot
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(catalog_snapshot, None)


def test_query_count_does_not_scale_with_off_page_facts(scale_dbs):
    measurements = []
    for db in scale_dbs:
        statements = []

        def record(c, cursor, statement, parameters, context, many):
            statements.append((statement, cursor.rowcount))

        sa.event.listen(db, "after_cursor_execute", record)
        try:
            with client_for(db) as client:
                for endpoint in ["universities", "programs", "cutoffs"]:
                    statements.clear()
                    response = client.get(f"/api/v1/{endpoint}", params={"year": 2024, "limit": 1})
                    assert response.status_code == 200
                    assert len(response.json()["items"]) == 1
                    source_queries = [(s, n) for s, n in statements if "JOIN cutoff_evidence" in s]
                    assert len(source_queries) == 1
                    if endpoint == "cutoffs":
                        # Primary + two evidence links for just one returned cutoff.
                        assert source_queries[0][1] == 3
                    # A bounded entity query fetches limit+1, not the filtered universe.
                    pages = [(s, n) for s, n in statements if "LIMIT" in s]
                    assert len(pages) == 1 and pages[0][1] == 2
                    measurements.append((endpoint, len(statements)))
        finally:
            sa.event.remove(db, "after_cursor_execute", record)
    assert measurements[:3] == measurements[3:]
    assert all(n <= 10 for _, n in measurements)


@pytest.mark.parametrize("limit", [1, 50, 200])
def test_dto_materialization_is_page_bounded(scale_dbs, monkeypatch, limit):
    count = 0
    original = queries.cutoff

    def observed(*args, **kwargs):
        nonlocal count
        count += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(queries, "cutoff", observed)
    with client_for(scale_dbs[-1]) as client:
        result = client.get("/api/v1/cutoffs", params={"year": 2026, "limit": limit}).json()
        assert len(result["items"]) == count == limit
        assert result["has_more"]


def test_walk_large_sql_pages_and_aggregate_counting_policy(scale_dbs):
    db = scale_dbs[-1]
    with client_for(db) as client:
        coverage = client.get("/api/v1/data-coverage", params={"year": 2026}).json()
        with db.connect() as c:
            assert (
                sum(x["canonical_cutoff_count"] for x in coverage["items"])
                == count_canonical_cutoffs(c)
                == 20_000
            )
        for endpoint, key, expected_count in [
            ("universities", "id", 200),
            ("programs", "program_year_id", coverage["coverage"]["offering_count"]),
            ("cutoffs", "id", coverage["coverage"]["canonical_cutoff_count"]),
        ]:
            seen = []
            params = {"year": 2026, "limit": 200}
            while True:
                page = client.get(f"/api/v1/{endpoint}", params=params).json()
                seen.extend(x[key] for x in page["items"])
                if not page["has_more"]:
                    break
                params["cursor"] = page["next_cursor"]
            assert len(seen) == len(set(seen)) == expected_count


def test_first_middle_final_pages_at_fifty(scale_dbs):
    with client_for(scale_dbs[0]) as client:
        for endpoint, key, expected in [
            ("universities", "id", 100),
            ("programs", "program_year_id", 100),
            ("cutoffs", "id", 200),
        ]:
            params = {"year": 2024, "limit": 50}
            seen = []
            page_lengths = []
            while True:
                response = client.get(f"/api/v1/{endpoint}", params=params)
                assert response.status_code == 200
                page = response.json()
                page_lengths.append(len(page["items"]))
                seen.extend(x[key] for x in page["items"])
                if not page["has_more"]:
                    assert page["next_cursor"] is None
                    break
                params["cursor"] = page["next_cursor"]
            assert len(seen) == len(set(seen)) == expected
            assert page_lengths == [50] * (expected // 50)
