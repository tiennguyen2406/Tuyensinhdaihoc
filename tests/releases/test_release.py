import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import sqlalchemy as sa

from services.api.db.models import metadata
from tests.fixtures import make_scope


def manifest_path(result):
    from urllib.request import url2pathname

    return Path(url2pathname(urlsplit(result["manifest_uri"]).path))


def test_snapshot_count_fidelity_and_frozen_coverage(release_db, tmp_path):
    from services.data.releases.builder import build, verify

    admin, runner, reader, f = release_db
    with admin.begin() as c:
        c.execute(metadata.tables["programs"].update().values(program_name="Ngành thử nghiệm Đ"))
        c.execute(
            metadata.tables["program_admissions"]
            .update()
            .values(
                condition_dsl={
                    "combination_status": "source_aggregate",
                    "conditions": {"operator": "lte", "value": 13},
                }
            )
        )
        c.execute(
            metadata.tables["cutoff_scores"]
            .insert()
            .values(**(f["cutoff_values"] | {"revision": 2, "is_current": False}))
        )
    result = build(runner, tmp_path)
    path = manifest_path(result)
    manifest = json.loads(path.read_bytes())
    data = json.loads((path.parent / "cutoffs.json").read_bytes())
    coverage = json.loads((path.parent / "coverage.json").read_bytes())
    assert manifest["counts"]["canonical_cutoffs"] == result["cutoff_count"] == 1
    assert len({r["cutoff"]["id"] for r in data["records"]}) == 1
    record = data["records"][0]
    assert record["cutoff"]["score"] == "24.12345"
    assert record["program"]["program_name"] == "Ngành thử nghiệm Đ"
    assert record["program"]["major_id"] is None
    assert record["unknown"]["track"] is None
    assert record["computation_status"] == "unavailable_aggregate_scope"
    assert record["scope"]["condition_dsl"]["conditions"] == {"operator": "lte", "value": 13}
    assert record["lineage"]["observations"][0]["parser_provenance"] == {
        "implementation_sha256": "a" * 64,
        "profile_sha256": "b" * 64,
        "lock_sha256": "c" * 64,
    }
    assert coverage["evidence_count"] == 2
    assert coverage["canonical_cutoffs"] == coverage["revisions"] == 1
    assert coverage["years_without_verified_data"] == [2024, 2025]
    assert "raw_fields" not in (path.parent / "cutoffs.json").read_text(encoding="utf-8")
    with admin.begin() as c:
        c.execute(metadata.tables["programs"].update().values(program_name="Changed after release"))
        c.execute(metadata.tables["program_admissions"].update().values(data_status="withdrawn"))
    with reader.begin() as c:
        assert verify(c, 3)["coverage"] == coverage


def test_combination_subjects_export_by_code_in_position_order(release_db, tmp_path):
    from services.data.releases.builder import build, verify

    admin, runner, reader, f = release_db
    with admin.begin() as c:
        combinations = metadata.tables["combinations"]
        combination_id = c.execute(
            combinations.insert()
            .values(code="TEST-A00", name="TEST ONLY A00")
            .returning(combinations.c.id)
        ).scalar_one()
        # Insertion order and lexical code order both differ from subject position.
        for code, name, position in [
            ("CHEM", "Hóa học thử nghiệm", 3),
            ("MATH", "Toán thử nghiệm", 1),
            ("PHYS", "Vật lý thử nghiệm", 2),
        ]:
            c.execute(metadata.tables["subjects"].insert().values(code=code, name=name))
            c.execute(
                metadata.tables["combination_subjects"]
                .insert()
                .values(combination_id=combination_id, subject_code=code, position=position)
            )
        c.execute(
            metadata.tables["program_admissions"]
            .update()
            .where(metadata.tables["program_admissions"].c.id == f["scope"])
            .values(combination_id=combination_id)
        )
    result = build(runner, tmp_path)
    path = manifest_path(result)
    before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
    payload = json.loads(before["cutoffs.json"])
    manifest = json.loads(before["manifest.json"])
    coverage = json.loads(before["coverage.json"])
    assert result["cutoff_count"] == manifest["counts"]["canonical_cutoffs"] == 1
    assert coverage["canonical_cutoffs"] == len(payload["records"]) == 1
    record = payload["records"][0]
    assert record["combination"]["code"] == "TEST-A00"
    assert [
        (s["subject_code"], s["subject"]["code"], s["subject"]["name"], s["position"])
        for s in record["combination_subjects"]
    ] == [
        ("MATH", "MATH", "Toán thử nghiệm", 1),
        ("PHYS", "PHYS", "Vật lý thử nghiệm", 2),
        ("CHEM", "CHEM", "Hóa học thử nghiệm", 3),
    ]
    with reader.begin() as c:
        assert verify(c, 3)["verified"]
    replay = build(runner, tmp_path, version=3)
    assert replay["cached"] and replay["release_id"] == result["release_id"]
    assert replay["cutoff_count"] == 1
    assert {p.name: p.read_bytes() for p in path.parent.iterdir()} == before


