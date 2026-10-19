"""Synthetic supplemental HTML; actual crawler snapshots are verified privately, not in CI."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from bs4 import BeautifulSoup

from services.api.db.models import metadata, observations
from services.api.source_profiles import SourceProfile
from services.data.normalization.contract import NormalizationContext
from services.data.normalization.normalize import normalize
from services.data.normalization.store import NormalizationStore
from services.data.parsers.html import locate
from services.data.parsers.persistence import ObservationStore
from services.data.parsers.registry import extract
from services.data.publication.packets import binding_for, checked_packet, inspect_packet
from services.data.resolution.contract import ResolutionInput
from services.data.resolution.resolve import propose_registry, resolve
from services.data.resolution.store import ResolutionStore
from tests.normalization.test_ueh import CODES, pending, raw
from tests.normalization.test_ueh import CTX as AUGUST_CTX
from tests.normalization.test_ueh import body as august_body
from tests.normalization.test_ueh import parsed as august_parsed
from tests.parsers.helpers import snapshot

URL = "https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-trung-tuyen-dot-xet-tuyen-bo-sung-khoa-50-dai-hoc-chinh-quy-tai-phan-hieu-vinh-long-ma-truong-ksv/"
CTX = NormalizationContext(version="normalizer/ueh-supplemental-2024/1.0.0")
NAMES = [
    "Tiếng Anh thương mại (**)",
    "Thuế (S)",
    "Công nghệ và đổi mới sáng tạo (*)",
    "Robot và Trí tuệ nhân tạo (hệ kỹ sư)",
    "Kinh doanh nông nghiệp (S)",
    "Quản trị khách sạn",
]
VALUES = ["20", "20", "17", "17", "17", "20"]


def body():
    rows = "".join(
        f"<tr><td>{i + 1}</td><td>{code}</td><td>{name}</td><td>A00, D01</td><td>42</td><td>{score}</td></tr>"
        for i, (code, name, score) in enumerate(zip(CODES, NAMES, VALUES))
    )
    return f"""<div class="elementor-widget-theme-post-title"><h2>UEH công bố điểm trúng tuyển đợt xét tuyển bổ sung Khóa 50 – Đại học chính Quy tại Phân hiệu Vĩnh Long (Mã trường KSV)</h2></div>
    <div class="elementor-widget-post-info"><li itemprop="datePublished"><time>30/09/2024</time></li></div>
    <div class="elementor-widget-theme-post-content"><div class="elementor-widget-container">
    <p>Hội đồng tuyển sinh Đại học Kinh tế Thành phố Hồ Chí Minh (UEH) công bố kết quả trúng tuyển Khóa 50 – Đại học chính quy, năm 2024 đợt xét tuyển bổ sung của các phương thức:</p>
    <p>– Phương thức xét tuyển quá trình học tập theo tổ hợp môn (PT4).</p>
    <p>– Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024 (PT6).</p>
    <p>2. ĐIỂM TRÚNG TUYỂN</p>
    <p>– Điểm chuẩn trúng tuyển của từng chương trình bằng nhau giữa các tổ hợp xét tuyển và bằng nhau giữa các nguyện vọng.</p>
    <table><tr><th>STT</th><th>Mã ĐKXT</th><th>Chương trình đào tạo</th><th>Tổ hợp xét tuyển</th><th>PT4</th><th>PT6</th></tr>{rows}</table>
    <p>(*): Toán nhân hệ số 2 (Đối với PT6 thi TNTHPT 2024), quy về thang điểm 30.</p>
    <p>(**): Tiếng Anh hệ số 2 (Đối với PT6 thi TNTHPT 2024), quy về thang điểm 30.</p>
    <p>(S) Chương trình song ngành tích hợp: mô tả synthetic, học phí 50%.</p>
    <p>3. ĐIỂM XÉT TUYỂN CỦA THÍ SINH (Theo Đề án Tuyển sinh năm 2024)</p>
    <p>– Trường hợp thí sinh trúng tuyển 01 chương trình đào tạo ở 02 phương thức, UEH xác định một phương thức trúng tuyển duy nhất theo thứ tự ưu tiên sau:</p>
    <ul><li>Ưu tiên 1: PT4</li><li>Ưu tiên 2: PT6</li></ul>
    <p>– Thí sinh trúng tuyển khi thỏa cả hai điều kiện sau:</p>
    <ul><li>Tốt nghiệp chương trình THPT hoặc tương đương</li><li>Điểm xét tuyển lớn hơn hoặc bằng điểm trúng tuyển</li></ul>
    <p>3.1.2. Phương thức xét điểm thi THPT.</p>
    <p>Điểm xét tuyển = Tổng điểm 3 môn theo tổ hợp xét tuyển + điểm ưu tiên đối tượng, ưu tiên khu vực (nếu có).</p>
    <p>Điểm xét tuyển chương trình Tiếng Anh thương mại = (Điểm môn 1 + Điểm môn 2 + Điểm môn Tiếng Anh x 2)x3/4+ Điểm ưu tiên (nếu có).</p>
    <p>Điểm xét tuyển chương trình Công nghệ đổi mới sáng tạo = (Điểm môn Toán x 2 + Điểm môn 2 + Điểm môn 3)x3/4+ Điểm ưu tiên (nếu có).</p>
    <p>3.2.1.1 Mức điểm ưu tiên đối tượng, ưu tiên khu vực quy đổi theo thang điểm 100 (PT4)</p>
    <table><tr><th>PT4 Điểm ưu tiên</th></tr><tr><td>100</td></tr></table>
    <p>3.2.1.2 Mức điểm ưu tiên đối tượng, ưu tiên khu vực quy đổi theo thang điểm 30 (PT6)</p>
    <p>– Mức điểm ưu tiên được quy đổi từ tổng điểm 22,5 trở lên (thang điểm 30):</p>
    <p>Điểm ưu tiên = [(30 – Tổng điểm đạt được)/7,5] × (Mức điểm ưu tiên đối tượng + Mức điểm ưu tiên khu vực)</p>
    <p>Trong đó, mức điểm ưu tiên theo thang điểm 30:</p>
    <table><tr><th>Ưu tiên đối tượng</th><th>Ưu tiên khu vực</th></tr><tr><td>2</td><td>0.75</td></tr></table>
    <p>4. HƯỚNG DẪN XÁC NHẬN NHẬP HỌC</p><p>Ngưỡng 15.00, chỉ tiêu 600, ngày 01/10/2024.</p>
    </div></div>""".encode()


def parsed(data=None):
    data = data or body()
    ref = snapshot(data).model_copy(update={"final_url": URL})
    profile = SourceProfile.model_validate_json(
        Path("config/sources/ueh-2024-supplemental-20261020-v1.json").read_text(encoding="utf8")
    ).model_copy(update={"parser": "ueh_2024_supplemental_html"})
    return extract(ref, profile, data, revision="supplemental-test"), ref


def candidates(result):
    return [c for o in result.observations for c in normalize(raw(o), CTX).candidates]


def test_six_original_pt6_cells_and_source_scope():
    result, ref = parsed()
    assert len(result.observations) == 6
    values = candidates(result)
    assert len(values) == 6
    soup = BeautifulSoup(body(), "html.parser")
    for code, name, score, c in zip(CODES, NAMES, VALUES, values):
        assert (
            c.scope["offering_code"]["display"] == code
            and c.scope["program_name"]["display"] == name
        )
        assert c.value.value == Decimal(score)
        assert c.lineage.raw_value == locate(soup, c.lineage.cell_locator).get_text()
        assert c.lineage.column == 5 and c.admission_year == 2024
        assert (
            c.scope["campus"]["display"] == "KSV"
            and c.scope["training_mode"]["display"] == "Chính quy"
        )
        assert c.method.display == "UEH PT6 — Thi tốt nghiệp THPT năm 2024"
        ev = c.lineage.scope_evidence["ueh_supplemental_2024"]
        assert ev["snapshot_sha256"] == ref.raw_hash
        assert ev["round"]["proposed_key"].endswith("20240930")
        assert ev["round"]["ordinal"] is None and not ev["round"]["approved"]
        assert ev["publication_date"]["value"] == "2024-09-30"
        assert c.round is c.conditions is c.population is c.score_scale is c.combinations is None
        assert c.verification_status == "unverified"
        assert len(ev["priority"]["pt6"]) >= 3 and "22,5" in str(ev["priority"]["pt6"])
        assert "100" not in str(ev["priority"]["pt6"])
        assert ev["eligibility"] and ev["method_preference"]


def test_marker_specific_weighting_and_formulas_not_rules():
    values = candidates(parsed()[0])
    for i, c in enumerate(values):
        ev = c.lineage.scope_evidence["ueh_supplemental_2024"]
        weight = ev["weighting"]
        if i in (0, 2):
            assert weight["subject"] == ("Tiếng Anh" if i == 0 else "Toán")
            assert weight["marker"] == ("(**)" if i == 0 else "(*)")
            assert weight["factor"] == "2" and "x3/4" in weight["formula"]["text"]
        else:
            assert weight is None
        if i in (1, 4):
            assert "(S)" in ev["program_markers"] and any(
                "(S)" in n["text"] for n in c.lineage.footnotes
            )
        assert "scoring_rule_id" not in c.entity_ids
    assert not any("Toán" in n["text"] for n in values[0].lineage.footnotes)
    assert not any("Tiếng Anh" in n["text"] for n in values[2].lineage.footnotes)


@pytest.mark.parametrize(
    "old,new",
    [
        ("Tiếng Anh thương mại (**)", "Tiếng Anh thương mại (*)"),
        ("Quản trị khách sạn", "Quản trị khách sạn (*)"),
        ("Tiếng Anh thương mại (**)", "Chương trình khác (**)"),
        ("Tiếng Anh thương mại (**)", "Tiếng Anh thương mại"),
    ],
)
def test_named_formula_requires_matching_program_and_marker(old, new):
    source = body().decode()
    assert old in source
    result, _ = parsed(source.replace(old, new).encode())
    assert not candidates(result)


def test_source_nbsp_method_spacing_preserves_raw_evidence():
    source = (
        body().decode().replace("– Phương thức xét tuyển dựa", "–\u00a0 Phương thức xét tuyển dựa")
    )
    result, _ = parsed(source.encode())
    values = candidates(result)
    assert len(values) == 6
    assert (
        "\u00a0" in values[0].lineage.scope_evidence["ueh_supplemental_2024"]["method"]["raw_text"]
    )


@pytest.mark.parametrize(
    "old,new",
    [
        ("năm 2024", "năm 2025"),
        ("Mã trường KSV", "Mã trường BVH"),
        ("đợt xét tuyển bổ sung", "đợt thông thường"),
        ("30/09/2024", "01/10/2024"),
        ("Mã ĐKXT", "Học phí"),
        ("Tổ hợp xét tuyển", "Chỉ tiêu"),
        ("<th>PT6</th>", "<th>PT4</th>"),
        ("elementor-widget-theme-post-content", "unrelated"),
    ],
)
def test_header_context_and_dom_mismatch_fail_closed(old, new):
    result, _ = parsed(body().decode().replace(old, new).encode())
    assert not candidates(result)


@pytest.mark.parametrize(
    "score_cell", ["<td></td>", "<td>—</td>", '<td rowspan="2">20</td>', '<td colspan="2">20</td>']
)
def test_blank_and_span_values_never_use_pt4_or_expand(score_cell):
    result, _ = parsed(body().decode().replace("<td>20</td>", score_cell, 1).encode())
    values = candidates(result)
    assert len(values) <= 5 and not any(
        c.value.value in (Decimal("42"), Decimal("100"), Decimal("600")) for c in values
    )


def test_binding_tamper_and_duplicate_business_root_are_blocked():
    result, _ = parsed()
    obs = raw(result.observations[0])
    fields = deepcopy(obs.raw_fields)
    fields["ueh_supplemental_2024"]["table_locator"] = "html:other"
    assert not normalize(obs.model_copy(update={"raw_fields": fields}), CTX).candidates
    duplicate = body() + body()
    assert not parsed(duplicate)[0].observations


@pytest.mark.parametrize(
    "old,new",
    [
        ("4. HƯỚNG DẪN XÁC NHẬN NHẬP HỌC", "Hướng dẫn khác"),
        ("Tiếng Anh thương mại (**)", "Tiếng Anh thương mại (*) (**)"),
        ("3.1.2. Phương thức xét điểm thi THPT.", "3.1.2. Phương thức PT4."),
    ],
)
def test_priority_boundary_and_conflicting_weight_markers_fail_closed(old, new):
    assert not parsed(body().decode().replace(old, new).encode())[0].observations


def test_august_september_scope_separation_and_actual_three_three_comparison():
    data = august_body().decode()
    old_names = [
        "Tiếng Anh thương mại (*)",
        "Thuế",
        "Công nghệ và đổi mới sáng tạo (*)",
        NAMES[3],
        "Kinh doanh nông nghiệp",
        NAMES[5],
    ]
    for i, name in enumerate(old_names):
        data = data.replace(f"Mẫu {i} (*)", name).replace(
            f"{19 + i}.25", "18.00" if i == 5 else "17.00"
        )
    old_result, _ = august_parsed(data.encode())
    old = [normalize(raw(o), AUGUST_CTX).candidates[0] for o in old_result.observations]
    new = candidates(parsed()[0])
    assert sum(a.value.value != b.value.value for a, b in zip(old, new)) == 3
    assert sum(a.value.value == b.value.value for a, b in zip(old, new)) == 3
    assert {c.candidate_key for c in old}.isdisjoint(c.candidate_key for c in new)
    inputs = [
        ResolutionInput(
            envelope_id=uuid4(),
            envelope=normalize(raw(o), AUGUST_CTX),
            final_url=old_result.observations[0].raw_fields["ueh_2024"]["source_url"],
            source_id=o.source_id,
        )
        for o in old_result.observations
    ]
    original = propose_registry(pending(), inputs)
    newer_inputs = [
        ResolutionInput(
            envelope_id=uuid4(),
            envelope=normalize(raw(o), CTX),
            final_url=URL,
            source_id=o.source_id,
        )
        for o in parsed()[0].observations
    ]
    combined = propose_registry(original, newer_inputs)
    hotel_old = resolve(inputs[5], combined).candidates[0]
    hotel_new = resolve(newer_inputs[5], combined).candidates[0]
    assert hotel_old.queries["program"] == hotel_new.queries["program"]
    assert hotel_old.lineage["scope_evidence"]["ueh_2024"]["round"]["value"] is None
    assert hotel_new.lineage["scope_evidence"]["ueh_supplemental_2024"]["round"]["proposed_key"]
    assert not hotel_new.publication_eligible
    assert all(e.canonical_id is None for e in combined.entities)


def test_postgres_new_pipeline_is_insert_only_and_packet_bound(db):
    result, ref = parsed()
    source = db.execute(
        metadata.tables["sources"]
        .insert()
        .values(
            canonical_url=URL,
            domain="tuyensinh.ueh.edu.vn",
            publisher="ueh",
            source_type="admission_office",
        )
        .returning(metadata.tables["sources"].c.id)
    ).scalar_one()
    snap = db.execute(
        metadata.tables["source_snapshots"]
        .insert()
        .values(
            source_id=source,
            raw_hash=ref.raw_hash,
            raw_uri="fixture://synthetic-supplemental",
            final_url=URL,
            media_type="text/html",
            byte_size=ref.byte_size,
        )
        .returning(metadata.tables["source_snapshots"].c.id)
    ).scalar_one()
    result.observations = [
        o.model_copy(
            update={
                "snapshot_id": snap,
                "source_id": source,
                "raw_fields": o.raw_fields
                | {
                    "ueh_supplemental_2024": o.raw_fields["ueh_supplemental_2024"]
                    | {"snapshot_id": str(snap)}
                },
            }
        )
        for o in result.observations
    ]
    names = [
        "cutoff_scores",
        "cutoff_evidence",
        "catalog_state",
        "audit_events",
        "dataset_releases",
    ]
    before = {n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in names}
    assert ObservationStore(db).save(result) == 6
    assert ObservationStore(db).save(result) == 0
    ids = list(
        db.execute(sa.select(observations.c.id).where(observations.c.snapshot_id == snap)).scalars()
    )
    ns = NormalizationStore(db)
    normal = ns.run(ids, CTX)
    assert normal["candidates"] == 6 and ns.replay(UUID(normal["job_id"]))["inserted"] == 0
    rs = ResolutionStore(db)
    resolution = rs.run(normal["job_id"], pending())
    assert resolution["candidates"] == 6 and rs.replay(resolution["job_id"])["inserted"] == 0
    rows = db.execute(
        sa.select(observations).where(
            observations.c.snapshot_id == snap,
            observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1",
        )
    ).mappings()
    for row in rows:
        c = row["normalized_fields"]["candidates"][0]
        packet = inspect_packet(db, row["id"], c["candidate_key"])
        assert checked_packet(db, binding_for(packet)) == packet
        assert not packet["resolution"]["publication_eligible"]
        assert packet["candidate"]["lineage"]["scope_evidence"]["ueh_supplemental_2024"]["round"][
            "proposed_key"
        ]
    assert before == {n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in names}
