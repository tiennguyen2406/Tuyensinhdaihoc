CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE universities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_code text NOT NULL UNIQUE,
    name text NOT NULL,
    short_name text,
    normalized_name text NOT NULL,
    slug text NOT NULL UNIQUE,
    province_code text,
    university_type text,
    website text,
    verification_status text NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified','verified','disputed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE university_aliases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid NOT NULL REFERENCES universities(id),
    alias text NOT NULL,
    normalized_alias text NOT NULL,
    alias_type text NOT NULL CHECK (alias_type IN ('name','short_name','legacy_code','domain')),
    valid_from date,
    valid_to date,
    evidence_url text NOT NULL,
    approved_by text NOT NULL,
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
    UNIQUE (university_id, normalized_alias, alias_type)
);
-- Alias không unique toàn cục: cùng cách gọi có thể trỏ tới nhiều trường.

CREATE TABLE majors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code_system text NOT NULL,
    major_code text NOT NULL,
    name text NOT NULL,
    UNIQUE (code_system, major_code)
);

CREATE TABLE programs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid NOT NULL REFERENCES universities(id),
    canonical_key text NOT NULL,
    program_name text NOT NULL,
    normalized_name text NOT NULL,
    major_id uuid REFERENCES majors(id),
    UNIQUE (university_id, canonical_key),
    UNIQUE (id, university_id)
);

CREATE TABLE program_aliases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid NOT NULL,
    program_id uuid NOT NULL,
    normalized_alias text NOT NULL,
    admission_year smallint,
    evidence_url text NOT NULL,
    approved_by text NOT NULL,
    FOREIGN KEY (program_id, university_id) REFERENCES programs(id, university_id),
    UNIQUE NULLS NOT DISTINCT (program_id, normalized_alias, admission_year)
);

CREATE TABLE admission_methods (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    input_kind text NOT NULL CHECK (input_kind IN ('subjects','transcript','exam_total','composite')),
    description text
);

CREATE TABLE subjects (
    code text PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE combinations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE,
    name text NOT NULL
);

CREATE TABLE combination_subjects (
    combination_id uuid NOT NULL REFERENCES combinations(id),
    subject_code text NOT NULL REFERENCES subjects(code),
    position smallint NOT NULL CHECK (position BETWEEN 1 AND 3),
    PRIMARY KEY (combination_id, subject_code),
    UNIQUE (combination_id, position)
);
-- Rule publication kiểm tra các tổ hợp chuẩn có đủ 3 môn;
-- trọng số thuộc scoring_rules, không hardcode trong combination.

CREATE TABLE sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_url text NOT NULL UNIQUE,
    domain text NOT NULL,
    publisher text NOT NULL,
    university_id uuid REFERENCES universities(id),
    source_type text NOT NULL CHECK (source_type IN
        ('university','admission_office','official_portal','exam_organizer','press','aggregator')),
    authority_scope jsonb NOT NULL DEFAULT '{}',
    title text,
    etag text,
    last_modified text,
    last_checked_at timestamptz,
    verification_status text NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified','verified','disputed','rejected'))
);

CREATE TABLE source_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid NOT NULL REFERENCES sources(id),
    raw_hash text NOT NULL CHECK (raw_hash ~ '^[0-9a-f]{64}$'),
    raw_uri text NOT NULL,
    final_url text NOT NULL,
    media_type text NOT NULL,
    byte_size bigint NOT NULL CHECK (byte_size >= 0),
    source_title text,
    source_published_at timestamptz,
    publication_precision text NOT NULL DEFAULT 'unknown'
        CHECK (publication_precision IN ('timestamp','date','unknown')),
    first_crawled_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_id, raw_hash)
);

