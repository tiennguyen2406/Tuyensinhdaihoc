"""Export the local API to site/ for GitHub Pages (no crawl, no database writes).

Run: .venv/Scripts/python.exe scripts/export_static.py
"""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from webapp import main as api  # noqa: E402

SITE = ROOT / "site"


def write(path: str, data):
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def advice_data(method: str, year: int) -> dict:
    # Let /api/advice select the canonical scale and default margin itself.
    reference = api.advice(method, 0, year=year, margin=-1, limit=0)
    scale = reference["scale"]
    if scale is None:
        return {"scale": None, "columns": [], "rows": [], "histories": {}}
    c = api.con()
    rows = api.advice_candidates(c, method, year, float("inf"), scale)
    combo_map = defaultdict(list)
    for row in c.execute("SELECT admission_id, combo FROM admission_combos ORDER BY rowid"):
        combo_map[row[0]].append(row[1])
    histories = {}
    for r in c.execute(
        "SELECT a.uni_code, a.program_code, a.year, a.score, a.id FROM admissions a "
        "WHERE a.method=? AND a.scale_max=? AND a.flag=''",
        (method, scale),
    ):
        key = json.dumps([r[0], r[1]], ensure_ascii=False, separators=(",", ":"))
        h = histories.setdefault(key, {})
        for combo in ["", *combo_map[r[4]]]:
            years = h.setdefault(combo, {})
            y = str(r[2])
            if r[3] is not None:
                if years.get(y) is None or r[3] > years[y]:
                    years[y] = r[3]
            else:
                years.setdefault(y, None)
    columns = list(rows[0]) if rows else []
    # Column arrays avoid repeating field names; combo membership is the normalized table.
    packed = [
        [*[r[k] for k in columns], combo_map[r["id"]]] for r in rows if r["score"] is not None
    ]
    c.close()
    return {"scale": scale, "columns": columns, "rows": packed, "histories": histories}


def export():
    SITE.mkdir(exist_ok=True)
    # Remove only previously generated data inside the fixed site/ directory.
    data = SITE / "data"
    if data.exists():
        shutil.rmtree(data)
    meta = api.meta()
    idx = api.search_index()
    write("data/meta.json", meta)
    write("data/universities.json", idx["unis"])
    programs = [dict(p, file=f"p{i:04}") for i, p in enumerate(idx["programs"])]
    write("data/majors.json", {"majors": idx["majors"], "programs": programs})
    write("data/coverage.json", api.coverage())
    for year in meta["years"]:
        for u in idx["unis"]:
            write(
                f"data/uni/{u['uni_code']}_{year}.json", api.university_scores(u["uni_code"], year)
            )
        for m in idx["majors"]:
            write(
                f"data/major/{m['major_code']}_{year}.json", api.major_scores(m["major_code"], year)
            )
        for p in programs:
            write(
                f"data/program/{p['file']}_{year}.json", api.program_scores(p["program_name"], year)
            )
        for m in meta["methods"]:
            write(f"data/advice/{m['method']}_{year}.json", advice_data(m["method"], year))
        print(f"Exported {year}", flush=True)
    write("data/network.json", api.network_list())
    for p in api.NETWORK_DIR.glob("*.json"):
        write(f"data/network/{p.name}", json.loads(p.read_text(encoding="utf-8")))
    for name in (
        "app.js",
        "style.css",
        "favicon.svg",
        "vendor/vis-network.min.js",
        "vendor/LICENSE-MIT",
        "vendor/LICENSE-APACHE-2.0",
    ):
        target = SITE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(api.STATIC / name, target)
    html = (api.STATIC / "index.html").read_text(encoding="utf-8")
    html = html.replace('<html lang="vi">', '<html lang="vi" data-mode="static">')
    (SITE / "index.html").write_text(html.replace('="static/', '="'), encoding="utf-8")
    (SITE / ".nojekyll").touch()
    files = [p for p in SITE.rglob("*") if p.is_file()]
    largest = max(files, key=lambda p: p.stat().st_size)
    if largest.stat().st_size >= 50_000_000:
        raise ValueError(f"File exceeds 50 MB: {largest}")
    print(
        f"{len(files)} files; {sum(p.stat().st_size for p in files):,} bytes; "
        f"largest: {largest.relative_to(SITE)} ({largest.stat().st_size:,} bytes)"
    )


if __name__ == "__main__":
    export()
