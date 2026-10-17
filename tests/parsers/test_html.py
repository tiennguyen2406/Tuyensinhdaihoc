"""Synthetic HTML behavior cases, permitted to store in Git."""

from bs4 import BeautifulSoup

from services.data.parsers.contract import ParseLimits
from services.data.parsers.html import locate, parse_html
from tests.parsers.helpers import profile, snapshot

HTML = """<html><body><nav>Điểm chuẩn 99</nav><article><h1>Thông tin tuyển sinh năm 2026</h1>
<p>Hình thức đào tạo: Chính quy</p><h2>Cơ sở phía Bắc</h2>
<h3>Điểm trúng tuyển 2024 và 2025</h3><table><caption>Kết quả đã công bố</caption><thead>
<tr><th rowspan=2>Ngành</th><th colspan=2>Năm 2024</th><th rowspan=2>Tổ hợp</th></tr>
<tr><th>THPT</th><th>HSA</th></tr></thead><tbody>
<tr><td rowspan=2>Ngành TEST</td><td>24,50</td><td>90</td><td>A00, A01 (*)</td></tr>
<tr><td></td><td>91</td><td>D01</td></tr></tbody></table>
<p class=footnote>(*) Các phương thức có điều kiện riêng.</p></article><aside>Điểm chuẩn 88</aside></body></html>""".encode()


def test_multi_headers_spans_blanks_footnotes_and_exact_locators():
    ref = snapshot(HTML)
    result = parse_html(ref, profile(), HTML)
    rows = [o for o in result.observations if o.raw_fields.get("kind") == "table_row"]
    assert len(rows) == 2 and all(o.fact_kind == "cutoff" for o in rows)
    one, two = rows
    assert one.raw_fields["cells"][1]["text"] == "24,50"
    assert two.raw_fields["cells"][1]["text"] == ""
    assert two.raw_fields["cells"][0]["span_reference"] is True
    assert two.raw_fields["cells"][0]["text"] is None
    assert one.raw_fields["cells"][3]["text"] == "A00, A01 (*)"
    assert [h["text"] for h in one.raw_fields["headers"][1]] == ["Năm 2024", "THPT"]
    assert "điều kiện" in one.raw_fields["footnotes"][0]["text"]
    soup = BeautifulSoup(HTML, "html.parser")
    for obs in rows:
        assert locate(soup, obs.record_locator).name == "tr"
        assert obs.snapshot_id == ref.snapshot_id and obs.source_id == ref.source_id
        assert obs.verification_status == "unverified" and obs.transform_version
        for cell in obs.raw_fields["cells"]:
            if cell["origin"]:
                assert locate(soup, cell["origin"]).name in ("td", "th")
    assert "Cơ sở phía Bắc" in str(one.raw_fields["context"])


def test_threshold_not_cutoff_and_ambiguous_header_not_assumed():
    data = "<article><h1>Tuyển sinh năm 2026</h1><h2>Ngưỡng đầu vào / Điểm sàn</h2><table><tr><th>Ngành</th><th>Điểm</th></tr><tr><td>TEST</td><td>18</td></tr></table></article>".encode()
    result = parse_html(snapshot(data), profile(), data)
    assert result.observations and not any(o.fact_kind == "cutoff" for o in result.observations)
    ambiguous = b"<article><table><tr><th>Code</th><th>Score</th></tr><tr><td>X</td><td>18</td></tr></table></article>"
    result = parse_html(snapshot(ambiguous), profile(), ambiguous)
    assert not any(o.fact_kind == "cutoff" for o in result.observations)
    assert "ambiguous_table_kind" in {i.code for i in result.issues}


def test_unknown_root_returns_issue_no_footer_facts():
    data = "<html><footer>Điểm trúng tuyển 2025 29</footer></html>".encode()
    result = parse_html(snapshot(data), profile(), data)
    assert not result.observations
    assert result.issues[0].code == "business_region_missing"


def test_image_and_nested_table_require_review_and_grid_budget_is_enforced():
    data = b'<article><p>Admission table image</p><img src="/table.png"><table><tr><td rowspan="999999">X</td></tr></table></article>'
    result = parse_html(snapshot(data), profile(), data, limits=ParseLimits(max_cells=100))
    assert not result.observations
    assert "table_cell_limit" in {i.code for i in result.issues}
    assert "image_requires_review" in {i.code for i in result.issues}


def test_repeated_parse_is_deterministic():
    ref = snapshot(HTML)
    assert (
        parse_html(ref, profile(), HTML).model_dump()
        == parse_html(ref, profile(), HTML).model_dump()
    )


def test_context_uses_preceding_heading_stack_not_future_campus():
    data = """<article><h1>Thông tin tuyển sinh 2026</h1><section><h3>Chính quy</h3><h5>Kết quả 2024</h5><h6>Cơ sở Bắc</h6><table><tr><th>Ngành</th><th>Điểm trúng tuyển</th></tr><tr><td>A</td><td>24</td></tr></table><h6>Cơ sở Nam</h6><table><tr><th>Ngành</th><th>Điểm trúng tuyển</th></tr><tr><td>B</td><td>23</td></tr></table></section></article>""".encode()
    result = parse_html(snapshot(data), profile(), data)
    rows = [o for o in result.observations if o.raw_fields.get("kind") == "table_row"]
    assert "Cơ sở Bắc" in str(rows[0].raw_fields["context"])
    assert "Cơ sở Nam" not in str(rows[0].raw_fields["context"])
    assert "Cơ sở Nam" in str(rows[1].raw_fields["context"])
    assert "Cơ sở Bắc" not in str(rows[1].raw_fields["context"])
    assert "Chính quy" in str(rows[0].raw_fields["context"])


def test_scholarship_including_tuition_is_not_a_tuition_policy():
    data = "<article><p>Học bổng đặc biệt bao gồm học phí.</p></article>".encode()
    result = parse_html(snapshot(data), profile(), data)
    assert result.observations[0].fact_kind == "scholarship"


def test_row_without_any_cutoff_value_remains_catalog_for_review():
    data = "<article><h2>Điểm trúng tuyển</h2><table><tr><th>Ngành</th><th>Điểm trúng tuyển</th></tr><tr><td>New TEST</td><td></td></tr></table></article>".encode()
    result = parse_html(snapshot(data), profile(), data)
    rows = [o for o in result.observations if o.raw_fields.get("kind") == "table_row"]
    assert len(rows) == 1 and rows[0].fact_kind == "catalog"
    assert "cutoff_row_without_value" in {i.code for i in result.issues}


def test_multiple_numbered_policy_sections_are_not_forced_into_one_fact_kind():
    data = "<article><p>5. Các thông tin tuyển sinh: điểm thưởng 1,00. 10. Học phí dự kiến 30 triệu. Học bổng hỗ trợ học phí theo quy định riêng.</p></article>".encode()
    result = parse_html(snapshot(data), profile(), data)
    assert result.observations[0].fact_kind == "catalog"
    assert "mixed_narrative_fact_kinds" in {i.code for i in result.issues}
