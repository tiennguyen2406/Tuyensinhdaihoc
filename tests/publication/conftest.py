import secrets
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import create_engine

from services.api.db.session import alembic_config


@pytest.fixture
def publication_database(database_factory):
    from services.data.publication.roles import provision_roles

    engine = database_factory("publication")
    with engine.begin() as c:
        cfg = alembic_config()
        cfg.attributes["connection"] = c
        command.upgrade(cfg, "head")
        provision_roles(c)
    yield engine
    engine.dispose()


@pytest.fixture
def publication_logins(publication_database):
    engines = {}
    for capability in ["reviewer", "reader", "publisher_only", "reviewer_only"]:
        name = "test_pub_" + uuid4().hex[:16]
        password = secrets.token_hex(24)
        with publication_database.begin() as c:
            c.exec_driver_sql(
                f"CREATE ROLE \"{name}\" LOGIN PASSWORD '{password}' NOSUPERUSER NOCREATEROLE NOCREATEDB"
            )
            groups = {
                "reader": ["eduradar_reader"],
                "reviewer": ["eduradar_reviewer", "eduradar_publisher"],
                "publisher_only": ["eduradar_publisher"],
                "reviewer_only": ["eduradar_reviewer"],
            }[capability]
            for group in groups:
                c.exec_driver_sql(f'GRANT "{group}" TO "{name}"')
        engines[capability] = create_engine(
            publication_database.url.set(username=name, password=password)
        )
    yield engines
    for e in engines.values():
        e.dispose()
    # No DROP: keep isolated test DB/logins under the user's preservation constraint.
