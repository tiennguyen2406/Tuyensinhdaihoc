"""Versioned review records. Pending proposals can never carry approved canonical UUIDs."""

from datetime import date
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.data.resolution.contract import Kind


class Review(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    status: Literal["pending", "approved", "revoked"] = "pending"
    evidence: list[str] = Field(min_length=1)
    reviewer: str | None = None
    at: date | None = None

    @model_validator(mode="after")
    def approval(self) -> "Review":
        if self.status in {"approved", "revoked"} and (not self.reviewer or not self.at):
            raise ValueError("Approved/revoked records require attributed review and date")
        return self


class Code(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    system: str = Field(min_length=1)
    value: str = Field(min_length=1)
    from_year: int | None = None
    to_year: int | None = None
    attributes: dict[str, str | int | None] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validity(self) -> "Code":
        if (
            self.from_year is not None
            and self.to_year is not None
            and self.from_year > self.to_year
        ):
            raise ValueError("Inverted code validity")
        return self


class Entity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str
    kind: Kind
    name: str
    canonical_id: UUID | None = None
    university_key: str | None = None
    program_key: str | None = None
    major_key: str | None = None
    domains: list[str] = Field(default_factory=list)
    attributes: dict[str, str | int | None] = Field(default_factory=dict)
    codes: list[Code] = Field(default_factory=list)
    review: Review

    @model_validator(mode="after")
    def approval(self) -> "Entity":
        if (self.review.status == "approved") != (self.canonical_id is not None):
            raise ValueError("Only approved entities carry canonical_id")
        if self.kind in {"program", "offering", "scope"} and not self.university_key:
            raise ValueError("Owned entity needs university key")
        if self.kind == "offering" and not self.program_key:
            raise ValueError("Offering needs program key")
        if self.kind == "offering" and self.review.status == "approved":
            if not isinstance(self.attributes.get("admission_year"), int) or not {
                "campus",
                "track",
                "language",
            }.issubset(self.attributes):
                raise ValueError(
                    "Approved offering requires year and explicit context (unknown allowed)"
                )
        if any(d != d.lower() or "://" in d or "/" in d or "*" in d for d in self.domains):
            raise ValueError("Registry requires exact lowercase hosts")
        return self


class Alias(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str
    target: str
    value: str
    kind: Literal["name", "short_name", "domain", "legacy_code"]
    code_system: str | None = None
    university_key: str | None = None
    from_year: int | None = None
    to_year: int | None = None
    attributes: dict[str, str | int | None] = Field(default_factory=dict)
    review: Review

    @model_validator(mode="after")
    def validity(self) -> "Alias":
        if (
            self.from_year is not None
            and self.to_year is not None
            and self.from_year > self.to_year
        ):
            raise ValueError("Inverted alias validity")
        if self.kind == "legacy_code" and not self.code_system:
            raise ValueError("Legacy code alias requires a code system")
        return self


class EntityRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    version: str
    alias_version: str
    classification: Literal["pilot_pending", "reviewed", "synthetic"]
    entities: list[Entity]
    aliases: list[Alias] = Field(default_factory=list)

    @model_validator(mode="after")
    def relationships(self) -> "EntityRegistry":
        entities = {e.key: e for e in self.entities}
        if len(entities) != len(self.entities) or len({a.key for a in self.aliases}) != len(
            self.aliases
        ):
            raise ValueError("Duplicate registry/alias key")
        canonical_pairs = [(e.kind, e.canonical_id) for e in self.entities if e.canonical_id]
        if len(set(canonical_pairs)) != len(canonical_pairs):
            raise ValueError("Duplicate canonical entity; use aliases instead of duplicate keys")
        for e in self.entities:
            for ref, kind in [
                (e.university_key, "university"),
                (e.program_key, "program"),
                (e.major_key, "major"),
            ]:
                if ref and (ref not in entities or entities[ref].kind != kind):
                    raise ValueError("Missing/wrong-type registry parent")
                if (
                    ref
                    and e.review.status == "approved"
                    and entities[ref].review.status != "approved"
                ):
                    raise ValueError("Approved entity cannot inherit pending parent")
            if e.program_key and entities[e.program_key].university_key != e.university_key:
                raise ValueError("Offering belongs to another university")
        for a in self.aliases:
            if a.target not in entities:
                raise ValueError("Missing alias target")
            if a.review.status == "approved" and entities[a.target].review.status != "approved":
                raise ValueError("Approved alias requires approved target")
            if a.university_key and (
                a.university_key not in entities or entities[a.university_key].kind != "university"
            ):
                raise ValueError("Invalid alias scope university")
        return self

    def entry(self, key: str) -> Entity:
        return next(e for e in self.entities if e.key == key)

    @classmethod
    def load(cls, path: Path) -> "EntityRegistry":
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def frozen(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
