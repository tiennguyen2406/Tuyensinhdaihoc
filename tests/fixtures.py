from decimal import Decimal
from uuid import uuid4

from services.api.db.models import metadata


def make_scope(db):
    assert db.engine.url.database.startswith("tuyensinh_test_")

    def add(table_name, **values):
        table = metadata.tables[table_name]
        if "id" in table.c and "id" not in values:
            values["id"] = uuid4()
        db.execute(table.insert().values(**values))
        return values.get("id")

    university = add(
        "universities",
        university_code=str(uuid4()),
        name="TEST ONLY",
        normalized_name="test only",
        slug=str(uuid4()),
    )
    program = add(
        "programs",
        university_id=university,
        canonical_key="TEST",
        program_name="TEST ONLY",
        normalized_name="test only",
    )
    method = add("admission_methods", code=str(uuid4()), name="TEST ONLY", input_kind="exam_total")
    source = add(
        "sources",
        canonical_url="https://example.invalid/" + str(uuid4()),
        domain="example.invalid",
        publisher="TEST ONLY",
        university_id=university,
        source_type="university",
        verification_status="verified",
        authority_scope={"years": [2026], "fact_kinds": ["cutoff", "scoring_rule"]},
    )
    snapshot = add(
        "source_snapshots",
        source_id=source,
        raw_hash="a" * 64,
        raw_uri="fixture://test",
        final_url="https://example.invalid/test",
        media_type="text/html",
        byte_size=0,
    )
    add("admission_years", university_id=university, admission_year=2026, status="verified")
    offering = add(
        "program_years",
        university_id=university,
        program_id=program,
        admission_year=2026,
        offering_code="TEST",
        offering_name="TEST ONLY",
        primary_snapshot_id=snapshot,
    )
    scale = add(
        "score_scales",
        method_id=method,
        admission_year=2026,
        code="TEST",
        exam_version="TEST ONLY",
        min_score=Decimal("1"),
        max_score=Decimal("30"),
        basis_description="Synthetic fixture, never production",
        primary_snapshot_id=snapshot,
    )
    scope_values = dict(
        program_year_id=offering,
        method_id=method,
        combination_id=None,
        round_key="TEST",
        population_key="TEST",
        condition_key="TEST",
        condition_text="TEST ONLY",
        condition_dsl={},
        score_scale_id=scale,
        data_status="published",
        primary_snapshot_id=snapshot,
    )
    scope = add("program_admissions", **scope_values)
    payload = {"schema_version": "fixture-v1", "score": "24.12345"}
    cutoff_values = dict(
        program_admission_id=scope,
        revision=1,
        score_scale_id=scale,
        score=Decimal("24.12345"),
        max_score=Decimal("30"),
        fact_fingerprint="b" * 64,
        publication_group_key="TEST",
        fact_payload=payload,
        primary_snapshot_id=snapshot,
        verification_status="verified",
        is_current=True,
    )
    cutoff = add("cutoff_scores", **cutoff_values)
    return dict(
        add=add,
        university=university,
        program=program,
        method=method,
        source=source,
        snapshot=snapshot,
        offering=offering,
        scale=scale,
        scope=scope,
        scope_values=scope_values,
        cutoff=cutoff,
        cutoff_values=cutoff_values,
        payload=payload,
    )
