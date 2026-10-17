"""One pinned-address HTTP hop. Redirects and robots are handled by shared policy."""

import http.client
import socket
import ssl
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from services.crawler.urls import URLPolicy

MAX_BYTES = 25 * 1024 * 1024
USER_AGENT = "TuyenSinhDaiHocPilot/0.1 (+https://github.com/tiennguyen2406/Tuyensinhdaihoc)"


@dataclass(frozen=True)
class Response:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes
    elapsed_ms: int


class Transport:
    def __init__(
        self, policy: URLPolicy, *, max_bytes: int = MAX_BYTES, timeout: float = 30
    ) -> None:
        self.policy = policy
        self.max_bytes = max_bytes
        self.timeout = min(timeout, 30)

    def get(
        self,
        url: str,
        headers: dict[str, str],
        *,
        document: bool = False,
        max_bytes: int | None = None,
    ) -> Response:
        started = time.monotonic()
        deadline = started + self.timeout
        host, port, address = self.policy.resolve(url, document=document)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("request_deadline")
        parsed = urlsplit(url)
        conn = http.client.HTTPConnection(host, port, timeout=self.timeout)
        conn.default_port = 443 if parsed.scheme == "https" else 80
        # Connect to the IP we validated, never resolve the hostname a second time.
        raw_socket = socket.create_connection((address, port), timeout=remaining)
        conn.sock = raw_socket

        expired = threading.Event()

        def abort() -> None:
            expired.set()
            try:
                if conn.sock is not None:
                    conn.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()

        timer = threading.Timer(max(0, deadline - time.monotonic()), abort)
        timer.daemon = True
        timer.start()
        try:
            if parsed.scheme == "https":
                secured = ssl.create_default_context().wrap_socket(
                    raw_socket, server_hostname=host, do_handshake_on_connect=False
                )
                conn.sock = secured
                secured.do_handshake()
            request_headers = {
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Connection": "close",
            } | headers
            conn.request(
                "GET",
                parsed.path + ("?" + parsed.query if parsed.query else ""),
                headers=request_headers,
            )
            response = conn.getresponse()
            values = {key.lower(): value for key, value in response.getheaders()}
            lengths = response.headers.get_all("Content-Length", [])
            if len(set(lengths)) > 1 or lengths and response.getheader("Transfer-Encoding"):
                raise ValueError("ambiguous_body_length")
            expected = int(values["content-length"]) if "content-length" in values else None
            if expected is not None and expected < 0:
                raise ValueError("invalid_body_length")
            limit = min(self.max_bytes, max_bytes if max_bytes is not None else self.max_bytes)
            if response.status == 304:
                body = b""
            else:
                if int(values.get("content-length", "0")) > limit:
                    raise ValueError("body_too_large")
                chunks: list[bytes] = []
                count = 0
                while True:
                    if time.monotonic() - started > self.timeout:
                        raise TimeoutError("request_deadline")
                    chunk = response.read1(min(65536, limit + 1 - count))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    count += len(chunk)
                    if count > limit:
                        raise ValueError("body_too_large")
                body = b"".join(chunks)
                if expected is not None and len(body) != expected:
                    raise OSError("incomplete_body")
            if expired.is_set() or time.monotonic() > deadline:
                raise TimeoutError("request_deadline")
            if values.get("content-encoding", "identity").lower() not in ("identity", ""):
                raise ValueError("unsupported_content_encoding")
            return Response(
                url, response.status, values, body, round((time.monotonic() - started) * 1000)
            )
        finally:
            timer.cancel()
            conn.close()
