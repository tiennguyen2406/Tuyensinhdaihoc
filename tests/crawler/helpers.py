from services.api.source_profiles import SourceProfile


def profile(**updates):
    values = dict(
        profile_id="test",
        university_key="TEST_ONLY",
        allowed_hosts=["example.edu.vn"],
        seed_urls=["https://example.edu.vn/"],
        years=[2025],
        authority_scope={"years": [2025]},
        parser="raw_http",
        review_status="eligible",
        robots_status="allowed",
        review_evidence=["Synthetic offline fixture"],
        access_basis="Synthetic offline fixture",
        snapshot_basis="Synthetic fixture; no real admissions data",
    )
    return SourceProfile.model_validate(values | updates)
