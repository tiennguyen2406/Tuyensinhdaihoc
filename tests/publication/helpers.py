"""TEST ONLY ingestion. Real test database, never the project pilot."""

from uuid import UUID, uuid4

import sqlalchemy as sa

from services.api.db.models import observations
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.store import ResolutionStore


def seed_registry():
    return EntityRegistry.model_validate(
        dict(
            version="registry/publication-test/" + uuid4().hex,
            alias_version="aliases/publication-test/" + uuid4().hex,
            classification="pilot_pending",
            entities=[
                dict(
                    key="test:university",
                    kind="university",
                    name="TEST ONLY",
                    domains=["example.invalid"],
                    review=dict(status="pending", evidence=["fixture://TEST-ONLY"]),
                ),
                dict(
                    key="test:method",
                    kind="method",
                    name="Thi tốt nghiệp THPT",
                    university_key="test:university",
                    review=dict(status="pending", evidence=["fixture://TEST-ONLY"]),
                ),
            ],
        )
    )


def input_packet(db, registry=None, score="24,50", source_type="university"):
    from services.api.db.models import metadata
    from services.data.normalization.store import NormalizationStore
    from services.data.parsers.contract import ExtractedObservation, ParseResult
    from services.data.parsers.persistence import ObservationStore
    from services.data.publication.packets import inspect_packet
    from tests.normalization.helpers import raw_row

    assert db.engine.url.database.startswith("tuyensinh_test_")
    sid = uuid4()
    snap = uuid4()
    db.execute(
        metadata.tables["sources"]
        .insert()
        .values(
            id=sid,
            canonical_url="https://example.invalid/" + str(sid),
            domain="example.invalid",
            publisher="TEST ONLY",
            source_type=source_type,
        )
    )
    db.execute(
        metadata.tables["source_snapshots"]
        .insert()
        .values(
            id=snap,
            source_id=sid,
            raw_hash=uuid4().hex * 2,
            raw_uri="fixture://TEST-ONLY",
            final_url="https://example.invalid/pilot",
            media_type="text/html",
            byte_size=0,
        )
    )
    raw = raw_row(score=score).model_copy(update={"snapshot_id": snap, "source_id": sid})
    ObservationStore(db).save(
        ParseResult(
            observations=[
                ExtractedObservation.model_validate(
                    raw.model_dump(exclude={"id", "normalized_fields"})
                )
            ]
        )
    )
    raw_id = db.scalar(sa.select(observations.c.id).where(observations.c.snapshot_id == snap))
    job = NormalizationStore(db).run([raw_id])["job_id"]
    ResolutionStore(db).run(job, registry or seed_registry())
    row = (
        db.execute(
            sa.select(observations).where(
                observations.c.raw_fields["normalization_job_id"].astext == job,
                observations.c.normalized_fields["schema_version"].astext == "entity-resolution/1",
            )
        )
        .mappings()
        .one()
    )
    return inspect_packet(db, row["id"], row["normalized_fields"]["candidates"][0]["candidate_key"])


def resolve_again(c, packet, registry):
    from services.data.publication.packets import inspect_packet

    ResolutionStore(c).run(packet["normalization_job_id"], registry)
    row = (
        c.execute(
            sa.select(observations).where(
                observations.c.raw_fields["normalization_job_id"].astext
                == packet["normalization_job_id"],
                observations.c.normalized_fields["registry_version"].astext == registry.version,
            )
        )
        .mappings()
        .one()
    )
    return inspect_packet(c, row["id"], packet["candidate_key"])


