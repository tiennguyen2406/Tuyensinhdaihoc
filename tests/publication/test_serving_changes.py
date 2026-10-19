"""Bootstrap invalidates the live catalog even before the first cutoff exists."""

from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from fastapi import HTTPException

from services.api.catalog import dto, queries
from services.api.db.models import metadata
from services.data.publication.contract import BootstrapOperation, ReviewCommand
from services.data.publication.review import ReviewService
from services.data.resolution.registry import EntityRegistry
from tests.publication.helpers import bootstrap_command, input_packet, seed_registry


def packet_with_alias(c):
    seed = seed_registry().frozen()
    seed["aliases"] = [
        {
            "key": "test:search-alias",
            "target": "test:university",
            "kind": "name",
            "value": "Searchable Alias",
            "review": {"status": "pending", "evidence": ["fixture://TEST-ONLY"]},
        }
    ]
    return input_packet(c, EntityRegistry.model_validate(seed))


def counts(c):
    return {
        table: c.scalar(sa.select(sa.func.count()).select_from(metadata.tables[table]))
        for table in [
            "universities",
            "programs",
            "admission_years",
            "university_aliases",
            "audit_events",
            "ingest_jobs",
        ]
    } | {"version": c.scalar(sa.text("SELECT dataset_version FROM catalog_state"))}


@pytest.mark.parametrize("change", ["university", "year", "alias", "program"])
def test_bootstrap_visible_without_cutoffs_invalidates_cursor_once_and_replays(
    publication_database, publication_logins, change
):
    with publication_database.begin() as c:
        packet = packet_with_alias(c)
        for suffix in ["a", "z"]:
            c.execute(
                metadata.tables["universities"]
                .insert()
                .values(
                    name="TEST " + suffix,
                    normalized_name="test " + suffix,
                    university_code="TEST-" + suffix,
                    slug="test-" + suffix,
                    verification_status="verified",
                )
            )
    with publication_logins["reviewer"].begin() as c:
        svc = ReviewService(c)
        original = bootstrap_command(c, packet)
        cmd = original
        if change != "university":
            omitted = {"year", "offering"} if change == "year" else {"program", "offering"}
            if change == "alias":
                omitted = set()
            boot = svc.apply(
                original.model_copy(
                    update={"operations": [o for o in original.operations if o.kind not in omitted]}
                )
            )
            owner = boot["ids"]["test:university"]
            if change == "alias":
                evidence = ["snapshot:" + packet["snapshot_id"] + "#html:main"]
                operation = BootstrapOperation(
                    key="test:search-alias",
                    kind="alias",
                    mode="create",
                    values={
                        "university_id": owner,
                        "alias": "Searchable Alias",
                        "normalized_alias": "searchable alias",
                        "alias_type": "name",
                        "evidence_url": evidence[0],
                    },
                    evidence=evidence,
                )
            else:
                operation = next(o for o in original.operations if o.kind == change)
                operation = operation.model_copy(
                    update={"values": operation.values | {"university_id": owner}}
                )
            cmd = original.model_copy(
                update={
                    "request_id": uuid4(),
                    "operations": [operation],
                    "expected_registry_version": boot["registry"]["version"],
                    "expected_alias_version": boot["registry"]["alias_version"],
                    "new_registry_version": "test/serving/" + uuid4().hex,
                    "new_alias_version": "test/aliases/" + uuid4().hex,
                }
            )
        params = dto.Universities(year=2024, limit=1)
        page = queries.search_universities(c, params)
        assert page["has_more"] and page["next_cursor"]
        before = counts(c)
        assert svc.plan(cmd)["effect"]["catalog_version_delta"] == 1
        assert counts(c) == before  # Planning is read-only.
        result = svc.apply(cmd)
        assert result["catalog_version_delta"] == 1
        assert result["dataset_version"] == before["version"] + 1
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 0
        refresh = (
            c.execute(
                sa.select(metadata.tables["ingest_jobs"]).where(
                    metadata.tables["ingest_jobs"].c.id == UUID(result["refresh_job_id"])
                )
            )
            .mappings()
            .one()
        )
        assert refresh["job_type"] == "refresh_serving" and refresh["status"] == "queued"
        assert refresh["payload"]["dataset_version"] == result["dataset_version"]
        after = counts(c)
        assert svc.apply(cmd) == result
        assert counts(c) == after
        with pytest.raises(HTTPException) as stale:
            queries.search_universities(
                c, params.model_copy(update={"cursor": page["next_cursor"]})
            )
        assert stale.value.status_code == 409
        assert stale.value.detail["code"] == "DATASET_CHANGED"
        owner = UUID(result["ids"]["test:university"])
        detail = queries.university_detail(c, owner, 2024)["item"]
        assert detail.cutoff_count == 0
        if change == "year":
            assert detail.data_status == "verified"
            assert queries.admission_years(c, owner)["items"][0].data_status == "verified"
        elif change == "alias":
            assert (
                queries.search_universities(
                    c, dto.Universities(year=2024, query="searchable alias")
                )["items"][0].id
                == owner
            )
        elif change == "program":
            program_id = UUID(result["ids"][operation.key])
            assert queries.program_detail(c, program_id, 2024)["item"].offerings == []


