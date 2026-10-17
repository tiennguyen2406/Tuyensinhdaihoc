from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
import sqlalchemy as sa

from services.api.db.models import ingest_jobs, metadata, observations
from services.data.normalization.contract import NormalizationContext
from services.data.normalization.store import NormalizationStore
from services.data.parsers.contract import ParseResult
from services.data.parsers.persistence import ObservationStore
from tests.normalization.helpers import raw_row
from tests.parsers.test_persistence import ref


def seed(db):
    snapshot = ref(db)
    row = raw_row().model_copy(
        update={"snapshot_id": snapshot["id"], "source_id": snapshot["source_id"]}
    )
    from services.data.parsers.contract import ExtractedObservation

    item = ExtractedObservation.model_validate(row.model_dump(exclude={"id", "normalized_fields"}))
    ObservationStore(db).save(ParseResult(observations=[item]))
    return db.execute(
        sa.select(observations.c.id).where(observations.c.snapshot_id == snapshot["id"])
    ).scalar_one()


def test_raw_rows_immutable_new_namespace_idempotent_and_versioned(db):
    raw_id = seed(db)
    before = dict(
        db.execute(sa.select(observations).where(observations.c.id == raw_id)).mappings().one()
    )
    counters = {
        name: db.execute(sa.select(sa.func.count()).select_from(metadata.tables[name])).scalar_one()
        for name in ["cutoff_scores", "dataset_releases"]
    }
    version_before = db.execute(
        sa.select(metadata.tables["catalog_state"].c.dataset_version)
    ).scalar_one()
    store = NormalizationStore(db)
    jobs_before = db.execute(sa.select(sa.func.count()).select_from(ingest_jobs)).scalar_one()
    preview = store.preview([raw_id])
    assert preview["summary"]["candidates"] == 1
    assert (
        db.execute(sa.select(sa.func.count()).select_from(ingest_jobs)).scalar_one() == jobs_before
    )
    first = store.run([raw_id])
    second = store.run([raw_id])
    assert first["inserted"] == 1 and second["inserted"] == 0 and second["cached"]
    assert first["job_id"] == second["job_id"]
    result = (
        db.execute(
            sa.select(observations).where(
                observations.c.id != raw_id, observations.c.snapshot_id == before["snapshot_id"]
            )
        )
        .mappings()
        .one()
    )
    assert result["raw_fields"] == before["raw_fields"]
    assert result["normalized_fields"]["input_observation_id"] == str(raw_id)
    assert result["normalized_fields"]["candidates"][0]["value"]["value"] == "24.50"
    assert result["verification_status"] == "unverified"
    assert (
        dict(
            db.execute(sa.select(observations).where(observations.c.id == raw_id)).mappings().one()
        )
        == before
    )
    newer = store.run([raw_id], NormalizationContext(version="normalizer/2.0.0"))
    assert newer["inserted"] == 1
    assert (
        db.execute(
            sa.select(sa.func.count())
            .select_from(observations)
            .where(observations.c.snapshot_id == before["snapshot_id"])
        ).scalar_one()
        == 3
    )
    for name, old in counters.items():
        assert (
            db.execute(sa.select(sa.func.count()).select_from(metadata.tables[name])).scalar_one()
            == old
        )
    assert (
        db.execute(sa.select(metadata.tables["catalog_state"].c.dataset_version)).scalar_one()
        == version_before
    )


def test_output_cannot_be_reused_as_input_and_config_drift_rejected(db):
    raw_id = seed(db)
    store = NormalizationStore(db)
    store.run([raw_id])
    output_id = (
        db.execute(
            sa.select(observations.c.id).where(
                observations.c.normalized_fields["input_observation_id"].astext == str(raw_id)
            )
        )
        .scalars()
        .first()
    )
    with pytest.raises(ValueError, match="raw-only"), db.begin_nested():
        store.run([output_id])
    with pytest.raises(ValueError, match="version"), db.begin_nested():
        store.run([raw_id], NormalizationContext(training_modes=("Chính quy", "Thường xuyên")))


def test_modified_input_or_output_under_same_namespace_rejected(db):
    raw_id = seed(db)
    store = NormalizationStore(db)
    store.run([raw_id])
    old = db.execute(
        sa.select(observations.c.raw_fields).where(observations.c.id == raw_id)
    ).scalar_one()
    changed = deepcopy(old)
    changed["text"] = "Synthetic tamper"
    with pytest.raises(ValueError, match="input"), db.begin_nested():
        db.execute(
            observations.update().where(observations.c.id == raw_id).values(raw_fields=changed)
        )
        store.run([raw_id])
    with pytest.raises(ValueError, match="payload"), db.begin_nested():
        db.execute(
            observations.update().where(observations.c.id != raw_id).values(payload_hash="0" * 64)
        )
        store.run([raw_id])


def test_concurrent_workers_do_not_duplicate_envelopes(migrated_engine):
    with migrated_engine.begin() as c:
        raw_id = seed(c)

    def work():
        with migrated_engine.begin() as c:
            return NormalizationStore(c).run([raw_id])

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: work(), range(2)))
    assert sorted(r["inserted"] for r in results) == [0, 1]
    assert len({r["job_id"] for r in results}) == 1


def test_missing_requested_input_fails_instead_of_silent_subset(db):
    from uuid import uuid4

    with pytest.raises(ValueError, match="input"):
        NormalizationStore(db).preview([uuid4()])


def test_batch_conflict_rolls_back_earlier_new_envelopes(db):
    ids = sorted([seed(db), seed(db), seed(db)])
    store = NormalizationStore(db)
    store.run([ids[-1]])
    db.execute(
        observations.update()
        .where(observations.c.normalized_fields["input_observation_id"].astext == str(ids[-1]))
        .values(payload_hash="f" * 64)
    )
    before = db.execute(sa.select(sa.func.count()).select_from(observations)).scalar_one()
    with pytest.raises(ValueError, match="payload"), db.begin_nested():
        store.run(ids)
    assert db.execute(sa.select(sa.func.count()).select_from(observations)).scalar_one() == before


def test_parent_metadata_drift_cannot_hide_in_a_different_batch(db):
    from decimal import Decimal

    old_id = seed(db)
    store = NormalizationStore(db)
    store.run([old_id])
    new_id = seed(db)
    with pytest.raises(ValueError, match="payload"), db.begin_nested():
        db.execute(
            observations.update()
            .where(observations.c.id == old_id)
            .values(extraction_confidence=Decimal("0.5000"))
        )
        store.run([old_id, new_id])
