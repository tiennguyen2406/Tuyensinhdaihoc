"""Synthetic identities/approvals for offline tests only; never seed production."""

import pytest

from services.data.resolution.contract import EntityQuery
from services.data.resolution.matching import match
from tests.resolution.helpers import alias, entity, registry


def test_exact_code_and_domain_conflict_fail_closed():
    reg = registry(
        [
            entity(codes=[{"system": "test:official", "value": "A"}], domains=["a.example.test"]),
            entity("u:b", name="Đại học Mẫu Beta", domains=["b.example.test"]),
        ]
    )
    exact = match(EntityQuery(kind="university", code="A", code_system="test:official"), reg)
    assert exact.status == "resolved" and exact.entity_key == "u:a" and exact.method == "exact_code"
    conflict = match(
        EntityQuery(
            kind="university", code="A", code_system="test:official", domain="b.example.test"
        ),
        reg,
    )
    assert conflict.status == "ambiguous" and conflict.canonical_id is None
    assert any("domain" in o.conflicts for o in conflict.options)


def test_pending_identity_and_alias_are_not_approved_by_matching():
    e = entity()
    e["canonical_id"] = None
    e["review"] = {"status": "pending", "evidence": ["fixture://proposal"]}
    a = alias()
    a["review"] = {"status": "pending", "evidence": ["fixture://proposal"]}
    reg = registry([e], [a])
    result = match(EntityQuery(kind="university", name="ĐH Mẫu A"), reg)
    assert result.canonical_id is None and result.status == "unresolved"
    assert result.options and result.options[0].proposal_key == "u:a"


def test_alias_collision_and_fuzzy_tie_remain_review():
    reg = registry(
        [entity(), entity("u:b", name="Đại học Mẫu Alpha B")],
        [alias(value="ĐH Mẫu"), alias("alias:b", "u:b", value="ĐH Mẫu")],
    )
    result = match(EntityQuery(kind="university", name="ĐH Mẫu"), reg)
    assert result.status == "ambiguous" and result.canonical_id is None
    fuzzy = match(EntityQuery(kind="university", name="Đại học Mẫu Alph"), reg)
    assert fuzzy.canonical_id is None and len(fuzzy.options) == 2
    assert fuzzy.margin is not None and fuzzy.margin < 0.08


def test_program_parent_and_offering_attributes_are_hard_blocks():
    es = [
        entity(),
        entity("u:b"),
        entity(
            "p:a", "program", university_key="u:a", codes=[{"system": "test:program", "value": "P"}]
        ),
        entity(
            "p:b", "program", university_key="u:b", codes=[{"system": "test:program", "value": "P"}]
        ),
    ]
    reg = registry(es)
    q = EntityQuery(kind="program", code="P", code_system="test:program", university_key="u:a")
    assert match(q, reg).entity_key == "p:a"
    assert match(q.model_copy(update={"university_key": None}), reg).canonical_id is None
    es += [
        entity(
            "o:a",
            "offering",
            university_key="u:a",
            program_key="p:a",
            attributes={"admission_year": 2024, "campus": "BVH", "language": "vi", "track": "A"},
            codes=[{"system": "test:offering", "value": "X"}],
        ),
        entity(
            "o:b",
            "offering",
            university_key="u:a",
            program_key="p:a",
            attributes={"admission_year": 2024, "campus": "BVS", "language": "en", "track": "B"},
            codes=[{"system": "test:offering", "value": "X"}],
        ),
    ]
    reg = registry(es)
    result = match(
        EntityQuery(
            kind="offering",
            code="X",
            code_system="test:offering",
            university_key="u:a",
            program_key="p:a",
            attributes={"admission_year": 2024, "campus": "BVS", "language": "en", "track": "B"},
        ),
        reg,
    )
    assert result.entity_key == "o:b"
    assert (
        match(
            EntityQuery(
                kind="offering",
                code="X",
                code_system="test:offering",
                university_key="u:a",
                program_key="p:a",
                attributes={"admission_year": 2024},
            ),
            reg,
        ).status
        == "ambiguous"
    )


def test_validity_unknown_and_wrong_code_system_never_fall_back_to_auto_name():
    reg = registry(
        [entity(codes=[{"system": "official:A", "value": "X", "from_year": 2024, "to_year": 2024}])]
    )
    assert (
        match(
            EntityQuery(
                kind="university",
                code="X",
                code_system="official:A",
                attributes={"admission_year": 2024},
            ),
            reg,
        ).status
        == "resolved"
    )
    assert (
        match(
            EntityQuery(
                kind="university",
                code="X",
                code_system="official:A",
                attributes={"admission_year": 2025},
            ),
            reg,
        ).canonical_id
        is None
    )
    assert (
        match(EntityQuery(kind="university", code="X", code_system="official:A"), reg).canonical_id
        is None
    )
    assert match(EntityQuery(kind="major", code="X", code_system="offering:A"), reg).options == []


def test_registry_requires_real_approval_fields_and_typed_parent_relationships():
    e = entity()
    e["review"] = {"status": "approved", "evidence": ["fixture://approval"]}
    with pytest.raises(ValueError):
        registry([e])
    e = entity()
    e["review"] = {"status": "pending", "evidence": ["fixture://proposal"]}
    with pytest.raises(ValueError):
        registry([e])
    with pytest.raises(ValueError):
        registry([entity(), entity("p:a", "program", university_key="absent")])


