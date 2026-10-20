"""Synthetic PTIT2026 layouts; real source validation is private and exhaustive."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa

from services.api.db.models import ingest_jobs, metadata, observations
from services.api.source_profiles import SourceProfile
from services.data.normalization.contract import NormalizationContext
from services.data.normalization.normalize import normalize
from services.data.normalization.store import NormalizationStore
from services.data.parsers.contract import ParseLimits
from services.data.parsers.persistence import ObservationStore
from services.data.parsers.registry import extract
from services.data.publication.packets import binding_for, checked_packets, inspect_packet
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.store import ResolutionStore
from tests.normalization.test_ueh import raw
from tests.parsers.helpers import snapshot

URL = "https://tuyensinh.ptit.edu.vn/thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2026/"
CTX = NormalizationContext(version="normalizer/ptit-2026-multimethod/1.0.1")


def body():
    head = """<tr><td rowspan=3>TT</td><td rowspan=3>Tên ngành, chương trình</td><td rowspan=3>Mã xét tuyển</td><td colspan=9>Điểm chuẩn trúng tuyển</td><td colspan=2 rowspan=2>Tiêu chí phụ (*)</td></tr>
    <tr><td rowspan=2>Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2026 (thang 30)</td><td rowspan=2>Phương thức xét tuyển dựa vào hồ sơ năng lực (xét tuyển tài năng) (thang 100)</td><td colspan=2>Xét tuyển dựa vào kết quả Chứng chỉ đánh giá năng lực quốc tế</td><td colspan=4>Xét tuyển dựa vào kết quả trong các kỳ thi ĐGNL, ĐGTD</td><td rowspan=2>Phương thức xét tuyển Kết hợp (thang 30)</td></tr>
    <tr><td>Chứng chỉ SAT (thang 1600)</td><td>Chứng chỉ ACT (thang 36)</td><td>Bài thi TSA (thang 100)</td><td>Bài thi HSA (thang 150)</td><td>Bài thi V-ACT (thang 1200)</td><td>Bài thi SPT (thang 30)</td><td>Điểm cộng</td><td>TTNV</td></tr>"""
    tables = []
    for campus, region in [("BVH", "BẮC"), ("BVS", "NAM")]:
        values = [
            "26.35",
            "82.50",
            "1234.56",
            "27.34",
            "73.50",
            "102.75",
            "910.25",
            "24.25",
            "26.40",
        ]
        rows = "<tr><td>I</td><td colspan=13>NGÀNH/CHƯƠNG TRÌNH ĐÀO TẠO ĐẠI TRÀ</td></tr>"
        rows += (
            "<tr><td>1</td><td>Công nghệ thông tin</td><td>7480201 CLC</td>"
            + "".join("<td>" + v + "</td>" for v in values)
            + "<td>ĐC&lt;=1.5</td><td>≤3</td></tr>"
        )
        rows += "<tr><td>III</td><td colspan=13>CHƯƠNG TRÌNH ĐÀO TẠO TÀI NĂNG – THẠC SĨ TÍCH HỢP CỬ NHÂN</td></tr>"
        rows += (
            "<tr><td>1</td><td>Khoa học máy tính tích hợp</td><td>8480104 TN</td><td>27.20</td>"
            + "<td>–</td>" * 8
            + "<td>–</td><td>=2</td></tr>"
        )
        tables.append(
            f"<ol>CƠ SỞ ĐÀO TẠO PHÍA {region} (mã {campus})</ol><table>{head}{rows}</table>"
        )
    return (
        '<article class="post-wrap"><h1>Thông báo Điểm chuẩn trúng tuyển vào đại học hệ chính quy năm 2026</h1><ul><li><span>10/08/2026</span></li></ul><p>Học viện Công nghệ Bưu chính Viễn thông thông báo điểm chuẩn trúng tuyển năm 2026 và kế hoạch xác nhận nhập học, nhập học như sau:</p><p>I. ĐIỂM CHUẨN TRÚNG TUYỂN :</p>'
        + "".join(tables)
        + "<p>(*) trường hợp nhiều thí sinh có cùng điểm xét ở cuối danh sách, thứ tự xét ưu tiên đối với các thí sinh có điểm cộng thấp hơn; trường hợp có điểm cộng bằng nhau, ưu tiên nguyện vọng cao hơn.</p></article>"
    ).encode()


def parsed(data=None):
    data = data or body()
    p = SourceProfile(
        profile_id="synthetic-ptit2026",
        university_key="ptit",
        allowed_hosts=["tuyensinh.ptit.edu.vn"],
        seed_urls=[URL],
        years=[2026],
        authority_scope={"years": [2026]},
        parser="ptit_2026_multimethod_html",
    )
    ref = snapshot(data).model_copy(update={"final_url": URL})
    return extract(ref, p, data), ref


def candidates(result):
    return [c for o in result.observations for c in normalize(raw(o), CTX).candidates]


def test_resource_failure_never_succeeds_with_partial_campus():
    from services.data.parsers.ptit_2026 import parse_ptit_2026

    data = body()
    p = SourceProfile.model_validate_json(
        Path("config/sources/ptit-2026-multimethod-parser-20261020-v1.json").read_text(
            encoding="utf8"
        )
    )
    ref = snapshot(data).model_copy(update={"final_url": URL})
    out = parse_ptit_2026(ref, p, data, limits=ParseLimits(max_cells=100))
    assert out.issues and any(i.severity == "error" for i in out.issues)
    assert not out.observations


def test_two_campuses_nine_instruments_and_integrated_rows():
    result, _ = parsed()
    cs = candidates(result)
    assert len(result.observations) == 4 and len(cs) == 20
    assert len(result.metadata["method_cell_ledger"]) == 36
    assert (
        sum(e["status"] == "not_a_cutoff_value" for e in result.metadata["method_cell_ledger"])
        == 16
    )
    assert {c.scope["campus"]["display"] for c in cs} == {"BVH", "BVS"}
    assert len({c.method.display for c in cs}) == 9
    for c in cs:
        assert (
            c.admission_year == 2026
            and c.round is c.population is c.conditions is c.score_scale is c.combinations is None
        )
        assert c.scope["offering_code"]["raw"] in ["7480201 CLC", "8480104 TN"]
        assert not c.entity_ids and c.verification_status == "unverified"
        m = c.lineage.scope_evidence["score_method"]
        assert m["family"] and m["nominal_scale"] and m["automatic_applicant_comparison"] is False
        assert c.lineage.header_path[0]["text"] == "Điểm chuẩn trúng tuyển"
    assert next(
        c for c in cs if c.lineage.scope_evidence["score_method"]["key"] == "SAT"
    ).value.value == Decimal("1234.56")
    assert next(
        c for c in cs if c.lineage.scope_evidence["score_method"]["key"] == "ACT"
    ).value.value == Decimal("27.34")


def test_bonus_ttnv_operators_are_evidence_only():
    result, _ = parsed()
    cs = candidates(result)
    assert all(c.lineage.column not in [12, 13] for c in cs)
    t = cs[0].lineage.scope_evidence["tie_break"]
    assert t["bonus"]["operator"] == "<=" and t["bonus"]["raw_text"] == "ĐC<=1.5"
    assert t["TTNV"]["operator"] == "≤"
    assert t["executable"] is False
    assert (
        next(
            c for c in cs if c.scope["offering_code"]["raw"] == "8480104 TN"
        ).lineage.scope_evidence["tie_break"]["bonus"]["operator"]
        is None
    )


@pytest.mark.parametrize(
    "old,new",
    [
        (b"2026", b"2025"),
        (b"10/08/2026", b"11/08/2026"),
        ("THPT năm 2026".encode(), b"THPT unknown"),
    ],
)
def test_wrong_year_date_or_method_fails_closed(old, new):
    assert not candidates(parsed(body().replace(old, new))[0])


def test_wrong_campus_blocks_one_group_only():
    result, _ = parsed(body().replace("(mã BVH)".encode(), b"(unknown)"))
    assert len(candidates(result)) == 10
    assert all(c.scope["campus"]["display"] == "BVS" for c in candidates(result))


@pytest.mark.parametrize("value", ["", "–", "bad", "-1"])
def test_missing_invalid_scores_keep_complete_ledger(value):
    result, _ = parsed(body().replace(b"<td>1234.56</td>", ("<td>" + value + "</td>").encode(), 1))
    assert len(candidates(result)) == 19 and len(result.metadata["method_cell_ledger"]) == 36


def test_physical_rebinding_and_spans_rejected():
    result, _ = parsed()
    o = result.observations[0]
    f = deepcopy(o.raw_fields)
    f["cells"][5] = f["cells"][3] | {"column": 5}
    out = normalize(raw(o.model_copy(update={"raw_fields": f})), CTX)
    assert len(out.candidates) == 8 and all(c.lineage.column != 5 for c in out.candidates)
    result, _ = parsed(
        body().replace(b"<td>1234.56</td><td>27.34</td>", b"<td colspan=2>1234.56</td>", 1)
    )
    assert len(candidates(result)) == 18


def test_context_not_new_round_or_correction_and_no_fanout():
    cs = candidates(parsed()[0])
    assert len({c.candidate_key for c in cs}) == 20
    assert all(c.scope["track"] and c.scope["language"] is None for c in cs)
    assert all("2024" not in c.method.display and "UEH" not in c.method.display for c in cs)


def test_postgres_batch_replay_packets_and_business_preservation(db):
    from services.data.parsers.ptit_2026 import METHODS

    data = body()
    result, ref = parsed(data)
    source = db.scalar(
        metadata.tables["sources"]
        .insert()
        .values(
            canonical_url=URL,
            domain="tuyensinh.ptit.edu.vn",
            publisher="ptit",
            source_type="admission_office",
        )
        .returning(metadata.tables["sources"].c.id)
    )
    snap = db.scalar(
        metadata.tables["source_snapshots"]
        .insert()
        .values(
            source_id=source,
            raw_hash=ref.raw_hash,
            raw_uri="fixture://synthetic-ptit2026",
            final_url=URL,
            media_type="text/html",
            byte_size=len(data),
        )
        .returning(metadata.tables["source_snapshots"].c.id)
    )
    obs = [
        o.model_copy(
            update={
                "snapshot_id": snap,
                "source_id": source,
                "raw_fields": o.raw_fields
                | {"ptit_2026": o.raw_fields["ptit_2026"] | {"snapshot_id": str(snap)}},
            }
        )
        for o in result.observations
    ]
    business = [
        "universities",
        "programs",
        "program_years",
        "cutoff_scores",
        "audit_events",
        "catalog_state",
        "dataset_releases",
    ]
    before = {n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business}
    result = result.model_copy(update={"observations": obs})
    assert ObservationStore(db).save(result) == 4 and ObservationStore(db).save(result) == 0
    ids = list(db.scalars(sa.select(observations.c.id).where(observations.c.snapshot_id == snap)))
    assert len(ids) == 4
    n = NormalizationStore(db).run(ids, CTX)
    assert (
        n["candidates"] == 20 and NormalizationStore(db).replay(UUID(n["job_id"]))["inserted"] == 0
    )
    evidence = ["fixture://synthetic-ptit2026-methods"]
    seed = EntityRegistry.model_validate(
        dict(
            version="registry/ptit2026-test/1",
            alias_version="aliases/ptit2026-test/1",
            classification="pilot_pending",
            entities=[
                dict(
                    key="proposal:ptit",
                    kind="university",
                    name="PTIT",
                    domains=["tuyensinh.ptit.edu.vn"],
                    review=dict(evidence=evidence),
                )
            ]
            + [
                dict(
                    key="proposal:ptit2026:" + m,
                    kind="method",
                    name="PTIT 2026 — " + v[0],
                    university_key="proposal:ptit",
                    attributes=dict(admission_year=2026),
                    review=dict(evidence=evidence),
                )
                for m, v in METHODS.items()
            ],
        )
    )
    r = ResolutionStore(db).run(n["job_id"], seed)
    assert r["candidates"] == 20 and ResolutionStore(db).replay(r["job_id"])["inserted"] == 0
    compiled = db.scalar(sa.select(ingest_jobs.c.payload).where(ingest_jobs.c.id == r["job_id"]))[
        "registry"
    ]
    assert sum(e["kind"] == "program" for e in compiled["entities"]) == 4
    rows = db.execute(
        sa.select(observations).where(
            observations.c.snapshot_id == snap,
            observations.c.normalized_fields["registry_version"].astext == r["registry_version"],
        )
    ).mappings()
    packets = [
        inspect_packet(db, row["id"], c["candidate_key"])
        for row in rows
        for c in row["normalized_fields"]["candidates"]
    ]
    assert len(packets) == 20 and checked_packets(db, [binding_for(p) for p in packets]) == packets
    assert all(not p["resolution"]["publication_eligible"] for p in packets)
    assert before == {
        n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business
    }
