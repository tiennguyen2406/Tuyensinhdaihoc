"""Versioned internal lookup routes. Each response uses one read-only RR connection."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from services.api.catalog import advice, dto, queries
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


def advice_snapshot(
    params: Annotated[dto.AdviceParams, Query()],
) -> Generator[Connection, None, None]:
    if not os.getenv("CATALOG_DB_USER") or not os.getenv("CATALOG_DB_PASSWORD"):
        raise HTTPException(503, detail={"code": "READER_REQUIRED"})
    with contextmanager(catalog_snapshot)() as c:
        reader: bool = c.exec_driver_sql(
            "SELECT current_user=session_user AND NOT r.rolsuper AND NOT r.rolcreatedb "
            "AND NOT r.rolcreaterole AND NOT r.rolbypassrls "
            "AND EXISTS (SELECT 1 FROM pg_roles cap WHERE cap.rolname='eduradar_reader' "
            "AND pg_has_role(session_user,cap.oid,'MEMBER')) "
            "AND NOT EXISTS (SELECT 1 FROM pg_class tbl JOIN pg_namespace ns "
            "ON ns.oid=tbl.relnamespace WHERE ns.nspname='public' AND tbl.relkind IN ('r','p') "
            "AND (pg_has_role(session_user,tbl.relowner,'MEMBER') OR "
            "has_table_privilege(session_user,tbl.oid,'INSERT,UPDATE,DELETE,TRUNCATE'))) "
            "FROM pg_roles r WHERE r.rolname=session_user"
        ).scalar_one()
        if not reader:
            raise HTTPException(503, detail={"code": "READER_REQUIRED"})
        yield c


@router.get("/advice/cutoffs", response_model=dto.AdvicePage)
def advice_cutoffs(
    params: Annotated[dto.AdviceParams, Query()],
    c: Annotated[Connection, Depends(advice_snapshot)],
) -> Any:
    return advice.search_advice(c, params)


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
