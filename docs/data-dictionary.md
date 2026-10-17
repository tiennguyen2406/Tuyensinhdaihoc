# Data dictionary

Generated from static mappings; matches frozen v1.0 DDL (see schema-provenance.md).

Scores/money use Decimal; JSON decimal values must be strings. All timestamps are timezone-aware.

## admission_methods

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| code | TEXT | False |  |
| name | TEXT | False |  |
| input_kind | TEXT | False |  |
| description | TEXT | True |  |

```sql
CREATE TABLE admission_methods (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	code TEXT NOT NULL, 
	name TEXT NOT NULL, 
	input_kind TEXT NOT NULL, 
	description TEXT, 
	CONSTRAINT admission_methods_pkey PRIMARY KEY (id), 
	CONSTRAINT admission_methods_input_kind_check CHECK (input_kind = ANY (ARRAY['subjects'::text, 'transcript'::text, 'exam_total'::text, 'composite'::text])), 
	CONSTRAINT admission_methods_code_key UNIQUE (code)
);
```

## admission_years

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| university_id | UUID | False |  |
| admission_year | SMALLINT | False |  |
| status | TEXT | False |  |
| primary_snapshot_id | UUID | True |  |
| updated_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE admission_years (
	university_id UUID NOT NULL, 
	admission_year SMALLINT NOT NULL, 
	status TEXT NOT NULL, 
	primary_snapshot_id UUID, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT admission_years_pkey PRIMARY KEY (university_id, admission_year), 
	CONSTRAINT admission_years_admission_year_check CHECK (admission_year >= 2000 AND admission_year <= 2100), 
	CONSTRAINT admission_years_status_check CHECK (status = ANY (ARRAY['unknown'::text, 'partial'::text, 'published'::text, 'verified'::text])), 
	CONSTRAINT admission_years_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT admission_years_university_id_fkey FOREIGN KEY(university_id) REFERENCES universities (id)
);
```

## audit_events

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | BIGINT | False | IDENTITY |
| actor_id | TEXT | False |  |
| action | TEXT | False |  |
| entity_kind | TEXT | False |  |
| entity_id | UUID | True |  |
| before_data | JSONB | True |  |
| after_data | JSONB | True |  |
| reason | TEXT | False |  |
| request_id | TEXT | False |  |
| created_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE audit_events (
	id BIGINT GENERATED ALWAYS AS IDENTITY, 
	actor_id TEXT NOT NULL, 
	action TEXT NOT NULL, 
	entity_kind TEXT NOT NULL, 
	entity_id UUID, 
	before_data JSONB, 
	after_data JSONB, 
	reason TEXT NOT NULL, 
	request_id TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT audit_events_pkey PRIMARY KEY (id)
);
```

