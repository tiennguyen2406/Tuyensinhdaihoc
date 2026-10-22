"""Real route/dependency fault paths, with no database or HTTP upstream."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from services.api.catalog import router
from services.api.main import app

PARAMS = dict(
    year=2026,
    method="TEST",
    scale_id="00000000-0000-0000-0000-000000000001",
    exam_version="TEST",
    basis_version="TEST",
    score="22",
)


def database_failure():
    return OperationalError("TEST PRIVATE SQL", None, Exception("TEST PRIVATE DRIVER DETAIL"))


@pytest.fixture
def fault_route(monkeypatch):
    events = []
    settings = dict(failure=None, reader=True, schema=True, query_error=database_failure())

    class Result:
        def scalar_one(self):
            return settings["reader"]

    class Transaction:
        def __enter__(self):
            events.append("transaction_enter")
            return self

        def __exit__(self, kind, error, traceback):
            events.append(("transaction_exit", kind))
            return False

    class Connection:
        def __enter__(self):
            events.append("connection_enter")
            return self

        def __exit__(self, kind, error, traceback):
            events.append(("connection_exit", kind))
            return False

        def execution_options(self, **options):
            assert options == {"isolation_level": "REPEATABLE READ"}
            events.append("repeatable_read")
            return self

        def begin(self):
            return Transaction()

        def scalar(self, statement):
            # Real search_advice/search_cutoffs execute their catalog version SQL
            # after the real dependency yields; fail at the DB boundary itself.
            events.append("query")
            raise settings["query_error"]

        def exec_driver_sql(self, sql):
            if sql.startswith("SET"):
                events.append(sql)
            else:
                events.append("reader_guard")
                if settings["failure"] == "guard":
                    raise database_failure()
            return Result()

    class Engine:
        def connect(self):
            events.append("connect")
            if settings["failure"] == "connect":
                raise database_failure()
            return Connection()

    def schema_check(c):
        events.append("schema_check")
        return settings["schema"]

    monkeypatch.setenv("CATALOG_DB_USER", "TEST_ONLY")
    monkeypatch.setenv("CATALOG_DB_PASSWORD", "TEST_ONLY")
    monkeypatch.setattr(router, "catalog_engine", Engine)
    monkeypatch.setattr(router, "schema_is_current", schema_check)
    # No dependency override: advice_snapshot and catalog_snapshot both execute.
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, settings, events


def assert_cleanup(events, kind):
    assert events[-2:] == [("transaction_exit", kind), ("connection_exit", kind)]
    assert events.count("transaction_enter") == events.count(("transaction_exit", kind)) == 1
    assert events.count("connection_enter") == events.count(("connection_exit", kind)) == 1


@pytest.mark.parametrize("failure", ["connect", "guard", "query"])
def test_advice_database_failures_are_structured_503_and_close_resources(fault_route, failure):
    client, settings, events = fault_route
    settings["failure"] = failure
    response = client.get("/api/v1/advice/cutoffs", params=PARAMS)
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "DATABASE_UNAVAILABLE"}}
    if failure == "connect":
        assert events == ["connect"]
    else:
        assert events[:6] == [
            "connect",
            "repeatable_read",
            "connection_enter",
            "transaction_enter",
            "SET TRANSACTION READ ONLY",
            "SET LOCAL statement_timeout='5000ms'",
        ]
        assert "reader_guard" in events
        assert ("query" in events) == (failure == "query")
        assert_cleanup(events, OperationalError)


def test_existing_cutoff_database_error_contract_stays_structured(fault_route):
    client, _, events = fault_route
    response = client.get("/api/v1/cutoffs", params={"year": 2026})
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "DATABASE_UNAVAILABLE"}}
    assert_cleanup(events, OperationalError)


@pytest.mark.parametrize("code", ["READER_REQUIRED", "SCHEMA_UNAVAILABLE"])
def test_intentional_dependency_errors_keep_their_codes_and_cleanup(fault_route, code):
    client, settings, events = fault_route
    settings["reader" if code == "READER_REQUIRED" else "schema"] = False
    response = client.get("/api/v1/advice/cutoffs", params=PARAMS)
    assert response.status_code == 503 and response.json()["detail"]["code"] == code
    assert "query" not in events
    assert_cleanup(events, HTTPException)


@pytest.mark.parametrize("status,code", [(422, "SCORE_OUT_OF_SCALE"), (409, "DATASET_CHANGED")])
def test_intentional_query_errors_are_not_rewritten_as_database_errors(fault_route, status, code):
    client, settings, events = fault_route
    settings["query_error"] = HTTPException(status, detail={"code": code})
    response = client.get("/api/v1/advice/cutoffs", params=PARAMS)
    assert response.status_code == status and response.json() == {"detail": {"code": code}}
    assert_cleanup(events, HTTPException)


def test_missing_reader_and_invalid_input_do_not_open_connections(fault_route, monkeypatch):
    client, _, events = fault_route
    monkeypatch.delenv("CATALOG_DB_PASSWORD")
    response = client.get("/api/v1/advice/cutoffs", params=PARAMS)
    assert response.status_code == 503 and response.json()["detail"]["code"] == "READER_REQUIRED"
    assert events == []
    response = client.get("/api/v1/advice/cutoffs", params=PARAMS | {"score": "NaN"})
    assert response.status_code == 422 and events == []
