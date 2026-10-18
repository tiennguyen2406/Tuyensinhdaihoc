"""Private immutable bundles, with recoverable staging and atomic directory install."""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from services.api.db.session import ROOT
from services.data.publication.__main__ import private_path
from services.data.publication.contract import json_value
from services.data.releases.snapshot import BUILDER, FILTER, SCHEMA, coverage


def encode(value: Any) -> bytes:
    return (
        json.dumps(
            json_value(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def code_provenance() -> dict[str, Any]:
    paths = sorted((ROOT / "services/data/releases").glob("*.py"))
    paths += [
        ROOT / p
        for p in [
            "services/api/db/validators.py",
            "services/api/db/models.py",
            "services/api/db/session.py",
            "services/data/publication/contract.py",
            "services/data/publication/bootstrap.py",
            "services/data/publication/__main__.py",
            "services/api/alembic/versions/0004_releases.sql",
            "services/api/alembic/versions/0004_releases.py",
        ]
    ]
    files = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}
    return dict(
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        working_tree_dirty=bool(
            subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all", "--", *files, "uv.lock"],
                cwd=ROOT,
            )
        ),
        implementation_files=files,
        implementation_sha256=sha(encode(files)),
        lock_sha256=sha((ROOT / "uv.lock").read_bytes()),
    )


def write_file(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def sync_directory(path: Path) -> None:
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def verify_bundle(path: Path, expected_hash: str | None = None) -> dict[str, Any]:
    try:
        path = private_path(path)
        raw = path.read_bytes()
        digest = sha(raw)
        if expected_hash and digest != expected_hash:
            raise ValueError("Integrity conflict: manifest checksum")
        manifest = json.loads(raw)
        if (
            manifest["schema_version"] != SCHEMA
            or manifest["builder_version"] != BUILDER
            or manifest["filters"] != FILTER
        ):
            raise ValueError("Integrity conflict: unsupported manifest contract")
        if set(manifest["files"]) != {"cutoffs.json", "coverage.json"}:
            raise ValueError("Integrity conflict: unexpected bundle files")
        loaded = {}
        for name, info in manifest["files"].items():
            target = path.parent / name
            if target.is_symlink():
                raise ValueError("Integrity conflict: artifact symlink")
            data = target.read_bytes()
            if len(data) != info["size"] or sha(data) != info["sha256"]:
                raise ValueError("Integrity conflict: artifact size/checksum")
            loaded[name] = json.loads(data)
        payload, cov = loaded["cutoffs.json"], loaded["coverage.json"]
        records = payload["records"]
        if (
            payload["schema_version"] != SCHEMA
            or payload["catalog_version"] != manifest["catalog_version"]
            or payload["filters"] != FILTER
            or coverage(records) != cov
            or len(records) != len({r["cutoff"]["id"] for r in records})
            or manifest["counts"]
            != {
                k: cov[k]
                for k in ["canonical_cutoffs", "publication_groups", "revisions", "evidence_count"]
            }
            or manifest["snapshot_sha256"] != sha(encode(payload | {"coverage": cov}))
        ):
            raise ValueError("Integrity conflict: counts, coverage or snapshot binding")
        return dict(
            manifest=manifest,
            manifest_sha256=digest,
            manifest_uri=path.as_uri(),
            cutoff_count=len(records),
            coverage=cov,
        )
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Integrity conflict: missing or invalid bundle") from error


def store(root: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    root = private_path(root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"version-{snapshot['catalog_version']}"
    snapshot_hash = sha(encode(snapshot))
    if target.exists():
        existing = verify_bundle(target / "manifest.json")
        if existing["manifest"]["snapshot_sha256"] != snapshot_hash:
            raise ValueError("Integrity conflict: same version has different canonical content")
        return existing
    staging = root / ("staging-" + uuid4().hex)
    staging.mkdir()
    # Partial staging is deliberately retained after any failure; never repair a final bundle.
    payload = {k: v for k, v in snapshot.items() if k != "coverage"}
    contents = {"cutoffs.json": encode(payload), "coverage.json": encode(snapshot["coverage"])}
    for name, data in contents.items():
        write_file(staging / name, data)
    manifest = dict(
        schema_version=SCHEMA,
        builder_version=BUILDER,
        catalog_version=snapshot["catalog_version"],
        filters=FILTER,
        artifact_built_at=datetime.now(timezone.utc).isoformat(),
        catalog_changed_at=snapshot["catalog_changed_at"],
        counts={
            k: snapshot["coverage"][k]
            for k in ["canonical_cutoffs", "publication_groups", "revisions", "evidence_count"]
        },
        snapshot_sha256=snapshot_hash,
        files={name: dict(size=len(data), sha256=sha(data)) for name, data in contents.items()},
        provenance=code_provenance(),
        input_provenance=[
            dict(cutoff_id=r["cutoff"]["id"], lineage=r["lineage"]) for r in snapshot["records"]
        ],
        publication_time_field="records[].cutoff.system_valid_from; not artifact_built_at",
        serialization="UTF-8 NFC JSON; sorted keys; compact separators; LF; Decimal strings; null retained; records sorted UUID",
        visibility="internal_dev_only",
    )
    write_file(staging / "manifest.json", encode(manifest))
    verify_bundle(staging / "manifest.json")
    sync_directory(staging)
    # Caller holds the database session builder lock. Rename never replaces a complete directory.
    staging.rename(target)
    sync_directory(root)
    return verify_bundle(target / "manifest.json")
