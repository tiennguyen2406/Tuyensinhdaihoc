"""Synthetic historical archive; actual41-row source is validated privately."""

from copy import deepcopy
from decimal import Decimal
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

URL = "https://tuyensinh.ptit.edu.vn/gioi-thieu/xem-diem-cac-nam-truoc/diem-trung-tuyen-nam-2025/"
CTX = NormalizationContext(version="normalizer/ptit-2025-historical/1.0.0")
CODES = ["7520207_ AIoT", "7340101_ LOG", "7480201_ CLC", "7480201 _UDU", "7480201_CLC"]


def body():
    header = "<tr><td>TT</td><td>Tên ngành, chương trình</td><td>Mã ngành, chương trình</td><td>Điểm chuẩn trúng tuyển</td><td>Thứ tự nguyện vọng (TTNV) trúng tuyển khi thí sinh có điểm xét tuyển bằng mức điểm trúng tuyển (*)</td></tr>"
    tables = []
    for campus, region, indices in [("BVH", "BẮC", [0, 1, 2]), ("BVS", "NAM", [3, 4])]:
        rows = "<tr><td>I</td><td colspan=4>NGÀNH, CHƯƠNG TRÌNH ĐÀO TẠO ĐẠI TRÀ</td></tr>"
        for i in indices:
            if i == indices[-1]:
                rows += "<tr><td>II</td><td colspan=4>CHƯƠNG TRÌNH CHẤT LƯỢNG CAO</td></tr>"
            predicate = ["TTNV=1", "TTNV&lt;=2", "TTNV&lt;=13", "TTNV=1", "TTNV&lt;=20"][i]
            rows += f"<tr><td>{i + 1}</td><td>Chương trình {i}</td><td>{CODES[i]}</td><td>25.10</td><td>{predicate}</td></tr>"
        tables.append(
            f"<ol><li>CƠ SỞ ĐÀO TẠO PHÍA {region} (mã {campus})</li></ol><table>{header}{rows}</table>"
        )
    return (
        '<h1>Điểm trúng tuyển 2025</h1><div class="elementor-5168"><div class="elementor-widget-text-editor"><div class="elementor-widget-container">'
        + "".join(tables)
        + "</div></div></div>"
    ).encode()


def parsed(data=None, **kwargs):
    data = data or body()
    p = SourceProfile(
        profile_id="synthetic-ptit2025",
        university_key="ptit",
        allowed_hosts=["tuyensinh.ptit.edu.vn"],
        seed_urls=[URL],
        years=[2025],
        authority_scope={"years": [2025]},
        parser="ptit_2025_historical_html",
    )
    ref = snapshot(data).model_copy(update={"final_url": URL})
    return extract(ref, p, data, **kwargs), ref


def candidates(out):
    return [c for o in out.observations for c in normalize(raw(o), CTX).candidates]


def test_archive_five_scores_not_nine_methods_and_raw_code_precision():
    out, _ = parsed()
    cs = candidates(out)
    assert len(out.observations) == len(cs) == 5 and len(out.metadata["score_cell_ledger"]) == 5
    assert {c.scope["offering_code"]["raw"] for c in cs} == set(CODES)
    assert {c.scope["campus"]["display"] for c in cs} == {"BVH", "BVS"}
    for c in cs:
        assert (
            c.method
            is c.score_scale
            is c.round
            is c.population
            is c.conditions
            is c.combinations
            is None
        )
        assert c.admission_year == 2025 and c.value.value == Decimal("25.10")
        assert c.scope["training_mode"] is None and c.scope["language"] is None
        assert c.lineage.scope_evidence["archive"]["publication_date"]["precision"] == "unknown"
        assert not c.entity_ids and c.verification_status == "unverified"


def test_ttnv_equality_inequality_and_equal_score_scope_preserved():
    cs = candidates(parsed()[0])
    t = [c.lineage.scope_evidence["TTNV"] for c in cs]
    assert [(e["operator"], e["bound"]) for e in t] == [
        ("=", 1),
        ("<=", 2),
        ("<=", 13),
        ("=", 1),
        ("<=", 20),
    ]
    assert all("bằng mức điểm trúng tuyển" in e["header_path"][0]["text"] for e in t)
    assert all(e["executable"] is False for e in t)


