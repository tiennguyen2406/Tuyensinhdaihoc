from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path

import pytest
import sqlalchemy as sa

from services.api.db.models import ingest_jobs, metadata, observations
from services.data.normalization.store import NormalizationStore
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.store import ResolutionStore
from tests.normalization.test_store import seed


def t06(db):
    identifier = seed(db)
    job = NormalizationStore(db).run([identifier])
    return job["job_id"]


def base():
    return EntityRegistry.load(Path("config/entities/ptit-v1.json"))


def test_frozen_input_job_namespace_idempotence_and_unchanged_old_data(db):
    job = t06(db)
    store = ResolutionStore(db)
    before = [
        dict(r) for r in db.execute(sa.select(observations).order_by(observations.c.id)).mappings()
    ]
    oldjobs = [
        dict(r) for r in db.execute(sa.select(ingest_jobs).order_by(ingest_jobs.c.id)).mappings()
    ]
    preview = store.preview(job, base())
    assert preview["summary"]["input_envelopes"] == 1 and preview["summary"]["candidates"] == 1
    first = store.run(job, base())
    again = store.replay(first["job_id"])
    assert first["inserted"] == 1 and again["inserted"] == 0 and again["cached"]
    assert first["job_id"] == again["job_id"]
    for old in before:
        assert (
            dict(
                db.execute(sa.select(observations).where(observations.c.id == old["id"]))
                .mappings()
                .one()
            )
            == old
        )
    for old in oldjobs:
        assert (
            dict(
                db.execute(sa.select(ingest_jobs).where(ingest_jobs.c.id == old["id"]))
                .mappings()
                .one()
            )
            == old
        )
    row = (
        db.execute(
            sa.select(observations).where(
                observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1",
                observations.c.normalized_fields["input_envelope_id"].astext
                == str(store.inputs(job)[1][0]["id"]),
            )
        )
        .mappings()
        .one()
    )
    assert row["verification_status"] == "unverified"
    assert row["normalized_fields"]["candidates"][0]["publication_eligible"] is False


def test_alias_registry_config_versions_frozen_and_new_version_keeps_history(db):
    job = t06(db)
    store = ResolutionStore(db)
    first = store.run(job, base())
    changed = base().model_copy(deep=True)
    changed.aliases[0].review.evidence.append("fixture://changed")
    with pytest.raises(ValueError, match="version"), db.begin_nested():
        store.run(job, changed)
    newer = changed.model_copy(
        update={"version": "registry/ptit-pilot/2", "alias_version": "aliases/ptit-pilot/2"}
    )
    second = store.run(job, newer)
    assert second["inserted"] == 1 and second["job_id"] != first["job_id"]
    assert store.replay(first["job_id"])["cached"]


def test_input_tampering_raw_output_and_wrong_job_types_rejected(db):
    job = t06(db)
    store = ResolutionStore(db)
    first = store.run(job, base())
    with pytest.raises(ValueError, match="normalization"), db.begin_nested():
        store.run(first["job_id"], base())
    env = store.inputs(job)[1][0]
    changed = deepcopy(env["normalized_fields"])
    changed["candidates"][0]["admission_year"] = 2026
    with pytest.raises(ValueError, match="payload|lineage|input"), db.begin_nested():
        db.execute(
            observations.update()
            .where(observations.c.id == env["id"])
            .values(normalized_fields=changed)
        )
        store.replay(first["job_id"])
    with pytest.raises(ValueError, match="payload"), db.begin_nested():
        db.execute(
            observations.update()
            .where(
                observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1"
            )
            .values(payload_hash="f" * 64)
        )
        store.replay(first["job_id"])


def test_pending_registry_does_not_create_canonical_catalogs_or_release(db):
    job = t06(db)
    tables = [
        "universities",
        "majors",
        "programs",
        "program_years",
        "admission_methods",
        "cutoff_scores",
        "dataset_releases",
    ]
    counts = {
        n: db.execute(sa.select(sa.func.count()).select_from(metadata.tables[n])).scalar_one()
        for n in tables
    }
    version = db.execute(sa.select(metadata.tables["catalog_state"].c.dataset_version)).scalar_one()
    ResolutionStore(db).run(job, base())
    assert {
        n: db.execute(sa.select(sa.func.count()).select_from(metadata.tables[n])).scalar_one()
        for n in tables
    } == counts
    assert (
        db.execute(sa.select(metadata.tables["catalog_state"].c.dataset_version)).scalar_one()
        == version
    )


def test_approved_canonical_id_must_exist_in_database(db):
    from tests.resolution.test_matcher import entity, registry

    job = t06(db)
    invalid = registry([entity()]).model_copy(update={"classification": "reviewed"})
    with pytest.raises(ValueError, match="canonical|synthetic"), db.begin_nested():
        ResolutionStore(db).run(job, invalid)


def test_concurrent_workers_create_one_resolution_manifest(migrated_engine):
    with migrated_engine.begin() as c:
        job = t06(c)

    def work():
        with migrated_engine.begin() as c:
            return ResolutionStore(c).run(job, base())

    with ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(pool.map(lambda _: work(), range(2)))
    assert sorted(r["inserted"] for r in rs) == [0, 1]
    assert len({r["job_id"] for r in rs}) == 1


def test_alias_withdrawal_has_versioned_impact_without_rewriting_history(db):
    job = t06(db)
    raw_registry = base().frozen()
    raw_registry.update(version="registry/impact-test/1", alias_version="aliases/impact-test/1")
    raw_registry["entities"][0]["domains"].append("example.invalid")
    for a in raw_registry["aliases"]:
        if a["kind"] == "domain":
            a["value"] = "example.invalid"
    reg = EntityRegistry.model_validate(raw_registry)
    store = ResolutionStore(db)
    original = store.run(job, reg)
    key = "proposal:alias:ptit:domain"
    impacted = store.affected(key)
    assert len(impacted) == 1 and impacted[0]["registry_version"] == "registry/impact-test/1"
    newer = reg.model_copy(deep=True).model_copy(
        update={"version": "registry/impact-test/2", "alias_version": "aliases/impact-test/2"}
    )
    # Immutable DTOs require a revalidated clone for the changed registry version.
    new_json = newer.model_dump(mode="json")
    for a in new_json["aliases"]:
        if a["key"] == key:
            a["review"] = {
                "status": "revoked",
                "reviewer": "SYNTHETIC TEST REVIEWER",
                "at": "2026-10-17",
                "evidence": ["fixture://withdraw"],
            }
    newer = EntityRegistry.model_validate(new_json)
    revised = store.run(job, newer)
    assert revised["job_id"] != original["job_id"]
    assert store.replay(original["job_id"])["cached"]
    assert store.affected(key)[0]["candidate_key"] == impacted[0]["candidate_key"]


def test_new_alias_impact_request_includes_old_unresolved_candidates(db):
    job = t06(db)
    store = ResolutionStore(db)
    store.run(job, base())
    changed = base().frozen()
    changed["alias_version"] = "aliases/new-impact/2"
    changed["aliases"].append(
        {
            "key": "new:alias",
            "target": "proposal:ptit",
            "value": "Tên chưa biết trước đây",
            "kind": "name",
            "review": {"status": "pending", "evidence": ["fixture://new-alias"]},
        }
    )
    newer = EntityRegistry.model_validate(changed)
    hits = store.affected("new:alias", newer)
    assert hits and hits[0]["impact_kind"] == "potential_registry_change"
