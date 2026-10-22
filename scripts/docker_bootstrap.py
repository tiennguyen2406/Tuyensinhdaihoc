"""Initialize the explicitly selected Docker database; never seed business facts."""

import os

from alembic import command
from psycopg import sql
from sqlalchemy import Connection

from services.api.catalog.roles import provision_reader
from services.api.db.session import alembic_config, engine


def provision_login(c: Connection, username: str, password: str) -> None:
    owner = c.exec_driver_sql("SELECT session_user").scalar_one()
    if not username or not password or username in {owner, "postgres", "eduradar_reader"}:
        raise ValueError("A separate reader login and nonempty password are required")
    existing = c.exec_driver_sql(
        "SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=%s",
        (username,),
    ).one_or_none()
    if existing and any(existing):
        raise ValueError("Refusing to reuse a privileged reader login")
    verb = sql.SQL("ALTER") if existing else sql.SQL("CREATE")
    statement = sql.SQL(
        "{} ROLE {} LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD {}"
    ).format(verb, sql.Identifier(username), sql.Literal(password))
    c.exec_driver_sql(statement.as_string(c.connection.driver_connection))
    provision_reader(c)
    grant = sql.SQL("GRANT eduradar_reader TO {}").format(sql.Identifier(username))
    c.exec_driver_sql(grant.as_string(c.connection.driver_connection))


def main() -> None:
    username, password = os.environ["CATALOG_DB_USER"], os.environ["CATALOG_DB_PASSWORD"]
    with engine.begin() as c:
        # All operator initialization is explicit in the one-shot compose service.
        c.exec_driver_sql("SELECT pg_advisory_xact_lock(hashtext('eduradar:docker-bootstrap'))")
        config = alembic_config()
        config.attributes["connection"] = c
        command.upgrade(config, "head")
        provision_login(c, username, password)
    print("Schema and dedicated catalog reader ready; no business facts seeded.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # SQL errors can contain password-bearing utility statements.
        raise SystemExit("Database initialization failed; check configuration privately.") from None
