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
