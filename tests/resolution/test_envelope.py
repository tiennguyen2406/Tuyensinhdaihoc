from copy import deepcopy
from uuid import uuid4

from services.data.normalization.contract import NormalizationContext
from services.data.normalization.normalize import normalize
from services.data.resolution.contract import ResolutionInput
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.resolve import propose_registry, resolve
from tests.normalization.helpers import raw_row
from tests.resolution.test_matcher import entity


def input_row(campus="BVH"):
    raw = raw_row(campus=campus)
    return ResolutionInput(
        envelope_id=uuid4(),
        envelope=normalize(raw, NormalizationContext()),
        final_url="https://tuyensinh.ptit.edu.vn/pilot",
        source_id=raw.source_id,
    )


def test_real_pilot_seed_is_pending_and_bvh_bvs_are_one_proposal():
    from pathlib import Path

    seed = EntityRegistry.load(Path("config/entities/ptit-v1.json"))
    north, south = input_row(), input_row("BVS")
    full = propose_registry(seed, [north, south])
    assert len([e for e in full.entities if e.kind == "university"]) == 1
    assert all(e.canonical_id is None and e.review.status == "pending" for e in full.entities)
    for row in [north, south]:
        before = deepcopy(row.model_dump(mode="json"))
        result = resolve(row, full)
        c = result.candidates[0]
        assert c.status == "unresolved" and not c.publication_eligible
        assert c.entities["university"].options[0].proposal_key == "proposal:ptit"
        assert c.input_envelope_id == row.envelope_id
        assert c.candidate_key == row.envelope.candidates[0].candidate_key
        assert c.admission_year == 2024
        assert c.lineage == row.envelope.candidates[0].lineage.model_dump(mode="json")
        assert row.model_dump(mode="json") == before
        assert all(m.canonical_id is None for m in c.entities.values())


def test_group_tuition_does_not_create_offering_or_admission_year():
    from pathlib import Path

    row = input_row()
    raw = raw_row()
    raw = raw.model_copy(
        update={
            "fact_kind": "tuition",
            "raw_fields": {
                "kind": "text_block",
                "raw_text": "Học phí năm học 2026-2027: khoảng 25 triệu đồng/năm đến 30 triệu đồng/năm.",
                "context": raw.raw_fields["context"],
            },
        }
    )
    row = row.model_copy(
        update={"envelope": normalize(raw, NormalizationContext()), "source_id": raw.source_id}
    )
    seed = EntityRegistry.load(Path("config/entities/ptit-v1.json"))
    result = resolve(row, propose_registry(seed, [row]))
    c = result.candidates[0]
    assert c.admission_year is None and c.academic_year == "2026–2027"
    assert not c.entities["offering"].options and c.entities["offering"].canonical_id is None
    assert "TUITION_GROUP_NOT_OFFERING" in c.publication_blockers


def test_partial_identity_does_not_imply_complete_fact_or_release_blocked_attempts():
    row = input_row()
    # Reviewed synthetic university/domain binding only; no source method/scale approval.
    e = entity("u:test", domains=["tuyensinh.ptit.edu.vn"])
    reg = EntityRegistry.model_validate(
        dict(
            version="registry/test/1",
            alias_version="aliases/test/1",
            classification="synthetic",
            entities=[e],
            aliases=[
                {
                    "key": "domain:test",
                    "target": "u:test",
                    "kind": "domain",
                    "value": "tuyensinh.ptit.edu.vn",
                    "review": e["review"],
                }
            ],
        )
    )
    result = resolve(row, reg)
    c = result.candidates[0]
    assert c.status == "partial" and c.entities["university"].canonical_id
    assert c.entities["major"].canonical_id is None and c.entities["scope"].canonical_id is None
    assert c.unresolved_fields["score_scale"] is None
    assert c.unresolved_fields["round"] is None and c.unresolved_fields["population"] is None
    assert not c.publication_eligible
    assert result.blocked_input_attempts == len(row.envelope.blocked)


def test_exact_provisional_program_limits_offering_suggestions_without_auto_link():
    from pathlib import Path

    a = input_row()
    b = input_row()
    b.envelope.candidates[0].scope["program_name"]["display"] = (
        "Ngành mẫu — Tiếng Pháp — Chất lượng cao"
    )
    reg = propose_registry(EntityRegistry.load(Path("config/entities/ptit-v1.json")), [a, b])
    result = resolve(a, reg).candidates[0]
    assert len(result.entities["program"].options) > 1
    assert result.entities["offering"].options
    assert result.entities["offering"].canonical_id is None
