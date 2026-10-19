"""T06 envelopes: mapped candidates are unverified drafts, never canonical facts."""

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from services.data.normalization.values import NumericValue, TextValue
from services.data.parsers.contract import TRANSFORM_VERSION, FactKind

VERSION = "normalizer/1.0.0"


class RawObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    id: UUID
    snapshot_id: UUID
    source_id: UUID | None = None
    fact_kind: FactKind
    record_locator: str
    parser_version: str
    transform_version: str = TRANSFORM_VERSION
    extraction_method: str
    extraction_confidence: Decimal | None = None
    raw_fields: dict[str, Any]
    normalized_fields: dict[str, Any] = Field(default_factory=dict)


class NormalizationContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    version: str = VERSION
    target_years: tuple[int, ...] = (2024, 2025, 2026)
    training_modes: tuple[str, ...] = ("Chính quy",)
    require_campus: bool = True
    document_issues: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def transform_version(self) -> str:
        return f"normalization/1;{self.version};resolver=none;aliases=none"


class Issue(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str
    level: Literal["document", "row", "cell", "field"]
    locator: str
    field: str | None = None
    blocks_candidate: bool
    detail: str
    origin: Literal["normalizer", "parser"] = "normalizer"


class Lineage(BaseModel):
    model_config = ConfigDict(frozen=True)
    observation_id: UUID
    snapshot_id: UUID
    source_id: UUID | None
    parser_version: str
    input_transform_version: str
    normalizer_version: str
    row_locator: str
    cell_locator: str
    column: int | None = None
    header_path: list[dict[str, Any]]
    raw_value: str
    bbox: list[float] | None = None
    context: list[dict[str, Any]]
    footnotes: list[dict[str, Any]]
    scope_evidence: dict[str, Any] = Field(default_factory=dict)


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    candidate_key: str
    fact_kind: FactKind
    admission_year: int | None = None
    document_year: int | None = None
    academic_year: str | None = None
    method: TextValue | None = None
    value: NumericValue
    scope: dict[str, Any]
    lineage: Lineage
    score_scale: None = None
    combinations: None = None
    round: None = None
    population: None = None
    conditions: None = None
    entity_ids: dict[str, str] = Field(default_factory=dict)
    verification_status: Literal["unverified"] = "unverified"
    status: Literal["needs_review"] = "needs_review"
    issues: list[Issue] = Field(default_factory=list)


class Blocked(BaseModel):
    value: NumericValue | None = None
    cell_locator: str
    raw_value: str | None
    header_path: list[dict[str, Any]]
    admission_year: int | None = None
    method: str | None = None
    issues: list[Issue]


class NormalizedObservation(BaseModel):
    schema_version: Literal["normalization-envelope/1"] = "normalization-envelope/1"
    input_observation_id: UUID
    snapshot_id: UUID
    normalizer_version: str
    transform_version: str
    candidates: list[Candidate] = Field(default_factory=list)
    blocked: list[Blocked] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    display_fields: dict[str, TextValue] = Field(default_factory=dict)
    status: Literal["needs_review"] = "needs_review"
