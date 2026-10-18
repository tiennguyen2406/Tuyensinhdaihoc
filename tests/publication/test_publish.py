from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from services.data.resolution.registry import EntityRegistry
from tests.publication.helpers import bootstrap_command, fact_command, input_packet, resolve_again


@pytest.fixture
def prepared(publication_database, publication_logins):
    from services.data.publication.review import ReviewService

    with publication_database.begin() as c:
        original = input_packet(c)
    e = publication_logins["reviewer"]
    with e.begin() as c:
        bootstrap = ReviewService(c).apply(bootstrap_command(c, original))
        registry = EntityRegistry.model_validate(bootstrap["registry"])
        packet = resolve_again(c, original, registry)
    return publication_database, e, packet, bootstrap


def reviewed(c, cmd):
    from services.data.publication.review import ReviewService

    svc = ReviewService(c)
    result = svc.apply(cmd)
    return svc.validated(UUID(result["decision_id"]))


def publish(c, cmd):
    from services.data.publication.publish import Publisher

    return Publisher(c).publish(reviewed(c, cmd), cmd.expected_revision)


def test_first_publication_scope_evidence_version_jobs_and_replay(prepared):
    admin, e, packet, boot = prepared
    with e.begin() as c:
        cmd = fact_command(packet, boot["ids"])
        draft = reviewed(c, cmd)
        assert draft.computation_status == "unavailable_rule"
        from services.data.publication.publish import Publisher

        result = Publisher(c).publish(draft, None)
        assert result.status == "published" and result.revision == 1 and result.dataset_version == 1
        replay = Publisher(c).publish(draft, None)
        assert replay.cached and replay.dataset_version == 1
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores WHERE is_current")) == 1
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_evidence")) == 1
        assert (
            c.scalar(
                sa.text(
                    "SELECT count(*) FROM ingest_jobs WHERE job_type='refresh_serving' AND status='queued'"
                )
            )
            == 1
        )
        assert c.scalar(sa.text("SELECT score FROM cutoff_scores")) == Decimal("24.5")
        assert c.scalar(sa.text("SELECT major_id FROM programs")) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("score_scale_id", None),
        ("basis_version", None),
        ("round_key", None),
        ("population_key", None),
        ("conditions", {}),
        ("conditions", {"schema_version": "conditions/1", "kind": "predicate"}),
        ("conditions", {"schema_version": "conditions/1", "kind": "predicate", "expression": {}}),
        ("conditions", {"schema_version": "unknown/1", "kind": "none"}),
        (
            "conditions",
            {"schema_version": "conditions/1", "kind": "none", "expression": {"field": "TEST"}},
        ),
        ("evidence", {}),
        ("combination_status", "unknown"),
        ("admission_year", 2025),
        ("program_year_id", uuid4()),
        ("method_id", uuid4()),
        ("score", Decimal("25.5")),
    ],
)
def test_missing_or_wrong_scope_basis_evidence_blocks_before_publication(prepared, field, value):
    admin, e, packet, boot = prepared
    cmd = fact_command(packet, boot["ids"])
    cmd = cmd.model_copy(update={"fact": cmd.fact.model_copy(update={field: value})})
    with e.begin() as c:
        with pytest.raises((ValueError, sa.exc.DBAPIError)):
            publish(c, cmd)
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 0


def additional(prepared, score="24,50", source_type="university"):
    from services.data.publication.contract import BootstrapOperation, ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService

    admin, e, old, boot = prepared
    with e.connect() as c:
        reg = ReviewService(c).registry(old)
    with admin.begin() as c:
        packet = input_packet(c, reg, score, source_type)
    with e.begin() as c:
        op = BootstrapOperation(
            key="source:" + packet["source_id"],
            kind="source",
            mode="link",
            canonical_id=packet["source_id"],
            values={
                "university_id": boot["ids"]["test:university"],
                "authority_scope": {"years": [2024], "fact_kinds": ["cutoff", "scoring_rule"]},
            },
            evidence=["snapshot:" + packet["snapshot_id"] + "#" + packet["evidence"]["locator"]],
        )
        cmd = ReviewCommand(
            request_id=uuid4(),
            action="bootstrap",
            binding=binding_for(packet),
            expected_registry_version=reg.version,
            expected_alias_version=reg.alias_version,
            new_registry_version="registry/test/" + uuid4().hex,
            new_alias_version=reg.alias_version,
            reason="TEST ONLY second source authority review",
            operations=[op],
        )
        b = ReviewService(c).apply(cmd)
        packet = resolve_again(c, packet, EntityRegistry.model_validate(b["registry"]))
    return packet