## catalog_state

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| singleton | BOOLEAN | False | true |
| dataset_version | BIGINT | False | 0 |
| changed_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE catalog_state (
	singleton BOOLEAN DEFAULT true NOT NULL, 
	dataset_version BIGINT DEFAULT 0 NOT NULL, 
	changed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT catalog_state_pkey PRIMARY KEY (singleton), 
	CONSTRAINT catalog_state_dataset_version_check CHECK (dataset_version >= 0), 
	CONSTRAINT catalog_state_singleton_check CHECK (singleton)
);
```

## combination_subjects

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| combination_id | UUID | False |  |
| subject_code | TEXT | False |  |
| position | SMALLINT | False |  |

```sql
CREATE TABLE combination_subjects (
	combination_id UUID NOT NULL, 
	subject_code TEXT NOT NULL, 
	position SMALLINT NOT NULL, 
	CONSTRAINT combination_subjects_pkey PRIMARY KEY (combination_id, subject_code), 
	CONSTRAINT combination_subjects_position_check CHECK ("position" >= 1 AND "position" <= 3), 
	CONSTRAINT combination_subjects_combination_id_fkey FOREIGN KEY(combination_id) REFERENCES combinations (id), 
	CONSTRAINT combination_subjects_subject_code_fkey FOREIGN KEY(subject_code) REFERENCES subjects (code), 
	CONSTRAINT combination_subjects_combination_id_position_key UNIQUE (combination_id, position)
);
```

## combinations

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| code | TEXT | False |  |
| name | TEXT | False |  |

```sql
CREATE TABLE combinations (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	code TEXT NOT NULL, 
	name TEXT NOT NULL, 
	CONSTRAINT combinations_pkey PRIMARY KEY (id), 
	CONSTRAINT combinations_code_key UNIQUE (code)
);
```

## conversion_rules

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| program_year_id | UUID | False |  |
| from_method_id | UUID | False |  |
| to_method_id | UUID | False |  |
| from_scale_id | UUID | False |  |
| to_scale_id | UUID | False |  |
| rule_key | TEXT | False |  |
| version | INTEGER | False |  |
| input_requirements | JSONB | False |  |
| formula_dsl | JSONB | False |  |
| applicability_dsl | JSONB | False |  |
| rounding_dsl | JSONB | False |  |
| primary_snapshot_id | UUID | False |  |
| verification_status | TEXT | False |  |
| is_current | BOOLEAN | False | false |

```sql
CREATE TABLE conversion_rules (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	program_year_id UUID NOT NULL, 
	from_method_id UUID NOT NULL, 
	to_method_id UUID NOT NULL, 
	from_scale_id UUID NOT NULL, 
	to_scale_id UUID NOT NULL, 
	rule_key TEXT NOT NULL, 
	version INTEGER NOT NULL, 
	input_requirements JSONB NOT NULL, 
	formula_dsl JSONB NOT NULL, 
	applicability_dsl JSONB NOT NULL, 
	rounding_dsl JSONB NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	verification_status TEXT NOT NULL, 
	is_current BOOLEAN DEFAULT false NOT NULL, 
	CONSTRAINT conversion_rules_pkey PRIMARY KEY (id), 
	CONSTRAINT conversion_rules_check CHECK (from_scale_id <> to_scale_id), 
	CONSTRAINT conversion_rules_check1 CHECK (NOT is_current OR verification_status = 'verified'::text), 
	CONSTRAINT conversion_rules_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT conversion_rules_version_check CHECK (version > 0), 
	CONSTRAINT conversion_rules_from_method_id_fkey FOREIGN KEY(from_method_id) REFERENCES admission_methods (id), 
	CONSTRAINT conversion_rules_from_scale_id_from_method_id_fkey FOREIGN KEY(from_scale_id, from_method_id) REFERENCES score_scales (id, method_id), 
	CONSTRAINT conversion_rules_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT conversion_rules_program_year_id_fkey FOREIGN KEY(program_year_id) REFERENCES program_years (id), 
	CONSTRAINT conversion_rules_to_method_id_fkey FOREIGN KEY(to_method_id) REFERENCES admission_methods (id), 
	CONSTRAINT conversion_rules_to_scale_id_to_method_id_fkey FOREIGN KEY(to_scale_id, to_method_id) REFERENCES score_scales (id, method_id), 
	CONSTRAINT conversion_rules_program_year_id_rule_key_version_key UNIQUE (program_year_id, rule_key, version)
);
```

```sql
CREATE UNIQUE INDEX one_current_conversion_rule ON conversion_rules (program_year_id, rule_key) WHERE is_current;
```

## crawl_fetches

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | BIGINT | False | IDENTITY |
| source_id | UUID | False |  |
| snapshot_id | UUID | True |  |
| checked_at | TIMESTAMP WITH TIME ZONE | False | now() |
| http_status | SMALLINT | True |  |
| outcome | TEXT | False |  |
| elapsed_ms | INTEGER | True |  |
| error_code | TEXT | True |  |
| response_validators | JSONB | False | '{}'::jsonb |

```sql
CREATE TABLE crawl_fetches (
	id BIGINT GENERATED ALWAYS AS IDENTITY, 
	source_id UUID NOT NULL, 
	snapshot_id UUID, 
	checked_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	http_status SMALLINT, 
	outcome TEXT NOT NULL, 
	elapsed_ms INTEGER, 
	error_code TEXT, 
	response_validators JSONB DEFAULT '{}'::jsonb NOT NULL, 
	CONSTRAINT crawl_fetches_pkey PRIMARY KEY (id), 
	CONSTRAINT crawl_fetches_elapsed_ms_check CHECK (elapsed_ms >= 0), 
	CONSTRAINT crawl_fetches_http_status_check CHECK (http_status >= 100 AND http_status <= 599), 
	CONSTRAINT crawl_fetches_snapshot_id_fkey FOREIGN KEY(snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT crawl_fetches_source_id_fkey FOREIGN KEY(source_id) REFERENCES sources (id)
);
```

```sql
CREATE INDEX source_checks ON crawl_fetches (source_id, checked_at DESC);
```

## cutoff_evidence

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| cutoff_id | UUID | False |  |
| observation_id | UUID | False |  |
| evidence_role | TEXT | False |  |
| attached_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE cutoff_evidence (
	cutoff_id UUID NOT NULL, 
	observation_id UUID NOT NULL, 
	evidence_role TEXT NOT NULL, 
	attached_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT cutoff_evidence_pkey PRIMARY KEY (cutoff_id, observation_id), 
	CONSTRAINT cutoff_evidence_evidence_role_check CHECK (evidence_role = ANY (ARRAY['primary'::text, 'supporting'::text, 'conflicting'::text, 'superseding'::text])), 
	CONSTRAINT cutoff_evidence_cutoff_id_fkey FOREIGN KEY(cutoff_id) REFERENCES cutoff_scores (id), 
	CONSTRAINT cutoff_evidence_observation_id_fkey FOREIGN KEY(observation_id) REFERENCES observations (id)
);
```

## cutoff_scores

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| program_admission_id | UUID | False |  |
| revision | INTEGER | False |  |
| score_scale_id | UUID | False |  |
| score | NUMERIC(12, 5) | False |  |
| max_score | NUMERIC(12, 5) | False |  |
| fact_fingerprint | TEXT | False |  |
| publication_group_key | TEXT | False |  |
| fact_payload | JSONB | False |  |
| primary_snapshot_id | UUID | False |  |
| source_published_at | TIMESTAMP WITH TIME ZONE | True |  |
| effective_from | DATE | True |  |
| system_valid_from | TIMESTAMP WITH TIME ZONE | False | now() |
| system_valid_to | TIMESTAMP WITH TIME ZONE | True |  |
| verification_status | TEXT | False |  |
| is_current | BOOLEAN | False | false |
| reviewed_by | TEXT | True |  |
| review_reason | TEXT | True |  |

```sql
CREATE TABLE cutoff_scores (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	program_admission_id UUID NOT NULL, 
	revision INTEGER NOT NULL, 
	score_scale_id UUID NOT NULL, 
	score NUMERIC(12, 5) NOT NULL, 
	max_score NUMERIC(12, 5) NOT NULL, 
	fact_fingerprint TEXT NOT NULL, 
	publication_group_key TEXT NOT NULL, 
	fact_payload JSONB NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	source_published_at TIMESTAMP WITH TIME ZONE, 
	effective_from DATE, 
	system_valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	system_valid_to TIMESTAMP WITH TIME ZONE, 
	verification_status TEXT NOT NULL, 
	is_current BOOLEAN DEFAULT false NOT NULL, 
	reviewed_by TEXT, 
	review_reason TEXT, 
	CONSTRAINT cutoff_scores_pkey PRIMARY KEY (id), 
	CONSTRAINT cutoff_scores_check CHECK (score >= 0::numeric AND score <= max_score), 
	CONSTRAINT cutoff_scores_check1 CHECK (system_valid_to IS NULL OR system_valid_to >= system_valid_from), 
	CONSTRAINT cutoff_scores_check2 CHECK (NOT is_current OR system_valid_to IS NULL AND (verification_status = ANY (ARRAY['verified'::text, 'disputed'::text]))), 
	CONSTRAINT cutoff_scores_fact_fingerprint_check CHECK (fact_fingerprint ~ '^[0-9a-f]{64}$'::text), 
	CONSTRAINT cutoff_scores_revision_check CHECK (revision > 0), 
	CONSTRAINT cutoff_scores_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT cutoff_scores_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT cutoff_scores_program_admission_id_score_scale_id_fkey FOREIGN KEY(program_admission_id, score_scale_id) REFERENCES program_admissions (id, score_scale_id), 
	CONSTRAINT cutoff_scores_score_scale_id_max_score_fkey FOREIGN KEY(score_scale_id, max_score) REFERENCES score_scales (id, max_score), 
	CONSTRAINT cutoff_scores_program_admission_id_revision_key UNIQUE (program_admission_id, revision)
);
```

```sql
CREATE INDEX current_verified_cutoff ON cutoff_scores (score_scale_id, score, program_admission_id) WHERE (is_current AND (verification_status = 'verified'::text));
```

```sql
CREATE UNIQUE INDEX one_current_cutoff ON cutoff_scores (program_admission_id) WHERE is_current;
```

## dataset_releases

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| version | BIGINT | False |  |
| manifest_uri | TEXT | False |  |
| manifest_sha256 | TEXT | False |  |
| cutoff_count | BIGINT | False |  |
| metadata | JSONB | False |  |
| published_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE dataset_releases (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	version BIGINT NOT NULL, 
	manifest_uri TEXT NOT NULL, 
	manifest_sha256 TEXT NOT NULL, 
	cutoff_count BIGINT NOT NULL, 
	metadata JSONB NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT dataset_releases_pkey PRIMARY KEY (id), 
	CONSTRAINT dataset_releases_cutoff_count_check CHECK (cutoff_count >= 0), 
	CONSTRAINT dataset_releases_manifest_sha256_check CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'::text), 
	CONSTRAINT dataset_releases_version_check CHECK (version >= 0), 
	CONSTRAINT dataset_releases_version_key UNIQUE (version)
);
```

## exam_events

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| method_id | UUID | False |  |
| exam_year | SMALLINT | False |  |
| organizer_key | TEXT | False |  |
| event_key | TEXT | False |  |
| revision | INTEGER | False |  |
| event_type | TEXT | False |  |
| name | TEXT | False |  |
| starts_at | TIMESTAMP WITH TIME ZONE | True |  |
| ends_at | TIMESTAMP WITH TIME ZONE | True |  |
| event_date | DATE | True |  |
| time_precision | TEXT | False |  |
| timezone_name | TEXT | False | 'Asia/Ho_Chi_Minh'::text |
| primary_snapshot_id | UUID | False |  |
| verification_status | TEXT | False |  |
| is_current | BOOLEAN | False | false |

```sql
CREATE TABLE exam_events (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	method_id UUID NOT NULL, 
	exam_year SMALLINT NOT NULL, 
	organizer_key TEXT NOT NULL, 
	event_key TEXT NOT NULL, 
	revision INTEGER NOT NULL, 
	event_type TEXT NOT NULL, 
	name TEXT NOT NULL, 
	starts_at TIMESTAMP WITH TIME ZONE, 
	ends_at TIMESTAMP WITH TIME ZONE, 
	event_date DATE, 
	time_precision TEXT NOT NULL, 
	timezone_name TEXT DEFAULT 'Asia/Ho_Chi_Minh'::text NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	verification_status TEXT NOT NULL, 
	is_current BOOLEAN DEFAULT false NOT NULL, 
	CONSTRAINT exam_events_pkey PRIMARY KEY (id), 
	CONSTRAINT exam_events_check CHECK (ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at), 
	CONSTRAINT exam_events_exam_year_check CHECK (exam_year >= 2000 AND exam_year <= 2100), 
	CONSTRAINT exam_events_revision_check CHECK (revision > 0), 
	CONSTRAINT exam_events_time_precision_check CHECK (time_precision = ANY (ARRAY['date'::text, 'timestamp'::text, 'unknown'::text])), 
	CONSTRAINT exam_events_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT exam_events_method_id_fkey FOREIGN KEY(method_id) REFERENCES admission_methods (id), 
	CONSTRAINT exam_events_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT exam_events_organizer_key_exam_year_event_key_revision_key UNIQUE (organizer_key, exam_year, event_key, revision)
);
```

```sql
CREATE UNIQUE INDEX one_current_exam_event ON exam_events (organizer_key, exam_year, event_key) WHERE is_current;
```

## ingest_jobs

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| job_type | TEXT | False |  |
| idempotency_key | TEXT | False |  |
| payload | JSONB | False |  |
| status | TEXT | False |  |
| priority | INTEGER | False | 0 |
| attempts | INTEGER | False | 0 |
| available_at | TIMESTAMP WITH TIME ZONE | False | now() |
| lease_until | TIMESTAMP WITH TIME ZONE | True |  |
| worker_id | TEXT | True |  |
| last_error | JSONB | True |  |
| created_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE ingest_jobs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	job_type TEXT NOT NULL, 
	idempotency_key TEXT NOT NULL, 
	payload JSONB NOT NULL, 
	status TEXT NOT NULL, 
	priority INTEGER DEFAULT 0 NOT NULL, 
	attempts INTEGER DEFAULT 0 NOT NULL, 
	available_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	lease_until TIMESTAMP WITH TIME ZONE, 
	worker_id TEXT, 
	last_error JSONB, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT ingest_jobs_pkey PRIMARY KEY (id), 
	CONSTRAINT ingest_jobs_attempts_check CHECK (attempts >= 0), 
	CONSTRAINT ingest_jobs_status_check CHECK (status = ANY (ARRAY['queued'::text, 'leased'::text, 'succeeded'::text, 'retry_wait'::text, 'failed'::text, 'quarantined'::text])), 
	CONSTRAINT ingest_jobs_idempotency_key_key UNIQUE (idempotency_key)
);
```

```sql
CREATE INDEX ready_jobs ON ingest_jobs (available_at, priority DESC) WHERE (status = ANY (ARRAY['queued'::text, 'retry_wait'::text]));
```

## majors

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| code_system | TEXT | False |  |
| major_code | TEXT | False |  |
| name | TEXT | False |  |

```sql
CREATE TABLE majors (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	code_system TEXT NOT NULL, 
	major_code TEXT NOT NULL, 
	name TEXT NOT NULL, 
	CONSTRAINT majors_pkey PRIMARY KEY (id), 
	CONSTRAINT majors_code_system_major_code_key UNIQUE (code_system, major_code)
);
```

## observations

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| snapshot_id | UUID | False |  |
| fact_kind | TEXT | False |  |
| record_locator | TEXT | False |  |
| parser_version | TEXT | False |  |
| transform_version | TEXT | False |  |
| raw_fields | JSONB | False |  |
| normalized_fields | JSONB | False |  |
| payload_hash | TEXT | False |  |
| extraction_method | TEXT | False |  |
| extraction_confidence | NUMERIC(5, 4) | True |  |
| verification_status | TEXT | False | 'unverified'::text |
| created_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE observations (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	snapshot_id UUID NOT NULL, 
	fact_kind TEXT NOT NULL, 
	record_locator TEXT NOT NULL, 
	parser_version TEXT NOT NULL, 
	transform_version TEXT NOT NULL, 
	raw_fields JSONB NOT NULL, 
	normalized_fields JSONB NOT NULL, 
	payload_hash TEXT NOT NULL, 
	extraction_method TEXT NOT NULL, 
	extraction_confidence NUMERIC(5, 4), 
	verification_status TEXT DEFAULT 'unverified'::text NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT observations_pkey PRIMARY KEY (id), 
	CONSTRAINT observations_extraction_confidence_check CHECK (extraction_confidence >= 0::numeric AND extraction_confidence <= 1::numeric), 
	CONSTRAINT observations_fact_kind_check CHECK (fact_kind = ANY (ARRAY['cutoff'::text, 'tuition'::text, 'scholarship'::text, 'exam_event'::text, 'scoring_rule'::text, 'conversion_rule'::text, 'catalog'::text])), 
	CONSTRAINT observations_payload_hash_check CHECK (payload_hash ~ '^[0-9a-f]{64}$'::text), 
	CONSTRAINT observations_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'reviewed'::text, 'verified'::text, 'rejected'::text, 'disputed'::text])), 
	CONSTRAINT observations_snapshot_id_fkey FOREIGN KEY(snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT observations_snapshot_id_record_locator_parser_version_tran_key UNIQUE (snapshot_id, record_locator, parser_version, transform_version)
);
```

```sql
CREATE INDEX observations_hash ON observations (payload_hash);
```

## program_admissions

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| program_year_id | UUID | False |  |
| method_id | UUID | False |  |
| combination_id | UUID | True |  |
| round_key | TEXT | False |  |
| population_key | TEXT | False |  |
| condition_key | TEXT | False |  |
| condition_text | TEXT | False |  |
| condition_dsl | JSONB | False |  |
| score_scale_id | UUID | False |  |
| scoring_rule_id | UUID | True |  |
| data_status | TEXT | False |  |
| primary_snapshot_id | UUID | False |  |

```sql
CREATE TABLE program_admissions (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	program_year_id UUID NOT NULL, 
	method_id UUID NOT NULL, 
	combination_id UUID, 
	round_key TEXT NOT NULL, 
	population_key TEXT NOT NULL, 
	condition_key TEXT NOT NULL, 
	condition_text TEXT NOT NULL, 
	condition_dsl JSONB NOT NULL, 
	score_scale_id UUID NOT NULL, 
	scoring_rule_id UUID, 
	data_status TEXT NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	CONSTRAINT program_admissions_pkey PRIMARY KEY (id), 
	CONSTRAINT program_admissions_data_status_check CHECK (data_status = ANY (ARRAY['announced'::text, 'published'::text, 'withdrawn'::text, 'unknown'::text])), 
	CONSTRAINT program_admissions_combination_id_fkey FOREIGN KEY(combination_id) REFERENCES combinations (id), 
	CONSTRAINT program_admissions_method_id_fkey FOREIGN KEY(method_id) REFERENCES admission_methods (id), 
	CONSTRAINT program_admissions_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT program_admissions_program_year_id_fkey FOREIGN KEY(program_year_id) REFERENCES program_years (id), 
	CONSTRAINT program_admissions_score_scale_id_method_id_fkey FOREIGN KEY(score_scale_id, method_id) REFERENCES score_scales (id, method_id), 
	CONSTRAINT program_admissions_scoring_rule_id_program_year_id_method__fkey FOREIGN KEY(scoring_rule_id, program_year_id, method_id, score_scale_id) REFERENCES scoring_rules (id, program_year_id, method_id, output_scale_id), 
	CONSTRAINT program_admissions_id_score_scale_id_key UNIQUE (id, score_scale_id), 
	CONSTRAINT program_admissions_program_year_id_method_id_combination_id_key UNIQUE NULLS NOT DISTINCT (program_year_id, method_id, combination_id, round_key, population_key, condition_key)
);
```

```sql
CREATE INDEX admission_filter ON program_admissions (method_id, combination_id, program_year_id);
```

## program_aliases

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_id | UUID | False |  |
| program_id | UUID | False |  |
| normalized_alias | TEXT | False |  |
| admission_year | SMALLINT | True |  |
| evidence_url | TEXT | False |  |
| approved_by | TEXT | False |  |

```sql
CREATE TABLE program_aliases (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_id UUID NOT NULL, 
	program_id UUID NOT NULL, 
	normalized_alias TEXT NOT NULL, 
	admission_year SMALLINT, 
	evidence_url TEXT NOT NULL, 
	approved_by TEXT NOT NULL, 
	CONSTRAINT program_aliases_pkey PRIMARY KEY (id), 
	CONSTRAINT program_aliases_program_id_university_id_fkey FOREIGN KEY(program_id, university_id) REFERENCES programs (id, university_id), 
	CONSTRAINT program_aliases_program_id_normalized_alias_admission_year_key UNIQUE NULLS NOT DISTINCT (program_id, normalized_alias, admission_year)
);
```

## program_years

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_id | UUID | False |  |
| program_id | UUID | False |  |
| admission_year | SMALLINT | False |  |
| offering_code | TEXT | False |  |
| offering_name | TEXT | False |  |
| campus_code | TEXT | False | 'UNSPECIFIED'::text |
| track_code | TEXT | False | 'UNSPECIFIED'::text |
| language_code | TEXT | False | 'UNSPECIFIED'::text |
| primary_snapshot_id | UUID | False |  |

```sql
CREATE TABLE program_years (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_id UUID NOT NULL, 
	program_id UUID NOT NULL, 
	admission_year SMALLINT NOT NULL, 
	offering_code TEXT NOT NULL, 
	offering_name TEXT NOT NULL, 
	campus_code TEXT DEFAULT 'UNSPECIFIED'::text NOT NULL, 
	track_code TEXT DEFAULT 'UNSPECIFIED'::text NOT NULL, 
	language_code TEXT DEFAULT 'UNSPECIFIED'::text NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	CONSTRAINT program_years_pkey PRIMARY KEY (id), 
	CONSTRAINT program_years_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT program_years_program_id_university_id_fkey FOREIGN KEY(program_id, university_id) REFERENCES programs (id, university_id), 
	CONSTRAINT program_years_university_id_admission_year_fkey FOREIGN KEY(university_id, admission_year) REFERENCES admission_years (university_id, admission_year), 
	CONSTRAINT program_years_id_university_id_admission_year_key UNIQUE (id, university_id, admission_year), 
	CONSTRAINT program_years_university_id_admission_year_offering_code_ca_key UNIQUE (university_id, admission_year, offering_code, campus_code, track_code, language_code)
);
```

```sql
CREATE INDEX program_year_filter ON program_years (admission_year, university_id, program_id);
```

## programs

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_id | UUID | False |  |
| canonical_key | TEXT | False |  |
| program_name | TEXT | False |  |
| normalized_name | TEXT | False |  |
| major_id | UUID | True |  |

```sql
CREATE TABLE programs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_id UUID NOT NULL, 
	canonical_key TEXT NOT NULL, 
	program_name TEXT NOT NULL, 
	normalized_name TEXT NOT NULL, 
	major_id UUID, 
	CONSTRAINT programs_pkey PRIMARY KEY (id), 
	CONSTRAINT programs_major_id_fkey FOREIGN KEY(major_id) REFERENCES majors (id), 
	CONSTRAINT programs_university_id_fkey FOREIGN KEY(university_id) REFERENCES universities (id), 
	CONSTRAINT programs_id_university_id_key UNIQUE (id, university_id), 
	CONSTRAINT programs_university_id_canonical_key_key UNIQUE (university_id, canonical_key)
);
```

```sql
CREATE INDEX program_name_trgm ON programs USING gin (normalized_name gin_trgm_ops);
```

## quality_issues

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| observation_id | UUID | True |  |
| entity_kind | TEXT | False |  |
| entity_id | UUID | True |  |
| issue_code | TEXT | False |  |
| severity | TEXT | False |  |
| details | JSONB | False |  |
| status | TEXT | False |  |
| resolved_by | TEXT | True |  |
| resolution_reason | TEXT | True |  |
| created_at | TIMESTAMP WITH TIME ZONE | False | now() |
| resolved_at | TIMESTAMP WITH TIME ZONE | True |  |

```sql
CREATE TABLE quality_issues (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	observation_id UUID, 
	entity_kind TEXT NOT NULL, 
	entity_id UUID, 
	issue_code TEXT NOT NULL, 
	severity TEXT NOT NULL, 
	details JSONB NOT NULL, 
	status TEXT NOT NULL, 
	resolved_by TEXT, 
	resolution_reason TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	CONSTRAINT quality_issues_pkey PRIMARY KEY (id), 
	CONSTRAINT quality_issues_severity_check CHECK (severity = ANY (ARRAY['info'::text, 'warning'::text, 'error'::text, 'critical'::text])), 
	CONSTRAINT quality_issues_status_check CHECK (status = ANY (ARRAY['open'::text, 'resolved'::text, 'dismissed'::text])), 
	CONSTRAINT quality_issues_observation_id_fkey FOREIGN KEY(observation_id) REFERENCES observations (id)
);
```

```sql
CREATE INDEX open_quality_issues ON quality_issues (issue_code, created_at) WHERE (status = 'open'::text);
```

## scholarships

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_id | UUID | False |  |
| admission_year | SMALLINT | False |  |
| program_year_id | UUID | True |  |
| policy_key | TEXT | False |  |
| revision | INTEGER | False |  |
| name | TEXT | False |  |
| eligibility_dsl | JSONB | False |  |
| eligibility_text | TEXT | False |  |
| benefit | JSONB | False |  |
| deadline_date | DATE | True |  |
| deadline_at | TIMESTAMP WITH TIME ZONE | True |  |
| deadline_precision | TEXT | False |  |
| primary_snapshot_id | UUID | False |  |
| verification_status | TEXT | False |  |
| is_current | BOOLEAN | False | false |

```sql
CREATE TABLE scholarships (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_id UUID NOT NULL, 
	admission_year SMALLINT NOT NULL, 
	program_year_id UUID, 
	policy_key TEXT NOT NULL, 
	revision INTEGER NOT NULL, 
	name TEXT NOT NULL, 
	eligibility_dsl JSONB NOT NULL, 
	eligibility_text TEXT NOT NULL, 
	benefit JSONB NOT NULL, 
	deadline_date DATE, 
	deadline_at TIMESTAMP WITH TIME ZONE, 
	deadline_precision TEXT NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	verification_status TEXT NOT NULL, 
	is_current BOOLEAN DEFAULT false NOT NULL, 
	CONSTRAINT scholarships_pkey PRIMARY KEY (id), 
	CONSTRAINT scholarships_check CHECK (NOT is_current OR (verification_status = ANY (ARRAY['verified'::text, 'disputed'::text]))), 
	CONSTRAINT scholarships_deadline_precision_check CHECK (deadline_precision = ANY (ARRAY['date'::text, 'timestamp'::text, 'unknown'::text])), 
	CONSTRAINT scholarships_revision_check CHECK (revision > 0), 
	CONSTRAINT scholarships_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT scholarships_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT scholarships_program_year_id_university_id_admission_year_fkey FOREIGN KEY(program_year_id, university_id, admission_year) REFERENCES program_years (id, university_id, admission_year), 
	CONSTRAINT scholarships_university_id_admission_year_fkey FOREIGN KEY(university_id, admission_year) REFERENCES admission_years (university_id, admission_year), 
	CONSTRAINT scholarships_university_id_admission_year_program_year_id_p_key UNIQUE NULLS NOT DISTINCT (university_id, admission_year, program_year_id, policy_key, revision)
);
```

```sql
CREATE UNIQUE INDEX one_current_scholarship ON scholarships (university_id, admission_year, program_year_id, policy_key) NULLS NOT DISTINCT WHERE is_current;
```

## score_scales

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| method_id | UUID | False |  |
| admission_year | SMALLINT | False |  |
| code | TEXT | False |  |
| exam_version | TEXT | False |  |
| min_score | NUMERIC(12, 5) | False | 0 |
| max_score | NUMERIC(12, 5) | False |  |
| basis_description | TEXT | False |  |
| primary_snapshot_id | UUID | False |  |

```sql
CREATE TABLE score_scales (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	method_id UUID NOT NULL, 
	admission_year SMALLINT NOT NULL, 
	code TEXT NOT NULL, 
	exam_version TEXT NOT NULL, 
	min_score NUMERIC(12, 5) DEFAULT 0 NOT NULL, 
	max_score NUMERIC(12, 5) NOT NULL, 
	basis_description TEXT NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	CONSTRAINT score_scales_pkey PRIMARY KEY (id), 
	CONSTRAINT score_scales_admission_year_check CHECK (admission_year >= 2000 AND admission_year <= 2100), 
	CONSTRAINT score_scales_check CHECK (min_score >= 0::numeric AND max_score > min_score), 
	CONSTRAINT score_scales_method_id_fkey FOREIGN KEY(method_id) REFERENCES admission_methods (id), 
	CONSTRAINT score_scales_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT score_scales_id_max_score_key UNIQUE (id, max_score), 
	CONSTRAINT score_scales_id_method_id_key UNIQUE (id, method_id), 
	CONSTRAINT score_scales_method_id_admission_year_code_exam_version_key UNIQUE (method_id, admission_year, code, exam_version)
);
```

## scoring_rules

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| program_year_id | UUID | False |  |
| method_id | UUID | False |  |
| output_scale_id | UUID | False |  |
| rule_key | TEXT | False |  |
| version | INTEGER | False |  |
| input_schema | JSONB | False |  |
| formula_dsl | JSONB | False |  |
| eligibility_dsl | JSONB | False | '{}'::jsonb |
| priority_dsl | JSONB | False | '{}'::jsonb |
| rounding_dsl | JSONB | False |  |
| required_components | JSONB | False |  |
| primary_snapshot_id | UUID | False |  |
| verification_status | TEXT | False |  |
| is_current | BOOLEAN | False | false |

```sql
CREATE TABLE scoring_rules (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	program_year_id UUID NOT NULL, 
	method_id UUID NOT NULL, 
	output_scale_id UUID NOT NULL, 
	rule_key TEXT NOT NULL, 
	version INTEGER NOT NULL, 
	input_schema JSONB NOT NULL, 
	formula_dsl JSONB NOT NULL, 
	eligibility_dsl JSONB DEFAULT '{}'::jsonb NOT NULL, 
	priority_dsl JSONB DEFAULT '{}'::jsonb NOT NULL, 
	rounding_dsl JSONB NOT NULL, 
	required_components JSONB NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	verification_status TEXT NOT NULL, 
	is_current BOOLEAN DEFAULT false NOT NULL, 
	CONSTRAINT scoring_rules_pkey PRIMARY KEY (id), 
	CONSTRAINT scoring_rules_check CHECK (NOT is_current OR verification_status = 'verified'::text), 
	CONSTRAINT scoring_rules_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT scoring_rules_version_check CHECK (version > 0), 
	CONSTRAINT scoring_rules_method_id_fkey FOREIGN KEY(method_id) REFERENCES admission_methods (id), 
	CONSTRAINT scoring_rules_output_scale_id_method_id_fkey FOREIGN KEY(output_scale_id, method_id) REFERENCES score_scales (id, method_id), 
	CONSTRAINT scoring_rules_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT scoring_rules_program_year_id_fkey FOREIGN KEY(program_year_id) REFERENCES program_years (id), 
	CONSTRAINT scoring_rules_id_program_year_id_method_id_output_scale_id_key UNIQUE (id, program_year_id, method_id, output_scale_id), 
	CONSTRAINT scoring_rules_program_year_id_method_id_rule_key_version_key UNIQUE (program_year_id, method_id, rule_key, version)
);
```

```sql
CREATE UNIQUE INDEX one_current_scoring_rule ON scoring_rules (program_year_id, method_id, rule_key) WHERE is_current;
```

## sna_runs

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| dataset_release_id | UUID | False |  |
| graph_type | TEXT | False |  |
| reference_year | SMALLINT | False |  |
| parameters | JSONB | False |  |
| library_versions | JSONB | False |  |
| random_seed | INTEGER | False |  |
| status | TEXT | False |  |
| graph_uri | TEXT | True |  |
| metrics | JSONB | True |  |
| started_at | TIMESTAMP WITH TIME ZONE | True |  |
| finished_at | TIMESTAMP WITH TIME ZONE | True |  |

```sql
CREATE TABLE sna_runs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	dataset_release_id UUID NOT NULL, 
	graph_type TEXT NOT NULL, 
	reference_year SMALLINT NOT NULL, 
	parameters JSONB NOT NULL, 
	library_versions JSONB NOT NULL, 
	random_seed INTEGER NOT NULL, 
	status TEXT NOT NULL, 
	graph_uri TEXT, 
	metrics JSONB, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	CONSTRAINT sna_runs_pkey PRIMARY KEY (id), 
	CONSTRAINT sna_runs_status_check CHECK (status = ANY (ARRAY['queued'::text, 'running'::text, 'succeeded'::text, 'failed'::text])), 
	CONSTRAINT sna_runs_dataset_release_id_fkey FOREIGN KEY(dataset_release_id) REFERENCES dataset_releases (id)
);
```

## source_snapshots

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| source_id | UUID | False |  |
| raw_hash | TEXT | False |  |
| raw_uri | TEXT | False |  |
| final_url | TEXT | False |  |
| media_type | TEXT | False |  |
| byte_size | BIGINT | False |  |
| source_title | TEXT | True |  |
| source_published_at | TIMESTAMP WITH TIME ZONE | True |  |
| publication_precision | TEXT | False | 'unknown'::text |
| first_crawled_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE source_snapshots (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	source_id UUID NOT NULL, 
	raw_hash TEXT NOT NULL, 
	raw_uri TEXT NOT NULL, 
	final_url TEXT NOT NULL, 
	media_type TEXT NOT NULL, 
	byte_size BIGINT NOT NULL, 
	source_title TEXT, 
	source_published_at TIMESTAMP WITH TIME ZONE, 
	publication_precision TEXT DEFAULT 'unknown'::text NOT NULL, 
	first_crawled_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT source_snapshots_pkey PRIMARY KEY (id), 
	CONSTRAINT source_snapshots_byte_size_check CHECK (byte_size >= 0), 
	CONSTRAINT source_snapshots_publication_precision_check CHECK (publication_precision = ANY (ARRAY['timestamp'::text, 'date'::text, 'unknown'::text])), 
	CONSTRAINT source_snapshots_raw_hash_check CHECK (raw_hash ~ '^[0-9a-f]{64}$'::text), 
	CONSTRAINT source_snapshots_source_id_fkey FOREIGN KEY(source_id) REFERENCES sources (id), 
	CONSTRAINT source_snapshots_source_id_raw_hash_key UNIQUE (source_id, raw_hash)
);
```

