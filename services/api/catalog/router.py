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
from services.api.db.session import engine, schema_is_current

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
    return queries.university_detail(c, id, params.year)


@router.get("/universities/{id}/admission-years", response_model=dto.Page[dto.AdmissionYear])
def admission_years(id: UUID, params: Annotated[dto.NoParams, Query()], c: DB) -> Any:
    return queries.admission_years(c, id)


@router.get("/programs", response_model=dto.Page[dto.Offering])
def programs(params: Annotated[dto.Programs, Query()], c: DB) -> Any:
    return queries.search_programs(c, params)


@router.get("/programs/{id}", response_model=dto.Detail[dto.ProgramDetail])
def program(id: UUID, params: Annotated[dto.Params, Query()], c: DB) -> Any:
    return queries.program_detail(c, id, params.year)


@router.get("/cutoffs", response_model=dto.Page[dto.Cutoff])
def cutoffs(params: Annotated[dto.Cutoffs, Query()], c: DB) -> Any:
    return queries.search_cutoffs(c, params)


@router.get("/data-coverage", response_model=dto.Page[dto.Coverage])
def data_coverage(params: Annotated[dto.CoverageParams, Query()], c: DB) -> Any:
    return queries.data_coverage(c, params)


@router.get("/sources/{id}", response_model=dto.Detail[dto.Source])
def source(id: UUID, params: Annotated[dto.Params, Query()], c: DB) -> Any:
    return queries.source_detail(c, id, params.year)
