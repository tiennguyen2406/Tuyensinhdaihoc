"""Synthetic DOM shaped like the authorized UEH fallback; no downloaded HTML in Git."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from bs4 import BeautifulSoup

from services.api.db.models import metadata, observations
from services.api.source_profiles import SourceProfile
from services.data.normalization.contract import NormalizationContext, RawObservation
from services.data.normalization.normalize import normalize
from services.data.normalization.store import NormalizationStore
from services.data.parsers.html import locate
from services.data.parsers.persistence import ObservationStore
from services.data.parsers.registry import extract
from services.data.resolution.contract import ResolutionInput
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.resolve import propose_registry, resolve
from services.data.resolution.store import ResolutionStore
from tests.parsers.helpers import snapshot

URL = "https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/"
CODES = ["7220201", "7340201_03", "7480201", "7480107", "7620114", "7810201"]
CTX = NormalizationContext(version="normalizer/ueh-2024-ksv/1.0.0")


def body():
    rows = "".join(
        f"<tr><td>{i}</td><td>{code}</td><td>Mẫu {i} (*)</td><td>900</td><td>80</td><td>81</td><td>850</td><td>A00, D01</td><td>{19 + i}.25</td></tr>"
        for i, code in enumerate(CODES)
    )
    return f"""<div class="elementor-widget-theme-post-content"><div class="elementor-widget-container">
    <p>Hội đồng tuyển sinh Đại học Kinh tế Thành phố Hồ Chí Minh (UEH) công bố kết quả trúng tuyển Khóa 50 – Đại học chính quy, năm 2024 của các phương thức:</p>
    <p>– Phương thức 6 (PT6): Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024.</p>
    <p>2. ĐIỂM TRÚNG TUYỂN</p>
    <p>– Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024 (PT6): Điểm trúng tuyển của từng chương trình đào tạo, cơ sở đào tạo bằng nhau giữa các tổ hợp xét tuyển và bằng nhau giữa các nguyện vọng.</p>
    <p>2.1. Đào tạo tại TP. Hồ Chí Minh (Mã trường KSA):</p>
    <table><tr><td>Điểm sàn</td><td>15</td></tr></table>
    <p>2.2. Đào tạo tại Vĩnh Long (Mã trường KSV):</p>
    <table><tr><td rowspan="2"><strong>Stt</strong></td><td rowspan="2"><strong>Mã đăng ký xét tuyển</strong></td><td rowspan="2"><strong>Chương trình đào tạo</strong></td><td rowspan="2"><strong>Tổng chỉ tiêu</strong></td><td><strong>PT3</strong></td><td><strong>PT4</strong></td><td><strong>PT5</strong></td><td colspan="2"><strong>PT6</strong></td></tr>
    <tr><td colspan="3"><strong>Điểm trúng tuyển</strong></td><td><strong>Tổ hợp xét tuyển</strong></td><td><strong>Điểm trúng tuyển</strong></td></tr>{rows}
    <tr><td colspan="9">Cộng: 600</td></tr></table>
    <p>Chương trình đào tạo (*): Đối với Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024 tổ hợp xét tuyển có bài thi/môn thi nhân hệ số 2, quy về thang điểm 30.</p>
    <p>UEH – Phân hiệu Vĩnh Long tiếp tục dành cơ hội cho thí sinh đợt xét tuyển bổ sung năm 2024.</p>
    <p>Ngưỡng nhận hồ sơ 18.00; chỉ tiêu 600.</p></div></div>""".encode()


def parsed(data=None):
    data = data or body()
    ref = snapshot(data).model_copy(update={"final_url": URL})
    profile = SourceProfile.model_validate_json(
        Path("config/sources/ueh-2024-fallback-20261019-v1.json").read_text(encoding="utf8")
    ).model_copy(update={"parser": "ueh_2024_html"})
    return extract(ref, profile, data, revision="ueh-test"), ref


def raw(obs):
    return RawObservation(id=uuid4(), **obs.model_dump())


def pending():
    return EntityRegistry.model_validate(
        dict(
            version="registry/ueh-test/1",
            alias_version="aliases/ueh-test/1",
            classification="pilot_pending",
            entities=[
                dict(
                    key="proposal:ueh",
                    kind="university",
                    name="UEH",
                    domains=["tuyensinh.ueh.edu.vn"],
                    attributes={"table_program_code_system": "ueh:admission-code"},
                    review={"evidence": ["fixture://ueh-host"]},
                ),
                dict(
                    key="proposal:ueh-pt6-2024",
                    kind="method",
                    name="UEH PT6 — Thi tốt nghiệp THPT năm 2024",
                    university_key="proposal:ueh",
                    attributes={"admission_year": 2024},
                    review={"evidence": ["fixture://method"]},
                ),
            ],
        )
    )


def test_six_physical_rows_exact_scores_and_locators():
    result, ref = parsed()
    assert len(result.observations) == 6
    soup = BeautifulSoup(body(), "html.parser")
    for i, obs in enumerate(result.observations):
        env = normalize(raw(obs), CTX)
        assert len(env.candidates) == 1
        c = env.candidates[0]
        assert c.scope["offering_code"]["display"] == CODES[i]
        assert c.value.value == Decimal(f"{19 + i}.25")
        assert c.lineage.raw_value == locate(soup, c.lineage.cell_locator).get_text()
        assert c.lineage.column == 8 and c.admission_year == 2024
        assert c.scope["campus"]["display"] == "KSV"
        assert c.scope["training_mode"]["display"] == "Chính quy"
        assert c.method.display == "UEH PT6 — Thi tốt nghiệp THPT năm 2024"
        assert c.round is c.population is c.conditions is c.score_scale is c.combinations is None
        evidence = c.lineage.scope_evidence["ueh_2024"]
        assert evidence["snapshot_sha256"] == ref.raw_hash
        assert evidence["round"]["value"] is None
        assert "bổ sung" not in evidence["campus"]["text"]
        assert "hệ số 2" in c.lineage.footnotes[0]["text"]
        assert "thang điểm 30" in evidence["scale"]["text"]
        assert evidence["weighted_subjects"] is evidence["weighted_formula"] is None


@pytest.mark.parametrize(
    "old,new",
    [
        ("năm 2024", "năm 2025"),
        ("Phương thức 6 (PT6)", "Phương thức 4 (PT4)"),
        ("Mã trường KSV", "Mã trường BVH"),
        ("2. ĐIỂM TRÚNG TUYỂN", "2. NGƯỠNG NHẬN HỒ SƠ"),
    ],
)
def test_missing_local_semantics_fail_closed(old, new):
    result, _ = parsed(body().decode().replace(old, new).encode())
    assert not result.observations
    assert result.issues


@pytest.mark.parametrize("replacement", ["", "<span></span>", "—"])
def test_blank_pt6_never_uses_pt4_or_quota(replacement):
    result, _ = parsed(body().replace(b"19.25", replacement.encode()))
    candidates = [c for o in result.observations for c in normalize(raw(o), CTX).candidates]
    assert len(candidates) == 5
    assert all(
        c.value.value not in (Decimal("81"), Decimal("900"), Decimal("600"), Decimal("18"))
        for c in candidates
    )


def test_score_span_reference_and_tampered_binding_do_not_emit():
    result, _ = parsed(
        body()
        .replace(b"<td>19.25</td>", b'<td rowspan="2">19.25</td>')
        .replace(b"<td>20.25</td>", b"")
    )
    candidates = [c for o in result.observations for c in normalize(raw(o), CTX).candidates]
    assert len(candidates) == 4
    result, _ = parsed()
    obs = raw(result.observations[0])
    fields = deepcopy(obs.raw_fields)
    fields["ueh_2024"]["table_locator"] = "html:other"
    env = normalize(obs.model_copy(update={"raw_fields": fields}), CTX)
    assert not env.candidates and env.issues


def test_footnotes_and_pending_identity_survive_t07_without_ptit_assumptions():
    result, _ = parsed()
    source = ResolutionInput(
        envelope_id=uuid4(),
        envelope=normalize(raw(result.observations[1]), CTX),
        final_url=URL,
        source_id=result.observations[1].source_id,
    )
    registry = propose_registry(pending(), [source])
    resolved = resolve(source, registry).candidates[0]
    assert resolved.lineage["footnotes"] == source.envelope.candidates[0].lineage.footnotes
    assert resolved.status == "unresolved" and not resolved.publication_eligible
    assert resolved.queries["offering"].code == "7340201_03"
    assert resolved.queries["offering"].code_system == "ueh:admission-code"
    assert resolved.queries["university"].code_system is None
    assert resolved.queries["method"].name.startswith("UEH PT6")
    assert resolved.entities["major"].canonical_id is None
    assert all(e.canonical_id is None for e in resolved.entities.values())


def test_total_row_document_issue_preserved_without_blocking_independent_score():
    result, _ = parsed()
    assert any(i.code == "cutoff_row_without_value" for i in result.issues)
    context = CTX.model_copy(update={"document_issues": [i.model_dump() for i in result.issues]})
    env = normalize(raw(result.observations[0]), context)
    assert len(env.candidates) == 1
    assert any(i.code == "cutoff_row_without_value" for i in env.issues)


@pytest.mark.parametrize(
    "header", ["Mã đăng ký xét tuyển", "Chương trình đào tạo", "Tổ hợp xét tuyển"]
)
def test_changed_identity_or_combination_header_cannot_be_positionally_mapped(header):
    result, _ = parsed(body().decode().replace(header, "Học phí").encode())
    assert not [c for o in result.observations for c in normalize(raw(o), CTX).candidates]


def test_postgres_pipeline_replay_and_business_state_preserved(db):
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
            raw_uri="fixture://ueh",
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
                | {"ueh_2024": o.raw_fields["ueh_2024"] | {"snapshot_id": str(snap)}},
            }
        )
        for o in result.observations
    ]
    before = {
        n: list(db.execute(sa.select(metadata.tables[n])).mappings())
        for n in ["cutoff_scores", "catalog_state", "dataset_releases", "audit_events"]
    }
    assert ObservationStore(db).save(result) == 6
    assert ObservationStore(db).save(result) == 0
    ids = list(
        db.execute(sa.select(observations.c.id).where(observations.c.snapshot_id == snap)).scalars()
    )
    first = NormalizationStore(db).run(ids, CTX)
    second = NormalizationStore(db).replay(__import__("uuid").UUID(first["job_id"]))
    assert first["candidates"] == 6 and second["inserted"] == 0 and second["cached"]
    rs = ResolutionStore(db).run(first["job_id"], pending())
    replay = ResolutionStore(db).replay(rs["job_id"])
    assert rs["candidates"] == 6 and replay["inserted"] == 0 and replay["cached"]
    for n, rows in before.items():
        assert list(db.execute(sa.select(metadata.tables[n])).mappings()) == rows