## sources

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| canonical_url | TEXT | False |  |
| domain | TEXT | False |  |
| publisher | TEXT | False |  |
| university_id | UUID | True |  |
| source_type | TEXT | False |  |
| authority_scope | JSONB | False | '{}'::jsonb |
| title | TEXT | True |  |
| etag | TEXT | True |  |
| last_modified | TEXT | True |  |
| last_checked_at | TIMESTAMP WITH TIME ZONE | True |  |
| verification_status | TEXT | False | 'unverified'::text |

```sql
CREATE TABLE sources (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	canonical_url TEXT NOT NULL, 
	domain TEXT NOT NULL, 
	publisher TEXT NOT NULL, 
	university_id UUID, 
	source_type TEXT NOT NULL, 
	authority_scope JSONB DEFAULT '{}'::jsonb NOT NULL, 
	title TEXT, 
	etag TEXT, 
	last_modified TEXT, 
	last_checked_at TIMESTAMP WITH TIME ZONE, 
	verification_status TEXT DEFAULT 'unverified'::text NOT NULL, 
	CONSTRAINT sources_pkey PRIMARY KEY (id), 
	CONSTRAINT sources_source_type_check CHECK (source_type = ANY (ARRAY['university'::text, 'admission_office'::text, 'official_portal'::text, 'exam_organizer'::text, 'press'::text, 'aggregator'::text])), 
	CONSTRAINT sources_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT sources_university_id_fkey FOREIGN KEY(university_id) REFERENCES universities (id), 
	CONSTRAINT sources_canonical_url_key UNIQUE (canonical_url)
);
```

