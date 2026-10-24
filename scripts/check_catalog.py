"""Small V2 catalog regressions; no PostgreSQL or crawling required."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.clean import block_rows  # noqa: E402
from webapp import main as api  # noqa: E402


def check():
    rows = block_rows(
        [
            {"code": "X02, K21; TH6", "name": "Toán, Ngữ văn, Tin học"},
            {"code": "(Ngữ văn, Vật lí, Tiếng Hàn)", "name": "Sai"},
            {"code": "HSA - Khoa học", "name": "Sai"},
        ]
    )
    assert dict(rows) == dict.fromkeys(["X02", "K21", "TH6"], "Toán, Ngữ văn, Tin học")
    conflicts = dict(
        block_rows(
            [
                {"code": "X02, TH3", "name": "Tin học"},
                {"code": "X07, TH3", "name": "Công nghệ"},
            ]
        )
    )
    assert "Tin học / Công nghệ" in conflicts["TH3"]
    idx = {u["uni_code"]: u for u in api.search_index()["unis"]}
    assert idx["BKA"]["vnur_rank"] == 3
    assert idx["QHI"]["vnur_rank"] == 1 and idx["QHI"]["vnur_parent"] == "ĐHQG HN"
    assert idx["QSB"]["vnur_rank"] == 2
    assert idx["DDK"]["vnur_rank"] == 9
    assert idx["DHT"]["vnur_rank"] == 14
    assert idx["DTK"]["vnur_rank"] == 15
    assert idx["SPK"]["vnur_rank"] == 38 and idx["DKS"]["vnur_rank"] == 64
    assert idx["THV"]["vnur_rank"] == 89 and idx["DHV"]["vnur_rank"] is None
    with api.con() as c:
        for u in idx.values():
            expected = c.execute(
                "SELECT COUNT(DISTINCT program_code),COUNT(DISTINCT method),MIN(year) "
                "FROM admissions WHERE uni_code=? AND year=?",
                (u["uni_code"], u["latest_year"]),
            ).fetchone()
            assert (u["n_programs"], u["n_methods"]) == tuple(expected)[:2]
    d = api.advice("THPT", 24, combo="A00", year=2026, limit=1000)
    assert d["rows"] == sorted(d["rows"], key=lambda r: -r["hot"])
    assert d["total"] == sum(d["counts"].values()) > 1000
    page2 = api.advice("THPT", 24, combo="A00", year=2026, offset=50)
    assert [r["id"] for r in page2["rows"]] == [r["id"] for r in d["rows"][50:100]]
    for r in d["rows"]:
        assert all(0 <= r[k] <= 1 for k in ("hot", "hot_uni", "hot_major", "hot_trend"))
        assert (
            abs(r["hot"] - (0.5 * r["hot_uni"] + 0.3 * r["hot_major"] + 0.2 * r["hot_trend"]))
            < 1e-3
        )
    base = {
        "uni_code": "X",
        "program_code": "X",
        "method": "THPT",
        "scale_max": 30,
        "major_code": None,
    }
    assert api.hot_parts(base | {"vnur_rank": 1, "vnur_parent": ""})["hot_uni"] == 1.0
    assert api.hot_parts(base | {"vnur_rank": 100, "vnur_parent": ""})["hot_uni"] == 0.01
    assert api.hot_parts(base | {"vnur_rank": 1, "vnur_parent": "ĐHQG HN"})["hot_uni"] == 0.8
    none = api.hot_parts(base | {"vnur_rank": None, "vnur_parent": ""})
    assert none["hot_uni"] == 0 and none["hot_trend"] == 0.5 and none["hot_major"] == 0
    hot = api.hot_index()
    assert len(hot["hot_majors"]) == -(-len(hot["major"]) // 10)
    print("PASS: block aliases/conflicts, parent groups, renamed schools, card counts, hot advice")


if __name__ == "__main__":
    check()
