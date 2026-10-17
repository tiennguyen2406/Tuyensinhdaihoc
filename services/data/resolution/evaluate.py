"""Offline synthetic gold evaluation. Metrics are coverage checks, not real-world claims."""

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from services.data.resolution.contract import EntityQuery
from services.data.resolution.matching import match
from services.data.resolution.registry import EntityRegistry


def evaluate(path: Path) -> dict[str, Any]:
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    if len(cases) < 200 or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Gold requires >=200 unique independently labelled cases")
    groups = {
        split: {c["family"] for c in cases if c["split"] == split}
        for split in ["calibration", "evaluation"]
    }
    if groups["calibration"] & groups["evaluation"]:
        raise ValueError("Calibration/evaluation family leakage")
    result = {}
    for split in groups:
        records = [c for c in cases if c["split"] == split]
        correct = tp = fp = expected_auto = auto = review = fuzzy_hit = fuzzy_total = 0
        decisions: Counter[str] = Counter()
        for case in records:
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
            decisions[actual.status] += 1
            correct += (
                actual.status == expected["status"] and actual.entity_key == expected["entity_key"]
            )
            expected_auto += expected["entity_key"] is not None
            if actual.canonical_id:
                auto += 1
                tp += actual.entity_key == expected["entity_key"]
                fp += actual.entity_key != expected["entity_key"]
            else:
                review += 1
            if case["family"].startswith("fuzzy_"):
                fuzzy_total += 1
                fuzzy_hit += set(expected["suggestions_contain"]).issubset(
                    {o.entity_key for o in actual.options}
                )
        # Wilson 95% interval: not an independent domain accuracy claim.
        interval = None
        if auto:
            z = 1.959963984540054
            p = tp / auto
            center = (p + z * z / (2 * auto)) / (1 + z * z / auto)
            half = (
                z * math.sqrt(p * (1 - p) / auto + z * z / (4 * auto * auto)) / (1 + z * z / auto)
            )
            interval = [max(0.0, center - half), min(1.0, center + half)]
        result[split] = dict(
            cases=len(records),
            correct_decisions=correct,
            decisions=dict(decisions),
            deterministic_auto_links=auto,
            true_positive=tp,
            false_positive=fp,
            precision=tp / auto if auto else None,
            recall=tp / expected_auto if expected_auto else None,
            precision_wilson_95=interval,
            review_count=review,
            review_rate=review / len(records),
            fuzzy_labelled_cases=fuzzy_total,
            fuzzy_top10_hit_rate=fuzzy_hit / fuzzy_total if fuzzy_total else None,
            fuzzy_auto_links=0,
        )
    return dict(
        classification="synthetic rule coverage; no demonstrated field precision or publication approval",
        total_cases=len(cases),
        splits=result,
        policy="fuzzy_auto_link_disabled",
    )