def test_three_sources_are_one_current_revision_with_three_evidence(prepared):
    admin, e, p, boot = prepared
    with e.begin() as c:
        publish(c, fact_command(p, boot["ids"]))
    for _ in range(2):
        packet = additional(prepared)
        with e.begin() as c:
            r = publish(c, fact_command(packet, boot["ids"], expected=1))
        assert r.status == "unchanged" and r.revision == 1
    with e.connect() as c:
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 1
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_evidence")) == 3
        assert c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == 3


def test_correction_history_stale_revision_and_official_conflict(prepared):
    admin, e, p, boot = prepared
    with e.begin() as c:
        first = publish(c, fact_command(p, boot["ids"]))
    packet = additional(prepared, "25,17")
    with e.begin() as c:
        corrected = publish(
            c,
            fact_command(
                packet, boot["ids"], score="25.17", expected=1, supersedes=first.cutoff_id
            ),
        )
        assert corrected.status == "corrected" and corrected.revision == 2
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 2
        assert (
            c.scalar(
                sa.text(
                    "SELECT count(*) FROM cutoff_scores WHERE NOT is_current AND system_valid_to IS NOT NULL"
                )
            )
            == 1
        )
        with pytest.raises(ValueError):
            publish(c, fact_command(packet, boot["ids"], score="25.17", expected=1))
    conflict_packet = additional(prepared, "26,00")
    with e.begin() as c:
        result = publish(c, fact_command(conflict_packet, boot["ids"], score="26", expected=2))
        assert result.status == "conflict"
        assert c.scalar(sa.text("SELECT score FROM cutoff_scores WHERE is_current")) == Decimal(
            "25.17"
        )
        assert (
            c.scalar(sa.text("SELECT verification_status FROM cutoff_scores WHERE is_current"))
            == "disputed"
        )
        assert (
            c.scalar(
                sa.text(
                    "SELECT count(*) FROM quality_issues WHERE issue_code='publication_conflict'"
                )
            )
            == 1
        )


def test_press_cannot_roll_back_and_revoked_decision_cannot_publish(prepared):
    from services.data.publication.contract import ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService

    admin, e, p, boot = prepared
    with e.begin() as c:
        draft = reviewed(c, fact_command(p, boot["ids"]))
        rev = ReviewCommand(
            request_id=uuid4(),
            action="revoke",
            binding=binding_for(p),
            expected_registry_version=p["registry_version"],
            expected_alias_version=p["alias_version"],
            reason="TEST ONLY evidence review withdrawn",
            revokes_decision_id=draft.decision_id,
        )
        ReviewService(c).apply(rev)
        from services.data.publication.publish import Publisher

        with pytest.raises(ValueError):
            Publisher(c).publish(draft, None)
        publish(c, fact_command(p, boot["ids"]))
    packet = additional(prepared, "20,00", "press")
    with e.begin() as c:
        with pytest.raises(ValueError):
            publish(c, fact_command(packet, boot["ids"], score="20", expected=1))
        assert c.scalar(sa.text("SELECT score FROM cutoff_scores WHERE is_current")) == Decimal(
            "24.5"
        )


def test_concurrent_identical_publish_is_idempotent(prepared):
    from concurrent.futures import ThreadPoolExecutor

    from services.data.publication.publish import Publisher

    admin, e, p, boot = prepared
    with e.begin() as c:
        draft = reviewed(c, fact_command(p, boot["ids"]))

    def worker(_):
        with e.begin() as c:
            return Publisher(c).publish(draft, None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, range(2)))
    assert len({r.cutoff_id for r in results}) == 1 and sum(r.cached for r in results) == 1


def test_mid_transaction_failure_rolls_back_every_publication_side_effect(prepared):
    from services.data.publication.publish import Publisher

    admin, e, p, boot = prepared
    with e.begin() as c:
        draft = reviewed(c, fact_command(p, boot["ids"]))
    with admin.begin() as c:
        c.exec_driver_sql(
            "CREATE FUNCTION fail_refresh_test() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.job_type='refresh_serving' THEN RAISE EXCEPTION 'TEST ONLY injected failure'; END IF; RETURN NEW; END $$"
        )
        c.exec_driver_sql(
            "CREATE TRIGGER fail_refresh BEFORE INSERT ON ingest_jobs FOR EACH ROW EXECUTE FUNCTION fail_refresh_test()"
        )
    with e.begin() as c:
        before = {
            t: c.scalar(sa.text("SELECT count(*) FROM " + t))
            for t in [
                "observations",
                "audit_events",
                "ingest_jobs",
                "cutoff_evidence",
                "cutoff_scores",
                "program_admissions",
            ]
        }
        with pytest.raises(sa.exc.DBAPIError):
            Publisher(c).publish(draft, None)
        assert {t: c.scalar(sa.text("SELECT count(*) FROM " + t)) for t in before} == before
        assert c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == 0


