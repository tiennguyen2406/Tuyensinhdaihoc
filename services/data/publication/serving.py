"""Bootstrap changes visible through the live T10 catalog, including empty identities."""

from datetime import date
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection, ScalarResult

from services.api.db.models import metadata
from services.api.db.validators import OFFICIAL_TYPES, TARGET_YEARS


def affects_serving(
    c: Connection,
    kind: str,
    mode: str,
    before: dict[str, Any] | None,
    after: dict[str, Any],
    verified_universities: set[UUID],
) -> bool:
    """Called with resolved values for both preview and apply, never registry metadata."""
    if kind == "source":
        return bool(
            before
            and before["verification_status"] != after["verification_status"]
            and before["source_type"] in OFFICIAL_TYPES
            and source_is_referenced(c, before)
        )
    if mode != "create":
        return False  # Other link operations validate equality and cannot alter canonical rows.
    if kind == "university":
        return True  # Verified identities serve without a cutoff or admission-year row.
    if kind not in {"program", "year", "alias"}:
        return False
    owner = after["university_id"]
    if owner not in verified_universities:
        u = metadata.tables["universities"]
        if not c.scalar(
            sa.select(sa.exists().where(u.c.id == owner, u.c.verification_status == "verified"))
        ):
            return False
    if kind == "year":
        return after["admission_year"] in TARGET_YEARS
    if kind == "alias":
        return bool(after["approved_by"]) and any(
            (after.get("valid_from") is None or after["valid_from"] <= date(year, 12, 31))
            and (after.get("valid_to") is None or after["valid_to"] >= date(year, 1, 1))
            for year in TARGET_YEARS
        )
    return True  # Program detail is available even when it has no eligible Offerings.


def source_is_referenced(c: Connection, source: dict[str, Any]) -> bool:
    """Mirror T10 fact/source eligibility for a source becoming verified."""
    cut, scope, off, u, snap, ev, obs = (
        metadata.tables[name]
        for name in [
            "cutoff_scores",
            "program_admissions",
            "program_years",
            "universities",
            "source_snapshots",
            "cutoff_evidence",
            "observations",
        ]
    )
    supporting = sa.exists(
        sa.select(ev.c.cutoff_id)
        .select_from(ev.join(obs, ev.c.observation_id == obs.c.id))
        .where(ev.c.cutoff_id == cut.c.id, obs.c.snapshot_id == snap.c.id)
        .correlate(cut, snap)
    )
    urls: ScalarResult[str | None] = c.scalars(
        sa.select(snap.c.final_url)
        .select_from(
            cut.join(scope, cut.c.program_admission_id == scope.c.id)
            .join(off, scope.c.program_year_id == off.c.id)
            .join(u, off.c.university_id == u.c.id)
            .join(snap, sa.or_(cut.c.primary_snapshot_id == snap.c.id, supporting))
        )
        .where(
            cut.c.is_current.is_(True),
            cut.c.verification_status == "verified",
            scope.c.data_status == "published",
            off.c.admission_year.in_(TARGET_YEARS),
            u.c.verification_status == "verified",
            snap.c.source_id == source["id"],
        )
        .distinct()
    )
    for url in urls:
        parsed = urlsplit(url or source["canonical_url"])
        if (
            parsed.scheme in {"http", "https"}
            and parsed.hostname
            and parsed.username is None
            and parsed.password is None
        ):
            return True
    return False
