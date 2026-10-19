"""Versioned internal lookup routes. Each response uses one read-only RR connection."""

import os
from collections.abc import Generator
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from services.api.catalog import dto, queries
from services.api.db.models import metadata
from services.api.db.session import engine, schema_is_current
from services.data.normalization.values import text

router = APIRouter(prefix="/api/v1", tags=["Internal catalog"])


@lru_cache(maxsize=1)
def catalog_engine() -> Engine:
    user, password = os.getenv("CATALOG_DB_USER"), os.getenv("CATALOG_DB_PASSWORD")
    if bool(user) != bool(password):
        raise RuntimeError("Both catalog reader credential variables are required")
    return (
        sa.create_engine(
            engine.url.set(username=user, password=password),
            hide_parameters=True,
            connect_args={"connect_timeout": 3},
        )
        if user
        else engine
    )


def catalog_snapshot() -> Generator[Connection, None, None]:
    try:
        with (
            catalog_engine().connect().execution_options(isolation_level="REPEATABLE READ") as c,
            c.begin(),
        ):
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            c.exec_driver_sql("SET LOCAL statement_timeout='5000ms'")
            if not schema_is_current(c):
                raise HTTPException(503, detail={"code": "SCHEMA_UNAVAILABLE"})
            yield c
    except SQLAlchemyError as error:
        raise HTTPException(503, detail={"code": "DATABASE_UNAVAILABLE"}) from error


DB = Annotated[Connection, Depends(catalog_snapshot)]


@router.get("/universities", response_model=dto.Page[dto.University])
def universities(params: Annotated[dto.Universities, Query()], c: DB) -> Any:
    return queries.search_universities(c, params)


@router.get("/universities/{id}", response_model=dto.Detail[dto.UniversityDetail])
def university(id: UUID, params: Annotated[dto.Params, Query()], c: DB) -> Any:
    v = queries.version(c)
    u = queries.require_university(c, id)
    values = params.model_dump() | {"university_id": id}
    rows = queries.facts(c, values)
    methods = {
        str(r["admission_methods"]["id"]): dto.Method(**r["admission_methods"]) for r in rows
    }
    item = dto.UniversityDetail(
        **queries.university(c, u, params.year, rows).model_dump(),
        methods=sorted(methods.values(), key=lambda m: m.code),
    )
    return queries.meta(c, v, values, rows) | {"item": item}


@router.get("/universities/{id}/admission-years", response_model=dto.Page[dto.AdmissionYear])
def admission_years(id: UUID, params: Annotated[dto.NoParams, Query()], c: DB) -> Any:
    v = queries.version(c)
    queries.require_university(c, id)
    items = []
    for year in (2024, 2025, 2026):
        rows = queries.facts(c, {"year": year, "university_id": id})
        items.append(
            dto.AdmissionYear(
                year=year,
                data_status="verified" if rows else "not_collected_or_not_verified",
                cutoff_count=len(rows),
                offering_count=len({r["program_years"]["id"] for r in rows}),
            )
        )
    rows = queries.facts(c, {"year": 2026, "university_id": id})
    return queries.meta(c, v, {"year": 2026, "university_id": id}, rows) | {"items": items}


@router.get("/programs", response_model=dto.Page[dto.Offering])
def programs(params: Annotated[dto.Programs, Query()], c: DB) -> Any:
    v = queries.version(c)
    values = params.model_dump()
    rows = queries.facts(c, values)
    return queries.page(
        queries.offerings(c, rows),
        lambda x: (text(x.offering_name).search_key, str(x.program_year_id)),
        "programs",
        params,
        v,
        queries.meta(c, v, values, rows),
    )


@router.get("/programs/{id}", response_model=dto.Detail[dto.ProgramDetail])
def program(id: UUID, params: Annotated[dto.Params, Query()], c: DB) -> Any:
    v = queries.version(c)
    p, u, m = (metadata.tables[n] for n in ["programs", "universities", "majors"])
    r = (
        c.execute(
            sa.select(p.c.id, p.c.program_name, p.c.university_id, p.c.major_id, m.c.name)
            .select_from(p.join(u).outerjoin(m))
            .where(p.c.id == id, u.c.verification_status == "verified")
        )
        .mappings()
        .one_or_none()
    )
    if not r:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "Không có chương trình này."}
        )
    values = params.model_dump() | {"program_id": id}
    rows = queries.facts(c, values)
    item = dto.ProgramDetail(
        id=r["id"],
        name=r["program_name"],
        university_id=r["university_id"],
        selected_year=params.year,
        major_id=r["major_id"],
        major_name=r["name"],
        offerings=queries.offerings(c, rows),
    )
    return queries.meta(c, v, values, rows) | {"item": item}


@router.get("/cutoffs", response_model=dto.Page[dto.Cutoff])
def cutoffs(params: Annotated[dto.Cutoffs, Query()], c: DB) -> Any:
    v = queries.version(c)
    values = params.model_dump()
    rows = queries.facts(c, values)
    return queries.page(
        [queries.cutoff(c, r) for r in rows],
        lambda x: (str(x.id),),
        "cutoffs",
        params,
        v,
        queries.meta(c, v, values, rows),
    )


@router.get("/data-coverage", response_model=dto.Page[dto.Coverage])
def data_coverage(params: Annotated[dto.CoverageParams, Query()], c: DB) -> Any:
    v = queries.version(c)
    values = params.model_dump()
    rows = queries.facts(c, values)
    items = [
        queries.coverage(c, values | {"year": year}, queries.facts(c, values | {"year": year}))
        for year in (2024, 2025, 2026)
    ]
    return queries.meta(c, v, values, rows) | {"items": items}


@router.get("/sources/{id}", response_model=dto.Detail[dto.Source])
def source(id: UUID, params: Annotated[dto.Params, Query()], c: DB) -> Any:
    v = queries.version(c)
    values = params.model_dump()
    rows = queries.facts(c, values)
    refs = [s for s in queries.sources(c, rows) if s.snapshot_id == id]
    if not refs:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "Không có nguồn đã xác minh cho năm này."}
        )
    return queries.meta(c, v, values, rows) | {"item": refs[0]}
