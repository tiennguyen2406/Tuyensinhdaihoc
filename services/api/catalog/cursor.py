"""Signed keyset cursors bound to endpoint, filters, limit, sort and serving version."""

import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Any

from fastapi import HTTPException

from services.data.normalization.values import text

_KEY = os.getenv("CATALOG_CURSOR_SECRET", "").encode() or secrets.token_bytes(32)


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def token(payload: dict[str, Any]) -> str:
    encoded = b64(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    return encoded + "." + b64(hmac.digest(_KEY, encoded.encode(), "sha256"))


def binding(endpoint: str, params: dict[str, Any]) -> str:
    values = {k: str(v) if v is not None else None for k, v in params.items() if k != "cursor"}
    if "query" in values:
        values["query"] = text(values["query"] or "").search_key
    raw = json.dumps([endpoint, values, "name_uuid/1"], sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def after(cursor: str | None, expected_binding: str, version: int) -> tuple[str, ...] | None:
    if not cursor:
        return None
    try:
        encoded, signature = cursor.split(".")
        if not hmac.compare_digest(signature, b64(hmac.digest(_KEY, encoded.encode(), "sha256"))):
            raise ValueError("signature")
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        if b64(raw) != encoded:
            raise ValueError("encoding")
        p = json.loads(raw)
        if (
            p["contract"] != "cursor/1"
            or p["binding"] != expected_binding
            or not isinstance(p["after"], list)
            or not all(isinstance(x, str) for x in p["after"])
            or len(p["after"]) not in (1, 2)
        ):
            raise ValueError("binding")
        if p["dataset_version"] != version:
            raise HTTPException(
                409,
                detail={
                    "code": "DATASET_CHANGED",
                    "message": "Dữ liệu đã thay đổi; bắt đầu lại danh sách.",
                },
            )
        return tuple(p["after"])
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            422,
            detail={
                "code": "INVALID_CURSOR",
                "message": "Cursor không hợp lệ hoặc không khớp bộ lọc.",
            },
        ) from error