CREATE TABLE crawl_fetches (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id uuid NOT NULL REFERENCES sources(id),
    snapshot_id uuid REFERENCES source_snapshots(id),
    checked_at timestamptz NOT NULL DEFAULT now(),
    http_status smallint CHECK (http_status BETWEEN 100 AND 599),
    outcome text NOT NULL,
    elapsed_ms integer CHECK (elapsed_ms >= 0),
    error_code text,
    response_validators jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE observations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    fact_kind text NOT NULL CHECK (fact_kind IN
        ('cutoff','tuition','scholarship','exam_event','scoring_rule','conversion_rule','catalog')),
    record_locator text NOT NULL,
    parser_version text NOT NULL,
    transform_version text NOT NULL,
    raw_fields jsonb NOT NULL,
    normalized_fields jsonb NOT NULL,
    payload_hash text NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    extraction_method text NOT NULL,
    extraction_confidence numeric(5,4)
        CHECK (extraction_confidence BETWEEN 0 AND 1),
    verification_status text NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified','reviewed','verified','rejected','disputed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (snapshot_id, record_locator, parser_version, transform_version)
);
-- transform_version bao gồm normalizer, resolver và alias registry versions.

CREATE TABLE admission_years (
    university_id uuid NOT NULL REFERENCES universities(id),
    admission_year smallint NOT NULL CHECK (admission_year BETWEEN 2000 AND 2100),
    status text NOT NULL CHECK (status IN ('unknown','partial','published','verified')),
    primary_snapshot_id uuid REFERENCES source_snapshots(id),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (university_id, admission_year)
);

CREATE TABLE university_year_features (
    university_id uuid NOT NULL,
    admission_year smallint NOT NULL,
    feature_key text NOT NULL,
    feature_value jsonb NOT NULL,
    verification_status text NOT NULL CHECK (verification_status IN
        ('unverified','verified','disputed','rejected')),
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    FOREIGN KEY (university_id, admission_year)
        REFERENCES admission_years(university_id, admission_year),
    PRIMARY KEY (university_id, admission_year, feature_key)
);
-- Ví dụ feature_key: dormitory, enterprise_partnerships.
-- Thiếu bản ghi nghĩa là unknown; false chỉ khi nguồn thật xác nhận không có.

CREATE TABLE program_years (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid NOT NULL,
    program_id uuid NOT NULL,
    admission_year smallint NOT NULL,
    offering_code text NOT NULL,
    offering_name text NOT NULL,
    campus_code text NOT NULL DEFAULT 'UNSPECIFIED',
    track_code text NOT NULL DEFAULT 'UNSPECIFIED',
    language_code text NOT NULL DEFAULT 'UNSPECIFIED',
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    FOREIGN KEY (program_id, university_id) REFERENCES programs(id, university_id),
    FOREIGN KEY (university_id, admission_year)
        REFERENCES admission_years(university_id, admission_year),
    UNIQUE (university_id, admission_year, offering_code, campus_code, track_code, language_code),
    UNIQUE (id, university_id, admission_year)
);

CREATE TABLE score_scales (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    method_id uuid NOT NULL REFERENCES admission_methods(id),
    admission_year smallint NOT NULL CHECK (admission_year BETWEEN 2000 AND 2100),
    code text NOT NULL,
    exam_version text NOT NULL,
    min_score numeric(12,5) NOT NULL DEFAULT 0,
    max_score numeric(12,5) NOT NULL,
    basis_description text NOT NULL,
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    CHECK (min_score >= 0 AND max_score > min_score),
    UNIQUE (method_id, admission_year, code, exam_version),
    UNIQUE (id, method_id),
    UNIQUE (id, max_score)
);


