"""Synthetic tables only; never real source rows or quota data."""

import hashlib
from uuid import uuid4

from services.api.source_profiles import SourceProfile
from services.data.normalization.contract import NormalizationContext, RawObservation
from services.data.normalization.normalize import normalize
from services.data.parsers.contract import SnapshotRef
from services.data.parsers.registry import extract


def run(school, url, body):
    data = body.encode()
    ref = SnapshotRef(
        snapshot_id=uuid4(),
        source_id=uuid4(),
        raw_hash=hashlib.sha256(data).hexdigest(),
        raw_uri="private",
        final_url=url,
        media_type="text/html",
        byte_size=len(data),
    )
    profile = SourceProfile(
        profile_id="synthetic-hcm",
        university_key=school,
        allowed_hosts=[url.split("/")[2]],
        seed_urls=[url],
        years=[2024, 2025, 2026],
        authority_scope={},
        parser="hcm_cutoff_tables_html",
    )
    parsed = extract(ref, profile, data)
    drafts = []
    for obs in parsed.observations:
        row = RawObservation(
            id=uuid4(),
            **obs.model_dump(exclude={"source_id", "issues", "verification_status"}),
            source_id=ref.source_id,
        )
        drafts.extend(
            normalize(row, NormalizationContext(version="normalizer/hcm-intake/1.0.0")).candidates
        )
    return parsed, drafts


def test_ou_preserves_suffix_zero_and_blank_without_inventing_campus():
    body = "<main><h2>Thông báo điểm chuẩn trúng tuyển phương thức sử dụng KQ thi TN THPT 2024</h2><table><tr><th>Mã ngành</th><th>Tên ngành</th><th>Điểm chuẩn</th></tr><tr><td>7480201C</td><td>Công nghệ thông tin CLC</td><td>20,50</td></tr><tr><td>7340101</td><td>Quản trị</td><td>—</td></tr></table></main>"
    parsed, drafts = run(
        "ou",
        "https://tuyensinh.ou.edu.vn/thong-bao-diem-chuan-trung-tuyen-phuong-thuc-su-dung-kq-thi-tn-thpt-2024",
        body,
    )
    assert len(drafts) == 1
    d = drafts[0]
    assert d.admission_year == 2024 and str(d.value.value) == "20.50"
    assert d.scope["offering_code"]["display"] == "7480201C"
    assert d.scope["campus"] is None and d.score_scale is None
    assert d.status == "needs_review" and d.verification_status == "unverified"
    assert d.entity_ids == {} and parsed.observations


def test_hcmue_rowspan_years_scales_and_non_hcm_scope():
    body = """<div id="component"><h2>ĐIỂM TRÚNG TUYỂN CỦA 2 NĂM GẦN NHẤT</h2><table><tr><td><table>
    <tr><th rowspan="2">TT</th><th rowspan="2">Mã xét tuyển</th><th rowspan="2">Tên chương trình</th><th rowspan="2">Mã ngành</th><th rowspan="2">Tên ngành</th><th rowspan="2">Phương thức</th><th colspan="3">Năm 2025</th><th colspan="3">Năm 2024</th></tr>
    <tr><th>Chỉ tiêu</th><th>Nhập học</th><th>Điểm TT/Thang điểm xét</th><th>Chỉ tiêu</th><th>Nhập học</th><th>Điểm TT/Thang điểm xét</th></tr>
    <tr><td>1</td><td rowspan="2">7140201_GL</td><td rowspan="2">Giáo dục mầm non (đào tạo tại phân hiệu Gia Lai)</td><td rowspan="2">7140201</td><td rowspan="2">Giáo dục mầm non</td><td>405</td><td>4</td><td>4</td><td>24.6/30</td><td>1</td><td>1</td><td>—</td></tr>
    <tr><td>2</td><td>401-NK</td><td>4</td><td>4</td><td>25/30</td><td>1</td><td>1</td><td>20/30</td></tr></table></td></tr></table></div>"""
    _, drafts = run(
        "hcmue", "https://tuyensinh.hcmue.edu.vn/index.php?id=27810&option=com_content", body
    )
    assert len(drafts) == 3
    assert {d.admission_year for d in drafts} == {2024, 2025}
    assert all(d.scope["geo_scope"] == "outside_hcm" for d in drafts)
    assert all(d.scope["offering_code"]["display"] == "7140201_GL" for d in drafts)
    assert {d.method.display for d in drafts} == {"405", "401-NK"}
    assert all(d.scope["source_scale_max"] == "30" for d in drafts)


