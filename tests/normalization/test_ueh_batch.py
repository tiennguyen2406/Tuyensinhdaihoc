"""Synthetic three-layout UEH appendix; real snapshot is validated privately in full."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from uuid import UUID

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
from services.data.parsers.ueh_batch import logical_id
from services.data.publication.packets import binding_for, checked_packet, inspect_packet
from services.data.resolution.store import ResolutionStore
from tests.normalization.test_ueh import pending, raw
from tests.parsers.helpers import snapshot

CTX = NormalizationContext(version="normalizer/ueh-2024-pt6-batch/1.0.0")


def table(isb=False, ksv=False):
    methods = ["PT3", "PT4"] + ([] if isb else ["PT5"])
    first = "".join(
        f'<td rowspan="2"><strong>{h}</strong></td>'
        for h in [
            "Stt",
            "Mã ĐKXT" if isb else "Mã đăng ký xét tuyển",
            "Chương trình đào tạo",
            "Tổng chỉ tiêu",
        ]
    )
    first += "".join(f"<td><strong>{h}</strong></td>" for h in methods)
    first += '<td colspan="2"><strong>PT6</strong></td>'
    if not isb:
        first += '<td colspan="3"><strong>Chương trình học</strong></td>'
    second = f'<td colspan="{len(methods)}"><strong>Điểm trúng tuyển</strong></td><td><strong>Tổ hợp xét tuyển</strong></td><td><strong>Điểm trúng tuyển</strong></td>'
    if not isb:
        second += "".join(
            f"<td><strong>{v}</strong></td>"
            for v in [
                "Tiếng Anh toàn phần",
                "Tiếng Anh bán phần",
                "Chương trình tiếng Việt" if ksv else "Tiếng Việt",
            ]
        )
    rows = (
        [
            ("ISB_CNTN", "Cử nhân Tài năng ISB BBus", "27.15"),
            ("ASA_Co-op", "Cử nhân ISB ASEAN Co-op", "25.30"),
        ]
        if isb
        else [
            ("7220201", "Tiếng Anh thương mại (*)", "17.00" if ksv else "26.30"),
            ("7340201_03", "Thuế", "18.00" if ksv else "26.50"),
        ]
    )
    data = ""
    for i, (code, name, value) in enumerate(rows, 1):
        cells = (
            [str(i), code, name, "900"] + ["88.00"] * len(methods) + ["A00, A01, D01, D07", value]
        )
        if not isb:
            cells += ["√", "√", "√"]
        data += "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
    total = ["", "", "Cộng:", "1800"] + [""] * (4 if isb else 8)
    data += "<tr>" + "".join(f"<td>{c}</td>" for c in total) + "</tr>"
    return f"<table><thead><tr>{first}</tr><tr>{second}</tr></thead><tbody>{data}</tbody></table>"


def body():
    note = "Chương trình đào tạo (*): Đối với Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024 tổ hợp xét tuyển có bài thi/môn thi nhân hệ số 2, quy về thang điểm 30."
    return f"""<div class="elementor-widget-post-info"><span itemprop="datePublished"><time>17/08/2024</time></span></div>
    <div class="elementor-widget-theme-post-content"><div class="elementor-widget-container">
    <p>Cơ quan báo chí đưa tin:</p><table><tr><td>Điểm chuẩn: 28</td></tr></table>
    <p>Hội đồng tuyển sinh Đại học Kinh tế Thành phố Hồ Chí Minh (UEH) công bố kết quả trúng tuyển Khóa 50 – Đại học chính quy, năm 2024 của các phương thức:</p>
    <p>– Phương thức 6 (PT6): Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024.</p>
    <p>2. ĐIỂM TRÚNG TUYỂN</p>
    <p>– Phương thức xét tuyển dựa vào kết quả thi tốt nghiệp THPT năm 2024 (PT6): Điểm trúng tuyển của từng chương trình đào tạo, cơ sở đào tạo bằng nhau giữa các tổ hợp xét tuyển và bằng nhau giữa các nguyện vọng.</p>
    <p>2.1. Đào tạo tại TP. Hồ Chí Minh (Mã trường KSA):</p>
    <p>1. Chương trình tiếng Việt, Chương trình tiếng Anh toàn phần, tiếng Anh bán phần</p>
    {table()}<p>{note}</p><ol><li>Chương trình Cử nhân tài năng, Asean Co-op</li></ol>{table(isb=True)}
    <p>2.2. Đào tạo tại Vĩnh Long (Mã trường KSV):</p>{table(ksv=True)}<p>{note}</p>
    <p>Ngưỡng nhận hồ sơ 18.00; chỉ tiêu 600.</p></div></div>""".encode()


def parsed(data=None):
    data = data or body()
    profile = SourceProfile.model_validate_json(
        Path("config/sources/ueh-2024-ksv-fallback-parser-20261019-v1.json").read_text(
            encoding="utf8"
        )
    ).model_copy(update={"parser": "ueh_2024_pt6_batch_html"})
    ref = snapshot(data).model_copy(update={"final_url": str(profile.seed_urls[0])})
    return extract(ref, profile, data, revision="batch-test"), ref


def candidates(result):
    return [c for o in result.observations for c in normalize(raw(o), CTX).candidates]


def test_three_groups_all_physical_rows_not_methods_combinations_or_languages():
    result, _ = parsed()
    values = candidates(result)
    assert len(result.observations) == len(values) == 6
    assert [v.value.value for v in values] == [
        Decimal(v) for v in ("26.30", "26.50", "27.15", "25.30", "17.00", "18.00")
    ]
    assert [v.scope["campus"]["display"] for v in values] == ["KSA"] * 4 + ["KSV"] * 2
    assert [v.scope["offering_code"]["display"] for v in values][2:4] == ["ISB_CNTN", "ASA_Co-op"]
    assert all(v.scope["track"] is v.scope["language"] is None for v in values)
    assert all(
        v.admission_year == 2024 and "PT6" in v.method.display and v.round is None for v in values
    )
    ledger = result.metadata["row_ledger"]
    assert len(ledger) == 9 and sum(r["status"] == "non_cutoff_row" for r in ledger) == 3
    assert len({r["row_locator"] for r in ledger}) == 9
    soup = BeautifulSoup(body(), "html.parser")
    for c in values:
        assert locate(soup, c.lineage.cell_locator).get_text() == c.lineage.raw_value
        assert c.lineage.header_path[-1]["text"] == "Điểm trúng tuyển"


def test_notes_are_section_local_and_only_starred_rows_claim_weight():
    values = candidates(parsed()[0])
    for i, c in enumerate(values):
        mapping = c.lineage.scope_evidence["ueh_batch_2024"]
        assert bool(mapping["weighting"]) == (i in (0, 4))
        if mapping["weighting"]:
            assert mapping["weighting"]["subject"] is None
            assert mapping["weighting"]["formula"] is None
            assert "30" in mapping["weighting"]["note"]["text"]
        if i in (2, 3):
            assert not c.lineage.footnotes and mapping["section_note"] is None


@pytest.mark.parametrize(
    "old,new",
    [
        ("năm 2024 của", "năm 2025 của"),
        ("(PT6): Phương thức", "(PT5): Phương thức"),
        ("17/08/2024", "30/09/2024"),
    ],
)
def test_missing_global_year_method_or_august_context_fails_closed(old, new):
    assert not candidates(parsed(body().decode().replace(old, new).encode())[0])


def test_bad_isb_layout_does_not_drop_ksa_ksv():
    data = body().decode().replace("Mã ĐKXT", "Chỉ tiêu")
    result, _ = parsed(data.encode())
    assert len(candidates(result)) == 4
    blocked = [r for r in result.metadata["row_ledger"] if r["status"] == "needs_review_or_blocked"]
    assert len(blocked) == 2 and all(r["reason"] for r in blocked)


@pytest.mark.parametrize("replacement", ["", "N/A", "<span>?</span>"])
def test_blank_or_non_numeric_score_not_filled_from_other_methods(replacement):
    data = body().decode().replace("<td>26.30</td>", f"<td>{replacement}</td>")
    result, _ = parsed(data.encode())
    assert len(candidates(result)) == 5
    assert any(r["status"] == "needs_review_or_blocked" for r in result.metadata["row_ledger"])


def test_score_span_does_not_generate_a_value():
    data = body().decode().replace("<td>26.30</td><td>√</td>", '<td colspan="2">26.30</td>')
    result, _ = parsed(data.encode())
    assert not any(c.value.value == Decimal("26.30") for c in candidates(result))


def test_unrecognized_weight_note_does_not_claim_factor_two():
    data = body().decode().replace("nhân hệ số 2", "nhân hệ số 3")
    cs = candidates(parsed(data.encode())[0])
    assert len(cs) == 6
    for c in cs:
        mapping = c.lineage.scope_evidence["ueh_batch_2024"]
        if "(*)" in c.scope["program_name"]["display"]:
            assert mapping["weighting"]["factor"] is None
            assert "hệ số 3" in mapping["weighting"]["note"]["text"]


def test_logical_id_excludes_transform_but_distinguishes_campus_and_notice():
    result, ref = parsed()
    c = candidates(result)[0]
    args = (ref, c.lineage.cell_locator, "7220201", "KSA", "2024-08-17")
    assert logical_id(*args) == logical_id(*args)
    assert logical_id(*args) != logical_id(
        ref, c.lineage.cell_locator, "7220201", "KSV", "2024-08-17"
    )
    assert logical_id(*args) != logical_id(
        ref, c.lineage.cell_locator, "7220201", "KSA", "2024-09-30"
    )


def test_normalizer_rejects_tampered_header_and_binding():
    obs = parsed()[0].observations[0]
    fields = deepcopy(obs.raw_fields)
    fields["headers"][8][-1]["text"] = "PT4"
    assert not normalize(raw(obs.model_copy(update={"raw_fields": fields})), CTX).candidates
    fields = deepcopy(obs.raw_fields)
    fields["ueh_batch_2024"]["campus"] = "BVS"
    assert not normalize(raw(obs.model_copy(update={"raw_fields": fields})), CTX).candidates


def test_batch_dispatch_preserves_raw_only_guard():
    obs = raw(parsed()[0].observations[0]).model_copy(
        update={"normalized_fields": {"already": True}}
    )
    with pytest.raises(ValueError, match="raw-only"):
        normalize(obs, CTX)


def test_narrative_ksv_mention_is_not_a_campus_boundary():
    data = (
        body()
        .decode()
        .replace("<p>2.1.", "<p>Thông tin Mã trường KSV trong bài giới thiệu.</p><p>2.1.")
    )
    assert len(candidates(parsed(data.encode())[0])) == 6


def test_missing_isb_section_keeps_rows_in_blocked_accounting():
    data = (
        body()
        .decode()
        .replace("Chương trình Cử nhân tài năng, Asean Co-op", "Unrecognized section")
    )
    result, _ = parsed(data.encode())
    assert len(candidates(result)) == 4
    ledger = result.metadata["row_ledger"]
    assert len(ledger) == 9 and sum(r["status"] == "needs_review_or_blocked" for r in ledger) == 2


def test_postgres_batch_replay_and_packet_membership(db):
    result, ref = parsed()
    source = db.execute(
        metadata.tables["sources"]
        .insert()
        .values(
            canonical_url=ref.final_url,
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
            raw_uri="fixture://synthetic-ueh-batch",
            final_url=ref.final_url,
            media_type="text/html",
            byte_size=ref.byte_size,
        )
        .returning(metadata.tables["source_snapshots"].c.id)
    ).scalar_one()
    for i, obs in enumerate(result.observations):
        fields = deepcopy(obs.raw_fields)
        mapping = fields["ueh_batch_2024"]
        mapping["snapshot_id"] = str(snap)
        score = fields["cells"][7 if mapping["group"] == "ksa_isb" else 8]
        mapping["logical_id"] = logical_id(
            ref.model_copy(update={"snapshot_id": snap}),
            score["origin"],
            fields["cells"][1]["text"],
            mapping["campus"],
            "2024-08-17",
        )
        result.observations[i] = obs.model_copy(
            update={"snapshot_id": snap, "source_id": source, "raw_fields": fields}
        )
    business = [
        "cutoff_scores",
        "cutoff_evidence",
        "catalog_state",
        "audit_events",
        "dataset_releases",
    ]
    before = {n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business}
    assert ObservationStore(db).save(result) == 6
    assert ObservationStore(db).save(result) == 0
    ids = list(db.scalars(sa.select(observations.c.id).where(observations.c.snapshot_id == snap)))
    normal = NormalizationStore(db).run(ids, CTX)
    assert (
        normal["candidates"] == 6
        and NormalizationStore(db).replay(UUID(normal["job_id"]))["inserted"] == 0
    )
    resolved = ResolutionStore(db).run(normal["job_id"], pending())
    assert (
        resolved["candidates"] == 6
        and ResolutionStore(db).replay(resolved["job_id"])["inserted"] == 0
    )
    rows = db.execute(
        sa.select(observations).where(
            observations.c.snapshot_id == snap,
            observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1",
        )
    ).mappings()
    packets = [
        inspect_packet(db, r["id"], r["normalized_fields"]["candidates"][0]["candidate_key"])
        for r in rows
    ]
    assert len(packets) == 6
    assert all(
        checked_packet(db, binding_for(p)) == p and not p["resolution"]["publication_eligible"]
        for p in packets
    )
    assert before == {
        n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business
    }
