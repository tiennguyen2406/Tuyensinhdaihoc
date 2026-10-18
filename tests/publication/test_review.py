from uuid import uuid4

import pytest
import sqlalchemy as sa


def test_real_login_roles_and_read_application_cannot_write(publication_logins):
    from services.data.publication.access import require

    with publication_logins["reviewer"].begin() as c:
        assert require(c, "reviewer").startswith("db:test_pub_")
        assert require(c, "publisher").startswith("db:test_pub_")
    with publication_logins["reader"].begin() as c:
        from services.api.db.session import schema_is_current

        assert schema_is_current(c)
        with pytest.raises(PermissionError):
            require(c, "reviewer")
        for table, operation in [
            ("cutoff_scores", "DELETE"),
            ("audit_events", "INSERT"),
            ("observations", "UPDATE"),
            ("ingest_jobs", "INSERT"),
        ]:
            assert not c.scalar(
                sa.text("SELECT has_table_privilege(current_user,:table,:operation)"),
                dict(table=table, operation=operation),
            )
        with pytest.raises(sa.exc.DBAPIError), c.begin_nested():
            c.exec_driver_sql("DELETE FROM cutoff_scores")


def test_bootstrap_no_circular_dependency_and_idempotence(publication_database, publication_logins):
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import bootstrap_command, input_packet

    with publication_database.begin() as c:
        packet = input_packet(c)
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, packet)
        svc = ReviewService(c)
        assert svc.plan(cmd)["can_apply"]
        first = svc.apply(cmd)
        assert svc.apply(cmd) == first
        assert first["registry"]["classification"] == "reviewed"
        assert sum(e["review"]["status"] == "approved" for e in first["registry"]["entities"]) == 4
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 0
        assert c.scalar(sa.text("SELECT count(*) FROM audit_events")) >= 8
        with pytest.raises(ValueError):
            svc.apply(cmd.model_copy(update={"request_id": uuid4()}))


def test_review_reject_request_more_and_revocation_do_not_approve(
    publication_database, publication_logins
):
    from services.data.publication.contract import ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import input_packet

    with publication_database.begin() as c:
        packet = input_packet(c)
    with publication_logins["reviewer"].begin() as c:
        svc = ReviewService(c)
        versions = svc.head(packet)
        for action in ["reject", "request_more"]:
            cmd = ReviewCommand(
                request_id=uuid4(),
                action=action,
                binding=binding_for(packet),
                expected_registry_version=versions[0],
                expected_alias_version=versions[1],
                reason="TEST ONLY: missing evidence",
            )
            result = svc.apply(cmd)
            assert result["status"] == "quarantined"
            with pytest.raises(ValueError):
                svc.validated(result["decision_id"])


@pytest.mark.parametrize("problem", ["wrong_parent", "wrong_campus", "bad_uuid"])
def test_bootstrap_context_errors_roll_back_all_review_writes(
    publication_database, publication_logins, problem
):
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import bootstrap_command, input_packet

    with publication_database.begin() as c:
        p = input_packet(c)
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, p)
        data = cmd.model_dump(mode="json")
        if problem == "bad_uuid":
            data["operations"][0].update(mode="link", canonical_id=str(uuid4()))
        else:
            op = next(o for o in data["operations"] if o["kind"] == "offering")
            op["values"]["university_id" if problem == "wrong_parent" else "campus_code"] = (
                str(uuid4()) if problem == "wrong_parent" else "BVS"
            )
        from services.data.publication.contract import ReviewCommand

        before = {
            t: c.scalar(sa.text("SELECT count(*) FROM " + t))
            for t in ["audit_events", "universities", "program_years", "ingest_jobs"]
        }
        with pytest.raises((ValueError, sa.exc.DBAPIError)):
            ReviewService(c).apply(ReviewCommand.model_validate(data))
        assert {t: c.scalar(sa.text("SELECT count(*) FROM " + t)) for t in before} == before


def test_alias_approval_has_real_actor_and_new_version(publication_database, publication_logins):
    from services.data.publication.contract import ReviewCommand
    from services.data.publication.review import ReviewService
    from services.data.resolution.registry import EntityRegistry
    from tests.publication.helpers import (
        bootstrap_command,
        input_packet,
        resolve_again,
        seed_registry,
    )

    seed = seed_registry().frozen()
    seed["aliases"] = [
        {
            "key": "test:domain-alias",
            "target": "test:university",
            "kind": "domain",
            "value": "example.invalid",
            "review": {"status": "pending", "evidence": ["fixture://TEST-ONLY"]},
        }
    ]
    with publication_database.begin() as c:
        p = input_packet(c, EntityRegistry.model_validate(seed))
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, p)
        data = cmd.model_dump(mode="json")
        data["new_alias_version"] = "aliases/test-approved/" + uuid4().hex
        data["operations"].append(
            {
                "key": "test:domain-alias",
                "kind": "alias",
                "mode": "create",
                "values": {
                    "university_id": "@test:university",
                    "alias": "example.invalid",
                    "normalized_alias": "example.invalid",
                    "alias_type": "domain",
                    "evidence_url": "snapshot:" + p["snapshot_id"] + "#" + p["evidence"]["locator"],
                },
                "evidence": ["snapshot:" + p["snapshot_id"] + "#" + p["evidence"]["locator"]],
            }
        )
        result = ReviewService(c).apply(ReviewCommand.model_validate(data))
        assert result["registry"]["aliases"][0]["review"]["reviewer"].startswith("db:test_pub_")
        assert c.scalar(sa.text("SELECT count(*) FROM university_aliases")) == 1
        again = resolve_again(c, p, EntityRegistry.model_validate(result["registry"]))
        assert again["resolution"]["entities"]["university"]["status"] == "resolved"


