"""EduRadar V2 - lam sach & chuan hoa du lieu diem chuan.

Dau vao : data/raw/cutoff/<nam>/<MA>.json   (tu crawler.fetch)
Dau ra  : data/clean/admissions.csv, universities.csv, majors.csv, admission_combos.csv
          data/eduradar.db (SQLite), data/clean/quality_report.md
          data/interim/major_unmatched.csv (ten nganh chua map duoc -> duyet tay)
Sua tay : data/manual/major_map.csv (cot: name_key,major_code) - duoc uu tien hon tu dong.
          major_code trong = chua quyet (bo qua); "-" = bo map tu dong (de lai chua map).

Chay: python -m pipeline.clean
"""

from __future__ import annotations

import difflib
import json
import re
import shutil
import sqlite3
import tempfile
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "cutoff"
CLEAN = ROOT / "data" / "clean"
INTERIM = ROOT / "data" / "interim"
MANUAL = ROOT / "data" / "manual"
DB = ROOT / "data" / "eduradar.db"

# mark_type cua nguon -> (ma chuan, ten hien thi, thang diem mac dinh)
METHODS = {
    1: ("THPT", "Điểm thi THPT", 30),
    2: ("DGNL_HCM", "ĐGNL ĐHQG-HCM (V-ACT)", 1200),
    3: ("HOCBA", "Học bạ", 30),
    4: ("KHAC", "Khác", None),
    5: ("DGNL_HN", "ĐGNL ĐHQG-HN (HSA)", 150),
    6: ("DGTD", "Đánh giá tư duy (TSA)", 100),
    7: ("DGNL_SPT", "ĐGNL ĐHSP HN (SPT)", 30),
    8: ("KHAC", "Khác", None),
    9: ("KHAC", "Khác", None),
    10: ("KETHOP", "Xét tuyển kết hợp", None),
    11: ("UTXT", "Ưu tiên / xét tuyển thẳng", None),
    12: ("CCQT", "Chứng chỉ quốc tế", None),
}

PROGRAM_PATTERNS = [  # (nhan, regex tren ten+ma da bo dau, chu thuong)
    ("TIEN_TIEN", r"tien tien|\bct tt\b|\btt\d"),
    ("CLC", r"chat luong cao|\bclc"),
    ("LIEN_KET", r"lien ket|song bang|\bliên kết|\buc\b|\bphap\b|viet - phap|viet phap|quoc te\)"),
    ("TIENG_ANH", r"tieng anh|bang ta\b|\bta\)|dhnnqt|\bnnqt|day va hoc bang ta|\bep\d"),
    ("PHAN_HIEU", r"phan hieu|co so|campus"),
    ("TAI_NANG", r"tai nang|elitech|honors?"),
]

# tu/cum tu bo khi so khop ten nganh voi danh muc
STRIP_WORDS = re.compile(
    r"\((?:[^()]*)\)|\[(?:[^\[\]]*)\]|"
    r"\b(chuong trinh|ct|tieu chuan|chat luong cao|clc|tien tien|tt|tc|th|dhnnqt|"
    r"lien ket|tich hop|chung chi quoc te|chung chi|dinh huong|theo|nganh|chuyen nganh|"
    r"day va hoc bang tieng anh|bang tieng anh|co so|phan hieu|ha noi|hcm|tp hcm|"
    r"pohe|e[- ]?\w+)\b",
)


