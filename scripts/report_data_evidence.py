"""Đọc nguồn đã chốt cho Chương 2; không crawl, không sửa DB.

Chạy: .venv/Scripts/python.exe scripts/report_data_evidence.py
Xuất toàn bộ 292 trường và URL có trong DB ra stdout (JSON UTF-8).
"""

import csv
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).resolve().parents[1]
con = sqlite3.connect(f"file:{root / 'data/eduradar.db'}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

queries = {
    "schools_292": """SELECT a.uni_code,u.name,COUNT(*) AS records,
      SUM(year=2024) AS y2024,SUM(year=2025) AS y2025,SUM(year=2026) AS y2026
      FROM admissions a JOIN universities u USING(uni_code)
      GROUP BY a.uni_code ORDER BY records DESC,a.uni_code""",
    "year_method": "SELECT year,method,COUNT(*) AS records FROM admissions GROUP BY year,method",
    "mapping": """SELECT COALESCE(NULLIF(match_how,''),'chua_map') AS match_how,
      COUNT(*) AS records,ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM admissions),2) AS pct
      FROM admissions GROUP BY match_how ORDER BY records DESC""",
    "flags": "SELECT COALESCE(NULLIF(flag,''),'ok') AS flag,COUNT(*) AS records FROM admissions GROUP BY flag",
    "tuition_urls": "SELECT source_url,source_type,COUNT(*) AS schools FROM tuition GROUP BY source_url,source_type ORDER BY source_url",
    "vnur_urls": "SELECT uni_code,vnur_url,vnur_parent FROM universities WHERE vnur_rank IS NOT NULL ORDER BY uni_code",
    "province_urls": "SELECT uni_code,province,province_source,province_url FROM universities ORDER BY uni_code",
    "sp2": """SELECT uni_code,year,method,program_code,program_name,score,score_equiv,combos
      FROM admissions WHERE uni_code='SP2' AND year=2026 AND program_code='7140247'""",
    "year_coverage": """SELECT y2024,y2025,y2026,COUNT(*) AS schools FROM
      (SELECT uni_code,MAX(year=2024) AS y2024,MAX(year=2025) AS y2025,
       MAX(year=2026) AS y2026 FROM admissions GROUP BY uni_code)
      GROUP BY y2024,y2025,y2026""",
}
result = {name: [dict(row) for row in con.execute(sql)] for name, sql in queries.items()}
with (root / "data/raw/fetch_log.csv").open(encoding="utf-8-sig", newline="") as fh:
    log = list(csv.DictReader(fh))
times = [datetime.fromisoformat(row["time"]) for row in log]
result["fetch_log"] = {
    "requests": len(log),
    "jobs_unique": len({(r["code"], r["year"]) for r in log}),
    "raw_records": sum(int(r["rows"]) for r in log),
    "first": min(times).isoformat(),
    "last": max(times).isoformat(),
    "duration_seconds": (max(times) - min(times)).total_seconds(),
    "errors": [r for r in log if r["error"]],
    "empty_by_year": dict(Counter(r["year"] for r in log if int(r["rows"]) == 0)),
    "raw_by_year": {
        y: sum(int(r["rows"]) for r in log if r["year"] == y) for y in ("2024", "2025", "2026")
    },
}
print(json.dumps(result, ensure_ascii=False, indent=2))
