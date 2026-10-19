-- Database boundary: publisher capability cannot manufacture reviewer decisions.
CREATE FUNCTION eduradar_review_insert_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.job_type IN ('review_decision','registry_version') THEN
        IF NOT EXISTS (SELECT FROM pg_roles r WHERE r.rolname='eduradar_reviewer'
            AND pg_has_role(session_user,r.oid,'MEMBER')) THEN
            RAISE EXCEPTION 'Reviewer database capability required for decisions/registry';
        END IF;
        IF NEW.job_type='review_decision' AND (
            NEW.payload->>'actor_id' IS DISTINCT FROM 'db:'||session_user
            OR NOT EXISTS (SELECT FROM audit_events a WHERE a.entity_id=NEW.id
                AND a.actor_id='db:'||session_user AND a.action='review_'||(NEW.payload->'command'->>'action')
                AND a.after_data=NEW.payload)) THEN
            RAISE EXCEPTION 'Authenticated matching review audit required';
        END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER review_insert_guard BEFORE INSERT ON ingest_jobs
FOR EACH ROW EXECUTE FUNCTION eduradar_review_insert_guard();

-- Additive policy. Legacy rows are not rewritten or blessed as T08-reviewed records.
CREATE FUNCTION eduradar_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Append-only audit/review history';
END $$;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION eduradar_append_only();

CREATE FUNCTION eduradar_job_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.job_type IN ('review_decision','registry_version','publication_request') THEN
        RAISE EXCEPTION 'Immutable reviewed manifest; append a new decision/version';
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER reviewed_jobs_immutable BEFORE UPDATE OR DELETE ON ingest_jobs
FOR EACH ROW EXECUTE FUNCTION eduradar_job_immutable();

