"""Local authenticated review, immutable decisions and expected registry versions."""

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from services.api.db.models import ingest_jobs, quality_issues
from services.api.db.validators import record
from services.data.normalization.store import digest
from services.data.publication.access import require
from services.data.publication.bootstrap import audit, operations
from services.data.publication.contract import ReviewCommand, ValidatedDraft, json_value
from services.data.publication.packets import checked_packet
from services.data.resolution.registry import EntityRegistry


class ReviewService:
    def __init__(self, c: Connection):
        self.c = c

    def registry(self, packet: dict[str, Any]) -> EntityRegistry:
        value = self.c.execute(
            sa.select(ingest_jobs.c.payload)
            .where(ingest_jobs.c.job_type == "registry_version")
            .order_by(ingest_jobs.c.created_at.desc(), ingest_jobs.c.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if value is None:
            value = record(self.c, "ingest_jobs", UUID(packet["resolution_job_id"]))["payload"]
        return EntityRegistry.model_validate(value["registry"])

    def head(self, packet: dict[str, Any]) -> tuple[str, str]:
        reg = self.registry(packet)
        return reg.version, reg.alias_version

    def versions(self, cmd: ReviewCommand, packet: dict[str, Any]) -> EntityRegistry:
        reg = self.registry(packet)
        if (cmd.expected_registry_version, cmd.expected_alias_version) != (
            reg.version,
            reg.alias_version,
        ):
            raise ValueError("Stale expected registry/alias version")
        return reg

    def revoked(self, decision_id: UUID) -> bool:
        return bool(
            self.c.scalar(
                sa.select(sa.func.count())
                .select_from(ingest_jobs)
                .where(
                    ingest_jobs.c.job_type == "review_decision",
                    ingest_jobs.c.payload["command"]["action"].astext == "revoke",
                    ingest_jobs.c.payload["command"]["revokes_decision_id"].astext
                    == str(decision_id),
                )
            )
        )

    def plan(self, cmd: ReviewCommand) -> dict[str, Any]:
        packet = checked_packet(self.c, cmd.binding)
        reg = self.versions(cmd, packet)
        try:
            actor = require(self.c, "reviewer")
            allowed = True
        except PermissionError:
            actor = "permission_required"
            allowed = False
        identifier = uuid5(NAMESPACE_URL, "eduradar/decision/" + str(cmd.request_id))
        effect: dict[str, Any] = {}
        if cmd.action == "bootstrap":
            effect = operations(self.c, cmd, reg, actor, identifier, packet, write=False)
        elif cmd.action == "publish":
            from services.data.publication.validate import build_draft

            draft = build_draft(self.c, cmd, identifier, actor, packet)
            effect = dict(
                identity=draft.identity,
                canonical_payload=draft.payload,
                computation_status=draft.computation_status,
            )
        elif cmd.action == "revoke":
            if cmd.revokes_decision_id is None:
                raise ValueError("Revocation target required")
            target = record(self.c, "ingest_jobs", cmd.revokes_decision_id)
            if target["job_type"] != "review_decision":
                raise ValueError("Target is not a review decision")
            applied = self.c.scalar(
                sa.select(sa.func.count())
                .select_from(ingest_jobs)
                .where(
                    ingest_jobs.c.job_type == "publication_request",
                    ingest_jobs.c.payload["decision_id"].astext == str(cmd.revokes_decision_id),
                )
            )
            from services.api.db.models import cutoff_scores

            # ponytail: conservative bootstrap withdrawal gate; dependency-level withdrawal belongs to full review governance.
            bootstrap_in_use = target["payload"]["command"]["action"] == "bootstrap" and bool(
                self.c.scalar(
                    sa.select(sa.func.count())
                    .select_from(cutoff_scores)
                    .where(cutoff_scores.c.is_current.is_(True))
                )
            )
            if applied or bootstrap_in_use:
                raise ValueError(
                    "Published approval requires an explicit serving withdrawal workflow; revoke refused"
                )
        return dict(
            can_apply=allowed,
            action=cmd.action,
            preview_only=True,
            decision_id=str(identifier),
            packet_sha256=packet["packet_sha256"],
            effect=effect,
        )

    def apply(self, cmd: ReviewCommand) -> dict[str, Any]:
        cmd = ReviewCommand.model_validate(json_value(cmd.model_dump(mode="json")))
        actor = require(self.c, "reviewer")
        with self.c.begin_nested():
            self.c.execute(
                sa.select(sa.func.pg_advisory_xact_lock(sa.func.hashtext("T08:registry-review")))
            )
            packet = checked_packet(self.c, cmd.binding)
            key = "review:" + str(cmd.request_id)
            old = (
                self.c.execute(sa.select(ingest_jobs).where(ingest_jobs.c.idempotency_key == key))
                .mappings()
                .one_or_none()
            )
            command_sha = digest(cmd.model_dump(mode="json"))
            if old:
                if old["payload"]["command_sha256"] != command_sha:
                    raise ValueError("Request ID reused for changed decision")
                if self.revoked(old["id"]):
                    raise ValueError("Decision revoked")
                return old["payload"]["result"]
            reg = self.versions(cmd, packet)
            self.plan(cmd)
            identifier = uuid5(NAMESPACE_URL, "eduradar/decision/" + str(cmd.request_id))
            result: dict[str, Any] = dict(
                decision_id=str(identifier),
                status="succeeded"
                if cmd.action in {"bootstrap", "publish", "revoke"}
                else "quarantined",
            )
            environment = None
            validated_payload = None
            validated_scope = None
            validated_snapshot = None
            if cmd.action == "bootstrap":
                effect = operations(self.c, cmd, reg, actor, identifier, packet, write=True)
                result.update(effect)
                if result["catalog_version_delta"]:
                    from services.data.publication.publish import advance_serving

                    version, refresh = advance_serving(self.c)
                    result.update(dataset_version=version, refresh_job_id=str(refresh))
                self.c.execute(
                    ingest_jobs.insert().values(
                        job_type="registry_version",
                        idempotency_key="registry:"
                        + str(cmd.new_registry_version)
                        + ":"
                        + str(cmd.new_alias_version),
                        status="succeeded",
                        payload=dict(
                            registry=effect["registry"],
                            registry_sha256=digest(effect["registry"]),
                            decision_id=str(identifier),
                            parent_registry_version=reg.version,
                            parent_alias_version=reg.alias_version,
                        ),
                    )
                )
            elif cmd.action == "publish":
                from services.data.publication.validate import environment_digest

                environment = environment_digest(self.c, cmd, packet)
                from services.data.publication.validate import build_draft

                approved = build_draft(self.c, cmd, identifier, actor, packet)
                validated_payload = approved.payload
                validated_scope = json_value(approved.scope)
                validated_snapshot = str(approved.snapshot_id)
            elif cmd.action in {"reject", "request_more"}:
                self.c.execute(
                    quality_issues.insert().values(
                        observation_id=cmd.binding.resolution_id,
                        entity_kind="review_packet",
                        issue_code="review_" + cmd.action,
                        severity="warning",
                        status="open",
                        details=dict(
                            packet_sha256=packet["packet_sha256"],
                            reason=cmd.reason,
                            request_id=str(cmd.request_id),
                        ),
                    )
                )
            payload = dict(
                schema_version="review-decision/1",
                actor_id=actor,
                command=cmd.model_dump(mode="json"),
                command_sha256=command_sha,
                packet_sha256=packet["packet_sha256"],
                environment_sha256=environment,
                validated_payload=validated_payload,
                validated_scope=validated_scope,
                validated_snapshot=validated_snapshot,
                result=result,
            )
            audit(
                self.c,
                actor,
                "review_" + cmd.action,
                "review_decision",
                identifier,
                None,
                payload,
                cmd.reason,
                str(cmd.request_id),
            )
            self.c.execute(
                ingest_jobs.insert().values(
                    id=identifier,
                    job_type="review_decision",
                    idempotency_key=key,
                    payload=payload,
                    status=result["status"],
                )
            )
            return result

    def validated(self, decision_id: UUID) -> ValidatedDraft:
        row = record(self.c, "ingest_jobs", decision_id)
        p = row["payload"]
        if (
            row["job_type"] != "review_decision"
            or row["status"] != "succeeded"
            or self.revoked(decision_id)
        ):
            raise ValueError("Pending/revoked/non-approved decision")
        cmd = ReviewCommand.model_validate(p["command"])
        if cmd.action != "publish" or digest(cmd.model_dump(mode="json")) != p["command_sha256"]:
            raise ValueError("Approved publication decision required")
        packet = checked_packet(self.c, cmd.binding)
        self.versions(cmd, packet)
        from services.data.publication.validate import build_draft, environment_digest

        if environment_digest(self.c, cmd, packet) != p["environment_sha256"]:
            raise ValueError("Reviewed canonical environment changed")
        return build_draft(self.c, cmd, decision_id, p["actor_id"], packet)
