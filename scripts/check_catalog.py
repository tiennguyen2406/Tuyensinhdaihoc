"""Small V2 catalog regressions; no PostgreSQL or crawling required."""

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.clean import block_rows, split_combos  # noqa: E402
from pipeline.tuition_import import SOURCE, parse  # noqa: E402
from webapp import main as api  # noqa: E402


def committed_catalog(idx):
    def read(path):
        return json.loads((ROOT / "site/data" / path).read_text(encoding="utf-8"))

    metadata = read("meta.json")
    overrides = json.loads(
        (ROOT / "data/manual/tuition_extra_overrides.json").read_text(encoding="utf-8")
    )
    for code, override in overrides.items():
        data = read(f"uni/{code}_2026.json")["tuition_extra"]
        assert all(data[k] == value for k, value in override.items()), code
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", metadata["updated_on"])
    for methods in metadata["combo_usage"].values():
        for items in methods.values():
            assert items == sorted(items, key=lambda r: (-r["n"], r["combo"]))
            assert all(metadata["combo_subjects"].get(i["combo"]) and i["n"] > 0 for i in items)
    for u in idx.values():
        data = read(f"uni/{u['uni_code']}_{u['latest_year']}.json")
        assert u["n_programs"] == len({r["program_code"] for r in data["rows"]})
        assert u["n_methods"] == len(data["methods"])
    for path in (ROOT / "site/data/advice").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for values in data["rows"]:
            r = dict(zip(data["columns"], values))
            assert all(0 <= r[k] <= 1 for k in ("hot", "hot_uni", "hot_major", "hot_trend"))
            expected_uni = (
                0
                if r["vnur_rank"] is None
                else (101 - r["vnur_rank"]) / 100 * (0.8 if r["vnur_parent"] else 1)
            )
            assert abs(r["hot_uni"] - expected_uni) < 1e-4
            assert (
                abs(r["hot"] - (0.5 * r["hot_uni"] + 0.3 * r["hot_major"] + 0.2 * r["hot_trend"]))
                < 1e-3
            )
            assert not set(r["combos"].split(";")) & {"BO3", "BO0", "AO1"}
    print("PASS: committed catalog, provinces, card counts, combos, hot formula")


def check():
    assert split_combos("BO3; b o0; A O 1; A00 A01; TH6") == ["A00", "A01", "B00", "B03", "TH6"]
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
                {"code": "X02, TH3", "name": "Tin học", "school_count": 98},
                {"code": "X07, TH3", "name": "Công nghệ", "school_count": 66},
            ]
        )
    )
    assert conflicts["TH3"] == "Tin học"
    overrides = json.loads(
        (ROOT / "data/manual/tuition_extra_overrides.json").read_text(encoding="utf-8")
    )
    tuition, review = parse()
    by_code = {r["uni_code"]: r for r in tuition}
    assert len(overrides) == 32
    assert not any(r["uni_code"] in overrides for r in review)
    source_parts = re.split(
        r"^### \d{2}\. ([A-Z0-9]{3}) — .+$", SOURCE.read_text(encoding="utf-8"), flags=re.M
    )
    source_by_code = dict(zip(source_parts[1::2], source_parts[2::2]))
    for code, override in overrides.items():
        assert by_code[code]["manual_override"] and by_code[code]["items"] == override["items"]
        source_numbers = set(re.findall(r"\d+(?:[.,]\d+)*", source_by_code[code]))
        for item in override["items"]:
            assert set(re.findall(r"\d+(?:[.,]\d+)*", item["amount"])) <= source_numbers, (
                code,
                item,
            )
    assert by_code["HHA"]["items"][1]["amount"] == "gần 700.000"
    assert "miễn học phí" in by_code["MDA"]["summary"]
    assert {i["unit"] for i in by_code["KTA"]["items"]} == {"đ/tín chỉ", "triệu đ/năm"}
    assert {i["unit"] for i in by_code["DVB"]["items"]} == {"đ/toàn khóa", "đ/tín chỉ"}
    assert len(by_code["TDB"]["items"]) == 8
    assert all(i["unit"] == "không ghi đơn vị trong nguồn" for i in by_code["NTS"]["items"][1:])
    committed = "--committed" in sys.argv
    unis = (
        json.loads((ROOT / "site/data/universities.json").read_text(encoding="utf-8"))
        if committed
        else api.search_index()["unis"]
    )
    idx = {u["uni_code"]: u for u in unis}
    with (ROOT / "data/manual/province_map.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            assert idx[row["uni_code"]]["province"] == row["tinh"] and row["nguon"].startswith(
                "https://"
            )
    assert all(u["province"] != "Khác" for u in idx.values())
    for code, province in {
        "VJU": "Thành phố Hà Nội",
        "QHQ": "Thành phố Hà Nội",
        "QHY": "Thành phố Hà Nội",
        "QSA": "An Giang",
        "DTK": "Thái Nguyên",
        "DTG": "Tuyên Quang",
        "DTP": "Lào Cai",
        "DDP": "Quảng Ngãi",
        "QSP": "Vĩnh Long",
    }.items():
        assert idx[code]["province"] == province
    assert idx["BKA"]["vnur_rank"] == 3
    assert idx["QHI"]["vnur_rank"] == 1 and idx["QHI"]["vnur_parent"] == "ĐHQG HN"
    assert idx["QSB"]["vnur_rank"] == 2
    assert idx["DDK"]["vnur_rank"] == 9
    assert idx["DHT"]["vnur_rank"] == 14
    assert idx["DTK"]["vnur_rank"] == 15
    assert idx["SPK"]["vnur_rank"] == 38 and idx["DKS"]["vnur_rank"] == 64
    assert idx["THV"]["vnur_rank"] == 89 and idx["DHV"]["vnur_rank"] is None
    if committed:
        committed_catalog(idx)
        return
    with api.con() as c:
        metadata = api.meta()
        for year, methods in metadata["combo_usage"].items():
            for method, items in methods.items():
                assert items == sorted(items, key=lambda r: (-r["n"], r["combo"]))
                for item in items:
                    assert metadata["combo_subjects"][item["combo"]]
                    assert (
                        item["n"]
                        == c.execute(
                            "SELECT COUNT(*) FROM admission_combos ac JOIN admissions a "
                            "ON a.id=ac.admission_id WHERE a.year=? AND a.method=? AND ac.combo=?",
                            (year, method, item["combo"]),
                        ).fetchone()[0]
                    )
        assert not c.execute(
            "SELECT 1 FROM admission_combos WHERE combo IN ('BO3','BO0','AO1')"
        ).fetchone()
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