## subjects

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| code | TEXT | False |  |
| name | TEXT | False |  |

```sql
CREATE TABLE subjects (
	code TEXT NOT NULL, 
	name TEXT NOT NULL, 
	CONSTRAINT subjects_pkey PRIMARY KEY (code)
);
```

## tuition

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_id | UUID | False |  |
| admission_year | SMALLINT | False |  |
| program_year_id | UUID | True |  |
| policy_key | TEXT | False |  |
| revision | INTEGER | False |  |
| amount_min | NUMERIC(18, 2) | True |  |
| amount_max | NUMERIC(18, 2) | True |  |
| currency | CHAR(3) | False |  |
| unit | TEXT | False |  |
| description | TEXT | False |  |
| scope_dsl | JSONB | False |  |
| primary_snapshot_id | UUID | False |  |
| verification_status | TEXT | False |  |
| is_current | BOOLEAN | False | false |

```sql
CREATE TABLE tuition (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_id UUID NOT NULL, 
	admission_year SMALLINT NOT NULL, 
	program_year_id UUID, 
	policy_key TEXT NOT NULL, 
	revision INTEGER NOT NULL, 
	amount_min NUMERIC(18, 2), 
	amount_max NUMERIC(18, 2), 
	currency CHAR(3) NOT NULL, 
	unit TEXT NOT NULL, 
	description TEXT NOT NULL, 
	scope_dsl JSONB NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	verification_status TEXT NOT NULL, 
	is_current BOOLEAN DEFAULT false NOT NULL, 
	CONSTRAINT tuition_pkey PRIMARY KEY (id), 
	CONSTRAINT tuition_amount_max_check CHECK (amount_max IS NULL OR amount_max >= 0::numeric), 
	CONSTRAINT tuition_amount_min_check CHECK (amount_min IS NULL OR amount_min >= 0::numeric), 
	CONSTRAINT tuition_check CHECK (amount_min IS NULL OR amount_max IS NULL OR amount_max >= amount_min), 
	CONSTRAINT tuition_check1 CHECK (NOT is_current OR (verification_status = ANY (ARRAY['verified'::text, 'disputed'::text]))), 
	CONSTRAINT tuition_revision_check CHECK (revision > 0), 
	CONSTRAINT tuition_unit_check CHECK (unit = ANY (ARRAY['credit'::text, 'semester'::text, 'academic_year'::text, 'full_program'::text, 'other'::text, 'unknown'::text])), 
	CONSTRAINT tuition_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT tuition_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT tuition_program_year_id_university_id_admission_year_fkey FOREIGN KEY(program_year_id, university_id, admission_year) REFERENCES program_years (id, university_id, admission_year), 
	CONSTRAINT tuition_university_id_admission_year_fkey FOREIGN KEY(university_id, admission_year) REFERENCES admission_years (university_id, admission_year), 
	CONSTRAINT tuition_university_id_admission_year_program_year_id_policy_key UNIQUE NULLS NOT DISTINCT (university_id, admission_year, program_year_id, policy_key, revision)
);
```

