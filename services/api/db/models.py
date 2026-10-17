"""Static mappings generated from the supplied baseline DDL, not runtime reflection."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


metadata = Base.metadata

admission_methods = sa.Table(
    "admission_methods",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("code", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("input_kind", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.CheckConstraint(
        "input_kind = ANY (ARRAY['subjects'::text, 'transcript'::text, 'exam_total'::text, 'composite'::text])",
        name="admission_methods_input_kind_check",
    ),
    sa.PrimaryKeyConstraint("id", name="admission_methods_pkey"),
    sa.UniqueConstraint("code", name="admission_methods_code_key"),
)

admission_years = sa.Table(
    "admission_years",
    metadata,
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint(
        "admission_year >= 2000 AND admission_year <= 2100",
        name="admission_years_admission_year_check",
    ),
    sa.CheckConstraint(
        "status = ANY (ARRAY['unknown'::text, 'partial'::text, 'published'::text, 'verified'::text])",
        name="admission_years_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="admission_years_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["university_id"], ["universities.id"], name="admission_years_university_id_fkey"
    ),
    sa.PrimaryKeyConstraint("university_id", "admission_year", name="admission_years_pkey"),
)

audit_events = sa.Table(
    "audit_events",
    metadata,
    sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column("actor_id", sa.Text(), nullable=False),
    sa.Column("action", sa.Text(), nullable=False),
    sa.Column("entity_kind", sa.Text(), nullable=False),
    sa.Column("entity_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("before_data", postgresql.JSONB(), nullable=True),
    sa.Column("after_data", postgresql.JSONB(), nullable=True),
    sa.Column("reason", sa.Text(), nullable=False),
    sa.Column("request_id", sa.Text(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="audit_events_pkey"),
)

catalog_state = sa.Table(
    "catalog_state",
    metadata,
    sa.Column("singleton", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    sa.Column("dataset_version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
    sa.Column(
        "changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint("dataset_version >= 0", name="catalog_state_dataset_version_check"),
    sa.CheckConstraint("singleton", name="catalog_state_singleton_check"),
    sa.PrimaryKeyConstraint("singleton", name="catalog_state_pkey"),
)

combination_subjects = sa.Table(
    "combination_subjects",
    metadata,
    sa.Column("combination_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("subject_code", sa.Text(), nullable=False),
    sa.Column("position", sa.SmallInteger(), nullable=False),
    sa.CheckConstraint(
        '"position" >= 1 AND "position" <= 3', name="combination_subjects_position_check"
    ),
    sa.ForeignKeyConstraint(
        ["combination_id"], ["combinations.id"], name="combination_subjects_combination_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["subject_code"], ["subjects.code"], name="combination_subjects_subject_code_fkey"
    ),
    sa.PrimaryKeyConstraint("combination_id", "subject_code", name="combination_subjects_pkey"),
    sa.UniqueConstraint(
        "combination_id", "position", name="combination_subjects_combination_id_position_key"
    ),
)

combinations = sa.Table(
    "combinations",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("code", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("id", name="combinations_pkey"),
    sa.UniqueConstraint("code", name="combinations_code_key"),
)

conversion_rules = sa.Table(
    "conversion_rules",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("program_year_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("from_method_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("to_method_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("from_scale_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("to_scale_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("rule_key", sa.Text(), nullable=False),
    sa.Column("version", sa.Integer(), nullable=False),
    sa.Column("input_requirements", postgresql.JSONB(), nullable=False),
    sa.Column("formula_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("applicability_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("rounding_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.CheckConstraint("from_scale_id <> to_scale_id", name="conversion_rules_check"),
    sa.CheckConstraint(
        "NOT is_current OR verification_status = 'verified'::text", name="conversion_rules_check1"
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="conversion_rules_verification_status_check",
    ),
    sa.CheckConstraint("version > 0", name="conversion_rules_version_check"),
    sa.ForeignKeyConstraint(
        ["from_method_id"], ["admission_methods.id"], name="conversion_rules_from_method_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["from_scale_id", "from_method_id"],
        ["score_scales.id", "score_scales.method_id"],
        name="conversion_rules_from_scale_id_from_method_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="conversion_rules_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["program_year_id"], ["program_years.id"], name="conversion_rules_program_year_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["to_method_id"], ["admission_methods.id"], name="conversion_rules_to_method_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["to_scale_id", "to_method_id"],
        ["score_scales.id", "score_scales.method_id"],
        name="conversion_rules_to_scale_id_to_method_id_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="conversion_rules_pkey"),
    sa.UniqueConstraint(
        "program_year_id",
        "rule_key",
        "version",
        name="conversion_rules_program_year_id_rule_key_version_key",
    ),
)

crawl_fetches = sa.Table(
    "crawl_fetches",
    metadata,
    sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column("source_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("snapshot_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column(
        "checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column("http_status", sa.SmallInteger(), nullable=True),
    sa.Column("outcome", sa.Text(), nullable=False),
    sa.Column("elapsed_ms", sa.Integer(), nullable=True),
    sa.Column("error_code", sa.Text(), nullable=True),
    sa.Column(
        "response_validators",
        postgresql.JSONB(),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    ),
    sa.CheckConstraint("elapsed_ms >= 0", name="crawl_fetches_elapsed_ms_check"),
    sa.CheckConstraint(
        "http_status >= 100 AND http_status <= 599", name="crawl_fetches_http_status_check"
    ),
    sa.ForeignKeyConstraint(
        ["snapshot_id"], ["source_snapshots.id"], name="crawl_fetches_snapshot_id_fkey"
    ),
    sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="crawl_fetches_source_id_fkey"),
    sa.PrimaryKeyConstraint("id", name="crawl_fetches_pkey"),
)

cutoff_evidence = sa.Table(
    "cutoff_evidence",
    metadata,
    sa.Column("cutoff_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("observation_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("evidence_role", sa.Text(), nullable=False),
    sa.Column(
        "attached_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint(
        "evidence_role = ANY (ARRAY['primary'::text, 'supporting'::text, 'conflicting'::text, 'superseding'::text])",
        name="cutoff_evidence_evidence_role_check",
    ),
    sa.ForeignKeyConstraint(
        ["cutoff_id"], ["cutoff_scores.id"], name="cutoff_evidence_cutoff_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["observation_id"], ["observations.id"], name="cutoff_evidence_observation_id_fkey"
    ),
    sa.PrimaryKeyConstraint("cutoff_id", "observation_id", name="cutoff_evidence_pkey"),
)

cutoff_scores = sa.Table(
    "cutoff_scores",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("program_admission_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("revision", sa.Integer(), nullable=False),
    sa.Column("score_scale_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("score", sa.Numeric(12, 5, asdecimal=True), nullable=False),
    sa.Column("max_score", sa.Numeric(12, 5, asdecimal=True), nullable=False),
    sa.Column("fact_fingerprint", sa.Text(), nullable=False),
    sa.Column("publication_group_key", sa.Text(), nullable=False),
    sa.Column("fact_payload", postgresql.JSONB(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("source_published_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("effective_from", sa.Date(), nullable=True),
    sa.Column(
        "system_valid_from",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
    sa.Column("system_valid_to", sa.DateTime(timezone=True), nullable=True),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.Column("reviewed_by", sa.Text(), nullable=True),
    sa.Column("review_reason", sa.Text(), nullable=True),
    sa.CheckConstraint("score >= 0::numeric AND score <= max_score", name="cutoff_scores_check"),
    sa.CheckConstraint(
        "system_valid_to IS NULL OR system_valid_to >= system_valid_from",
        name="cutoff_scores_check1",
    ),
    sa.CheckConstraint(
        "NOT is_current OR system_valid_to IS NULL AND (verification_status = ANY (ARRAY['verified'::text, 'disputed'::text]))",
        name="cutoff_scores_check2",
    ),
    sa.CheckConstraint(
        "fact_fingerprint ~ '^[0-9a-f]{64}$'::text", name="cutoff_scores_fact_fingerprint_check"
    ),
    sa.CheckConstraint("revision > 0", name="cutoff_scores_revision_check"),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="cutoff_scores_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="cutoff_scores_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["program_admission_id", "score_scale_id"],
        ["program_admissions.id", "program_admissions.score_scale_id"],
        name="cutoff_scores_program_admission_id_score_scale_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["score_scale_id", "max_score"],
        ["score_scales.id", "score_scales.max_score"],
        name="cutoff_scores_score_scale_id_max_score_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="cutoff_scores_pkey"),
    sa.UniqueConstraint(
        "program_admission_id", "revision", name="cutoff_scores_program_admission_id_revision_key"
    ),
)

dataset_releases = sa.Table(
    "dataset_releases",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("version", sa.BigInteger(), nullable=False),
    sa.Column("manifest_uri", sa.Text(), nullable=False),
    sa.Column("manifest_sha256", sa.Text(), nullable=False),
    sa.Column("cutoff_count", sa.BigInteger(), nullable=False),
    sa.Column("metadata", postgresql.JSONB(), nullable=False),
    sa.Column(
        "published_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint("cutoff_count >= 0", name="dataset_releases_cutoff_count_check"),
    sa.CheckConstraint(
        "manifest_sha256 ~ '^[0-9a-f]{64}$'::text", name="dataset_releases_manifest_sha256_check"
    ),
    sa.CheckConstraint("version >= 0", name="dataset_releases_version_check"),
    sa.PrimaryKeyConstraint("id", name="dataset_releases_pkey"),
    sa.UniqueConstraint("version", name="dataset_releases_version_key"),
)

exam_events = sa.Table(
    "exam_events",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("method_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("exam_year", sa.SmallInteger(), nullable=False),
    sa.Column("organizer_key", sa.Text(), nullable=False),
    sa.Column("event_key", sa.Text(), nullable=False),
    sa.Column("revision", sa.Integer(), nullable=False),
    sa.Column("event_type", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("event_date", sa.Date(), nullable=True),
    sa.Column("time_precision", sa.Text(), nullable=False),
    sa.Column(
        "timezone_name",
        sa.Text(),
        server_default=sa.text("'Asia/Ho_Chi_Minh'::text"),
        nullable=False,
    ),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.CheckConstraint(
        "ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at", name="exam_events_check"
    ),
    sa.CheckConstraint(
        "exam_year >= 2000 AND exam_year <= 2100", name="exam_events_exam_year_check"
    ),
    sa.CheckConstraint("revision > 0", name="exam_events_revision_check"),
    sa.CheckConstraint(
        "time_precision = ANY (ARRAY['date'::text, 'timestamp'::text, 'unknown'::text])",
        name="exam_events_time_precision_check",
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="exam_events_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["method_id"], ["admission_methods.id"], name="exam_events_method_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="exam_events_primary_snapshot_id_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="exam_events_pkey"),
    sa.UniqueConstraint(
        "organizer_key",
        "exam_year",
        "event_key",
        "revision",
        name="exam_events_organizer_key_exam_year_event_key_revision_key",
    ),
)

ingest_jobs = sa.Table(
    "ingest_jobs",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("job_type", sa.Text(), nullable=False),
    sa.Column("idempotency_key", sa.Text(), nullable=False),
    sa.Column("payload", postgresql.JSONB(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("priority", sa.Integer(), server_default=sa.text("0"), nullable=False),
    sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
    sa.Column(
        "available_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
    sa.Column("worker_id", sa.Text(), nullable=True),
    sa.Column("last_error", postgresql.JSONB(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint("attempts >= 0", name="ingest_jobs_attempts_check"),
    sa.CheckConstraint(
        "status = ANY (ARRAY['queued'::text, 'leased'::text, 'succeeded'::text, 'retry_wait'::text, 'failed'::text, 'quarantined'::text])",
        name="ingest_jobs_status_check",
    ),
    sa.PrimaryKeyConstraint("id", name="ingest_jobs_pkey"),
    sa.UniqueConstraint("idempotency_key", name="ingest_jobs_idempotency_key_key"),
)

majors = sa.Table(
    "majors",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("code_system", sa.Text(), nullable=False),
    sa.Column("major_code", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("id", name="majors_pkey"),
    sa.UniqueConstraint("code_system", "major_code", name="majors_code_system_major_code_key"),
)

observations = sa.Table(
    "observations",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("fact_kind", sa.Text(), nullable=False),
    sa.Column("record_locator", sa.Text(), nullable=False),
    sa.Column("parser_version", sa.Text(), nullable=False),
    sa.Column("transform_version", sa.Text(), nullable=False),
    sa.Column("raw_fields", postgresql.JSONB(), nullable=False),
    sa.Column("normalized_fields", postgresql.JSONB(), nullable=False),
    sa.Column("payload_hash", sa.Text(), nullable=False),
    sa.Column("extraction_method", sa.Text(), nullable=False),
    sa.Column("extraction_confidence", sa.Numeric(5, 4, asdecimal=True), nullable=True),
    sa.Column(
        "verification_status",
        sa.Text(),
        server_default=sa.text("'unverified'::text"),
        nullable=False,
    ),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint(
        "extraction_confidence >= 0::numeric AND extraction_confidence <= 1::numeric",
        name="observations_extraction_confidence_check",
    ),
    sa.CheckConstraint(
        "fact_kind = ANY (ARRAY['cutoff'::text, 'tuition'::text, 'scholarship'::text, 'exam_event'::text, 'scoring_rule'::text, 'conversion_rule'::text, 'catalog'::text])",
        name="observations_fact_kind_check",
    ),
    sa.CheckConstraint(
        "payload_hash ~ '^[0-9a-f]{64}$'::text", name="observations_payload_hash_check"
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'reviewed'::text, 'verified'::text, 'rejected'::text, 'disputed'::text])",
        name="observations_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["snapshot_id"], ["source_snapshots.id"], name="observations_snapshot_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="observations_pkey"),
    sa.UniqueConstraint(
        "snapshot_id",
        "record_locator",
        "parser_version",
        "transform_version",
        name="observations_snapshot_id_record_locator_parser_version_tran_key",
    ),
)

program_admissions = sa.Table(
    "program_admissions",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("program_year_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("method_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("combination_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("round_key", sa.Text(), nullable=False),
    sa.Column("population_key", sa.Text(), nullable=False),
    sa.Column("condition_key", sa.Text(), nullable=False),
    sa.Column("condition_text", sa.Text(), nullable=False),
    sa.Column("condition_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("score_scale_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("scoring_rule_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("data_status", sa.Text(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.CheckConstraint(
        "data_status = ANY (ARRAY['announced'::text, 'published'::text, 'withdrawn'::text, 'unknown'::text])",
        name="program_admissions_data_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["combination_id"], ["combinations.id"], name="program_admissions_combination_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["method_id"], ["admission_methods.id"], name="program_admissions_method_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="program_admissions_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["program_year_id"], ["program_years.id"], name="program_admissions_program_year_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["score_scale_id", "method_id"],
        ["score_scales.id", "score_scales.method_id"],
        name="program_admissions_score_scale_id_method_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["scoring_rule_id", "program_year_id", "method_id", "score_scale_id"],
        [
            "scoring_rules.id",
            "scoring_rules.program_year_id",
            "scoring_rules.method_id",
            "scoring_rules.output_scale_id",
        ],
        name="program_admissions_scoring_rule_id_program_year_id_method__fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="program_admissions_pkey"),
    sa.UniqueConstraint("id", "score_scale_id", name="program_admissions_id_score_scale_id_key"),
    sa.UniqueConstraint(
        "program_year_id",
        "method_id",
        "combination_id",
        "round_key",
        "population_key",
        "condition_key",
        name="program_admissions_program_year_id_method_id_combination_id_key",
        postgresql_nulls_not_distinct=True,
    ),
)

program_aliases = sa.Table(
    "program_aliases",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("program_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("normalized_alias", sa.Text(), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=True),
    sa.Column("evidence_url", sa.Text(), nullable=False),
    sa.Column("approved_by", sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(
        ["program_id", "university_id"],
        ["programs.id", "programs.university_id"],
        name="program_aliases_program_id_university_id_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="program_aliases_pkey"),
    sa.UniqueConstraint(
        "program_id",
        "normalized_alias",
        "admission_year",
        name="program_aliases_program_id_normalized_alias_admission_year_key",
        postgresql_nulls_not_distinct=True,
    ),
)

program_years = sa.Table(
    "program_years",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("program_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=False),
    sa.Column("offering_code", sa.Text(), nullable=False),
    sa.Column("offering_name", sa.Text(), nullable=False),
    sa.Column(
        "campus_code", sa.Text(), server_default=sa.text("'UNSPECIFIED'::text"), nullable=False
    ),
    sa.Column(
        "track_code", sa.Text(), server_default=sa.text("'UNSPECIFIED'::text"), nullable=False
    ),
    sa.Column(
        "language_code", sa.Text(), server_default=sa.text("'UNSPECIFIED'::text"), nullable=False
    ),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="program_years_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["program_id", "university_id"],
        ["programs.id", "programs.university_id"],
        name="program_years_program_id_university_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["university_id", "admission_year"],
        ["admission_years.university_id", "admission_years.admission_year"],
        name="program_years_university_id_admission_year_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="program_years_pkey"),
    sa.UniqueConstraint(
        "id",
        "university_id",
        "admission_year",
        name="program_years_id_university_id_admission_year_key",
    ),
    sa.UniqueConstraint(
        "university_id",
        "admission_year",
        "offering_code",
        "campus_code",
        "track_code",
        "language_code",
        name="program_years_university_id_admission_year_offering_code_ca_key",
    ),
)

programs = sa.Table(
    "programs",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("canonical_key", sa.Text(), nullable=False),
    sa.Column("program_name", sa.Text(), nullable=False),
    sa.Column("normalized_name", sa.Text(), nullable=False),
    sa.Column("major_id", sa.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(["major_id"], ["majors.id"], name="programs_major_id_fkey"),
    sa.ForeignKeyConstraint(
        ["university_id"], ["universities.id"], name="programs_university_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="programs_pkey"),
    sa.UniqueConstraint("id", "university_id", name="programs_id_university_id_key"),
    sa.UniqueConstraint(
        "university_id", "canonical_key", name="programs_university_id_canonical_key_key"
    ),
)

quality_issues = sa.Table(
    "quality_issues",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("observation_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("entity_kind", sa.Text(), nullable=False),
    sa.Column("entity_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("issue_code", sa.Text(), nullable=False),
    sa.Column("severity", sa.Text(), nullable=False),
    sa.Column("details", postgresql.JSONB(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("resolved_by", sa.Text(), nullable=True),
    sa.Column("resolution_reason", sa.Text(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint(
        "severity = ANY (ARRAY['info'::text, 'warning'::text, 'error'::text, 'critical'::text])",
        name="quality_issues_severity_check",
    ),
    sa.CheckConstraint(
        "status = ANY (ARRAY['open'::text, 'resolved'::text, 'dismissed'::text])",
        name="quality_issues_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["observation_id"], ["observations.id"], name="quality_issues_observation_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="quality_issues_pkey"),
)

scholarships = sa.Table(
    "scholarships",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=False),
    sa.Column("program_year_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("policy_key", sa.Text(), nullable=False),
    sa.Column("revision", sa.Integer(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("eligibility_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("eligibility_text", sa.Text(), nullable=False),
    sa.Column("benefit", postgresql.JSONB(), nullable=False),
    sa.Column("deadline_date", sa.Date(), nullable=True),
    sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("deadline_precision", sa.Text(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.CheckConstraint(
        "NOT is_current OR (verification_status = ANY (ARRAY['verified'::text, 'disputed'::text]))",
        name="scholarships_check",
    ),
    sa.CheckConstraint(
        "deadline_precision = ANY (ARRAY['date'::text, 'timestamp'::text, 'unknown'::text])",
        name="scholarships_deadline_precision_check",
    ),
    sa.CheckConstraint("revision > 0", name="scholarships_revision_check"),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="scholarships_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="scholarships_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["program_year_id", "university_id", "admission_year"],
        ["program_years.id", "program_years.university_id", "program_years.admission_year"],
        name="scholarships_program_year_id_university_id_admission_year_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["university_id", "admission_year"],
        ["admission_years.university_id", "admission_years.admission_year"],
        name="scholarships_university_id_admission_year_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="scholarships_pkey"),
    sa.UniqueConstraint(
        "university_id",
        "admission_year",
        "program_year_id",
        "policy_key",
        "revision",
        name="scholarships_university_id_admission_year_program_year_id_p_key",
        postgresql_nulls_not_distinct=True,
    ),
)

score_scales = sa.Table(
    "score_scales",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("method_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=False),
    sa.Column("code", sa.Text(), nullable=False),
    sa.Column("exam_version", sa.Text(), nullable=False),
    sa.Column(
        "min_score", sa.Numeric(12, 5, asdecimal=True), server_default=sa.text("0"), nullable=False
    ),
    sa.Column("max_score", sa.Numeric(12, 5, asdecimal=True), nullable=False),
    sa.Column("basis_description", sa.Text(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.CheckConstraint(
        "admission_year >= 2000 AND admission_year <= 2100",
        name="score_scales_admission_year_check",
    ),
    sa.CheckConstraint(
        "min_score >= 0::numeric AND max_score > min_score", name="score_scales_check"
    ),
    sa.ForeignKeyConstraint(
        ["method_id"], ["admission_methods.id"], name="score_scales_method_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="score_scales_primary_snapshot_id_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="score_scales_pkey"),
    sa.UniqueConstraint("id", "max_score", name="score_scales_id_max_score_key"),
    sa.UniqueConstraint("id", "method_id", name="score_scales_id_method_id_key"),
    sa.UniqueConstraint(
        "method_id",
        "admission_year",
        "code",
        "exam_version",
        name="score_scales_method_id_admission_year_code_exam_version_key",
    ),
)

scoring_rules = sa.Table(
    "scoring_rules",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("program_year_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("method_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("output_scale_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("rule_key", sa.Text(), nullable=False),
    sa.Column("version", sa.Integer(), nullable=False),
    sa.Column("input_schema", postgresql.JSONB(), nullable=False),
    sa.Column("formula_dsl", postgresql.JSONB(), nullable=False),
    sa.Column(
        "eligibility_dsl", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
    ),
    sa.Column(
        "priority_dsl", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
    ),
    sa.Column("rounding_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("required_components", postgresql.JSONB(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.CheckConstraint(
        "NOT is_current OR verification_status = 'verified'::text", name="scoring_rules_check"
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="scoring_rules_verification_status_check",
    ),
    sa.CheckConstraint("version > 0", name="scoring_rules_version_check"),
    sa.ForeignKeyConstraint(
        ["method_id"], ["admission_methods.id"], name="scoring_rules_method_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["output_scale_id", "method_id"],
        ["score_scales.id", "score_scales.method_id"],
        name="scoring_rules_output_scale_id_method_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="scoring_rules_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["program_year_id"], ["program_years.id"], name="scoring_rules_program_year_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="scoring_rules_pkey"),
    sa.UniqueConstraint(
        "id",
        "program_year_id",
        "method_id",
        "output_scale_id",
        name="scoring_rules_id_program_year_id_method_id_output_scale_id_key",
    ),
    sa.UniqueConstraint(
        "program_year_id",
        "method_id",
        "rule_key",
        "version",
        name="scoring_rules_program_year_id_method_id_rule_key_version_key",
    ),
)

sna_runs = sa.Table(
    "sna_runs",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("dataset_release_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("graph_type", sa.Text(), nullable=False),
    sa.Column("reference_year", sa.SmallInteger(), nullable=False),
    sa.Column("parameters", postgresql.JSONB(), nullable=False),
    sa.Column("library_versions", postgresql.JSONB(), nullable=False),
    sa.Column("random_seed", sa.Integer(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("graph_uri", sa.Text(), nullable=True),
    sa.Column("metrics", postgresql.JSONB(), nullable=True),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint(
        "status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text])",
        name="sna_runs_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["dataset_release_id"], ["dataset_releases.id"], name="sna_runs_dataset_release_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="sna_runs_pkey"),
)

source_snapshots = sa.Table(
    "source_snapshots",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("source_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("raw_hash", sa.Text(), nullable=False),
    sa.Column("raw_uri", sa.Text(), nullable=False),
    sa.Column("final_url", sa.Text(), nullable=False),
    sa.Column("media_type", sa.Text(), nullable=False),
    sa.Column("byte_size", sa.BigInteger(), nullable=False),
    sa.Column("source_title", sa.Text(), nullable=True),
    sa.Column("source_published_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "publication_precision",
        sa.Text(),
        server_default=sa.text("'unknown'::text"),
        nullable=False,
    ),
    sa.Column(
        "first_crawled_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
    sa.CheckConstraint("byte_size >= 0", name="source_snapshots_byte_size_check"),
    sa.CheckConstraint(
        "publication_precision = ANY (ARRAY['timestamp'::text, 'date'::text, 'unknown'::text])",
        name="source_snapshots_publication_precision_check",
    ),
    sa.CheckConstraint("raw_hash ~ '^[0-9a-f]{64}$'::text", name="source_snapshots_raw_hash_check"),
    sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="source_snapshots_source_id_fkey"),
    sa.PrimaryKeyConstraint("id", name="source_snapshots_pkey"),
    sa.UniqueConstraint("source_id", "raw_hash", name="source_snapshots_source_id_raw_hash_key"),
)

sources = sa.Table(
    "sources",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("canonical_url", sa.Text(), nullable=False),
    sa.Column("domain", sa.Text(), nullable=False),
    sa.Column("publisher", sa.Text(), nullable=False),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("source_type", sa.Text(), nullable=False),
    sa.Column(
        "authority_scope", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
    ),
    sa.Column("title", sa.Text(), nullable=True),
    sa.Column("etag", sa.Text(), nullable=True),
    sa.Column("last_modified", sa.Text(), nullable=True),
    sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "verification_status",
        sa.Text(),
        server_default=sa.text("'unverified'::text"),
        nullable=False,
    ),
    sa.CheckConstraint(
        "source_type = ANY (ARRAY['university'::text, 'admission_office'::text, 'official_portal'::text, 'exam_organizer'::text, 'press'::text, 'aggregator'::text])",
        name="sources_source_type_check",
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="sources_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["university_id"], ["universities.id"], name="sources_university_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="sources_pkey"),
    sa.UniqueConstraint("canonical_url", name="sources_canonical_url_key"),
)

subjects = sa.Table(
    "subjects",
    metadata,
    sa.Column("code", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("code", name="subjects_pkey"),
)

tuition = sa.Table(
    "tuition",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=False),
    sa.Column("program_year_id", sa.UUID(as_uuid=True), nullable=True),
    sa.Column("policy_key", sa.Text(), nullable=False),
    sa.Column("revision", sa.Integer(), nullable=False),
    sa.Column("amount_min", sa.Numeric(18, 2, asdecimal=True), nullable=True),
    sa.Column("amount_max", sa.Numeric(18, 2, asdecimal=True), nullable=True),
    sa.Column("currency", sa.CHAR(3), nullable=False),
    sa.Column("unit", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=False),
    sa.Column("scope_dsl", postgresql.JSONB(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.CheckConstraint(
        "amount_max IS NULL OR amount_max >= 0::numeric", name="tuition_amount_max_check"
    ),
    sa.CheckConstraint(
        "amount_min IS NULL OR amount_min >= 0::numeric", name="tuition_amount_min_check"
    ),
    sa.CheckConstraint(
        "amount_min IS NULL OR amount_max IS NULL OR amount_max >= amount_min", name="tuition_check"
    ),
    sa.CheckConstraint(
        "NOT is_current OR (verification_status = ANY (ARRAY['verified'::text, 'disputed'::text]))",
        name="tuition_check1",
    ),
    sa.CheckConstraint("revision > 0", name="tuition_revision_check"),
    sa.CheckConstraint(
        "unit = ANY (ARRAY['credit'::text, 'semester'::text, 'academic_year'::text, 'full_program'::text, 'other'::text, 'unknown'::text])",
        name="tuition_unit_check",
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="tuition_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"], ["source_snapshots.id"], name="tuition_primary_snapshot_id_fkey"
    ),
    sa.ForeignKeyConstraint(
        ["program_year_id", "university_id", "admission_year"],
        ["program_years.id", "program_years.university_id", "program_years.admission_year"],
        name="tuition_program_year_id_university_id_admission_year_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["university_id", "admission_year"],
        ["admission_years.university_id", "admission_years.admission_year"],
        name="tuition_university_id_admission_year_fkey",
    ),
    sa.PrimaryKeyConstraint("id", name="tuition_pkey"),
    sa.UniqueConstraint(
        "university_id",
        "admission_year",
        "program_year_id",
        "policy_key",
        "revision",
        name="tuition_university_id_admission_year_program_year_id_policy_key",
        postgresql_nulls_not_distinct=True,
    ),
)

universities = sa.Table(
    "universities",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_code", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("short_name", sa.Text(), nullable=True),
    sa.Column("normalized_name", sa.Text(), nullable=False),
    sa.Column("slug", sa.Text(), nullable=False),
    sa.Column("province_code", sa.Text(), nullable=True),
    sa.Column("university_type", sa.Text(), nullable=True),
    sa.Column("website", sa.Text(), nullable=True),
    sa.Column(
        "verification_status",
        sa.Text(),
        server_default=sa.text("'unverified'::text"),
        nullable=False,
    ),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text])",
        name="universities_verification_status_check",
    ),
    sa.PrimaryKeyConstraint("id", name="universities_pkey"),
    sa.UniqueConstraint("slug", name="universities_slug_key"),
    sa.UniqueConstraint("university_code", name="universities_university_code_key"),
)

university_aliases = sa.Table(
    "university_aliases",
    metadata,
    sa.Column(
        "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
    ),
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("alias", sa.Text(), nullable=False),
    sa.Column("normalized_alias", sa.Text(), nullable=False),
    sa.Column("alias_type", sa.Text(), nullable=False),
    sa.Column("valid_from", sa.Date(), nullable=True),
    sa.Column("valid_to", sa.Date(), nullable=True),
    sa.Column("evidence_url", sa.Text(), nullable=False),
    sa.Column("approved_by", sa.Text(), nullable=False),
    sa.CheckConstraint(
        "alias_type = ANY (ARRAY['name'::text, 'short_name'::text, 'legacy_code'::text, 'domain'::text])",
        name="university_aliases_alias_type_check",
    ),
    sa.CheckConstraint(
        "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
        name="university_aliases_check",
    ),
    sa.ForeignKeyConstraint(
        ["university_id"], ["universities.id"], name="university_aliases_university_id_fkey"
    ),
    sa.PrimaryKeyConstraint("id", name="university_aliases_pkey"),
    sa.UniqueConstraint(
        "university_id",
        "normalized_alias",
        "alias_type",
        name="university_aliases_university_id_normalized_alias_alias_typ_key",
    ),
)

university_year_features = sa.Table(
    "university_year_features",
    metadata,
    sa.Column("university_id", sa.UUID(as_uuid=True), nullable=False),
    sa.Column("admission_year", sa.SmallInteger(), nullable=False),
    sa.Column("feature_key", sa.Text(), nullable=False),
    sa.Column("feature_value", postgresql.JSONB(), nullable=False),
    sa.Column("verification_status", sa.Text(), nullable=False),
    sa.Column("primary_snapshot_id", sa.UUID(as_uuid=True), nullable=False),
    sa.CheckConstraint(
        "verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])",
        name="university_year_features_verification_status_check",
    ),
    sa.ForeignKeyConstraint(
        ["primary_snapshot_id"],
        ["source_snapshots.id"],
        name="university_year_features_primary_snapshot_id_fkey",
    ),
    sa.ForeignKeyConstraint(
        ["university_id", "admission_year"],
        ["admission_years.university_id", "admission_years.admission_year"],
        name="university_year_features_university_id_admission_year_fkey",
    ),
    sa.PrimaryKeyConstraint(
        "university_id", "admission_year", "feature_key", name="university_year_features_pkey"
    ),
)


sa.Index(
    "one_current_conversion_rule",
    conversion_rules.c.program_year_id,
    conversion_rules.c.rule_key,
    unique=True,
    postgresql_where=sa.text("is_current"),
)

sa.Index(
    "source_checks", crawl_fetches.c.source_id, crawl_fetches.c.checked_at.desc(), unique=False
)


sa.Index(
    "current_verified_cutoff",
    cutoff_scores.c.score_scale_id,
    cutoff_scores.c.score,
    cutoff_scores.c.program_admission_id,
    unique=False,
    postgresql_where=sa.text("(is_current AND (verification_status = 'verified'::text))"),
)
sa.Index(
    "one_current_cutoff",
    cutoff_scores.c.program_admission_id,
    unique=True,
    postgresql_where=sa.text("is_current"),
)


sa.Index(
    "one_current_exam_event",
    exam_events.c.organizer_key,
    exam_events.c.exam_year,
    exam_events.c.event_key,
    unique=True,
    postgresql_where=sa.text("is_current"),
)

sa.Index(
    "ready_jobs",
    ingest_jobs.c.available_at,
    ingest_jobs.c.priority.desc(),
    unique=False,
    postgresql_where=sa.text("(status = ANY (ARRAY['queued'::text, 'retry_wait'::text]))"),
)


sa.Index("observations_hash", observations.c.payload_hash, unique=False)

sa.Index(
    "admission_filter",
    program_admissions.c.method_id,
    program_admissions.c.combination_id,
    program_admissions.c.program_year_id,
    unique=False,
)


sa.Index(
    "program_year_filter",
    program_years.c.admission_year,
    program_years.c.university_id,
    program_years.c.program_id,
    unique=False,
)

sa.Index(
    "program_name_trgm",
    programs.c.normalized_name,
    unique=False,
    postgresql_using="gin",
    postgresql_ops={"normalized_name": "gin_trgm_ops"},
)

sa.Index(
    "open_quality_issues",
    quality_issues.c.issue_code,
    quality_issues.c.created_at,
    unique=False,
    postgresql_where=sa.text("(status = 'open'::text)"),
)

sa.Index(
    "one_current_scholarship",
    scholarships.c.university_id,
    scholarships.c.admission_year,
    scholarships.c.program_year_id,
    scholarships.c.policy_key,
    unique=True,
    postgresql_nulls_not_distinct=True,
    postgresql_where=sa.text("is_current"),
)


sa.Index(
    "one_current_scoring_rule",
    scoring_rules.c.program_year_id,
    scoring_rules.c.method_id,
    scoring_rules.c.rule_key,
    unique=True,
    postgresql_where=sa.text("is_current"),
)


sa.Index(
    "one_current_tuition",
    tuition.c.university_id,
    tuition.c.admission_year,
    tuition.c.program_year_id,
    tuition.c.policy_key,
    unique=True,
    postgresql_nulls_not_distinct=True,
    postgresql_where=sa.text("is_current"),
)

sa.Index(
    "university_name_trgm",
    universities.c.normalized_name,
    unique=False,
    postgresql_using="gin",
    postgresql_ops={"normalized_name": "gin_trgm_ops"},
)

sa.Index(
    "university_alias_trgm",
    university_aliases.c.normalized_alias,
    unique=False,
    postgresql_using="gin",
    postgresql_ops={"normalized_alias": "gin_trgm_ops"},
)


class University(Base):
    __table__ = universities


class UniversityAlias(Base):
    __table__ = university_aliases


class Major(Base):
    __table__ = majors


class Program(Base):
    __table__ = programs


class ProgramAlias(Base):
    __table__ = program_aliases


class AdmissionMethod(Base):
    __table__ = admission_methods


class Subject(Base):
    __table__ = subjects


class Combination(Base):
    __table__ = combinations


class CombinationSubject(Base):
    __table__ = combination_subjects


class Source(Base):
    __table__ = sources


class SourceSnapshot(Base):
    __table__ = source_snapshots


class CrawlFetch(Base):
    __table__ = crawl_fetches


class Observation(Base):
    __table__ = observations


class AdmissionYear(Base):
    __table__ = admission_years


class UniversityYearFeature(Base):
    __table__ = university_year_features


class ProgramYear(Base):
    __table__ = program_years


class ScoreScale(Base):
    __table__ = score_scales


class ScoringRule(Base):
    __table__ = scoring_rules


class ProgramAdmission(Base):
    __table__ = program_admissions


class CutoffScore(Base):
    __table__ = cutoff_scores


class CutoffEvidence(Base):
    __table__ = cutoff_evidence


class ConversionRule(Base):
    __table__ = conversion_rules


class Tuition(Base):
    __table__ = tuition


class Scholarship(Base):
    __table__ = scholarships


class ExamEvent(Base):
    __table__ = exam_events


class IngestJob(Base):
    __table__ = ingest_jobs


class QualityIssue(Base):
    __table__ = quality_issues


class AuditEvent(Base):
    __table__ = audit_events


class DatasetRelease(Base):
    __table__ = dataset_releases


class CatalogState(Base):
    __table__ = catalog_state


class SnaRun(Base):
    __table__ = sna_runs
