"""Year coverage and SQL page regressions; synthetic PostgreSQL only."""

from datetime import date
from uuid import uuid4

import pytest

from services.api.catalog import queries
from services.api.db.models import metadata


@pytest.mark.parametrize("status", ["unknown", "partial", "published", "verified"])
def test_year_status_is_not_inferred_from_verified_facts(catalog_client, status):
    client, db, f = catalog_client
    ident = str(f[0]["university"])
    with db.begin() as c:
        c.execute(
            metadata.tables["admission_years"]
            .update()
            .where(metadata.tables["admission_years"].c.university_id == f[0]["university"])
            .values(status=status)
        )
    page = client.get("/api/v1/universities", params={"year": 2026, "query": "HUST"}).json()
    detail = client.get(f"/api/v1/universities/{ident}", params={"year": 2026}).json()
    years = client.get(f"/api/v1/universities/{ident}/admission-years").json()
    coverage = client.get(
        "/api/v1/data-coverage", params={"year": 2026, "university_id": ident}
    ).json()
    assert page["items"][0]["data_status"] == detail["item"]["data_status"] == status
    assert detail["item"]["cutoff_count"] == 2
    assert next(y for y in years["items"] if y["year"] == 2026)["data_status"] == status
    for value in [
        page["coverage"],
        detail["coverage"],
        coverage["coverage"],
        coverage["items"][-1],
    ]:
        assert value["admission_year_status_counts"][status] == 1
        assert sum(value["admission_year_status_counts"].values()) == 1
    assert all(
        x["verification_status"] == "verified"
        for x in client.get(
            "/api/v1/cutoffs", params={"year": 2026, "university_id": ident}
        ).json()["items"]
    )


@pytest.mark.parametrize("empty_status", ["unknown", "partial", "published", "verified"])
def test_missing_and_empty_admission_years_keep_status_separate(catalog_client, empty_status):
    client, db, f = catalog_client
    ident = f[0]["university"]
    with db.begin() as c:
        c.execute(
            metadata.tables["admission_years"]
            .insert()
            .values(university_id=ident, admission_year=2025, status=empty_status)
        )
    for year, status in [(2024, "not_collected"), (2025, empty_status)]:
        detail = client.get(f"/api/v1/universities/{ident}", params={"year": year}).json()
        assert detail["item"]["data_status"] == status
        assert detail["item"]["cutoff_count"] == 0
        assert detail["coverage"]["admission_year_status_counts"][status] == 1