def test_unapproved_or_revoked_alias_cannot_be_used_for_automatic_link():
    a = alias()
    a["review"] = {
        "status": "revoked",
        "reviewer": "SYNTHETIC TEST REVIEWER",
        "evidence": ["fixture://revoke"],
        "at": "2026-10-17",
    }
    reg = registry(aliases=[a])
    assert match(EntityQuery(kind="university", name="ĐH Mẫu A"), reg).canonical_id is None


def test_equal_score_maximum_is_not_an_identity_feature():
    reg = registry(
        [
            entity("m:a", "method", "Kỳ thi Mẫu A", attributes={"max_score": 30}),
            entity("m:b", "method", "Kỳ thi Mẫu B", attributes={"max_score": 1200}),
        ]
    )
    a = match(EntityQuery(kind="method", name="Kỳ thi Mẫu", attributes={}), reg)
    b = match(EntityQuery(kind="method", name="Kỳ thi Mẫu", attributes={"max_score": 30}), reg)
    assert [(o.entity_key, o.score) for o in a.options] == [
        (o.entity_key, o.score) for o in b.options
    ]
    assert not b.canonical_id


def test_fuzzy_alias_dependency_is_retained_for_revocation_impact():
    reg = registry(aliases=[alias(value="Đại học Mẫu tên cũ")])
    result = match(EntityQuery(kind="university", name="Đại học Mẫu tên củ"), reg)
    assert result.canonical_id is None
    assert any("alias:a" in o.alias_keys for o in result.options)


def test_registry_cannot_duplicate_same_canonical_entity_as_two_keys():
    a = entity()
    b = entity("u:b")
    b["canonical_id"] = a["canonical_id"]
    with pytest.raises(ValueError):
        registry([a, b])


def test_official_code_conflicting_with_another_approved_name_requires_review():
    reg = registry(
        [
            entity(name="Trường Mẫu A", codes=[{"system": "test:official", "value": "A"}]),
            entity("u:b", name="Trường Mẫu B"),
        ]
    )
    result = match(
        EntityQuery(kind="university", code="A", code_system="test:official", name="Trường Mẫu B"),
        reg,
    )
    assert result.status == "ambiguous" and result.canonical_id is None


def test_hard_context_blocks_remain_explainable():
    reg = registry(
        [
            entity(
                attributes={"province": "TEST-A"}, codes=[{"system": "test:official", "value": "A"}]
            )
        ]
    )
    result = match(
        EntityQuery(
            kind="university",
            code="A",
            code_system="test:official",
            attributes={"province": "TEST-B"},
        ),
        reg,
    )
    assert result.canonical_id is None
    assert result.blocked_entities["u:a"] == ["province"]


def test_approved_legacy_code_alias_only_applies_inside_reviewed_time_scope():
    e = entity(codes=[{"system": "official:fixture", "value": "NEW", "from_year": 2025}])
    a = alias(value="OLD", code_system="official:fixture", from_year=2024, to_year=2024)
    a["kind"] = "legacy_code"
    reg = registry([e], [a])
    q = EntityQuery(
        kind="university",
        code="OLD",
        code_system="official:fixture",
        attributes={"admission_year": 2024},
    )
    result = match(q, reg)
    assert result.entity_key == "u:a" and result.method == "approved_alias"
    assert (
        match(q.model_copy(update={"attributes": {"admission_year": 2025}}), reg).canonical_id
        is None
    )
    assert match(q.model_copy(update={"attributes": {}}), reg).canonical_id is None


def test_known_other_registered_domain_blocks_code_or_alias_even_if_target_domain_missing():
    es = [
        entity(codes=[{"system": "test:official", "value": "A"}]),
        entity("u:b", domains=["b.example.test"]),
    ]
    reg = registry(es, [alias()])
    for query in [
        EntityQuery(
            kind="university", code="A", code_system="test:official", domain="b.example.test"
        ),
        EntityQuery(kind="university", name="ĐH Mẫu A", domain="b.example.test"),
    ]:
        result = match(query, reg)
        assert result.canonical_id is None and result.status == "ambiguous"


def test_approved_entity_without_canonical_uuid_is_rejected_by_contract():
    e = entity()
    e["canonical_id"] = None
    with pytest.raises(ValueError):
        registry([e])


def test_code_binding_order_cannot_hide_a_complete_approved_binding():
    codes = [
        {"system": "test:official", "value": "A", "attributes": {"province": "TEST-A"}},
        {"system": "test:official", "value": "A"},
    ]
    query = EntityQuery(kind="university", code="A", code_system="test:official")
    for values in [codes, list(reversed(codes))]:
        result = match(query, registry([entity(codes=values)]))
        assert result.status == "resolved" and result.entity_key == "u:a"


def test_approved_offering_requires_year_and_missing_canonical_context_cannot_link():
    owner = entity()
    program = entity("p:a", "program", university_key="u:a")
    bad = entity(
        "o:a",
        "offering",
        university_key="u:a",
        program_key="p:a",
        codes=[{"system": "test:offering", "value": "A"}],
    )
    with pytest.raises(ValueError):
        registry([owner, program, bad])
    bad["attributes"] = {"admission_year": 2024, "campus": None, "language": None, "track": None}
    reg = registry([owner, program, bad])
    result = match(
        EntityQuery(
            kind="offering",
            university_key="u:a",
            program_key="p:a",
            code="A",
            code_system="test:offering",
            attributes={"admission_year": 2024, "campus": "BVH"},
        ),
        reg,
    )
    assert result.canonical_id is None and result.options
