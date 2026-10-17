import ipaddress
import re
import socket
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from queue import Empty, Queue
from typing import Any
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

from services.api.source_profiles import SourceProfile

TRACKING = {"fbclid", "gclid", "dclid", "msclkid", "_ga", "mc_cid", "mc_eid"}


def _path(value: str) -> str:
    # RFC 3986 unreserved normalization and remove_dot_segments; preserve double slashes.
    value = re.sub(
        r"%[0-9a-fA-F]{2}",
        lambda m: (
            chr(int(m[0][1:], 16))
            if chr(int(m[0][1:], 16))
            in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
            else m[0].upper()
        ),
        value,
    )
    output = ""
    while value:
        if value.startswith(("../", "./")):
            value = value.partition("/")[2]
        elif value.startswith("/./") or value == "/.":
            value = "/" + value[3:]
        elif value.startswith("/../") or value == "/..":
            value = "/" + value[4:]
            output = output.rsplit("/", 1)[0]
        elif value in (".", ".."):
            value = ""
        else:
            end = value.find("/", 1 if value.startswith("/") else 0)
            if end == -1:
                output += value
                value = ""
            else:
                output += value[:end]
                value = value[end:]
    return quote(output or "/", safe="/:@!$&'()*+,;=-._~%")


def canonicalize(url: str, base: str | None = None) -> str:
    if re.search(r"[\x00-\x20\x7f\\]", url) or re.search(r"%0[ad]", url, re.I):
        raise ValueError("Invalid URL characters")
    parsed = urlsplit(urljoin(base, url) if base else url)
    if parsed.scheme.lower() not in {"https", "http"} or not parsed.hostname:
        raise ValueError("HTTP(S) URL required")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials forbidden")
    host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    if port and port != (443 if parsed.scheme.lower() == "https" else 80):
        host += f":{port}"
    # Preserve escaping, repeated parameters and order. Only remove declared tracking keys.
    query = "&".join(
        part
        for part in parsed.query.split("&")
        if part
        and not (
            (key := unquote(part.split("=", 1)[0]).lower()).startswith("utm_") or key in TRACKING
        )
    )
    return urlunsplit(
        (
            parsed.scheme.lower(),
            host,
            _path(parsed.path),
            quote(query, safe="=&?/:@!$'()*+,;%-._~"),
            "",
        )
    )


def retry_after(value: str | None, now: datetime) -> datetime | None:
    if not value:
        return None
    try:
        if value.strip().isdigit():
            return now + timedelta(seconds=int(value.strip()))
        result = parsedate_to_datetime(value)
        if result.tzinfo is None:
            result = result.replace(tzinfo=UTC)
        return max(now, result)
    except (ValueError, TypeError, OverflowError):
        return None


class URLPolicy:
    def __init__(
        self,
        profile: SourceProfile,
        *,
        resolver: Callable[..., Any] = socket.getaddrinfo,
        test_local: bool = False,
    ) -> None:
        self.profile = profile
        self.resolver = resolver
        # Only constructed by offline fixtures. No CLI/environment flag enables private networks.
        self.test_local = test_local

    def check(self, url: str, *, document: bool = False) -> str:
        url = canonicalize(url)
        parsed = urlsplit(url)
        hosts = self.profile.allowed_hosts + (
            self.profile.allowed_document_hosts if document else []
        )
        if parsed.hostname not in hosts:
            raise ValueError("Host outside allowlist")
        if not self.test_local and parsed.port not in (None, 80, 443):
            raise ValueError("Port outside policy")
        return url

    def resolve(self, url: str, *, document: bool = False) -> tuple[str, int, str]:
        parsed = urlsplit(self.check(url, document=document))
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        result: Queue[Any] = Queue(maxsize=1)

        def lookup() -> None:
            try:
                result.put(self.resolver(host, port, 0, socket.SOCK_STREAM))
            except Exception as exc:
                result.put(exc)

        threading.Thread(target=lookup, daemon=True).start()
        try:
            answers = result.get(timeout=5)
        except Empty:
            raise TimeoutError("dns_timeout") from None
        if isinstance(answers, Exception):
            raise OSError("dns_error") from None
        addresses = list(dict.fromkeys(item[4][0] for item in answers))
        if (
            not addresses
            or any(
                not ipaddress.ip_address(ip).is_global
                or ipaddress.ip_address(ip).is_multicast
                or ipaddress.ip_address(ip).is_reserved
                for ip in addresses
            )
            and not self.test_local
        ):
            raise ValueError("Non-public destination forbidden")
        return host, port, addresses[0]

    def discoverable(self, url: str, depth: int, *, document: bool = False) -> bool:
        try:
            self.check(url, document=document)
            path = urlsplit(url).path
            return (
                depth <= self.profile.max_depth
                and not any(
                    re.search(pattern, path) for pattern in self.profile.exclude_path_patterns
                )
                and (
                    not self.profile.include_path_patterns
                    or any(
                        re.search(pattern, path) for pattern in self.profile.include_path_patterns
                    )
                )
            )
        except ValueError:
            return False
