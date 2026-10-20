"""Synthetic UEH layouts; full real211-cell validation lives privately in state/."""

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa
from bs4 import BeautifulSoup

from services.api.db.models import ingest_jobs, metadata, observations
from services.api.source_profiles import SourceProfile
from services.data.normalization.contract import NormalizationContext
from services.data.normalization.normalize import normalize
from services.data.normalization.store import NormalizationStore
from services.data.parsers.persistence import ObservationStore
from services.data.parsers.registry import extract
from services.data.parsers.ueh_pt345 import METHODS
from services.data.publication.packets import binding_for, checked_packets, inspect_packet
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.store import ResolutionStore
from tests.normalization.test_ueh import pending, raw
from tests.normalization.test_ueh_batch import body as pt6_body
from tests.parsers.helpers import snapshot

CTX = NormalizationContext(version="normalizer/ueh-2024-pt345/1.0.0")
DEFS = """<p>– Phương thức 3 (PT3): Phương thức xét tuyển học sinh Giỏi.</p>
<p>– Phương thức 4 (PT4): Phương thức xét tuyển quá trình học tập theo tổ hợp môn.</p>
<p>– Phương thức 5 (PT5): Phương thức xét tuyển dựa vào kết quả thi đánh giá năng lực của Đại học Quốc gia TP.HCM tổ chức đợt 1 năm 2024.</p>
<p>– Các phương thức xét tuyển sớm (Phương thức 1,2,3,4,5): UEH đã công bố kết quả xét tuyển vào ngày 20/6/2024 và ngày 09/7/2024.</p>"""


def body():
    soup = BeautifulSoup(pt6_body(), "html.parser")
    root = soup.select(".elementor-widget-theme-post-content > .elementor-widget-container")[0]
    root.insert(0, BeautifulSoup(DEFS, "html.parser"))
    for ti, table in enumerate(root.find_all("table")[1:]):
        for tr in table.find_all("tbody")[0].find_all("tr")[:-1]:
            cells = tr.find_all("td", recursive=False)
            for col, value in [(4, "70.25"), (5, "75.50")] + ([] if ti == 1 else [(6, "900")]):
                cells[col].string = value
    return str(soup).encode()


def parsed(data=None):
    data = data or body()
    profile = SourceProfile.model_validate_json(
        Path("config/sources/ueh-2024-pt6-full-parser-20261020-v1.json").read_text(encoding="utf8")
    ).model_copy(update={"parser": "ueh_2024_pt345_html"})
    ref = snapshot(data).model_copy(update={"final_url": str(profile.seed_urls[0])})
    return extract(ref, profile, data, revision="pt345-test"), ref


def values(result):
    return [c for o in result.observations for c in normalize(raw(o), CTX).candidates]


def test_all_three_layouts_physical_methods_and_no_pt6_fanout():
    result, _ = parsed()
    candidates = values(result)
    assert len(result.observations) == 6
    assert len(candidates) == 16
    assert len(result.metadata["method_cell_ledger"]) == 16
    assert len(result.metadata["method_not_offered"]) == 2
    for c in candidates:
        method = c.method.display.split()[1]
        assert (
            c.value.value
            == {"PT3": Decimal("70.25"), "PT4": Decimal("75.50"), "PT5": Decimal("900")}[method]
        )
        assert c.combinations is c.score_scale is c.round is c.population is c.conditions is None
        assert not c.lineage.footnotes and "combinations" not in c.lineage.scope_evidence
        assert c.scope["track"] is c.scope["language"] is None
        assert "PT6" not in str(c.lineage.scope_evidence)
    assert all(
        "PT5" not in c.method.display
        for c in candidates
        if c.scope["offering_code"]["display"] in {"ISB_CNTN", "ASA_Co-op"}
    )


def test_method_definitions_early_context_year_and_header_are_bound():
    result, _ = parsed()
    for c in values(result):
        method = c.method.display.split()[1]
        assert c.admission_year == 2024
        assert method in c.lineage.scope_evidence["method_definition"]["raw_text"]
        assert c.lineage.header_path[0]["text"] == method
        assert "20/6/2024" in c.lineage.scope_evidence["early_admission_context"]["raw_text"]
        assert "Round1" not in str(c.lineage.scope_evidence)
    assert not values(parsed(body().replace("năm 2024 của".encode(), "năm 2023 của".encode()))[0])