def test_source_url_and_header_drift_fail_closed():
    parsed, drafts = run(
        "ou",
        "https://tuyensinh.ou.edu.vn/unknown-2024",
        "<main><h2>Điểm chuẩn 2024</h2><table><tr><td>20</td></tr></table></main>",
    )
    assert not drafts and parsed.issues


def test_ueh_multi_method_cell_stays_one_aggregate_with_campus_evidence():
    from services.data.parsers.hcm_intake import UEH_2025

    body = """<div class="elementor-widget-theme-post-title"><h2>UEH công bố điểm chuẩn năm 2025</h2></div><div class="elementor-widget-theme-post-content"><div class="elementor-widget-container"><p>II. Điểm trúng tuyển tại TP. Hồ Chí Minh (Mã trường: KSA)</p><table><tr><th>STT</th><th>Mã xét tuyển</th><th>Chương trình đào tạo</th><th>Chỉ tiêu 2025</th><th>Điểm trúng tuyển (PT2,3,4,5)</th></tr><tr><td>1</td><td>7340101_01</td><td>Chương trình A</td><td>100</td><td>24.50</td></tr></table></div></div>"""
    _, drafts = run("ueh", "https://tuyensinh.ueh.edu.vn" + UEH_2025, body)
    assert len(drafts) == 1
    assert drafts[0].scope["source_aggregate"] is True
    assert drafts[0].scope["campus"]["display"] == "KSA"
    assert drafts[0].scope["method_namespace"] == "ueh:2025"
    assert drafts[0].score_scale is None

    _, named_code = run(
        "ueh", "https://tuyensinh.ueh.edu.vn" + UEH_2025, body.replace("7340101_01", "ISB_CNTN")
    )
    assert len(named_code) == 1 and named_code[0].scope["offering_code"]["display"] == "ISB_CNTN"


def test_ou_methods_remain_distinct_and_score_spans_are_quarantined():
    from services.data.parsers.hcm_intake import OU_2026

    body = """<main><h2>Thông báo điểm chuẩn trúng tuyển 2026</h2><table><tr><th>TT</th><th>Mã xét tuyển</th><th>Tên ngành</th><th>Điểm chuẩn theo điểm TN THPT</th><th>Điểm chuẩn ĐGNL</th></tr><tr><td>1</td><td>7480201</td><td>Test A</td><td>22,99</td><td>800</td></tr><tr><td>2</td><td>7480201C</td><td>Test CLC</td><td colspan="2">22</td></tr></table></main>"""
    _, drafts = run("ou", "https://tuyensinh.ou.edu.vn" + OU_2026, body)
    assert len(drafts) == 2
    assert {d.method.display for d in drafts} == {"THPT", "ĐGNL"}
    assert all(d.scope["offering_code"]["display"] == "7480201" for d in drafts)


def test_negative_out_of_scale_and_missing_scores_never_become_zero():
    from services.data.parsers.hcm_intake import OU_2024

    body = """<main><h2>Điểm chuẩn trúng tuyển THPT 2024</h2><table><tr><th>Mã ngành</th><th>Tên ngành</th><th>Điểm chuẩn</th></tr><tr><td>7480201</td><td>A</td><td>-1</td></tr><tr><td>7480202</td><td>B</td><td>31/30</td></tr><tr><td>7480203</td><td>C</td><td></td></tr><tr><td>7480204</td><td>D</td><td>0</td></tr></table></main>"""
    _, drafts = run("ou", "https://tuyensinh.ou.edu.vn" + OU_2024, body)
    assert len(drafts) == 1 and drafts[0].value.raw == "0"