def test_bootstrap_requires_snapshot_locator_not_an_arbitrary_evidence_string(
    publication_database, publication_logins
):
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import bootstrap_command, input_packet

    with publication_database.begin() as c:
        p = input_packet(c)
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, p)
        cmd = cmd.model_copy(
            update={
                "operations": [
                    cmd.operations[0].model_copy(update={"evidence": ["just trust this"]}),
                    *cmd.operations[1:],
                ]
            }
        )
        with pytest.raises(ValueError):
            ReviewService(c).apply(cmd)
        assert c.scalar(sa.text("SELECT count(*) FROM universities")) == 0


def test_supporting_source_bootstrap_requires_its_cached_evidence_and_same_publisher(
    publication_database, publication_logins
):
    from services.api.db.models import source_snapshots, sources
    from services.data.publication.contract import BootstrapOperation
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import bootstrap_command, input_packet

    with publication_database.begin() as c:
        packet = input_packet(c)
        sid, snap = uuid4(), uuid4()
        c.execute(
            sources.insert().values(
                id=sid,
                canonical_url="https://example.invalid/support",
                domain="example.invalid",
                publisher="TEST ONLY",
                source_type="admission_office",
            )
        )
        c.execute(
            source_snapshots.insert().values(
                id=snap,
                source_id=sid,
                raw_hash="a" * 64,
                raw_uri="fixture://TEST-ONLY",
                final_url="https://example.invalid/support",
                media_type="text/html",
                byte_size=0,
            )
        )
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, packet)
        support = BootstrapOperation(
            key="test:support-source",
            kind="source",
            mode="link",
            canonical_id=sid,
            values={
                "university_id": "@test:university",
                "authority_scope": {"years": [2024], "fact_kinds": ["cutoff", "scoring_rule"]},
            },
            evidence=["snapshot:" + str(snap) + "#html:main"],
        )
        cmd = cmd.model_copy(update={"operations": [*cmd.operations, support]})
        assert ReviewService(c).plan(cmd)["can_apply"]
        result = ReviewService(c).apply(cmd)
        assert (
            c.scalar(sa.select(sources.c.verification_status).where(sources.c.id == sid))
            == "verified"
        )
        assert result["ids"]["test:support-source"] == str(sid)
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 0


@pytest.mark.parametrize("problem", ["wrong_snapshot", "foreign_host", "unofficial"])
def test_supporting_source_authority_does_not_accept_unrelated_evidence(
    publication_database, publication_logins, problem
):
    from services.api.db.models import source_snapshots, sources
    from services.data.publication.contract import BootstrapOperation
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import bootstrap_command, input_packet

    with publication_database.begin() as c:
        packet = input_packet(c)
        sid, snap = uuid4(), uuid4()
        domain = "other.invalid" if problem == "foreign_host" else "example.invalid"
        c.execute(
            sources.insert().values(
                id=sid,
                canonical_url="https://" + domain + "/support",
                domain=domain,
                publisher="TEST ONLY",
                source_type="press" if problem == "unofficial" else "admission_office",
            )
        )
        c.execute(
            source_snapshots.insert().values(
                id=snap,
                source_id=sid,
                raw_hash="b" * 64,
                raw_uri="fixture://TEST-ONLY",
                final_url="https://" + domain + "/support",
                media_type="text/html",
                byte_size=0,
            )
        )
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, packet)
        evidence_snapshot = packet["snapshot_id"] if problem == "wrong_snapshot" else str(snap)
        support = BootstrapOperation(
            key="test:unrelated-source",
            kind="source",
            mode="link",
            canonical_id=sid,
            values={
                "university_id": "@test:university",
                "authority_scope": {"years": [2024], "fact_kinds": ["cutoff"]},
            },
            evidence=["snapshot:" + evidence_snapshot + "#html:main"],
        )
        cmd = cmd.model_copy(update={"operations": [*cmd.operations, support]})
        with pytest.raises(ValueError):
            ReviewService(c).apply(cmd)
        assert (
            c.scalar(sa.select(sources.c.verification_status).where(sources.c.id == sid))
            == "unverified"
        )
        assert c.scalar(sa.text("SELECT count(*) FROM audit_events")) == 0
