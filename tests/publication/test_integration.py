"""Synthetic registries/packets; all mutations use isolated PostgreSQL test DBs."""

from copy import deepcopy
from uuid import uuid4

import pytest
import sqlalchemy as sa

from services.data.publication.contract import ReviewCommand
from services.data.publication.packets import binding_for
from services.data.publication.review import ReviewService
from tests.publication.helpers import bootstrap_command, input_packet


def prepared(database, logins):
    from services.data.publication.integration import prepare_integration

    # A second unrelated approved registry head must survive proposal integration.
    with database.begin() as c:
        p = input_packet(c)
    with logins["reviewer"].begin() as c:
        first = ReviewService(c).apply(bootstrap_command(c, p))
    from tests.publication.helpers import seed_registry

    seed = seed_registry().frozen()
    seed["entities"][0]["key"] = "other:university"
    seed["entities"][0]["domains"] = ["other.invalid"]
    seed["entities"][1]["university_key"] = "other:university"
    seed["entities"][1]["key"] = "other:method"
    from services.data.resolution.registry import EntityRegistry

    with database.begin() as c:
        p2 = input_packet(c, EntityRegistry.model_validate(seed), host="other.invalid")
        reg = c.scalar(
            sa.text("SELECT payload->'registry' FROM ingest_jobs WHERE id=:id"),
            {"id": p2["resolution_job_id"]},
        )
    keys = [e["key"] for e in reg["entities"]]
    with logins["reviewer"].begin() as c:
        spec = prepare_integration(c, [binding_for(p2)], keys, "registry/integrated/" + uuid4().hex)
    return p2, first, spec


def test_controlled_integration_preserves_approved_head_and_pending_provenance(
    publication_database, publication_logins
):
    p, approved, result = prepared(publication_database, publication_logins)
    with publication_logins["reviewer"].begin() as c:
        assert result["proposal_only"] and not result["execution_ready"]
        assert ReviewService(c).head(p) == (
            approved["registry"]["version"],
            approved["registry"]["alias_version"],
        )
        integrated = result["registry"]
        assert integrated["aliases"] == approved["registry"]["aliases"]
        assert (
            integrated["entities"][: len(approved["registry"]["entities"])]
            == approved["registry"]["entities"]
        )
        assert all(
            e["review"]["status"] == "pending" and e["canonical_id"] is None
            for e in integrated["entities"][len(approved["registry"]["entities"]) :]
        )
        assert len(result["added_keys"]) == 4


def test_integration_future_apply_is_atomic_idempotent_and_legacy_hash_stable(
    publication_database, publication_logins
):
    p, approved, result = prepared(publication_database, publication_logins)
    with publication_logins["reviewer"].begin() as c:
        cmd = bootstrap_command(c, p)
        data = cmd.model_dump(mode="json")
        assert "proposal_integration" not in data and "operation_bindings" not in data
        assert ReviewCommand.model_validate(data).model_dump(mode="json") == data
        # Keep only this synthetic University's identity: no authority/scale approval.
        op = next(o for o in cmd.operations if o.kind == "university")
        op = op.model_copy(
            update={
                "key": "other:university",
                "values": op.values | {"university_code": "TEST-SECOND", "slug": "test-second"},
            }
        )
        data.update(
            expected_registry_version=approved["registry"]["version"],
            expected_alias_version=approved["registry"]["alias_version"],
            proposal_integration=result["spec"],
            operation_bindings={op.key: [binding_for(p).model_dump(mode="json")]},
            operations=[op.model_dump(mode="json")],
        )
        command = ReviewCommand.model_validate(data)
        svc = ReviewService(c)
        reused = ReviewCommand.model_validate(
            data | {"new_registry_version": approved["registry"]["version"]}
        )
        with pytest.raises(ValueError, match="new registry version"):
            svc.plan(reused)
        plan = svc.plan(command)
        assert plan["preview_only"]
        before = c.scalar(sa.text("SELECT count(*) FROM universities"))
        for patch in [
            {"domains": ["unrelated.invalid"]},
            {"attributes": {"table_program_code_system": "other:system"}},
        ]:
            changed = deepcopy(data)
            changed["operations"][0]["registry_fields"] = patch
            with pytest.raises(ValueError, match="identity|metadata"):
                svc.apply(ReviewCommand.model_validate(changed))
        assert c.scalar(sa.text("SELECT count(*) FROM universities")) == before
        out = svc.apply(command)
        assert svc.apply(command) == out
        assert c.scalar(sa.text("SELECT count(*) FROM universities")) == before + 1
        assert c.scalar(sa.text("SELECT count(*) FROM cutoff_scores")) == 0
        assert (
            out["registry"]["entities"][: len(approved["registry"]["entities"])]
            == approved["registry"]["entities"]
        )


