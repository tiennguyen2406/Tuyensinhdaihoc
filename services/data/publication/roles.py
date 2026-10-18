"""Explicit owner-run grants. No passwords/logins or project .env modifications."""

from sqlalchemy.engine import Connection


def provision_roles(c: Connection) -> None:
    for role in ["eduradar_reader", "eduradar_reviewer", "eduradar_publisher"]:
        c.exec_driver_sql(
            "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='"
            + role
            + "') THEN CREATE ROLE "
            + role
            + " NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END $$"
        )
    c.exec_driver_sql(
        "GRANT USAGE ON SCHEMA public TO eduradar_reader,eduradar_reviewer,eduradar_publisher"
    )
    c.exec_driver_sql(
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO eduradar_reviewer,eduradar_publisher"
    )
    c.exec_driver_sql(
        "GRANT SELECT ON alembic_version,universities,university_aliases,majors,programs,program_aliases,program_years,admission_years,admission_methods,score_scales,scoring_rules,program_admissions,cutoff_scores,cutoff_evidence,tuition,scholarships,exam_events,sources,source_snapshots,catalog_state TO eduradar_reader"
    )
    c.exec_driver_sql(
        "GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO eduradar_reviewer,eduradar_publisher"
    )
    c.exec_driver_sql(
        "GRANT INSERT ON universities,university_aliases,majors,programs,program_aliases,program_years,admission_years,admission_methods,score_scales,subjects,combinations,combination_subjects,observations,ingest_jobs,audit_events,quality_issues TO eduradar_reviewer"
    )
    c.exec_driver_sql(
        "GRANT UPDATE (verification_status,authority_scope,university_id) ON sources TO eduradar_reviewer"
    )
    c.exec_driver_sql("GRANT UPDATE (payload) ON ingest_jobs TO eduradar_reviewer")
    c.exec_driver_sql(
        "GRANT INSERT ON observations,program_admissions,cutoff_scores,cutoff_evidence,ingest_jobs,audit_events,quality_issues TO eduradar_publisher"
    )
    c.exec_driver_sql(
        "GRANT UPDATE (is_current,system_valid_to,verification_status) ON cutoff_scores TO eduradar_publisher"
    )
    c.exec_driver_sql("GRANT UPDATE (data_status) ON program_admissions TO eduradar_publisher")
    c.exec_driver_sql("GRANT UPDATE ON catalog_state TO eduradar_publisher,eduradar_reviewer")
