from uuid import uuid4

import pytest


def test_docker_reader_setup_is_repeatable_and_cannot_mutate(db):
    from scripts.docker_bootstrap import provision_login

    username = "handover_test_" + uuid4().hex[:12]
    password = "test-only-'quoted-password"
    provision_login(db, username, password)
    provision_login(db, username, password)
    row = db.exec_driver_sql(
        "SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=%s",
        (username,),
    ).one()
    assert not any(row)
    assert db.exec_driver_sql(
        "SELECT has_table_privilege(%s,'cutoff_scores','SELECT')", (username,)
    ).scalar_one()
    assert not db.exec_driver_sql(
        "SELECT has_table_privilege(%s,'cutoff_scores','INSERT,UPDATE,DELETE,TRUNCATE')",
        (username,),
    ).scalar_one()
    assert not db.exec_driver_sql(
        "SELECT has_table_privilege(%s,'ingest_jobs','SELECT')", (username,)
    ).scalar_one()
    owner = db.exec_driver_sql("SELECT session_user").scalar_one()
    with pytest.raises(ValueError, match="separate"):
        provision_login(db, owner, password)
