"""Bulk synthetic catalog facts. Never valid for a pilot/production database."""

from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa

from services.api.db.models import metadata


def synthetic_id(kind, number):
    return uuid5(NAMESPACE_URL, f"https://example.invalid/t10-scale/{kind}/{number}")


def seed_catalog(connection, fact_count=20_000, university_count=200):
    """Insert a deterministic scale fixture in the caller's transaction; no deletion.

    Two methods per Offering, three years/campuses, duplicate normalized sort names,
    real normalized search fields, approved aliases, two evidence links per fact.
    Guard remains active even under python -O. Caller must supply an empty fact table.
    """
    if not (connection.engine.url.database or "").startswith("tuyensinh_test_"):
        raise ValueError("Synthetic scale fixture requires tuyensinh_test_* database")
    if fact_count < 2 or fact_count % 2:
        raise ValueError("fact_count must be an even integer >= 2")
    if connection.scalar(sa.select(sa.func.count()).select_from(metadata.tables["cutoff_scores"])):
        raise ValueError("Refusing to seed over existing facts")
    university_count = min(university_count, fact_count // 2)
    program_count = min(university_count * 5, fact_count // 2)
    rows = {}

    def add(table, **values):
        rows.setdefault(table, []).append(values)

    for i in range(university_count):
        uid, sid, snap = (synthetic_id(k, i) for k in ("university", "source", "snapshot"))
        name = f"Synthetic University {i // 2:04d}"
        add(
            "universities",
            id=uid,
            university_code=f"SYN{i:04d}",
            name=name,
            normalized_name=name.lower(),
            slug=f"synthetic-{i}",
            verification_status="verified",
        )
        add(
            "university_aliases",
            id=synthetic_id("alias", i),
            university_id=uid,
            alias=f"Synthetic Alias {i:04d}",
            normalized_alias=f"synthetic alias {i:04d}",
            alias_type="name",
            evidence_url=f"https://example.invalid/{i}",
            approved_by="SYNTHETIC ONLY",
        )
        add(
            "sources",
            id=sid,
            canonical_url=f"https://example.invalid/{i}",
            domain="example.invalid",
            publisher="SYNTHETIC ONLY",
            university_id=uid,
            source_type="university",
            verification_status="verified",
        )
        add(
            "source_snapshots",
            id=snap,
            source_id=sid,
            raw_hash=f"{i:064x}",
            raw_uri="fixture://synthetic-only",
            final_url=f"https://example.invalid/{i}",
            media_type="text/html",
            byte_size=0,
        )
        for year in (2024, 2025, 2026):
            add(
                "admission_years",
                university_id=uid,
                admission_year=year,
                status=("unknown", "partial", "published", "verified")[(i + year) % 4],
            )
        add(
            "observations",
            id=synthetic_id("supporting", i),
            snapshot_id=snap,
            fact_kind="cutoff",
            record_locator="supporting/table",
            parser_version="synthetic/1",
            transform_version="synthetic/1",
            raw_fields={},
            normalized_fields={},
            payload_hash=f"{i:064x}",
            extraction_method="synthetic",
            verification_status="verified",
        )
    for i in range(program_count):
        name = f"Synthetic Program {i % 50:03d}"
        add(
            "programs",
            id=synthetic_id("program", i),
            university_id=synthetic_id("university", i % university_count),
            canonical_key=f"SYN{i}",
            program_name=name,
            normalized_name=name.lower(),
        )
    for method in range(2):
        mid = synthetic_id("method", method)
        add(
            "admission_methods",
            id=mid,
            code=f"SYN{method}",
            name=f"Synthetic Method {method}",
            input_kind="exam_total",
        )
        for year in (2024, 2025, 2026):
            add(
                "score_scales",
                id=synthetic_id("scale", year * 10 + method),
                method_id=mid,
                admission_year=year,
                code="SYN",
                exam_version="SYNTHETIC ONLY",
                min_score=0,
                max_score=30,
                basis_description="Synthetic benchmark only",
                primary_snapshot_id=synthetic_id("snapshot", 0),
            )
    for i in range(fact_count // 2):
        program = i % program_count
        uni = program % university_count
        year = 2024 + (i // program_count) % 3
        snap = synthetic_id("snapshot", uni)
        add(
            "program_years",
            id=synthetic_id("offering", i),
            university_id=synthetic_id("university", uni),
            program_id=synthetic_id("program", program),
            admission_year=year,
            offering_code=f"SYN{i:06d}",
            offering_name=f"Synthetic Offering {i % 50:03d}",
            campus_code=("A", "B", "C")[(i // (program_count * 3)) % 3],
            primary_snapshot_id=snap,
        )
        for method in range(2):
            fact = i * 2 + method
            scope, cutoff = (synthetic_id(k, fact) for k in ("scope", "cutoff"))
            scale = synthetic_id("scale", year * 10 + method)
            add(
                "program_admissions",
                id=scope,
                program_year_id=synthetic_id("offering", i),
                method_id=synthetic_id("method", method),
                round_key="SYN",
                population_key="SYN",
                condition_key="SYN",
                condition_text="Synthetic only",
                condition_dsl={},
                score_scale_id=scale,
                data_status="published",
                primary_snapshot_id=snap,
            )
            add(
                "cutoff_scores",
                id=cutoff,
                program_admission_id=scope,
                revision=1,
                score_scale_id=scale,
                score=Decimal("24.12345"),
                max_score=30,
                fact_fingerprint=f"{fact:064x}",
                publication_group_key="SYNTHETIC BENCHMARK ONLY",
                fact_payload={"schema_version": "synthetic/1", "score": "24.12345"},
                primary_snapshot_id=snap,
                verification_status="verified",
                is_current=True,
            )
            obs = synthetic_id("observation", fact)
            add(
                "observations",
                id=obs,
                snapshot_id=snap,
                fact_kind="cutoff",
                record_locator=f"table/row/{fact}",
                parser_version="synthetic/1",
                transform_version="synthetic/1",
                raw_fields={},
                normalized_fields={},
                payload_hash=f"{fact:064x}",
                extraction_method="synthetic",
                verification_status="verified",
            )
            for observation, role in [
                (obs, "primary"),
                (synthetic_id("supporting", uni), "supporting"),
            ]:
                add(
                    "cutoff_evidence",
                    cutoff_id=cutoff,
                    observation_id=observation,
                    evidence_role=role,
                )
    order = (
        "universities",
        "university_aliases",
        "sources",
        "source_snapshots",
        "admission_years",
        "programs",
        "admission_methods",
        "score_scales",
        "program_years",
        "program_admissions",
        "cutoff_scores",
        "observations",
        "cutoff_evidence",
    )
    for name in order:
        values = rows[name]
        for start in range(0, len(values), 1000):
            connection.execute(metadata.tables[name].insert(), values[start : start + 1000])
    return {name: len(rows[name]) for name in order}
