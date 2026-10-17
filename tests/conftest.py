import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from services.api.main import engine as existing_engine


@pytest.fixture(scope="session")
def database_factory():
    admin = create_engine(
        existing_engine.url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    created = []

    def create_database(label):
        name = f"tuyensinh_test_{label}_{uuid4().hex[:12]}"
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        created.append(name)
        return create_engine(existing_engine.url.set(database=name))

    yield create_database
    admin.dispose()
    print("Retained newly created test databases (no existing DB modified):", ", ".join(created))


@pytest.fixture(scope="session")
def empty_engine(database_factory):
    db = database_factory("empty")
    yield db
    db.dispose()


@pytest.fixture(scope="session")
def migrated_engine(database_factory):
    from alembic import command

    from services.api.db.session import alembic_config

    db = database_factory("schema")
    with db.connect() as connection:
        config = alembic_config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield db
    db.dispose()


@pytest.fixture
def db(migrated_engine):
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()


@pytest.fixture
def test_environment(migrated_engine):
    environment = os.environ.copy()
    environment["POSTGRES_DB"] = migrated_engine.url.database
    return environment
