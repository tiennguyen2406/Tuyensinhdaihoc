from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from services.api.db.models import (
    catalog_state,
    cutoff_scores,
    ingest_jobs,
    observations,
    source_snapshots,
    sources,
)
from services.crawler.raw import RawStorage
from services.data.parsers.contract import SnapshotRef
from services.data.parsers.jobs import ParserJobs
from tests.parsers.helpers import profile
from tests.parsers.test_html import HTML


def seed(engine, raw, data=HTML, mime="text/html"):
    digest, uri = raw.put(data)
    with engine.begin() as c:
        source = c.execute(
            sources.insert()
            .values(
                canonical_url=f"https://example.edu.vn/{uuid4()}",
                domain="example.edu.vn",
                publisher="SYNTHETIC TEST",
                source_type="university",
            )
            .returning(sources.c.id)
        ).scalar_one()
        row = (
            c.execute(
                source_snapshots.insert()
                .values(
                    source_id=source,
                    raw_hash=digest,
                    raw_uri=uri,
                    final_url="https://example.edu.vn/pilot",
                    media_type=mime,
                    byte_size=len(data),
                )
                .returning(source_snapshots)
            )
            .mappings()
            .one()
        )
    return SnapshotRef(
        snapshot_id=row["id"],
        **{
            k: row[k]
            for k in ["source_id", "raw_hash", "raw_uri", "final_url", "media_type", "byte_size"]
        },
    )


def test_durable_parse_replay_new_version_and_no_publisher(migrated_engine, tmp_path):
    raw = RawStorage(tmp_path)
    ref = seed(migrated_engine, raw)
    jobs = ParserJobs(migrated_engine, raw)
    job = jobs.enqueue(ref.snapshot_id, profile())
    with migrated_engine.connect() as c:
        before = c.execute(select(func.count()).select_from(cutoff_scores)).scalar_one()
        version = c.execute(select(catalog_state.c.dataset_version)).scalar_one()
    one = jobs.run(job)
    two = jobs.run(job)
    assert one["inserted"] == two["inserted"]
    assert two["cached"] is True
    assert jobs.enqueue(ref.snapshot_id, profile()) == job
    other = jobs.enqueue(ref.snapshot_id, profile(), revision="2")
    assert other != job and jobs.run(other)["inserted"] == one["inserted"]
    with migrated_engine.connect() as c:
        assert (
            c.execute(
                select(func.count())
                .select_from(observations)
                .where(observations.c.snapshot_id == ref.snapshot_id)
            ).scalar_one()
            == 2 * one["inserted"]
        )
        assert c.execute(select(func.count()).select_from(cutoff_scores)).scalar_one() == before
        assert c.execute(select(catalog_state.c.dataset_version)).scalar_one() == version


def test_frozen_configuration_change_requires_new_revision(migrated_engine, tmp_path):
    raw = RawStorage(tmp_path)
    ref = seed(migrated_engine, raw)
    jobs = ParserJobs(migrated_engine, raw)
    jobs.enqueue(ref.snapshot_id, profile())
    p = profile().model_copy(update={"access_basis": "CHANGED REVIEW"})
    with pytest.raises(ValueError, match="revision"):
        jobs.enqueue(ref.snapshot_id, p)


def test_scan_job_quarantined_no_facts_and_expired_lease_recovers(migrated_engine, tmp_path):
    from tests.parsers.test_pdf import document

    raw = RawStorage(tmp_path)
    ref = seed(migrated_engine, raw, document(scan=True), "application/pdf")
    jobs = ParserJobs(migrated_engine, raw)
    job = jobs.enqueue(ref.snapshot_id, profile())
    with migrated_engine.begin() as c:
        c.execute(
            ingest_jobs.update()
            .where(ingest_jobs.c.id == job)
            .values(
                status="leased", worker_id="dead", lease_until=text("now()-interval '1 second'")
            )
        )
    report = jobs.run(job)
    assert report["status"] == "quarantined" and report["inserted"] == 0
    assert "ocr_required" in report["issues"]


def test_cli_replay_handles_vietnamese_on_legacy_windows_pipe(
    migrated_engine, tmp_path, test_environment
):
    import json
    import subprocess
    import sys

    raw = RawStorage(tmp_path / "raw")
    ref = seed(migrated_engine, raw)
    config = tmp_path / "profile.json"
    config.write_text(profile().model_dump_json(), encoding="utf-8")
    env = test_environment | {"CRAWLER_RAW_DIR": str(raw.root), "PYTHONIOENCODING": "cp1252"}
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "services.data.parsers",
            "replay",
            str(ref.snapshot_id),
            "--profile",
            str(config),
        ],
        env=env,
        capture_output=True,
        timeout=10,
    )
    assert run.returncode == 0, run.stderr.decode(errors="replace")
    parsed = json.loads(run.stdout.decode("utf-8"))
    assert "2026" in parsed["metadata"]["document_title"]
    assert parsed["persisted"] is False


def test_busy_and_stale_parse_workers_cannot_write(migrated_engine, tmp_path, monkeypatch):
    import services.data.parsers.jobs as module
    from services.data.parsers.contract import ParseResult

    raw = RawStorage(tmp_path)
    ref = seed(migrated_engine, raw)
    jobs = ParserJobs(migrated_engine, raw)
    job = jobs.enqueue(ref.snapshot_id, profile())
    with migrated_engine.begin() as c:
        c.execute(
            ingest_jobs.update()
            .where(ingest_jobs.c.id == job)
            .values(status="leased", lease_until=text("now()+interval '5 minutes'"))
        )
    assert jobs.run(job)["status"] == "busy"
    with migrated_engine.begin() as c:
        c.execute(ingest_jobs.update().where(ingest_jobs.c.id == job).values(status="queued"))

    def steal(*args, **kwargs):
        with migrated_engine.begin() as c:
            row = c.execute(
                select(ingest_jobs.c.payload).where(ingest_jobs.c.id == job)
            ).scalar_one()
            c.execute(
                ingest_jobs.update()
                .where(ingest_jobs.c.id == job)
                .values(payload=row | {"lease_token": "new-worker"})
            )
        return ParseResult()

    monkeypatch.setattr(module, "replay", steal)
    with pytest.raises(ValueError, match="lease"):
        jobs.run(job)
    with migrated_engine.connect() as c:
        assert (
            c.execute(
                select(func.count())
                .select_from(observations)
                .where(observations.c.snapshot_id == ref.snapshot_id)
            ).scalar_one()
            == 0
        )


def test_job_rejects_output_for_another_snapshot(migrated_engine, tmp_path, monkeypatch):
    import services.data.parsers.jobs as module
    from tests.parsers.test_persistence import result

    raw = RawStorage(tmp_path)
    ref = seed(migrated_engine, raw)
    other = seed(migrated_engine, raw)
    jobs = ParserJobs(migrated_engine, raw)
    job = jobs.enqueue(ref.snapshot_id, profile())
    monkeypatch.setattr(
        module,
        "replay",
        lambda *a, **k: result({"id": other.snapshot_id, "source_id": other.source_id}),
    )
    with pytest.raises(ValueError, match="contract"):
        jobs.run(job)
