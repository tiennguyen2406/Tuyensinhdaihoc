from decimal import Decimal
from uuid import uuid4

import pytest


def test_fingerprints_separate_fact_from_bundle_and_reject_float():
    from services.data.publication.contract import (
        bundle_fingerprint,
        canonical_decimal,
        fingerprint,
    )

    assert canonical_decimal(Decimal("24.50000")) == "24.5"
    with pytest.raises(ValueError):
        canonical_decimal(24.5)
    identity = {"schema_version": "test", "offering": str(uuid4()), "year": 2024}
    fact = fingerprint(identity | {"score": "24.5"})
    assert fact == fingerprint({"score": "24.5", **identity})
    assert bundle_fingerprint(identity, ["fee-a"], []) != bundle_fingerprint(
        identity, ["fee-b"], []
    )
    assert fact == fingerprint(identity | {"score": "24.5"})
    with pytest.raises(ValueError):
        fingerprint({"score": 24.5})


def test_superuser_is_not_a_review_identity(db):
    from services.data.publication.access import require

    with pytest.raises(PermissionError):
        require(db, "reviewer")


def test_packet_is_bound_to_real_candidate_and_changes_on_parent_tampering(db):
    from services.data.publication.packets import binding_for, inspect_packet
    from tests.publication.helpers import input_packet

    packet = input_packet(db)
    assert packet["candidate"]["admission_year"] == 2024
    bound = binding_for(packet)
    assert (
        inspect_packet(db, bound.resolution_id, bound.candidate_key)["packet_sha256"]
        == bound.packet_sha256
    )
    from services.api.db.models import observations

    db.execute(
        observations.update()
        .where(observations.c.id == packet["raw_observation_id"])
        .values(raw_fields={"tampered": True})
    )
    with pytest.raises(ValueError):
        inspect_packet(db, bound.resolution_id, bound.candidate_key)


def test_review_rejects_blank_reason_and_naive_publication_time():
    from datetime import datetime

    from pydantic import ValidationError

    from services.data.publication.contract import Binding, CutoffSpec, ReviewCommand

    with pytest.raises(ValidationError):
        ReviewCommand(
            request_id=uuid4(),
            action="reject",
            binding=Binding(resolution_id=uuid4(), candidate_key="test", packet_sha256="0" * 64),
            expected_registry_version="r/1",
            expected_alias_version="a/1",
            reason="        ",
        )
    # Gate tested on the actual Pydantic field definitions, no actor/score coercion.
    with pytest.raises(ValidationError):
        CutoffSpec(
            university_id=uuid4(),
            program_year_id=uuid4(),
            admission_year=2024,
            method_id=uuid4(),
            score="24.5",
            evidence={},
            source_published_at=datetime(2024, 8, 20),
        )
