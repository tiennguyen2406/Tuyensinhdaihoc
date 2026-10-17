"""Explicit operator CLI, separate from FastAPI. Does not run migrations."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from services.api.db.models import crawl_schedules, source_snapshots, sources
from services.api.db.session import engine, schema_is_current
from services.api.source_profiles import SourceProfile
from services.crawler.downloader import Crawler, Deferred, links
from services.crawler.raw import RawStorage
from services.crawler.state import Store


def output(value: object) -> None:
    print(json.dumps(value, default=str, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Raw-only crawler; no admission facts are published"
    )
    parser.add_argument(
        "command",
        choices=[
            "validate",
            "preflight",
            "start",
            "due",
            "work",
            "stop",
            "resume",
            "stats",
            "replay",
        ],
    )
    parser.add_argument("target", help="Profile JSON path, run UUID, or snapshot UUID (replay)")
    parser.add_argument(
        "--budget", type=int, default=5, help="All HTTP hops including robots, max 1000"
    )
    parser.add_argument("--additional-budget", type=int, default=0)
    parser.add_argument("--worker", default=f"cli-{os.getpid()}")
    args = parser.parse_args()
    profile_commands = {"validate", "preflight", "start", "due"}
    profile = (
        SourceProfile.model_validate_json(Path(args.target).read_text(encoding="utf-8"))
        if args.command in profile_commands
        else None
    )
    if args.command == "validate":
        assert profile is not None
        output(
            {
                "profile_id": profile.profile_id,
                "review_status": profile.review_status,
                "schema_valid": True,
            }
        )
        return 0
    with engine.connect() as connection:
        if not schema_is_current(connection):
            output(
                {"error": "schema_out_of_date", "action": "Run reviewed Alembic upgrade explicitly"}
            )
            return 2
    store = Store(engine)
    raw = RawStorage(Path(os.getenv("CRAWLER_RAW_DIR", "state/raw")))
    if args.command in ("start", "preflight", "due"):
        assert profile is not None
        if args.command == "preflight":
            run = store.start(profile, args.budget, preflight=True)
            crawler = Crawler(store, raw, profile)
            try:
                robots, interval = crawler.robots(run, str(profile.seed_urls[0]))
                from services.crawler.transport import USER_AGENT

                output(
                    {
                        "run_id": run,
                        "robots_allow_seeds": {
                            str(url): robots.can_fetch(str(url), USER_AGENT)
                            for url in profile.seed_urls
                        },
                        "minimum_interval_seconds": interval,
                    }
                )
            except (Deferred, ValueError, OSError) as exc:
                store.stop(run, "preflight_incomplete")
                output(
                    {
                        "run_id": run,
                        "error": type(exc).__name__,
                        "details": "Review robots/network state; no page downloaded",
                    }
                )
                return 2
            store.stop(run, "preflight_finished_no_content_fetch")
            output(store.stats(run))
            return 0
        run = store.start(profile, args.budget, preflight=args.command == "due")
        if args.command == "due":
            if profile.review_status != "eligible":
                raise ValueError("Profile not eligible")
            with engine.connect() as c:
                rows = c.execute(
                    sa.select(sources.c.canonical_url, crawl_schedules.c.resource_kind)
                    .join(crawl_schedules, crawl_schedules.c.source_id == sources.c.id)
                    .where(
                        crawl_schedules.c.profile_id == profile.profile_id,
                        crawl_schedules.c.due_at <= datetime.now(UTC),
                        crawl_schedules.c.resource_kind != "robots",
                    )
                ).all()
            for url, kind in rows:
                store.enqueue(run, str(url), 0, str(kind))
        print(f"run_id={run}", flush=True)
        Crawler(store, raw, profile).work(run, worker=args.worker)
        output(store.stats(run))
        return 0
    identifier = UUID(args.target)
    if args.command == "replay":
        with engine.connect() as c:
            row = (
                c.execute(sa.select(source_snapshots).where(source_snapshots.c.id == identifier))
                .mappings()
                .one()
            )
        body = raw.read(row["raw_hash"])
        output(
            {
                "snapshot_id": identifier,
                "sha256": row["raw_hash"],
                "byte_size": len(body),
                "hash_valid": True,
                "links": links(body, row["final_url"])
                if row["media_type"] in ("text/html", "application/xhtml+xml")
                else [],
                "facts_written": 0,
            }
        )
        return 0
    if args.command == "stop":
        store.stop(identifier)
    elif args.command in ("work", "resume"):
        if args.command == "resume":
            store.resume(identifier, args.additional_budget)
        profile = SourceProfile.model_validate(store.stats(identifier)["profile"])
        Crawler(store, raw, profile).work(identifier, worker=args.worker)
    stats = store.stats(identifier)
    stats.pop("profile", None)
    output(stats)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Worker interrupted; task lease recovers after five minutes", file=sys.stderr)
        sys.exit(130)
    except (ValueError, OSError, SQLAlchemyError):
        print(
            "Crawler stopped: configuration, storage or database error; no credentials logged",
            file=sys.stderr,
        )
        sys.exit(2)
