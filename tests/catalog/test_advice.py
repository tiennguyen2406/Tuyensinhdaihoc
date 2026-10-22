"""Advice foundation: synthetic PostgreSQL only; numeric matches are not approvals."""

import secrets
from decimal import Decimal
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from fastapi.testclient import TestClient

from services.api.catalog import cursor, dto, queries
from services.api.db.models import metadata
from services.api.db.session import alembic_config
from services.api.main import app
from tests.fixtures import make_scope


@pytest.fixture(scope="module")
def advice_store(database_factory):
    db = database_factory("advice")
    with db.begin() as c:
        cfg = alembic_config()
        cfg.attributes["connection"] = c
        command.upgrade(cfg, "head")
        f = make_scope(c)
        t = metadata.tables
        c.execute(t["universities"].update().values(verification_status="verified"))
        c.execute(t["catalog_state"].update().values(dataset_version=3))
        base = {
            "combination_status": "confirmed_none",
            "basis_version": "TEST-final/1",
            "conditions": {"schema_version": "conditions/1", "kind": "none"},
        }
        c.execute(t["program_admissions"].update().values(condition_dsl=base))
        numeric_ids = []
        for i, score in enumerate(["1", "17", "19", "20", "22", "22.99", "23", "25.99999", "26"]):
            scope = f["add"](
                "program_admissions",
                **(f["scope_values"] | {"round_key": f"TEST-{i}", "condition_dsl": base}),
            )
            ident = f["add"](
                "cutoff_scores",
                **(f["cutoff_values"] | {"program_admission_id": scope, "score": Decimal(score)}),
            )
            numeric_ids.append(ident)
        aggregate = f["add"](
            "program_admissions",
            **(
                f["scope_values"]
                | {
                    "round_key": "AGG",
                    "condition_dsl": base | {"combination_status": "source_aggregate"},
                }
            ),
        )
        f["add"]("cutoff_scores", **(f["cutoff_values"] | {"program_admission_id": aggregate}))
        missing = f["add"]("program_admissions", **(f["scope_values"] | {"round_key": "MISSING"}))
        f["add"]("cutoff_scores", **(f["cutoff_values"] | {"program_admission_id": missing}))
        method = c.scalar(
            sa.select(t["admission_methods"].c.code).where(
                t["admission_methods"].c.id == f["method"]
            )
        )
        f["empty_year_scale"] = f["add"](
            "score_scales",
            method_id=f["method"],
            admission_year=2025,
            code="TEST",
            exam_version="TEST ONLY",
            min_score=Decimal("1"),
            max_score=Decimal("30"),
            basis_description="TEST ONLY empty year",
            primary_snapshot_id=f["snapshot"],
        )
    yield (
        db,
        f,
        numeric_ids,
        dict(
            year=2026,
            method=method,
            scale_id=str(f["scale"]),
            exam_version="TEST ONLY",
            basis_version="TEST-final/1",
            score="22",
        ),
    )
    db.dispose()


@pytest.fixture
def advice_client(advice_store):
    from services.api.catalog import router

    db, f, ids, params = advice_store

    def snapshot():
        with db.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            c.exec_driver_sql("SET LOCAL statement_timeout='5000ms'")
            yield c

    # Only the connection changes. The real route, validation and SQL gates run.
    app.dependency_overrides[router.advice_snapshot] = snapshot
    try:
        with TestClient(app) as client:
            yield client, db, f, ids, params
    finally:
        app.dependency_overrides.pop(router.advice_snapshot, None)


