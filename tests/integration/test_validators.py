from decimal import Decimal
from uuid import uuid4

import pytest

from services.api.db.models import metadata
from tests.fixtures import make_scope


def test_validator_rejects_wrong_scale_year(db):
    from services.api.db.validators import validate_admission

    f = make_scope(db)
    db.execute(
        metadata.tables["score_scales"]
        .update()
        .where(metadata.tables["score_scales"].c.id == f["scale"])
        .values(admission_year=2025)
    )
    with pytest.raises(ValueError, match="year"):
        validate_admission(db, f["scope_values"])


def test_validator_requires_three_subjects(db):
    from services.api.db.validators import validate_admission

    f = make_scope(db)
    combination = f["add"]("combinations", code=str(uuid4()), name="TEST ONLY")
    with pytest.raises(ValueError, match="three"):
        validate_admission(db, f["scope_values"] | {"combination_id": combination})


@pytest.mark.parametrize("score", [Decimal("0.5"), Decimal("NaN"), 24.5, Decimal("24.123456")])
def test_cutoff_validator_rejects_invalid_or_lossy_score(db, score):
    from services.api.db.validators import validate_cutoff

    f = make_scope(db)
    with pytest.raises(ValueError):
        validate_cutoff(db, f["cutoff_values"] | {"score": score})


def test_verified_cutoff_requires_verified_scoped_source(db):
    from services.api.db.validators import validate_cutoff

    f = make_scope(db)
    sources = metadata.tables["sources"]
    db.execute(
        sources.update().where(sources.c.id == f["source"]).values(verification_status="unverified")
    )
    with pytest.raises(ValueError, match="source"):
        validate_cutoff(db, f["cutoff_values"])
    db.execute(
        sources.update()
        .where(sources.c.id == f["source"])
        .values(
            verification_status="verified",
            authority_scope={"years": [2025], "fact_kinds": ["cutoff"]},
        )
    )
    with pytest.raises(ValueError, match="authority"):
        validate_cutoff(db, f["cutoff_values"])


def test_conflicting_condition_registry_is_rejected(db):
    from services.api.db.validators import validate_admission

    f = make_scope(db)
    with pytest.raises(ValueError, match="condition"):
        validate_admission(db, f["scope_values"] | {"condition_dsl": {"different": True}})


def test_primary_evidence_requires_matching_payload_and_snapshot(db):
    from services.api.db.validators import validate_evidence

    f = make_scope(db)
    observation = f["add"](
        "observations",
        snapshot_id=f["snapshot"],
        fact_kind="cutoff",
        record_locator="row:1",
        parser_version="fixture-v1",
        transform_version="fixture-v1",
        raw_fields={},
        normalized_fields={"canonical_fact": {"different": True}},
        payload_hash="c" * 64,
        extraction_method="manual",
        verification_status="verified",
    )
    values = {"cutoff_id": f["cutoff"], "observation_id": observation, "evidence_role": "primary"}
    with pytest.raises(ValueError, match="payload"):
        validate_evidence(db, values)
    observations = metadata.tables["observations"]
    db.execute(
        observations.update()
        .where(observations.c.id == observation)
        .values(normalized_fields={"canonical_fact": f["payload"]})
    )
    validate_evidence(db, values)
    validate_evidence(db, values | {"evidence_role": "supporting"})
    with pytest.raises(ValueError, match="conflicting"):
        validate_evidence(db, values | {"evidence_role": "conflicting"})


def test_canonical_count_does_not_count_revisions_or_nonpublic_records(db):
    from services.api.db.validators import count_canonical_cutoffs

    f = make_scope(db)
    assert count_canonical_cutoffs(db) == 1
    f["add"]("cutoff_scores", **(f["cutoff_values"] | {"revision": 2, "is_current": False}))
    assert count_canonical_cutoffs(db) == 1
    admissions = metadata.tables["program_admissions"]
    db.execute(
        admissions.update().where(admissions.c.id == f["scope"]).values(data_status="withdrawn")
    )
    assert count_canonical_cutoffs(db) == 0


def test_guarded_session_rejects_inplace_cutoff_edit(db):
    from services.api.db.models import CutoffScore
    from services.api.db.session import SessionFactory

    f = make_scope(db)
    with SessionFactory(bind=db) as session:
        score = session.get(CutoffScore, f["cutoff"])
        score.score = Decimal("25")
        with pytest.raises(ValueError, match="immutable"):
            session.flush()


def test_lossless_trailing_zero_decimals_are_accepted(db):
    from services.api.db.validators import validate_cutoff

    f = make_scope(db)
    validate_cutoff(db, f["cutoff_values"] | {"score": Decimal("24.500000")})


def test_verified_rule_rejects_cross_year_scale(db):
    from services.api.db.validators import validate_rule

    f = make_scope(db)
    values = {
        "program_year_id": f["offering"],
        "method_id": f["method"],
        "output_scale_id": f["scale"],
        "verification_status": "verified",
        "primary_snapshot_id": f["snapshot"],
    }
    validate_rule(db, values)
    scales = metadata.tables["score_scales"]
    db.execute(scales.update().where(scales.c.id == f["scale"]).values(admission_year=2025))
    with pytest.raises(ValueError, match="year"):
        validate_rule(db, values)