def test_db_guards_stop_core_history_and_audit_rewrites(prepared):
    admin, e, p, boot = prepared
    with e.begin() as c:
        publish(c, fact_command(p, boot["ids"]))
    with admin.begin() as c:
        for sql in [
            "UPDATE cutoff_scores SET score=1",
            "DELETE FROM cutoff_scores",
            "UPDATE audit_events SET reason='tampered'",
            "DELETE FROM audit_events",
            "UPDATE score_scales SET max_score=99",
            "UPDATE observations SET verification_status='unverified' WHERE starts_with(transform_version,'validated/1;')",
            "UPDATE ingest_jobs SET payload='{}' WHERE job_type='review_decision'",
        ]:
            with pytest.raises(sa.exc.DBAPIError), c.begin_nested():
                c.exec_driver_sql(sql)
        assert c.scalar(sa.text("SELECT score FROM cutoff_scores WHERE is_current")) == Decimal(
            "24.5"
        )


def test_identical_new_decision_and_fee_change_do_not_create_cutoff_revision(prepared):
    admin, e, p, boot = prepared
    with e.begin() as c:
        r = publish(c, fact_command(p, boot["ids"]))
    from services.api.db.models import tuition

    with admin.begin() as c:
        c.execute(
            tuition.insert().values(
                university_id=UUID(boot["ids"]["test:university"]),
                admission_year=2024,
                program_year_id=None,
                policy_key="TEST-FEE",
                revision=1,
                amount_min=Decimal("25000000.12"),
                currency="VND",
                unit="academic_year",
                description="TEST ONLY group tuition",
                scope_dsl={"academic_year": "2026–2027", "kind": "test_group"},
                primary_snapshot_id=UUID(p["snapshot_id"]),
                verification_status="unverified",
                is_current=False,
            )
        )
    with e.begin() as c:
        again = publish(c, fact_command(p, boot["ids"], expected=1))
        assert (
            again.status == "unchanged"
            and again.dataset_version == r.dataset_version
            and again.evidence_added == 0
        )
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 1


def test_basis_change_requires_explicit_replacement_and_preserves_old_scope(prepared):
    from services.data.publication.contract import BootstrapOperation, ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import resolve_again

    admin, e, p, boot = prepared
    with e.begin() as c:
        first = publish(c, fact_command(p, boot["ids"]))
        old_scope = c.scalar(
            sa.text("SELECT program_admission_id FROM cutoff_scores WHERE id=:id"),
            {"id": first.cutoff_id},
        )
        reg = ReviewService(c).registry(p)
        op = BootstrapOperation(
            key="test:scale2",
            kind="scale",
            mode="create",
            values={
                "method_id": boot["ids"]["test:method"],
                "admission_year": 2024,
                "code": "TEST-SCALE2",
                "exam_version": "TEST-2024",
                "min_score": "0",
                "max_score": "100",
                "basis_description": "TEST ONLY second explicitly reviewed basis",
                "primary_snapshot_id": p["snapshot_id"],
            },
            evidence=["snapshot:" + p["snapshot_id"] + "#" + p["evidence"]["locator"]],
        )
        cmd = ReviewCommand(
            request_id=uuid4(),
            action="bootstrap",
            binding=binding_for(p),
            expected_registry_version=reg.version,
            expected_alias_version=reg.alias_version,
            new_registry_version="registry/test/basis/" + uuid4().hex,
            new_alias_version=reg.alias_version,
            reason="TEST ONLY revised basis explicitly reviewed",
            operations=[op],
        )
        newer = ReviewService(c).apply(cmd)
        packet = resolve_again(c, p, EntityRegistry.model_validate(newer["registry"]))
        pc = fact_command(packet, boot["ids"], expected=1)
        pc = pc.model_copy(
            update={
                "fact": pc.fact.model_copy(
                    update={
                        "score_scale_id": UUID(newer["ids"]["test:scale2"]),
                        "basis_version": "TEST-BASIS/2",
                    }
                )
            }
        )
        with pytest.raises(ValueError):
            publish(c, pc)
        pc = pc.model_copy(
            update={
                "request_id": uuid4(),
                "fact": pc.fact.model_copy(update={"replaces_scope_id": old_scope}),
            }
        )
        result = publish(c, pc)
        assert result.status == "replaced" and result.revision == 1
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores WHERE is_current")) == 1
        assert (
            c.scalar(
                sa.text("SELECT data_status FROM program_admissions WHERE id=:id"),
                {"id": old_scope},
            )
            == "withdrawn"
        )
        assert c.scalar(sa.text("SELECT count(*) FROM program_admissions")) == 2