def nfc(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = unicodedata.normalize("NFC", str(s)).replace("�", "")
    return re.sub(r"\s+", " ", s).strip()


def unaccent(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def name_key(name: str) -> str:
    k = unaccent(name)
    k = re.sub(r"^\(\d+\)\s*", "", k)
    k = re.sub(r"[–—-]", " ", k)
    k = STRIP_WORDS.sub(" ", k)
    k = re.sub(r"[^a-z0-9 ]", " ", k)
    return re.sub(r"\s+", " ", k).strip()


def program_type(name: str, code: str) -> str:
    s = unaccent(f"{name} {code}")
    for label, pat in PROGRAM_PATTERNS:
        if re.search(pat, s):
            return label
    return "CHUAN"


def infer_scale(score: float, default) -> int | None:
    if default and score <= default:
        return default
    for cap in (30, 40, 100, 150, 1200, 1600):
        if score <= cap:
            return cap
    return None


def split_combos(block) -> list[str]:
    parts = re.split(r"[;,/\s]+", nfc(block).upper())
    return sorted({p for p in parts if re.fullmatch(r"[A-Z]\d{2}", p)})


# ---------------------------------------------------------------- load
def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, schools = [], {}
    for f in sorted(RAW.glob("*/*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        s = p["school"]
        schools[s["code"]] = s
        for r in (p.get("response") or {}).get("data") or []:
            r = dict(r)
            r["uni_code"] = s["code"]
            r["year_file"] = p["year"]
            r["source_url"] = p.get("source_url")
            r["crawled_at"] = p.get("fetched_at")
            rows.append(r)
    return pd.DataFrame(rows), pd.DataFrame(schools.values())


def main() -> None:
    for d in (CLEAN, INTERIM, MANUAL):
        d.mkdir(parents=True, exist_ok=True)
    raw, schools = load_raw()
    if raw.empty:
        raise SystemExit("Chua co du lieu trong data/raw/cutoff - chay crawler.fetch truoc.")
    steps: list[tuple[str, int, str]] = [("Dong tho tu API", len(raw), "")]

    df = raw.copy()
    df["year"] = df["year"].fillna(df["year_file"]).astype(int)

    # 1. diem: ep kieu, bo dong khong co diem
    df["mark"] = pd.to_numeric(df["mark"], errors="coerce")
    n0 = len(df)
    df = df[df["mark"].notna() & (df["mark"] > 0)]
    steps.append(("Bo dong khong co diem / diem <= 0", n0 - len(df), ""))

    # 2. chuan hoa van ban
    df["name"] = df["name"].map(nfc).str.replace(r"^\(\d+\)\s*", "", regex=True)
    df["code"] = df["code"].map(nfc).str.replace(" ", "", regex=False)
    df["note"] = df["introtext"].map(nfc)
    df["sub_method"] = df["sub_mark_type"].map(nfc)
    n0 = len(df)
    df = df[df["name"] != ""]
    steps.append(("Bo dong khong co ten nganh", n0 - len(df), ""))

    # 3. phuong thuc
    mt = pd.to_numeric(df["mark_type"], errors="coerce").fillna(0).astype(int)
    df["method"] = mt.map(lambda m: METHODS.get(m, ("KHAC",))[0])
    df["method_name"] = mt.map(lambda m: METHODS.get(m, (None, "Khác"))[1])
    df["default_scale"] = mt.map(lambda m: METHODS.get(m, (None, None, None))[2])
    # 1 = diem goc cua phuong thuc; moi gia tri khac (0, null, du lieu loi nhu 26) coi la diem quy doi/thuong
    df["is_conv"] = (pd.to_numeric(df["is_converted_score"], errors="coerce") == 1).astype(int)

    # 4. to hop
    df["combos"] = df["block"].map(lambda b: ";".join(split_combos(b)))

    # 5. ghep cap diem goc / diem quy doi (nguon tra 2 dong cho cung 1 nganh)
    key = ["uni_code", "year", "method", "sub_method", "code", "name", "combos", "note"]
    pkey = [k for k in key if k != "note"]
    native = df[df["is_conv"] == 1]
    equiv = df[df["is_conv"] == 0]
    paired_keys = set(map(tuple, native[pkey].astype(str).values))
    eq_key = equiv[pkey].astype(str).apply(tuple, axis=1) if len(equiv) else pd.Series(dtype=object)
    eq_pair = equiv[eq_key.isin(paired_keys)][pkey + ["mark"]].rename(
        columns={"mark": "score_equiv"}
    )
    eq_pair = eq_pair.drop_duplicates(pkey)
    singles = equiv[~eq_key.isin(paired_keys)].copy()
    singles["score_equiv"] = float("nan")
    merged = native.merge(eq_pair, on=pkey, how="left")
    df = pd.concat([d for d in (merged, singles) if len(d)], ignore_index=True)
    steps.append(("Gop cap (diem goc + diem quy doi) thanh 1 dong", len(equiv) - len(singles), ""))
    df["score"] = df["mark"]

    # 6. thang diem + ngoai mien
    df["scale_max"] = [infer_scale(s, d) for s, d in zip(df["score"], df["default_scale"])]
    df["flag"] = ""
    df.loc[df["scale_max"].isna(), "flag"] = "outlier"
    df.loc[
        (df["method"].isin(["THPT", "HOCBA"])) & (df["scale_max"] != 30) & (df["flag"] == ""),
        "flag",
    ] = "thang_khac_30"
    df.loc[(df["method"] == "THPT") & (df["score"] < 12), "flag"] = "diem_thap_bat_thuong"

    # 7. loai trung
    dkey = key + ["score"]
    n0 = len(df)
    df = df.drop_duplicates(dkey)
    steps.append(("Bo dong trung hoan toan", n0 - len(df), ""))
    conflict = df[df.duplicated(key, keep=False)]
    conflict.sort_values(key).to_csv(INTERIM / "conflicts.csv", index=False, encoding="utf-8-sig")
    steps.append(
        ("Trung khoa khac diem (giu ca, xem data/interim/conflicts.csv)", len(conflict), "")
    )

    # 8. loai chuong trinh + ma nganh chuan
    df["program_type"] = [program_type(n, c) for n, c in zip(df["name"], df["code"])]
    df["name_key"] = df["name"].map(name_key)
    m = df["code"].str.extract(r"^(7\d{6})")[0]
    df["major_code"] = m
    df["match_how"] = m.notna().map({True: "ma_7_so", False: ""})

    # danh muc nganh tu chinh du lieu: ma 7 so -> ten pho bien nhat
    base = df[df["major_code"].notna()]
    catalog = {}
    for code, grp in base.groupby("major_code"):
        plain = grp[grp["program_type"] == "CHUAN"]["name"]
        src = plain if len(plain) else grp["name"]
        catalog[code] = Counter(src).most_common(1)[0][0]
    # moi ten (name_key) -> ma xuat hien nhieu nhat (truoc day lay ma gap dau tien -> map sai)
    votes = Counter(zip(base["name_key"], base["major_code"]))
    best: dict[str, tuple[str, int]] = {}
    for (k, code), n in votes.items():
        if k and (k not in best or n > best[k][1]):
            best[k] = (code, n)
    key_to_code: dict[str, str] = {k: c for k, (c, _) in best.items()}
    # ten danh muc chuan -> ma; neu nhieu ma trung ten (VD 7340120 va 7310120 deu la
    # "Kinh doanh quoc te") thi lay ma duoc nhieu dong/truong dung nhat
    code_rows = base["major_code"].value_counts()

    def dominant(pairs) -> dict[str, str]:
        out: dict[str, str] = {}
        for key, code in pairs:
            if key and (key not in out or code_rows.get(code, 0) > code_rows.get(out[key], 0)):
                out[key] = code
        return out

    cat_by_key = dominant((name_key(nm), code) for code, nm in catalog.items())
    key_to_code.update(cat_by_key)

    manual = {}
    mfile = MANUAL / "major_map.csv"
    if mfile.exists():
        mm = pd.read_csv(mfile, dtype=str).dropna()
        manual = dict(zip(mm["name_key"], mm["major_code"]))

    keys_list = list(key_to_code)

    # cum tu ten chuan (giu nguyen tu, chi bo dau) - dung khi khong con cach nao khac
    def lite(x: str) -> str:
        x = re.sub(r"\([^()]*\)", " ", unaccent(x))
        return " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", x)).strip() + " "

    cat_phrases = sorted(
        dominant((lite(nm), code) for code, nm in catalog.items()).items(), key=lambda x: -len(x[0])
    )

    # ten chuan (>= 2 tu) dung o dau ten chuong trinh, VD "kiem toan ..." -> Kiem toan
    cat_prefix = sorted(
        ((ck, code) for ck, code in cat_by_key.items() if len(ck.split()) >= 2),
        key=lambda x: -len(x[0]),
    )

    def prefix_hit(k: str) -> str:
        for ck, code in cat_prefix:
            if k.startswith(ck + " "):
                return code
        return ""

    def contained(name: str) -> str:
        L = lite(name)
        core = name_key(name).split()  # tu con lai sau khi bo tu chung chung (CT, CLC...)
        for ph, code in cat_phrases:
            n = len(ph.split())
            if ph in L and (n >= 2 or len(ph.strip()) >= 6) and n / max(len(core), 1) >= 0.6:
                return code
        return ""

    cache: dict[str, tuple[str, str]] = {}

    def resolve(k: str) -> tuple[str, str]:
        if k in cache:
            return cache[k]
        if k in manual:
            r = ("", "thu_cong_bo") if manual[k] == "-" else (manual[k], "thu_cong")
        elif k in key_to_code:
            r = (key_to_code[k], "ten_khop")
        elif hit := prefix_hit(k):
            r = (hit, "dau_ten_chuan")
        else:
            best = difflib.get_close_matches(k, keys_list, n=1, cutoff=0.9)
            if best:
                r = (key_to_code[best[0]], "ten_gan_dung")
            elif hit := contained(key_name.get(k, k)):
                r = (hit, "chua_ten_chuan")
            else:
                r = ("", "")
        cache[k] = r
        return r

    key_name = dict(zip(df["name_key"], df["name"]))
    need = df["major_code"].isna()
    res = df.loc[need, "name_key"].map(resolve)
    df.loc[need, "major_code"] = res.map(lambda t: t[0] or pd.NA)
    df.loc[need, "match_how"] = res.map(lambda t: t[1])

    unmatched = (
        df[df["major_code"].isna()]
        .groupby("name_key")
        .agg(
            vi_du=("name", "first"),
            so_dong=("name", "size"),
            truong=("uni_code", lambda s: ",".join(sorted(set(s))[:5])),
        )
        .sort_values("so_dong", ascending=False)
        .reset_index()
    )
    unmatched["major_code"] = ""
    unmatched.to_csv(INTERIM / "major_unmatched.csv", index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------ outputs
    df = df.sort_values(["uni_code", "year", "method", "code"]).reset_index(drop=True)
    df["id"] = range(1, len(df) + 1)
    adm_cols = [
        "id",
        "uni_code",
        "year",
        "method",
        "method_name",
        "sub_method",
        "code",
        "major_code",
        "name",
        "program_type",
        "combos",
        "score",
        "scale_max",
        "score_equiv",
        "note",
        "flag",
        "match_how",
        "source_url",
        "crawled_at",
    ]
    adm = df[adm_cols].rename(columns={"code": "program_code", "name": "program_name"})
    adm.to_csv(CLEAN / "admissions.csv", index=False, encoding="utf-8-sig")

    combos = adm[["id", "combos"]].assign(combo=adm["combos"].str.split(";")).explode("combo")
    combos = combos[combos["combo"].fillna("") != ""][["id", "combo"]].rename(
        columns={"id": "admission_id"}
    )
    combos.to_csv(CLEAN / "admission_combos.csv", index=False, encoding="utf-8-sig")

    unis = schools.rename(
        columns={"code": "uni_code", "orther_name": "short_name", "id": "source_id"}
    )
    unis = unis[["uni_code", "name", "short_name", "alias", "source_id", "level"]]
    unis = unis[unis["uni_code"].isin(adm["uni_code"])]
    unis.to_csv(CLEAN / "universities.csv", index=False, encoding="utf-8-sig")

    used = adm["major_code"].dropna().unique()
    majors = pd.DataFrame({"major_code": sorted(used)})
    majors["major_name"] = majors["major_code"].map(lambda c: catalog.get(c, ""))
    majors["field_code"] = majors["major_code"].str[:5]  # nhom nganh cap III (5 so)
    majors.to_csv(CLEAN / "majors.csv", index=False, encoding="utf-8-sig")

    # dung DB o thu muc tam roi chep sang (an toan voi o mang / thu muc dong bo)
    tmp_db = Path(tempfile.gettempdir()) / "eduradar_build.db"
    if tmp_db.exists():
        tmp_db.unlink()
    with sqlite3.connect(tmp_db) as con:
        unis.to_sql("universities", con, index=False)
        majors.to_sql("majors", con, index=False)
        adm.to_sql("admissions", con, index=False)
        combos.to_sql("admission_combos", con, index=False)
        tfile = MANUAL / "tuition.csv"
        if tfile.exists():
            tu = pd.read_csv(tfile, dtype={"uni_code": str})
            tu = tu[tu["uni_code"].isin(unis["uni_code"])]
            tu.rename(columns={"text": "text"}).to_sql("tuition", con, index=False)
            steps.append(("Hoc phi (tu data/manual/tuition.csv)", len(tu), ""))
        con.executescript("""
            CREATE INDEX ix_adm_uni_year ON admissions(uni_code, year);
            CREATE INDEX ix_adm_major_year ON admissions(major_code, year);
            CREATE INDEX ix_adm_method ON admissions(method, year, score);
            CREATE INDEX ix_combo ON admission_combos(combo, admission_id);
        """)
    con.close()
    shutil.copyfile(tmp_db, DB)

    write_report(adm, raw, steps, unmatched, conflict)
    print(f"Xong: {len(adm):,} dong sach -> {CLEAN.relative_to(ROOT)} va {DB.relative_to(ROOT)}")


def md_table(df: pd.DataFrame) -> str:
    """DataFrame -> bang Markdown (khong can thu vien tabulate)."""
    df = df.reset_index()
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    body = [
        "| " + " | ".join(f"{v:,}" if isinstance(v, int) else str(v) for v in row) + " |"
        for row in df.itertuples(index=False)
    ]
    return "\n".join([head, sep, *body])


def write_report(adm, raw, steps, unmatched, conflict) -> None:
    lines = [
        "# Báo cáo chất lượng dữ liệu",
        "",
        f"Tạo lúc {datetime.now():%d/%m/%Y %H:%M}. Nguồn: API diemthi.tuyensinh247.com.",
        "",
        "## Các bước làm sạch",
        "",
        "| Bước | Số dòng |",
        "| --- | ---: |",
    ]
    lines += [f"| {s} | {n:,} |" for s, n, _ in steps]
    lines += [f"| **Bảng sạch cuối cùng** | **{len(adm):,}** |", ""]
    lines += [
        "## Số dòng theo năm × phương thức",
        "",
        adm.pivot_table(
            index="method", columns="year", values="id", aggfunc="count", fill_value=0
        ).pipe(md_table),
        "",
    ]
    mh = adm["match_how"].replace("", "chua_map").value_counts()
    lines += [
        "## Chuẩn hoá mã ngành",
        "",
        "| Cách map | Số dòng | Tỉ lệ |",
        "| --- | ---: | ---: |",
    ]
    lines += [f"| {k} | {v:,} | {v / len(adm):.1%} |" for k, v in mh.items()]
    lines += ["", f"Tên chưa map: {len(unmatched)} (xem `data/interim/major_unmatched.csv`).", ""]
    lines += [
        "## Cờ chất lượng",
        "",
        md_table(adm["flag"].replace("", "ok").value_counts().to_frame("so_dong")),
        "",
    ]
    lines += [f"Dòng trùng khoá khác điểm: {len(conflict)} (`data/interim/conflicts.csv`).", ""]
    lines += [
        "## Tổng quan",
        "",
        f"- Số trường: {adm['uni_code'].nunique()}",
        f"- Số ngành chuẩn (mã 7 số): {adm['major_code'].nunique()}",
        f"- Số tổ hợp khác nhau: {adm['combos'].str.split(';').explode().replace('', pd.NA).nunique()}",
        "- Loại chương trình: "
        + ", ".join(f"{k} {v:,}" for k, v in adm["program_type"].value_counts().items()),
    ]
    (CLEAN / "quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
