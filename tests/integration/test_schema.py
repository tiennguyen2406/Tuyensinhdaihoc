from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.api.db.models import CutoffScore, metadata
from services.api.db.session import alembic_config
from tests.fixtures import make_scope


def test_full_metadata_matches_migration(migrated_engine):
    with migrated_engine.connect() as c:
        assert len(metadata.tables) == 34
        assert set(inspect(c).get_table_names()) == set(metadata.tables) | {"alembic_version"}
        assert (
            compare_metadata(
                MigrationContext.configure(c, opts={"compare_server_default": True}), metadata
            )
            == []
        )
        for name in metadata.tables:
            for column in metadata.tables[name].c:
                if column.type.__class__.__name__ == "DateTime":
                    assert column.type.timezone is True


def test_upgrade_preserves_existing_data_and_is_idempotent(database_factory):
    db = database_factory("existing")
    try:
        with db.begin() as c:
            c.execute(
                text("CREATE TABLE existing_data (id integer PRIMARY KEY, note text NOT NULL)")
            )
            c.execute(text("INSERT INTO existing_data VALUES (1, 'keep me')"))
        with db.connect() as c:
            config = alembic_config()
            config.attributes["connection"] = c
            command.upgrade(config, "head")
            command.upgrade(config, "head")
            assert (
                c.execute(text("SELECT note FROM existing_data WHERE id=1")).scalar_one()
                == "keep me"
            )
            assert (
                c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0004_releases"
            )
    finally:
        db.dispose()


def test_null_combination_scope_cannot_be_duplicated(db):
    f = make_scope(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        f["add"]("program_admissions", **f["scope_values"])


def test_program_cannot_be_attached_to_wrong_university(db):
    f = make_scope(db)
    other = f["add"](
        "universities",
        university_code=str(uuid4()),
        name="OTHER TEST",
        normalized_name="other test",
        slug=str(uuid4()),
    )
    db.execute(
        metadata.tables["admission_years"]
        .insert()
        .values(university_id=other, admission_year=2026, status="unknown")
    )
    with pytest.raises(IntegrityError), db.begin_nested():
        f["add"](
            "program_years",
            university_id=other,
            program_id=f["program"],
            admission_year=2026,
            offering_code="WRONG",
            offering_name="TEST",
            primary_snapshot_id=f["snapshot"],
        )


def test_scale_cannot_belong_to_another_method(db):
    f = make_scope(db)
    method = f["add"]("admission_methods", code=str(uuid4()), name="OTHER", input_kind="exam_total")
    values = f["scope_values"] | {"method_id": method, "round_key": "OTHER"}
    with pytest.raises(IntegrityError), db.begin_nested():
        f["add"]("program_admissions", **values)


def test_only_one_current_cutoff_per_scope(db):
    f = make_scope(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        f["add"]("cutoff_scores", **(f["cutoff_values"] | {"revision": 2}))


def test_score_and_money_round_trip_as_decimal(db):
    f = make_scope(db)
    table = metadata.tables["cutoff_scores"]
    assert db.execute(
        select(table.c.score).where(table.c.id == f["cutoff"])
    ).scalar_one() == Decimal("24.12345")
    # ORM mapper must retain the same Decimal semantics.
    with Session(bind=db) as session:
        assert session.get(CutoffScore, f["cutoff"]).__dict__["score"] == Decimal("24.12345")
    tuition = metadata.tables["tuition"]
    row = f["add"](
        "tuition",
        university_id=f["university"],
        admission_year=2026,
        policy_key="TEST",
        revision=1,
        amount_min=Decimal("12345678.90"),
        currency="VND",
        unit="academic_year",
        description="TEST ONLY",
        scope_dsl={},
        primary_snapshot_id=f["snapshot"],
        verification_status="unverified",
    )
    value = db.execute(select(tuition.c.amount_min).where(tuition.c.id == row)).scalar_one()
    assert isinstance(value, Decimal)
    assert value == Decimal("12345678.90")
