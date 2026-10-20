"""Trusted local CLI. Review identity comes from DB authentication, never a JSON actor."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from services.api.db.session import ROOT, engine, schema_is_current
from services.api.db.validators import record
from services.data.publication.contract import IntegrationRequest, ReviewCommand
from services.data.publication.packets import inspect_packet, list_packets
from services.data.publication.publish import Publisher
from services.data.publication.review import ReviewService


def private_path(path: Path) -> Path:
    value = path.resolve()
    if value.is_relative_to(ROOT) and not value.is_relative_to(ROOT / "state"):
        raise ValueError(
            "Review decision/output files must be in ignored state/ or outside checkout"
        )
    return value


def packet_plan(packet: dict[str, Any]) -> dict[str, Any]:
    c = packet["candidate"]
    needs = [
        "source_authority",
        "canonical_registry",
        "scale",
        "basis",
        "combination",
        "round",
        "population",
        "conditions",
        "publication_review",
    ]
    if c["fact_kind"] == "tuition":
        needs = [
            "academic_year_scope_review",
            "admission_year_required_by_current_DDL",
            "no_fake_offering_or_cohort",
        ]
    return dict(
        preview_only=True,
        can_publish=False,
        binding={k: packet[k] for k in ["resolution_id", "candidate_key", "packet_sha256"]},
        source=packet["source_identity"],
        evidence=packet["evidence"],
        candidate=c,
        proposals=packet["resolution"]["entities"],
        needs_decision=needs,
        impact=dict(canonical_entities_created=0, cutoffs_created=0, catalog_version_delta=0),
        next_steps=[
            "Responsible reviewer authenticates using a dedicated DB login",
            "Review exact registry mappings and field evidence",
            "Plan/apply bootstrap, export immutable registry and rerun T07",
            "Review cutoff-specific gates; then plan/apply publication",
        ],
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Local reviewed T08 CLI; no production OIDC/API or implicit approvals"
    )
    parser.add_argument(
        "command", choices=["list", "inspect", "plan", "apply", "replay", "export", "integrate"]
    )
    parser.add_argument("--resolution", type=UUID)
    parser.add_argument("--candidate")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--file-sha256", help="SHA-256 of exact human-reviewed file bytes")
    parser.add_argument("--decision", type=UUID)
    parser.add_argument("--registry-job", type=UUID)
    parser.add_argument("--expected-revision", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = private_path(args.output) if args.output else None
    body = private_path(args.file).read_bytes() if args.file else None
    if args.file_sha256 and (body is None or hashlib.sha256(body).hexdigest() != args.file_sha256):
        raise ValueError("Reviewed file digest changed")
    command = (
        ReviewCommand.model_validate_json(body) if body and args.command != "integrate" else None
    )
    integration = (
        IntegrationRequest.model_validate_json(body)
        if body and args.command == "integrate"
        else None
    )
    if args.command == "integrate" and (integration is None or output and output.exists()):
        raise ValueError("Integration requires an input file and a fresh immutable output path")
    if (
        command
        and args.command == "apply"
        and (command.proposal_integration or command.operation_bindings)
        and not args.file_sha256
    ):
        raise ValueError("Batch bootstrap apply requires --file-sha256 of human-reviewed bytes")
    user = os.getenv("PUBLICATION_DB_USER")
    password = os.getenv("PUBLICATION_DB_PASSWORD")
    if bool(user) != bool(password):
        raise PermissionError("Both dedicated publication DB credential variables are required")
    db = (
        create_engine(
            engine.url.set(username=user, password=password),
            hide_parameters=True,
            connect_args={"connect_timeout": 3},
        )
        if user
        else engine
    )
    result: Any
    try:
        with db.begin() as c:
            if args.command in {"list", "inspect", "plan", "export", "integrate"}:
                c.exec_driver_sql("SET TRANSACTION READ ONLY")
            if not schema_is_current(c):
                raise ValueError("Schema is not current; CLI never migrates automatically")
            svc = ReviewService(c)
            if args.command == "integrate":
                from services.data.publication.integration import prepare_integration

                assert integration is not None
                result = prepare_integration(
                    c, integration.bindings, integration.proposal_keys, integration.version
                )
                if (
                    result["expected_registry_version"],
                    result["expected_alias_version"],
                    result["spec"]["base_sha256"],
                ) != (
                    integration.expected_registry_version,
                    integration.expected_alias_version,
                    integration.base_sha256,
                ):
                    raise ValueError("Stale integration registry/alias/base hash")
            elif args.command == "list":
                result = list_packets(c)
            elif args.command in {"inspect", "plan"}:
                if command and args.command == "plan":
                    result = svc.plan(command)
                else:
                    if not args.resolution or not args.candidate:
                        raise ValueError("--resolution and --candidate required")
                    packet = inspect_packet(c, args.resolution, args.candidate)
                    result = packet_plan(packet) if args.command == "plan" else packet
            elif args.command == "export":
                if not args.registry_job:
                    raise ValueError("--registry-job required")
                job = record(c, "ingest_jobs", args.registry_job)
                if job["job_type"] != "registry_version":
                    raise ValueError("Registry manifest required")
                result = job["payload"]["registry"]
            elif args.command == "apply" and command:
                if args.decision:
                    raise ValueError("Choose a review file or an approved decision, not both")
                result = svc.apply(command)
            else:
                if not args.decision:
                    raise ValueError("--decision required for publication apply/replay")
                draft = svc.validated(args.decision)
                revision = args.expected_revision
                if args.command == "replay":
                    revision = record(c, "ingest_jobs", args.decision)["payload"]["command"][
                        "expected_revision"
                    ]
                result = Publisher(c).publish(draft, revision).model_dump(mode="json")
        data = json.dumps(result, ensure_ascii=False, indent=2, default=str)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(data, encoding="utf-8")
        print(data)
        return 0
    finally:
        db.dispose()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, PermissionError, OSError, SQLAlchemyError) as error:
        # Database exceptions can embed SQL/DSNs/parameters; never print their details.
        reason = (
            str(error)
            if isinstance(error, (ValueError, PermissionError))
            and not isinstance(error, SQLAlchemyError)
            else "Database or private file operation blocked; details withheld"
        )
        print(
            json.dumps(
                dict(blocked=True, error_type=type(error).__name__, reason=reason),
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(2)