def test_publisher_role_cannot_forge_review_or_bypass_with_a_legacy_marker(
    prepared, publication_logins
):
    from services.api.db.models import cutoff_scores, ingest_jobs

    admin, e, p, boot = prepared
    with e.begin() as c:
        result = publish(c, fact_command(p, boot["ids"]))
    with admin.connect() as c:
        row = dict(
            c.execute(sa.select(cutoff_scores).where(cutoff_scores.c.id == result.cutoff_id))
            .mappings()
            .one()
        )
    with publication_logins["publisher_only"].begin() as c:
        from services.data.publication.access import require

        with pytest.raises(PermissionError):
            require(c, "reviewer")
        with pytest.raises(sa.exc.DBAPIError), c.begin_nested():
            c.execute(
                ingest_jobs.insert().values(
                    job_type="review_decision",
                    idempotency_key="forge:" + str(uuid4()),
                    status="succeeded",
                    payload={"actor_id": "db:fake", "command": {"action": "publish"}},
                )
            )
        row.update(id=uuid4(), revision=2, is_current=False, publication_group_key="BYPASS")
        with pytest.raises(sa.exc.DBAPIError), c.begin_nested():
            c.execute(cutoff_scores.insert().values(**row))


def test_applied_fact_and_supporting_bootstrap_decisions_cannot_be_silently_revoked(prepared):
    from services.data.publication.contract import ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.publish import Publisher
    from services.data.publication.review import ReviewService

    admin, e, p, boot = prepared
    with e.begin() as c:
        draft = reviewed(c, fact_command(p, boot["ids"]))
        result = Publisher(c).publish(draft, None)
        for target in [draft.decision_id, UUID(boot["decision_id"])]:
            cmd = ReviewCommand(
                request_id=uuid4(),
                action="revoke",
                binding=binding_for(p),
                expected_registry_version=p["registry_version"],
                expected_alias_version=p["alias_version"],
                reason="TEST ONLY revoke requires serving withdrawal",
                revokes_decision_id=target,
            )
            with pytest.raises(ValueError, match="withdrawal"):
                ReviewService(c).apply(cmd)
            assert not ReviewService(c).revoked(target)
        assert (
            c.scalar(sa.text("SELECT dataset_version FROM catalog_state")) == result.dataset_version
        )
        assert (
            c.scalar(sa.text("SELECT verification_status FROM cutoff_scores WHERE is_current"))
            == "verified"
        )


def test_dedicated_publisher_can_apply_but_not_issue_review(prepared, publication_logins):
    from services.data.publication.publish import Publisher

    admin, e, p, boot = prepared
    with e.begin() as c:
        draft = reviewed(c, fact_command(p, boot["ids"]))
    with publication_logins["publisher_only"].begin() as c:
        result = Publisher(c).publish(draft, None)
        assert result.status == "published" and result.revision == 1


def test_revoked_source_authority_review_cannot_start_publication(prepared):
    from services.api.db.models import ingest_jobs
    from services.data.publication.contract import ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService

    admin, e, p, boot = prepared
    packet = additional(prepared)
    with e.begin() as c:
        head = c.execute(
            sa.select(ingest_jobs.c.payload).where(
                ingest_jobs.c.job_type == "registry_version",
                ingest_jobs.c.payload["registry"]["version"].astext == packet["registry_version"],
            )
        ).scalar_one()
        revoke = ReviewCommand(
            request_id=uuid4(),
            action="revoke",
            binding=binding_for(packet),
            expected_registry_version=packet["registry_version"],
            expected_alias_version=packet["alias_version"],
            reason="TEST ONLY source authority review withdrawn",
            revokes_decision_id=UUID(head["decision_id"]),
        )
        ReviewService(c).apply(revoke)
        with pytest.raises(ValueError):
            publish(c, fact_command(packet, boot["ids"]))
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 0


