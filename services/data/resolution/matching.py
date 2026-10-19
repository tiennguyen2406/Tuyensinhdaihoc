"""Deterministic code/approved-alias matching; fuzzy is always a review suggestion."""

from difflib import SequenceMatcher
from typing import Any

from services.data.normalization.values import text
from services.data.resolution.contract import EntityMatch, EntityQuery, Option
from services.data.resolution.registry import EntityRegistry


def exact(value: str) -> str:
    return text(value).display.casefold()


def similarity(a: str, b: str) -> float:
    a, b = (" ".join(sorted(text(v).search_key.split())) for v in (a, b))
    return SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else 0.0


def validity(start: int | None, end: int | None, year: Any) -> tuple[list[str], list[str]]:
    if start is None and end is None:
        return [], []
    if year is None:
        return [], ["validity_year_unknown"]
    return (
        ["validity_year_conflict"]
        if (start is not None and year < start) or (end is not None and year > end)
        else []
    ), []


def match(query: EntityQuery, registry: EntityRegistry, *, allow_link: bool = True) -> EntityMatch:
    if query.kind in {"program", "offering", "scope"} and not query.university_key:
        return EntityMatch(kind=query.kind, reasons=["UNIVERSITY_REQUIRED"])
    if query.kind == "offering" and (
        not query.program_key or query.attributes.get("admission_year") is None
    ):
        return EntityMatch(kind=query.kind, reasons=["OFFERING_PARENT_YEAR_REQUIRED"])
    options = []
    blocked_entities: dict[str, list[str]] = {}
    approved_name_targets = {
        e.key
        for e in registry.entities
        if e.kind == query.kind
        and e.review.status == "approved"
        and query.name
        and exact(query.name) == exact(e.name)
    }
    if query.name:
        approved_name_targets.update(
            a.target
            for a in registry.aliases
            if a.review.status == "approved"
            and registry.entry(a.target).kind == query.kind
            and a.kind in {"name", "short_name"}
            and exact(a.value) == exact(query.name)
            and not validity(a.from_year, a.to_year, query.attributes.get("admission_year"))[0]
            and (not a.university_key or a.university_key == query.university_key)
        )
    approved_domain_targets = {
        e.key
        for e in registry.entities
        if e.kind == query.kind
        and e.review.status == "approved"
        and query.domain
        and query.domain in e.domains
    }
    approved_domain_targets.update(
        a.target
        for a in registry.aliases
        if a.review.status == "approved"
        and registry.entry(a.target).kind == query.kind
        and a.kind == "domain"
        and query.domain == a.value
    )
    fatal_code_conflict = False
    for e in registry.entities:
        if e.kind != query.kind or e.review.status == "revoked":
            continue
        # Blocking never interprets missing metadata as a mismatch.
        if query.university_key and e.university_key and query.university_key != e.university_key:
            blocked_entities[e.key] = ["university_key"]
            continue
        if query.program_key and e.program_key and query.program_key != e.program_key:
            blocked_entities[e.key] = ["program_key"]
            continue
        features: dict[str, Any] = {}
        conflicts = []
        missing = []
        identity_fields = {
            "admission_year",
            "campus",
            "language",
            "track",
            "training_mode",
            "province",
        }
        for key in sorted((set(query.attributes) | set(e.attributes)) & identity_fields):
            attr_a, attr_b = query.attributes.get(key), e.attributes.get(key)
            features[key] = (
                "unknown"
                if attr_a is None or attr_b is None
                else "match"
                if attr_a == attr_b
                else "conflict"
            )
            if query.kind == "offering" and attr_a is not None and attr_b is None:
                missing.append(key + "_canonical_context_unknown")
            if attr_a is not None and attr_b is not None and attr_a != attr_b:
                conflicts.append(key)
        if conflicts:
            blocked_entities[e.key] = list(conflicts)
            continue
        domain_match = bool(query.domain and query.domain in e.domains)
        if query.domain and e.domains and not domain_match:
            conflicts.append("domain")
        features["domain"] = (
            "match"
            if domain_match
            else "unknown"
            if not query.domain or not e.domains
            else "conflict"
        )
        codes = [c for c in e.codes if c.value == query.code and c.system == query.code_system]
        if codes:
            if approved_name_targets and e.key not in approved_name_targets:
                conflicts.append("approved_name_identity")
            good = []
            for code in codes:
                bad, absent = validity(
                    code.from_year, code.to_year, query.attributes.get("admission_year")
                )
                bad += [
                    k
                    for k, v in code.attributes.items()
                    if v is not None
                    and query.attributes.get(k) is not None
                    and query.attributes[k] != v
                ]
                absent += [
                    k + "_unknown"
                    for k, v in code.attributes.items()
                    if v is not None and query.attributes.get(k) is None
                ]
                if not bad:
                    good.append((code, absent))
            if good:
                missing.extend(min(good, key=lambda binding: len(binding[1]))[1])
            else:
                conflicts.append("code_validity_or_scope")
            if conflicts:
                fatal_code_conflict = True
        elif query.code:
            missing.append("code_not_confirmed_in_system")
            if any(c.system == query.code_system for c in e.codes):
                conflicts.append("code")
        aliases = []
        alias_score = 0.0
        alias_keys = []
        for a in registry.aliases:
            if a.target != e.key or a.review.status == "revoked":
                continue
            if a.university_key and a.university_key != query.university_key:
                continue
            bad, absent = validity(a.from_year, a.to_year, query.attributes.get("admission_year"))
            if bad or any(
                query.attributes.get(k) is not None and v is not None and query.attributes[k] != v
                for k, v in a.attributes.items()
            ):
                continue
            hit = (
                (
                    a.kind in {"name", "short_name"}
                    and query.name is not None
                    and exact(query.name) == exact(a.value)
                )
                or (a.kind == "domain" and query.domain == a.value)
                or (
                    a.kind == "legacy_code"
                    and query.code == a.value
                    and query.code_system == a.code_system
                )
            )
            if query.name and a.review.status == "approved":
                alias_similarity = similarity(query.name, a.value)
                alias_score = max(alias_score, alias_similarity)
                if alias_similarity > 0:
                    alias_keys.append(a.key)
            if hit:
                aliases.append(a)
                alias_keys.append(a.key)
                missing.extend(absent)
                missing.extend(
                    k + "_unknown"
                    for k, v in a.attributes.items()
                    if v is not None and query.attributes.get(k) is None
                )
        approved_legacy = any(
            a.review.status == "approved" and a.kind == "legacy_code" for a in aliases
        )
        if approved_legacy:
            conflicts = [k for k in conflicts if k != "code"]
            missing = [k for k in missing if k != "code_not_confirmed_in_system"]
            if approved_name_targets and e.key not in approved_name_targets:
                conflicts.append("approved_name_identity")
            if conflicts:
                fatal_code_conflict = True
        approved_alias = any(a.review.status == "approved" for a in aliases)
        if (
            (codes or approved_alias)
            and approved_domain_targets
            and e.key not in approved_domain_targets
        ):
            conflicts.append("other_registered_domain_identity")
            fatal_code_conflict = True
        name_exact = bool(query.name and exact(query.name) == exact(e.name))
        name_score = similarity(query.name or "", e.name)
        context_values = [1.0 for k, v in features.items() if v == "match"]
        context_score = sum(context_values) / len(context_values) if context_values else 0.0
        method = (
            "exact_code"
            if codes
            else "approved_alias"
            if approved_alias
            else "contextual_match"
            if name_exact or domain_match or aliases
            else "fuzzy_suggestion"
        )
        if method == "fuzzy_suggestion" and name_score < 0.5:
            continue
        features.update(
            name_similarity=name_score,
            alias_similarity=alias_score,
            context_score=context_score,
            code_system=query.code_system,
            review_status=e.review.status,
        )
        score = round(0.60 * name_score + 0.25 * alias_score + 0.15 * context_score, 10)
        context_auto = name_exact and domain_match and query.kind == "university"
        auto = (
            allow_link
            and e.review.status == "approved"
            and not conflicts
            and not missing
            and (method in {"exact_code", "approved_alias"} or context_auto)
        )
        options.append(
            Option(
                entity_key=e.key,
                proposal_key=e.key if e.canonical_id is None else None,
                canonical_id=e.canonical_id,
                method=method,
                score=score,
                features=features,
                conflicts=conflicts,
                missing=missing,
                eligible=not conflicts,
                auto_eligible=auto,
                alias_keys=sorted(set(alias_keys)),
                evidence=e.review.evidence
                + [v for a in aliases for v in a.review.evidence]
                + [v for c in codes for v in c.evidence],
            )
        )
    ranks = {"exact_code": 0, "approved_alias": 1, "contextual_match": 2, "fuzzy_suggestion": 3}
    options.sort(key=lambda o: (not o.eligible, ranks[o.method], -o.score, o.entity_key))
    options = options[:10]
    margin = round(options[0].score - options[1].score, 10) if len(options) > 1 else None
    result = EntityMatch(
        kind=query.kind,
        options=options,
        margin=margin,
        reasons=["REVIEW_REQUIRED"],
        blocked_entities=blocked_entities,
    )
    if fatal_code_conflict:
        return result.model_copy(
            update={"status": "ambiguous", "reasons": ["CODE_CONTEXT_CONFLICT"]}
        )
    eligible = [o for o in options if o.eligible]
    if not eligible:
        return result
    top = eligible[0]
    peers = [o for o in eligible if ranks[o.method] == ranks[top.method]]
    ambiguous = len(peers) > 1 and (
        top.method != "fuzzy_suggestion"
        or (
            top.features["name_similarity"] >= 0.85
            and peers[1].features["name_similarity"] >= 0.85
            and abs(top.score - peers[1].score) < 0.08
        )
    )
    if ambiguous:
        return result.model_copy(
            update={"status": "ambiguous", "reasons": ["MULTIPLE_MATCHES_OR_FUZZY_TIE"]}
        )
    if top.auto_eligible and top.method != "fuzzy_suggestion":
        return result.model_copy(
            update={
                "status": "resolved",
                "entity_key": top.entity_key,
                "canonical_id": top.canonical_id,
                "method": top.method,
                "reasons": [],
            }
        )
    return result
