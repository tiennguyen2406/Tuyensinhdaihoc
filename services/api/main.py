from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from services.api.catalog.router import router as catalog_router
from services.api.db.session import engine, schema_is_current


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="TuyenSinhDaiHoc API", version="0.1.0", lifespan=lifespan)
app.include_router(catalog_router)


@app.get("/health/live", tags=["Health"])
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/health/ready",
    tags=["Health"],
    responses={503: {"description": "Database unavailable or schema out of date"}},
)
def health_ready() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout = '3000ms'"))
            connection.execute(text("SELECT 1"))
            if not schema_is_current(connection):
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unavailable",
                        "database": "connected",
                        "schema": "out_of_date",
                    },
                )
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "unavailable", "database": "unavailable"}
        )
    return JSONResponse(content={"status": "ok", "database": "connected"})