def test_supported_contract_accepts_older_builder_provenance(release_db, tmp_path, monkeypatch):
    from services.data.releases import artifacts
    from services.data.releases.builder import build, verify

    admin, runner, reader, _ = release_db
    result = build(runner, tmp_path)
    path = manifest_path(result)
    before = path.read_bytes()
    old_manifest = json.loads(before)
    with admin.connect() as c:
        audit_count = c.scalar(sa.text("SELECT count(*) FROM audit_events"))
    # Simulate upgrading the implementation while retaining the supported wire contract.
    monkeypatch.setattr(artifacts, "BUILDER", "release-builder/1.1.0")
    bundle = artifacts.verify_bundle(path, result["manifest_sha256"])
    assert bundle["manifest"] == old_manifest
    assert bundle["manifest"]["builder_version"] == "release-builder/1.0.0"
    with reader.begin() as c:
        assert verify(c, 3)["verified"]
    replay = build(runner, tmp_path, version=3)
    assert replay["cached"] and replay["release_id"] == result["release_id"]
    assert replay["manifest_sha256"] == result["manifest_sha256"]
    assert path.read_bytes() == before
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM audit_events")) == audit_count
        assert c.scalar(sa.text("SELECT count(*) FROM dataset_releases")) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [("schema_version", "canonical-release/999"), ("filters", {"years": [2026]})],
)
def test_unsupported_bundle_contract_is_rejected(release_db, tmp_path, field, value):
    from services.data.releases.artifacts import encode, sha, verify_bundle
    from services.data.releases.builder import build

    _, runner, _, _ = release_db
    result = build(runner, tmp_path)
    path = manifest_path(result)
    manifest = json.loads(path.read_bytes())
    manifest[field] = value
    raw = encode(manifest)
    path.write_bytes(raw)
    # The checksum is correct: rejection must be based on the unsupported contract.
    with pytest.raises(ValueError, match="unsupported manifest contract"):
        verify_bundle(path, sha(raw))


@pytest.mark.parametrize("excluded", ["unverified", "noncurrent", "withdrawn", "year"])
def test_excludes_noncanonical_inputs(release_db, tmp_path, excluded):
    from services.data.releases.builder import build

    admin, runner, _, f = release_db
    with admin.begin() as c:
        t = metadata.tables
        if excluded == "unverified":
            c.execute(
                t["cutoff_scores"]
                .update()
                .values(is_current=False, verification_status="unverified")
            )
        elif excluded == "noncurrent":
            c.execute(t["cutoff_scores"].update().values(is_current=False))
        elif excluded == "withdrawn":
            c.execute(t["program_admissions"].update().values(data_status="withdrawn"))
        else:
            c.execute(
                t["admission_years"]
                .insert()
                .values(university_id=f["university"], admission_year=2023, status="verified")
            )
            c.execute(t["program_years"].update().values(admission_year=2023))
    assert build(runner, tmp_path)["cutoff_count"] == 0


def test_repeatable_read_never_mixes_version_and_publication(release_db):
    from services.data.releases.snapshot import capture

    admin, runner, _, _ = release_db
    with runner.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
        c.exec_driver_sql("SET TRANSACTION READ ONLY")
        assert c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == 3
        with admin.begin() as writer:
            make_scope(writer)
            writer.execute(metadata.tables["catalog_state"].update().values(dataset_version=4))
        frozen = capture(c)
        assert frozen["catalog_version"] == 3
        assert frozen["coverage"]["canonical_cutoffs"] == len(frozen["records"]) == 1