```sql
CREATE UNIQUE INDEX one_current_tuition ON tuition (university_id, admission_year, program_year_id, policy_key) NULLS NOT DISTINCT WHERE is_current;
```

## universities

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_code | TEXT | False |  |
| name | TEXT | False |  |
| short_name | TEXT | True |  |
| normalized_name | TEXT | False |  |
| slug | TEXT | False |  |
| province_code | TEXT | True |  |
| university_type | TEXT | True |  |
| website | TEXT | True |  |
| verification_status | TEXT | False | 'unverified'::text |
| created_at | TIMESTAMP WITH TIME ZONE | False | now() |
| updated_at | TIMESTAMP WITH TIME ZONE | False | now() |

```sql
CREATE TABLE universities (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_code TEXT NOT NULL, 
	name TEXT NOT NULL, 
	short_name TEXT, 
	normalized_name TEXT NOT NULL, 
	slug TEXT NOT NULL, 
	province_code TEXT, 
	university_type TEXT, 
	website TEXT, 
	verification_status TEXT DEFAULT 'unverified'::text NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT universities_pkey PRIMARY KEY (id), 
	CONSTRAINT universities_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text])), 
	CONSTRAINT universities_slug_key UNIQUE (slug), 
	CONSTRAINT universities_university_code_key UNIQUE (university_code)
);
```

