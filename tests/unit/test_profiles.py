import pytest
from pydantic import ValidationError


def test_source_profile_rejects_outside_hosts_and_wrong_year():
    from services.api.source_profiles import SourceProfile

    base = dict(
        profile_id="fixture_only",
        university_key="TEST",
        allowed_hosts=["example.invalid"],
        seed_urls=["https://example.invalid/admissions"],
        years=[2024, 2025, 2026],
        parser="fixture-v1",
        authority_scope={"fact_kinds": ["cutoff"]},
    )
    assert SourceProfile.model_validate(base).verified is False
    with pytest.raises(ValidationError):
        SourceProfile.model_validate(base | {"seed_urls": ["https://outside.invalid/"]})
    with pytest.raises(ValidationError):
        SourceProfile.model_validate(base | {"years": [2023]})
    with pytest.raises(ValidationError):
        SourceProfile.model_validate(base | {"robots_policy": "ignore"})


def test_all_real_inventory_profiles_validate_and_schema_is_current():
    import json
    from pathlib import Path

    from services.api.source_profiles import SourceProfile

    paths = [p for p in Path("config/sources").glob("*.json") if p.name != "profile.schema.json"]
    # Versioned evidence/preflight profiles do not create additional universities.
    universities = {
        SourceProfile.model_validate_json(p.read_text(encoding="utf-8")).university_key
        for p in paths
    }
    assert 10 <= len(universities) <= 15
    for path in paths:
        profile = SourceProfile.model_validate_json(path.read_text(encoding="utf-8"))
        assert profile.verified is False
        assert all(
            "example" not in url.host and "invalid" not in url.host for url in profile.seed_urls
        )
    assert (
        json.loads(Path("config/sources/profile.schema.json").read_text())
        == SourceProfile.model_json_schema()
    )
