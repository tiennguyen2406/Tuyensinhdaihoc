"""Synthetic fixtures authored for this repository; no admissions source copied."""

import hashlib
from uuid import uuid4

from services.data.parsers.contract import SnapshotRef
from tests.crawler.helpers import profile as base_profile


def profile():
    return base_profile()


def snapshot(data: bytes, mime="text/html"):
    return SnapshotRef(
        snapshot_id=uuid4(),
        source_id=uuid4(),
        raw_hash=hashlib.sha256(data).hexdigest(),
        raw_uri="fixture://synthetic",
        final_url="https://example.edu.vn/pilot",
        media_type=mime,
        byte_size=len(data),
    )
