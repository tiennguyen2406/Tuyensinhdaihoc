"""Explicit owner provisioning for a catalog reader; no source bodies/private job access."""

from sqlalchemy.engine import Connection

from services.data.publication.bootstrap import audit


def provision_reader(c: Connection) -> None:
    c.exec_driver_sql(
        "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='eduradar_reader') THEN CREATE ROLE eduradar_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END $$"
    )
    c.exec_driver_sql("GRANT USAGE ON SCHEMA public TO eduradar_reader")
    c.exec_driver_sql(
        "GRANT SELECT ON alembic_version,catalog_state,universities,university_aliases,programs,program_years,admission_methods,score_scales,program_admissions,cutoff_scores,cutoff_evidence,source_snapshots,sources,majors,dataset_releases TO eduradar_reader"
    )
    c.exec_driver_sql(
        "GRANT SELECT (id,snapshot_id,record_locator) ON observations TO eduradar_reader"
    )
    actor = "db:" + str(c.exec_driver_sql("SELECT session_user").scalar_one())
    audit(
        c,
        actor,
        "provision_catalog_reader",
        "role",
        None,
        None,
        {
            "capability": "eduradar_reader",
            "observation_columns": ["id", "snapshot_id", "record_locator"],
        },
        "T10 read-only lookup, no raw observation bodies/jobs/audit privileges",
        "T10:catalog/1:reader",
    )