```sql
CREATE INDEX university_name_trgm ON universities USING gin (normalized_name gin_trgm_ops);
```

## university_aliases

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| id | UUID | False | gen_random_uuid() |
| university_id | UUID | False |  |
| alias | TEXT | False |  |
| normalized_alias | TEXT | False |  |
| alias_type | TEXT | False |  |
| valid_from | DATE | True |  |
| valid_to | DATE | True |  |
| evidence_url | TEXT | False |  |
| approved_by | TEXT | False |  |

```sql
CREATE TABLE university_aliases (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	university_id UUID NOT NULL, 
	alias TEXT NOT NULL, 
	normalized_alias TEXT NOT NULL, 
	alias_type TEXT NOT NULL, 
	valid_from DATE, 
	valid_to DATE, 
	evidence_url TEXT NOT NULL, 
	approved_by TEXT NOT NULL, 
	CONSTRAINT university_aliases_pkey PRIMARY KEY (id), 
	CONSTRAINT university_aliases_alias_type_check CHECK (alias_type = ANY (ARRAY['name'::text, 'short_name'::text, 'legacy_code'::text, 'domain'::text])), 
	CONSTRAINT university_aliases_check CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from), 
	CONSTRAINT university_aliases_university_id_fkey FOREIGN KEY(university_id) REFERENCES universities (id), 
	CONSTRAINT university_aliases_university_id_normalized_alias_alias_typ_key UNIQUE (university_id, normalized_alias, alias_type)
);
```

