"""Fail-closed data guards; not a publisher, score engine, or DSL evaluator."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from sqlalchemy import Connection, Table, event, func, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from services.api.db.models import Base, metadata

TARGET_YEARS = (2024, 2025, 2026)
OFFICIAL_TYPES = {"university", "admission_office", "official_portal", "exam_organizer"}


def record(connection: Connection, table_name: str, identifier: Any) -> Mapping[str, Any]:
    table = metadata.tables[table_name]
    row = connection.execute(select(table).where(table.c.id == identifier)).mappings().one_or_none()
    if row is None:
        raise ValueError(f"Missing referenced {table_name} record")
    return {str(key): value for key, value in row.items()}


def decimal_value(value: Any, places: int) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("Finite Decimal required; float is not accepted")
    try:
        exact = value.quantize(Decimal(1).scaleb(-places))
    except InvalidOperation as error:
        raise ValueError("Decimal exceeds supported precision") from error
    if exact != value:
        raise ValueError("Decimal precision would be lost")
    return value


def validate_source(
    connection: Connection, snapshot_id: Any, offering: Mapping[str, Any], kind: str
) -> None:
    snapshot = record(connection, "source_snapshots", snapshot_id)
    source = record(connection, "sources", snapshot["source_id"])
    authority = source["authority_scope"]
    if source["verification_status"] != "verified" or source["source_type"] not in OFFICIAL_TYPES:
        raise ValueError("A verified authoritative source is required")
    university = offering["university_id"]
    if source["university_id"] != university and str(university) not in authority.get(
        "universities", []
    ):
        raise ValueError("Source authority does not cover this university")
    if offering["admission_year"] not in authority.get("years", []) or kind not in authority.get(
        "fact_kinds", []
    ):
        raise ValueError("Source authority does not cover this year/fact kind")


def validate_admission(connection: Connection, values: Mapping[str, Any]) -> None:
    offering = record(connection, "program_years", values["program_year_id"])
    scale = record(connection, "score_scales", values["score_scale_id"])
    if offering["admission_year"] not in TARGET_YEARS:
        raise ValueError("Admission year outside project scope")
    if scale["admission_year"] != offering["admission_year"]:
        raise ValueError(
            "Cross-year scale requires reviewed compatibility support, not implemented yet"
        )
    if scale["method_id"] != values["method_id"]:
        raise ValueError("Scale method mismatch")
    combination = values.get("combination_id")
    subjects = metadata.tables["combination_subjects"]
    if combination is not None:
        codes: set[str] = set(
            connection.scalars(
                select(subjects.c.subject_code).where(subjects.c.combination_id == combination)
            )
        )
        if len(codes) != 3:
            raise ValueError("A standard combination must contain three subjects")
        if values.get("scoring_rule_id") is not None:
            rule = record(connection, "scoring_rules", values["scoring_rule_id"])
            required = rule["required_components"]
            if (
                not isinstance(required, list)
                or not all(isinstance(code, str) for code in required)
                or not codes.issubset(set(required))
            ):
                raise ValueError("Rule component schema is incompatible with this combination")
    if values.get("scoring_rule_id") is not None:
        rule = record(connection, "scoring_rules", values["scoring_rule_id"])
        if rule["verification_status"] != "verified" or not rule["is_current"]:
            raise ValueError("Admission requires a verified current scoring rule")
    table = metadata.tables["program_admissions"]
    rows = connection.execute(
        select(table.c.id, table.c.condition_key, table.c.condition_dsl)
    ).mappings()
    for other in rows:
        if other["id"] == values.get("id"):
            continue
        same_key = other["condition_key"] == values["condition_key"]
        same_dsl = other["condition_dsl"] == values["condition_dsl"]
        if same_key != same_dsl:
            raise ValueError("Conflicting condition registry; review mapping before publication")


def validate_rule(
    connection: Connection, values: Mapping[str, Any], conversion: bool = False
) -> None:
    offering = record(connection, "program_years", values["program_year_id"])
    pairs = (
        [("from_scale_id", "from_method_id"), ("to_scale_id", "to_method_id")]
        if conversion
        else [("output_scale_id", "method_id")]
    )
    for scale_key, method_key in pairs:
        scale = record(connection, "score_scales", values[scale_key])
        if (
            scale["method_id"] != values[method_key]
            or scale["admission_year"] != offering["admission_year"]
        ):
            raise ValueError(
                "Rule scale/method/year mismatch; unsupported compatibility must be reviewed"
            )
    if values.get("verification_status") == "verified" or values.get("is_current"):
        validate_source(
            connection,
            values["primary_snapshot_id"],
            offering,
            "conversion_rule" if conversion else "scoring_rule",
        )


def validate_cutoff(connection: Connection, values: Mapping[str, Any]) -> None:
    payload = values.get("fact_payload")
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("schema_version"), str)
        or not payload["schema_version"]
    ):
        raise ValueError("Cutoff payload requires schema_version")
    score = decimal_value(values["score"], 5)
    maximum = decimal_value(values["max_score"], 5)
    admission = record(connection, "program_admissions", values["program_admission_id"])
    validate_admission(connection, admission)
    scale = record(connection, "score_scales", values["score_scale_id"])
    if scale["id"] != admission["score_scale_id"] or maximum != scale["max_score"]:
        raise ValueError("Cutoff scale mismatch")
    if not scale["min_score"] <= score <= maximum:
        raise ValueError("Score outside scale bounds")
    if values.get("verification_status") == "verified" or values.get("is_current"):
        offering = record(connection, "program_years", admission["program_year_id"])
        validate_source(connection, values["primary_snapshot_id"], offering, "cutoff")
        validate_source(connection, scale["primary_snapshot_id"], offering, "scoring_rule")


def validate_evidence(connection: Connection, values: Mapping[str, Any]) -> None:
    cutoff = record(connection, "cutoff_scores", values["cutoff_id"])
    observation = record(connection, "observations", values["observation_id"])
    canonical = observation["normalized_fields"].get("canonical_fact")
    if observation["fact_kind"] != "cutoff" or canonical is None:
        raise ValueError("Evidence requires a normalized cutoff canonical payload")
    same = canonical == cutoff["fact_payload"]
    role = values["evidence_role"]
    if role in {"primary", "supporting"}:
        if not same or observation["verification_status"] != "verified":
            raise ValueError("Evidence payload must match verified canonical fact")
        if role == "primary" and observation["snapshot_id"] != cutoff["primary_snapshot_id"]:
            raise ValueError("Primary evidence snapshot mismatch")
        admission = record(connection, "program_admissions", cutoff["program_admission_id"])
        offering = record(connection, "program_years", admission["program_year_id"])
        validate_source(connection, observation["snapshot_id"], offering, "cutoff")
    elif role == "conflicting" and same:
        raise ValueError("Matching evidence cannot be conflicting")


def count_canonical_cutoffs(connection: Connection) -> int:
    cutoffs = metadata.tables["cutoff_scores"]
    admissions = metadata.tables["program_admissions"]
    offerings = metadata.tables["program_years"]
    query = (
        select(func.count())
        .select_from(cutoffs.join(admissions).join(offerings))
        .where(
            cutoffs.c.is_current.is_(True),
            cutoffs.c.verification_status == "verified",
            admissions.c.data_status == "published",
            offerings.c.admission_year.in_(TARGET_YEARS),
        )
    )
    return int(connection.scalar(query) or 0)


def guard_session(session: Session, flush_context: Any, instances: Any) -> None:
    protected = {
        "program_years",
        "program_admissions",
        "cutoff_scores",
        "score_scales",
        "scoring_rules",
        "conversion_rules",
        "dataset_releases",
    }
    for obj in session.deleted:
        if isinstance(obj, Base):
            raise ValueError("Canonical ORM deletion is disabled")
    for obj in session.dirty:
        if (
            isinstance(obj, Base)
            and cast(Table, obj.__table__).name in protected
            and session.is_modified(obj)
        ):
            raise ValueError(
                "Persisted facts/rules are immutable; audited publisher updates belong to T08"
            )
    connection = session.connection()
    for obj in session.new:
        if not isinstance(obj, Base):
            continue
        name = cast(Table, obj.__table__).name
        values = inspect(obj).dict
        if name == "program_admissions":
            validate_admission(connection, values)
        elif name == "cutoff_scores":
            validate_cutoff(connection, values)
        elif name == "cutoff_evidence":
            validate_evidence(connection, values)
        elif name in {"scoring_rules", "conversion_rules"}:
            validate_rule(connection, values, conversion=name == "conversion_rules")
        elif name == "tuition":
            for key in ("amount_min", "amount_max"):
                if values.get(key) is not None:
                    decimal_value(values[key], 2)
        elif name == "dataset_releases":
            raise ValueError("Release publication requires a manifest-verified publisher (T08/T09)")


def install_guards(factory: sessionmaker[Session]) -> None:
    event.listen(factory, "before_flush", guard_session)
