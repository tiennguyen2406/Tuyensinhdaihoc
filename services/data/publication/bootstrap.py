"""Ordered, reviewed canonical creation/linking. No approved-UUID bootstrap cycle."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from services.api.db.models import audit_events, metadata
from services.api.db.validators import decimal_value, record
from services.data.publication.contract import ReviewCommand, json_value
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.store import validate_targets

TABLES = {
    "university": "universities",
    "major": "majors",
    "program": "programs",
    "offering": "program_years",
    "method": "admission_methods",
    "year": "admission_years",
    "source": "sources",
    "scale": "score_scales",
    "alias": "university_aliases",
    "subject": "subjects",
    "combination": "combinations",
}
ORDER = [
    "university",
    "method",
    "major",
    "source",
    "year",
    "subject",
    "combination",
    "program",
    "offering",
    "scale",
    "alias",
]
IMMUTABLE_FIELDS = {
    "created_at",
    "updated_at",
    "reviewed_by",
    "approved_by",
    "verification_status",
    "id",
}


def audit(
    c: Connection,
    actor: str,
    action: str,
    kind: str,
    identifier: UUID | None,
    before: Any,
    after: Any,
    reason: str,
    request: str,
) -> None:
    c.execute(
        audit_events.insert().values(
            actor_id=actor,
            action=action,
            entity_kind=kind,
            entity_id=identifier,
            before_data=json_value(before),
            after_data=json_value(after),
            reason=reason,
            request_id=request,
        )
    )


def operations(
    c: Connection,
    cmd: ReviewCommand,
    seed: EntityRegistry,
    actor: str,
    decision_id: UUID,
    packet: dict[str, Any],
    *,
    write: bool,
) -> dict[str, Any]:
    if not cmd.operations or not cmd.new_registry_version or not cmd.new_alias_version:
        raise ValueError("Bootstrap needs operations and explicit new versions")
    if len({o.key for o in cmd.operations}) != len(cmd.operations):
        raise ValueError("Duplicate operation key")
    if cmd.new_registry_version == seed.version:
        raise ValueError("Bootstrap needs a new registry version")
    if (
        any(o.kind == "alias" for o in cmd.operations)
        and cmd.new_alias_version == seed.alias_version
    ):
        raise ValueError("Alias approval needs a new alias version")
    reg = seed.frozen()
    ids = {e.key: e.canonical_id for e in seed.entities if e.canonical_id}
    effects = []
    for op in sorted(cmd.operations, key=lambda o: ORDER.index(o.kind)):
        for evidence in op.evidence:
            if not evidence.startswith("snapshot:") or "#" not in evidence:
                raise ValueError("Bootstrap evidence requires a cached snapshot and locator")
            sid, locator = evidence[9:].split("#", 1)
            record(c, "source_snapshots", UUID(sid))
            if not locator.strip():
                raise ValueError("Bootstrap evidence locator is empty")
        table = metadata.tables[TABLES[op.kind]]

        def ref(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("@"):
                if value[1:] not in ids:
                    raise ValueError("Unresolved parent operation")
                return ids[value[1:]]
            return value

        values = {k: ref(v) for k, v in op.values.items()}
        subjects = values.pop("subjects", None) if op.kind == "combination" else None
        if set(values) - set(table.c.keys()) or set(values) & IMMUTABLE_FIELDS:
            raise ValueError("Unsupported/client-controlled canonical column")
        if op.kind == "source":
            if op.mode != "link" or op.canonical_id != UUID(packet["source_id"]):
                raise ValueError("Authority review must link this packet source")
            if set(values) != {"university_id", "authority_scope"}:
                raise ValueError("Explicit source authority required")
            values["verification_status"] = "verified"
        elif op.kind == "university":
            values["verification_status"] = "verified"
        elif op.kind == "alias":
            values["approved_by"] = actor
        for key, value in list(values.items()):
            col = table.c[key]
            if isinstance(col.type, sa.Uuid) and value is not None:
                values[key] = UUID(str(value))
            if isinstance(col.type, sa.Numeric) and value is not None:
                if isinstance(value, float):
                    raise ValueError("Decimal/string required")
                values[key] = decimal_value(Decimal(value), 5)
            if isinstance(col.type, sa.Date) and isinstance(value, str):
                values[key] = date.fromisoformat(value)
        if op.kind == "offering":
            for key in ["campus_code", "track_code", "language_code"]:
                if key not in values:
                    raise ValueError("Offering context must be explicit, unknown is UNSPECIFIED")
            if values.get("admission_year") != packet["candidate"]["admission_year"]:
                raise ValueError("Offering year conflicts with candidate evidence")
            scope = packet["candidate"]["scope"]
            if values.get("offering_code") != (scope.get("offering_code") or {}).get("display"):
                raise ValueError("Offering code conflicts with source")
            if values.get("campus_code") != (
                (scope.get("campus") or {}).get("display") or "UNSPECIFIED"
            ):
                raise ValueError("Offering campus conflicts with source")
            if "training_mode" not in op.registry_fields.get("attributes", {}):
                raise ValueError("Training mode review must be explicit")
        identifier = (
            op.canonical_id
            if op.mode == "link"
            else uuid5(NAMESPACE_URL, "eduradar/review/" + str(cmd.request_id) + "/" + op.key)
        )
        if op.mode == "link":
            if identifier is None:
                raise ValueError("Link requires canonical UUID")
            old = dict(record(c, table.name, identifier))
            if (
                op.kind == "source"
                and old["verification_status"] == "verified"
                and any(old[k] != v for k, v in values.items())
            ):
                from services.api.db.models import cutoff_scores

                # ponytail: freeze verified authority globally once any fact serves; finer withdrawal/authority versions require governance.
                if c.scalar(
                    sa.select(sa.func.count())
                    .select_from(cutoff_scores)
                    .where(cutoff_scores.c.is_current.is_(True))
                ):
                    raise ValueError(
                        "Serving source authority change requires explicit withdrawal/version workflow"
                    )
            if op.kind != "source" and any(old[k] != v for k, v in values.items()):
                raise ValueError("Linked canonical context mismatch")
            if op.kind == "university" and old["verification_status"] != "verified":
                raise ValueError("Linked university must already be verified")
            if write and op.kind == "source":
                c.execute(table.update().where(table.c.id == identifier).values(**values))
        else:
            old = None
            if "id" in table.c:
                values["id"] = identifier
            required = [
                col.name
                for col in table.c
                if not col.nullable and col.server_default is None and col.name not in values
            ]
            if required:
                raise ValueError("Missing canonical fields: " + ",".join(required))
            if write:
                c.execute(table.insert().values(**values))
        assert identifier is not None
        ids[op.key] = identifier
        if op.kind == "combination":
            if not isinstance(subjects, list) or len(set(subjects)) != 3:
                raise ValueError("Three explicit combination subjects required")
            if write:
                for i, code in enumerate(subjects, 1):
                    c.execute(
                        metadata.tables["combination_subjects"]
                        .insert()
                        .values(combination_id=identifier, subject_code=code, position=i)
                    )
        after = values | ({"id": identifier} if "id" in table.c else {})
        if write:
            audit(
                c,
                actor,
                "bootstrap_" + op.mode,
                op.kind,
                identifier,
                old,
                {"row": after, "decision_id": str(decision_id), "evidence": op.evidence},
                cmd.reason,
                str(cmd.request_id),
            )
        effects.append(dict(key=op.key, kind=op.kind, mode=op.mode, planned_id=str(identifier)))
        if op.kind in {"university", "major", "program", "offering", "method"}:
            matches = [e for e in reg["entities"] if e["key"] == op.key]
            if not matches:
                raise ValueError("Canonical entity must have an explicit registry proposal")
            e = matches[0]
            if e["kind"] != op.kind:
                raise ValueError("Entity kind mismatch")
            patch = op.registry_fields
            if set(patch) - {
                "name",
                "domains",
                "codes",
                "attributes",
                "university_key",
                "program_key",
                "major_key",
            }:
                raise ValueError("Unsupported registry metadata")
            e.update(
                patch,
                canonical_id=str(identifier),
                review={
                    "status": "approved",
                    "reviewer": actor,
                    "at": datetime.now(timezone.utc).date().isoformat(),
                    "evidence": op.evidence + ["decision:" + str(decision_id)],
                },
            )
            if op.kind == "method":
                e.setdefault("attributes", {})["input_kind"] = values.get(
                    "input_kind", old["input_kind"] if old else None
                )
        elif op.kind == "alias":
            found = [a for a in reg["aliases"] if a["key"] == op.key]
            if len(found) != 1:
                raise ValueError("Alias approval requires an explicit proposed alias")
            a = found[0]
            target = next(e for e in reg["entities"] if e["key"] == a["target"])
            if target.get("canonical_id") != str(values.get("university_id")) or a[
                "value"
            ] != values.get("alias"):
                raise ValueError("Alias target/value mismatch")
            a["review"] = {
                "status": "approved",
                "reviewer": actor,
                "at": datetime.now(timezone.utc).date().isoformat(),
                "evidence": op.evidence + ["decision:" + str(decision_id)],
            }
    reg.update(
        version=cmd.new_registry_version,
        alias_version=cmd.new_alias_version,
        classification="reviewed",
    )
    registry = EntityRegistry.model_validate(reg)
    if write:
        validate_targets(c, registry)
    return dict(
        registry=registry.frozen(), effects=effects, ids={k: str(v) for k, v in ids.items()}
    )


def alias_affects_serving(c: Connection, cmd: ReviewCommand, effect: dict[str, Any]) -> bool:
    from services.api.db.models import cutoff_scores, program_admissions, program_years

    for op in cmd.operations:
        if op.kind != "alias" or op.mode != "create":
            continue
        owner = op.values.get("university_id")
        if isinstance(owner, str) and owner.startswith("@"):
            owner = effect["ids"].get(owner[1:])
        if owner is None:
            continue
        exists = c.scalar(
            sa.select(sa.func.count())
            .select_from(cutoff_scores.join(program_admissions).join(program_years))
            .where(
                cutoff_scores.c.is_current.is_(True),
                program_years.c.university_id == UUID(str(owner)),
            )
        )
        if exists:
            return True
    return False