CREATE TABLE scoring_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    program_year_id uuid NOT NULL REFERENCES program_years(id),
    method_id uuid NOT NULL REFERENCES admission_methods(id),
    output_scale_id uuid NOT NULL,
    rule_key text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    input_schema jsonb NOT NULL,
    formula_dsl jsonb NOT NULL,
    eligibility_dsl jsonb NOT NULL DEFAULT '{}',
    priority_dsl jsonb NOT NULL DEFAULT '{}',
    rounding_dsl jsonb NOT NULL,
    required_components jsonb NOT NULL,
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    verification_status text NOT NULL
        CHECK (verification_status IN ('unverified','verified','disputed','rejected')),
    is_current boolean NOT NULL DEFAULT false,
    FOREIGN KEY (output_scale_id, method_id) REFERENCES score_scales(id, method_id),
    UNIQUE (program_year_id, method_id, rule_key, version),
    UNIQUE (id, program_year_id, method_id, output_scale_id),
    CHECK (NOT is_current OR verification_status = 'verified')
);
CREATE UNIQUE INDEX one_current_scoring_rule
    ON scoring_rules(program_year_id, method_id, rule_key) WHERE is_current;

CREATE TABLE program_admissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    program_year_id uuid NOT NULL REFERENCES program_years(id),
    method_id uuid NOT NULL REFERENCES admission_methods(id),
    combination_id uuid REFERENCES combinations(id),
    round_key text NOT NULL,
    population_key text NOT NULL,
    condition_key text NOT NULL,
    condition_text text NOT NULL,
    condition_dsl jsonb NOT NULL,
    score_scale_id uuid NOT NULL,
    scoring_rule_id uuid,
    data_status text NOT NULL CHECK (data_status IN ('announced','published','withdrawn','unknown')),
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    FOREIGN KEY (score_scale_id, method_id) REFERENCES score_scales(id, method_id),
    FOREIGN KEY (scoring_rule_id, program_year_id, method_id, score_scale_id)
        REFERENCES scoring_rules(id, program_year_id, method_id, output_scale_id),
    UNIQUE NULLS NOT DISTINCT
        (program_year_id, method_id, combination_id, round_key, population_key, condition_key),
    UNIQUE (id, score_scale_id)
);

CREATE TABLE cutoff_scores (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    program_admission_id uuid NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    score_scale_id uuid NOT NULL,
    score numeric(12,5) NOT NULL,
    max_score numeric(12,5) NOT NULL,
    fact_fingerprint text NOT NULL CHECK (fact_fingerprint ~ '^[0-9a-f]{64}$'),
    publication_group_key text NOT NULL,
    fact_payload jsonb NOT NULL,
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    source_published_at timestamptz,
    effective_from date,
    system_valid_from timestamptz NOT NULL DEFAULT now(),
    system_valid_to timestamptz,
    verification_status text NOT NULL CHECK (verification_status IN
        ('unverified','verified','disputed','rejected')),
    is_current boolean NOT NULL DEFAULT false,
    reviewed_by text,
    review_reason text,
    FOREIGN KEY (program_admission_id, score_scale_id)
        REFERENCES program_admissions(id, score_scale_id),
    FOREIGN KEY (score_scale_id, max_score) REFERENCES score_scales(id, max_score),
    CHECK (score >= 0 AND score <= max_score),
    CHECK (system_valid_to IS NULL OR system_valid_to >= system_valid_from),
    CHECK (NOT is_current OR
        (system_valid_to IS NULL AND verification_status IN ('verified','disputed'))),
    UNIQUE (program_admission_id, revision)
);
CREATE UNIQUE INDEX one_current_cutoff
    ON cutoff_scores(program_admission_id) WHERE is_current;

CREATE TABLE cutoff_evidence (
    cutoff_id uuid NOT NULL REFERENCES cutoff_scores(id),
    observation_id uuid NOT NULL REFERENCES observations(id),
    evidence_role text NOT NULL CHECK (evidence_role IN
        ('primary','supporting','conflicting','superseding')),
    attached_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (cutoff_id, observation_id)
);

