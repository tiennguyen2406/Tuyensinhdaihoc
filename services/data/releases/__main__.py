"""DEV-only local CLI. plan/inspect/verify/replay never mutate the database."""

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from services.api.db.session import engine, schema_is_current
from services.data.publication.__main__ import private_path
from services.data.releases.builder import build, verify
from services.data.releases.snapshot import capture


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "build", "inspect", "verify", "replay"])
    parser.add_argument("--version", type=int)
    parser.add_argument("--root", type=Path, default=Path("state/releases/canonical"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = private_path(args.output) if args.output else None
    if output and output.exists():
        raise ValueError("Output already exists; choose a new checkpoint path")
    user, password = os.getenv("RELEASE_DB_USER"), os.getenv("RELEASE_DB_PASSWORD")
    if bool(user) != bool(password):
        raise PermissionError("Both dedicated release credential variables are required")
    db = (
        create_engine(
            engine.url.set(username=user, password=password),
            hide_parameters=True,
            connect_args={"connect_timeout": 3},
        )
        if user
        else engine
    )
    try:
        if args.command == "build":
            result = build(db, private_path(args.root), args.version)
        else:
            with db.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
                c.exec_driver_sql("SET TRANSACTION READ ONLY")
                if not schema_is_current(c):
                    raise ValueError("Schema is not current; CLI never migrates automatically")
                if args.command == "plan":
                    if args.version is not None:
                        raise ValueError(
                            "Plan captures current catalog only; inspect a historical release by version"
                        )
                    snapshot = capture(c)
                    result = dict(
                        read_only=True,
                        version=snapshot["catalog_version"],
                        coverage=snapshot["coverage"],
                        filters=snapshot["filters"],
                        catalog_version_delta=0,
                        expected_new_releases=1,
                    )
                else:
                    if args.version is None:
                        raise ValueError(
                            "--version required for registered release inspection/verification/replay"
                        )
                    result = verify(c, args.version) | {"read_only": True}
        data = json.dumps(result, ensure_ascii=False, indent=2)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as stream:
                stream.write(data + "\n")
        print(data)
        return 0
    finally:
        db.dispose()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, PermissionError, OSError, SQLAlchemyError) as error:
        reason = (
            str(error)
            if isinstance(error, ValueError | PermissionError)
            and not isinstance(error, SQLAlchemyError)
            else "Database or private file operation blocked; details withheld"
        )
        print(
            json.dumps(dict(blocked=True, error_type=type(error).__name__, reason=reason)),
            file=sys.stderr,
        )
        sys.exit(2)
