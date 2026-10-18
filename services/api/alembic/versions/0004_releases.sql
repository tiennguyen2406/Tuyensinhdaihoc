CREATE FUNCTION eduradar_release_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'Immutable dataset release'; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles r WHERE r.rolname='eduradar_release_builder'
        AND pg_has_role(session_user,r.oid,'MEMBER'))
        OR EXISTS (SELECT FROM pg_roles WHERE rolname=session_user AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls))
        OR session_user=pg_get_userbyid((SELECT relowner FROM pg_class WHERE oid='dataset_releases'::regclass)) THEN
        RAISE EXCEPTION 'Dedicated release database capability required';
    END IF;
    IF NEW.version > (SELECT dataset_version FROM catalog_state)
        OR NEW.metadata->>'schema_version' IS DISTINCT FROM 'canonical-release/1'
        OR (NEW.metadata->>'catalog_version')::bigint IS DISTINCT FROM NEW.version
        OR (NEW.metadata->'counts'->>'canonical_cutoffs')::bigint IS DISTINCT FROM NEW.cutoff_count
        OR NOT EXISTS (SELECT FROM audit_events a WHERE a.entity_id=NEW.id AND a.action='register_release'
            AND a.actor_id='db:'||session_user
            AND a.after_data->>'transaction_id'=pg_current_xact_id()::text
            AND to_jsonb(jsonb_populate_record(NULL::dataset_releases,a.after_data->'row'))=to_jsonb(NEW)) THEN
        RAISE EXCEPTION 'Verified manifest and matching register audit required';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER dataset_release_guard BEFORE INSERT OR UPDATE OR DELETE ON dataset_releases
FOR EACH ROW EXECUTE FUNCTION eduradar_release_guard();

CREATE FUNCTION eduradar_refresh_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE release_row record;
BEGIN
    IF EXISTS (SELECT FROM pg_roles r WHERE r.rolname='eduradar_release_builder'
        AND pg_has_role(session_user,r.oid,'MEMBER'))
        AND NOT EXISTS (SELECT FROM pg_roles WHERE rolname=session_user AND rolsuper)
        AND OLD.job_type <> 'refresh_serving' THEN
        RAISE EXCEPTION 'Release runner cannot mutate other jobs';
    END IF;
    IF OLD.job_type <> 'refresh_serving' THEN
        IF TG_OP='DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
    END IF;
    IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Refresh history cannot be deleted'; END IF;
    IF (to_jsonb(OLD)-'payload'-'status'-'attempts'-'available_at'-'lease_until'-'worker_id'-'last_error')
       IS DISTINCT FROM (to_jsonb(NEW)-'payload'-'status'-'attempts'-'available_at'-'lease_until'-'worker_id'-'last_error')
       OR (OLD.payload-'release_lease_token'-'release_result') IS DISTINCT FROM (NEW.payload-'release_lease_token'-'release_result')
       OR OLD.status='succeeded' THEN
        RAISE EXCEPTION 'Immutable refresh identity/request/result';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles r WHERE r.rolname='eduradar_release_builder'
        AND pg_has_role(session_user,r.oid,'MEMBER')) OR NOT EXISTS (
        SELECT FROM audit_events a WHERE a.entity_id=NEW.id AND a.action='refresh_'||NEW.status
        AND a.actor_id='db:'||session_user AND to_jsonb(jsonb_populate_record(NULL::ingest_jobs,a.after_data->'row'))=to_jsonb(NEW)
        AND a.after_data->>'transaction_id'=pg_current_xact_id()::text) THEN
        RAISE EXCEPTION 'Release capability and matching refresh audit required';
    END IF;
    IF NEW.status='leased' THEN
        IF NOT (OLD.status IN ('queued','retry_wait') OR (OLD.status='leased' AND OLD.lease_until<=clock_timestamp()))
            OR NEW.attempts<>OLD.attempts+1 OR NEW.lease_until IS NULL OR NEW.lease_until<=clock_timestamp()
            OR NULLIF(NEW.payload->>'release_lease_token','') IS NULL
            OR NEW.payload ? 'release_result' THEN RAISE EXCEPTION 'Invalid refresh lease'; END IF;
    ELSIF NEW.status IN ('succeeded','retry_wait') THEN
        IF OLD.status<>'leased' OR OLD.lease_until IS NULL OR OLD.lease_until<=clock_timestamp()
            OR NEW.payload->>'release_lease_token' IS DISTINCT FROM OLD.payload->>'release_lease_token'
            OR NEW.attempts<>OLD.attempts OR NEW.lease_until IS NOT NULL THEN
            RAISE EXCEPTION 'Stale or invalid refresh lease completion';
        END IF;
        IF NEW.status='succeeded' THEN
            SELECT * INTO release_row FROM dataset_releases WHERE id=(NEW.payload->'release_result'->>'release_id')::uuid;
            IF NOT FOUND OR release_row.version IS DISTINCT FROM (NEW.payload->'release_result'->>'actual_version')::bigint
                OR release_row.version<(OLD.payload->>'dataset_version')::bigint
                OR (NEW.payload->'release_result'->>'requested_version')::bigint IS DISTINCT FROM (OLD.payload->>'dataset_version')::bigint
                OR NEW.payload->'release_result'->>'manifest_sha256' IS DISTINCT FROM release_row.manifest_sha256
                OR NEW.payload->'release_result'->>'outcome' IS DISTINCT FROM
                    (CASE WHEN release_row.version=(OLD.payload->>'dataset_version')::bigint THEN 'built' ELSE 'coalesced' END) THEN
                RAISE EXCEPTION 'Registered release binding required before refresh success';
            END IF;
        END IF;
    ELSE RAISE EXCEPTION 'Unsupported release refresh transition'; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER refresh_release_guard BEFORE UPDATE OR DELETE ON ingest_jobs
FOR EACH ROW EXECUTE FUNCTION eduradar_refresh_guard();
