from uuid import uuid4

import pytest
import sqlalchemy as sa

from services.api.db.models import metadata
from tests.fixtures import make_scope
from tests.releases.conftest import release_db as release_db


def test_accents_alias_and_similar_universities_remain_distinct(catalog_client):
    client, _, fixtures = catalog_client
    for query in ["Bách khoa", "bach khoa"]:
        response = client.get("/api/v1/universities", params={"year": 2026, "query": query})
        assert response.status_code == 200
        page = response.json()
        assert len(page["items"]) == len({x["id"] for x in page["items"]}) == 3
        assert page["dataset_version"] == 3 and page["release"] is None
    for query in ["HUST", "Bach khoa Thu do"]:
        page = client.get("/api/v1/universities", params={"year": 2026, "query": query}).json()
        assert [x["id"] for x in page["items"]] == [str(fixtures[0]["university"])]


def test_offerings_cutoffs_year_and_evidence_fanout(catalog_client):
    client, _, f = catalog_client
    params = {"year": 2026, "university_id": str(f[0]["university"])}
    page = client.get("/api/v1/programs", params=params).json()
    assert len(page["items"]) == 2
    assert len({x["program_id"] for x in page["items"]}) == 1
    assert {x["campus"] for x in page["items"]} == {"BVH", "BVS"}
    assert all(x["tuition"] is None and x["scholarships"] is None for x in page["items"])
    cutoffs = client.get("/api/v1/cutoffs", params=params).json()
    assert len(cutoffs["items"]) == 2
    assert all(x["score"] == "24.12345" for x in cutoffs["items"])
    assert (
        len(client.get("/api/v1/cutoffs", params=params | {"campus": "BVH"}).json()["items"]) == 1
    )
    assert (
        client.get("/api/v1/cutoffs", params=params | {"method": "DOES-NOT-EXIST"}).json()["items"]
        == []
    )
    for year in [2024, 2025]:
        for endpoint in ["programs", "cutoffs"]:
            empty = client.get(f"/api/v1/{endpoint}", params=params | {"year": year}).json()
            assert empty["items"] == [] and empty["coverage"]["canonical_cutoff_count"] == 0
    sources = cutoffs["items"][0]["sources"]
    assert sources and all(s["snapshot_id"] == str(f[0]["snapshot"]) for s in sources)
    assert (
        client.get(f"/api/v1/sources/{f[0]['snapshot']}", params={"year": 2026}).status_code == 200
    )
    assert (
        client.get(f"/api/v1/sources/{f[0]['snapshot']}", params={"year": 2025}).status_code == 404
    )


def test_cursor_signature_filters_and_version(catalog_client):
    client, db, _ = catalog_client
    params = {"year": 2026, "limit": 1}
    first = client.get("/api/v1/universities", params=params).json()
    assert first["has_more"] and first["next_cursor"]
    cursor = first["next_cursor"]
    second = client.get("/api/v1/universities", params=params | {"cursor": cursor}).json()
    assert second["items"][0]["id"] != first["items"][0]["id"]
    assert (
        client.get(
            "/api/v1/universities", params=params | {"cursor": cursor, "query": "HUST"}
        ).status_code
        == 422
    )
    altered = cursor[:-1] + ("a" if cursor[-1] != "a" else "b")
    assert (
        client.get("/api/v1/universities", params=params | {"cursor": altered}).status_code == 422
    )
    with db.begin() as c:
        c.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
    response = client.get("/api/v1/universities", params=params | {"cursor": cursor})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "DATASET_CHANGED"
    assert client.get("/api/v1/cutoffs", params={"year": 2026}).json()["release"] is None


@pytest.mark.parametrize(
    "url", ["/api/v1/universities", "/api/v1/programs", "/api/v1/cutoffs", "/api/v1/data-coverage"]
)
def test_validation_and_unknown_filters(catalog_client, url):
    client, _, _ = catalog_client
    for params in [
        {},
        {"year": 2023},
        {"year": 2026, "tuition_max": 100},
        {"year": 2026, "limit": 201},
        {"year": "2026.0"},
        {"year": "2_026"},
    ]:
        assert client.get(url, params=params).status_code == 422


def test_detail_status_and_dto_allowlist(catalog_client):
    client, _, f = catalog_client
    for endpoint, ident in [("universities", f[0]["university"]), ("programs", f[0]["program"])]:
        response = client.get(f"/api/v1/{endpoint}/{ident}", params={"year": 2026})
        assert response.status_code == 200
        assert client.get(f"/api/v1/{endpoint}/{uuid4()}", params={"year": 2026}).status_code == 404
        assert client.get(f"/api/v1/{endpoint}/bad", params={"year": 2026}).status_code == 422
    years = client.get(f"/api/v1/universities/{f[0]['university']}/admission-years").json()
    assert [x["year"] for x in years["items"]] == [2024, 2025, 2026]
    for endpoint in ["universities", "programs", "cutoffs", "data-coverage"]:
        raw = client.get(f"/api/v1/{endpoint}", params={"year": 2026}).text
        for forbidden in [
            "raw_uri",
            "raw_fields",
            "review_reason",
            "reviewed_by",
            "approved_by",
            "payload_hash",
            "DO NOT EXPORT",
            "ingest_jobs",
            "audit_events",
        ]:
            assert forbidden not in raw


