import pytest

from services.crawler.raw import RawStorage
from services.data.parsers.contract import ParseLimits
from services.data.parsers.registry import extract
from services.data.parsers.runner import replay
from tests.parsers.helpers import profile, snapshot
from tests.parsers.test_html import HTML


def test_isolated_replay_hash_and_no_network(tmp_path):
    raw = RawStorage(tmp_path)
    raw.put(HTML)
    ref = snapshot(HTML)
    result = replay(ref, profile(), raw=raw)
    assert result.observations
    assert result.metadata["network_disabled"] is True
    assert result.metadata["parser_version"].startswith("html/")
    assert result.metadata["peak_rss_bytes"] > 0
    assert result.metadata["elapsed_seconds"] > 0
    raw.path(ref.raw_hash).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="hash"):
        replay(ref, profile(), raw=raw)


def test_output_and_memory_and_timeout_budgets(tmp_path):
    raw = RawStorage(tmp_path)
    raw.put(HTML)
    ref = snapshot(HTML)
    for limits, code in [
        (ParseLimits(timeout_seconds=0.001), "parse_timeout"),
        (ParseLimits(max_rss_bytes=1024 * 1024), "parse_memory_limit"),
        (ParseLimits(max_output_bytes=10), "parse_output_limit"),
    ]:
        result = replay(ref, profile(), raw=raw, limits=limits)
        assert not result.observations
        assert code in {i.code for i in result.issues}


def test_registry_keeps_same_raw_for_new_parser_namespace_and_rejects_wrong_hash():
    ref = snapshot(HTML)
    a = extract(ref, profile(), HTML, revision="1")
    b = extract(ref, profile(), HTML, revision="2")
    assert a.observations[0].raw_fields == b.observations[0].raw_fields
    assert a.observations[0].parser_version != b.observations[0].parser_version
    with pytest.raises(ValueError, match="hash"):
        extract(ref, profile(), HTML + b"x")
