"""Check committed site data (--committed), or compare it with the local FastAPI data."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from webapp import main  # noqa: E402


def read(path):
    return json.loads((ROOT / "site" / path).read_text(encoding="utf-8"))


def main_check():
    committed = "--committed" in sys.argv
    metadata = read("data/meta.json")
    if not committed:
        assert metadata == main.meta()
        assert read("data/dean.json") == main.dean_index()
        assert read("data/uni/BKA_2026.json") == main.university_scores("BKA", 2026)
        assert read("data/major/7480201_2025.json") == main.major_scores("7480201", 2025)
    idx = read("data/majors.json")
    program = idx["programs"][0]
    if not committed:
        assert read(f"data/program/{program['file']}_2026.json") == main.program_scores(
            program["program_name"], 2026
        )
        assert read("data/network/g2_uni_uni_2026.json") == main.network("g2_uni_uni", 2026)
    coverage = read("data/coverage.json")
    assert len(coverage["missing"]) == 15
    assert (
        sum(sum(u["counts"].values()) for u in coverage["universities"])
        == metadata["stats"]["rows"]
    )
    unis = read("data/universities.json")
    assert len(unis) == metadata["stats"]["unis"] == len(coverage["universities"])
    assert len(idx["majors"]) == metadata["stats"]["majors"]
    for u in unis:
        for year in metadata["years"]:
            data = read(f"data/uni/{u['uni_code']}_{year}.json")
            assert data["university"]["uni_code"] == u["uni_code"] and data["year"] == year
            assert data["university"]["province"] == u["province"]
    for m in idx["majors"]:
        for year in metadata["years"]:
            assert read(f"data/major/{m['major_code']}_{year}.json")["year"] == year
    for p in idx["programs"]:
        for year in metadata["years"]:
            assert read(f"data/program/{p['file']}_{year}.json")["year"] == year
    for p in (ROOT / "site/data/network").glob("g*.json"):
        g = json.loads(p.read_text(encoding="utf-8"))
        nodes = {n["id"] for n in g["nodes"]}
        assert all(e["source"] in nodes and e["target"] in nodes for e in g["edges"])
    files = [p for p in (ROOT / "site").rglob("*") if p.is_file()]
    largest = max(files, key=lambda p: p.stat().st_size)
    assert largest.stat().st_size < 50_000_000
    print(
        f"PASS: {'committed data' if committed else 'API parity'}, coverage; {len(files)} files, "
        f"{sum(p.stat().st_size for p in files):,} bytes; "
        f"largest {largest.relative_to(ROOT)} ({largest.stat().st_size:,} bytes)"
    )


if __name__ == "__main__":
    main_check()
