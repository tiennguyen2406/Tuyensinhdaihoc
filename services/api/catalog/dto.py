"""Explicit response allowlists and strict query contracts for catalog/1."""

import re
from datetime import date, datetime
from typing import Annotated, Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Year = Annotated[int, Field(ge=2024, le=2026)]
YearStatus = Literal["unknown", "partial", "published", "verified", "not_collected"]


class Params(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year: Year

    @field_validator("year", mode="before")
    @classmethod
    def integer_year(cls, value: Any) -> Any:
        if isinstance(value, str) and re.fullmatch(r"202[456]", value):
            return int(value)
        if type(value) is int and value in (2024, 2025, 2026):
            return value
        raise ValueError("year must be 2024, 2025 or 2026 as four digits")


class FilterParams(Params):
    university_id: UUID | None = None
    method: str | None = Field(default=None, min_length=1, max_length=40)
    campus: str | None = Field(default=None, min_length=1, max_length=40)


class Pagination(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    cursor: str | None = Field(default=None, max_length=4096)


class Universities(Params, Pagination):
    query: str = Field(default="", max_length=120)
    method: str | None = Field(default=None, min_length=1, max_length=40)
    campus: str | None = Field(default=None, min_length=1, max_length=40)


class Programs(FilterParams, Pagination):
    query: str = Field(default="", max_length=120)


class Cutoffs(FilterParams, Pagination):
    program_id: UUID | None = None
    program_year_id: UUID | None = None


class CoverageParams(FilterParams):
    pass


class NoParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(BaseModel):
    snapshot_id: UUID
    source_id: UUID
    title: str | None
    url: str
    locator: str | None
    source_type: str


class Method(BaseModel):
    id: UUID
    code: str
    name: str


class University(BaseModel):
    id: UUID
    name: str
    code: str
    slug: str
    province: str | None
    type: str | None
    selected_year: Year
    data_status: YearStatus
    program_count: int
    offering_count: int
    cutoff_count: int
    updated_at: datetime
    sources: list[Source]


class UniversityDetail(University):
    methods: list[Method]


class Offering(BaseModel):
    program_id: UUID
    program_name: str
    program_year_id: UUID
    offering_code: str
    offering_name: str
    year: Year
    university_id: UUID
    university_name: str
    campus: str | None
    track: str | None
    language: str | None
    major_id: UUID | None
    major_name: str | None
    method_codes: list[str]
    cutoff_count: int
    tuition: None = None
    scholarships: None = None
    sources: list[Source]


class ProgramDetail(BaseModel):
    id: UUID
    name: str
    university_id: UUID
    selected_year: Year
    major_id: UUID | None
    major_name: str | None
    offerings: list[Offering]


class Scale(BaseModel):
    id: UUID
    code: str
    exam_version: str | None
    min_score: str
    max_score: str
    basis_description: str


class Scope(BaseModel):
    id: UUID
    combination_id: UUID | None
    combination_status: str | None
    round_key: str
    population_key: str
    condition_text: str
    conditions: dict[str, Any] | None
    aggregation_basis: str | None


class Cutoff(BaseModel):
    id: UUID
    program_id: UUID
    program_year_id: UUID
    university_id: UUID
    program_name: str
    offering_code: str
    offering_name: str
    campus: str | None
    year: Year
    method: Method
    score: str
    max_score: str
    scale: Scale
    basis_version: str | None
    scope: Scope
    revision: int
    verification_status: Literal["verified"] = "verified"
    computation_status: str
    sources: list[Source]
    source_published_at: datetime | None
    effective_from: date | None
    updated_at: datetime


class Coverage(BaseModel):
    year: Year
    canonical_cutoff_count: int
    university_count: int
    program_count: int
    offering_count: int
    disputed_cutoff_count: int
    available_years: list[int]
    missing_years: list[int]
    tuition_status: Literal["not_available_in_slice"] = "not_available_in_slice"
    scholarship_status: Literal["not_available_in_slice"] = "not_available_in_slice"
    computation_unavailable_count: int
    admission_year_status_counts: dict[YearStatus, int]


class AdmissionYear(BaseModel):
    year: Year
    data_status: YearStatus
    cutoff_count: int
    offering_count: int


class Release(BaseModel):
    id: UUID
    version: int


class Metadata(BaseModel):
    dataset_version: int
    coverage: Coverage
    warnings: list[str]
    release: Release | None
    contract_version: Literal["catalog/1"] = "catalog/1"


T = TypeVar("T")


class Page(Metadata, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False


class Detail(Metadata, Generic[T]):
    item: T