@pytest.mark.parametrize("field", ["base_sha256", "registry_sha256"])
def test_tampered_integration_rejected(publication_database, publication_logins, field):
    from services.data.publication.contract import ProposalIntegration
    from services.data.publication.integration import checked_integration

    p, _, result = prepared(publication_database, publication_logins)
    with publication_logins["reviewer"].begin() as c:
        spec = deepcopy(result["spec"])
        spec[field] = "0" * 64
        with pytest.raises(ValueError, match="integration|Integration"):
            checked_integration(
                c, ReviewService(c).registry(p), ProposalIntegration.model_validate(spec)
            )


def test_each_offering_uses_its_own_packet_and_wrong_binding_rolls_back(
    publication_database, publication_logins
):
    from uuid import UUID

    from services.api.db.validators import record
    from services.data.publication.integration import prepare_integration
    from services.data.resolution.registry import EntityRegistry

    with publication_database.begin() as c:
        p = input_packet(c)
        registry = EntityRegistry.model_validate(
            record(c, "ingest_jobs", UUID(p["resolution_job_id"]))["payload"]["registry"]
        )
        second = input_packet(
            c,
            registry.model_copy(update={"version": "registry/second/" + uuid4().hex}),
            campus="BVS",
        )
    with publication_logins["reviewer"].begin() as c:
        reg = record(c, "ingest_jobs", UUID(second["resolution_job_id"]))["payload"]["registry"]
        result = prepare_integration(
            c,
            [binding_for(p), binding_for(second)],
            [e["key"] for e in reg["entities"]],
            "registry/batch/" + uuid4().hex,
        )
        cmd = bootstrap_command(c, p)
        other = bootstrap_command(c, second)
        offering = next(o for o in other.operations if o.kind == "offering")
        offering_entry = next(
            e
            for e in reg["entities"]
            if e["kind"] == "offering" and e["attributes"]["campus"] == "BVS"
        )
        offering = offering.model_copy(
            update={
                "key": offering_entry["key"],
                "registry_fields": {"attributes": offering_entry["attributes"]},
                "values": offering.values
                | {"campus_code": "BVS", "primary_snapshot_id": second["snapshot_id"]},
                "evidence": [
                    "snapshot:" + second["snapshot_id"] + "#" + second["evidence"]["locator"]
                ],
            }
        )
        ops = [
            o
            for o in cmd.operations
            if o.kind in {"university", "method", "year", "program", "offering"}
        ] + [offering]
        # The second campus has a separate source-local Program proposal, not an automatic merge.
        second_program = next(
            e
            for e in reg["entities"]
            if e["key"]
            == next(e for e in reg["entities"] if e["key"] == offering.key)["program_key"]
        )
        program = next(o for o in cmd.operations if o.kind == "program")
        program = program.model_copy(
            update={
                "key": second_program["key"],
                "values": program.values | {"canonical_key": "TEST-SECOND-PROGRAM"},
                "evidence": offering.evidence,
            }
        )
        ops.append(program)
        offering = offering.model_copy(
            update={"values": offering.values | {"program_id": "@" + program.key}}
        )
        ops = [offering if o.key == offering.key else o for o in ops]
        binds = {
            o.key: [
                binding_for(second if o.key in {offering.key, program.key} else p).model_dump(
                    mode="json"
                )
            ]
            for o in ops
        }
        data = cmd.model_dump(mode="json") | dict(
            proposal_integration=result["spec"],
            operation_bindings=binds,
            operations=[o.model_dump(mode="json") for o in ops],
        )
        svc = ReviewService(c)
        valid = ReviewCommand.model_validate(data)
        from uuid import NAMESPACE_URL, uuid5

        explicit = deepcopy(data)
        direct = next(o for o in explicit["operations"] if o["key"] == offering.key)
        direct["values"]["university_id"] = str(
            uuid5(NAMESPACE_URL, "eduradar/review/" + str(cmd.request_id) + "/test:university")
        )
        assert len(svc.plan(ReviewCommand.model_validate(explicit))["effect"]["effects"]) == 7
        assert len(svc.plan(valid)["effect"]["effects"]) == 7
        wrong = deepcopy(data)
        wrong["operation_bindings"][offering.key] = [binding_for(p).model_dump(mode="json")]
        before = {
            t: c.scalar(sa.text("SELECT count(*) FROM " + t))
            for t in ["universities", "programs", "program_years", "audit_events", "ingest_jobs"]
        }
        with pytest.raises(ValueError, match="binding|evidence|packet"):
            svc.apply(ReviewCommand.model_validate(wrong))
        assert before == {t: c.scalar(sa.text("SELECT count(*) FROM " + t)) for t in before}
        wrong_snapshot = deepcopy(data)
        next(o for o in wrong_snapshot["operations"] if o["key"] == offering.key)["values"][
            "primary_snapshot_id"
        ] = p["snapshot_id"]
        with pytest.raises(ValueError, match="snapshot"):
            svc.apply(ReviewCommand.model_validate(wrong_snapshot))
        assert before == {t: c.scalar(sa.text("SELECT count(*) FROM " + t)) for t in before}
        wrong_parent = deepcopy(data)
        second_op = next(o for o in wrong_parent["operations"] if o["key"] == offering.key)
        first_program = next(o for o in cmd.operations if o.kind == "program")
        second_op["registry_fields"]["program_key"] = first_program.key
        second_op["values"]["program_id"] = "@" + first_program.key
        with pytest.raises(ValueError, match="identity metadata"):
            svc.apply(ReviewCommand.model_validate(wrong_parent))
        assert before == {t: c.scalar(sa.text("SELECT count(*) FROM " + t)) for t in before}
        mid_transaction = deepcopy(data)
        next(o for o in mid_transaction["operations"] if o["key"] == program.key)["values"][
            "canonical_key"
        ] = "TEST-PROGRAM"
        collision = ReviewCommand.model_validate(mid_transaction)
        assert svc.plan(collision)["preview_only"]
        with pytest.raises(sa.exc.IntegrityError):
            svc.apply(collision)
        assert before == {t: c.scalar(sa.text("SELECT count(*) FROM " + t)) for t in before}
        out = svc.apply(valid)
        assert svc.apply(valid) == out
        assert c.scalar(sa.text("SELECT count(*) FROM program_years")) == 2
    with publication_database.begin() as c:
        from services.api.db.models import ingest_jobs

        payload = deepcopy(record(c, "ingest_jobs", UUID(second["resolution_job_id"]))["payload"])
        payload["input_sha256"] = "0" * 64
        c.execute(
            ingest_jobs.update()
            .where(ingest_jobs.c.id == UUID(second["resolution_job_id"]))
            .values(payload=payload)
        )
    with publication_logins["reviewer"].begin() as c:
        with pytest.raises(ValueError, match="manifest"):
            ReviewService(c).apply(valid)


