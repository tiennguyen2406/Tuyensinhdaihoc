"""Import hand-researched tuition notes (Markdown) into data/clean/tuition_extra.json.

Run: python -m pipeline.tuition_import
Source: data/manual/hoc_phi_bo_sung_89_truong_20261024.md, one "### NN. MÃ — Tên" section per school.
Amounts keep the source unit (tín chỉ, học kỳ, tháng, năm, toàn khoá); nothing is converted to a year.
Sections the rules cannot read with confidence are listed in data/interim/tuition_extra_review.csv
and keep the source sentence verbatim as their summary.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/manual/hoc_phi_bo_sung_89_truong_20261024.md"
OUT = ROOT / "data/clean/tuition_extra.json"
REVIEW = ROOT / "data/interim/tuition_extra_review.csv"

EVIDENCE = [
    ("chua xac minh muc tien", "unverified"),
    ("ban luu ben thu ba", "official_archived"),
    ("tham khao thu cap", "secondary"),
    ("nguon chinh thuc", "official"),
]
UNITS = [  # (category, regex after the amount, label)
    ("tin_chi", r"/\s*(?:tín chỉ|TC)\b", "đ/tín chỉ"),
    ("hoc_ky", r"/\s*(?:học kỳ\s*I{1,2}\b|học kỳ|kỳ|HK\s*I{1,2}\b|HK\s*1|HKI)", "đ/học kỳ"),
    ("thang", r"(?:/\s*(?:SV|sinh viên)\s*)?/\s*tháng", "đ/tháng"),
    ("nam", r"(?:/\s*(?:SV|sinh viên)\s*)?/\s*năm(?:\s*học)?(?:\s*đầu)?", "đ/năm"),
    ("toan_khoa", r"/\s*(?:toàn khóa|toàn khoá|khóa)", "đ/toàn khoá"),
    ("dot", r"(?:\s*học phí)?\s*/\s*đợt", "đ/đợt"),
]
AMOUNT = r"(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?\s*triệu)"
LOW = r"(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?(?:\s*triệu)?)"  # lower end of 'A–B triệu'
BARE = re.compile(r"(?<![\d/.,])(\d{1,3}(?:\.\d{3}){1,3})(?![\d.]*\s*(?:đ|đồng)?\s*/)")
CURRENCY = r"\s*(?:đ|đồng|VNĐ)?"
RANGE_SEP = r"\s*(?:–|-|đến)\s*"
BARE_TRIEU = re.compile(r"(?<![\d.,])\d+(?:,\d+)?\s*triệu")
HEAD_UNIT = re.compile(r"^Mức(?: công bố)?\s*(?:/\s*|theo\s+)(năm|học kỳ|tháng|tín chỉ)\s*:", re.I)
BARE_RANGE = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d+)?\s*–\s*\d{1,3}(?:,\d+)?(?![\d.,]*\s*(?:triệu|nghìn|đ|%|tín|năm|tháng))")
TECH = re.compile(
    r"đã kiểm chứng|đã đọc|đã xem|đã mở|đã tải|urllib|trang in|dòng \d|hàng \d|PDF trang|"
    r"đọc trực tiếp|bản scan|^nguồn chính thức$|^chưa xác minh$|^nguồn thứ cấp|:\s*$|\(\s*,|"
    r"tên file|thay trạng thái|sửa mapping|^cần (?:giữ|đối chiếu|kiểm)|^mục \d+|không nên dùng",
    re.I,
)


def plain(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def clean(s: str) -> str:
    s = re.sub(r"\*\*", "", s)
    return re.sub(r"\s+", " ", s).strip()


def value(token: str) -> float:
    if "triệu" in token:
        return float(token.replace("triệu", "").strip().replace(",", ".")) * 1e6
    return float(token.replace(".", ""))


def head_unit(fee: str) -> str | None:
    """'Mức/học kỳ: A 18 triệu; …' or 'Mức công bố theo năm: …' -> unit category for amounts written bare."""
    m = HEAD_UNIT.match(fee)
    return {"năm": "nam", "học kỳ": "hoc_ky", "tháng": "thang", "tín chỉ": "tin_chi"}[m[1].lower()] if m else None


def money(text: str, default: str | None = None) -> list[dict]:
    """Amounts with an explicit unit (or the sentence's leading unit); a range 'A–B unit' yields both ends."""
    found = []

    def add(m, cat, label):
        hi, lo = m.group(2), m.group(1)
        if lo and "triệu" in hi and "triệu" not in lo:
            lo += " triệu"
        for tok in (lo, hi):
            if tok:
                found.append({"cat": cat, "label": label, "token": tok.strip(), "pos": m.start(), "end": m.end(),
                              "in_paren": text[: m.start()].count("(") > text[: m.start()].count(")")})

    for cat, unit_re, label in UNITS:
        for m in re.finditer(rf"(?:{LOW}{CURRENCY}{RANGE_SEP})?{AMOUNT}{CURRENCY}\s*{unit_re}", text, re.I):
            add(m, cat, label)
    if default:
        label = next(lb for c, _, lb in UNITS if c == default)
        for m in re.finditer(rf"(?:{LOW}{CURRENCY}{RANGE_SEP})?{AMOUNT}(?![.,]?\d){CURRENCY}", text):
            if not re.match(r"\s*/", text[m.end():]) and not any(f["pos"] <= m.start() < f["end"] for f in found):
                add(m, default, label)
    return sorted(found, key=lambda x: x["pos"])


def year_of(*texts: str) -> tuple[str, int | None]:
    for t in texts:
        m = re.search(r"(20\d\d)\s*[–-]\s*(20\d\d)", t)
        if m:
            return f"{m[1]}–{m[2]}", int(m[1])
    for t in texts:
        m = re.search(r"(Khóa|Tuyển sinh|Đề án(?: tuyển sinh)?|khóa nhập học)\s*(20\d\d)", t, re.I)
        if m:
            return f"{m[1][0].upper()}{m[1][1:]} {m[2]}", int(m[2])
    for t in texts:
        m = re.search(r"\b(20\d\d)\b", t)
        if m:
            return m[1], int(m[1])
    return "", None


def fmt_token(tok: str) -> str:
    return tok if "triệu" in tok else tok


def summary_of(fee: str, pairs: list[dict], flags: set[str]) -> tuple[str | None, list[str]]:
    """One line in the source unit; returns (summary, reasons_if_uncertain)."""
    if not pairs:
        return None, ["không tìm thấy số tiền có đơn vị"]
    primary = pairs[0]["cat"]
    sentence = re.split(r"(?<=\.)\s+(?=[A-ZĐ])", fee)[0]
    unit_spans = [(p["pos"], p["end"]) for p in pairs]
    bare = [m for m in [*BARE.finditer(sentence), *BARE_TRIEU.finditer(sentence)]
            if not any(a <= m.start() < b for a, b in unit_spans)]
    if bare:
        return None, [f"có {len(bare)} số tiền không ghi đơn vị trong câu (VD {bare[0].group(0)})"]
    loose = [m for m in BARE_RANGE.finditer(sentence) if not any(a <= m.start() < b for a, b in unit_spans)]
    if loose:
        return None, [f"có khoảng số không ghi đơn vị (VD {loose[0].group(0)})"]
    others = {p["cat"] for p in pairs if p["cat"] != primary and not p["in_paren"]}
    reasons = [f"nhiều đơn vị ({primary}, {', '.join(sorted(others))})"] if others else []
    same = [p for p in pairs if p["cat"] == primary]
    lo = min(same, key=lambda p: value(p["token"]))
    hi = max(same, key=lambda p: value(p["token"]))
    label = primary_label = same[0]["label"]
    if all("triệu" in p["token"] for p in (lo, hi)):
        label = primary_label.replace("đ/", "triệu đ/")
        lo_t, hi_t = (p["token"].replace("triệu", "").strip() for p in (lo, hi))
    else:
        lo_t, hi_t = lo["token"], hi["token"]
        if "triệu" in lo_t or "triệu" in hi_t:
            reasons.append("trộn đồng và triệu đồng")
    amount = lo_t if lo_t == hi_t else f"{lo_t} – {hi_t}"
    prefix = []
    head = plain(fee[: pairs[0]["pos"] + 40])
    if "du kien" in flags:
        prefix.append("Dự kiến")
    if "tam thu" in plain(fee[max(0, pairs[0]["pos"] - 40) : pairs[0]["pos"] + 60]):
        prefix.append("tạm thu")
    if re.search(r"\btu\s*$|\btu \d", plain(fee[: pairs[0]["pos"] + 3])) or head.strip().startswith("tu "):
        prefix.append("từ")
    if re.search(r"khoang\s*$", plain(fee[max(0, pairs[0]["pos"] - 12) : pairs[0]["pos"]])):
        prefix.append("khoảng")
    text = " ".join(prefix + [f"{amount} {label}"]).strip()
    return text[0].upper() + text[1:], reasons


def table_items(block: str) -> list[dict]:
    rows = [r for r in block.splitlines() if r.startswith("|") and not re.match(r"\|\s*-", r)]
    if len(rows) < 2:
        return []
    head = [c.strip() for c in rows[0].strip("|").split("|")]
    unit = "đ/tín chỉ" if "tín chỉ" in rows[0] else "đ"
    items = []
    for r in rows[1:]:
        cells = [c.strip() for c in r.strip("|").split("|")]
        item = {"name": cells[0], "amount": cells[1], "unit": unit}
        if len(cells) > 2 and len(head) > 2:
            item["extra"] = f"{head[2]}: {cells[2]}"
        items.append(item)
    return items


def prose_items(fee: str, unit: str | None = None) -> tuple[list[dict], bool]:
    """'Ngành A 350.000đ/tín chỉ; Ngành B 370.000đ/tín chỉ' -> items. Returns (items, clean_split)."""
    first = HEAD_UNIT.sub("", re.split(r"\.\s+(?=[A-ZĐÂƠƯ])", fee)[0]).strip()
    segs = [s.strip() for s in re.split(r";\s*|\.\s+(?=[A-ZĐ][^.]{0,60}\d)", first) if s.strip()]
    items, ok = [], True
    for seg in segs:
        pairs = money(seg, unit)
        bare = re.findall(AMOUNT, seg)
        if not pairs:
            if bare:
                ok = False
            continue
        p = pairs[0]
        name = clean(seg[: p["pos"]]).rstrip(" :–-(").removesuffix(" nhóm")
        name = re.sub(r"^(?:Mức[^:]*:|Ví dụ[^:]*:|\d{4}–\d{4}[^:]*:|HKI[^:]*:|Áp dụng[^:]*:)\s*", "", name)
        if not name or len(name) > 160:
            ok = False
            continue
        amount = p["token"] if len([q for q in pairs if q["cat"] == p["cat"]]) == 1 else " / ".join(
            q["token"] for q in pairs if q["cat"] == p["cat"])
        items.append({"name": name, "amount": amount, "unit": p["label"]})
    return (items if len(items) >= 2 else []), ok


def section(text: str, label: str) -> str:
    m = re.search(rf"\*\*{label}:\*\*\s*(.*?)(?=\n\*\*[^*]+:\*\*|\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def notes_of(limit: str, fee: str) -> str:
    out = []
    for s in re.split(r"(?<=[.;])\s+|\s+(?=Không )", clean(limit) + " " + " ".join(
            s for s in re.split(r"(?<=\.)\s+", clean(fee))[1:] if not money(s))):
        s = s.strip(" .;")
        if len(s) < 12 or TECH.search(s) or s.lower().startswith(("nguồn", "ví dụ")):
            continue
        out.append(s[0].upper() + s[1:])
    return ". ".join(dict.fromkeys(out))[:420] + ("." if out else "")


def parse() -> tuple[list[dict], list[dict]]:
    md = SOURCE.read_text(encoding="utf-8")
    parts = re.split(r"^### (\d{2})\. ([A-Z0-9]{3}) — (.+)$", md, flags=re.M)
    schools, review = [], []
    for i in range(1, len(parts), 4):
        num, code, name, body = parts[i], parts[i + 1], clean(parts[i + 2]), parts[i + 3]
        body = body.split("\n## ")[0]
        scope_raw = clean(section(body, "Năm và phạm vi")).rstrip(".")
        fee_block = section(body, "Mức học phí")
        fee = clean(re.sub(r"^\|.*$", "", fee_block, flags=re.M))
        evidence_raw = clean(section(body, "Cấp bằng chứng"))
        evidence = next((e for k, e in EVIDENCE if k in plain(evidence_raw)), None)
        limit = clean(section(body, "Giới hạn/ghi chú"))
        sources = re.findall(r"\]\((https?://[^)\s]+)\)", section(body, "Nguồn"))
        reasons, minor = [], []
        if not evidence:
            reasons.append(f"không nhận ra cấp bằng chứng: {evidence_raw}")
        if scope_raw.lower().startswith("theo nội dung"):
            m = re.match(r"([^:]{4,90}):", fee)
            scope = m.group(1).strip() if m else ""
            if not scope:
                reasons.append("phạm vi nằm trong đoạn mức học phí, không tách được")
        else:
            scope = scope_raw
        school_year, start = year_of(scope, fee)
        if not school_year:
            reasons.append("không xác định được năm học")
        all_text = plain(" ".join([scope_raw, fee, limit]))
        unit = head_unit(fee)
        pairs = money(fee, unit)
        flags = set()
        for cat in {p["cat"] for p in pairs}:
            flags.add({"tin_chi": "theo_tin_chi", "hoc_ky": "theo_hoc_ky", "thang": "theo_thang",
                       "toan_khoa": "toan_khoa", "dot": "theo_hoc_ky", "nam": ""}[cat])
        flags.discard("")
        if start is not None and start < 2025:
            flags.add("nam_cu")
        if "du kien" in all_text:
            flags.add("du_kien")
        if "tam thu" in all_text:
            flags.add("tam_thu")
        if re.search(r"trung binh|binh quan", plain(fee)):
            flags.add("trung_binh")
        if re.search(r"giam \d+%|hoc bong|uu dai|da tru", plain(fee)):
            flags.add("co_uu_dai")
        only = None
        m = re.search(r"(?:riêng|chỉ (?:cho|có|xác minh được)[^,.;]*?)\s+ngành\s+([^,.;]+)", scope_raw + ". " + fee, re.I) \
            or re.search(r"^Riêng ([^:]+?)(?: chính quy)?:", fee) \
            or re.search(r",\s*ngành\s+([A-ZĐ][^,.;]+)$", scope_raw)
        if m:
            only = re.sub(r"\s+trong đề án\s*\d*$", "", clean(m.group(1)))
            flags.add("chi_mot_nganh")
            if only.lower() in ("này", "đó"):
                only = None
                reasons.append("chỉ có một số ngành nhưng không tách được tên ngành")
        if evidence == "unverified":
            summary, items = None, []
            flags.clear()
        else:
            summary, why = summary_of(fee, pairs, flags)
            reasons += why
            if reasons:
                summary = re.split(r"(?<=\.)\s+(?=[A-ZĐ])", fee)[0][:230]
            items = table_items(fee_block)
            if not items:
                items, ok = prose_items(fee, unit)
                if not ok:  # summary is still sure; only the per-major table is dropped
                    items = []
                    minor.append("không tách được bảng theo ngành (bỏ bảng)")
        entry = {
            "uni_code": code,
            "name": name,
            "school_year": school_year,
            "year_start": start,
            "scope": scope,
            "summary": summary,
            "items": items,
            "flags": sorted(flags),
            "only_major": only,
            "evidence": evidence,
            "note": notes_of(limit, fee),
            "sources": sources,
            "auto_ok": not reasons,
        }
        schools.append(entry)
        if reasons or minor:
            review.append({"stt": num, "uni_code": code, "level": "xem tay" if reasons else "nhỏ",
                           "reasons": "; ".join(reasons + minor), "summary_used": summary or ""})
    return schools, review


def main():
    schools, review = parse()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": SOURCE.name, "schools": schools}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, ["stt", "uni_code", "level", "reasons", "summary_used"])
        w.writeheader()
        w.writerows(review)
    ev = {}
    for s in schools:
        ev[s["evidence"]] = ev.get(s["evidence"], 0) + 1
    hard = sum(r["level"] == "xem tay" for r in review)
    print(f"Tuition extra: {len(schools)} schools {ev}; {hard} need manual review, "
          f"{len(review) - hard} minor -> {REVIEW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
