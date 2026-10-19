from copy import deepcopy
from uuid import uuid4

import pytest

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
        assert c.queries["offering"].code_system == "ptit:table-program-label"
        assert c.entities["offering"].options
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
    e = entity(
        "u:test",
        domains=["tuyensinh.ptit.edu.vn"],
        attributes={"table_program_code_system": "test:table-program-label"},
    )
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


def pending_uit_registry(code_system=None):
    attributes = {} if code_system is None else {"table_program_code_system": code_system}
    return EntityRegistry.model_validate(
        dict(
            version="registry/uit-fixture/1",
            alias_version="aliases/uit-fixture/1",
            classification="pilot_pending",
            entities=[
                dict(
                    key="proposal:uit",
                    kind="university",
                    name="Synthetic UIT fixture",
                    domains=["tuyensinh.uit.edu.vn"],
                    attributes=attributes,
                    review={"status": "pending", "evidence": ["fixture://uit-owner"]},
                )
            ],
        )
    )


def test_pending_new_source_uses_its_own_offering_code_namespace():
    row = input_row().model_copy(update={"final_url": "https://tuyensinh.uit.edu.vn/fixture"})
    full = propose_registry(pending_uit_registry("uit:table-program-label"), [row])
    offering = next(e for e in full.entities if e.kind == "offering")
    assert offering.codes[0].system == "uit:table-program-label"
    assert all(e.canonical_id is None and e.review.status == "pending" for e in full.entities)
    result = resolve(row, full).candidates[0]
    assert result.queries["offering"].code_system == "uit:table-program-label"
    assert result.entities["offering"].options
    assert result.status == "unresolved" and not result.publication_eligible


def test_unknown_source_without_code_namespace_cannot_inherit_ptit_offerings():
    row = input_row().model_copy(update={"final_url": "https://tuyensinh.uit.edu.vn/fixture"})
    full = propose_registry(pending_uit_registry(), [row])
    assert [e.kind for e in full.entities] == ["university"]
    result = resolve(row, full).candidates[0]
    assert result.queries["offering"].code_system is None
    assert result.entities["offering"].status == "unresolved"
    assert not result.entities["offering"].options
    assert "OFFERING_CODE_SYSTEM_MISSING" in result.entities["offering"].reasons


@pytest.mark.parametrize("namespace", ["", " uit:table-program-label", "uit", 7])
def test_invalid_explicit_source_code_namespace_is_rejected(namespace):
    row = input_row().model_copy(update={"final_url": "https://tuyensinh.uit.edu.vn/fixture"})
    with pytest.raises(ValueError, match="code system"):
        propose_registry(pending_uit_registry(namespace), [row])