def test_duplicate_bindings_unknown_keys_and_stale_heads_are_rejected(
    publication_database, publication_logins
):
    from services.data.publication.integration import prepare_integration
    from services.data.publication.packets import checked_packets

    p, approved, result = prepared(publication_database, publication_logins)
    b = binding_for(p)
    with publication_logins["reviewer"].begin() as c:
        with pytest.raises(ValueError, match="Duplicate"):
            checked_packets(c, [b, b])
        with pytest.raises(ValueError, match="lineage"):
            prepare_integration(c, [b], ["invented:key"], "registry/bad")
        bad = b.model_copy(update={"packet_sha256": "0" * 64})
        with pytest.raises(ValueError, match="digest"):
            checked_packets(c, [bad])
        cmd = bootstrap_command(c, p).model_copy(update={"expected_registry_version": "stale/head"})
        with pytest.raises(ValueError, match="Stale"):
            ReviewService(c).plan(cmd)


def test_exact_review_file_hash_is_checked_before_authentication(tmp_path, monkeypatch, capsys):
    from services.data.publication.__main__ import main

    f = tmp_path / "tampered.json"
    f.write_text("{}", encoding="utf8")
    monkeypatch.setattr("sys.argv", ["review", "plan", "--file", str(f), "--file-sha256", "0" * 64])
    with pytest.raises(ValueError, match="file.*digest"):
        main()


