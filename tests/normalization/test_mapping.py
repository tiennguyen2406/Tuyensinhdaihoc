from copy import deepcopy
from decimal import Decimal

import pytest

from services.data.normalization.contract import NormalizationContext
from services.data.normalization.normalize import normalize
from tests.normalization.helpers import raw_row


def test_explicit_cell_mapping_lineage_and_year_separated_from_document():
    row = raw_row()
    before = row.model_dump(mode="json")
    result = normalize(row, NormalizationContext())
    assert len(result.candidates) == 1
    item = result.candidates[0]
    assert item.admission_year == 2024 and item.document_year == 2026
    assert item.value.value == Decimal("24.50")
    assert item.method.display == "Thi tốt nghiệp THPT"
    assert item.scope["campus"]["display"] == "BVH"
    assert item.scope["training_mode"]["display"] == "Chính quy"
    assert item.scope["program_name"]["display"] == "Ngành mẫu — Tiếng Anh — Chất lượng cao"
    assert item.lineage.observation_id == row.id and item.lineage.snapshot_id == row.snapshot_id
    assert item.lineage.row_locator == row.record_locator
    assert item.lineage.cell_locator.endswith("td:nth-of-type(3)")
    assert [h["text"] for h in item.lineage.header_path] == [
        "Năm tuyển sinh 2024",
        "Điểm trúng tuyển",
        "Thi tốt nghiệp THPT",
    ]
    assert item.score_scale is None and item.verification_status == "unverified"
    assert row.model_dump(mode="json") == before


@pytest.mark.parametrize(
    "year,method,score,code",
    [
        ("2025", "", "24", "METHOD_MISSING"),
        ("2024", "ĐGNL, ĐGTD", "24", "METHOD_AMBIGUOUS"),
        ("2024", "Điểm TT", "24", "METHOD_AMBIGUOUS"),
        ("2023", "Thi tốt nghiệp THPT", "24", "YEAR_OUT_OF_SCOPE"),
        ("2024", "Thi tốt nghiệp THPT", "1.200", "NUMERIC_AMBIGUOUS"),
        ("2024", "Thi tốt nghiệp THPT", "—", "VALUE_NOT_REPORTED"),
    ],
)
def test_ambiguity_never_uses_stale_method_or_title_year(year, method, score, code):
    result = normalize(raw_row(year=year, method=method, score=score), NormalizationContext())
    assert result.candidates == []
    assert code in [i.code for b in result.blocked for i in b.issues]


def test_null_is_blocked_but_zero_is_a_value():
    row = raw_row(score="0")
    assert normalize(row, NormalizationContext()).candidates[0].value.value == Decimal("0")
    row.raw_fields["cells"][-1]["text"] = ""
    row.raw_fields["cells"][-1]["raw_text"] = ""
    row.raw_fields["origin_cells"][row.raw_fields["cells"][-1]["origin"]]["text"] = ""
    row.raw_fields["origin_cells"][row.raw_fields["cells"][-1]["origin"]]["raw_text"] = ""
    assert not normalize(row, NormalizationContext()).candidates


def test_methods_years_and_combinations_are_not_cartesian_expanded():
    row = raw_row()
    f = row.raw_fields
    f["headers"].append(
        [
            {"text": "Năm tuyển sinh 2025", "locator": "header:2025"},
            {"text": "Điểm trúng tuyển", "locator": "header:score"},
            {"text": "Xét tuyển tài năng", "locator": "header:talent"},
        ]
    )
    cell = {
        "column": 3,
        "origin": "cell:2025",
        "text": "72.52",
        "raw_text": "72.52",
        "span_reference": False,
    }
    f["cells"].append(cell)
    f["origin_cells"]["cell:2025"] = {
        "text": "72.52",
        "raw_text": "72.52",
        "row": 3,
        "column": 3,
        "colspan": 1,
        "rowspan": 1,
        "locator": "cell:2025",
    }
    f["footnotes"] = [{"text": "Tổ hợp A00, A01; áp dụng điều kiện riêng (*)", "locator": "note:1"}]
    result = normalize(row, NormalizationContext())
    assert [(c.admission_year, c.value.value) for c in result.candidates] == [
        (2024, Decimal("24.50")),
        (2025, Decimal("72.52")),
    ]
    assert all(c.combinations is None and c.score_scale is None for c in result.candidates)
    assert all(c.lineage.footnotes[0]["locator"] == "note:1" for c in result.candidates)
    assert all("CONDITIONS_REQUIRE_REVIEW" in [i.code for i in c.issues] for c in result.candidates)


def test_score_span_and_reference_slots_never_duplicate_values():
    row = raw_row()
    original = row.raw_fields["cells"][-1]
    row.raw_fields["cells"].append(
        original | {"column": 3, "text": None, "raw_text": None, "span_reference": True}
    )
    row.raw_fields["headers"].append(deepcopy(row.raw_fields["headers"][-1]))
    row.raw_fields["origin_cells"][original["origin"]]["colspan"] = 2
    result = normalize(row, NormalizationContext())
    assert not result.candidates and len(result.blocked) == 1
    assert "SCORE_SPAN_AMBIGUOUS" in [i.code for i in result.blocked[0].issues]


def test_cross_row_score_span_does_not_attach_to_another_program():
    row = raw_row()
    row.raw_fields["origin_cells"][row.raw_fields["cells"][-1]["origin"]]["rowspan"] = 2
    assert not normalize(row, NormalizationContext()).candidates


