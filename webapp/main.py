"""EduRadar V2 - web tra cuu diem chuan + tu van + mang SNA.

Chay (PowerShell, thu muc DiemThiDaiHoc):
    .venv\\Scripts\\python.exe -m uvicorn webapp.main:app --reload
Mo http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import re
import sqlite3
import traceback
import unicodedata
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "eduradar.db"
NETWORK_DIR = ROOT / "data" / "network"
STATIC = Path(__file__).resolve().parent / "static"
METHOD_ORDER = [
    "THPT",
    "HOCBA",
    "DGNL_HCM",
    "DGNL_HN",
    "DGTD",
    "DGNL_SPT",
    "KETHOP",
    "CCQT",
    "UTXT",
    "KHAC",
]

app = FastAPI(title="EduRadar", version="2.0")


@app.middleware("http")
async def no_cache(request, call_next):  # luon lay ban moi nhat cua giao dien khi dang phat trien
    resp = await call_next(request)
    if not request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.exception_handler(Exception)
async def show_error(request, exc):  # chay o may ca nhan -> hien loi de sua nhanh
    return JSONResponse(
        {"detail": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()[-1500:]},
        status_code=500,
    )


def con() -> sqlite3.Connection:
    if not DB.exists():
        raise HTTPException(503, "Chưa có dữ liệu: chạy python -m pipeline.clean")
    c = sqlite3.connect(
        DB.resolve().as_uri() + "?mode=ro&immutable=1", uri=True, check_same_thread=False
    )
    c.row_factory = sqlite3.Row
    return c


def unaccent(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").replace("đ", "d").replace("Đ", "D"))
    return (
        re.sub(r"\s+", " ", "".join(ch for ch in s if unicodedata.category(ch) != "Mn"))
        .lower()
        .strip()
    )


@lru_cache(maxsize=1)
def dean_index() -> dict:
    path = ROOT / "data/clean/dean.json"
    return (
        json.loads(path.read_text(encoding="utf-8"))
        if path.exists()
        else {"plans": {}, "stats": {}}
    )


def university_plan(code: str, year: int = 9999):
    plans = dean_index()["plans"].get(code, [])
    candidates = [p for p in plans if p["year"] is not None and p["year"] <= year]
    return max(candidates or plans, key=lambda p: (p["year"] or 0, p["modified"]), default=None)


def university_info(row: dict) -> dict:
    if row["province"] == "Khác":
        plan = university_plan(row["uni_code"])
        if plan and plan["province"] != "Khác":
            row["province"] = plan["province"]
            row["province_source"] = "HOCMAI"
    return row


@lru_cache(maxsize=1)
def search_index() -> dict:
    c = con()
    unis = [
        dict(r)
        for r in c.execute(
            "SELECT u.*, COUNT(a.id) AS n_rows, MIN(a.year) first_year, MAX(a.year) latest_year "
            "FROM universities u "
            "JOIN admissions a ON a.uni_code = u.uni_code GROUP BY u.uni_code"
        )
    ]
    majors = [
        dict(r)
        for r in c.execute(
            "SELECT m.major_code, m.major_name, COUNT(DISTINCT a.uni_code) AS n_unis FROM majors m "
            "JOIN admissions a ON a.major_code = m.major_code GROUP BY m.major_code"
        )
    ]
    # ten chuong trinh goc chua map ma nganh -> van tim duoc trong o tim nganh
    programs = [
        dict(r)
        for r in c.execute(
            "SELECT program_name, COUNT(DISTINCT uni_code) AS n_unis, COUNT(*) AS n_rows "
            "FROM admissions WHERE major_code IS NULL GROUP BY program_name"
        )
    ]
    for u in unis:
        university_info(u)
        latest = c.execute(
            "SELECT COUNT(DISTINCT program_code), COUNT(DISTINCT method) FROM admissions "
            "WHERE uni_code=? AND year=?",
            (u["uni_code"], u["latest_year"]),
        ).fetchone()
        u["n_programs"], u["n_methods"] = latest
        u["_k"] = unaccent(f"{u['name']} {u['short_name'] or ''} {u['uni_code']}")
    for m in majors:
        m["_k"] = unaccent(f"{m['major_name']} {m['major_code']}")
    for p in programs:
        p["_k"] = unaccent(p["program_name"])
        p["kind"] = "program"
    return {"unis": unis, "majors": majors, "programs": programs}


def rank(items: list[dict], q: str, limit: int) -> list[dict]:
    words = unaccent(q).split()
    hits = [i for i in items if all(w in i["_k"] for w in words)]
    hits.sort(
        key=lambda i: (not i["_k"].startswith(unaccent(q)), -i.get("n_rows", i.get("n_unis", 0)))
    )
    return [{k: v for k, v in i.items() if k != "_k"} for i in hits[:limit]]


@app.get("/api/search-index")
def browser_search_index():
    return search_index()


@app.get("/api/coverage")
def coverage():
    c = con()
    years = meta()["years"]
    counts = {
        (r[0], r[1]): r[2]
        for r in c.execute(
            "SELECT uni_code, year, COUNT(*) FROM admissions GROUP BY uni_code, year"
        )
    }
    unis = [
        university_info(dict(r)) for r in c.execute("SELECT * FROM universities ORDER BY uni_code")
    ]
    for u in unis:
        u["counts"] = {str(y): counts.get((u["uni_code"], y), 0) for y in years}
    source = ROOT / "data/raw/schools.json"
    schools = json.loads(source.read_text(encoding="utf-8")) if source.exists() else []
    codes = {u["uni_code"] for u in unis}
    missing = [
        {"uni_code": s["code"], "name": s["name"]}
        for s in schools
        if s.get("level") == 2 and s["code"] not in codes
    ]
    dates = c.execute("SELECT MIN(crawled_at), MAX(crawled_at) FROM admissions").fetchone()
    return {
        "years": years,
        "universities": unis,
        "missing": missing,
        "collected_from": dates[0],
        "collected_to": dates[1],
        "source_url": "https://diemthi.tuyensinh247.com",
    }


def method_sort(m: str) -> int:
    return METHOD_ORDER.index(m) if m in METHOD_ORDER else 99


def vnur_sort_key(row: dict):
    return (
        row["vnur_rank"] is None,
        row["vnur_rank"] or 0,
        bool(row["vnur_parent"]),
        -row["score"],
    )


@app.get("/api/meta")
def meta():
    c = con()
    years = [r[0] for r in c.execute("SELECT DISTINCT year FROM admissions ORDER BY year DESC")]
    methods = [
        dict(r)
        for r in c.execute(
            "SELECT method, method_name, COUNT(*) n FROM admissions GROUP BY method, method_name"
        )
    ]
    methods.sort(key=lambda m: method_sort(m["method"]))
    combos = [
        r[0]
        for r in c.execute(
            "SELECT combo FROM admission_combos GROUP BY combo HAVING COUNT(*) >= 5 ORDER BY combo"
        )
    ]
    stats = dict(
        c.execute(
            "SELECT COUNT(*) rows, COUNT(DISTINCT uni_code) unis, "
            "COUNT(DISTINCT major_code) majors FROM admissions"
        ).fetchone()
    )
    subjects = dict(c.execute("SELECT combo, subjects FROM combos ORDER BY combo"))
    stats["ranked_unis"] = c.execute(
        "SELECT COUNT(*) FROM universities WHERE vnur_rank IS NOT NULL"
    ).fetchone()[0]
    stats["inherited_unis"] = c.execute(
        "SELECT COUNT(*) FROM universities WHERE vnur_parent != ''"
    ).fetchone()[0]
    stats["dean_unis"] = dean_index()["stats"].get("universities", 0)
    return {
        "years": years,
        "methods": methods,
        "combos": sorted(set(combos) | subjects.keys()),
        "combo_subjects": subjects,
        "stats": stats,
        "ranking_source": {"name": "VNUR 2026", "url": "https://vnur.vn/bang-xep-hang/"},
    }


@app.get("/api/universities")
def universities(q: str = "", limit: int = Query(15, le=50)):
    return rank(search_index()["unis"], q, limit) if q.strip() else []


@app.get("/api/majors")
def majors(q: str = "", limit: int = Query(15, le=50)):
    """Nganh chuan truoc, sau do toi da 5 ten chuong trinh goc chua map (kind=program)."""
    if not q.strip():
        return []
    idx = search_index()
    found = rank(idx["majors"], q, limit)
    return found + rank(idx["programs"], q, min(5, limit) if found else limit)


@app.get("/api/universities/{code}/scores")
def university_scores(code: str, year: int):
    c = con()
    uni = c.execute("SELECT * FROM universities WHERE uni_code = ?", (code.upper(),)).fetchone()
    if not uni:
        raise HTTPException(404, "Không tìm thấy trường")
    rows = [
        dict(r)
        for r in c.execute(
            "SELECT * FROM admissions WHERE uni_code = ? AND year = ? ORDER BY program_code",
            (uni["uni_code"], year),
        )
    ]
    methods = sorted({r["method"] for r in rows}, key=method_sort)
    names = {r["method"]: r["method_name"] for r in rows}
    table: "OrderedDict[tuple, dict]" = OrderedDict()
    # dong THPT/hoc ba tao hang (moi to hop 1 hang); phuong thuc khac gan vao hang dau cua chuong trinh
    for r in sorted(rows, key=lambda r: (method_sort(r["method"]), r["program_code"])):
        prog = (r["program_code"], r["program_name"])
        if r["method"] in ("THPT", "HOCBA"):
            k = prog + (r["combos"],)
            if k not in table:
                first = next(
                    (
                        kk
                        for kk in table
                        if kk[:2] == prog and r["method"] not in table[kk]["scores"]
                    ),
                    None,
                )
                k = first or k
        else:
            k = next((kk for kk in table if kk[:2] == prog), prog + ("",))
        row = table.setdefault(
            k,
            {
                "program_code": r["program_code"],
                "program_name": r["program_name"],
                "major_code": r["major_code"],
                "program_type": r["program_type"],
                "combos": r["combos"] if r["method"] in ("THPT", "HOCBA") else "",
                "scores": {},
                "notes": [],
            },
        )
        if not row["combos"] and r["method"] in ("THPT", "HOCBA"):
            row["combos"] = r["combos"]
        cell = {"score": r["score"], "scale": r["scale_max"], "equiv": r["score_equiv"]}
        if r["method"] in row["scores"]:  # nhieu dong cung phuong thuc (VD ket hop nhieu dien)
            row["scores"].setdefault(r["method"] + "_more", []).append(cell)
        else:
            row["scores"][r["method"]] = cell
        if r["note"]:
            row["notes"].append(r["note"])
    for row in table.values():
        row["notes"] = sorted(set(row["notes"]))[:3]
    years = [
        x[0]
        for x in c.execute(
            "SELECT DISTINCT year FROM admissions WHERE uni_code=? ORDER BY year DESC",
            (uni["uni_code"],),
        )
    ]
    tuition = None
    try:
        t = c.execute(
            "SELECT * FROM tuition WHERE uni_code=? AND year<=? ORDER BY year DESC LIMIT 1",
            (uni["uni_code"], year),
        ).fetchone()
        tuition = dict(t) if t else None
    except sqlite3.OperationalError:
        pass
    return {
        "university": university_info(dict(uni)),
        "year": year,
        "years": years,
        "methods": [{"method": m, "method_name": names[m]} for m in methods],
        "rows": list(table.values()),
        "tuition": tuition,
        "source_url": rows[0]["source_url"] if rows else None,
        "dean": university_plan(uni["uni_code"], year),
    }


def scores_where(c: sqlite3.Connection, where: str, args: list, method: str) -> list[dict]:
    sql = (
        "SELECT a.*, u.name AS uni_name, u.short_name FROM admissions a "
        f"JOIN universities u ON u.uni_code = a.uni_code WHERE {where}"
    )
    if method:
        sql += " AND a.method = ?"
        args = args + [method]
    rows = [dict(r) for r in c.execute(sql, args)]
    rows.sort(key=lambda r: (method_sort(r["method"]), -(r["score"] or 0)))
    return rows


@app.get("/api/majors/{major_code}/scores")
def major_scores(major_code: str, year: int, method: str = ""):
    c = con()
    m = c.execute("SELECT * FROM majors WHERE major_code = ?", (major_code,)).fetchone()
    if not m:
        raise HTTPException(404, "Không tìm thấy ngành")
    rows = scores_where(c, "a.major_code = ? AND a.year = ?", [major_code, year], method)
    return {"major": dict(m), "year": year, "rows": rows}


@app.get("/api/programs/scores")
def program_scores(name: str, year: int, method: str = ""):
    """Diem theo ten chuong trinh goc (chi cac dong chua map ma nganh)."""
    c = con()
    where = "a.major_code IS NULL AND a.program_name = ?"
    years = [
        r[0]
        for r in c.execute(
            f"SELECT DISTINCT year FROM admissions a WHERE {where} ORDER BY year DESC", (name,)
        )
    ]
    if not years:
        raise HTTPException(404, "Không tìm thấy chương trình chưa map với tên này")
    rows = scores_where(c, where + " AND a.year = ?", [name, year], method)
    major = {"major_code": "", "major_name": name, "unmapped": True}
    return {"major": major, "year": year, "years": years, "rows": rows}


@app.get("/api/majors/{major_code}/similar")
def similar_majors(major_code: str, year: int):
    """Nganh lien ket manh nhat voi nganh nay trong mang G3 (Jaccard tap truong)."""
    f = NETWORK_DIR / f"similar_majors_{year}.json"
    if not f.exists():
        return []
    data = json.loads(f.read_text(encoding="utf-8"))
    return [
        {"major_code": c, "major_name": n, "jaccard": w} for c, n, w in data.get(major_code, [])
    ]


@app.get("/api/advice")
def advice(
    method: str,
    score: float,
    combo: str = "",
    year: int | None = None,
    margin: float | None = None,
    limit: int = Query(300, le=1000),
    sort: Literal["rank", "score"] = "rank",
):
    """margin/nguong muc tinh theo don vi 1 diem tren thang 30, quy doi sang thang cua phuong thuc
    (VD DGNL HCM thang 1200 -> 1 don vi = 40 diem). Moi muc lay toi da ~limit/3 dong gan diem nhat."""
    c = con()
    if year is None:
        year = c.execute("SELECT MAX(year) FROM admissions WHERE method = ?", (method,)).fetchone()
        year = year[0]
    # chi so sanh trong thang diem pho bien nhat cua phuong thuc (KETHOP/CCQT tron nhieu thang)
    sc = c.execute(
        "SELECT scale_max FROM admissions WHERE method = ? AND year = ? AND flag = '' "
        "AND scale_max IS NOT NULL GROUP BY scale_max ORDER BY COUNT(*) DESC LIMIT 1",
        (method, year),
    ).fetchone()
    out = {"year": year, "method": method, "combo": combo, "score": score, "sort": sort}
    if not sc:
        return out | {"scale": None, "margin": margin, "counts": {}, "total": 0, "rows": []}
    scale = sc[0]
    unit = scale / 30
    margin = unit if margin is None else margin
    combo_sql = " AND a.id IN (SELECT admission_id FROM admission_combos WHERE combo = ?)"
    cands = advice_candidates(c, method, year, score + margin, scale, combo)
    levels = ["Thử sức", "Vừa sức", "An toàn"]
    groups: dict[str, list[dict]] = {lv: [] for lv in levels}
    for r in cands:
        d = r["score"] - score
        r["level"] = levels[0] if d > 0 else (levels[1] if d > -unit else levels[2])
        groups[r["level"]].append(r)
    if sort == "rank":
        for group in groups.values():
            group.sort(key=vnur_sort_key)
    # chia deu han muc cho 3 muc (muc nao thieu thi nhuong cho muc khac)
    take = dict.fromkeys(levels, 0)
    left = limit
    while left and any(take[lv] < len(groups[lv]) for lv in levels):
        for lv in levels:
            if left and take[lv] < len(groups[lv]):
                take[lv] += 1
                left -= 1
    # Moi muc lay theo thu tu da chon (hang truong hoac diem).
    rows = [r for lv in levels for r in groups[lv][: take[lv]]]
    # xu huong 3 nam cua tung chuong trinh, cung thang diem (+ cung to hop neu co loc)
    hist_sql = (
        "SELECT a.year, MAX(a.score) FROM admissions a WHERE a.uni_code = ? AND a.program_code = ? "
        "AND a.method = ? AND a.scale_max = ? AND a.flag = ''"
    )
    for r in rows:
        hargs = [r["uni_code"], r["program_code"], method, scale]
        if combo:
            hargs.append(combo.upper())
        hist = c.execute(hist_sql + (combo_sql if combo else "") + " GROUP BY a.year", hargs)
        r["history"] = {str(y): s for y, s in hist}
        r["history"][str(year)] = r["score"]  # nam tham chieu = dung diem cua dong nay
    counts = {lv: len(groups[lv]) for lv in levels}
    return out | {
        "scale": scale,
        "margin": margin,
        "counts": counts,
        "total": len(cands),
        "rows": rows,
    }


def advice_candidates(c, method: str, year: int, ceiling: float, scale: float, combo: str = ""):
    """Shared query keeps score ties in the same SQLite order for API and static export."""
    where = "a.method = ? AND a.year = ? AND a.score <= ? AND a.flag = '' AND a.scale_max = ?"
    args: list = [method, year, ceiling, scale]
    if combo:
        where += " AND a.id IN (SELECT admission_id FROM admission_combos WHERE combo = ?)"
        args.append(combo.upper())
    return [
        dict(r)
        for r in c.execute(
            "SELECT a.*, u.name AS uni_name, u.short_name, "
            "u.vnur_rank, u.vnur_parent, u.vnur_name, u.vnur_url FROM admissions a "
            f"JOIN universities u ON u.uni_code = a.uni_code WHERE {where} ORDER BY a.score DESC",
            args,
        )
    ]


@app.get("/api/network/{name}")
def network(name: str, year: int):
    f = NETWORK_DIR / f"{name}_{year}.json"
    if not re.fullmatch(r"[a-z0-9_]+", name) or not f.exists():
        raise HTTPException(404, "Chưa có dữ liệu mạng này")
    return json.loads(f.read_text(encoding="utf-8"))


@app.get("/api/network")
def network_list():
    if not NETWORK_DIR.exists():
        return []
    # similar_majors_* la bang tra cuu cho /similar, khong phai do thi
    return sorted(
        p.stem
        for p in NETWORK_DIR.glob("*.json")
        if p.stem != "summary" and not p.stem.startswith("similar_majors_")
    )


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