def bootstrap_command(c, packet):
    from services.api.db.validators import record
    from services.data.publication.contract import BootstrapOperation, ReviewCommand
    from services.data.publication.packets import binding_for

    job = record(c, "ingest_jobs", UUID(packet["resolution_job_id"]))
    reg = job["payload"]["registry"]
    program = next(e for e in reg["entities"] if e["kind"] == "program")
    offering = next(e for e in reg["entities"] if e["kind"] == "offering")
    sid = packet["snapshot_id"]
    evidence = ["snapshot:" + sid + "#" + packet["evidence"]["locator"]]

    def op(key, kind, values, **extra):
        return BootstrapOperation(
            key=key, kind=kind, mode="create", values=values, evidence=evidence, **extra
        )

    uid = "test:university"
    pid = program["key"]
    ops = [
        op(
            uid,
            "university",
            dict(
                university_code="TEST-UNI",
                name="TEST ONLY",
                normalized_name="test only",
                slug="test-only",
            ),
        ),
        op(
            "test:method",
            "method",
            dict(code="TEST-THPT", name="Thi tốt nghiệp THPT", input_kind="subjects"),
            registry_fields=dict(
                codes=[dict(system="admission_methods.code", value="TEST-THPT", evidence=evidence)]
            ),
        ),
        BootstrapOperation(
            key="test:source",
            kind="source",
            mode="link",
            canonical_id=UUID(packet["source_id"]),
            values=dict(
                university_id="@" + uid,
                authority_scope=dict(years=[2024], fact_kinds=["cutoff", "scoring_rule"]),
            ),
            evidence=evidence,
        ),
        op(
            "test:year",
            "year",
            dict(
                university_id="@" + uid,
                admission_year=2024,
                status="verified",
                primary_snapshot_id=sid,
            ),
        ),
        op(
            pid,
            "program",
            dict(
                university_id="@" + uid,
                canonical_key="TEST-PROGRAM",
                program_name=program["name"],
                normalized_name="test program",
                major_id=None,
            ),
        ),
        op(
            offering["key"],
            "offering",
            dict(
                university_id="@" + uid,
                program_id="@" + pid,
                admission_year=2024,
                offering_code="TEST-A",
                offering_name=offering["name"],
                campus_code="BVH",
                track_code="UNSPECIFIED",
                language_code="UNSPECIFIED",
                primary_snapshot_id=sid,
            ),
            registry_fields=dict(attributes=offering["attributes"]),
        ),
        op(
            "test:scale",
            "scale",
            dict(
                method_id="@test:method",
                admission_year=2024,
                code="TEST-SCALE",
                exam_version="TEST-2024",
                min_score="0",
                max_score="30",
                basis_description="TEST ONLY confirmed basis; no real admissions inference",
                primary_snapshot_id=sid,
            ),
        ),
    ]
    return ReviewCommand(
        request_id=uuid4(),
        action="bootstrap",
        binding=binding_for(packet),
        expected_registry_version=reg["version"],
        expected_alias_version=reg["alias_version"],
        new_registry_version="registry/reviewed-test/" + uuid4().hex,
        new_alias_version=reg["alias_version"],
        reason="TEST ONLY explicitly reviewed synthetic bootstrap",
        operations=ops,
    )


def fact_command(packet, ids, *, expected=None, score="24.5", supersedes=None):
    from services.data.publication.contract import CutoffSpec, ReviewCommand
    from services.data.publication.packets import binding_for

    locator = "snapshot:" + packet["snapshot_id"] + "#" + packet["evidence"]["locator"]
    evidence = {
        k: [locator]
        for k in [
            "year",
            "program",
            "method",
            "scale",
            "basis",
            "combination",
            "round",
            "population",
            "conditions",
            "publication",
            "score",
            "correction",
        ]
    }
    offering = next(v for k, v in ids.items() if k.startswith("proposal:offering:"))
    return ReviewCommand(
        request_id=uuid4(),
        action="publish",
        binding=binding_for(packet),
        expected_registry_version=packet["registry_version"],
        expected_alias_version=packet["alias_version"],
        reason="TEST ONLY explicitly reviewed fact and scope",
        expected_revision=expected,
        fact=CutoffSpec(
            university_id=ids["test:university"],
            program_year_id=offering,
            admission_year=2024,
            method_id=ids["test:method"],
            score_scale_id=ids["test:scale"],
            score=score,
            basis_version="TEST-BASIS/1",
            combination_status="confirmed_none",
            round_key="TEST-ROUND",
            population_key="TEST-POPULATION",
            conditions={"schema_version": "conditions/1", "kind": "none"},
            condition_text="TEST ONLY reviewed absence of extra conditions",
            evidence=evidence,
            supersedes_cutoff_id=supersedes,
        ),
    )