def test_limit_one_materializes_only_the_returned_cutoff(catalog_client, monkeypatch):
    client, _, _ = catalog_client
    original = queries.cutoff
    calls = []

    def observed(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(queries, "cutoff", observed)
    page = client.get("/api/v1/cutoffs", params={"year": 2026, "limit": 1}).json()
    assert len(page["items"]) == len(calls) == 1
    assert page["has_more"]


def test_alias_year_intervals_and_literal_wildcards(catalog_client):
    client, db, f = catalog_client
    with db.begin() as c:
        c.execute(
            metadata.tables["university_aliases"]
            .insert()
            .values(
                university_id=f[0]["university"],
                alias="100%_ Bách",
                normalized_alias="100%_ bach",
                alias_type="name",
                evidence_url="https://example.invalid/TEST",
                approved_by="TEST",
                valid_from=date(2024, 1, 1),
                valid_to=date(2024, 12, 31),
            )
        )
    for query in ["%", "_", "100%_ bách"]:
        assert (
            len(
                client.get("/api/v1/universities", params={"year": 2024, "query": query}).json()[
                    "items"
                ]
            )
            == 1
        )
        assert (
            client.get("/api/v1/universities", params={"year": 2025, "query": query}).json()[
                "items"
            ]
            == []
        )


@pytest.mark.parametrize("endpoint", ["universities", "programs", "cutoffs"])
@pytest.mark.parametrize("limit", [1, 50, 200])
def test_sql_pages_do_not_skip_or_duplicate_ties(catalog_client, endpoint, limit):
    client, db, _ = catalog_client
    with db.begin() as c:
        c.execute(
            metadata.tables["universities"]
            .update()
            .values(name="TEST TIE", normalized_name="test tie")
        )
    seen = []
    params = {"year": 2026, "limit": limit}
    while True:
        response = client.get(f"/api/v1/{endpoint}", params=params)
        assert response.status_code == 200
        page = response.json()
        seen.extend(
            x["program_year_id"] if endpoint == "programs" else x["id"] for x in page["items"]
        )
        if not page["has_more"]:
            assert page["next_cursor"] is None
            break
        params["cursor"] = page["next_cursor"]
    assert len(seen) == len(set(seen)) == (3 if endpoint == "universities" else 4)


def test_cursor_rejected_before_sources_or_coverage(catalog_client, monkeypatch):
    from services.api.catalog import cursor

    client, db, _ = catalog_client
    params = {"year": 2026, "limit": 1}
    first = client.get("/api/v1/cutoffs", params=params).json()

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid cursor must be rejected before DTO/source/coverage work")

    monkeypatch.setattr(queries, "source_refs", forbidden)
    monkeypatch.setattr(queries, "coverages", forbidden)
    monkeypatch.setattr(queries, "cutoff", forbidden)
    old = cursor.token(
        dict(
            contract="cursor/1",
            binding="old",
            after=[str(uuid4())],
            dataset_version=3,
        )
    )
    response = client.get("/api/v1/cutoffs", params=params | {"cursor": old})
    assert response.status_code == 422 and response.json()["detail"]["code"] == "UNSUPPORTED_CURSOR"
    for changed in [{"limit": 50}, {"campus": "BVS"}, {"year": 2025}]:
        assert (
            client.get(
                "/api/v1/cutoffs", params=params | {"cursor": first["next_cursor"]} | changed
            ).status_code
            == 422
        )
    with db.begin() as c:
        c.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
    assert (
        client.get("/api/v1/cutoffs", params=params | {"cursor": first["next_cursor"]}).status_code
        == 409
    )


def test_offering_label_search_accents_and_wildcards(catalog_client):
    client, db, f = catalog_client
    with db.begin() as c:
        c.execute(
            metadata.tables["program_years"]
            .update()
            .where(metadata.tables["program_years"].c.id == f[0]["offering"])
            .values(offering_name="Kỹ thuật máy tính 100%_")
        )
    for query in ["Kỹ thuật máy", "ky thuat may", "100%_", "%", "_"]:
        items = client.get("/api/v1/programs", params={"year": 2026, "query": query}).json()[
            "items"
        ]
        assert len(items) == 1 and items[0]["program_year_id"] == str(f[0]["offering"])


@pytest.mark.parametrize(
    ("name", "query"), [("A\u200bB", "ab"), ("A&amp;B", "a&b"), ("Straße", "strasse")]
)
def test_offering_display_normalization(catalog_client, name, query):
    client, db, f = catalog_client
    with db.begin() as c:
        c.execute(
            metadata.tables["program_years"]
            .update()
            .where(metadata.tables["program_years"].c.id == f[0]["offering"])
            .values(offering_name=name)
        )
    items = client.get("/api/v1/programs", params={"year": 2026, "query": query}).json()["items"]
    assert len(items) == 1 and items[0]["program_year_id"] == str(f[0]["offering"])


def test_source_url_credentials_are_not_exported(catalog_client):
    client, db, fixtures = catalog_client
    with db.begin() as c:
        c.execute(
            metadata.tables["source_snapshots"]
            .update()
            .where(metadata.tables["source_snapshots"].c.id == fixtures[0]["snapshot"])
            .values(final_url="https://SYNTHETIC:DO-NOT-EXPORT@example.invalid/source")
        )
    page = client.get("/api/v1/cutoffs", params={"year": 2026}).json()
    assert "DO-NOT-EXPORT" not in str(page)
    assert all(
        item["sources"] == []
        for item in page["items"]
        if item["university_id"] == str(fixtures[0]["university"])
    )