def test_workers_replay_and_coalescing_are_idempotent(release_db, tmp_path):
    from services.data.releases.builder import build

    admin, runner, _, _ = release_db
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: build(runner, tmp_path), range(2)))
    assert results[0]["release_id"] == results[1]["release_id"]
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM dataset_releases")) == 1
        audits = c.scalar(sa.text("SELECT count(*) FROM audit_events"))
        jobs = (
            c.execute(sa.text("SELECT status,payload FROM ingest_jobs ORDER BY idempotency_key"))
            .mappings()
            .all()
        )
        assert [j["payload"]["dataset_version"] for j in jobs] == [1, 2, 3]
        assert [j["payload"]["release_result"]["outcome"] for j in jobs] == [
            "coalesced",
            "coalesced",
            "built",
        ]
        assert all(
            j["status"] == "succeeded" and j["payload"]["release_result"]["actual_version"] == 3
            for j in jobs
        )
    assert build(runner, tmp_path, version=3)["cached"]
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM audit_events")) == audits
        assert c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == 3
        assert c.scalar(sa.text("SELECT count(*) FROM ingest_jobs")) == 3
    assert len(list(tmp_path.glob("version-*"))) == 1


@pytest.mark.parametrize("damage", ["missing", "checksum", "manifest"])
def test_registered_damage_is_integrity_conflict(release_db, tmp_path, damage):
    from services.data.releases.builder import build, verify

    _, runner, reader, _ = release_db
    result = build(runner, tmp_path)
    path = manifest_path(result)
    target = path if damage == "manifest" else path.parent / "cutoffs.json"
    if damage == "missing":
        target.unlink()
    else:
        target.write_bytes(b"corrupt")
    with reader.begin() as c, pytest.raises(ValueError, match="[Ii]ntegrity"):
        verify(c, 3)
    with pytest.raises(ValueError, match="[Ii]ntegrity"):
        build(runner, tmp_path)


@pytest.mark.parametrize("failure", ["writing", "registration", "finalization"])
def test_crash_retry_preserves_completed_artifacts(release_db, tmp_path, monkeypatch, failure):
    from services.data.releases import artifacts
    from services.data.releases.builder import build

    admin, runner, _, _ = release_db
    if failure == "writing":
        original = artifacts.write_file
        calls = 0

        def broken(path, data):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("TEST ONLY interrupted write")
            return original(path, data)

        monkeypatch.setattr(artifacts, "write_file", broken)
    else:
        table = "dataset_releases" if failure == "registration" else "ingest_jobs"
        when = "INSERT" if failure == "registration" else "UPDATE"
        with admin.begin() as c:
            c.exec_driver_sql(
                "CREATE FUNCTION fail_release_test() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF TG_OP='INSERT' OR NEW.status='succeeded' THEN RAISE EXCEPTION 'TEST ONLY failure'; END IF; RETURN NEW; END $$"
            )
            c.exec_driver_sql(
                f"CREATE TRIGGER fail_release_test BEFORE {when} ON {table} FOR EACH ROW EXECUTE FUNCTION fail_release_test()"
            )
    with pytest.raises((OSError, sa.exc.DBAPIError)):
        build(runner, tmp_path)
    completed = list(tmp_path.glob("version-*/manifest.json"))
    before = completed[0].read_bytes() if completed else None
    with admin.begin() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM dataset_releases")) == 0
        assert c.scalar(sa.text("SELECT count(*) FROM ingest_jobs WHERE status='succeeded'")) == 0
        if failure != "writing":
            c.exec_driver_sql(f"DROP TRIGGER fail_release_test ON {table}")
    monkeypatch.undo()
    result = build(runner, tmp_path)
    if before:
        assert manifest_path(result).read_bytes() == before
    else:
        assert list(tmp_path.glob("staging-*"))  # Partial attempt retained, never blessed.


def test_reader_owner_and_direct_mutations_are_blocked(release_db, tmp_path):
    from services.data.releases.builder import build

    admin, runner, reader, _ = release_db
    for e in [reader, admin]:
        with pytest.raises(PermissionError):
            build(e, tmp_path)
    result = build(runner, tmp_path)
    for e in [runner, reader]:
        for sql in [
            "UPDATE dataset_releases SET cutoff_count=0",
            "DELETE FROM dataset_releases",
            "UPDATE ingest_jobs SET payload='{}'::jsonb",
        ]:
            with e.begin() as c, pytest.raises(sa.exc.DBAPIError):
                c.exec_driver_sql(sql)
    assert result["version"] == 3