def test_ueh_2026_integrated_score_and_nine_digit_code_are_not_thpt():
    from services.data.parsers.hcm_intake import UEH_2026

    body = """<div class="elementor-widget-theme-post-title"><h2>UEH công bố kết quả xét tuyển năm 2026</h2></div><div class="elementor-widget-theme-post-content"><div class="elementor-widget-container"><p>2. Phương thức 2: Phương thức xét tuyển tích hợp.</p><p>- KSA:</p><table><tr><th>STT</th><th>Mã xét tuyển</th><th>Chương trình đào tạo</th><th>Chỉ tiêu 2026</th><th>Tổ hợp môn</th><th>Điểm trúng tuyển</th></tr><tr><td>1</td><td>731010201</td><td>Chương trình A</td><td>100</td><td>A00, A01</td><td>83.40</td></tr></table></div></div>"""
    body = body.replace("<p>- KSA:</p>", "<li>KSA:</li>")
    _, drafts = run("ueh", "https://tuyensinh.ueh.edu.vn" + UEH_2026, body)
    assert len(drafts) == 1 and drafts[0].admission_year == 2026
    assert drafts[0].scope["offering_code"]["display"] == "731010201"
    assert drafts[0].method.display == "PT2 tích hợp"
    assert drafts[0].scope["source_aggregate"] is False
    assert drafts[0].score_scale is None


def test_ou_2025_supplemental_round_is_kept_separate():
    from services.data.parsers.hcm_intake import OU_2025_R2

    body = "<main><h2>Điểm chuẩn xét tuyển đại học chính quy đợt 2 năm 2025</h2><table><tr><th>STT</th><th>Mã xét tuyển</th><th>Tên mã xét tuyển</th><th>Điểm chuẩn đối với Điểm thi Tốt nghiệp THPT</th></tr><tr><td>1</td><td>7480201C</td><td>Chương trình tiên tiến</td><td>15,00</td></tr></table></main>"
    _, drafts = run("ou", "https://tuyensinh.ou.edu.vn" + OU_2025_R2, body)
    assert len(drafts) == 1 and drafts[0].scope["source_round"] == "đợt 2"


def test_hcmue_2026_rejects_swapped_method_columns():
    body = """<div id="component"><h2>THÔNG BÁO KẾT QUẢ XÉT TUYỂN NĂM 2026</h2><table><tr><th>Mã tuyển sinh</th><th>Mã ngành</th><th>Tên ngành</th><th>Điểm trúng tuyển học tập THPT kết hợp ĐGNLCB</th><th>Điểm trúng tuyển thi tốt nghiệp THPT 2026</th></tr><tr><td>SPS</td><td>7480201</td><td>Công nghệ thông tin</td><td>17</td><td>18</td></tr></table></div>"""
    parsed, drafts = run(
        "hcmue", "https://tuyensinh.hcmue.edu.vn/index.php?id=27833&option=com_content", body
    )
    assert not drafts and any(i.code == "HCM_HEADERS" for i in parsed.issues)
    body = "<main><h2>Điểm chuẩn 2024</h2><table><tr><th>Mã ngành</th><th>Điểm chuẩn</th><th>Tên ngành</th></tr><tr><td>7480201</td><td>20</td><td>Test</td></tr></table></main>"
    parsed, drafts = run(
        "ou",
        "https://tuyensinh.ou.edu.vn/thong-bao-diem-chuan-trung-tuyen-phuong-thuc-su-dung-kq-thi-tn-thpt-2024",
        body,
    )
    assert not drafts and parsed.issues
