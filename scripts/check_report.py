"""Kiem bao cao va tao docs/kiem_tra_bao_cao.md; khong crawl, khong sua du lieu."""

from __future__ import annotations

import csv
import re
import sqlite3
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


def main():
    md = (DOCS / "BAO_CAO_DO_AN.md").read_text(encoding="utf-8")
    checks = []
    evidence = []

    def check(name, ok):
        checks.append((name, bool(ok)))

    def number(label, actual, expected, source):
        check(label, actual == expected)
        evidence.append(
            (label, str(actual), str(expected), source, "Khớp" if actual == expected else "SAI")
        )

    with sqlite3.connect(f"file:{ROOT / 'data/eduradar.db'}?mode=ro", uri=True) as db:

        def scalar(sql):
            return db.execute(sql).fetchone()[0]

        number(
            "Dòng sạch", scalar("SELECT COUNT(*) FROM admissions"), 71011, "DB: admissions COUNT(*)"
        )
        number(
            "Trường có điểm",
            scalar("SELECT COUNT(DISTINCT uni_code) FROM admissions"),
            292,
            "DB: admissions DISTINCT uni_code",
        )
        number(
            "Dòng map ngành",
            scalar("SELECT COUNT(*) FROM admissions WHERE major_code IS NOT NULL"),
            69276,
            "DB: admissions major_code NOT NULL",
        )
        number(
            "Dòng chưa map",
            scalar("SELECT COUNT(*) FROM admissions WHERE major_code IS NULL"),
            1735,
            "DB: admissions major_code NULL",
        )
        number("Mã ngành", scalar("SELECT COUNT(*) FROM majors"), 472, "DB: majors COUNT(*)")
        number(
            "Lượt dòng–tổ hợp",
            scalar("SELECT COUNT(*) FROM admission_combos"),
            264630,
            "DB: admission_combos COUNT(*)",
        )
        number(
            "Tổ hợp đang dùng",
            scalar("SELECT COUNT(DISTINCT combo) FROM admission_combos"),
            385,
            "DB: admission_combos DISTINCT combo",
        )
        number(
            "Hạng VNUR gồm kế thừa",
            scalar("SELECT COUNT(*) FROM universities WHERE vnur_rank IS NOT NULL"),
            149,
            "DB: universities vnur_rank",
        )
        number(
            "Học phí bộ đầu", scalar("SELECT COUNT(*) FROM tuition"), 203, "DB: tuition COUNT(*)"
        )
        for year, n in [(2024, 18590), (2025, 24234), (2026, 28187)]:
            number(
                f"Dòng năm {year}",
                scalar(f"SELECT COUNT(*) FROM admissions WHERE year={year}"),
                n,
                "DB: admissions GROUP BY year",
            )
        for flag, n in [
            ("", 69893),
            ("thang_khac_30", 1113),
            ("diem_thap_bat_thuong", 3),
            ("outlier", 2),
        ]:
            actual = db.execute("SELECT COUNT(*) FROM admissions WHERE flag=?", (flag,)).fetchone()[
                0
            ]
            number(f"Cờ {flag or 'ok'}", actual, n, "DB: admissions GROUP BY flag")
        number(
            "ma_7_so",
            scalar("SELECT COUNT(*) FROM admissions WHERE match_how='ma_7_so'"),
            56418,
            "DB: admissions.match_how",
        )
        number(
            "dau_ten_chuan",
            scalar("SELECT COUNT(*) FROM admissions WHERE match_how='dau_ten_chuan'"),
            1182,
            "DB: admissions.match_how",
        )
    with (ROOT / "data/raw/fetch_log.csv").open(encoding="utf-8-sig", newline="") as f:
        log = list(csv.DictReader(f))
    number("Tác vụ tải điểm", len(log), 921, "data/raw/fetch_log.csv: số dòng")
    number("Dòng thô", sum(int(r["rows"]) for r in log), 76726, "fetch_log.csv: SUM(rows)")
    number("Tác vụ rỗng", sum(int(r["rows"]) == 0 for r in log), 88, "fetch_log.csv: rows=0")
    number("Lỗi tác vụ", sum(bool(r["error"]) for r in log), 0, "fetch_log.csv: error không rỗng")
    with (ROOT / "data/network/summary.csv").open(encoding="utf-8-sig", newline="") as f:
        summary = list(csv.DictReader(f))
    number("Dòng summary", len(summary), 12, "data/network/summary.csv: số dòng")
    for network, field, want in [
        ("g2_uni_uni", "nodes", 249),
        ("g2_uni_uni", "edges", 2531),
        ("g2_uni_uni", "modularity_louvain", 0.4822),
        ("g3_major_major", "nodes", 377),
        ("g3_major_major", "edges", 1412),
        ("g3_major_major", "modularity_louvain", 0.8363),
        ("g4_competition", "edges", 9215),
        ("g4_competition", "spearman_authority_vs_avg_score", 0.2343),
        ("g4_competition", "spearman_pagerank_vs_avg_score", 0.6069),
    ]:
        row = next(r for r in summary if r["network"] == network and r["year"] == "2026")
        number(
            f"{network} 2026 {field}",
            float(row[field]),
            want,
            f"summary.csv: network={network}, year=2026, {field}",
        )
    totals = (ROOT / "docs/TONG_KET_DU_LIEU.md").read_text(encoding="utf-8")
    for label, literal in [
        ("Đề án 267/292", "267/292"),
        ("Học phí 285/292", "285/292"),
        ("Hạng trực tiếp 95", "95 hạng trực tiếp"),
        ("Hạng kế thừa 54", "54 đơn vị kế thừa"),
    ]:
        check(label, literal in totals and literal in md)
        evidence.append(
            (
                label,
                literal,
                literal,
                "docs/TONG_KET_DU_LIEU.md",
                "Khớp" if literal in totals and literal in md else "SAI",
            )
        )
    check(
        "Không còn số dòng cũ", not re.search(r"71[.,]00[89]|71[ _]?00[89]|26 trường học phí", md)
    )
    image_paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
    check("Mọi hình nhúng tồn tại", all((DOCS / p).is_file() for p in image_paths))
    check(
        "Đủ 20 dòng kiểm tra",
        len(re.findall(r"^\| \d+ \| \d+ \| [A-Z0-9]+ \| 202[456] \|", md, re.M)) == 20,
    )
    check(
        "Có bảng đủ 292 trường",
        len(re.findall(r"^\| .+ \([A-Z0-9]+\) \| \d+ \| \d+ \| \d+ \| \d+ \|$", md, re.M)) == 292,
    )
    metric_names = [
        "Degree centrality và Degree distribution",
        "Betweenness centrality",
        "Closeness centrality",
        "Eigenvector centrality",
        "PageRank",
        "HITS",
        "Density",
        "Average shortest path length",
        "Diameter",
        "Clustering coefficient",
        "Modularity",
        "Các độ đo bổ sung",
    ]
    metric_rows = []
    for i, name in enumerate(metric_names, 1):
        match = re.search(rf"^### 3\.2\.{i}\. (.*?)(?=^### |^## |\Z)", md, re.M | re.S)
        block = match.group(0) if match else ""
        flags = [name in block, "**(1)" in block, "$" in block, "| ---" in block, "**(5)" in block]
        check(f"Độ đo {name}: mục/định nghĩa/công thức/bảng/diễn giải", all(flags))
        metric_rows.append((name, f"3.2.{i}", *["Có" if f else "THIẾU" for f in flags[1:]]))
    docx = DOCS / "BAO_CAO_DO_AN.docx"
    if docx.exists():
        with zipfile.ZipFile(docx) as z:
            xml = ET.fromstring(z.read("word/document.xml"))
            instructions = " ".join(e.text or "" for e in xml.findall(".//w:instrText", NS))
            maths = len(xml.findall(".//m:oMath", NS))
            tables = xml.findall(".//w:tbl", NS)
            check("Mục lục tự động TOC", bool(re.search(r"\bTOC\b", instructions)))
            check("Công thức Word OMML", maths >= 30)
            check(
                "Bảng có header lặp", all(t.find(".//w:tblHeader", NS) is not None for t in tables)
            )
            check(
                "Bảng rộng 100%",
                all(
                    t.find("w:tblPr/w:tblW", NS).get("{" + NS["w"] + "}w") == "5000" for t in tables
                ),
            )
            text_runs = [
                r for t in tables for r in t.findall(".//w:r", NS) if r.find("w:t", NS) is not None
            ]
            check(
                "Mọi chữ trong bảng kể cả hyperlink là 9pt",
                all(
                    r.find("w:rPr/w:sz", NS) is not None
                    and r.find("w:rPr/w:sz", NS).get("{" + NS["w"] + "}val") == "18"
                    for r in text_runs
                ),
            )
            check(
                "Phụ lục C khổ ngang",
                any(
                    e.get("{" + NS["w"] + "}orient") == "landscape"
                    for e in xml.findall(".//w:pgSz", NS)
                ),
            )
    else:
        maths, tables = 0, []
        check("Đã xuất DOCX", False)

    def table(headers, rows):
        return "\n".join(
            ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
            + ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
        )

    result = "# Kiểm tra báo cáo đồ án EduRadar\n\nNgày kiểm: 25/10/2026 (UTC+7). Chạy `python scripts/check_report.py` để tái kiểm dữ liệu và cấu trúc.\n\n"
    result += "## 1. Đối chiếu yêu cầu đề bài\n\n"
    result += table(
        ["Yêu cầu", "Mục", "Bằng chứng và kết quả"],
        [
            [
                "(1)",
                "Chương 1",
                "Có bối cảnh, chủ đề, 5 câu hỏi nghiên cứu, phạm vi; trả lời ở Chương 7.",
            ],
            [
                "(2)",
                "2.1–2.6, Phụ lục A–C",
                "Có nguồn, crawl, định nghĩa record, làm sạch/chuẩn hoá, chất lượng; 71.011 > 20.000; Hình2.1–2.4. Thiếu lịch sử URL/ngày truy cập/robots của một số nguồn bổ trợ được ghi rõ, không bịa.",
            ],
            [
                "(3)",
                "3.1–3.4",
                "Có 12 tiểu mục độ đo; bảng năm/top10; công thức, hàm, trọng số và giới hạn liên thông; xem bảng dưới.",
            ],
            [
                "(3')",
                "4.1–4.6",
                "Có Louvain, GN, HITS/PageRank, AA, độ nhạy, ứng dụng; AA23% là 2024→2026, đã thêm hai kiểm chứng năm liền kề.",
            ],
            [
                "(4)",
                "Chương 5",
                "Có mạng, phân bố, top betweenness, scatter, độ nhạy, web tương tác. Hai ảnh Gephi còn để người thực hiện bổ sung theo yêu cầu.",
            ],
            [
                "(5)",
                "Chương 6",
                "URL web thật; 5tab; ảnh1280px,375px; đề án+học phí; kịch bản demo5bước.",
            ],
        ],
    )
    result += "\n\n## 2. Kiểm từng độ đo\n\n" + table(
        ["Độ đo", "Mục", "Định nghĩa", "Công thức", "Số liệu/bảng", "Diễn giải"], metric_rows
    )
    result += "\n\nCác hình phân bố: Hình3.2–3.7; mạng và cộng đồng: Hình5.1–5.2; betweenness: Hình5.3; PageRank: Hình5.4; độ nhạy: Hình5.5–5.6. Các độ đo toàn cục có bảng riêng, không cần thêm một hình lặp lại cùng số liệu.\n"
    result += "\n## 3. Số quan trọng và nguồn đối chiếu\n\n" + table(
        ["Chỉ tiêu", "Đọc lại từ nguồn", "Mốc trong báo cáo", "Nguồn", "Kết quả"], evidence
    )
    result += "\n\nCác bảng top10 được xuất/đối chiếu từ metrics với tên trong DB; bảng292trường, mẫu20dòng và năm×phương thức được dựng từ DB. Tỉ lệ map là độ phủ, chưa phải độ chính xác. Kiểm số không đồng nghĩa kiểm chứng từng thông báo tuyển sinh gốc.\n"
    result += "\n## 4. Kiểm cấu trúc và bản Word\n\n" + table(
        ["Kiểm tra", "Kết quả"], [(k, "Đạt" if ok else "KHÔNG ĐẠT") for k, ok in checks]
    )
    result += f"\n\nCó {len(image_paths)} tham chiếu hình nhúng, {len(tables)} bảng Word và {maths} công thức OMML. Bảng được kẻ ô, 100%vùng chữ, tiêu đề lặp; công thức không phải ảnh. Hai đường dẫn Gephi dự kiến chưa được nhúng nên không gây liên kết ảnh hỏng.\n"
    qa = ROOT / "tmp/report/render_qa.md"
    result += "\n### Kiểm tra hiển thị\n\n" + (
        qa.read_text(encoding="utf-8")
        if qa.exists()
        else "Chưa hoàn tất kiểm tra hiển thị PDF; không coi kiểm XML là kiểm trang in.\n"
    )
    result += "\n## 5. Những chỗ người thực hiện cần tự điền\n\n"
    result += "- Trang bìa: [Họ tên — MSSV], [Lớp], [Giảng viên], [Ngày nộp].\n- Mục2.6.2 và Phụ lụcC: kết quả __/20; để trống toàn bộ cột Đúng/Sai cho đến khi đối chiếu nguồn.\n- Mục5.4: xuất hai hình Gephi G2/G3 theo hướng dẫn, lưu docs/fig/gephi_g2_2026.png và gephi_g3_2026.png rồi thay hai khối đánh dấu, dựng lại Word.\n- Nếu hồ sơ nguồn gốc còn giữ: bổ sung ngày truy cập, URL từng bài đề án/học phí và nội dung robots.txt/Content-Signal lịch sử còn thiếu ở2.1. Các mục này chưa đủ bằng chứng trong nguồn số được phép dùng; không tự điền từ suy đoán.\n"
    result += "\n## 6. Phạm vi thay đổi\n\nKhông crawl, không sửa raw/clean/DB hoặc tính lại đè data/network; chỉ thêm báo cáo, hình và script. Không commit raw, DB, .venv hoặc tmp. Thực nghiệm bổ sung được tính đọc từ DB, không thay bộ summary gốc.\n"
    (DOCS / "kiem_tra_bao_cao.md").write_text(result, encoding="utf-8")
    failures = [k for k, ok in checks if not ok]
    print(
        f"Checks: {len(checks)}; failures: {len(failures)}; figures: {len(image_paths)}; OMML: {maths}"
    )
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