def test_evidence_rows_do_not_inflate_canonical_count(db):
    from services.api.db.validators import count_canonical_cutoffs

    f = make_scope(db)
    for i in range(2):
        observation = f["add"](
            "observations",
            snapshot_id=f["snapshot"],
            fact_kind="cutoff",
            record_locator=f"row:{i}",
            parser_version="fixture-v1",
            transform_version="fixture-v1",
            raw_fields={},
            normalized_fields={"canonical_fact": f["payload"]},
            payload_hash="c" * 64,
            extraction_method="manual",
            verification_status="verified",
        )
        f["add"](
            "cutoff_evidence",
            cutoff_id=f["cutoff"],
            observation_id=observation,
            evidence_role="supporting",
        )
    assert count_canonical_cutoffs(db) == 1


def test_orm_insert_cannot_bypass_decimal_validator(db):
    from services.api.db.models import CutoffScore
    from services.api.db.session import SessionFactory

    f = make_scope(db)
    with SessionFactory(bind=db) as session:
        session.add(
            CutoffScore(
                id=uuid4(),
                **(f["cutoff_values"] | {"revision": 2, "is_current": False, "score": 24.5}),
            )
        )
        with pytest.raises(ValueError, match="Decimal"):
            session.flush()


def test_persisted_scope_basis_cannot_change_under_a_cutoff(db):
    from services.api.db.models import ProgramAdmission
    from services.api.db.session import SessionFactory

    f = make_scope(db)
    with SessionFactory(bind=db) as session:
        scope = session.get(ProgramAdmission, f["scope"])
        scope.condition_dsl = {"changed": True}
        with pytest.raises(ValueError, match="immutable"):
            session.flush()


def test_persisted_offering_year_cannot_reinterpret_historical_cutoff(db):
    from services.api.db.models import ProgramYear
    from services.api.db.session import SessionFactory

    f = make_scope(db)
    db.execute(
        metadata.tables["admission_years"]
        .insert()
        .values(university_id=f["university"], admission_year=2025, status="unknown")
    )
    with SessionFactory(bind=db) as session:
        offering = session.get(ProgramYear, f["offering"])
        offering.admission_year = 2025
        with pytest.raises(ValueError, match="immutable"):
            session.flush()


def test_cutoff_payload_requires_schema_version(db):
    from services.api.db.validators import validate_cutoff

    f = make_scope(db)
    with pytest.raises(ValueError, match="schema_version"):
        validate_cutoff(db, f["cutoff_values"] | {"fact_payload": {"score": "24.12345"}})


@pytest.mark.parametrize("mismatch", [None, "method", "offering", "campus", "snapshot"])
def test_source_publication_bindings_enforce_actual_admission_context(db, mismatch):
    from services.api.db.validators import record, validate_cutoff

    f = make_scope(db)
    offering = record(db, "program_years", f["scope_values"]["program_year_id"])
    method = record(db, "admission_methods", f["scope_values"]["method_id"])
    binding = dict(
        admission_year=offering["admission_year"],
        method_code=method["code"],
        offering_code=offering["offering_code"],
        campus_code=offering["campus_code"],
        snapshot_ids=[str(f["snapshot"])],
    )
    if mismatch:
        key = {"method": "method_code", "offering": "offering_code", "campus": "campus_code"}.get(
            mismatch
        )
        if key:
            binding[key] = "OUTSIDE-APPROVED-SCOPE"
        else:
            binding["snapshot_ids"] = [str(uuid4())]
    source = record(db, "sources", f["source"])
    db.execute(
        metadata.tables["sources"]
        .update()
        .where(metadata.tables["sources"].c.id == f["source"])
        .values(authority_scope=source["authority_scope"] | {"publication_bindings": [binding]})
    )
    if mismatch:
        with pytest.raises(ValueError, match="binding"):
            validate_cutoff(db, f["cutoff_values"])
    else:
        validate_cutoff(db, f["cutoff_values"])


def test_conversion_requires_restricted_authority_for_both_methods(db):
    from services.api.db.validators import record, validate_rule

    f = make_scope(db)
    target_method = f["add"](
        "admission_methods", code="TEST-TARGET", name="TEST ONLY", input_kind="exam_total"
    )
    target_scale = f["add"](
        "score_scales",
        method_id=target_method,
        admission_year=2026,
        code="TEST-TARGET",
        exam_version="TEST ONLY",
        min_score=Decimal("0"),
        max_score=Decimal("100"),
        basis_description="TEST ONLY",
        primary_snapshot_id=f["snapshot"],
    )
    offering = record(db, "program_years", f["offering"])
    method = record(db, "admission_methods", f["method"])
    binding = {
        "admission_year": 2026,
        "method_code": method["code"],
        "offering_code": offering["offering_code"],
        "campus_code": offering["campus_code"],
        "snapshot_ids": [str(f["snapshot"])],
    }
    authority = {
        "years": [2026],
        "fact_kinds": ["conversion_rule"],
        "publication_bindings": [binding],
    }
    db.execute(
        metadata.tables["sources"]
        .update()
        .where(metadata.tables["sources"].c.id == f["source"])
        .values(authority_scope=authority)
    )
    values = {
        "program_year_id": f["offering"],
        "from_method_id": f["method"],
        "from_scale_id": f["scale"],
        "to_method_id": target_method,
        "to_scale_id": target_scale,
        "verification_status": "verified",
        "primary_snapshot_id": f["snapshot"],
    }
    with pytest.raises(ValueError, match="binding"):
        validate_rule(db, values, conversion=True)
    authority["publication_bindings"].append(binding | {"method_code": "TEST-TARGET"})
    db.execute(
        metadata.tables["sources"]
        .update()
        .where(metadata.tables["sources"].c.id == f["source"])
        .values(authority_scope=authority)
    )
    validate_rule(db, values, conversion=True)