@pytest.mark.parametrize("year", ["2024", "2026"])
def test_archive_title_year_never_inferred_from_other_notices(year):
    assert not candidates(parsed(body().replace(b"2025", year.encode()))[0])


def test_broken_campus_only_blocks_its_group():
    out, _ = parsed(body().replace("(mã BVH)".encode(), b"(unknown)"))
    assert len(candidates(out)) == 2
    assert len(out.metadata["score_cell_ledger"]) == 5
    assert all(c.scope["campus"]["display"] == "BVS" for c in candidates(out))


@pytest.mark.parametrize("replacement", ["", "–", "not a score", "-1"])
def test_blank_invalid_score_cells_fail_closed_and_ledger_complete(replacement):
    out, _ = parsed(body().replace(b"<td>25.10</td>", ("<td>" + replacement + "</td>").encode(), 1))
    assert len(candidates(out)) == 4 and len(out.metadata["score_cell_ledger"]) == 5


def test_score_origin_spans_and_tampered_mapping_do_not_create_candidates():
    out, _ = parsed()
    o = out.observations[0]
    f = deepcopy(o.raw_fields)
    f["cells"][3] = f["cells"][4] | {"column": 3}
    assert not normalize(raw(o.model_copy(update={"raw_fields": f})), CTX).candidates
    out, _ = parsed(
        body().replace(b"<td>25.10</td><td>TTNV=1</td>", b"<td colspan=2>25.10</td>", 1)
    )
    assert len(candidates(out)) == 4


def test_unusual_ttnv_keeps_score_and_review_issue_without_guess():
    cs = candidates(parsed(body().replace(b"TTNV=1", b"unknown", 1))[0])
    assert len(cs) == 5 and cs[0].lineage.scope_evidence["TTNV"]["operator"] is None
    assert any(i.code == "PTIT2025_TTNV_REVIEW" for i in cs[0].issues)


def test_resource_failure_propagates_and_no_partial_campus():
    out, _ = parsed(limits=ParseLimits(max_cells=45))
    assert not out.observations and any(i.severity == "error" for i in out.issues)
    assert len(out.metadata["score_cell_ledger"]) == 5


def test_unrelated_table_is_accounted_without_extra_score():
    data = body().replace(
        b"</div></div></div>",
        b"<table><tr><td>Quota</td><td>Year</td></tr><tr><td>500</td><td>2025</td></tr></table></div></div></div>",
    )
    out, _ = parsed(data)
    assert len(candidates(out)) == 5 and len(out.metadata["score_cell_ledger"]) == 5
    assert any(r["classification"] == "unrelated" for r in out.metadata["physical_row_ledger"])


def test_supporting_urls_cannot_emit_archive_cutoffs_and_hash_tamper_rejected():
    data = body()
    _, ref = parsed()
    p = SourceProfile(
        profile_id="wrong-source",
        university_key="ptit",
        allowed_hosts=["tuyensinh.ptit.edu.vn"],
        seed_urls=[URL],
        years=[2025],
        authority_scope={},
        parser="ptit_2025_historical_html",
    )
    for path in [
        "thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2025/",
        "diem-trung-tuyen-cac-phuong-thuc-xet-tuyen-dai-hoc-he-chinh-quy-dot-1-nam-2025/",
    ]:
        assert not extract(
            ref.model_copy(update={"final_url": "https://tuyensinh.ptit.edu.vn/" + path}), p, data
        ).observations
    with pytest.raises(ValueError, match="hash"):
        extract(ref.model_copy(update={"raw_hash": "0" * 64}), p, data)


