"""T05 raw contracts: Decimal confidence is extraction confidence, never admission likelihood."""

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FactKind = Literal[
    "cutoff", "tuition", "scholarship", "exam_event", "scoring_rule", "conversion_rule", "catalog"
]
TRANSFORM_VERSION = "raw-only/1;normalizer=none;resolver=none;aliases=none"


class SnapshotRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    snapshot_id: UUID
    source_id: UUID | None = None
    raw_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_uri: str
    final_url: str
    media_type: str
    byte_size: int = Field(ge=0)


class ParseLimits(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    max_bytes: int = Field(default=25 * 1024 * 1024, ge=1, le=25 * 1024 * 1024)
    max_pages: int = Field(default=200, ge=1, le=200)
    max_cells: int = Field(default=200000, ge=1, le=200000)
    timeout_seconds: float = Field(default=60, gt=0, le=60)
    max_rss_bytes: int = Field(default=512 * 1024 * 1024, ge=1024 * 1024, le=512 * 1024 * 1024)
    max_output_bytes: int = Field(default=32 * 1024 * 1024, ge=1, le=32 * 1024 * 1024)


class ParseIssue(BaseModel):
    code: str
    locator: str
    detail: str
    severity: Literal["warning", "error"] = "warning"


class ExtractedObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    snapshot_id: UUID
    source_id: UUID | None
    fact_kind: FactKind
    record_locator: str
    parser_version: str
    transform_version: str = TRANSFORM_VERSION
    extraction_method: Literal["html_dom", "pdf_text", "pdf_table"]
    raw_fields: dict[str, Any]
    extraction_confidence: Decimal = Field(
        ge=Decimal(0), le=Decimal(1), max_digits=5, decimal_places=4
    )
    issues: list[ParseIssue] = Field(default_factory=list)
    verification_status: Literal["unverified"] = "unverified"


class ParseResult(BaseModel):
    observations: list[ExtractedObservation] = Field(default_factory=list)
    issues: list[ParseIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def needs_review(self) -> bool:
        return bool(self.issues or any(o.issues for o in self.observations))

    def issue(
        self,
        code: str,
        locator: str,
        detail: str,
        severity: Literal["warning", "error"] = "warning",
    ) -> None:
        self.issues.append(ParseIssue(code=code, locator=locator, detail=detail, severity=severity))
