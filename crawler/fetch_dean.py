"""Fetch HOCMAI admission plans and taxonomy terms for factual reference.

Run with the web stopped: python -m crawler.fetch_dean [--force]
Full source HTML stays in ignored data/raw/dean/; only facts are published.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "https://huongnghiep.hocmai.vn"
RAW = Path(__file__).resolve().parents[1] / "data/raw/dean"
UA = "EduRadar-student-project/2.0 (non-commercial SNA coursework; factual reference only)"
COLLECTIONS = ["de-an", "nam", "thanh-pho-tax", "nhom-truong", "phuong-thuc-xet-tuyen"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    last_request = 0.0

    def request(url):
        nonlocal last_request
        for attempt in range(3):
            time.sleep(max(0, 2 - (time.monotonic() - last_request)))
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": UA, "Accept": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=60) as response:
                    return response.read(), dict(response.headers)
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
            finally:
                last_request = time.monotonic()

    robots = urllib.robotparser.RobotFileParser(BASE + "/robots.txt")
    body, _ = request(BASE + "/robots.txt")
    robots.parse(body.decode("utf-8").splitlines())
    metadata_path = RAW / "fetch_meta.json"
    old = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    metadata = {
        "source": BASE,
        "collected_at": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds"),
        "collections": {},
    }
    for collection in COLLECTIONS:
        page, pages, total = 1, 1, 0
        while page <= pages:
            target = RAW / f"{collection}_{page}.json"
            previous = old.get("collections", {}).get(collection)
            if target.exists() and previous and not args.force:
                pages, total = previous["pages"], previous["total"]
            else:
                url = f"{BASE}/wp-json/wp/v2/{collection}?per_page=100&page={page}"
                if not robots.can_fetch(UA, url):
                    raise RuntimeError(f"robots.txt disallows {url}")
                body, headers = request(url)
                payload = json.loads(body)
                if not isinstance(payload, list):
                    raise ValueError(f"Unexpected WordPress response: {collection}")
                headers = {k.lower(): v for k, v in headers.items()}
                pages = max(1, int(headers.get("x-wp-totalpages", 1)))
                total = int(headers.get("x-wp-total", len(payload)))
                target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                print(f"{collection}: page {page}/{pages}, {len(payload)} records", flush=True)
            page += 1
        metadata["collections"][collection] = {"pages": pages, "total": total}
        for stale in RAW.glob(f"{collection}_*.json"):
            if int(stale.stem.rsplit("_", 1)[1]) > pages:
                stale.unlink()
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print("Saved raw plans and terms to data/raw/dean/", flush=True)


if __name__ == "__main__":
    main()
