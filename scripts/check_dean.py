"""Admission-plan extraction regression: publish facts, not source paragraphs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.dean import certificate_facts, extract_plan, short_summary  # noqa: E402


def check():
    html = """
    <style>BAD STYLE</style><script>BAD SCRIPT</script>
    <h2>Giới thiệu trường</h2><p>DO NOT PUBLISH INTRO</p>
    <h2>Phương thức xét tuyển năm 2026</h2>
    <h3>1. Xét kết quả thi THPT</h3><h4>Đối tượng</h4>
    <p>Thí sinh đã tốt nghiệp THPT năm 2026.</p><h4>Điều kiện</h4>
    <p>Điểm xét tuyển từ 20 điểm, IELTS từ 6.5.</p>
    <h3>2. Tuyển thẳng</h3><p>Thí sinh đạt giải nhất quốc gia.</p>
    <h2>Danh sách ngành đào tạo</h2><p>DO NOT PUBLISH PROGRAMS</p>
    <h2>Thời gian và hồ sơ</h2><p>Nộp hồ sơ từ 01/06/2026 đến 30/06/2026.</p>
    <ul><li>Học bạ THPT</li><li>Bản sao căn cước công dân</li></ul>
    """
    data = extract_plan(html)
    assert len(data["methods"]) == 2
    assert "20" in data["methods"][0]["summary"]
    assert "6.5" in data["methods"][0]["summary"]
    assert all(len(m["summary"]) <= 300 for m in data["methods"])
    assert any("01/06/2026" in s and "30/06/2026" in s for s in data["timeline"])
    assert any("Học bạ" in s for s in data["documents"])
    assert "DO NOT PUBLISH" not in str(data) and "BAD" not in str(data)
    assert "IELTS > 6.5" in short_summary("", "IELTS trên 6.5")
    assert certificate_facts("IELTS 5,5 trở lên hoặc TOEFL iBT từ 55") == [
        "IELTS ≥ 5,5",
        "TOEFL IBT ≥ 55",
    ]
    assert certificate_facts("IELTS >5.5 / TOEFL >46 / TOEIC L&R >=785") == [
        "IELTS > 5.5",
        "TOEFL > 46",
        "TOEIC L&R ≥ 785",
    ]
    assert certificate_facts("V-SAT từ 300 điểm") == ["V-SAT ≥ 300"]
    assert certificate_facts("V-SAT-TNU năm 2025 đạt từ 225/450 điểm") == [
        "V-SAT-TNU ≥ 225/450",
    ]
    assert certificate_facts("IELTS 6.5 (kỹ năng viết từ 6.0)") == ["IELTS: 6.5"]
    assert certificate_facts("IELTS Academic 6.0, TOEFL iBT: 79 (viết từ 21)") == [
        "IELTS: 6.0",
        "TOEFL IBT: 79",
    ]
    assert certificate_facts("SAT từ 1.068") == ["SAT ≥ 1068"]
    assert certificate_facts("TOEIC (4 kỹ năng: L&R600,S130&W130)") == []
    assert certificate_facts("IELTS (2 năm)") == []
    assert "SAT" not in short_summary("", "", rules="Điểm khuyến khích\nSAT từ 1068")
    assert "diện chứng chỉ quốc tế" not in short_summary("Có kết quả V-SAT", "")
    assert "IELTS" not in short_summary("", "IELTS từ 1530")
    assert "ĐTB" not in short_summary("", "Điểm trung bình và IELTS từ 6.5")
    assert "ĐTB" not in short_summary("", "Chứng chỉ ACT có điểm trung bình từ 25 trở lên")
    assert "ĐTB > 8" in short_summary("", "Điểm trung bình trên 8")
    assert "tốt nghiệp THPT" not in short_summary("Dự kỳ thi tốt nghiệp THPT", "")
    assert "Đối tượng: tốt nghiệp THPT" in short_summary(
        "Đã tốt nghiệp trung học phổ thông (THPT) Việt Nam hoặc bằng nước ngoài tương đương", ""
    )
    nested = extract_plan(
        "<h2>Phương thức xét tuyển năm 2026</h2><h3>1. A</h3><h4>Danh sách ngành đào tạo</h4><p>FORBIDDEN</p><h3>2. B</h3><h4>Quy chế</h4><p>IELTS từ 6.5</p>"
    )
    assert len(nested["methods"]) == 2 and "6.5" in nested["methods"][1]["summary"]
    from webapp import main

    plans = main.dean_index()
    assert plans["stats"]["universities"] == len(plans["plans"])
    assert main.university_plan("BKA")["methods"]
    assert main.university_plan("NTH")["methods"]
    assert main.university_plan("BVS") is None
    assert all(
        len(m["summary"]) <= 300 for v in plans["plans"].values() for p in v for m in p["methods"]
    )
    idx = {u["uni_code"]: u for u in main.search_index()["unis"]}
    assert idx["BKA"]["province"] == "Thành phố Hà Nội"
    assert any(u.get("province_source") == "HOCMAI" for u in idx.values())
    print("PASS: heading boundaries, short facts, dates, documents, excluded sections")


if __name__ == "__main__":
    check()
