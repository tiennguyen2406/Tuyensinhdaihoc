"""Explicit current-canonical queries; no release rebuild, cache or mutation path."""

from collections.abc import Callable
from datetime import date
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.engine import Connection

from services.api.catalog import cursor, dto
from services.api.db.models import metadata
from services.api.db.validators import TARGET_YEARS
from services.data.normalization.values import text
from services.data.publication.contract import canonical_decimal

t = metadata.tables
FIELDS = {
    "cutoff_scores": "id revision score max_score source_published_at effective_from system_valid_from primary_snapshot_id",
    "program_admissions": "id combination_id round_key population_key condition_text condition_dsl scoring_rule_id",
    "program_years": "id university_id program_id admission_year offering_code offering_name campus_code track_code language_code",
    "programs": "id program_name major_id",
    "universities": "id name university_code slug province_code university_type updated_at",
    "admission_methods": "id code name",
    "score_scales": "id code exam_version min_score max_score basis_description",
    "majors": "id name",
}
WARNINGS = [
    "Dữ liệu nội bộ còn thiếu; chưa đạt 20.000 cutoff hoặc nghiệm thu Phase 1.",
    "Năm trống là chưa thu thập/chưa xác minh, không có nghĩa trường không tuyển sinh.",
    "Chưa tính/so sánh điểm hoặc xác nhận trúng tuyển; điều kiện TTNV chỉ tại biên bằng cutoff.",
]


def facts(c: Connection, params: dict[str, Any], status: str = "verified") -> list[dict[str, Any]]:
    cut, scope, off, program, uni, method, scale, major = (t[n] for n in FIELDS)
    query = (
        sa.select(
            *(
                table.c[k]
                for name, columns in FIELDS.items()
                for table in [t[name]]
                for k in columns.split()
            )
        )
        .select_from(
            cut.join(scope, cut.c.program_admission_id == scope.c.id)
            .join(off, scope.c.program_year_id == off.c.id)
            .join(program, off.c.program_id == program.c.id)
            .join(uni, off.c.university_id == uni.c.id)
            .join(method, scope.c.method_id == method.c.id)
            .join(scale, cut.c.score_scale_id == scale.c.id)
            .outerjoin(major, program.c.major_id == major.c.id)
        )
        .where(
            cut.c.is_current.is_(True),
            cut.c.verification_status == status,
            scope.c.data_status == "published",
            off.c.admission_year == params["year"],
            off.c.admission_year.in_(TARGET_YEARS),
            uni.c.verification_status == "verified",
        )
    )
    for key, column in {
        "university_id": uni.c.id,
        "program_id": program.c.id,
        "program_year_id": off.c.id,
        "method": method.c.code,
        "campus": off.c.campus_code,
    }.items():
        if params.get(key) is not None:
            query = query.where(column == params[key])
    if "_university_ids" in params:
        query = query.where(uni.c.id.in_(params["_university_ids"]))
    result = [
        {name: {k: row[t[name].c[k]] for k in columns.split()} for name, columns in FIELDS.items()}
        for row in c.execute(query.order_by(cut.c.id)).mappings()
    ]
    if params.get("query"):
        key = text(params["query"]).search_key
        result = [
            r
            for r in result
            if any(
                key in text(str(v)).search_key
                for v in [
                    r["programs"]["program_name"],
                    r["program_years"]["offering_name"],
                    r["program_years"]["offering_code"],
                ]
            )
        ]
    return result


def sources(c: Connection, rows: list[dict[str, Any]]) -> list[dto.Source]:
    if not rows:
        return []
    snapshots = {r["cutoff_scores"]["primary_snapshot_id"] for r in rows}
    ids = [r["cutoff_scores"]["id"] for r in rows]
    ev, obs, snap, src = (
        t[n] for n in ["cutoff_evidence", "observations", "source_snapshots", "sources"]
    )
    locators: dict[UUID, set[str]] = {}
    for r in c.execute(
        sa.select(obs.c.snapshot_id, obs.c.record_locator)
        .select_from(ev.join(obs, ev.c.observation_id == obs.c.id))
        .where(ev.c.cutoff_id.in_(ids))
    ).mappings():
        snapshots.add(r["snapshot_id"])
        locators.setdefault(r["snapshot_id"], set()).add(
            r["record_locator"].split("/review:", 1)[0]
        )
    query = (
        sa.select(
            snap.c.id,
            snap.c.source_id,
            snap.c.source_title,
            snap.c.final_url,
            src.c.title,
            src.c.canonical_url,
            src.c.source_type,
        )
        .select_from(snap.join(src))
        .where(
            snap.c.id.in_(snapshots),
            src.c.verification_status == "verified",
            src.c.source_type.in_(
                ["university", "admission_office", "official_portal", "exam_organizer"]
            ),
        )
    )
    result = []
    for s in c.execute(query.order_by(snap.c.id)).mappings():
        url = s["final_url"] or s["canonical_url"]
        if urlsplit(url).scheme not in {"http", "https"}:
            continue
        locator_values: list[str | None] = list(sorted(locators.get(s["id"], set()))) or [None]
        for locator in locator_values:
            result.append(
                dto.Source(
                    snapshot_id=s["id"],
                    source_id=s["source_id"],
                    title=s["source_title"] or s["title"],
                    url=url,
                    locator=locator,
                    source_type=s["source_type"],
                )
            )
    return result