def test_postgres_nullable_method_packets_replay_and_no_crossyear_merge(db):
    out, ref = parsed()
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
            raw_uri="fixture://synthetic-ptit2025",
            final_url=URL,
            media_type="text/html",
            byte_size=ref.byte_size,
        )
        .returning(metadata.tables["source_snapshots"].c.id)
    )
    obs = [
        o.model_copy(
            update={
                "snapshot_id": snap,
                "source_id": source,
                "raw_fields": o.raw_fields
                | {"ptit_2025": o.raw_fields["ptit_2025"] | {"snapshot_id": str(snap)}},
            }
        )
        for o in out.observations
    ]
    business = [
        "universities",
        "programs",
        "program_years",
        "cutoff_scores",
        "catalog_state",
        "audit_events",
        "dataset_releases",
    ]
    before = {n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business}
    out = out.model_copy(update={"observations": obs})
    assert ObservationStore(db).save(out) == 5 and ObservationStore(db).save(out) == 0
    ids = list(db.scalars(sa.select(observations.c.id).where(observations.c.snapshot_id == snap)))
    assert len(ids) == 5
    n = NormalizationStore(db).run(ids, CTX)
    assert (
        n["candidates"] == 5 and NormalizationStore(db).replay(UUID(n["job_id"]))["inserted"] == 0
    )
    seed = EntityRegistry.model_validate(
        dict(
            version="registry/ptit2025-test/1",
            alias_version="aliases/ptit2025-test/1",
            classification="pilot_pending",
            entities=[
                dict(
                    key="proposal:ptit",
                    kind="university",
                    name="PTIT",
                    domains=["tuyensinh.ptit.edu.vn"],
                    review=dict(evidence=["fixture://synthetic"]),
                )
            ],
        )
    )
    frozen = seed.frozen()
    for year in [2024, 2026]:
        pk = f"proposal:prior-program:{year}"
        frozen["entities"] += [
            dict(
                key=pk,
                kind="program",
                name="Chương trình 0",
                university_key="proposal:ptit",
                attributes=dict(admission_year=year, campus="BVH"),
                review=dict(evidence=["fixture://cross-year"]),
            ),
            dict(
                key=f"proposal:prior-offering:{year}",
                kind="offering",
                name="Chương trình 0",
                university_key="proposal:ptit",
                program_key=pk,
                attributes=dict(admission_year=year, campus="BVH"),
                codes=[
                    dict(
                        system="ptit:table-program-label",
                        value=CODES[0],
                        from_year=year,
                        to_year=year,
                        evidence=["fixture://cross-year"],
                    )
                ],
                review=dict(evidence=["fixture://cross-year"]),
            ),
        ]
    seed = EntityRegistry.model_validate(frozen)
    frozen = seed.frozen()
    r = ResolutionStore(db).run(n["job_id"], seed)
    assert r["candidates"] == 5 and ResolutionStore(db).replay(r["job_id"])["inserted"] == 0
    compiled = db.scalar(sa.select(ingest_jobs.c.payload).where(ingest_jobs.c.id == r["job_id"]))[
        "registry"
    ]
    assert compiled["entities"][: len(frozen["entities"])] == frozen["entities"]
    assert (
        sum(
            e["kind"] == "offering" and e["attributes"].get("admission_year") == 2025
            for e in compiled["entities"]
        )
        == 5
    )
    rows = db.execute(
        sa.select(observations).where(
            observations.c.snapshot_id == snap,
            observations.c.normalized_fields["registry_version"].astext == r["registry_version"],
        )
    ).mappings()
    packets = [
        inspect_packet(db, row["id"], v["candidate_key"])
        for row in rows
        for v in row["normalized_fields"]["candidates"]
    ]
    assert len(packets) == 5 and checked_packets(db, [binding_for(p) for p in packets]) == packets
    assert all(
        p["candidate"]["method"] is None
        and "METHOD_NOT_STATED" in p["resolution"]["entities"]["method"]["reasons"]
        and not p["resolution"]["publication_eligible"]
        for p in packets
    )
    assert before == {
        n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business
    }


def test_changed_archive_score_header_has_explicit_diagnostic():
    out, _ = parsed(body().replace("Điểm chuẩn trúng tuyển".encode(), b"Unknown"))
    assert not candidates(out)
    assert "PTIT2025_TABLES_MISSING" in {i.code for i in out.issues}
