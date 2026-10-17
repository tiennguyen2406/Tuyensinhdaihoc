"""Offline T05 operator commands. `parse` persists staging; `replay` is a dry run."""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from services.api.db.models import observations, source_snapshots
from services.api.db.session import ROOT, engine, schema_is_current
from services.api.source_profiles import SourceProfile
from services.crawler.raw import RawStorage
from services.data.parsers.html import locate
from services.data.parsers.jobs import ParserJobs
from services.data.parsers.runner import replay


def output(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Offline HTML/digital PDF parser. No crawl or canonical publishing."
    )
    parser.add_argument("command", choices=["list", "replay", "parse", "job", "inspect"])
    parser.add_argument("target", nargs="?")
    parser.add_argument("--profile", default="config/sources/ptit.json")
    parser.add_argument(
        "--revision",
        default="1",
        help="Explicit new output namespace for changed parser/config; implementation version also recorded",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Private JSON report (must be ignored state/ or outside checkout)",
    )
    parser.add_argument("--locator")
    args = parser.parse_args()
    with engine.connect() as c:
        if not schema_is_current(c):
            raise ValueError("Schema is not current; parser does not migrate")
        if args.command == "list":
            output(
                [
                    dict(r)
                    for r in c.execute(
                        sa.select(
                            source_snapshots.c.id,
                            source_snapshots.c.media_type,
                            source_snapshots.c.final_url,
                            sa.func.count(observations.c.id).label("observations"),
                        )
                        .outerjoin(
                            observations, observations.c.snapshot_id == source_snapshots.c.id
                        )
                        .group_by(source_snapshots.c.id)
                    ).mappings()
                ]
            )
            return 0
    if args.target is None:
        parser.error("target UUID required")
    identifier = UUID(args.target)
    raw = RawStorage(Path(os.getenv("CRAWLER_RAW_DIR", "state/raw")))
    jobs = ParserJobs(engine, raw)
    if args.command == "job":
        output(jobs.status(identifier))
        return 0
    profile = SourceProfile.model_validate_json(Path(args.profile).read_text(encoding="utf-8"))
    ref = jobs.snapshot(identifier)
    if args.command == "parse":
        job = jobs.enqueue(identifier, profile, revision=args.revision)
        output(jobs.run(job))
        return 0
    result = replay(ref, profile, raw=raw, revision=args.revision)
    if args.command == "inspect":
        if not args.locator:
            parser.error("inspect requires --locator")
        if args.locator.startswith("html:"):
            from bs4 import BeautifulSoup

            node = locate(BeautifulSoup(raw.read(ref.raw_hash), "html.parser"), args.locator)
            output(
                {
                    "snapshot_id": identifier,
                    "record_locator": args.locator,
                    "tag": node.name,
                    "text": node.get_text(),
                }
            )
        else:
            output(
                {
                    "snapshot_id": identifier,
                    "matching_observations": [
                        o.model_dump(mode="json")
                        for o in result.observations
                        if o.record_locator == args.locator
                    ],
                    "issues": [i.model_dump() for i in result.issues if i.locator == args.locator],
                }
            )
        return 0
    if args.output:
        path = args.output.resolve()
        if path.is_relative_to(ROOT) and not path.is_relative_to(ROOT / "state"):
            raise ValueError("Parser raw report must stay outside Git/inside state")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    output(
        {
            "snapshot_id": identifier,
            "observations": len(result.observations),
            "fact_kinds": dict(Counter(o.fact_kind for o in result.observations)),
            "issues": dict(Counter(i.code for i in result.issues)),
            "metadata": result.metadata,
            "persisted": False,
        }
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, SQLAlchemyError) as exc:
        print(
            f"Parser stopped ({type(exc).__name__}): configuration/database/raw integrity error; credentials not logged",
            file=sys.stderr,
        )
        sys.exit(2)
