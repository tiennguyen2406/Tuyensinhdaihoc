"""Extract short admission facts from HOCMAI HTML; never publish article HTML.

Run after crawler.fetch_dean: python -m pipeline.dean
University decisions live in data/manual/dean_map.csv, not generated output.
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/dean"
CLEAN = ROOT / "data/clean/dean.json"
TAXONOMIES = ("nam", "thanh-pho-tax", "nhom-truong", "phuong-thuc-xet-tuyen")
DATE = re.compile(
    r"\b\d{1,2}(?:\s*[-–]\s*\d{1,2})?[/]\d{1,2}(?:/\d{2,4})?\b"
    r"|\b\d{1,2}[-.]\d{1,2}[-.]\d{4}\b"
    r"|\btháng\s+\d{1,2}(?:\s+năm\s+\d{4})?",
    re.I,
)


def text(value) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def key(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    return re.sub(r"\s+", " ", "".join(c for c in value if unicodedata.category(c) != "Mn")).strip()


def unique(items):
    return list(dict.fromkeys(items))


CERTIFICATE = re.compile(
    r"(?<![\w-])(?:IELTS|TOEFL(?:\s+(?:iBT|ITP|PBT))?|TOEIC(?:\s+L&R)?|PTE|"
    r"V-SAT(?:-TNU)?|SAT|ACT|HSA|V-ACT|TSA|VSTEP)(?![\w-])",
    re.I,
)


def certificate_facts(value: str) -> list[str]:
    matches = list(CERTIFICATE.finditer(value))
    out = []
    for i, match in enumerate(matches):
        # A score belongs only to the certificate immediately before it.
        tail = value[match.end() : matches[i + 1].start() if i + 1 < len(matches) else len(value)][
            :120
        ]
        tail = re.split(r"[;\n]|\.(?!\d)", tail, maxsplit=1)[0]
        # Read an immediately attached overall score before looking for a later
        # threshold: "IELTS 6.5 (kỹ năng viết từ 6.0)" means overall 6.5.
        direct = re.match(
            r"\s*(?:\(?Academic\)?\s*)?(?:[:(]\s*)?"
            r"(đạt\s+từ|đạt\s+trên|từ|tối thiểu|trên|≥|>=|>|đạt|:)?\s*"
            r"(\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)",
            tail,
            re.I,
        )
        found = direct or re.search(
            r"(đạt\s+từ|đạt\s+trên|từ|tối thiểu|trên|≥|>=|>|đạt|:)\s*"
            r"(\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)",
            tail,
            re.I,
        )
        if not found:
            continue
        if not direct and re.search(
            r"kỹ năng|kĩ năng|điểm (?:trung bình|xét tuyển)|học bạ|quy đổi|điểm thưởng",
            tail[: found.start()],
            re.I,
        ):
            continue
        raw, op, rest = found[2], key(found[1] or ":"), tail[found.end() :]
        if re.match(r"\s*(?:kỹ năng|kĩ năng|năm|tháng|lần|môn)\b", rest, re.I):
            continue
        name = match[0].upper()
        if name in ("SAT", "TOEIC", "TOEIC L&R", "V-ACT"):
            raw = re.sub(r"(?<=\d)[.,](?=\d{3}(?:\D|$))", "", raw)
        number = float(raw.split("/")[0].replace(",", "."))
        caps = {
            "IELTS": 9,
            "TOEFL IBT": 120,
            "TOEFL": 677,
            "TOEFL ITP": 677,
            "TOEFL PBT": 677,
            "TOEIC": 990,
            "TOEIC L&R": 990,
            "PTE": 90,
            "SAT": 1600,
            "ACT": 36,
            "HSA": 150,
            "TSA": 100,
            "V-ACT": 1200,
        }
        cap = caps.get(name)
        if (cap is not None and not 0 <= number <= cap) or (name == "SAT" and number < 400):
            continue
        operator = (
            ">"
            if "tren" in op or op == ">"
            else "≥"
            if op in ["tu", "dat tu", "toi thieu", "≥", ">="]
            or key(rest[:15]).startswith("tro len")
            else ":"
        )
        separator = ": " if operator == ":" else f" {operator} "
        out.append(f"{name}{separator}{raw.replace(' ', '')}")
    return unique(out)


def short_summary(audience: str, conditions: str, method_name: str = "", rules: str = "") -> str:
    """Write two factual labels from recognized facts, rather than truncating source prose."""
    a = re.sub(r"trung hoc pho thong(?:\s*\(thpt\))?", "thpt", key(audience))
    # Some articles put the main eligibility conditions under H4 "Quy chế".
    # Conversion/bonus tables and program-specific rules are not general entry requirements.
    safe_rules = (
        ""
        if re.search(
            r"quy doi|diem thuong|diem uu tien|diem cong|khuyen khich|chuong trinh|doi voi",
            key(rules),
        )
        else rules
    )
    eligibility = (
        audience
        + " "
        + conditions
        + (" " + safe_rules if not conditions or "xem them" in key(conditions) else "")
    )
    c = re.sub(r"trung hoc pho thong(?:\s*\(thpt\))?", "thpt", key(eligibility))
    people = []
    if re.search(r"(?<!thi )tot nghiep thpt", a):
        people.append("tốt nghiệp THPT" + ("/tương đương" if "tuong duong" in a else ""))
    if "thi tot nghiep thpt" in a or "thi thpt" in a:
        people.append("dự thi THPT")
    if "danh gia tu duy" in a or "dgtd" in a:
        people.append("dự thi ĐGTD")
    if "danh gia nang luc" in a or "dgnl" in a:
        people.append("có kết quả ĐGNL")
    if "hoc sinh gioi" in a or re.search(r"\bhsg\b", a):
        levels = [
            label
            for phrase, label in [("quoc gia", "quốc gia"), ("quoc te", "quốc tế")]
            if phrase in a
        ]
        people.append("diện HSG" + (" " + "/".join(levels) if levels else ""))
    if "olympic" in a:
        people.append("diện Olympic")
    if "khkt" in a or "khoa hoc ky thuat" in a:
        people.append("diện giải KHKT")
    if "nuoc ngoai" in a and not people:
        people.append("có bằng/chương trình nước ngoài")
    if "chung chi" in a or re.search(r"(?<![\w-])(?:SAT|ACT|IB|A-Level)(?![\w-])", audience, re.I):
        people.append("diện chứng chỉ quốc tế")
    if "hoc ba" in a:
        people.append("có kết quả học bạ THPT")
    if "tuyen thang" in a:
        people.append("thuộc diện tuyển thẳng theo quy chế")
    facts = certificate_facts(eligibility)
    for match in re.finditer(
        r"điểm\s+(?:xét tuyển|trung bình|trung bình chung|học bạ)[^;\n]{0,65}?"
        r"(từ|đạt\s*(?:từ\s*)?|tối thiểu|trên|≥|>=|>)\s*(\d+(?:[.,]\d+)?)",
        eligibility,
        re.I,
    ):
        if CERTIFICATE.search(match[0]):
            continue
        preceding = re.split(r"[;\n]|\.(?!\d)", eligibility[: match.start()])[-1][-50:]
        if CERTIFICATE.search(preceding) and not re.search(
            r"học tập|học bạ|lớp\s*\d", match[0], re.I
        ):
            continue
        label = "điểm xét tuyển" if "xét tuyển" in match[0].lower() else "ĐTB"
        operator = ">" if key(match[1]) in ("tren", ">") else "≥"
        facts.append(f"{label} {operator} {match[2]}")
    for phrase, label in [
        ("tot nghiep thpt", "tốt nghiệp THPT"),
        ("so tuyen", "đạt yêu cầu sơ tuyển"),
        ("suc khoe", "đáp ứng yêu cầu sức khỏe"),
        ("nguong diem", "đạt ngưỡng điểm của trường"),
    ]:
        if phrase in c and (
            phrase != "tot nghiep thpt" or re.search(r"(?<!thi )tot nghiep thpt", c)
        ):
            facts.append(label)
    if re.search(r"(?:hoc tap|hoc luc)[^.;]{0,50}\bkha\b", c):
        facts.append("học tập từ Khá (theo diện)")
    if re.search(r"hanh kiem[^.;]{0,50}\bkha\b", c):
        facts.append("hạnh kiểm từ Khá")
    if "giai nhat" in a or "giai nhi" in a or "giai ba" in a:
        facts.append("giải/thành tích theo diện của trường")
    first = (
        "Đối tượng: " + "; ".join(unique(people)[:3])
        if people
        else "Đối tượng: theo diện " + (method_name.lower() or "dự tuyển trong bài gốc")
    )
    second = (
        "Điều kiện theo diện: " + "; ".join(unique(facts))
        if facts
        else "Điều kiện chi tiết: xem bài gốc"
    )
    # A decimal dot is part of a number, not an extra sentence. Do not cut a number/token.
    budget = 298 - len(first) - 2
    if len(second) > budget:
        second = second[: max(0, budget - 1)].rsplit(";", 1)[0].rstrip(" ,;") + "…"
    return f"{first}. {second}."


DOCUMENTS = [
    (r"h[oọ]c b[aạ]", "Học bạ THPT"),
    (
        r"b[aằ]ng t[oố]t nghi[eệ]p|ch[uứ]ng nh[aậ]n t[oố]t nghi[eệ]p",
        "Bằng/giấy chứng nhận tốt nghiệp",
    ),
    (r"c[aă]n c[uướơớ]+c|\bCCCD\b|\bCMND\b", "Căn cước/CCCD/CMND"),
    (r"gi[aấ]y khai sinh", "Giấy khai sinh"),
    (
        r"ch[uứ]ng ch[iỉ].{0,25}(ngo[aạ]i ng[uữ]|ti[eế]ng [Aa]nh|IELTS|qu[oố]c t[eế])",
        "Chứng chỉ ngoại ngữ/quốc tế",
    ),
    (
        r"phi[eế]u.{0,25}(đ[aă]ng k[yý]|d[uự] tuy[eể]n|x[eé]t tuy[eể]n)",
        "Phiếu đăng ký xét tuyển/dự tuyển",
    ),
    (r"gi[aấ]y.{0,25}(k[eế]t qu[aả]|đi[eể]m thi)", "Giấy chứng nhận kết quả thi"),
    (r"minh ch[uứ]ng.{0,20}ưu ti[eê]n|gi[aấ]y.{0,25}ưu ti[eê]n", "Giấy tờ minh chứng ưu tiên"),
    (r"gi[aấ]y.{0,15}s[uứ]c kh[oỏ]e", "Giấy khám sức khỏe"),
    (r"[aả]nh.{0,10}(3x4|4x6|ch[aâ]n dung)", "Ảnh thẻ"),
]


def time_facts(blocks: list[str]) -> tuple[list[str], list[str]]:
    dates, documents, round_label = [], [], ""
    for block in blocks:
        for pattern, label in DOCUMENTS:
            if re.search(pattern, block, re.I):
                documents.append(label)
        for part in re.split(r"[;\n]|(?=Đợt\s+\d+\s*:)", block):
            round_match = re.search(r"[Đđ]ợt\s+(\d+)", part)
            if round_match:
                round_label = f"Đợt {round_match[1]} – "
            found = unique(text(m[0]) for m in DATE.finditer(part))
            if not found:
                continue
            k = key(part)
            event = (
                "đăng ký"
                if "dang ky" in k
                else "nộp hồ sơ"
                if "nop" in k
                else "thi"
                if "thi" in k
                else "mốc thời gian"
            )
            dates.append(f"{round_label}{event}: {', '.join(found)}")
    return unique(dates), unique(documents)


def extract_plan(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["style", "script", "noscript"]):
        element.decompose()
    # Program tables can also appear inside a method's rules, not just their own H2.
    for table in soup.find_all("table"):
        if re.search(r"ma nganh|ten nganh", key(table.get_text(" ", strip=True))):
            table.decompose()
    section, parent_section, detail, current = "", "", "", None
    methods, time_blocks, title_year, methods_year = [], [], None, None
    for element in soup.find_all(["h2", "h3", "h4", "p", "li", "tr"]):
        value = text(element.get_text(" ", strip=True))
        k = key(value)
        if element.name in ("h2", "h3", "h4"):
            if "gioi thieu truong" in k or "danh sach nganh dao tao" in k:
                section, current = "excluded", None
                if element.name == "h2":
                    parent_section = "excluded"
                continue
            if element.name == "h2":
                current, detail = None, ""
                year_match = re.search(r"\b20\d{2}\b", value)
                if "de an tuyen sinh" in k and year_match:
                    title_year = int(year_match[0])
                if "phuong thuc xet tuyen" in k:
                    section = "methods"
                    methods_year = int(year_match[0]) if year_match else None
                elif "thoi gian" in k or "ho so" in k:
                    section = "time"
                else:
                    section = "other"
                parent_section = section
            elif element.name == "h3" and parent_section == "methods":
                section = "methods"
                name = re.sub(r"^\s*\d+[.)]?\s*", "", value)
                name = re.sub(r"\s*[–—-]\s*20\d{2}\s*$", "", name)
                current = {"name": name, "audience": [], "conditions": [], "rules": []}
                methods.append(current)
                detail = "audience"
            elif element.name == "h4" and section == "methods":
                detail = (
                    "audience"
                    if "doi tuong" in k
                    else "conditions"
                    if "dieu kien" in k
                    else "rules"
                    if "quy che" in k
                    else ""
                )
            continue
        if element.find_parent(["li", "p", "tr"]):
            continue
        if section == "methods" and current and detail:
            if "danh sach nganh dao tao" not in k:
                current[detail].append(value)
        elif section == "time":
            time_blocks.append(value)
    dates, docs = time_facts(time_blocks)
    return {
        "year": title_year or methods_year,
        "methods_year": methods_year,
        "methods": [
            {
                "name": m["name"],
                "summary": short_summary(
                    " ".join(m["audience"]),
                    " ".join(m["conditions"]),
                    m["name"],
                    "\n".join(m["rules"]),
                ),
            }
            for m in methods
        ],
        "timeline": dates,
        "documents": docs,
    }


def main():
    with (ROOT / "data/manual/dean_map.csv").open(encoding="utf-8-sig", newline="") as f:
        mappings = {int(r["post_id"]): r for r in csv.DictReader(f)}
    terms = {
        tax: {
            t["id"]: text(t["name"])
            for file in RAW.glob(f"{tax}_*.json")
            for t in json.loads(file.read_text(encoding="utf-8"))
        }
        for tax in TAXONOMIES
    }
    plans = defaultdict(list)
    for file in sorted(RAW.glob("de-an_*.json")):
        for post in json.loads(file.read_text(encoding="utf-8")):
            mapping = mappings[post["id"]]
            code = mapping["uni_code"]
            if not code:
                continue
            data = extract_plan(post["content"]["rendered"])
            tax = {
                name: [terms[name][i] for i in post.get(name, []) if i in terms[name]]
                for name in TAXONOMIES
            }
            if data["year"] is None and tax["nam"]:
                data["year"] = int(tax["nam"][0])
            provinces = [p for p in tax["thanh-pho-tax"] if p != "Tỉnh/thành khác"]
            data.update(
                {
                    "post_id": post["id"],
                    "source_url": post["link"],
                    "modified": post["modified"],
                    "school_name": mapping["hocmai_name"],
                    "province": provinces[0] if len(provinces) == 1 else "Khác",
                    "groups": tax["nhom-truong"],
                    "taxonomy_years": tax["nam"],
                    "method_tags": tax["phuong-thuc-xet-tuyen"],
                }
            )
            plans[code].append(data)
    with sqlite3.connect(ROOT / "data/eduradar.db") as c:
        codes = {r[0] for r in c.execute("SELECT uni_code FROM universities")}
    result = {
        "plans": dict(plans),
        "stats": {"universities": len(codes & plans.keys()), "total_universities": len(codes)},
    }
    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    CLEAN.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Admission plans: {result['stats']['universities']}/{len(codes)} universities -> data/clean/dean.json"
    )


if __name__ == "__main__":
    main()
