"""Bounded subprocess replay. No DB credentials passed to the extraction child."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

from services.api.source_profiles import SourceProfile
from services.crawler.raw import RawStorage
from services.data.parsers.contract import ParseLimits, ParseResult, SnapshotRef

ROOT = Path(__file__).resolve().parents[3]


def replay(
    snapshot: SnapshotRef,
    profile: SourceProfile,
    *,
    raw: RawStorage | None = None,
    limits: ParseLimits | None = None,
    revision: str = "1",
) -> ParseResult:
    limits = limits or ParseLimits()
    raw = raw or RawStorage(Path(os.getenv("CRAWLER_RAW_DIR", "state/raw")))
    path = raw.path(snapshot.raw_hash)
    if path.stat().st_size > limits.max_bytes:
        result = ParseResult()
        result.issue("body_limit", "document", "Raw file exceeds byte budget", "error")
        return result
    data = raw.read(snapshot.raw_hash)
    if len(data) != snapshot.byte_size:
        raise ValueError("Snapshot size mismatch")
    request = {
        "snapshot": snapshot.model_dump(mode="json"),
        "profile": profile.model_dump(mode="json"),
        "limits": limits.model_dump(),
        "revision": revision,
        "raw_path": str(path),
    }
    result = ParseResult()
    peak = 0
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tuyensinh-parse-") as directory:
        base = Path(directory)
        input_file = base / "request.json"
        output_file = base / "result.json"
        input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        env = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
        }
        env |= {"PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1"}
        with subprocess.Popen(
            [
                sys.executable,
                "-m",
                "services.data.parsers.worker",
                str(input_file),
                str(output_file),
            ],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ) as process:
            monitor = psutil.Process(process.pid)
            code = None
            while process.poll() is None:
                if time.monotonic() - start > limits.timeout_seconds:
                    code = "parse_timeout"
                try:
                    peak = max(peak, monitor.memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                if peak > limits.max_rss_bytes:
                    code = "parse_memory_limit"
                if output_file.exists() and output_file.stat().st_size > limits.max_output_bytes:
                    code = "parse_output_limit"
                if code:
                    process.kill()
                    process.wait(timeout=5)
                    break
                time.sleep(0.02)
            if code:
                result.issue(code, "document", "Isolated parser resource budget exceeded", "error")
            elif process.returncode != 0 or not output_file.exists():
                result.issue(
                    "parse_process_failed",
                    "document",
                    "Parser process failed; no partial output committed",
                    "error",
                )
            elif output_file.stat().st_size > limits.max_output_bytes:
                result.issue(
                    "parse_output_limit", "document", "Parser output exceeds budget", "error"
                )
            else:
                try:
                    result = ParseResult.model_validate_json(
                        output_file.read_text(encoding="utf-8")
                    )
                except ValueError:
                    result.issue(
                        "invalid_parse_output", "document", "Child output invalid", "error"
                    )
    result.metadata |= {
        "peak_rss_bytes": peak,
        "elapsed_seconds": round(time.monotonic() - start, 4),
        "network_disabled": True,
    }
    return result
