"""Synthetic PostgreSQL inputs only; never the DEV publication database."""

import secrets
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command

from services.api.db.models import metadata
from services.api.db.session import alembic_config
from tests.fixtures import make_scope


@pytest.fixture
def release_db(database_factory):
    from services.data.releases.roles import provision_roles

    db = database_factory("release")
    with db.begin() as c:
        cfg = alembic_config()
        cfg.attributes["connection"] = c
        command.upgrade(cfg, "head")
        provision_roles(c)
        f = make_scope(c)
        c.execute(metadata.tables["catalog_state"].update().values(dataset_version=3))
        for v in (1, 2, 3):
            f["add"](
                "ingest_jobs",
                job_type="refresh_serving",
                idempotency_key=f"refresh_serving:{v}",
                status="queued",
                payload={"dataset_version": v, "release_builder": "not_implemented_T09"},
            )
        for i in (1, 2):
            obs = f["add"](
                "observations",
                snapshot_id=f["snapshot"],
                fact_kind="cutoff",
                record_locator=f"html:table tr:nth-child({i})",
                parser_version="fixture/1",
                transform_version="fixture/1",
                raw_fields={
                    "_extraction": {
                        "implementation_sha256": "a" * 64,
                        "profile_sha256": "b" * 64,
                        "lock_sha256": "c" * 64,
                    }
                },
                normalized_fields={},
                payload_hash=str(i) * 64,
                extraction_method="manual",
                verification_status="verified",
            )
            c.execute(
                metadata.tables["cutoff_evidence"]
                .insert()
                .values(
                    cutoff_id=f["cutoff"],
                    observation_id=obs,
                    evidence_role="primary" if i == 1 else "supporting",
                )
            )
    engines = {}
    for role in ("eduradar_release_builder", "eduradar_reader"):
        user, password = "test_release_" + uuid4().hex[:16], secrets.token_hex(24)
        with db.begin() as c:
            c.exec_driver_sql(
                f"CREATE ROLE {user} LOGIN PASSWORD '{password}' NOSUPERUSER NOCREATEDB NOCREATEROLE"
            )
            c.exec_driver_sql(f"GRANT {role} TO {user}")
        engines[role] = sa.create_engine(
            db.url.set(username=user, password=password), hide_parameters=True
        )
    yield db, engines["eduradar_release_builder"], engines["eduradar_reader"], f
    for e in [db, *engines.values()]:
        e.dispose()