CREATE TABLE conversion_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    program_year_id uuid NOT NULL REFERENCES program_years(id),
    from_method_id uuid NOT NULL REFERENCES admission_methods(id),
    to_method_id uuid NOT NULL REFERENCES admission_methods(id),
    from_scale_id uuid NOT NULL,
    to_scale_id uuid NOT NULL,
    rule_key text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    input_requirements jsonb NOT NULL,
    formula_dsl jsonb NOT NULL,
    applicability_dsl jsonb NOT NULL,
    rounding_dsl jsonb NOT NULL,
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    verification_status text NOT NULL CHECK (verification_status IN
        ('unverified','verified','disputed','rejected')),
    is_current boolean NOT NULL DEFAULT false,
    FOREIGN KEY (from_scale_id, from_method_id) REFERENCES score_scales(id, method_id),
    FOREIGN KEY (to_scale_id, to_method_id) REFERENCES score_scales(id, method_id),
    UNIQUE (program_year_id, rule_key, version),
    CHECK (from_scale_id <> to_scale_id),
    CHECK (NOT is_current OR verification_status = 'verified')
);
CREATE UNIQUE INDEX one_current_conversion_rule
    ON conversion_rules(program_year_id, rule_key) WHERE is_current;


CREATE TABLE tuition (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid NOT NULL,
    admission_year smallint NOT NULL,
    program_year_id uuid,
    policy_key text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    amount_min numeric(18,2),
    amount_max numeric(18,2),
    currency char(3) NOT NULL,
    unit text NOT NULL CHECK (unit IN
        ('credit','semester','academic_year','full_program','other','unknown')),
    description text NOT NULL,
    scope_dsl jsonb NOT NULL,
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    verification_status text NOT NULL CHECK (verification_status IN
        ('unverified','verified','disputed','rejected')),
    is_current boolean NOT NULL DEFAULT false,
    FOREIGN KEY (university_id, admission_year)
        REFERENCES admission_years(university_id, admission_year),
    FOREIGN KEY (program_year_id, university_id, admission_year)
        REFERENCES program_years(id, university_id, admission_year),
    CHECK (amount_min IS NULL OR amount_min >= 0),
    CHECK (amount_max IS NULL OR amount_max >= 0),
    CHECK (amount_min IS NULL OR amount_max IS NULL OR amount_max >= amount_min),
    CHECK (NOT is_current OR verification_status IN ('verified','disputed')),
    UNIQUE NULLS NOT DISTINCT
        (university_id, admission_year, program_year_id, policy_key, revision)
);
CREATE UNIQUE INDEX one_current_tuition
    ON tuition(university_id, admission_year, program_year_id, policy_key)
    NULLS NOT DISTINCT WHERE is_current;

CREATE TABLE scholarships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id uuid NOT NULL,
    admission_year smallint NOT NULL,
    program_year_id uuid,
    policy_key text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    name text NOT NULL,
    eligibility_dsl jsonb NOT NULL,
    eligibility_text text NOT NULL,
    benefit jsonb NOT NULL,
    deadline_date date,
    deadline_at timestamptz,
    deadline_precision text NOT NULL CHECK (deadline_precision IN ('date','timestamp','unknown')),
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    verification_status text NOT NULL CHECK (verification_status IN
        ('unverified','verified','disputed','rejected')),
    is_current boolean NOT NULL DEFAULT false,
    FOREIGN KEY (university_id, admission_year)
        REFERENCES admission_years(university_id, admission_year),
    FOREIGN KEY (program_year_id, university_id, admission_year)
        REFERENCES program_years(id, university_id, admission_year),
    CHECK (NOT is_current OR verification_status IN ('verified','disputed')),
    UNIQUE NULLS NOT DISTINCT
        (university_id, admission_year, program_year_id, policy_key, revision)
);
CREATE UNIQUE INDEX one_current_scholarship
    ON scholarships(university_id, admission_year, program_year_id, policy_key)
    NULLS NOT DISTINCT WHERE is_current;