def test_missing_score_is_rejected_before_database_access():
    with TestClient(app) as client:
        response = client.get("/api/v1/advice/cutoffs", params={"year": 2026})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "score,want",
    [
        ("22", ["1", "17", "19", "20", "22", "22.99"]),
        ("25", ["1", "17", "19", "20", "22", "22.99", "23", "25.99999"]),
    ],
)
def test_sql_numeric_threshold_has_strict_upper_bound_and_no_lower_bound(advice_store, score, want):
    from services.api.catalog.advice import threshold_page

    db, _, ids, values = advice_store
    params = dto.AdviceParams(**(values | {"score": score, "limit": 2}))
    cut = metadata.tables["cutoff_scores"]
    candidates = (
        queries.fact_query({"year": 2026})
        .with_only_columns(cut.c.id.label("cutoff_id"))
        .where(cut.c.id.in_(ids))
    )
    found, last = [], None
    with db.connect() as c:
        while True:
            rows = list(c.execute(threshold_page(candidates, params, last)).mappings())
            found.extend(str(r["score"].normalize()) for r in rows[:2])
            if len(rows) <= 2:
                break
            last = (str(rows[1]["cutoff_id"]),)
    assert sorted(Decimal(x) for x in found) == [Decimal(x) for x in want]
    assert len(found) == len(set(found))


@pytest.mark.parametrize(
    "score",
    ["", "NaN", "Infinity", "-1", "+22", "2e1", "22,5", "1,000.1", " 22", "22.000001", "31", "0"],
)
def test_invalid_and_out_of_scale_scores(advice_client, score):
    client, _, _, _, params = advice_client
    response = client.get("/api/v1/advice/cutoffs", params=params | {"score": score})
    assert response.status_code == 422


def test_aggregate_missing_context_and_unavailable_rule_fail_closed(advice_client):
    client, _, _, _, params = advice_client
    response = client.get("/api/v1/advice/cutoffs", params=params)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [] and body["status"] == "unsupported"
    assert body["excluded_summary"] == {
        "AGGREGATE_SCOPE": 1,
        "MISSING_CONTEXT": 1,
        "UNAVAILABLE_RULE": 10,
    }
    assert body["context"]["score"] == "22" and body["dataset_version"] == 3
    assert not body["has_more"] and body["next_cursor"] is None


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"method": "SPT"}, "METHOD_MISMATCH"),
        ({"exam_version": "other"}, "EXAM_VERSION_MISMATCH"),
        ({"year": 2025}, "CROSS_YEAR_UNSUPPORTED"),
        ({"scale_id": str(uuid4())}, "SCALE_NOT_FOUND"),
    ],
)
def test_context_mismatch_never_uses_equal_max_or_another_year(advice_client, changes, reason):
    client, _, _, _, params = advice_client
    body = client.get("/api/v1/advice/cutoffs", params=params | changes).json()
    assert body["items"] == [] and body["status"] == "unsupported"
    assert reason in body["unsupported_reasons"]
    # Bounds of a known selected scale are always enforced, before compatibility.
    response = client.get("/api/v1/advice/cutoffs", params=params | changes | {"score": "31"})
    if "scale_id" in changes:
        assert response.status_code == 200 and reason in response.json()["unsupported_reasons"]
    else:
        assert (
            response.status_code == 422
            and response.json()["detail"]["code"] == "SCORE_OUT_OF_SCALE"
        )


def test_basis_filter_and_unknown_filters(advice_client):
    client, _, _, _, params = advice_client
    body = client.get("/api/v1/advice/cutoffs", params=params | {"basis_version": "other"}).json()
    assert body["items"] == [] and body["excluded_summary"]["BASIS_MISMATCH"] == 10
    assert (
        client.get(
            "/api/v1/advice/cutoffs", params=params | {"allow_unverified": "true"}
        ).status_code
        == 422
    )


def test_major_and_combination_filters_do_not_manufacture_bindings(advice_client):
    client, _, _, _, params = advice_client
    body = client.get("/api/v1/advice/cutoffs", params=params | {"major_id": str(uuid4())}).json()
    assert body["status"] == "no_data" and body["excluded_summary"] == {} and body["items"] == []
    body = client.get(
        "/api/v1/advice/cutoffs", params=params | {"combination_id": str(uuid4())}
    ).json()
    assert body["items"] == [] and body["excluded_summary"] == {"AGGREGATE_SCOPE": 1}


