"""Insert-only T05 staging. This module cannot publish canonical data."""

import hashlib
import json
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from services.api.db.models import observations, source_snapshots
from services.data.parsers.contract import ParseResult


class ObservationStore:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def save(self, result: ParseResult) -> int:
        c = self.connection
        seen = set()
        inserted = 0
        for obs in result.observations:
            key = (obs.snapshot_id, obs.record_locator, obs.parser_version, obs.transform_version)
            if key in seen:
                raise ValueError("Duplicate extraction locator/version")
            seen.add(key)
            source: UUID = c.execute(
                sa.select(source_snapshots.c.source_id).where(
                    source_snapshots.c.id == obs.snapshot_id
                )
            ).scalar_one()
            if obs.source_id is not None and source != obs.source_id:
                raise ValueError("Observation source does not match snapshot")
            fields = obs.raw_fields | {
                "_extraction": {
                    "source_id": str(source),
                    "issues": [i.model_dump() for i in obs.issues],
                    "profile_sha256": result.metadata.get("profile_sha256"),
                    "implementation_version": result.metadata.get("implementation_version"),
                    "implementation_sha256": result.metadata.get("implementation_sha256"),
                    "lock_sha256": result.metadata.get("lock_sha256"),
                    "parse_job_id": result.metadata.get("parse_job_id"),
                }
            }
            payload = {
                "fact_kind": obs.fact_kind,
                "raw_fields": fields,
                "extraction_method": obs.extraction_method,
                "extraction_confidence": str(obs.extraction_confidence),
            }
            digest = hashlib.sha256(
                json.dumps(
                    payload,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode()
            ).hexdigest()
            result_id = c.execute(
                insert(observations)
                .values(
                    snapshot_id=obs.snapshot_id,
                    fact_kind=obs.fact_kind,
                    record_locator=obs.record_locator,
                    parser_version=obs.parser_version,
                    transform_version=obs.transform_version,
                    raw_fields=fields,
                    normalized_fields={},
                    payload_hash=digest,
                    extraction_method=obs.extraction_method,
                    extraction_confidence=obs.extraction_confidence,
                    verification_status="unverified",
                )
                .on_conflict_do_nothing(
                    index_elements=[
                        observations.c.snapshot_id,
                        observations.c.record_locator,
                        observations.c.parser_version,
                        observations.c.transform_version,
                    ]
                )
                .returning(observations.c.id)
            ).scalar_one_or_none()
            if result_id is not None:
                inserted += 1
            else:
                old: str = c.execute(
                    sa.select(observations.c.payload_hash).where(
                        observations.c.snapshot_id == key[0],
                        observations.c.record_locator == key[1],
                        observations.c.parser_version == key[2],
                        observations.c.transform_version == key[3],
                    )
                ).scalar_one()
                if old != digest:
                    raise ValueError(
                        "Same parser/transform version produced different payload; bump version, never overwrite"
                    )
        return inserted
