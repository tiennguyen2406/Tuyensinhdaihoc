"""Explicit owner provisioning; application runner has only the release capability."""

from sqlalchemy.engine import Connection

from services.data.publication.bootstrap import audit


def provision_roles(c: Connection) -> None:
    c.exec_driver_sql(
        "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='eduradar_reader') THEN CREATE ROLE eduradar_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END $$"
    )
    c.exec_driver_sql(
        "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='eduradar_release_builder') THEN CREATE ROLE eduradar_release_builder NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END $$"
    )
    c.exec_driver_sql("GRANT USAGE ON SCHEMA public TO eduradar_release_builder")
    c.exec_driver_sql(
        "GRANT SELECT ON alembic_version,catalog_state,universities,programs,program_years,majors,admission_methods,score_scales,scoring_rules,program_admissions,cutoff_scores,cutoff_evidence,observations,source_snapshots,sources,ingest_jobs,dataset_releases,combinations,combination_subjects,subjects TO eduradar_release_builder"
    )
    c.exec_driver_sql("GRANT INSERT ON dataset_releases,audit_events TO eduradar_release_builder")
    c.exec_driver_sql("GRANT SELECT ON audit_events TO eduradar_release_builder")
    c.exec_driver_sql("GRANT USAGE ON SEQUENCE audit_events_id_seq TO eduradar_release_builder")
    c.exec_driver_sql(
        "GRANT UPDATE (status,attempts,available_at,lease_until,worker_id,last_error,payload) ON ingest_jobs TO eduradar_release_builder"
    )
    c.exec_driver_sql("GRANT USAGE ON SCHEMA public TO eduradar_reader")
    c.exec_driver_sql("GRANT SELECT ON dataset_releases,alembic_version TO eduradar_reader")
    actor = "db:" + str(c.exec_driver_sql("SELECT session_user").scalar_one())
    audit(
        c,
        actor,
        "provision_release_capability",
        "role",
        None,
        None,
        dict(capability="eduradar_release_builder", policy="release/1"),
        "Explicit DEV T09 provisioning; no owner application runner",
        "T09:provision:release/1",
    )


def require(c: Connection) -> str:
    row = (
        c.exec_driver_sql(
            "SELECT session_user AS actor,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=session_user"
        )
        .mappings()
        .one()
    )
    owner: str = c.exec_driver_sql(
        "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='dataset_releases'::regclass"
    ).scalar_one()
    if (
        any(row[k] for k in ["rolsuper", "rolcreatedb", "rolcreaterole", "rolbypassrls"])
        or row["actor"] == owner
        or not c.exec_driver_sql(
            "SELECT pg_has_role(session_user,'eduradar_release_builder','MEMBER')"
        ).scalar_one()
    ):
        raise PermissionError("Dedicated non-owner non-superuser release capability required")
    return "db:" + row["actor"]