def test_predicate_and_rule_presence_do_not_bypass_eligibility(advice_store):
    from services.api.catalog.advice import classified_candidates

    db, _, _, _ = advice_store
    t = metadata.tables
    # This rollback transaction is in the same synthetic DB, never DEV.
    with db.connect() as c, c.begin() as tx:
        f = make_scope(c)
        c.execute(
            t["universities"]
            .update()
            .where(t["universities"].c.id == f["university"])
            .values(verification_status="verified")
        )
        base = {
            "basis_version": "TEST/1",
            "combination_status": "confirmed_none",
            "conditions": {
                "schema_version": "conditions/1",
                "kind": "predicate",
                "expression": {"TEST": True},
            },
        }
        c.execute(
            t["program_admissions"]
            .update()
            .where(t["program_admissions"].c.id == f["scope"])
            .values(condition_dsl=base)
        )
        method = c.scalar(
            sa.select(t["admission_methods"].c.code).where(
                t["admission_methods"].c.id == f["method"]
            )
        )
        params = dto.AdviceParams(
            year=2026,
            university_id=f["university"],
            method=method,
            scale_id=f["scale"],
            exam_version="TEST ONLY",
            basis_version="TEST/1",
            score="22",
        )
        assert (
            c.execute(classified_candidates(params)).mappings().one()["reason"]
            == "CONDITIONS_NOT_EVALUATED"
        )
        rule = f["add"](
            "scoring_rules",
            program_year_id=f["offering"],
            method_id=f["method"],
            output_scale_id=f["scale"],
            rule_key="TEST",
            version=1,
            input_schema={},
            formula_dsl={},
            rounding_dsl={},
            required_components=[],
            primary_snapshot_id=f["snapshot"],
            verification_status="verified",
            is_current=True,
        )
        c.execute(
            t["program_admissions"]
            .update()
            .where(t["program_admissions"].c.id == f["scope"])
            .values(
                condition_dsl=base
                | {"conditions": {"schema_version": "conditions/1", "kind": "none"}},
                scoring_rule_id=rule,
            )
        )
        assert (
            c.execute(classified_candidates(params)).mappings().one()["reason"]
            == "RULE_NOT_EVALUATED"
        )
        tx.rollback()


def test_unavailable_year_is_empty_without_fallback(advice_client):
    client, _, f, _, params = advice_client
    body = client.get(
        "/api/v1/advice/cutoffs",
        params=params | {"year": 2025, "scale_id": str(f["empty_year_scale"])},
    ).json()
    assert body["status"] == "no_data" and body["items"] == []
    assert body["context"]["year"] == 2025 and body["excluded_summary"] == {}
    assert body["coverage"]["canonical_cutoff_count"] == 0


def test_response_stays_in_one_read_only_repeatable_snapshot(advice_client, monkeypatch):
    client, db, f, _, params = advice_client
    original = queries.version
    called = False

    def change_after_version(c):
        nonlocal called
        assert c.exec_driver_sql("SHOW transaction_read_only").scalar_one() == "on"
        assert c.exec_driver_sql("SHOW transaction_isolation").scalar_one() == "repeatable read"
        assert c.exec_driver_sql("SHOW statement_timeout").scalar_one() == "5s"
        value = original(c)
        if not called:
            called = True
            with db.begin() as writer:
                writer.execute(
                    metadata.tables["cutoff_scores"]
                    .update()
                    .where(metadata.tables["cutoff_scores"].c.id == f["cutoff"])
                    .values(verification_status="disputed")
                )
                writer.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
        return value

    monkeypatch.setattr(queries, "version", change_after_version)
    try:
        first = client.get("/api/v1/advice/cutoffs", params=params).json()
        assert first["dataset_version"] == 3 and first["items"] == []
        assert first["coverage"]["canonical_cutoff_count"] == 12
        assert first["excluded_summary"]["UNAVAILABLE_RULE"] == 10
        second = client.get("/api/v1/advice/cutoffs", params=params).json()
        assert second["dataset_version"] == 4 and second["items"] == []
        assert second["coverage"]["canonical_cutoff_count"] == 11
        assert second["excluded_summary"]["UNAVAILABLE_RULE"] == 9
    finally:
        with db.begin() as c:
            c.execute(
                metadata.tables["cutoff_scores"]
                .update()
                .where(metadata.tables["cutoff_scores"].c.id == f["cutoff"])
                .values(verification_status="verified")
            )
            c.execute(metadata.tables["catalog_state"].update().values(dataset_version=3))


