"""Extraction subprocess entry point. Never imports database configuration."""

import json
import socket
import sys
from pathlib import Path

from services.api.source_profiles import SourceProfile
from services.data.parsers.contract import ParseLimits, SnapshotRef
from services.data.parsers.registry import extract


def deny_network(*args: object, **kwargs: object) -> None:
    raise PermissionError("Parser network access disabled")


def main() -> None:
    socket.socket.connect = deny_network  # type: ignore[method-assign]
    socket.socket.connect_ex = deny_network  # type: ignore[method-assign,assignment]
    socket.getaddrinfo = deny_network  # type: ignore[assignment]
    socket.create_connection = deny_network  # type: ignore[assignment]
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    limits = ParseLimits.model_validate(request["limits"])
    path = Path(request["raw_path"])
    if path.stat().st_size > limits.max_bytes:
        raise ValueError("Body limit")
    result = extract(
        SnapshotRef.model_validate(request["snapshot"]),
        SourceProfile.model_validate(request["profile"]),
        path.read_bytes(),
        limits=limits,
        revision=request["revision"],
    )
    Path(sys.argv[2]).write_text(result.model_dump_json(), encoding="utf-8")


if __name__ == "__main__":
    main()
