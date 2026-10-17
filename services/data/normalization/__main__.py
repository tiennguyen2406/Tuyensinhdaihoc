"""Offline normalization CLI. No crawler imports, raw downloads or canonical writes."""

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from services.api.db.session import ROOT, engine, schema_is_current
from services.data.normalization.store import NormalizationStore


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Offline unverified normalization: preview/run/replay"
    )
    parser.add_argument("command", choices=["preview", "run", "replay"])
    parser.add_argument(
        "--snapshot", type=UUID, help="Filter raw inputs; default all raw-only observations"
    )
    parser.add_argument("--job", type=UUID, help="Frozen normalization job to replay")
    parser.add_argument(
        "--output", type=Path, help="Private preview report in ignored state/ or outside checkout"
    )
    args = parser.parse_args()
    if args.command == "replay" and (not args.job or args.snapshot):
        parser.error("replay requires --job and does not accept --snapshot")
    if args.command != "replay" and args.job:
        parser.error("--job only applies to replay")
    path = args.output.resolve() if args.output else None
    if path and path.is_relative_to(ROOT) and not path.is_relative_to(ROOT / "state"):
        raise ValueError("Private reports must remain in ignored state/ or outside checkout")
    if args.command == "preview":
        with engine.connect() as c:
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            if not schema_is_current(c):
                raise ValueError("Schema not current; normalizer never migrates")
            store = NormalizationStore(c)
            value = store.preview(store.raw_ids(args.snapshot))
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {k: v for k, v in value.items() if k != "results"}, ensure_ascii=False, indent=2
            )
        )
    else:
        with engine.begin() as c:
            if not schema_is_current(c):
                raise ValueError("Schema not current; normalizer never migrates")
            store = NormalizationStore(c)
            result = (
                store.replay(args.job)
                if args.command == "replay"
                else store.run(store.raw_ids(args.snapshot))
            )
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, SQLAlchemyError) as exc:
        print(
            f"Normalization stopped ({type(exc).__name__}): input/configuration/database error; credentials not logged",
            file=sys.stderr,
        )
        sys.exit(2)
