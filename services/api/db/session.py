import os
from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from dotenv import load_dotenv
from sqlalchemy import URL, Connection, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.api.db.validators import install_guards

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")


def database_url() -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", "tuyensinh"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "tuyensinhdaihoc"),
    )


def create_db_engine() -> Engine:
    return create_engine(
        database_url(), pool_pre_ping=True, pool_timeout=3, connect_args={"connect_timeout": 3}
    )


engine = create_db_engine()
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
install_guards(SessionFactory)


def get_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session


def alembic_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


@lru_cache(maxsize=1)
def required_schema_heads() -> frozenset[str]:
    return frozenset(ScriptDirectory.from_config(alembic_config()).get_heads())


def schema_is_current(connection: Connection) -> bool:
    required = required_schema_heads()
    current = frozenset(MigrationContext.configure(connection).get_current_heads())
    return bool(required) and current == required