def test_document_issues_remain_open_but_unrelated_image_not_a_cell_blocker():
    row = raw_row()
    context = NormalizationContext(
        document_issues=[
            {
                "code": "image_requires_review",
                "locator": "html:other > img",
                "detail": "Not downloaded",
            },
            {"code": "ocr_required", "locator": "pdf:p1", "detail": "Scan"},
        ]
    )
    result = normalize(row, context)
    assert len(result.candidates) == 1
    assert len(result.issues) >= 2
    assert all(
        not i.blocks_candidate and i.level == "document"
        for i in result.issues
        if i.code in {"image_requires_review", "ocr_required"}
    )
    row.raw_fields["_extraction"] = {
        "issues": [
            {
                "code": "mixed_threshold_cutoff_context",
                "locator": row.raw_fields["table_locator"],
                "detail": "Ambiguous meaning",
            }
        ]
    }
    assert not normalize(row, context).candidates


def test_different_scope_and_outside_pilot_are_not_merged():
    north = normalize(raw_row(campus="BVH"), NormalizationContext())
    south = normalize(raw_row(campus="BVS"), NormalizationContext())
    assert north.candidates[0].scope != south.candidates[0].scope
    outside = normalize(raw_row(form="Thường xuyên"), NormalizationContext())
    assert not outside.candidates
    assert any(i.code == "TRAINING_MODE_OUT_OF_SCOPE" for b in outside.blocked for i in b.issues)


def test_admission_year_not_guessed_from_academic_year_or_posting_date():
    row = raw_row(year="2025–2026")
    row.raw_fields["headers"][-1][0]["text"] = "Năm học 2025–2026"
    row.raw_fields["published_at"] = "2026-05-01"
    result = normalize(row, NormalizationContext())
    assert not result.candidates
    assert "ADMISSION_YEAR_MISSING" in [i.code for b in result.blocked for i in b.issues]


def test_input_must_be_raw_only_not_normalizer_output():
    row = raw_row()
    bad = row.model_copy(
        update={"transform_version": "normalizer/1", "normalized_fields": {"candidates": []}}
    )
    with pytest.raises(ValueError, match="raw-only"):
        normalize(bad, NormalizationContext())


def test_tuition_academic_year_and_range_are_not_admission_year_or_average():
    row = raw_row()
    row = row.model_copy(
        update={
            "fact_kind": "tuition",
            "raw_fields": {
                "kind": "text_block",
                "raw_text": "Học phí chương trình mẫu năm học 2026-2027: trung bình từ khoảng 35,9 triệu đồng/năm đến 40,7 triệu đồng/năm tùy theo chương trình;",
                "context": row.raw_fields["context"],
            },
        }
    )
    result = normalize(row, NormalizationContext())
    assert len(result.candidates) == 1
    c = result.candidates[0]
    assert c.admission_year is None and c.academic_year == "2026–2027"
    assert c.value.minimum == Decimal("35900000") and c.value.maximum == Decimal("40700000")
    assert c.value.approximate and c.value.unit == "academic_year"
    assert c.lineage.cell_locator == row.record_locator


def test_threshold_and_abbreviated_header_remain_review_not_cutoff():
    row = raw_row()
    row.raw_fields["headers"][-1][1]["text"] = "Điểm sàn"
    assert not normalize(row, NormalizationContext()).candidates
    row.raw_fields["headers"][-1][1]["text"] = "Điểm TT"
    assert not normalize(row, NormalizationContext()).candidates


def test_blocked_value_retains_typed_null_status_and_does_not_become_zero():
    result = normalize(raw_row(score="N/A"), NormalizationContext())
    assert not result.candidates
    assert result.blocked[0].value.status == "not_applicable"
    assert result.blocked[0].value.value is None
    assert result.blocked[0].value.raw == "N/A"


def test_tuition_missing_training_scope_requires_review():
    row = raw_row()
    row = row.model_copy(
        update={
            "fact_kind": "tuition",
            "raw_fields": {
                "kind": "text_block",
                "raw_text": "Học phí năm học 2026-2027: khoảng 25 triệu đồng/năm đến 30 triệu đồng/năm.",
                "context": [],
            },
        }
    )
    result = normalize(row, NormalizationContext())
    assert not result.candidates
    assert any(i.code == "TRAINING_MODE_MISSING" for b in result.blocked for i in b.issues)


def test_later_mixed_campus_cannot_keep_a_precise_previous_campus():
    row = raw_row()
    row.raw_fields["context"].append({"text": "Áp dụng cho BVH và BVS", "locator": "context:joint"})
    result = normalize(row, NormalizationContext())
    assert not result.candidates
    assert "CAMPUS_AMBIGUOUS" in [i.code for b in result.blocked for i in b.issues]


def test_conflicting_program_columns_cannot_choose_last_program_for_score():
    row = raw_row()
    row.raw_fields["headers"].append(
        [{"text": "Mã chương trình/ngành năm 2025", "locator": "header:othercode"}]
    )
    row.raw_fields["cells"].append(
        {"column": 3, "origin": "cell:othercode", "text": "TEST-B", "raw_text": "TEST-B"}
    )
    result = normalize(row, NormalizationContext())
    assert not result.candidates
    assert "PROGRAM_SCOPE_AMBIGUOUS" in [i.code for b in result.blocked for i in b.issues]


def test_multiple_tuition_ranges_are_reviewed_without_selecting_first():
    row = raw_row()
    row = row.model_copy(
        update={
            "fact_kind": "tuition",
            "raw_fields": {
                "kind": "text_block",
                "raw_text": "Học phí năm học 2026-2027: nhóm A từ 25 triệu đồng/năm đến 30 triệu đồng/năm; nhóm B từ 40 triệu đồng/năm đến 50 triệu đồng/năm.",
                "context": row.raw_fields["context"],
            },
        }
    )
    result = normalize(row, NormalizationContext())
    assert not result.candidates
    assert "TUITION_MULTIPLE_RANGES" in [i.code for b in result.blocked for i in b.issues]
