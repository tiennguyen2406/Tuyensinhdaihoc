"""The database login is the actor. No JSON reviewer or superuser approval mode."""

import sqlalchemy as sa
from sqlalchemy.engine import Connection


def require(c: Connection, capability: str) -> str:
    if capability not in {"reviewer", "publisher"}:
        raise PermissionError("Unknown capability")
    row = (
        c.execute(
            sa.text(
                "SELECT session_user AS actor, rolsuper, rolcreaterole FROM pg_roles WHERE rolname=session_user"
            )
        )
        .mappings()
        .one()
    )
    exists = c.scalar(
        sa.text("SELECT EXISTS(SELECT FROM pg_roles WHERE rolname=:role)"),
        {"role": "eduradar_" + capability},
    )
    if row["rolsuper"] or row["rolcreaterole"] or not exists:
        raise PermissionError("Dedicated non-superuser local database identity required")
    allowed = c.scalar(
        sa.text("SELECT pg_has_role(session_user,:role,'MEMBER')"),
        {"role": "eduradar_" + capability},
    )
    if not allowed:
        raise PermissionError("Database login lacks required capability")
    return "db:" + row["actor"]