def test_internal_registry_link_preserves_serving_version_and_replays(
    publication_database, publication_logins
):
    with publication_database.begin() as c:
        packet = input_packet(c)
    with publication_logins["reviewer"].begin() as c:
        svc = ReviewService(c)
        original = bootstrap_command(c, packet)
        boot = svc.apply(original)
        university = original.operations[0].model_copy(
            update={
                "mode": "link",
                "canonical_id": UUID(boot["ids"]["test:university"]),
                "registry_fields": {"domains": ["example.invalid", "metadata.example.invalid"]},
            }
        )
        cmd = original.model_copy(
            update={
                "request_id": uuid4(),
                "operations": [university],
                "expected_registry_version": boot["registry"]["version"],
                "new_registry_version": "test/internal/" + uuid4().hex,
            }
        )
        before = counts(c)
        assert svc.plan(cmd)["effect"]["catalog_version_delta"] == 0
        result = svc.apply(cmd)
        assert result["catalog_version_delta"] == 0
        assert counts(c)["version"] == before["version"]
        after = counts(c)
        assert svc.apply(cmd) == result and counts(c) == after


@pytest.mark.parametrize("change", ["future_year", "expired_alias", "offering", "source_metadata"])
def test_bootstrap_outside_catalog_surface_preserves_version(
    publication_database, publication_logins, change
):
    with publication_database.begin() as c:
        packet = packet_with_alias(c)
    with publication_logins["reviewer"].begin() as c:
        svc = ReviewService(c)
        original = bootstrap_command(c, packet)
        boot = svc.apply(
            original.model_copy(
                update={"operations": [o for o in original.operations if o.kind != "offering"]}
            )
        )
        if change == "expired_alias":
            operation = BootstrapOperation(
                key="test:search-alias",
                kind="alias",
                mode="create",
                values={
                    "university_id": boot["ids"]["test:university"],
                    "alias": "Searchable Alias",
                    "normalized_alias": "searchable alias",
                    "alias_type": "name",
                    "evidence_url": original.operations[0].evidence[0],
                    "valid_to": "2023-12-31",
                },
                evidence=original.operations[0].evidence,
            )
        else:
            kind = {"future_year": "year", "source_metadata": "source", "offering": "offering"}[
                change
            ]
            operation = next(o for o in original.operations if o.kind == kind)
            if change == "future_year":
                operation = operation.model_copy(
                    update={"values": operation.values | {"admission_year": 2027}}
                )
            elif change == "source_metadata":
                operation = operation.model_copy(
                    update={
                        "values": operation.values
                        | {
                            "authority_scope": {
                                "years": [2024, 2025],
                                "fact_kinds": ["cutoff", "scoring_rule"],
                            }
                        }
                    }
                )
        cmd = original.model_copy(
            update={
                "request_id": uuid4(),
                "operations": [operation],
                "expected_registry_version": boot["registry"]["version"],
                "new_registry_version": "test/not-visible/" + uuid4().hex,
                "new_alias_version": "test/aliases/" + uuid4().hex,
            }
        )
        before = counts(c)
        assert svc.plan(cmd)["effect"]["catalog_version_delta"] == 0
        result = svc.apply(cmd)
        assert result["catalog_version_delta"] == 0
        assert counts(c)["version"] == before["version"]
        assert (
            c.scalar(sa.text("SELECT count(*) FROM ingest_jobs WHERE job_type='refresh_serving'"))
            == 1
        )
        after = counts(c)
        assert svc.apply(cmd) == result and counts(c) == after


