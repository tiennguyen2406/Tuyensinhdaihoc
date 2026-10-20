from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from services.data.normalization.contract import NormalizedObservation

VERSION = "resolver/1.0.8"
Kind = Literal["university", "major", "program", "offering", "method", "scope"]
State = Literal["resolved", "partial", "ambiguous", "unresolved"]


class EntityQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Kind
    name: str | None = None
    code: str | None = None
    code_system: str | None = None
    domain: str | None = None
    university_key: str | None = None
    program_key: str | None = None
    attributes: dict[str, str | int | None] = Field(default_factory=dict)


class Option(BaseModel):
    entity_key: str
    proposal_key: str | None
    canonical_id: UUID | None
    method: str
    score: float
    features: dict[str, Any]
    conflicts: list[str]
    missing: list[str]
    eligible: bool
    auto_eligible: bool
    alias_keys: list[str]
    evidence: list[str]


class EntityMatch(BaseModel):
    kind: Kind
    status: State = "unresolved"
    entity_key: str | None = None
    canonical_id: UUID | None = None
    method: str | None = None
    options: list[Option] = Field(default_factory=list)
    blocked_entities: dict[str, list[str]] = Field(default_factory=dict)
    margin: float | None = None
    reasons: list[str] = Field(default_factory=list)


class ResolutionInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    envelope_id: UUID
    envelope: NormalizedObservation
    final_url: str
    source_id: UUID


class CandidateResolution(BaseModel):
    candidate_key: str
    input_envelope_id: UUID
    raw_observation_id: UUID
    snapshot_id: UUID
    lineage: dict[str, Any]
    fact_kind: str
    admission_year: int | None
    academic_year: str | None
    status: State
    entities: dict[str, EntityMatch]
    dependencies: list[str]
    preserved_input_issues: list[dict[str, Any]]
    queries: dict[str, EntityQuery]
    unresolved_fields: dict[str, Any]
    publication_eligible: Literal[False] = False
    publication_blockers: list[str]
    verification_status: Literal["unverified"] = "unverified"


class EntityResolution(BaseModel):
    schema_version: Literal["entity-resolution/1"] = "entity-resolution/1"
    input_envelope_id: UUID
    normalizer_namespace: str
    resolver_version: str = VERSION
    registry_version: str
    alias_version: str
    candidates: list[CandidateResolution]
    blocked_input_attempts: int
    input_issue_count: int