def test_disputed_noncurrent_withdrawn_are_excluded(catalog_client):
    client, db, f = catalog_client
    with db.begin() as c:
        c.execute(
            metadata.tables["cutoff_scores"]
            .update()
            .where(metadata.tables["cutoff_scores"].c.id == f[0]["cutoff"])
            .values(verification_status="disputed")
        )
        c.execute(
            metadata.tables["cutoff_scores"]
            .update()
            .where(metadata.tables["cutoff_scores"].c.id == f[1]["cutoff"])
            .values(is_current=False)
        )
        c.execute(
            metadata.tables["program_admissions"]
            .update()
            .where(metadata.tables["program_admissions"].c.id == f[2]["scope"])
            .values(data_status="withdrawn")
        )
    assert len(client.get("/api/v1/cutoffs", params={"year": 2026}).json()["items"]) == 1


def test_publication_during_response_keeps_repeatable_snapshot(catalog_client, monkeypatch):
    from services.api.catalog import queries

    client, db, fixtures = catalog_client
    original = queries.version
    called = False

    def publish_after_version_read(c):
        nonlocal called
        value = original(c)
        if not called:
            called = True
            with db.begin() as writer:
                added = make_scope(writer)
                writer.execute(
                    metadata.tables["universities"]
                    .update()
                    .where(metadata.tables["universities"].c.id == added["university"])
                    .values(verification_status="verified")
                )
                writer.execute(
                    metadata.tables["admission_years"]
                    .update()
                    .where(
                        metadata.tables["admission_years"].c.university_id
                        == fixtures[0]["university"]
                    )
                    .values(status="partial")
                )
                writer.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
        return value

    monkeypatch.setattr(queries, "version", publish_after_version_read)
    response = client.get("/api/v1/cutoffs", params={"year": 2026}).json()
    assert response["dataset_version"] == 3 and len(response["items"]) == 4
    assert response["coverage"]["canonical_cutoff_count"] == 4
    assert response["coverage"]["admission_year_status_counts"]["partial"] == 0
    next_response = client.get("/api/v1/cutoffs", params={"year": 2026}).json()
    assert next_response["dataset_version"] == 4 and len(next_response["items"]) == 5
    assert next_response["coverage"]["admission_year_status_counts"]["partial"] == 1


def test_live_version_does_not_mislabel_old_release_and_reader_is_scoped(release_db, tmp_path):
    from fastapi.testclient import TestClient

    from services.api.catalog.roles import provision_reader
    from services.api.catalog.router import catalog_snapshot
    from services.api.main import app
    from services.data.releases.builder import build

    admin, builder, reader, _ = release_db
    with admin.begin() as c:
        provision_reader(c)
        c.execute(metadata.tables["universities"].update().values(verification_status="verified"))
    result = build(builder, tmp_path)

    def snapshot():
        with reader.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            yield c

    app.dependency_overrides[catalog_snapshot] = snapshot
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/cutoffs", params={"year": 2026}).json()
            assert response["release"] == {"id": result["release_id"], "version": 3}
            assert len(response["items"]) == 1 and response["items"][0]["sources"]
            with admin.begin() as c:
                c.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
            response = client.get("/api/v1/cutoffs", params={"year": 2026}).json()
            assert response["dataset_version"] == 4 and response["release"] is None
        for forbidden in [
            "SELECT raw_fields FROM observations",
            "SELECT * FROM ingest_jobs",
            "SELECT * FROM audit_events",
            "UPDATE cutoff_scores SET score=0",
        ]:
            with reader.begin() as c, pytest.raises(sa.exc.DBAPIError):
                c.exec_driver_sql(forbidden)
    finally:
        app.dependency_overrides.pop(catalog_snapshot, None)


def test_empty_year_method_filter_retains_other_year_coverage(catalog_client):
    client, db, fixtures = catalog_client
    with db.connect() as c:
        code = c.scalar(
            sa.select(metadata.tables["admission_methods"].c.code).where(
                metadata.tables["admission_methods"].c.id == fixtures[0]["method"]
            )
        )
    page = client.get(
        "/api/v1/universities", params={"year": 2025, "query": "HUST", "method": code}
    ).json()
    assert page["items"] == []
    assert page["coverage"]["canonical_cutoff_count"] == 0
    assert page["coverage"]["available_years"] == [2026]
    assert page["coverage"]["missing_years"] == [2024, 2025]


def test_condition_aggregate_and_date_precision_preserved(catalog_client):
    from datetime import date

    client, db, fixtures = catalog_client
    condition = {
        "schema_version": "conditions/1",
        "kind": "predicate",
        "expression": {
            "applies_when": {
                "left": "reviewed_admission_score",
                "right": "cutoff_score",
                "operator": "eq",
            },
            "requirement": {"field": "preference_order", "operator": "lte", "value": 13},
            "otherwise": "not_applicable",
        },
    }
    with db.begin() as c:
        c.execute(
            metadata.tables["program_admissions"]
            .update()
            .where(metadata.tables["program_admissions"].c.id == fixtures[0]["scope"])
            .values(
                condition_text="TEST ONLY TTNV<=13 when equal",
                condition_dsl={"combination_status": "source_aggregate", "conditions": condition},
            )
        )
        c.execute(
            metadata.tables["cutoff_scores"]
            .update()
            .where(metadata.tables["cutoff_scores"].c.id == fixtures[0]["cutoff"])
            .values(effective_from=date(2026, 8, 20))
        )
    items = client.get("/api/v1/cutoffs", params={"year": 2026}).json()["items"]
    row = next(x for x in items if x["id"] == str(fixtures[0]["cutoff"]))
    assert row["scope"]["conditions"] == condition
    assert row["computation_status"] == "unavailable_aggregate_scope"
    assert row["effective_from"] == "2026-08-20"
