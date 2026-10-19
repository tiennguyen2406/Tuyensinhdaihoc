"""Synthetic catalog DB. No pilot writes, and no source crawling."""

from uuid import uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient

from services.api.db.models import metadata
from services.api.db.session import alembic_config
from tests.fixtures import make_scope


@pytest.fixture
def catalog_db(database_factory):
    db = database_factory("catalog")
    with db.begin() as c:
        cfg = alembic_config()
        cfg.attributes["connection"] = c
        command.upgrade(cfg, "head")
        fixtures = []
        for name, code in [
            ("Đại học Bách khoa Hà Nội", "HUST"),
            ("Đại học Bách khoa Đà Nẵng", "DUT"),
            ("Đại học Bách khoa TP Hồ Chí Minh", "HCMUT"),
        ]:
            f = make_scope(c)
            c.execute(
                metadata.tables["universities"]
                .update()
                .where(metadata.tables["universities"].c.id == f["university"])
                .values(name=name, university_code=code, verification_status="verified")
            )
            c.execute(
                metadata.tables["program_years"]
                .update()
                .where(metadata.tables["program_years"].c.id == f["offering"])
                .values(campus_code="BVH")
            )
            fixtures.append(f)
        first = fixtures[0]
        c.execute(
            metadata.tables["university_aliases"]
            .insert()
            .values(
                university_id=first["university"],
                alias="Bách khoa Thủ đô",
                normalized_alias="bach khoa thu do",
                alias_type="name",
                evidence_url="https://example.invalid/TEST-ONLY",
                approved_by="TEST ONLY",
            )
        )
        off = uuid4()
        c.execute(
            metadata.tables["program_years"]
            .insert()
            .values(
                id=off,
                university_id=first["university"],
                program_id=first["program"],
                admission_year=2026,
                offering_code="TEST-BVS",
                offering_name="TEST ONLY South",
                campus_code="BVS",
                primary_snapshot_id=first["snapshot"],
            )
        )
        scope = uuid4()
        c.execute(
            metadata.tables["program_admissions"]
            .insert()
            .values(id=scope, **(first["scope_values"] | {"program_year_id": off}))
        )
        c.execute(
            metadata.tables["cutoff_scores"]
            .insert()
            .values(**(first["cutoff_values"] | {"program_admission_id": scope}))
        )
        for i in (1, 2):
            obs = uuid4()
            c.execute(
                metadata.tables["observations"]
                .insert()
                .values(
                    id=obs,
                    snapshot_id=first["snapshot"],
                    fact_kind="cutoff",
                    record_locator=f"html:table tr:nth-child({i})",
                    parser_version="TEST ONLY",
                    transform_version="TEST ONLY",
                    raw_fields={"secret": "DO NOT EXPORT"},
                    normalized_fields={},
                    payload_hash=str(i) * 64,
                    extraction_method="manual",
                    verification_status="verified",
                )
            )
            c.execute(
                metadata.tables["cutoff_evidence"]
                .insert()
                .values(
                    cutoff_id=first["cutoff"],
                    observation_id=obs,
                    evidence_role="primary" if i == 1 else "supporting",
                )
            )
        c.execute(metadata.tables["catalog_state"].update().values(dataset_version=3))
    yield db, fixtures
    db.dispose()


@pytest.fixture
def catalog_client(catalog_db):
    from services.api.catalog.router import catalog_snapshot
    from services.api.main import app

    db, fixtures = catalog_db

    def snapshot():
        with db.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            yield c

    app.dependency_overrides[catalog_snapshot] = snapshot
    with TestClient(app) as client:
        yield client, db, fixtures
    app.dependency_overrides.pop(catalog_snapshot, None)
