"""Synthetic HTML only: school/program names do not refer to actual admissions."""

from uuid import uuid4

from services.data.normalization.contract import RawObservation
from services.data.parsers.html import parse_html
from tests.parsers.helpers import profile, snapshot


def raw_row(
    *,
    year="2024",
    method="Thi tốt nghiệp THPT",
    score="24,50",
    campus="BVH",
    form="Chính quy",
    extra="",
    notes="",
):
    body = f"""<article><h1>Thông tin tuyển sinh năm 2026</h1>
    <section><h3>II. Tuyển sinh {form}</h3><h4>Phương thức THPT năm 2026</h4>
    <h5>11. Kết quả hai năm trước</h5><h6>Cơ sở ({campus})</h6>
    <table><thead><tr><th rowspan=3>Mã chương trình/ngành</th><th rowspan=3>Tên chương trình/ngành</th>
    <th>Năm tuyển sinh {year}</th>{extra}</tr><tr><th>Điểm trúng tuyển</th></tr>
    <tr><th>{method}</th></tr></thead><tbody><tr><td>TEST-A</td>
    <td>Ngành mẫu — Tiếng Anh — Chất lượng cao</td><td>{score}</td></tr></tbody></table>{notes}</section></article>""".encode()
    parsed = parse_html(snapshot(body), profile(), body)
    row = next(o for o in parsed.observations if o.raw_fields.get("kind") == "table_row")
    return RawObservation(
        id=uuid4(),
        **row.model_dump(exclude={"fact_kind"}),
        fact_kind="cutoff",
        normalized_fields={},
    )