def offering(c: Connection, rows: list[dict[str, Any]]) -> dto.Offering:
    r = rows[0]
    off, p, u, m = (r[n] for n in ["program_years", "programs", "universities", "majors"])

    def unknown(value: str | None) -> str | None:
        return None if value in (None, "UNSPECIFIED") else value

    return dto.Offering(
        program_id=p["id"],
        program_name=p["program_name"],
        program_year_id=off["id"],
        offering_code=off["offering_code"],
        offering_name=off["offering_name"],
        year=off["admission_year"],
        university_id=u["id"],
        university_name=u["name"],
        campus=unknown(off["campus_code"]),
        track=unknown(off["track_code"]),
        language=unknown(off["language_code"]),
        major_id=m["id"],
        major_name=m["name"],
        method_codes=sorted({x["admission_methods"]["code"] for x in rows}),
        cutoff_count=len(rows),
        sources=sources(c, rows),
    )


def offerings(c: Connection, rows: list[dict[str, Any]]) -> list[dto.Offering]:
    grouped: dict[UUID, list[dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(r["program_years"]["id"], []).append(r)
    return [offering(c, group) for group in grouped.values()]


def cutoff(c: Connection, r: dict[str, Any]) -> dto.Cutoff:
    cut, scope, off, p = (
        r[n] for n in ["cutoff_scores", "program_admissions", "program_years", "programs"]
    )
    scale = r["score_scales"]
    dsl = scope["condition_dsl"]
    return dto.Cutoff(
        id=cut["id"],
        program_id=p["id"],
        program_year_id=off["id"],
        university_id=off["university_id"],
        program_name=p["program_name"],
        offering_code=off["offering_code"],
        offering_name=off["offering_name"],
        campus=None if off["campus_code"] == "UNSPECIFIED" else off["campus_code"],
        year=off["admission_year"],
        method=dto.Method(**r["admission_methods"]),
        score=canonical_decimal(cut["score"]),
        max_score=canonical_decimal(cut["max_score"]),
        scale=dto.Scale(
            **(
                scale
                | {
                    "min_score": canonical_decimal(scale["min_score"]),
                    "max_score": canonical_decimal(scale["max_score"]),
                }
            )
        ),
        basis_version=dsl.get("basis_version"),
        scope=dto.Scope(
            id=scope["id"],
            combination_id=scope["combination_id"],
            combination_status=dsl.get("combination_status"),
            round_key=scope["round_key"],
            population_key=scope["population_key"],
            condition_text=scope["condition_text"],
            conditions=dsl.get("conditions"),
            aggregation_basis=dsl.get("aggregation_basis"),
        ),
        revision=cut["revision"],
        computation_status="unavailable_aggregate_scope"
        if dsl.get("combination_status") == "source_aggregate"
        else "rule_available_not_evaluated"
        if scope["scoring_rule_id"]
        else "unavailable_rule",
        sources=sources(c, [r]),
        source_published_at=cut["source_published_at"],
        effective_from=cut["effective_from"],
        updated_at=cut["system_valid_from"],
    )


def coverage(c: Connection, params: dict[str, Any], rows: list[dict[str, Any]]) -> dto.Coverage:
    available = [year for year in TARGET_YEARS if facts(c, params | {"year": year})]
    return dto.Coverage(
        year=params["year"],
        canonical_cutoff_count=len(rows),
        university_count=len({r["universities"]["id"] for r in rows}),
        program_count=len({r["programs"]["id"] for r in rows}),
        offering_count=len({r["program_years"]["id"] for r in rows}),
        disputed_cutoff_count=len(facts(c, params, "disputed")),
        available_years=available,
        missing_years=[y for y in TARGET_YEARS if y not in available],
        computation_unavailable_count=sum(
            r["program_admissions"]["scoring_rule_id"] is None
            or r["program_admissions"]["condition_dsl"].get("combination_status")
            == "source_aggregate"
            for r in rows
        ),
    )


def version(c: Connection) -> int:
    return int(c.scalar(sa.select(t["catalog_state"].c.dataset_version)) or 0)


def meta(
    c: Connection, v: int, params: dict[str, Any], rows: list[dict[str, Any]]
) -> dict[str, Any]:
    release = (
        c.execute(
            sa.select(t["dataset_releases"].c.id, t["dataset_releases"].c.version).where(
                t["dataset_releases"].c.version == v
            )
        )
        .mappings()
        .one_or_none()
    )
    return dict(
        dataset_version=v,
        coverage=coverage(c, params, rows),
        warnings=WARNINGS,
        release=dto.Release(**dict(release)) if release else None,
    )


def page(
    items: list[Any],
    key: Callable[[Any], tuple[str, ...]],
    endpoint: str,
    params: dto.Pagination,
    v: int,
    metadata_values: dict[str, Any],
) -> dict[str, Any]:
    bind = cursor.binding(endpoint, params.model_dump())
    last = cursor.after(params.cursor, bind, v)
    ordered = sorted(items, key=key)
    if last:
        ordered = [x for x in ordered if key(x) > last]
    selected = ordered[: params.limit]
    more = len(ordered) > params.limit
    next_cursor = (
        cursor.token(
            dict(contract="cursor/1", binding=bind, dataset_version=v, after=key(selected[-1]))
        )
        if more
        else None
    )
    return metadata_values | dict(items=selected, has_more=more, next_cursor=next_cursor)


def university_rows(c: Connection, ident: UUID | None = None) -> list[dict[str, Any]]:
    uni = t["universities"]
    q = sa.select(*(uni.c[k] for k in FIELDS["universities"].split())).where(
        uni.c.verification_status == "verified"
    )
    if ident:
        q = q.where(uni.c.id == ident)
    return [dict(r) for r in c.execute(q).mappings()]


def university(
    c: Connection, u: dict[str, Any], year: int, rows: list[dict[str, Any]]
) -> dto.University:
    return dto.University(
        id=u["id"],
        name=u["name"],
        code=u["university_code"],
        slug=u["slug"],
        province=u["province_code"],
        type=u["university_type"],
        selected_year=year,
        data_status="verified" if rows else "not_collected_or_not_verified",
        program_count=len({r["programs"]["id"] for r in rows}),
        offering_count=len({r["program_years"]["id"] for r in rows}),
        cutoff_count=len(rows),
        updated_at=u["updated_at"],
        sources=sources(c, rows),
    )


def search_universities(c: Connection, params: dto.Universities) -> dict[str, Any]:
    v = version(c)
    values = params.model_dump()
    rows = facts(c, values | {"query": ""})
    unis = university_rows(c)
    key = text(params.query).search_key
    if key:
        alias = t["university_aliases"]
        approved = (
            c.execute(
                sa.select(alias.c.university_id, alias.c.alias).where(
                    alias.c.approved_by != "",
                    sa.or_(
                        alias.c.valid_from.is_(None),
                        alias.c.valid_from <= date(params.year, 12, 31),
                    ),
                    sa.or_(alias.c.valid_to.is_(None), alias.c.valid_to >= date(params.year, 1, 1)),
                )
            )
            .mappings()
            .all()
        )
        matched_aliases = {
            a["university_id"] for a in approved if key in text(a["alias"]).search_key
        }
        unis = [
            u
            for u in unis
            if u["id"] in matched_aliases
            or any(key in text(u[f]).search_key for f in ["name", "university_code"])
        ]
    candidate_ids = {u["id"] for u in unis}
    if params.method or params.campus:
        unis = [u for u in unis if any(r["universities"]["id"] == u["id"] for r in rows)]
    ids = {u["id"] for u in unis}
    rows = [r for r in rows if r["universities"]["id"] in ids]
    items = [
        university(c, u, params.year, [r for r in rows if r["universities"]["id"] == u["id"]])
        for u in unis
    ]
    return page(
        items,
        lambda x: (text(x.name).search_key, str(x.id)),
        "universities",
        params,
        v,
        meta(c, v, values | {"query": "", "_university_ids": candidate_ids}, rows),
    )


def require_university(c: Connection, ident: UUID) -> dict[str, Any]:
    rows = university_rows(c, ident)
    if not rows:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Không có trường này."})
    return rows[0]
