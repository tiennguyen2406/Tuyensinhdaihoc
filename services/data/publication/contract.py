"""Typed review commands and publication payloads. Unknown is never a default scope."""

import hashlib
import json
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

VERSION = "publication/1.2.0"


def canonical_decimal(value: Decimal) -> str:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("Finite Decimal required, never float")
    return "0" if value == 0 else format(value.normalize(), "f")


def json_value(value: Any) -> Any:
    if isinstance(value, float):
        raise ValueError("Float forbidden in canonical payload")
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if isinstance(value, (UUID, date, datetime)):
        return str(value)
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value


def fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            json_value(value),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def bundle_fingerprint(
    identity: dict[str, Any], tuition: list[str], scholarships: list[str]
) -> str:
    return fingerprint(
        dict(
            schema_version="admission-bundle/1",
            identity=identity,
            tuition=sorted(set(tuition)),
            scholarships=sorted(set(scholarships)),
        )
    )


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Binding(Frozen):
    resolution_id: UUID
    candidate_key: str
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SourceRelationship(Frozen):
    snapshot_id: UUID
    locator: str = Field(min_length=1)
    target_host: str = Field(min_length=1)


class BootstrapOperation(Frozen):
    key: str
    kind: Literal[
        "university",
        "major",
        "program",
        "offering",
        "method",
        "year",
        "source",
        "scale",
        "alias",
        "combination",
        "subject",
    ]
    mode: Literal["create", "link"]
    canonical_id: UUID | None = None
    values: dict[str, Any]
    registry_fields: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(min_length=1)


class CutoffSpec(Frozen):
    university_id: UUID
    program_year_id: UUID
    admission_year: int
    method_id: UUID
    combination_id: UUID | None = None
    combination_status: Literal["specified", "confirmed_none", "source_aggregate", "unknown"] = (
        "unknown"
    )
    round_key: str | None = None
    population_key: str | None = None
    conditions: dict[str, Any] | None = None
    condition_text: str | None = None
    score_scale_id: UUID | None = None
    basis_version: str | None = None
    scoring_rule_id: UUID | None = None
    score: Decimal
    effective_from: date | None = None
    source_published_at: datetime | None = None
    supersedes_cutoff_id: UUID | None = None
    replaces_scope_id: UUID | None = None
    evidence: dict[str, list[str]]

    @field_validator("score", mode="before")
    @classmethod
    def no_float(cls, value: Any) -> Any:
        if not isinstance(value, (Decimal, str)):
            raise ValueError("Score must be Decimal/string")
        return value

    @field_validator("source_published_at")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError(
                "Publication timestamp requires timezone; date-only is not a timestamp"
            )
        return value


class ReviewCommand(Frozen):
    request_id: UUID
    action: Literal["bootstrap", "publish", "reject", "request_more", "revoke"]
    binding: Binding
    expected_registry_version: str
    expected_alias_version: str
    reason: str = Field(min_length=8)
    operations: list[BootstrapOperation] = Field(default_factory=list)
    new_registry_version: str | None = None
    new_alias_version: str | None = None
    fact: CutoffSpec | None = None
    expected_revision: int | None = Field(default=None, ge=1)
    revokes_decision_id: UUID | None = None

    @field_validator("reason")
    @classmethod
    def meaningful_reason(cls, value: str) -> str:
        if len(value.strip()) < 8:
            raise ValueError("An explicit review reason is required")
        return value.strip()


class ValidatedDraft(Frozen):
    decision_id: UUID
    decision_sha256: str
    actor_id: str
    packet_sha256: str
    scope: dict[str, Any]
    identity: dict[str, Any]
    payload: dict[str, Any]
    fact: CutoffSpec
    snapshot_id: UUID
    primary_observation_id: UUID
    computation_status: Literal[
        "rule_available_not_evaluated", "unavailable_rule", "unavailable_aggregate_scope"
    ]


class PublicationResult(Frozen):
    status: Literal["published", "unchanged", "corrected", "conflict", "late_ignored", "replaced"]
    cutoff_id: UUID | None
    revision: int | None
    dataset_version: int
    evidence_added: int
    refresh_job_id: UUID | None
    request_job_id: UUID
    cached: bool = False
