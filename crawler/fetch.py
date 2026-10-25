"""EduRadar V2 - tai diem chuan tu API cong khai cua diemthi.tuyensinh247.com.

Chi dung thu vien chuan Python (khong can pip install).

Cach chay (PowerShell, tai thu muc DiemThiDaiHoc):
    .venv\\Scripts\\python.exe -m crawler.fetch --limit 5      # thu 5 truong
    .venv\\Scripts\\python.exe -m crawler.fetch                # tat ca truong dai hoc, 2024-2026
    .venv\\Scripts\\python.exe -m crawler.fetch --blocks-only  # chi danh muc to hop

Ket qua:
    data/raw/schools.json                    danh sach truong
    data/raw/blocks.json                     ma to hop + ten mon tu API
    data/raw/cutoff/<nam>/<MA>.json          JSON goc cua tung truong/nam
    data/raw/fetch_log.csv                   nhat ky (thoi gian, truong, nam, so dong, loi)

Chay lai bao nhieu lan cung duoc: file da tai se duoc bo qua (dung --force de tai lai).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime
from pathlib import Path

BASE = "https://diemthi.tuyensinh247.com"
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 EduRadar-student-project"
    ),
    "Accept": "application/json",
    "Accept-Language": "vi-VN,vi;q=0.9",
}
DELAY = 1.5
_last_request = 0.0
_robots = None


def read_url(url: str) -> bytes:
    global _last_request
    time.sleep(max(0, DELAY - (time.monotonic() - _last_request)))
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
            return r.read()
    finally:
        _last_request = time.monotonic()


def check_robots(url: str):
    global _robots
    if _robots is None:
        _robots = urllib.robotparser.RobotFileParser(BASE + "/robots.txt")
        try:
            _robots.parse(read_url(BASE + "/robots.txt").decode("utf-8").splitlines())
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                _robots.parse([])
            else:
                raise
    if not _robots.can_fetch(HEADERS["User-Agent"], url):
        raise RuntimeError(f"robots.txt khong cho phep: {url}")


def get_json(path: str, params: dict | None = None, retries: int = 3) -> dict:
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    check_robots(url)
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return json.loads(read_url(url).decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            wait = 5 * attempt
            print(f"   ! loi lan {attempt}: {exc} -> doi {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"That bai sau {retries} lan: {url} ({last})")


def load_schools(force: bool) -> list[dict]:
    path = RAW / "schools.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    data = get_json("/api/school/search")
    schools = data.get("data") or []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schools, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Da luu {len(schools)} truong -> {path.relative_to(ROOT)}")
    return schools


def load_blocks(force: bool = False):
    path = RAW / "blocks.json"
    if path.exists() and not force:
        return
    data = get_json("/api/common/blocks")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Da luu to hop -> {path.relative_to(ROOT)}")


def main() -> int:
    global DELAY
    ap = argparse.ArgumentParser(description="Tai diem chuan tuyensinh247 (API JSON)")
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025, 2026])
    ap.add_argument("--limit", type=int, default=0, help="chi lay N truong dau (de thu)")
    ap.add_argument("--codes", default="", help="danh sach ma truong, VD: BKA,KHA,NTH")
    ap.add_argument("--include-colleges", action="store_true", help="lay ca cao dang")
    ap.add_argument("--delay", type=float, default=1.5, help="giay nghi giua 2 request")
    ap.add_argument("--force", action="store_true", help="tai lai ca file da co")
    ap.add_argument("--blocks-only", action="store_true", help="chi tai danh muc to hop")
    args = ap.parse_args()
    DELAY = max(1.5, args.delay)
    load_blocks(args.force)
    if args.blocks_only:
        return 0

    schools = load_schools(args.force)
    if not args.include_colleges:
        schools = [s for s in schools if s.get("level") == 2]  # level 2 = dai hoc
    if args.codes:
        wanted = {c.strip().upper() for c in args.codes.split(",") if c.strip()}
        schools = [s for s in schools if (s.get("code") or "").upper() in wanted]
    if args.limit:
        schools = schools[: args.limit]

    jobs = [(s, y) for s in schools for y in args.years]
    todo = [
        (s, y)
        for s, y in jobs
        if args.force or not (RAW / "cutoff" / str(y) / f"{s['code']}.json").exists()
    ]
    est = len(todo) * (args.delay + 0.5) / 60
    print(
        f"{len(schools)} truong x {len(args.years)} nam = {len(jobs)} trang; "
        f"can tai {len(todo)} (uoc ~{est:.0f} phut)"
    )

    log_path = RAW / "fetch_log.csv"
    new_log = not log_path.exists()
    total_rows = 0
    with log_path.open("a", newline="", encoding="utf-8") as fh:
        log = csv.writer(fh)
        if new_log:
            log.writerow(["time", "school_id", "code", "year", "rows", "error"])
        for i, (s, y) in enumerate(todo, 1):
            out = RAW / "cutoff" / str(y) / f"{s['code']}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            err, n = "", 0
            try:
                data = get_json("/api/common/cutoff-score", {"school_id": s["id"], "year": y})
                if not data.get("success", False):
                    err = f"success=false {data.get('msg')}"
                n = len(data.get("data") or [])
                payload = {
                    "school": s,
                    "year": y,
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "source_url": f"{BASE}/diem-chuan/{s.get('alias')}-{s['code']}.html",
                    "response": data,
                }
                out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                total_rows += n
            except Exception as exc:  # ghi log va chay tiep, khong dung ca dot
                err = str(exc)
            log.writerow(
                [datetime.now().isoformat(timespec="seconds"), s["id"], s["code"], y, n, err]
            )
            fh.flush()
            print(
                f"[{i}/{len(todo)}] {s['code']:<6} {y}: {n:>4} dong {('LOI ' + err) if err else ''}",
                flush=True,
            )
            time.sleep(args.delay + random.uniform(0, 0.5))

    print(f"Xong. Them {total_rows} dong tho. Chay tiep: python -m pipeline.clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
