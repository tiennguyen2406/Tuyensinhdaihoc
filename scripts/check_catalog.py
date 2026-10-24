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
    for sorting in ("rank", "score"):
        d = api.advice("THPT", 24, combo="A00", year=2026, limit=1000, sort=sorting)
        for level in d["counts"]:
            group = [r for r in d["rows"] if r["level"] == level]
            key = (
                (
                    lambda r: (
                        r["vnur_rank"] is None,
                        r["vnur_rank"] or 0,
                        bool(r["vnur_parent"]),
                        -r["score"],
                    )
                )
                if sorting == "rank"
                else (lambda r: -r["score"])
            )
            assert group == sorted(group, key=key)
    direct = {"vnur_rank": 1, "vnur_parent": "", "score": 20}
    inherited = {"vnur_rank": 1, "vnur_parent": "ĐHQG HN", "score": 29}
    assert sorted([inherited, direct], key=api.vnur_sort_key) == [direct, inherited]
    print(
        "PASS: block aliases/conflicts, 5 parent groups, renamed schools, card counts, advice sorts"
    )


if __name__ == "__main__":
    check()
