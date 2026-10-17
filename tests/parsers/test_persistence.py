from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from services.api.db.models import metadata, observations
from services.data.parsers.contract import ExtractedObservation, ParseResult
from services.data.parsers.persistence import ObservationStore
from tests.fixtures import make_scope


def ref(db):
    f = make_scope(db)
    table = metadata.tables["source_snapshots"]
    return db.execute(select(table).where(table.c.id == f["snapshot"])).mappings().one()


def result(row, version="html/1.0.0+1"):
    return ParseResult(
        observations=[
            ExtractedObservation(
                snapshot_id=row["id"],
                source_id=row["source_id"],
                fact_kind="catalog",
                record_locator="html:article:nth-of-type(1)",
                parser_version=version,
                extraction_method="html_dom",
                raw_fields={"text": "SYNTHETIC TEST ONLY", "kind": "text_block"},
                extraction_confidence=Decimal("0.7000"),
            )
        ]
    )


def test_insert_only_idempotency_new_version_and_no_canonical_effect(db):
    row = ref(db)
    store = ObservationStore(db)
    before = db.execute(select(metadata.tables["catalog_state"].c.dataset_version)).scalar_one()
    payload = result(row)
    assert store.save(payload) == 1
    assert store.save(payload) == 0
    assert store.save(result(row, "html/1.0.0+2")) == 1
    records = (
        db.execute(select(observations).where(observations.c.snapshot_id == row["id"]))
        .mappings()
        .all()
    )
    assert len(records) == 2
    assert all(
        r["verification_status"] == "unverified" and r["normalized_fields"] == {} for r in records
    )
    assert all(r["extraction_confidence"] == Decimal("0.7000") for r in records)
    assert (
        db.execute(select(metadata.tables["catalog_state"].c.dataset_version)).scalar_one()
        == before
    )


def test_same_key_changed_payload_rejected_and_original_preserved(db):
    row = ref(db)
    store = ObservationStore(db)
    payload = result(row)
    store.save(payload)
    changed = payload.model_copy(deep=True)
    changed.observations[0].raw_fields["text"] = "CHANGED"
    with pytest.raises(ValueError, match="version"), db.begin_nested():
        store.save(changed)
    record = db.execute(
        select(observations.c.raw_fields).where(observations.c.snapshot_id == row["id"])
    ).scalar_one()
    assert record["text"] == "SYNTHETIC TEST ONLY"


def test_wrong_snapshot_source_or_duplicate_locator_is_rejected(db):
    row = ref(db)
    store = ObservationStore(db)
    payload = result(row)
    bad = payload.model_copy(deep=True)
    bad.observations[0] = bad.observations[0].model_copy(update={"source_id": uuid4()})
    with pytest.raises(ValueError, match="source"), db.begin_nested():
        store.save(bad)
    duplicate = ParseResult(observations=payload.observations * 2)
    with pytest.raises(ValueError, match="Duplicate"), db.begin_nested():
        store.save(duplicate)