def test_source_authority_used_by_serving_cannot_be_overwritten(prepared):
    from services.data.publication.contract import BootstrapOperation, ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService

    admin, e, p, boot = prepared
    with e.begin() as c:
        publish(c, fact_command(p, boot["ids"]))
        op = BootstrapOperation(
            key="source-change",
            kind="source",
            mode="link",
            canonical_id=p["source_id"],
            values={
                "university_id": boot["ids"]["test:university"],
                "authority_scope": {"years": [2025], "fact_kinds": ["cutoff"]},
            },
            evidence=["snapshot:" + p["snapshot_id"] + "#" + p["evidence"]["locator"]],
        )
        cmd = ReviewCommand(
            request_id=uuid4(),
            action="bootstrap",
            binding=binding_for(p),
            expected_registry_version=p["registry_version"],
            expected_alias_version=p["alias_version"],
            new_registry_version="registry/source-change/" + uuid4().hex,
            new_alias_version=p["alias_version"],
            reason="TEST ONLY unsafe authority change must stop",
            operations=[op],
        )
        with pytest.raises(ValueError):
            ReviewService(c).apply(cmd)


def test_approving_alias_for_serving_university_updates_version_and_refresh(
    publication_database, publication_logins
):
    from services.data.publication.contract import BootstrapOperation, ReviewCommand
    from services.data.publication.packets import binding_for
    from services.data.publication.review import ReviewService
    from tests.publication.helpers import seed_registry

    seed = seed_registry().frozen()
    seed["aliases"] = [
        {
            "key": "test:late-alias",
            "target": "test:university",
            "kind": "domain",
            "value": "example.invalid",
            "review": {"status": "pending", "evidence": ["fixture://TEST-ONLY"]},
        }
    ]
    with publication_database.begin() as c:
        packet = input_packet(c, EntityRegistry.model_validate(seed))
    with publication_logins["reviewer"].begin() as c:
        svc = ReviewService(c)
        boot = svc.apply(bootstrap_command(c, packet))
        p = resolve_again(c, packet, EntityRegistry.model_validate(boot["registry"]))
        first = publish(c, fact_command(p, boot["ids"]))
        op = BootstrapOperation(
            key="test:late-alias",
            kind="alias",
            mode="create",
            values={
                "university_id": boot["ids"]["test:university"],
                "alias": "example.invalid",
                "normalized_alias": "example.invalid",
                "alias_type": "domain",
                "evidence_url": "snapshot:" + p["snapshot_id"] + "#" + p["evidence"]["locator"],
            },
            evidence=["snapshot:" + p["snapshot_id"] + "#" + p["evidence"]["locator"]],
        )
        cmd = ReviewCommand(
            request_id=uuid4(),
            action="bootstrap",
            binding=binding_for(p),
            expected_registry_version=p["registry_version"],
            expected_alias_version=p["alias_version"],
            new_registry_version="registry/late-alias/" + uuid4().hex,
            new_alias_version="aliases/late-alias/" + uuid4().hex,
            reason="TEST ONLY approved alias changes serving labels",
            operations=[op],
        )
        svc.apply(cmd)
        assert (
            c.scalar(sa.text("SELECT dataset_version FROM catalog_state"))
            == first.dataset_version + 1
        )
        assert (
            c.scalar(sa.text("SELECT count(*) FROM ingest_jobs WHERE job_type='refresh_serving'"))
            == 2
        )


def test_reviewed_predicate_has_structured_identity_without_running_rules(prepared):
    admin, e, packet, boot = prepared
    cmd = fact_command(packet, boot["ids"])
    predicate = {
        "schema_version": "conditions/1",
        "kind": "predicate",
        "expression": {"field": "TEST-ONLY-certificate", "operator": "eq", "value": "TEST-PASS"},
    }
    cmd = cmd.model_copy(
        update={
            "fact": cmd.fact.model_copy(
                update={
                    "conditions": predicate,
                    "condition_text": "TEST ONLY reviewed certificate requirement",
                }
            )
        }
    )
    with e.begin() as c:
        draft = reviewed(c, cmd)
        assert draft.scope["condition_dsl"]["conditions"] == predicate
        assert draft.computation_status == "unavailable_rule"
        result = publish(c, cmd)
        assert result.status == "published"
        assert (
            c.scalar(sa.text("SELECT condition_dsl->'conditions' FROM program_admissions"))
            == predicate
        )
