"""Extract structured admission facts from HOCMAI HTML; never publish article HTML.

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
    (r"l[eệ] ph[ií]", "Lệ phí xét tuyển"),
]
# Each method is split into labelled groups of one-sentence facts.
FIELDS = ("audience", "conditions", "formula", "bonus", "quota", "notes")
MAX_BULLET = 240
MAX_ITEMS = 12
LEAD = re.compile(
    r"^(?:[–—\-+•*·]+\)?|\(?[ivx]{1,4}\)|\(?[a-gA-G][.)]|\(?\d+(?:\.\d+)+\)?(?=\s)"
    r"|\(?\d+[.)](?=\s)|\(\*+\))\s*"
)
LABEL = re.compile(
    r"^(?:đối tượng(?: xét tuyển| dự tuyển| tuyển sinh)?|điều kiện(?: xét tuyển| dự tuyển)?"
    r"|trong đó|cụ thể|phương thức\s*\d+)\s*:\s*",
    re.I,
)
NOTE = re.compile(r"^(?:lưu ý|chú ý|ghi chú)\s*:?\s*", re.I)
SKIP = re.compile(
    r"danh sách ngành|xem chi tiết|tại đây|xem thêm|bảng quy đổi|cơ hội|minh bạch|đa dạng hóa"
    r"|hàng đầu|uy tín|chào đón|trải nghiệm|tự hào|môi trường học tập",
    re.I,
)
FILLER = [
    r"ngoài các điều kiện cần thiết \(theo các phương thức tuyển sinh\),?\s*",
    r"tính tới thời điểm xét tuyển trước khi công bố kết quả xét tuyển chính thức\s*",
    r",?\s*cụ thể như sau",
]
RULES = [
    ("quota", r"chỉ tiêu"),
    ("bonus", r"điểm (?:cộng|thưởng|ưu tiên|khuyến khích)|cộng (?:thêm )?(?:\d|điểm)|được cộng"),
    (
        "formula",
        r"công thức|=|×|được tính|hệ số|nhân đôi|thang (?:điểm )?\d+|quy đổi|quy về|tổ hợp|tính điểm"
        r"|cách tính|chiếm \d+ ?%|điểm xét tuyển (?:được tính|là)|\bĐXT\b",
    ),
    (
        "conditions",
        r"điều kiện|ngưỡng|tối thiểu|trở lên|đạt từ|\btừ \d|xếp loại|học lực|hạnh kiểm"
        r"|sức khỏe|sơ tuyển|còn hiệu lực|không quá \d",
    ),
]
THRESHOLD = re.compile(
    r"(?:trở lên|đạt từ|tối thiểu|\btừ)\s*\S*\d|\d\S*\s*(?:trở lên|điểm trở)"
    r"|(?:mức|loại|từ)\s+(?:khá|giỏi|tốt|xuất sắc)",
    re.I,
)
HEADER = re.compile(r"^(?:nhóm đối tượng|điều kiện nộp hồ sơ|quy định về)[^.:]{0,70}\.?$", re.I)


def norm(value: str) -> str:
    """Normalise spacing, counts, date ranges, decimals and multiplication signs."""
    s = text(value)
    s = re.sub(r"\bT[Pp]\.\s+", "TP.", s)
    s = re.sub(r"(một|hai|ba)\s*\(0?\d+\)", r"\1", s)
    s = re.sub(r"(?<![\w/.,\-–])0(\d)\b(?![/.,\-–]\d)", r"\1", s)
    s = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", s))
    s = re.sub(r"(\d{1,2})\s*[-–]\s*(\d{1,2}/\d{1,2})", r"\1–\2", s)
    s = re.sub(r"(?<=[\w)\]])\s+[xX]\s+(?=[\w(\[])", " × ", s)
    s = re.sub(r"(?<=\d)\.(?=\d{1,2}\b(?!/))", ",", s)
    return s.strip()


def shorten(s: str) -> str:
    if len(s) <= MAX_BULLET:
        return s
    for pattern in FILLER:
        s = re.sub(pattern, "", s, flags=re.I)
    s = re.sub(r"\s*\([^()]{50,}\)", "", s)
    if len(s) <= MAX_BULLET:
        return s
    # Cat o dau phay/khoang trang ngoai ngoac gan gioi han nhat, khong cat giua so/ngoac.
    depth, comma, space = 0, 0, 0
    for i, ch in enumerate(s[:MAX_BULLET]):
        depth += (ch == "(") - (ch == ")")
        if depth == 0 and ch in ",;" and s[i + 1 : i + 2] == " " and i > 100:
            comma = i
        if depth == 0 and ch == " ":
            space = i
    return s[: comma or space or MAX_BULLET].rstrip(" ,;:(") + "…"


def balance(s: str) -> str:
    """Drop parentheses left unmatched after a paragraph is split into sentences."""
    out, open_at = list(s), []
    for i, ch in enumerate(s):
        if ch == "(":
            open_at.append(i)
        elif ch == ")":
            if open_at:
                open_at.pop()
            else:
                out[i] = ""
    for i in open_at:
        out[i] = ""
    return re.sub(r"\s+", " ", "".join(out)).strip()


def sentences(value: str) -> list[tuple[str, bool]]:
    """Split one source paragraph into short facts; returns (fact, is_note)."""
    out = []
    parts = re.split(
        r"(?<=[.;!?])\s+(?=[A-ZĐÂĂÊÔƠƯÁÀẢÃẠÉÈÍÌÓÒÚÙÝ\d(+–-])|;\s+|\s+(?=\+\)\s)"
        r"|(?<=[:;.])\s+(?=[+–•]\s)",
        norm(value),
    )
    for part in parts:
        s = balance(LEAD.sub("", part.strip()))
        is_note = bool(NOTE.match(s))
        s = LABEL.sub("", NOTE.sub("", s)).strip()
        s = re.sub(r"\s+(?:hoặc|và)\s*[;.]?$", "", s).strip(" ;")
        s = re.sub(r"^(?:hoặc|và)\s+", "", s, flags=re.I)
        if s.endswith(":"):
            s = re.sub(r",?\s*(?:cụ thể\s*)?(?:như sau|cụ thể)\s*:$", "", s).rstrip(" :")
            if len(s) < 40 and not re.search(r"\d", s):
                continue
        if len(s) < 12 or SKIP.search(s) or HEADER.match(s):
            continue
        s = shorten(s[0].upper() + s[1:])
        if not s.endswith(("…", ".", "?", ")")):
            s += "."
        out.append((s, is_note))
    return out


def classify(s: str, heading: str, is_note: bool) -> str:
    if is_note:
        return "notes"
    hits = {field for field, pattern in RULES if re.search(pattern, s, re.I)}
    if "quota" in hits and re.search(r"\d", s):
        return "quota"
    if re.search(r"=|công thức", s, re.I):
        return "formula"
    if "bonus" in hits:
        return "bonus"
    if heading in ("quota", "bonus"):
        return heading
    threshold = THRESHOLD.search(s)
    if heading == "audience":
        return "conditions" if threshold else "audience"
    if heading == "conditions":
        return "formula" if "formula" in hits and not threshold else "conditions"
    for field in ("formula", "conditions"):
        if field in hits:
            return field
    if re.match(r"(?:thí sinh|học sinh|người)\b", s, re.I):
        return "audience"
    return "notes"


EVENTS = [
    ("xac nhan nhap hoc", "Xác nhận nhập học"),
    ("nhap hoc", "Nhập học"),
    ("dang ky", "Đăng ký"),
    ("nop", "Nộp hồ sơ"),
    ("cong bo|thong bao ket qua|ket qua", "Công bố kết quả"),
    ("thi", "Thi"),
    ("xet tuyen", "Xét tuyển"),
]
DOCUMENT_ITEM = re.compile(
    r"^(?:bản sao|bản chính|phiếu|giấy|học bạ|ảnh|chứng chỉ|lệ phí|đơn|sổ|căn cước"
    r"|\d+\s*(?:ảnh|bản|phong bì))",
    re.I,
)


def time_facts(blocks: list[str]) -> tuple[list[dict], list[str]]:
    """Return [{date, event}] and a document list from the timeline/documents section."""
    events, labels, items = [], [], []
    for block in blocks:
        block = norm(block)
        for pattern, label in DOCUMENTS:
            if re.search(pattern, block, re.I):
                labels.append(label)
        item = LEAD.sub("", block)
        if DOCUMENT_ITEM.match(item) and len(item) < 160 and not DATE.search(item):
            items.append(shorten(item.rstrip(" ;.,")))
        round_label = ""
        for part in re.split(r"[;\n]|(?=Đợt\s+\d+\s*:)", block):
            round_match = re.search(r"[Đđ]ợt\s+(\d+)", part)
            if round_match:
                round_label = f"Đợt {round_match[1]}"
            found = unique(text(m[0]) for m in DATE.finditer(part))
            if not found:
                continue
            between = part[part.find(found[0]) : part.rfind(found[-1])] if len(found) == 2 else ""
            date = (" – " if re.search(r"đến|[-–]", between) else ", ").join(found)
            event = re.sub(r"[Đđ]ợt\s+\d+\s*:?", "", DATE.sub(" ", part))
            event = re.sub(r"\([^)]*\)?|\d{1,2}\s*(?:giờ|g|h)\s*\d{0,2}", " ", event)
            event = re.sub(
                r"\b(?:dự kiến|từ ngày|đến ngày|đến hết|từ|đến|ngày|hết|thời gian|trước)\b",
                " ",
                event,
                flags=re.I,
            )
            event = re.sub(r"\d+\s*/\s*\d+(?:/\d+)?|/\s*\d{2,4}|^\s*\d+\s+", " ", event)
            event = re.sub(r"\s+", " ", event).strip(" :,.–-•+*")
            event = re.sub(r"\s*:\s*,?\s*", ": ", event)
            if not 3 <= len(event) <= 60:
                k = key(part)
                event = next((lb for p, lb in EVENTS if re.search(p, k)), "Mốc thời gian")
            event = event[0].upper() + event[1:]
            if round_label:
                event = f"{round_label}: {event}"
            events.append({"date": date, "event": event})
    timeline = list({(e["date"], e["event"]): e for e in events}.values())
    return timeline, unique(items) or unique(labels)


def empty_fields() -> dict:
    return {field: [] for field in FIELDS}


H4_FIELDS = [
    ("doi tuong", "audience"),
    ("dieu kien", "conditions"),
    ("chi tieu", "quota"),
    ("thoi gian|ho so", "time"),
    ("diem cong|uu tien", "bonus"),
]


def extract_plan(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["style", "script", "noscript"]):
        element.decompose()
    # Program tables can also appear inside a method's rules, not just their own H2.
    for table in soup.find_all("table"):
        if re.search(r"ma nganh|ten nganh", key(table.get_text(" ", strip=True))):
            table.decompose()
    section, parent_section, detail, current, lead = "", "", "", None, ""
    methods, time_blocks, intro, title_year, methods_year = [], [], [], None, None
    for element in soup.find_all(["h2", "h3", "h4", "p", "li", "tr"]):
        value = text(element.get_text(" ", strip=True))
        k = key(value)
        if element.name in ("h2", "h3", "h4"):
            lead = ""
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
                current = {"name": name, "fields": empty_fields()}
                methods.append(current)
                detail = "audience"
            elif element.name == "h4" and section == "methods":
                detail = next((f for p, f in H4_FIELDS if re.search(p, k)), "rules")
            continue
        if element.find_parent(["li", "p", "tr"]):
            continue
        if section == "methods" and current and detail:
            if detail == "time":
                time_blocks.append(value)
            elif element.name != "tr":  # bang quy doi/diem thanh phan: khong chep
                if lead and len(value) <= 160:
                    value = f"{lead} {value}"
                lead = value if value.endswith(":") and len(value) <= 100 else ""
                if lead:
                    # "Dieu kien du tuyen:" trong muc Doi tuong -> cac y sau la dieu kien
                    if key(lead).startswith("dieu kien"):
                        detail = "conditions"
                    elif key(lead).startswith("doi tuong"):
                        detail = "audience"
                    continue
                for fact, is_note in sentences(value):
                    current["fields"][classify(fact, detail, is_note)].append(fact)
        elif section == "time":
            time_blocks.append(value)
        elif section == "other" and element.name != "tr":
            intro.append(value)
    for m in methods:
        m["fields"] = {f: unique(v)[:MAX_ITEMS] for f, v in m["fields"].items()}
    # Facts repeated in several methods (VD quy dinh ngoai ngu chung) are shown once.
    seen: dict[tuple, int] = defaultdict(int)
    for m in methods:
        for f, items in m["fields"].items():
            for s in items:
                seen[(f, s)] += 1
    common = empty_fields()
    for m in methods:
        m["shared"] = False
        for f in FIELDS:
            if f == "audience":
                continue
            shared = [s for s in m["fields"][f] if seen[(f, s)] >= 2]
            if shared:
                m["fields"][f] = [s for s in m["fields"][f] if seen[(f, s)] < 2]
                m["shared"] = True
                common[f] = unique(common[f] + shared)
    timeline, docs = time_facts(time_blocks)
    quota = unique(
        s for v in intro for s, _ in sentences(v) if "chỉ tiêu" in s.lower() and re.search(r"\d", s)
    )
    return {
        "year": title_year or methods_year,
        "methods_year": methods_year,
        "quota": quota[:3],
        "methods": methods,
        "common": common,
        "timeline": timeline,
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