@pytest.mark.parametrize("field", ["input_sha256", "input_envelope_ids", "registry"])
def test_batch_rejects_tampered_parent_manifest(db, field):
    from uuid import UUID

    from services.api.db.models import ingest_jobs
    from services.api.db.validators import record
    from services.data.publication.packets import checked_packets

    p = input_packet(db)
    payload = deepcopy(record(db, "ingest_jobs", UUID(p["resolution_job_id"]))["payload"])
    if field == "registry":
        payload[field]["entities"][0]["name"] = "TAMPERED SOURCE OWNER"
    else:
        payload[field] = "0" * 64 if field == "input_sha256" else payload[field] + [str(uuid4())]
    db.execute(
        ingest_jobs.update()
        .where(ingest_jobs.c.id == UUID(p["resolution_job_id"]))
        .values(payload=payload)
    )
    with pytest.raises(ValueError, match="manifest|parent"):
        checked_packets(db, [binding_for(p)])


@pytest.mark.parametrize("extra", [{"universities": [str(uuid4())]}, {"years": [2024, 2025]}])
def test_batch_authority_cannot_expand_owner_or_year(db, extra):
    from uuid import UUID

    from services.api.db.validators import record
    from services.data.publication.integration import check_operation
    from services.data.resolution.registry import EntityRegistry

    p = input_packet(db)
    cmd = bootstrap_command(db, p)
    seed = EntityRegistry.model_validate(
        record(db, "ingest_jobs", UUID(p["resolution_job_id"]))["payload"]["registry"]
    )
    op = next(o for o in cmd.operations if o.kind == "source")
    uid = uuid4()
    scope = (
        op.values["authority_scope"]
        | {
            "publication_bindings": [
                dict(
                    admission_year=2024,
                    method_code="TEST-THPT",
                    offering_code="TEST-A",
                    campus_code="BVH",
                    snapshot_ids=[p["snapshot_id"]],
                )
            ]
        }
        | extra
    )
    with pytest.raises(ValueError, match="Authority scope"):
        check_operation(
            op,
            [p],
            seed,
            {"test:university": uid},
            dict(university_id=uid, authority_scope=scope),
            cmd,
        )


def test_readonly_integration_cli_and_required_review_file_digest(
    publication_database, publication_logins, tmp_path
):
    import json
    import os
    import subprocess
    import sys

    p, approved, result = prepared(publication_database, publication_logins)
    request = dict(
        version=result["spec"]["version"],
        expected_registry_version=result["expected_registry_version"],
        expected_alias_version=result["expected_alias_version"],
        base_sha256=result["spec"]["base_sha256"],
        bindings=result["spec"]["bindings"],
        proposal_keys=result["spec"]["proposal_keys"],
    )
    f = tmp_path / "request.json"
    f.write_text(json.dumps(request), encoding="utf8")
    env = os.environ.copy() | {"POSTGRES_DB": publication_database.url.database}
    run = subprocess.run(
        [sys.executable, "-m", "services.data.publication", "integrate", "--file", str(f)],
        capture_output=True,
        text=True,
        encoding="utf8",
        env=env,
        timeout=40,
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout) == result
    request["expected_alias_version"] = "stale/aliases"
    f.write_text(json.dumps(request), encoding="utf8")
    run = subprocess.run(
        [sys.executable, "-m", "services.data.publication", "integrate", "--file", str(f)],
        capture_output=True,
        text=True,
        encoding="utf8",
        env=env,
        timeout=40,
    )
    assert run.returncode == 2 and "Stale" in json.loads(run.stderr)["reason"]
    with publication_database.connect() as c:
        cmd = bootstrap_command(c, p).model_dump(mode="json")
    cmd["proposal_integration"] = result["spec"]
    f.write_text(json.dumps(cmd), encoding="utf8")
    run = subprocess.run(
        [sys.executable, "-m", "services.data.publication", "apply", "--file", str(f)],
        capture_output=True,
        text=True,
        encoding="utf8",
        env=env,
        timeout=40,
    )
    assert run.returncode == 2 and "--file-sha256" in json.loads(run.stderr)["reason"]