def test_bad_cell_does_not_block_other_methods_or_rows():
    soup = BeautifulSoup(body(), "html.parser")
    table = soup.find_all("table")[1]
    row = table.find("tbody").find("tr")
    row.find_all("td")[4].string = ""
    result, _ = parsed(str(soup).encode())
    assert len(values(result)) == 15
    blocked = [
        x for x in result.metadata["method_cell_ledger"] if x["status"] != "eligible_source_cell"
    ]
    assert len(blocked) == 1 and blocked[0]["method"] == "PT3"


def test_missing_method_definition_blocks_only_that_method():
    data = body().replace("Phương thức xét tuyển học sinh Giỏi.".encode(), b"unknown.")
    result, _ = parsed(data)
    assert len(values(result)) == 10
    assert not any("PT3" in c.method.display for c in values(result))


def test_merged_score_fails_closed_but_independent_row_survives():
    soup = BeautifulSoup(body(), "html.parser")
    table = soup.find_all("table")[1]
    row = table.find("tbody").find("tr")
    cells = row.find_all("td")
    cells[4]["colspan"] = "2"
    cells[5].decompose()
    result, _ = parsed(str(soup).encode())
    assert len(values(result)) == 14


def test_parser_and_normalizer_reject_tampered_mapping_and_wrong_source():
    result, _ = parsed()
    assert not values(parsed(body().replace(b"17/08/2024", b"17/08/2023"))[0])
    o = result.observations[0]
    fields = dict(o.raw_fields)
    mapping = dict(fields["ueh_pt345_2024"])
    mapping["snapshot_id"] = "wrong"
    fields["ueh_pt345_2024"] = mapping
    assert not normalize(raw(o.model_copy(update={"raw_fields": fields})), CTX).candidates


def test_candidates_are_distinct_by_cell_and_method_not_score():
    result, _ = parsed()
    c = values(result)
    assert len({v.candidate_key for v in c}) == 16
    assert {v.scope["campus"]["display"] for v in c} == {"KSA", "KSV"}
    assert all(not v.entity_ids for v in c)


def test_pt6_physical_origin_cannot_be_rebound_to_pt4_header():
    result, _ = parsed()
    o = result.observations[0]
    f = deepcopy(o.raw_fields)
    f["cells"][5] = f["cells"][8] | {"column": 5}
    out = normalize(raw(o.model_copy(update={"raw_fields": f})), CTX)
    assert len(out.candidates) == 2
    assert not any("PT4" in c.method.display for c in out.candidates)


@pytest.mark.parametrize("value", ["not published", "-1", "", "2024/2023"])
def test_invalid_score_is_explicitly_blocked_without_silent_drop(value):
    soup = BeautifulSoup(body(), "html.parser")
    soup.find_all("table")[1].find("tbody").find("tr").find_all("td")[6].string = value
    result, _ = parsed(str(soup).encode())
    assert len(result.metadata["method_cell_ledger"]) == 16
    assert len(values(result)) == 15
    assert sum(len(normalize(raw(o), CTX).blocked) for o in result.observations) == 1


def test_missing_isb_section_has_no_phantom_pt5_and_keeps_ledger():
    data = body().replace("Chương trình Cử nhân tài năng, Asean Co-op".encode(), b"unknown")
    result, _ = parsed(data)
    assert len(result.metadata["method_cell_ledger"]) == 16
    assert len(values(result)) == 12
    assert all(
        e["method"] != "PT5"
        for e in result.metadata["method_cell_ledger"]
        if e["group"] == "unmapped"
    )


def test_wrong_method_header_blocks_group_but_not_other_tables():
    soup = BeautifulSoup(body(), "html.parser")
    table = soup.find_all("table")[1]
    next(c for c in table.find("tr").find_all("td") if c.get_text() == "PT4").string = "PT5"
    result, _ = parsed(str(soup).encode())
    assert len(result.metadata["method_cell_ledger"]) == 16
    assert len(values(result)) == 10


