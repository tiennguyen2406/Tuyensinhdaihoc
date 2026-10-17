"""Offline T07 commands; detailed source-derived outputs remain outside Git."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from services.api.db.session import ROOT, engine, schema_is_current
from services.data.resolution.evaluate import evaluate
from services.data.resolution.registry import EntityRegistry
from services.data.resolution.store import ResolutionStore

DEFAULT_NORMALIZATION_JOB = "7bc439bf-a6d7-4beb-bf03-bb47956c5383"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Offline T07 entity resolution, review only; no canonical publication"
    )
    parser.add_argument("command", choices=["preview", "run", "replay", "affected", "evaluate"])
    parser.add_argument("--normalization-job", type=UUID, default=UUID(DEFAULT_NORMALIZATION_JOB))
    parser.add_argument("--job", type=UUID)
    parser.add_argument("--registry", type=Path, default=ROOT / "config/entities/ptit-v1.json")
    parser.add_argument("--gold", type=Path, default=ROOT / "tests/resolution/gold.json")
    parser.add_argument(
        "--entry", help="Registry or alias key whose historical dependents should be listed"
    )
    parser.add_argument(
        "--output", type=Path, help="Detailed private JSON in ignored state/ or outside checkout"
    )
    args = parser.parse_args()
    if args.command == "replay" and not args.job:
        parser.error("replay requires --job")
    if args.command == "affected" and not args.entry:
        parser.error("affected requires --entry")
    path = args.output.resolve() if args.output else None
    if path and path.is_relative_to(ROOT) and not path.is_relative_to(ROOT / "state"):
        raise ValueError("Source-derived output must remain in ignored state/ or outside checkout")
    value: Any
    public: Any
    if args.command == "evaluate":
        value = evaluate(args.gold)
        public = value
    elif args.command in {"preview", "affected"}:
        with engine.connect() as c:
            c.exec_driver_sql("SET TRANSACTION READ ONLY")
            if not schema_is_current(c):
                raise ValueError("Schema not current; resolver never migrates")
            store = ResolutionStore(c)
            if args.command == "preview":
                value = store.preview(args.normalization_job, EntityRegistry.load(args.registry))
                public = {k: v for k, v in value.items() if k not in {"results", "registry"}}
                public["registry_counts"] = {
                    "entities": len(value["registry"]["entities"]),
                    "aliases": len(value["registry"]["aliases"]),
                }
            else:
                value = store.affected(args.entry, EntityRegistry.load(args.registry))
                public = value
    else:
        with engine.begin() as c:
            if not schema_is_current(c):
                raise ValueError("Schema not current; resolver never migrates")
            store = ResolutionStore(c)
            value = (
                store.replay(args.job)
                if args.command == "replay"
                else store.run(args.normalization_job, EntityRegistry.load(args.registry))
            )
            public = value
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
    print(json.dumps(public, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, SQLAlchemyError) as error:
        print(
            f"Resolution stopped ({type(error).__name__}): input/registry/database integrity error; credentials not logged",
            file=sys.stderr,
        )
        sys.exit(2)
