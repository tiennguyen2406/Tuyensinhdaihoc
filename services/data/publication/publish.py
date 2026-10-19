"""Short PostgreSQL transaction: canonical revisions, evidence, audit, version and refresh."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from services.api.db.models import (
    catalog_state,
    cutoff_evidence,
    cutoff_scores,
    ingest_jobs,
    observations,
    program_admissions,
    quality_issues,
)
from services.api.db.validators import (
    record,
    validate_admission,
    validate_cutoff,
    validate_evidence,
)
from services.data.publication.access import require
from services.data.publication.bootstrap import audit
from services.data.publication.contract import (
    VERSION,
    PublicationResult,
    ValidatedDraft,
    fingerprint,
)
from services.data.publication.review import ReviewService


def advance_serving(c: Connection) -> tuple[int, UUID]:
    version: int = c.execute(
        catalog_state.update()
        .values(dataset_version=catalog_state.c.dataset_version + 1, changed_at=sa.func.now())
        .returning(catalog_state.c.dataset_version)
    ).scalar_one()
    refresh: UUID = c.execute(
        ingest_jobs.insert()
        .values(
            job_type="refresh_serving",
            idempotency_key="refresh_serving:" + str(version),
            status="queued",
            payload=dict(dataset_version=version, release_builder="not_implemented_T09"),
        )
        .returning(ingest_jobs.c.id)
    ).scalar_one()
    return version, refresh


class Publisher:
    def __init__(self, c: Connection):
        self.c = c

    def evidence(self, d: ValidatedDraft, cutoff: dict[str, Any], role: str) -> int:
        c = self.c
        existing = c.execute(
            sa.select(observations.c.id)
            .join(cutoff_evidence, cutoff_evidence.c.observation_id == observations.c.id)
            .where(
                cutoff_evidence.c.cutoff_id == cutoff["id"],
                observations.c.raw_fields["raw_observation_id"].astext
                == str(d.primary_observation_id),
                observations.c.normalized_fields["canonical_fact"] == d.payload,
            )
        ).scalar_one_or_none()
        if existing:
            return 0
        raw = record(c, "observations", d.primary_observation_id)
        data = dict(
            canonical_fact=d.payload,
            review_decision_id=str(d.decision_id),
            input_packet_sha256=d.packet_sha256,
        )
        identifier = c.execute(
            insert(observations)
            .values(
                snapshot_id=d.snapshot_id,
                fact_kind="cutoff",
                record_locator=raw["record_locator"] + "/review:" + str(d.decision_id),
                parser_version=raw["parser_version"],
                transform_version="validated/1;" + VERSION,
                raw_fields=dict(
                    raw_observation_id=str(d.primary_observation_id), decision_id=str(d.decision_id)
                ),
                normalized_fields=data,
                payload_hash=fingerprint(data),
                extraction_method="reviewed_publication",
                verification_status="verified",
            )
            .on_conflict_do_nothing()
            .returning(observations.c.id)
        ).scalar_one_or_none()
        if identifier is None:
            identifier = c.scalar(
                sa.select(observations.c.id).where(
                    observations.c.raw_fields["decision_id"].astext == str(d.decision_id),
                    observations.c.normalized_fields["canonical_fact"] == d.payload,
                )
            )
        values = dict(cutoff_id=cutoff["id"], observation_id=identifier, evidence_role=role)
        validate_evidence(c, values)
        added = c.execute(
            insert(cutoff_evidence)
            .values(**values)
            .on_conflict_do_nothing()
            .returning(cutoff_evidence.c.observation_id)
        ).scalar_one_or_none()
        return int(added is not None)

    def transition(
        self,
        actor: str,
        old: dict[str, Any],
        changes: dict[str, Any],
        action: str,
        d: ValidatedDraft,
    ) -> None:
        after = old | changes
        tx = str(self.c.scalar(sa.text("SELECT pg_current_xact_id()::text")))
        audit(
            self.c,
            actor,
            action,
            "cutoff",
            old["id"],
            old,
            {"row": after, "transaction_id": tx},
            "Reviewed decision " + str(d.decision_id),
            str(d.decision_id),
        )
        self.c.execute(
            cutoff_scores.update().where(cutoff_scores.c.id == old["id"]).values(**changes)
        )

    def publish(self, draft: ValidatedDraft, expected_revision: int | None) -> PublicationResult:
        actor = require(self.c, "publisher")
        with self.c.begin_nested():
            return self._publish(draft, expected_revision, actor)

    def _publish(
        self, draft: ValidatedDraft, expected_revision: int | None, actor: str
    ) -> PublicationResult:
        c = self.c
        c.execute(
            sa.select(sa.func.pg_advisory_xact_lock_shared(sa.func.hashtext("T08:registry-review")))
        )
        fresh = ReviewService(c).validated(draft.decision_id)
        if fresh != draft:
            raise ValueError("ValidatedDraft does not match its approved decision")
        decision = record(c, "ingest_jobs", draft.decision_id)["payload"]
        if decision["command"]["expected_revision"] != expected_revision:
            raise ValueError("Expected revision differs from review decision")
        key = "publish:" + str(draft.decision_id)
        c.execute(
            sa.select(
                sa.func.pg_advisory_xact_lock(
                    sa.func.hashtext(
                        "T08:publish:"
                        + fingerprint(
                            {k: v for k, v in draft.identity.items() if k != "condition_key"}
                        )
                    )
                )
            )
        )
        oldjob = (
            c.execute(sa.select(ingest_jobs).where(ingest_jobs.c.idempotency_key == key))
            .mappings()
            .one_or_none()
        )
        if oldjob:
            return PublicationResult.model_validate(oldjob["payload"]["result"]).model_copy(
                update={"cached": True}
            )
        scope = draft.scope
        keys = [
            "program_year_id",
            "method_id",
            "combination_id",
            "round_key",
            "population_key",
            "condition_key",
        ]
        admission: Any = (
            c.execute(
                sa.select(program_admissions).where(
                    *(program_admissions.c[k] == scope[k] for k in keys)
                )
            )
            .mappings()
            .one_or_none()
        )
        related = (
            c.execute(
                sa.select(program_admissions).where(
                    *(program_admissions.c[k] == scope[k] for k in keys if k != "condition_key"),
                    program_admissions.c.condition_key != scope["condition_key"],
                    program_admissions.c.condition_dsl["conditions"] == draft.fact.conditions,
                    program_admissions.c.data_status == "published",
                )
            )
            .mappings()
            .all()
        )
        active = []
        for prior in related:
            fact = (
                c.execute(
                    sa.select(cutoff_scores)
                    .where(
                        cutoff_scores.c.program_admission_id == prior["id"],
                        cutoff_scores.c.is_current.is_(True),
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if fact:
                active.append((prior, fact))
        replacement = False
        if active:
            if len(active) != 1 or draft.fact.replaces_scope_id != active[0][0]["id"]:
                raise ValueError("Basis change requires explicit reviewed replacement scope")
            prior, prior_fact = active[0]
            if draft.fact.basis_version == prior["condition_dsl"].get("basis_version"):
                raise ValueError("Basis replacement requires a new basis version")
            if expected_revision is None or prior_fact["revision"] != expected_revision:
                raise ValueError("Stale expected replacement revision")
            self.transition(
                actor,
                dict(prior_fact),
                dict(is_current=False, system_valid_to=datetime.now(timezone.utc)),
                "retire_cutoff",
                draft,
            )
            withdrawn = dict(prior) | {"data_status": "withdrawn"}
            audit(
                c,
                actor,
                "withdraw_scope",
                "admission_scope",
                prior["id"],
                dict(prior),
                {
                    "row": withdrawn,
                    "transaction_id": str(c.scalar(sa.text("SELECT pg_current_xact_id()::text"))),
                },
                decision["command"]["reason"],
                str(draft.decision_id),
            )
            c.execute(
                program_admissions.update()
                .where(program_admissions.c.id == prior["id"])
                .values(data_status="withdrawn")
            )
            replacement = True
        elif draft.fact.replaces_scope_id:
            raise ValueError("Replacement target is not a current related scope")
        if admission is None:
            validate_admission(c, scope)
            aid = uuid4()
            audit(
                c,
                actor,
                "create_scope",
                "admission_scope",
                aid,
                None,
                {
                    "row": dict(scope, id=aid),
                    "transaction_id": str(c.scalar(sa.text("SELECT pg_current_xact_id()::text"))),
                },
                decision["command"]["reason"],
                str(draft.decision_id),
            )
            c.execute(program_admissions.insert().values(id=aid, **scope))
            admission = record(c, "program_admissions", aid)
        else:
            if (
                any(
                    admission[k] != scope[k]
                    for k in ["score_scale_id", "scoring_rule_id", "condition_dsl"]
                )
                or admission["data_status"] != "published"
            ):
                raise ValueError("Scope basis changed; create reviewed replacement scope")
        current: Any = (
            c.execute(
                sa.select(cutoff_scores)
                .where(
                    cutoff_scores.c.program_admission_id == admission["id"],
                    cutoff_scores.c.is_current.is_(True),
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if (
            not replacement
            and expected_revision is not None
            and (current is None or current["revision"] != expected_revision)
        ):
            raise ValueError("Stale expected cutoff revision")
        same = current is not None and current["fact_payload"] == draft.payload
        if current and current["fact_fingerprint"] == fingerprint(draft.payload) and not same:
            raise ValueError("Fingerprint collision/canonical payload mismatch")
        status: Any = "unchanged"
        changed = False
        if not same:
            if current is None or draft.fact.supersedes_cutoff_id == current["id"]:
                if current:
                    if expected_revision is None:
                        raise ValueError("Correction requires expected revision")
                    incoming = draft.fact.source_published_at
                    if (
                        incoming
                        and current["source_published_at"]
                        and incoming < current["source_published_at"]
                    ):
                        raise ValueError("Older publication cannot supersede current correction")
                    self.transition(
                        actor,
                        dict(current),
                        dict(is_current=False, system_valid_to=datetime.now(timezone.utc)),
                        "retire_cutoff",
                        draft,
                    )
                revision = current["revision"] + 1 if current else 1
                values = dict(
                    id=uuid4(),
                    program_admission_id=admission["id"],
                    revision=revision,
                    score_scale_id=draft.fact.score_scale_id,
                    score=draft.fact.score,
                    max_score=record(c, "score_scales", draft.fact.score_scale_id)["max_score"],
                    fact_payload=draft.payload,
                    fact_fingerprint=fingerprint(draft.payload),
                    publication_group_key="publication/1:" + str(draft.primary_observation_id),
                    primary_snapshot_id=draft.snapshot_id,
                    source_published_at=draft.fact.source_published_at,
                    effective_from=draft.fact.effective_from,
                    verification_status="verified",
                    is_current=True,
                    reviewed_by=draft.actor_id,
                    review_reason=decision["command"]["reason"],
                )
                validate_cutoff(c, values)
                tx = str(c.scalar(sa.text("SELECT pg_current_xact_id()::text")))
                audit(
                    c,
                    actor,
                    "publish_cutoff",
                    "cutoff",
                    values["id"],
                    None,
                    {"row": values, "transaction_id": tx},
                    decision["command"]["reason"],
                    str(draft.decision_id),
                )
                c.execute(cutoff_scores.insert().values(**values))
                current = values
                status = "replaced" if replacement else "corrected" if revision > 1 else "published"
                changed = True
            else:
                status = "conflict"
                if current["verification_status"] != "disputed":
                    self.transition(
                        actor,
                        dict(current),
                        dict(verification_status="disputed"),
                        "dispute_cutoff",
                        draft,
                    )
                    changed = True
                c.execute(
                    quality_issues.insert().values(
                        observation_id=draft.primary_observation_id,
                        entity_kind="cutoff",
                        entity_id=current["id"],
                        issue_code="publication_conflict",
                        severity="error",
                        status="open",
                        details=dict(
                            decision_id=str(draft.decision_id),
                            incoming=draft.payload,
                            current=current["fact_payload"],
                        ),
                    )
                )
        assert current is not None
        added = self.evidence(
            draft,
            dict(current),
            "conflicting"
            if status == "conflict"
            else "primary"
            if status in {"published", "corrected", "replaced"}
            else "supporting",
        )
        changed = changed or bool(added)
        refresh: UUID | None = None
        version: int
        if changed:
            version, refresh = advance_serving(c)
        else:
            version = int(c.scalar(sa.select(catalog_state.c.dataset_version)) or 0)
        identifier = uuid4()
        result = PublicationResult(
            status=status,
            cutoff_id=current["id"],
            revision=current["revision"],
            dataset_version=version,
            evidence_added=added,
            refresh_job_id=refresh,
            request_job_id=identifier,
        )
        audit(
            c,
            actor,
            "publication_result",
            "cutoff",
            current["id"],
            None,
            result.model_dump(mode="json"),
            decision["command"]["reason"],
            str(draft.decision_id),
        )
        c.execute(
            ingest_jobs.insert().values(
                id=identifier,
                job_type="publication_request",
                idempotency_key=key,
                status="succeeded",
                payload=dict(
                    decision_id=str(draft.decision_id), result=result.model_dump(mode="json")
                ),
            )
        )
        return result
