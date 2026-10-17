"""PDFs generated entirely from synthetic data for tests; no real document embedded."""

from io import BytesIO

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from services.data.parsers.contract import ParseLimits
from services.data.parsers.pdf import parse_pdf
from tests.parsers.helpers import profile, snapshot


def document(*, scan=False, pages=2, score="24.50", continued=True):
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=(600, 800))
    for number in range(pages):
        if scan:
            pdf.drawImage(ImageReader(Image.new("RGB", (200, 200), "white")), 50, 100, 400, 600)
        else:
            pdf.drawString(
                40,
                770,
                "SYNTHETIC FIXTURE - Diem trung tuyen 2025"
                + (" (continued)" if number and continued else ""),
            )
            pdf.drawString(40, 740, "Co so phia Bac - Hinh thuc dao tao: Chinh quy")
            # Ruled table, repeated header on next page; one deliberately empty score cell.
            for x in [40, 260, 400, 550]:
                pdf.line(x, 700, x, 580)
            for y in [700, 660, 620, 580]:
                pdf.line(40, y, 550, y)
            for x, text in [(50, "Program"), (270, "Method"), (410, "Diem trung tuyen")]:
                pdf.drawString(x, 677, text)
            pdf.drawString(50, 637, "TEST A")
            pdf.drawString(270, 637, "THPT")
            pdf.drawString(410, 637, score)
            pdf.drawString(50, 597, "TEST B")
            pdf.drawString(270, 597, "HSA")
            pdf.drawString(40, 550, "(*) Synthetic footnote; separate methods, no conversion.")
        pdf.showPage()
    pdf.save()
    return stream.getvalue()


def test_pdf_tables_pages_bboxes_headers_and_footnotes():
    data = document()
    result = parse_pdf(snapshot(data, "application/pdf"), profile(), data)
    rows = [o for o in result.observations if o.raw_fields.get("kind") == "table_row"]
    assert len(rows) == 4 and sum(o.fact_kind == "cutoff" for o in rows) == 2
    assert {o.raw_fields["page"] for o in rows} == {1, 2}
    assert rows[0].raw_fields["cells"][2]["text"] == "24.50"
    assert rows[1].raw_fields["cells"][2]["text"] == ""
    assert rows[2].raw_fields["continuation_of"] is not None
    assert "Synthetic footnote" in str(rows[0].raw_fields["footnotes"])
    for obs in rows:
        assert obs.record_locator.startswith("pdf:p")
        assert len(obs.raw_fields["bbox"]) == 4
        assert all(len(c["bbox"]) == 4 for c in obs.raw_fields["cells"] if c["bbox"])
    assert "empty_score_cell" in {i.code for i in result.issues}


def test_scan_generates_ocr_review_without_observations():
    data = document(scan=True)
    result = parse_pdf(snapshot(data, "application/pdf"), profile(), data)
    assert not result.observations
    assert result.needs_review
    assert [i.code for i in result.issues].count("ocr_required") == 2


def test_pdf_page_budget_rejects_entire_document():
    data = document(pages=2)
    result = parse_pdf(
        snapshot(data, "application/pdf"), profile(), data, limits=ParseLimits(max_pages=1)
    )
    assert not result.observations and result.issues[0].code == "pdf_page_limit"


def test_pdf_text_entry_threshold_is_not_cutoff():
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawString(30, 700, "Thong tin tuyen sinh 2026 - Nguong dau vao 18 diem")
    pdf.save()
    data = stream.getvalue()
    result = parse_pdf(snapshot(data, "application/pdf"), profile(), data)
    assert result.observations and all(o.fact_kind != "cutoff" for o in result.observations)


def test_pdf_numeric_ambiguity_preserved_and_continuation_not_assumed():
    data = document(score="1.200", continued=False)
    result = parse_pdf(snapshot(data, "application/pdf"), profile(), data)
    rows = [o for o in result.observations if o.raw_fields.get("kind") == "table_row"]
    assert rows[0].raw_fields["cells"][2]["text"] == "1.200"
    assert rows[2].raw_fields["continuation_of"] is None
    codes = {i.code for i in result.issues}
    assert "ambiguous_numeric_token" in codes
    assert "possible_table_continuation" in codes


def test_pdf_year_only_second_header_row_is_not_data():
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=(600, 800))
    for x in [40, 260, 400, 550]:
        pdf.line(x, 700, x, 580)
    for y in [700, 660, 620, 580]:
        pdf.line(40, y, 550, y)
    for x, y, value in [
        (50, 677, "Program"),
        (270, 677, "Diem trung tuyen"),
        (410, 677, "Diem trung tuyen"),
        (270, 637, "2024"),
        (410, 637, "2025"),
        (50, 597, "TEST A"),
        (270, 597, "24.50"),
        (410, 597, "25.00"),
    ]:
        pdf.drawString(x, y, value)
    pdf.save()
    data = stream.getvalue()
    result = parse_pdf(snapshot(data, "application/pdf"), profile(), data)
    rows = [o for o in result.observations if o.raw_fields.get("kind") == "table_row"]
    assert len(rows) == 1
    assert [h["text"] for h in rows[0].raw_fields["headers"][1]] == ["Diem trung tuyen", "2024"]
    assert rows[0].raw_fields["cells"][1]["text"] == "24.50"