def test_bootstrap_refresh_failure_rolls_back_canonical_audit_and_version(
    publication_database, publication_logins
):
    with publication_database.begin() as c:
        packet = input_packet(c)
        c.exec_driver_sql(
            "CREATE FUNCTION fail_bootstrap_refresh() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN IF NEW.job_type='refresh_serving' THEN RAISE EXCEPTION 'TEST injected failure'; "
            "END IF; RETURN NEW; END $$"
        )
        c.exec_driver_sql(
            "CREATE TRIGGER fail_refresh BEFORE INSERT ON ingest_jobs FOR EACH ROW "
            "EXECUTE FUNCTION fail_bootstrap_refresh()"
        )
    with publication_logins["reviewer"].begin() as c:
        before = counts(c)
        with pytest.raises(sa.exc.DBAPIError, match="TEST injected failure"):
            ReviewService(c).apply(bootstrap_command(c, packet))
        assert counts(c) == before


@pytest.mark.parametrize("evidence_role", ["primary", "supporting"])
def test_source_verification_invalidates_existing_catalog_references(
    publication_database, publication_logins, evidence_role
):
    from services.data.publication.packets import binding_for
    from tests.fixtures import make_scope

    with publication_database.begin() as c:
        packet = input_packet(c)
        fixture = make_scope(c)
        c.execute(
            metadata.tables["universities"]
            .update()
            .where(metadata.tables["universities"].c.id == fixture["university"])
            .values(verification_status="verified")
        )
        if evidence_role == "primary":
            c.execute(
                metadata.tables["cutoff_scores"]
                .update()
                .where(metadata.tables["cutoff_scores"].c.id == fixture["cutoff"])
                .values(primary_snapshot_id=UUID(packet["snapshot_id"]))
            )
        else:
            c.execute(
                metadata.tables["cutoff_evidence"]
                .insert()
                .values(
                    cutoff_id=fixture["cutoff"],
                    observation_id=UUID(packet["raw_observation_id"]),
                    evidence_role="supporting",
                )
            )
    with publication_logins["reviewer"].begin() as c:
        svc = ReviewService(c)
        registry_version, alias_version = svc.head(packet)
        cmd = ReviewCommand(
            request_id=uuid4(),
            action="bootstrap",
            binding=binding_for(packet),
            expected_registry_version=registry_version,
            expected_alias_version=alias_version,
            new_registry_version="test/source/" + uuid4().hex,
            new_alias_version=alias_version,
            reason="TEST ONLY expose an existing referenced source",
            operations=[
                BootstrapOperation(
                    key="test:source",
                    kind="source",
                    mode="link",
                    canonical_id=UUID(packet["source_id"]),
                    values={
                        "university_id": str(fixture["university"]),
                        "authority_scope": {"years": [2026], "fact_kinds": ["cutoff"]},
                    },
                    evidence=["snapshot:" + packet["snapshot_id"] + "#html:main"],
                )
            ],
        )
        old_sources = queries.university_detail(c, fixture["university"], 2026)["item"].sources
        assert UUID(packet["snapshot_id"]) not in {s.snapshot_id for s in old_sources}
        assert svc.plan(cmd)["effect"]["catalog_version_delta"] == 1
        result = svc.apply(cmd)
        assert result["catalog_version_delta"] == 1 and result["dataset_version"] == 1
        sources = queries.university_detail(c, fixture["university"], 2026)["item"].sources
        assert UUID(packet["snapshot_id"]) in {s.snapshot_id for s in sources}
        before = counts(c)
        assert svc.apply(cmd) == result and counts(c) == before
