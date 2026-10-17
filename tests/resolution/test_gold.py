import json
from pathlib import Path

import pytest

from services.data.resolution.contract import EntityQuery
from services.data.resolution.matching import match
from services.data.resolution.registry import EntityRegistry

GOLD = json.loads(Path(__file__).with_name("gold.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", GOLD, ids=lambda c: c["id"])
def test_independently_annotated_gold(case):
    registry = EntityRegistry.model_validate(
        dict(
            version="registry/gold/1",
            alias_version="aliases/gold/1",
            classification="synthetic",
            entities=case["entities"],
            aliases=case["aliases"],
        )
    )
    actual = match(EntityQuery.model_validate(case["query"]), registry)
    expected = case["expected"]
    assert actual.status == expected["status"]
    assert actual.entity_key == expected["entity_key"]
    assert set(expected["suggestions_contain"]).issubset({o.entity_key for o in actual.options})
    if actual.method == "fuzzy_suggestion":
        assert actual.canonical_id is None


def test_gold_partitions_have_no_shared_family_or_case():
    assert len(GOLD) >= 200
    a = {c["family"] for c in GOLD if c["split"] == "calibration"}
    b = {c["family"] for c in GOLD if c["split"] == "evaluation"}
    assert not a & b and len({c["id"] for c in GOLD}) == len(GOLD)
