import re
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class SourceProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: str = Field(min_length=1)
    university_key: str = Field(min_length=1)
    allowed_hosts: list[str] = Field(min_length=1)
    allowed_document_hosts: list[str] = Field(default_factory=list)
    seed_urls: list[HttpUrl] = Field(min_length=1)
    years: list[Literal[2024, 2025, 2026]] = Field(min_length=1, max_length=3)
    authority_scope: dict[str, list[str | int]]
    parser: str = Field(min_length=1)
    include_path_patterns: list[str] = Field(default_factory=list)
    exclude_path_patterns: list[str] = Field(default_factory=list)
    max_depth: int = Field(default=4, ge=0, le=4)
    max_discovery_urls: int = Field(default=5000, gt=0)
    max_query_variants_per_path: int = Field(default=20, gt=0)
    concurrency: int = Field(default=1, ge=1, le=1)
    requests_per_second: float = Field(default=0.5, gt=0, le=0.5)
    max_burst: int = Field(default=1, ge=1, le=1)
    render_js: bool = False
    source_locale: Literal["vi_VN"] = "vi_VN"
    robots_policy: Literal["obey"] = "obey"
    verified: bool = False
    review_status: Literal["candidate", "checked", "eligible"] = "candidate"
    access_basis: str = "Not reviewed"
    snapshot_basis: str = "Not reviewed; no redistribution permission assumed"
    robots_status: Literal["unknown", "allowed", "denied"] = "unknown"
    review_evidence: list[str] = Field(default_factory=list)
    observed_years: list[Literal[2024, 2025, 2026]] = Field(default_factory=list)
    html_interval_seconds: int = Field(default=21600, ge=3600)
    attachment_interval_seconds: int = Field(default=86400, ge=3600)

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        hosts = self.allowed_hosts + self.allowed_document_hosts
        if any(host != host.lower() or "/" in host or ":" in host or not host for host in hosts):
            raise ValueError("Use exact lowercase hostnames, without paths or schemes")
        if any(
            url.scheme != "https" or url.host not in self.allowed_hosts for url in self.seed_urls
        ):
            raise ValueError("Seed URL must use HTTPS on an allowed host")
        if len(set(self.years)) != len(self.years):
            raise ValueError("Duplicate years")
        if not set(self.observed_years) <= set(self.years):
            raise ValueError("Observed years must be within target years")
        for pattern in self.include_path_patterns + self.exclude_path_patterns:
            re.compile(pattern)
        if self.review_status == "eligible" and (
            self.robots_status != "allowed"
            or not self.review_evidence
            or self.access_basis == "Not reviewed"
        ):
            raise ValueError(
                "Eligible profile needs robots/access evidence; eligibility grants no publication right"
            )
        # Verified is review metadata, not permission for an untrusted API caller to publish.
        return self