def test_exact_source_path_required_and_old_pt6_output_unchanged():
    data = body()
    profile = SourceProfile.model_validate_json(
        Path("config/sources/ueh-2024-pt6-full-parser-20261020-v1.json").read_text(encoding="utf8")
    )
    ref = snapshot(data).model_copy(update={"final_url": str(profile.seed_urls[0])})
    old = extract(ref, profile, data)
    assert len(old.observations) == 6
    parsed(data)
    assert extract(ref, profile, data) == old
    new = profile.model_copy(update={"parser": "ueh_2024_pt345_html"})
    assert not extract(
        ref.model_copy(update={"final_url": "https://tuyensinh.ueh.edu.vn/other/"}), new, data
    ).observations


def test_postgres_multi_candidate_replay_identity_reuse_and_packets(db):
    data = body()
    _, ref = parsed(data)
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
            raw_uri="fixture://synthetic-pt345",
            final_url=ref.final_url,
            media_type="text/html",
            byte_size=ref.byte_size,
        )
        .returning(metadata.tables["source_snapshots"].c.id)
    ).scalar_one()
    ref = ref.model_copy(update={"snapshot_id": snap, "source_id": source})
    profile = SourceProfile.model_validate_json(
        Path("config/sources/ueh-2024-pt6-full-parser-20261020-v1.json").read_text(encoding="utf8")
    )
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
    old = extract(ref, profile, data)
    assert ObservationStore(db).save(old) == 6
    ids = list(db.scalars(sa.select(observations.c.id).where(observations.c.snapshot_id == snap)))
    assert len(ids) == 6
    n6 = NormalizationStore(db).run(
        ids, NormalizationContext(version="normalizer/ueh-2024-pt6-batch/1.0.0")
    )
    r6 = ResolutionStore(db).run(n6["job_id"], pending())
    seed = dict(
        db.scalar(sa.select(ingest_jobs.c.payload).where(ingest_jobs.c.id == r6["job_id"]))[
            "registry"
        ]
    )
    identity_keys = {e["key"] for e in seed["entities"] if e["kind"] in {"program", "offering"}}
    seed["version"] = "registry/ueh-test-pt345/1"
    seed["entities"] = seed["entities"] + [
        dict(
            key="proposal:ueh-" + m.lower() + "-2024",
            kind="method",
            name=name,
            university_key="proposal:ueh",
            attributes={"admission_year": 2024},
            review={"evidence": ["fixture://synthetic-method"]},
        )
        for m, name in METHODS.items()
    ]
    result = extract(ref, profile.model_copy(update={"parser": "ueh_2024_pt345_html"}), data)
    assert ObservationStore(db).save(result) == 6
    assert ObservationStore(db).save(result) == 0
    ids = list(
        db.scalars(
            sa.select(observations.c.id).where(
                observations.c.snapshot_id == snap,
                observations.c.parser_version == result.observations[0].parser_version,
            )
        )
    )
    normal = NormalizationStore(db).run(ids, CTX)
    assert (
        normal["candidates"] == 16
        and NormalizationStore(db).replay(UUID(normal["job_id"]))["inserted"] == 0
    )
    resolution = ResolutionStore(db).run(normal["job_id"], EntityRegistry.model_validate(seed))
    assert (
        resolution["candidates"] == 16
        and ResolutionStore(db).replay(resolution["job_id"])["inserted"] == 0
    )
    compiled = db.scalar(
        sa.select(ingest_jobs.c.payload).where(ingest_jobs.c.id == resolution["job_id"])
    )["registry"]
    assert identity_keys == {
        e["key"] for e in compiled["entities"] if e["kind"] in {"program", "offering"}
    }
    output = db.execute(
        sa.select(observations).where(
            observations.c.normalized_fields["registry_version"].astext
            == resolution["registry_version"]
        )
    ).mappings()
    packets = [
        inspect_packet(db, r["id"], c["candidate_key"])
        for r in output
        for c in r["normalized_fields"]["candidates"]
    ]
    assert len(packets) == 16 and checked_packets(db, [binding_for(p) for p in packets]) == packets
    assert all(
        not p["resolution"]["publication_eligible"] and not p["candidate"]["entity_ids"]
        for p in packets
    )
    assert before == {
        n: list(db.execute(sa.select(metadata.tables[n])).mappings()) for n in business
    }