def test_real_reader_route_does_not_fallback_to_owner(advice_store, monkeypatch):
    from services.api.catalog import router
    from services.api.catalog.roles import provision_reader

    db, _, _, params = advice_store
    with TestClient(app) as client:
        monkeypatch.delenv("CATALOG_DB_USER", raising=False)
        monkeypatch.delenv("CATALOG_DB_PASSWORD", raising=False)
        assert (
            client.get("/api/v1/advice/cutoffs", params=params).json()["detail"]["code"]
            == "READER_REQUIRED"
        )
        monkeypatch.setenv("CATALOG_DB_USER", "TEST ONLY")
        monkeypatch.setenv("CATALOG_DB_PASSWORD", "TEST ONLY")
        monkeypatch.setattr(router, "catalog_engine", lambda: db)
        assert client.get("/api/v1/advice/cutoffs", params=params).status_code == 503
        user, password = "test_advice_" + uuid4().hex[:16], secrets.token_hex(24)
        with db.begin() as c:
            provision_reader(c)
            c.exec_driver_sql(
                f"CREATE ROLE {user} LOGIN PASSWORD '{password}' NOSUPERUSER NOCREATEDB NOCREATEROLE"
            )
            c.exec_driver_sql(f"GRANT eduradar_reader TO {user}")
        reader = sa.create_engine(
            db.url.set(username=user, password=password), hide_parameters=True
        )
        monkeypatch.setattr(router, "catalog_engine", lambda: reader)
        try:
            response = client.get("/api/v1/advice/cutoffs", params=params)
            assert response.status_code == 200 and response.json()["items"] == []
            with reader.connect() as c:
                assert c.exec_driver_sql("SELECT current_user").scalar_one() == user
                assert (
                    c.exec_driver_sql(
                        "SELECT has_table_privilege('cutoff_scores','UPDATE')"
                    ).scalar_one()
                    is False
                )
            with db.begin() as c:
                c.exec_driver_sql(f"ALTER ROLE {user} BYPASSRLS")
            assert client.get("/api/v1/advice/cutoffs", params=params).status_code == 503
            with db.begin() as c:
                c.exec_driver_sql(f"ALTER ROLE {user} NOBYPASSRLS")
                c.exec_driver_sql("CREATE TABLE test_advice_owner_marker (id integer)")
                c.exec_driver_sql(f"ALTER TABLE test_advice_owner_marker OWNER TO {user}")
                c.exec_driver_sql(f"REVOKE ALL ON test_advice_owner_marker FROM {user}")
            # Ownership survives REVOKE; reader must still be rejected.
            assert client.get("/api/v1/advice/cutoffs", params=params).status_code == 503
        finally:
            reader.dispose()


def test_cursor_is_bound_to_score_all_context_filters_and_version(advice_client):
    client, db, _, ids, values = advice_client
    params = dto.AdviceParams(**values)
    token = cursor.token(
        dict(
            contract="cursor/2",
            binding=cursor.binding("advice", params.model_dump()),
            dataset_version=3,
            after=[str(ids[0])],
        )
    )
    for changes in [
        {"score": "23"},
        {"basis_version": "other"},
        {"year": 2025},
        {"exam_version": "other"},
        {"method": "SPT"},
        {"major_id": str(uuid4())},
        {"combination_id": str(uuid4())},
        {"campus": "OTHER"},
        {"limit": 1},
    ]:
        assert (
            client.get(
                "/api/v1/advice/cutoffs", params=values | {"cursor": token} | changes
            ).status_code
            == 422
        )
    assert (
        client.get("/api/v1/advice/cutoffs", params=values | {"cursor": token}).status_code == 200
    )
    with db.begin() as c:
        c.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
    try:
        response = client.get("/api/v1/advice/cutoffs", params=values | {"cursor": token})
        assert (
            response.status_code == 409 and response.json()["detail"]["code"] == "DATASET_CHANGED"
        )
    finally:
        with db.begin() as c:
            c.execute(metadata.tables["catalog_state"].update().values(dataset_version=3))
