import socket
from datetime import UTC, datetime, timedelta

import pytest

from services.crawler.urls import URLPolicy, canonicalize, retry_after
from tests.crawler.helpers import profile


def test_business_query_and_duplicate_order_survive_tracking_removal():
    assert (
        canonicalize(
            "HTTPS://Example.EDU.VN:443/path?year=2025&page=2&id=7&id=8&utm_source=x&fbclid=x#top"
        )
        == "https://example.edu.vn/path?year=2025&page=2&id=7&id=8"
    )
    assert (
        canonicalize("../a?year=2024", "https://example.edu.vn/x/y")
        == "https://example.edu.vn/a?year=2024"
    )


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://user:pass@example.edu.vn/",
        "https://other.edu.vn/",
        "https://example.edu.vn:8443/",
        "https://example.edu.vn/a\\evil",
        "https://example.edu.vn/a%0d%0aX:y",
    ],
)
def test_reject_unsafe_or_unlisted_urls(url):
    with pytest.raises(ValueError):
        URLPolicy(profile()).check(url)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "::1",
        "fc00::1",
        "100.64.0.1",
        "224.0.0.1",
        "ff02::1",
        "::ffff:127.0.0.1",
    ],
)
def test_dns_blocks_non_public_destinations(address):
    def resolver(*a):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]

    with pytest.raises(ValueError, match="destination"):
        URLPolicy(profile(), resolver=resolver).resolve("https://example.edu.vn/")


def test_mixed_public_private_dns_is_rejected():
    def resolver(*a):
        return [(2, 1, 6, "", (ip, 443)) for ip in ["8.8.8.8", "127.0.0.1"]]

    with pytest.raises(ValueError):
        URLPolicy(profile(), resolver=resolver).resolve("https://example.edu.vn/")


def test_retry_after_seconds_and_http_date_are_not_capped():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert retry_after("7200", now) == now + timedelta(hours=2)
    assert retry_after("Thu, 01 Jan 2026 03:00:00 GMT", now) == now + timedelta(hours=3)
    assert retry_after("invalid", now) is None


def test_production_transport_pins_validated_address(monkeypatch):
    from services.crawler.transport import Transport

    calls = []

    def resolver(*args):
        calls.append("resolve")
        return [(2, 1, 6, "", ("8.8.8.8", 443))]

    def connect(address, **kwargs):
        calls.append(address)
        raise OSError("Stop before wire I/O")

    monkeypatch.setattr("services.crawler.transport.socket.create_connection", connect)
    with pytest.raises(OSError):
        Transport(URLPolicy(profile(), resolver=resolver)).get("https://example.edu.vn/", {})
    assert calls == ["resolve", ("8.8.8.8", 443)]


def test_equivalent_dot_segments_and_unicode_urls_are_canonical():
    assert (
        canonicalize("https://example.edu.vn/a/../b/./%7euser?year=2025")
        == "https://example.edu.vn/b/~user?year=2025"
    )
    assert (
        canonicalize("https://example.edu.vn/tuyển-sinh?name=Đại")
        == "https://example.edu.vn/tuy%E1%BB%83n-sinh?name=%C4%90%E1%BA%A1i"
    )
