"""Admission-plan extraction regression: publish structured facts, not source paragraphs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.dean import FIELDS, MAX_BULLET, extract_plan, norm, sentences  # noqa: E402


def check():
    html = """
    <style>BAD STYLE</style><script>BAD SCRIPT</script>
    <h2>Giới thiệu trường</h2><p>DO NOT PUBLISH INTRO</p>
    <h2>Đề án tuyển sinh 2026</h2><p>Tổng chỉ tiêu năm 2026 là 3.000 sinh viên.</p>
    <p>Trường mang đến cơ hội học tập hàng đầu.</p>
    <h2>Phương thức xét tuyển năm 2026</h2>
    <h3>1. Xét kết quả thi THPT</h3><h4>Đối tượng</h4>
    <p>Đối tượng xét tuyển: Thí sinh đã tốt nghiệp THPT năm 2026.</p>
    <h4>Điều kiện</h4><p>Điểm xét tuyển từ 20 điểm, IELTS từ 6.5 trở lên.</p>
    <h4>Quy chế</h4><p>Công thức tính điểm tổ hợp A00:</p><p>Toán x 2 + Lý + Hóa.</p>
    <p>Điểm cộng tối đa 1,5 điểm cho chứng chỉ ngoại ngữ.</p>
    <p>Lưu ý: Thí sinh cần đăng ký trên hệ thống của Bộ.</p>
    <p>Quy định chung: thang điểm 30 cho mọi phương thức.</p>
    <h3>2. Tuyển thẳng</h3><p>Thí sinh đạt giải nhất quốc gia; dành 10% chỉ tiêu.</p>
    <h4>Quy chế</h4><p>Quy định chung: thang điểm 30 cho mọi phương thức.</p>
    <h2>Danh sách ngành đào tạo</h2><p>DO NOT PUBLISH PROGRAMS</p>
    <h2>Thời gian và hồ sơ</h2><p>Đợt 1: Nộp hồ sơ từ 01/06/2026 đến 30/06/2026; Công bố kết quả 15-16/07/2026.</p>
    <ul><li>Bản sao học bạ THPT</li><li>Bản sao căn cước công dân</li></ul>
    """
    data = extract_plan(html)
    assert len(data["methods"]) == 2
    thpt, direct = (m["fields"] for m in data["methods"])
    assert set(thpt) == set(FIELDS)
    assert thpt["audience"] == ["Thí sinh đã tốt nghiệp THPT năm 2026."]
    assert any("IELTS từ 6,5" in s for s in thpt["conditions"]), thpt
    assert thpt["formula"] == ["Công thức tính điểm tổ hợp A00: Toán × 2 + Lý + Hóa."], thpt
    assert thpt["bonus"] == ["Điểm cộng tối đa 1,5 điểm cho chứng chỉ ngoại ngữ."]
    assert thpt["notes"] == ["Thí sinh cần đăng ký trên hệ thống của Bộ."]
    assert direct["quota"] == ["Dành 10% chỉ tiêu."], direct
    # Repeated facts move to the shared block once.
    assert data["common"]["formula"] == ["Quy định chung: thang điểm 30 cho mọi phương thức."]
    assert data["methods"][0]["shared"] and data["methods"][1]["shared"]
    assert data["quota"] == ["Tổng chỉ tiêu năm 2026 là 3.000 sinh viên."]
    assert {"date": "01/06/2026 – 30/06/2026", "event": "Đợt 1: Nộp hồ sơ"} in data["timeline"]
    assert {"date": "15–16/07/2026", "event": "Đợt 1: Công bố kết quả"} in data["timeline"]
    assert data["documents"] == ["Bản sao học bạ THPT", "Bản sao căn cước công dân"]
    assert "DO NOT PUBLISH" not in str(data) and "BAD" not in str(data)
    assert "cơ hội" not in str(data)
    # Normalisation keeps subject-combination codes and dates, drops padded counts.
    assert norm("A00, D01 trong 06 học kỳ, (01) ngày 05-15/12/2025") == (
        "A00, D01 trong 6 học kỳ, (1) ngày 05–15/12/2025"
    )
    assert norm("một (01) trong") == "một trong"
    long = "Thí sinh " + ", ".join(f"điều kiện số {i} rất dài" for i in range(40)) + "."
    assert all(len(s) <= MAX_BULLET + 1 for s, _ in sentences(long))
    from webapp import main

    plans = main.dean_index()
    assert plans["stats"]["universities"] == len(plans["plans"])
    for code in ("BKA", "NTH", "YHB", "DVL"):
        plan = main.university_plan(code)
        assert plan["methods"] and all(set(m["fields"]) == set(FIELDS) for m in plan["methods"])
        assert any(any(m["fields"].values()) for m in plan["methods"]), code
    assert main.university_plan("BVS") is None
    bullets = [
        s
        for v in plans["plans"].values()
        for p in v
        for m in [*p["methods"], {"fields": p["common"]}]
        for items in m["fields"].values()
        for s in items
    ]
    assert max(map(len, bullets)) <= MAX_BULLET + 1
    idx = {u["uni_code"]: u for u in main.search_index()["unis"]}
    assert idx["BKA"]["province"] == "Thành phố Hà Nội"
    assert any(u.get("province_source") == "HOCMAI" for u in idx.values())
    print(f"PASS: structured fields, shared facts, timeline, documents; {len(bullets)} bullets")


if __name__ == "__main__":
    check()
