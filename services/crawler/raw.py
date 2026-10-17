"""Immutable content-addressed blobs, independent of source URL and fetch chronology."""

import hashlib
import os
import re
import tempfile
from pathlib import Path


class RawStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        repository = Path(__file__).resolve().parents[2]
        if self.root.is_relative_to(repository) and not any(
            self.root.is_relative_to(repository / allowed) for allowed in ("state/raw", "data/raw")
        ):
            raise ValueError("Raw storage must be in an ignored raw directory or outside checkout")
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, digest: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid SHA-256")
        return self.root / digest[:2] / digest[2:4] / digest

    def read(self, digest: str) -> bytes:
        data = self.path(digest).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("Raw hash mismatch")
        return data

    def put(self, data: bytes) -> tuple[str, str]:
        digest = hashlib.sha256(data).hexdigest()
        target = self.path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".raw-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Atomic create-if-absent on Windows/Unix. No replacement of an existing blob.
                os.link(temporary, target)
            except FileExistsError:
                self.read(digest)
        finally:
            os.unlink(temporary)  # Only the unique temporary file owned by this call.
        return digest, target.as_uri()
