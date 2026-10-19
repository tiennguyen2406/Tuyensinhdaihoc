"""Author synthetic expected decisions without importing/calling the resolver.
Families are assigned wholly to calibration/evaluation before scoring.
"""

import json
from pathlib import Path

from tests.resolution.helpers import alias, entity

FAMILIES = [
    "official_code",
    "approved_alias",
    "fuzzy_typo",
    "fuzzy_tie",
    "three_bach_khoa",
    "alias_collision",
    "code_domain_conflict",
    "expired_code",
    "program_ownership",
    "offering_variants",
    "source_methods",
    "unknown_context",
    "fuzzy_typo_holdout",
    "fuzzy_tie_holdout",
]


def build():
    cases = []
    for f in FAMILIES:
        for i in range(20):
            prefix = f + ":" + str(i)
            u = "u:" + prefix
            e = entity(
                u,
                name=f"Đại học Mẫu {f} {i}",
                codes=[{"system": "test:university", "value": "TEST-" + str(i)}],
            )
            es = [e]
            als = []
            q = {"kind": "university", "code": "TEST-" + str(i), "code_system": "test:university"}
            want = "resolved"
            chosen = u
            top = []
            if f == "approved_alias":
                als = [alias("a:" + prefix, u, "ĐH Mẫu riêng " + str(i))]
                q = {"kind": "university", "name": als[0]["value"]}
            elif f in {"fuzzy_typo", "fuzzy_typo_holdout"}:
                e["name"] = f"Đại học Mẫu Công nghệ Alpha {i}"
                q = {"kind": "university", "name": f"Đại học Mẫu Công nghệ Alpa {i}"}
                want = "unresolved"
                chosen = None
                if f.endswith("holdout"):
                    e["name"] = f"Đại học Mẫu Khoa học Delta ứng dụng {i}"
                    q["name"] = f"Đại học Mẫu Khoa học Dalta ứng dụng {i}"
                top = [u]
            elif f in {"fuzzy_tie", "fuzzy_tie_holdout"}:
                e["name"] = f"Đại học Mẫu Alpha {i} A"
                es.append(entity(u + ":b", name=f"Đại học Mẫu Alpha {i} B"))
                q = {"kind": "university", "name": f"Đại học Mẫu Alpha {i}"}
                want = "ambiguous"
                chosen = None
                if f.endswith("holdout"):
                    e["name"] = f"Đại học Mẫu Kỹ thuật Beta {i} A"
                    es[-1]["name"] = f"Đại học Mẫu Kỹ thuật Beta {i} B"
                    q["name"] = f"Đại học Mẫu Kỹ thuật Beta {i}"
                top = [u, u + ":b"]
            elif f == "three_bach_khoa":
                names = [
                    "Đại học Bách khoa Hà Nội",
                    "Đại học Bách khoa TP.HCM",
                    "Đại học Bách khoa Đà Nẵng",
                ]
                es = [
                    entity(
                        u + ":" + str(n),
                        name=name,
                        codes=[{"system": "fixture:not-official", "value": f"TEST-BK-{i}-{n}"}],
                    )
                    for n, name in enumerate(names)
                ]
                chosen = u + ":" + str(i % 3)
                q = {
                    "kind": "university",
                    "code": f"TEST-BK-{i}-{i % 3}",
                    "code_system": "fixture:not-official",
                }
            elif f == "alias_collision":
                es.append(entity(u + ":b", name="Đại học Mẫu Khác " + str(i)))
                als = [
                    alias("a:" + prefix, u, "Bách khoa"),
                    alias("b:" + prefix, u + ":b", "Bách khoa"),
                ]
                q = {"kind": "university", "name": "Bách khoa"}
                want = "ambiguous"
                chosen = None
                top = [u, u + ":b"]
            elif f == "code_domain_conflict":
                e["domains"] = [f"a{i}.example.test"]
                es.append(entity(u + ":b", domains=[f"b{i}.example.test"]))
                q["domain"] = f"b{i}.example.test"
                want = "ambiguous"
                chosen = None
            elif f == "expired_code":
                e["codes"][0].update(from_year=2020 + i % 3, to_year=2023)
                q["attributes"] = {"admission_year": 2024}
                want = "ambiguous"
                chosen = None
            elif f == "program_ownership":
                es.append(entity(u + ":b"))
                es += [
                    entity(
                        "p:" + prefix,
                        "program",
                        "Ngành mẫu giống tên",
                        university_key=u,
                        codes=[{"system": "test:program", "value": "P"}],
                    ),
                    entity(
                        "p:" + prefix + ":b",
                        "program",
                        "Ngành mẫu giống tên",
                        university_key=u + ":b",
                        codes=[{"system": "test:program", "value": "P"}],
                    ),
                ]
                chosen = "p:" + prefix
                q = {
                    "kind": "program",
                    "university_key": u,
                    "code": "P",
                    "code_system": "test:program",
                }
            elif f == "offering_variants":
                pk = "p:" + prefix
                es.append(entity(pk, "program", university_key=u))
                a = {"admission_year": 2024, "campus": "BVH", "language": "vi", "track": "A"}
                b = a | (
                    {"campus": "BVS"}
                    if i % 4 in {0, 3}
                    else {"language": "en"}
                    if i % 4 == 1
                    else {"track": "B"}
                )
                es += [
                    entity(
                        "o:" + prefix,
                        "offering",
                        university_key=u,
                        program_key=pk,
                        attributes=a,
                        codes=[{"system": "test:offering", "value": "X"}],
                    ),
                    entity(
                        "o:" + prefix + ":b",
                        "offering",
                        university_key=u,
                        program_key=pk,
                        attributes=b,
                        codes=[{"system": "test:offering", "value": "X"}],
                    ),
                ]
                attrs = b.copy()
                chosen = "o:" + prefix + ":b"
                if i % 4 == 3:
                    attrs.pop("campus")
                    want = "ambiguous"
                    chosen = None
                q = {
                    "kind": "offering",
                    "university_key": u,
                    "program_key": pk,
                    "code": "X",
                    "code_system": "test:offering",
                    "attributes": attrs,
                }
            elif f == "source_methods":
                labels = ["Xét tuyển Tài năng", "Xét tuyển kết hợp", "HSA", "TSA"]
                es += [
                    entity(
                        "m:" + prefix + ":" + str(n),
                        "method",
                        label,
                        university_key=u,
                        attributes={
                            "input_kind": "composite" if n < 2 else "exam_total",
                            "max_score": 30,
                        },
                    )
                    for n, label in enumerate(labels)
                ]
                if i % 4 < 2:
                    chosen = "m:" + prefix + ":" + str(i % 4)
                    als = [alias("a:" + prefix, chosen, labels[i % 4], university_key=u)]
                    q = {"kind": "method", "name": labels[i % 4], "university_key": u}
                else:
                    chosen = None
                    want = "unresolved"
                    q = {
                        "kind": "method",
                        "name": "ĐGNL và ĐGTD" if i % 4 == 2 else "HSA",
                        "university_key": u,
                        "attributes": {"max_score": 30},
                    }
            elif f == "unknown_context":
                if i % 4 == 0:
                    q["attributes"] = {"province": "UNKNOWN_TO_REGISTRY"}
                elif i % 4 == 1:
                    es.append(entity("p:" + prefix, "program", university_key=u))
                    q = {"kind": "program", "name": "Đại học Mẫu Alpha"}
                    want = "unresolved"
                    chosen = None
                elif i % 4 == 2:
                    es.append(entity("p:" + prefix, "program", university_key=u))
                    es.append(
                        entity(
                            "o:" + prefix,
                            "offering",
                            university_key=u,
                            program_key="p:" + prefix,
                            attributes={"admission_year": 2024},
                            codes=[{"system": "test:offering", "value": "X"}],
                        )
                    )
                    q = {
                        "kind": "offering",
                        "university_key": u,
                        "program_key": "p:" + prefix,
                        "code": "X",
                        "code_system": "test:offering",
                    }
                    want = "unresolved"
                    chosen = None
                else:
                    es.append(
                        entity(
                            "major:" + prefix,
                            "major",
                            codes=[{"system": "taxonomy:fixture", "value": "123"}],
                        )
                    )
                    q = {"kind": "major", "code": "123", "code_system": "offering:fixture"}
                    want = "unresolved"
                    chosen = None
            cases.append(
                {
                    "id": prefix,
                    "family": f,
                    "split": "calibration" if FAMILIES.index(f) < 4 else "evaluation",
                    "provenance": "synthetic independently authored expected decision from T07 requirements; all UUIDs/reviewers/codes are fixture-only",
                    "entities": es,
                    "aliases": als,
                    "query": q,
                    "expected": {"status": want, "entity_key": chosen, "suggestions_contain": top},
                }
            )
    return {
        "schema": "resolution-gold/1",
        "classification": "synthetic; not independent real-world entity verification",
        "cases": cases,
    }


if __name__ == "__main__":
    gold = build()
    cases = gold.pop("cases")
    header = json.dumps(gold, ensure_ascii=False)[:-1]
    content = (
        header
        + ', "cases": [\n'
        + ",\n".join(json.dumps(c, ensure_ascii=False, sort_keys=True) for c in cases)
        + "\n]}\n"
    )
    Path("tests/resolution/gold.json").write_text(content, encoding="utf-8")