CREATE FUNCTION eduradar_cutoff_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE required_action text;
BEGIN
    IF TG_OP='INSERT' THEN
        IF NOT starts_with(NEW.publication_group_key,'publication/1:') THEN
            IF EXISTS(SELECT FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN RETURN NEW; END IF;
            RAISE EXCEPTION 'Ordinary writer cannot bypass reviewed publication via legacy marker';
        END IF;
        IF NOT EXISTS (SELECT FROM audit_events a WHERE a.entity_id=NEW.id AND a.action='publish_cutoff'
            AND a.actor_id='db:'||session_user AND a.after_data->>'transaction_id'=pg_current_xact_id()::text
            AND a.after_data->'row'->'fact_payload'=NEW.fact_payload
            AND (a.after_data->'row'->>'score')::numeric=NEW.score
            AND EXISTS (SELECT FROM ingest_jobs j JOIN program_admissions pa ON pa.id=NEW.program_admission_id
                WHERE j.id::text=a.request_id AND j.job_type='review_decision' AND j.status='succeeded'
                AND j.payload->'command'->>'action'='publish'
                AND j.payload->'validated_payload'=NEW.fact_payload
                AND (j.payload->>'validated_snapshot')::uuid=NEW.primary_snapshot_id
                AND (j.payload->'validated_payload'->>'score')::numeric=NEW.score
                AND (j.payload->'validated_payload'->>'max_score')::numeric=NEW.max_score
                AND (j.payload->'validated_payload'->>'scale_id')::uuid=NEW.score_scale_id
                AND to_jsonb(pa) @> ((j.payload->'validated_scope')-'primary_snapshot_id')
                AND NEW.is_current AND NEW.verification_status='verified'
                AND NOT EXISTS(SELECT FROM ingest_jobs rev WHERE rev.job_type='review_decision'
                    AND rev.payload->'command'->>'action'='revoke'
                    AND rev.payload->'command'->>'revokes_decision_id'=j.id::text))) THEN
            RAISE EXCEPTION 'Audited publication insert required';
        END IF;
        RETURN NEW;
    END IF;
    IF NOT starts_with(OLD.publication_group_key,'publication/1:') THEN
        IF TG_OP='DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
    END IF;
    IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Canonical publication history cannot be deleted'; END IF;
    IF to_jsonb(OLD)=to_jsonb(NEW) THEN RETURN NEW; END IF;
    IF OLD.is_current AND NOT NEW.is_current AND NEW.system_valid_to IS NOT NULL
        AND (to_jsonb(OLD)-'is_current'-'system_valid_to')=(to_jsonb(NEW)-'is_current'-'system_valid_to') THEN
        required_action='retire_cutoff';
    ELSIF OLD.is_current AND NEW.verification_status='disputed'
        AND (to_jsonb(OLD)-'verification_status')=(to_jsonb(NEW)-'verification_status') THEN
        required_action='dispute_cutoff';
    ELSE RAISE EXCEPTION 'Immutable cutoff payload; only audited retire/dispute permitted'; END IF;
    IF NOT EXISTS (SELECT FROM audit_events a WHERE a.entity_id=OLD.id AND a.action=required_action
        AND a.actor_id='db:'||session_user AND a.after_data->>'transaction_id'=pg_current_xact_id()::text) THEN
        RAISE EXCEPTION 'Audited transition in same transaction required';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER publication_cutoff_guard BEFORE INSERT OR UPDATE OR DELETE ON cutoff_scores
FOR EACH ROW EXECUTE FUNCTION eduradar_cutoff_guard();

CREATE FUNCTION eduradar_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target uuid; required_action text;
BEGIN
    IF TG_OP='INSERT' THEN
        IF NEW.condition_dsl->>'schema_version' IS DISTINCT FROM 'publication-scope/1' THEN
            IF EXISTS(SELECT FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN RETURN NEW; END IF;
            RAISE EXCEPTION 'Ordinary writer requires reviewed scope schema';
        END IF;
        target=NEW.id;required_action='create_scope';
    ELSE
        IF OLD.condition_dsl->>'schema_version' IS DISTINCT FROM 'publication-scope/1' THEN
            IF TG_OP='DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END IF;
        IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Scope history cannot be deleted'; END IF;
        IF NEW.data_status!='withdrawn' OR (to_jsonb(OLD)-'data_status')!=(to_jsonb(NEW)-'data_status') THEN
            RAISE EXCEPTION 'Scope basis is immutable; create replacement';
        END IF;
        target=OLD.id;required_action='withdraw_scope';
    END IF;
    IF NOT EXISTS (SELECT FROM audit_events a WHERE a.entity_id=target AND a.action=required_action
        AND a.actor_id='db:'||session_user AND a.after_data->>'transaction_id'=pg_current_xact_id()::text) THEN
        RAISE EXCEPTION 'Audited scope transaction required';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER publication_scope_guard BEFORE INSERT OR UPDATE OR DELETE ON program_admissions
FOR EACH ROW EXECUTE FUNCTION eduradar_scope_guard();

CREATE FUNCTION eduradar_reviewed_entity_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT FROM audit_events a WHERE a.entity_id=OLD.id AND a.entity_kind=TG_ARGV[0]
        AND a.action IN ('bootstrap_create','bootstrap_link')) THEN
        RAISE EXCEPTION 'Reviewed entity/basis immutable; use versioned replacement';
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER reviewed_scale_guard BEFORE UPDATE OR DELETE ON score_scales
FOR EACH ROW EXECUTE FUNCTION eduradar_reviewed_entity_guard('scale');
CREATE TRIGGER reviewed_offering_guard BEFORE UPDATE OR DELETE ON program_years
FOR EACH ROW EXECUTE FUNCTION eduradar_reviewed_entity_guard('offering');
CREATE TRIGGER reviewed_program_guard BEFORE UPDATE OR DELETE ON programs
FOR EACH ROW EXECUTE FUNCTION eduradar_reviewed_entity_guard('program');

CREATE FUNCTION eduradar_validated_observation_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF starts_with(OLD.transform_version,'validated/1;') THEN RAISE EXCEPTION 'Validated evidence is immutable'; END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER validated_observation_guard BEFORE UPDATE OR DELETE ON observations
FOR EACH ROW EXECUTE FUNCTION eduradar_validated_observation_guard();
