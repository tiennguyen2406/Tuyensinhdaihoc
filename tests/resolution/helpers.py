"""Synthetic fixture identities/review records; never approved production entries."""

from uuid import NAMESPACE_URL, uuid5

from services.data.resolution.registry import EntityRegistry


def entity(key="u:a", kind="university", name="Đại học Mẫu Alpha", **extra):
    if kind == "offering":
        extra["attributes"] = {
            "campus": None,
            "track": None,
            "language": None,
            **extra.get("attributes", {}),
        }
    return dict(
        key=key,
        kind=kind,
        name=name,
        canonical_id=str(uuid5(NAMESPACE_URL, key)),
        review={
            "status": "approved",
            "reviewer": "SYNTHETIC TEST REVIEWER",
            "evidence": ["fixture://independent-expected"],
            "at": "2026-10-17",
        },
        **extra,
    )


def registry(entities=None, aliases=None):
    return EntityRegistry.model_validate(
        dict(
            version="registry/test/1",
            alias_version="aliases/test/1",
            classification="synthetic",
            entities=entities or [entity()],
            aliases=aliases or [],
        )
    )


def alias(key="alias:a", target="u:a", value="ĐH Mẫu A", **extra):
    return dict(
        key=key,
        target=target,
        value=value,
        kind="name",
        review={
            "status": "approved",
            "reviewer": "SYNTHETIC TEST REVIEWER",
            "evidence": ["fixture://alias"],
            "at": "2026-10-17",
        },
        **extra,
    )