```sql
CREATE INDEX university_alias_trgm ON university_aliases USING gin (normalized_alias gin_trgm_ops);
```

## university_year_features

| Column | PostgreSQL type | Nullable | Default |
|---|---|---|---|
| university_id | UUID | False |  |
| admission_year | SMALLINT | False |  |
| feature_key | TEXT | False |  |
| feature_value | JSONB | False |  |
| verification_status | TEXT | False |  |
| primary_snapshot_id | UUID | False |  |

```sql
CREATE TABLE university_year_features (
	university_id UUID NOT NULL, 
	admission_year SMALLINT NOT NULL, 
	feature_key TEXT NOT NULL, 
	feature_value JSONB NOT NULL, 
	verification_status TEXT NOT NULL, 
	primary_snapshot_id UUID NOT NULL, 
	CONSTRAINT university_year_features_pkey PRIMARY KEY (university_id, admission_year, feature_key), 
	CONSTRAINT university_year_features_verification_status_check CHECK (verification_status = ANY (ARRAY['unverified'::text, 'verified'::text, 'disputed'::text, 'rejected'::text])), 
	CONSTRAINT university_year_features_primary_snapshot_id_fkey FOREIGN KEY(primary_snapshot_id) REFERENCES source_snapshots (id), 
	CONSTRAINT university_year_features_university_id_admission_year_fkey FOREIGN KEY(university_id, admission_year) REFERENCES admission_years (university_id, admission_year)
);
```