CREATE TABLE exam_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    method_id uuid NOT NULL REFERENCES admission_methods(id),
    exam_year smallint NOT NULL CHECK (exam_year BETWEEN 2000 AND 2100),
    organizer_key text NOT NULL,
    event_key text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    event_type text NOT NULL,
    name text NOT NULL,
    starts_at timestamptz,
    ends_at timestamptz,
    event_date date,
    time_precision text NOT NULL CHECK (time_precision IN ('date','timestamp','unknown')),
    timezone_name text NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',
    primary_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
    verification_status text NOT NULL CHECK (verification_status IN
        ('unverified','verified','disputed','rejected')),
    is_current boolean NOT NULL DEFAULT false,
    CHECK (ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at),
    UNIQUE (organizer_key, exam_year, event_key, revision)
);
CREATE UNIQUE INDEX one_current_exam_event
    ON exam_events(organizer_key, exam_year, event_key) WHERE is_current;


CREATE TABLE ingest_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type text NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    payload jsonb NOT NULL,
    status text NOT NULL CHECK (status IN
        ('queued','leased','succeeded','retry_wait','failed','quarantined')),
    priority integer NOT NULL DEFAULT 0,
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at timestamptz NOT NULL DEFAULT now(),
    lease_until timestamptz,
    worker_id text,
    last_error jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quality_issues (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id uuid REFERENCES observations(id),
    entity_kind text NOT NULL,
    entity_id uuid,
    issue_code text NOT NULL,
    severity text NOT NULL CHECK (severity IN ('info','warning','error','critical')),
    details jsonb NOT NULL,
    status text NOT NULL CHECK (status IN ('open','resolved','dismissed')),
    resolved_by text,
    resolution_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE TABLE audit_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id text NOT NULL,
    action text NOT NULL,
    entity_kind text NOT NULL,
    entity_id uuid,
    before_data jsonb,
    after_data jsonb,
    reason text NOT NULL,
    request_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dataset_releases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version bigint NOT NULL UNIQUE CHECK (version >= 0),
    manifest_uri text NOT NULL,
    manifest_sha256 text NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    cutoff_count bigint NOT NULL CHECK (cutoff_count >= 0),
    metadata jsonb NOT NULL,
    published_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE catalog_state (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    dataset_version bigint NOT NULL DEFAULT 0 CHECK (dataset_version >= 0),
    changed_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO catalog_state(singleton, dataset_version) VALUES (true, 0);

CREATE TABLE sna_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_release_id uuid NOT NULL REFERENCES dataset_releases(id),
    graph_type text NOT NULL,
    reference_year smallint NOT NULL,
    parameters jsonb NOT NULL,
    library_versions jsonb NOT NULL,
    random_seed integer NOT NULL,
    status text NOT NULL CHECK (status IN ('queued','running','succeeded','failed')),
    graph_uri text,
    metrics jsonb,
    started_at timestamptz,
    finished_at timestamptz
);

CREATE INDEX university_name_trgm ON universities USING gin (normalized_name gin_trgm_ops);
CREATE INDEX university_alias_trgm ON university_aliases USING gin (normalized_alias gin_trgm_ops);
CREATE INDEX program_name_trgm ON programs USING gin (normalized_name gin_trgm_ops);
CREATE INDEX program_year_filter ON program_years(admission_year, university_id, program_id);
CREATE INDEX admission_filter ON program_admissions(method_id, combination_id, program_year_id);
CREATE INDEX current_verified_cutoff ON cutoff_scores(score_scale_id, score, program_admission_id)
    WHERE is_current AND verification_status = 'verified';
CREATE INDEX observations_hash ON observations(payload_hash);
CREATE INDEX source_checks ON crawl_fetches(source_id, checked_at DESC);
CREATE INDEX ready_jobs ON ingest_jobs(available_at, priority DESC)
    WHERE status IN ('queued','retry_wait');
CREATE INDEX open_quality_issues ON quality_issues(issue_code, created_at)
    WHERE status = 'open';
