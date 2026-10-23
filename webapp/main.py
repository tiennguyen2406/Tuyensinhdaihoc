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
def search_index() -> dict:
    c = con()
    unis = [
        dict(r)
        for r in c.execute(
            "SELECT u.*, COUNT(a.id) AS n_rows FROM universities u "
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
    for u in unis:
        u["_k"] = unaccent(f"{u['name']} {u['short_name'] or ''} {u['uni_code']}")
    for m in majors:
        m["_k"] = unaccent(f"{m['major_name']} {m['major_code']}")
    return {"unis": unis, "majors": majors}


def rank(items: list[dict], q: str, limit: int) -> list[dict]:
    words = unaccent(q).split()
    hits = [i for i in items if all(w in i["_k"] for w in words)]
    hits.sort(
        key=lambda i: (not i["_k"].startswith(unaccent(q)), -i.get("n_rows", i.get("n_unis", 0)))
    )
    return [{k: v for k, v in i.items() if k != "_k"} for i in hits[:limit]]


def method_sort(m: str) -> int:
    return METHOD_ORDER.index(m) if m in METHOD_ORDER else 99


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
    return {"years": years, "methods": methods, "combos": combos, "stats": stats}


@app.get("/api/universities")
def universities(q: str = "", limit: int = Query(15, le=50)):
    return rank(search_index()["unis"], q, limit) if q.strip() else []


@app.get("/api/majors")
def majors(q: str = "", limit: int = Query(15, le=50)):
    return rank(search_index()["majors"], q, limit) if q.strip() else []


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
        "university": dict(uni),
        "year": year,
        "years": years,
        "methods": [{"method": m, "method_name": names[m]} for m in methods],
        "rows": list(table.values()),
        "tuition": tuition,
        "source_url": rows[0]["source_url"] if rows else None,
    }


@app.get("/api/majors/{major_code}/scores")
def major_scores(major_code: str, year: int, method: str = ""):
    c = con()
    m = c.execute("SELECT * FROM majors WHERE major_code = ?", (major_code,)).fetchone()
    if not m:
        raise HTTPException(404, "Không tìm thấy ngành")
    sql = (
        "SELECT a.*, u.name AS uni_name, u.short_name FROM admissions a "
        "JOIN universities u ON u.uni_code = a.uni_code WHERE a.major_code = ? AND a.year = ?"
    )
    args: list = [major_code, year]
    if method:
        sql += " AND a.method = ?"
        args.append(method)
    rows = [dict(r) for r in c.execute(sql + " ORDER BY a.method, a.score DESC", args)]
    rows.sort(key=lambda r: (method_sort(r["method"]), -(r["score"] or 0)))
    return {"major": dict(m), "year": year, "rows": rows}


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
    margin: float = 1.0,
    limit: int = Query(300, le=1000),
):
    c = con()
    if year is None:
        year = c.execute("SELECT MAX(year) FROM admissions WHERE method = ?", (method,)).fetchone()[
            0
        ]
    sql = (
        "SELECT a.*, u.name AS uni_name, u.short_name FROM admissions a "
        "JOIN universities u ON u.uni_code = a.uni_code "
        "WHERE a.method = ? AND a.year = ? AND a.score <= ? AND a.flag = ''"
    )
    args: list = [method, year, score + margin]
    if combo:
        sql += " AND a.id IN (SELECT admission_id FROM admission_combos WHERE combo = ?)"
        args.append(combo.upper())
    if method in ("THPT", "HOCBA"):
        sql += " AND a.scale_max = 30"
    rows = [dict(r) for r in c.execute(sql + " ORDER BY a.score DESC LIMIT ?", args + [limit])]
    # xu huong 3 nam cho tung chuong trinh
    for r in rows:
        hist = c.execute(
            "SELECT year, MAX(score) s FROM admissions WHERE uni_code=? AND program_code=? "
            "AND method=? GROUP BY year ORDER BY year",
            (r["uni_code"], r["program_code"], method),
        )
        r["history"] = {str(y): s for y, s in hist}
        d = r["score"] - score
        r["level"] = "Thử sức" if d > 0 else ("Vừa sức" if d > -1 else "An toàn")
    return {"year": year, "method": method, "combo": combo, "score": score, "rows": rows}


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
    return sorted(p.stem for p in NETWORK_DIR.glob("*.json") if p.stem != "summary")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