def test_build_publication_race_keeps_snapshot_version(release_db, tmp_path, monkeypatch):
    from services.data.publication.publish import advance_serving
    from services.data.releases import builder

    admin, runner, _, _ = release_db
    original = builder.capture

    def concurrent_publication(c):
        assert c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == 3
        with admin.begin() as writer:
            make_scope(writer)
            advance_serving(writer)
        return original(c)

    monkeypatch.setattr(builder, "capture", concurrent_publication)
    result = builder.build(runner, tmp_path)
    assert result["version"] == 3 and result["cutoff_count"] == 1
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == 4
        assert (
            c.scalar(
                sa.text("SELECT status FROM ingest_jobs WHERE idempotency_key='refresh_serving:4'")
            )
            == "queued"
        )


def test_expired_lease_fencing_and_recovery(release_db, tmp_path):
    from services.data.releases.builder import build, claim, finalize
    from services.data.releases.roles import require

    admin, runner, _, _ = release_db
    with runner.begin() as c:
        actor = require(c)
        leases = claim(c, actor, 3)
    # TEST ONLY simulate elapsed time without sleeping five minutes.
    with admin.begin() as c:
        c.exec_driver_sql("ALTER TABLE ingest_jobs DISABLE TRIGGER refresh_release_guard")
        c.exec_driver_sql("UPDATE ingest_jobs SET lease_until=now()-interval '1 second'")
        c.exec_driver_sql("ALTER TABLE ingest_jobs ENABLE TRIGGER refresh_release_guard")
    with runner.begin() as c, pytest.raises(ValueError, match="lease lost"):
        finalize(c, actor, leases, {})
    result = build(runner, tmp_path)
    assert result["version"] == 3
    with admin.connect() as c:
        assert set(c.scalars(sa.text("SELECT attempts FROM ingest_jobs"))) == {2}


def test_completed_orphan_recovery_after_catalog_advances(release_db, tmp_path, monkeypatch):
    from services.data.publication.publish import advance_serving
    from services.data.releases import builder

    admin, runner, _, _ = release_db
    original = builder.register

    def crash(*args):
        raise RuntimeError("TEST ONLY process failure after files")

    monkeypatch.setattr(builder, "register", crash)
    with pytest.raises(RuntimeError):
        builder.build(runner, tmp_path)
    before = (tmp_path / "version-3" / "manifest.json").read_bytes()
    with admin.begin() as c:
        make_scope(c)
        advance_serving(c)
    monkeypatch.setattr(builder, "register", original)
    result = builder.build(runner, tmp_path, version=3)
    assert result["version"] == 3 and result["cutoff_count"] == 1
    assert manifest_path(result).read_bytes() == before
    with pytest.raises(ValueError, match="[Ii]ntegrity"):
        builder.build(runner, tmp_path, version=2)


def test_runner_cannot_update_other_jobs_or_forge_registration(release_db, tmp_path):
    from uuid import uuid4

    admin, runner, _, _ = release_db
    with admin.begin() as c:
        c.execute(
            metadata.tables["ingest_jobs"]
            .insert()
            .values(
                id=uuid4(),
                job_type="TEST ONLY unrelated",
                idempotency_key="unrelated",
                status="queued",
                payload={},
            )
        )
    with runner.begin() as c, pytest.raises(sa.exc.DBAPIError):
        c.exec_driver_sql(
            "UPDATE ingest_jobs SET status='succeeded' WHERE idempotency_key='unrelated'"
        )
    with runner.begin() as c, pytest.raises(sa.exc.DBAPIError):
        c.execute(
            metadata.tables["dataset_releases"]
            .insert()
            .values(
                version=3,
                cutoff_count=1,
                manifest_uri="file:///TEST-ONLY",
                manifest_sha256="a" * 64,
                metadata={},
            )
        )


