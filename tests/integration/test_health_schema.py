import os

from sqlalchemy import inspect

from tests.integration.test_health import probe


def test_unmigrated_schema_is_not_ready_without_running_migrations(empty_engine):
    environment = os.environ.copy()
    environment["POSTGRES_DB"] = empty_engine.url.database
    result = probe(environment)
    assert result["live_status"] == 200
    assert result["ready_status"] == 503
    assert result["ready_body"] == {
        "status": "unavailable",
        "database": "connected",
        "schema": "out_of_date",
    }
    assert inspect(empty_engine).get_table_names() == []


def test_unknown_database_revision_is_not_ready(migrated_engine):
    from sqlalchemy import text

    environment = os.environ.copy()
    environment["POSTGRES_DB"] = migrated_engine.url.database
    with migrated_engine.begin() as c:
        c.execute(text("UPDATE alembic_version SET version_num='unknown_future_revision'"))
    try:
        result = probe(environment)
        assert result["live_status"] == 200
        assert result["ready_status"] == 503
        assert result["ready_body"] == {
            "status": "unavailable",
            "database": "connected",
            "schema": "out_of_date",
        }
    finally:
        with migrated_engine.begin() as c:
            c.execute(text("UPDATE alembic_version SET version_num='0001_core'"))
