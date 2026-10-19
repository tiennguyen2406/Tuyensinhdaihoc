"""Explicit versioned parser registry; no source fetching or normalization."""

import hashlib
import json
import re
from typing import Callable
from urllib.parse import urlsplit

from services.api.source_profiles import SourceProfile
from services.data.parsers.contract import (
    ExtractedObservation,
    ParseLimits,
    ParseResult,
    SnapshotRef,
)
from services.data.parsers.html import VERSION as HTML_VERSION
from services.data.parsers.html import parse_html
from services.data.parsers.pdf import VERSION as PDF_VERSION
from services.data.parsers.pdf import parse_pdf
from services.data.parsers.ueh import VERSION as UEH_VERSION
from services.data.parsers.ueh import parse_ueh

ADAPTERS: dict[str, tuple[str, Callable[..., ParseResult]]] = {
    "text/html": (HTML_VERSION, parse_html),
    "application/xhtml+xml": (HTML_VERSION, parse_html),
    "application/pdf": (PDF_VERSION, parse_pdf),
}


def profile_hash(profile: SourceProfile) -> str:
    return hashlib.sha256(
        json.dumps(
            profile.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def parser_version(
    snapshot: SnapshotRef, revision: str = "1", profile: SourceProfile | None = None
) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", revision):
        raise ValueError("Invalid parser revision")
    if profile and profile.parser == "ueh_2024_html" and snapshot.media_type == "text/html":
        return UEH_VERSION + "+" + revision
    return ADAPTERS.get(snapshot.media_type, ("unsupported/1.0.0", None))[0] + "+" + revision


def extract(
    snapshot: SnapshotRef,
    profile: SourceProfile,
    data: bytes,
    *,
    limits: ParseLimits | None = None,
    revision: str = "1",
) -> ParseResult:
    if hashlib.sha256(data).hexdigest() != snapshot.raw_hash:
        raise ValueError("Snapshot hash mismatch")
    if len(data) != snapshot.byte_size:
        raise ValueError("Snapshot size mismatch")
    if (
        urlsplit(snapshot.final_url).hostname
        not in profile.allowed_hosts + profile.allowed_document_hosts
    ):
        raise ValueError("Snapshot host outside source profile")
    version = parser_version(snapshot, revision, profile)
    adapter = ADAPTERS.get(snapshot.media_type)
    if profile.parser == "ueh_2024_html" and snapshot.media_type == "text/html":
        adapter = (UEH_VERSION, parse_ueh)
    if adapter is None:
        result = ParseResult()
        result.issue(
            "unsupported_media_type",
            "document",
            "No parser registered; robots/plain text/XLSX/JSON are not admission facts",
        )
    else:
        result = adapter[1](
            snapshot, profile, data, limits=limits or ParseLimits(), version=version
        )
    result.metadata |= {
        "snapshot_id": str(snapshot.snapshot_id),
        "source_id": str(snapshot.source_id) if snapshot.source_id else None,
        "parser_version": version,
        "implementation_version": version.split("+")[0],
        "profile_sha256": profile_hash(profile),
    }
    return result


def parse(snapshot: SnapshotRef, profile: SourceProfile) -> list[ExtractedObservation]:
    """Required two-argument list API. Use runner.replay for document-level diagnostics."""
    from services.data.parsers.runner import replay

    return replay(snapshot, profile).observations