def test_registered_release_recovers_jobs_after_prior_worker_dies(release_db, tmp_path):
    from services.data.releases.builder import build, claim
    from services.data.releases.roles import require

    admin, runner, _, _ = release_db
    with runner.begin() as c:
        claim(c, require(c), 3)  # Simulate process death after durable claim.
    first = build(runner, tmp_path)
    with admin.begin() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM ingest_jobs WHERE status='leased'")) == 3
        c.exec_driver_sql("ALTER TABLE ingest_jobs DISABLE TRIGGER refresh_release_guard")
        c.exec_driver_sql("UPDATE ingest_jobs SET lease_until=now()-interval '1 second'")
        c.exec_driver_sql("ALTER TABLE ingest_jobs ENABLE TRIGGER refresh_release_guard")
    second = build(runner, tmp_path)
    assert second["release_id"] == first["release_id"] and second["cached"]
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM ingest_jobs WHERE status='succeeded'")) == 3


def test_database_rejects_audited_null_lease(release_db):
    from services.data.releases.builder import transition
    from services.data.releases.roles import require

    _, runner, _, _ = release_db
    with runner.begin() as c, pytest.raises(sa.exc.DBAPIError):
        row = dict(c.execute(sa.select(metadata.tables["ingest_jobs"]).limit(1)).mappings().one())
        transition(
            c,
            require(c),
            row,
            dict(
                status="leased",
                attempts=1,
                lease_until=None,
                payload=row["payload"] | {"release_lease_token": "TEST ONLY"},
            ),
        )


def test_owner_crawler_job_updates_are_unaffected(release_db):
    admin, _, _, _ = release_db
    with admin.begin() as c:
        job = metadata.tables["ingest_jobs"]
        ident = c.execute(
            job.insert()
            .values(
                job_type="TEST ONLY crawler", idempotency_key="crawler", status="queued", payload={}
            )
            .returning(job.c.id)
        ).scalar_one()
        c.execute(job.update().where(job.c.id == ident).values(status="leased"))
        assert c.execute(job.delete().where(job.c.id == ident)).rowcount == 1


def test_database_requires_actual_release_version_in_success(release_db, tmp_path):
    from services.data.releases.artifacts import store
    from services.data.releases.builder import claim, register, transition
    from services.data.releases.roles import require
    from services.data.releases.snapshot import capture

    _, runner, _, _ = release_db
    with runner.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
        c.exec_driver_sql("SET TRANSACTION READ ONLY")
        bundle = store(tmp_path, capture(c))
    with runner.begin() as c:
        actor = require(c)
        claim(c, actor, 3)
        result = register(c, actor, bundle)
    with runner.begin() as c, pytest.raises(sa.exc.DBAPIError):
        row = dict(
            c.execute(
                sa.select(metadata.tables["ingest_jobs"]).where(
                    metadata.tables["ingest_jobs"].c.idempotency_key == "refresh_serving:3"
                )
            )
            .mappings()
            .one()
        )
        payload = row["payload"] | {
            "release_result": {
                "requested_version": 3,
                "release_id": result["release_id"],
                "manifest_sha256": result["manifest_sha256"],
                "outcome": "built",
            }
        }
        transition(c, actor, row, dict(status="succeeded", lease_until=None, payload=payload))


def test_cli_plan_build_verify_replay_and_reader_denial(release_db, tmp_path):
    import os
    import subprocess
    import sys

    admin, runner, reader, _ = release_db
    env = os.environ.copy() | {
        "POSTGRES_DB": admin.url.database,
        "RELEASE_DB_USER": runner.url.username,
        "RELEASE_DB_PASSWORD": runner.url.password,
    }

    def run(*args):
        return subprocess.run(
            [sys.executable, "-m", "services.data.releases", *args],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )

    result = run("plan")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["read_only"]
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM dataset_releases")) == 0
        assert c.scalar(sa.text("SELECT count(*) FROM audit_events")) == 1  # provision only
    result = run("build", "--root", str(tmp_path / "Đ Unicode %25"))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["cutoff_count"] == 1
    with admin.connect() as c:
        audit_count = c.scalar(sa.text("SELECT count(*) FROM audit_events"))
    env |= {"RELEASE_DB_USER": reader.url.username, "RELEASE_DB_PASSWORD": reader.url.password}
    for command in ["verify", "replay", "inspect"]:
        result = run(command, "--version", "3")
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["verified"]
    assert run("build").returncode == 2
    with admin.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM audit_events")) == audit_count
