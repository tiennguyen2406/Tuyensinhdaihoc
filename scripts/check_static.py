"""Compare exported API payloads; run after python scripts/export_static.py."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from webapp import main  # noqa: E402


def read(path):
    return json.loads((ROOT / "site" / path).read_text(encoding="utf-8"))


def main_check():
    assert read("data/meta.json") == main.meta()
    assert read("data/uni/BKA_2026.json") == main.university_scores("BKA", 2026)
    assert read("data/major/7480201_2025.json") == main.major_scores("7480201", 2025)
    idx = read("data/majors.json")
    program = idx["programs"][0]
    assert read(f"data/program/{program['file']}_2026.json") == main.program_scores(
        program["program_name"], 2026
    )
    assert read("data/network/g2_uni_uni_2026.json") == main.network("g2_uni_uni", 2026)
    coverage = read("data/coverage.json")
    assert len(coverage["missing"]) == 15
    assert sum(sum(u["counts"].values()) for u in coverage["universities"]) == 71009
    files = [p for p in (ROOT / "site").rglob("*") if p.is_file()]
    largest = max(files, key=lambda p: p.stat().st_size)
    assert largest.stat().st_size < 50_000_000
    print(
        f"PASS: API parity, coverage; {len(files)} files, "
        f"{sum(p.stat().st_size for p in files):,} bytes; "
        f"largest {largest.relative_to(ROOT)} ({largest.stat().st_size:,} bytes)"
    )


if __name__ == "__main__":
    main_check()
