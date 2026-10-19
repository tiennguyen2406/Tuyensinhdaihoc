"""SQL canonical filtering/keysets/aggregates; hydrate only returned page entities."""

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
STATUSES: tuple[dto.YearStatus, ...] = (
    "unknown",
    "partial",
    "published",
    "verified",
    "not_collected",
)
WARNINGS = [
    "Dữ liệu nội bộ còn thiếu; chưa đạt 20.000 cutoff hoặc nghiệm thu Phase 1.",
    "Trạng thái năm tách khỏi xác minh từng cutoff; không chứng minh coverage đầy đủ.",
    "Năm trống là chưa thu thập/chưa xác minh, không có nghĩa trường không tuyển sinh.",
    "Chưa tính/so sánh điểm hoặc xác nhận trúng tuyển; điều kiện TTNV chỉ tại biên bằng cutoff.",
]


def literal_contains(column: Any, key: str) -> Any:
    pattern = "%" + key.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    return column.like(pattern, escape="\\")


def normalized_label(column: Any) -> Any:
    """Vietnamese fallback for Offering label/code, which have no normalized DDL column."""
    column = sa.func.replace(sa.func.replace(column, "\u200b", ""), "\ufeff", "")
    # Legacy display encodings; normalized Program identity remains the primary key.
    for encoded, decoded in (
        ("&amp;", "&"),
        ("&nbsp;", " "),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&#39;", "'"),
    ):
        column = sa.func.replace(column, encoded, decoded)
    column = sa.func.replace(sa.func.lower(column), "ß", "ss")
    return sa.func.regexp_replace(
        sa.func.regexp_replace(
            sa.func.normalize(sa.func.lower(sa.func.translate(column, "Đđ", "Dd")), sa.text("NFD")),
            "[\u0300-\u036f]",
            "",
            "g",
        ),
        "\\s+",
        " ",
        "g",
    )


def university_candidates(params: dict[str, Any]) -> Any:
    u, a, p, o = (t[n] for n in ["universities", "university_aliases", "programs", "program_years"])
    q = sa.select(u.c.id).where(u.c.verification_status == "verified")
    if params.get("university_id") is not None:
        q = q.where(u.c.id == params["university_id"])
    if params.get("program_id") is not None:
        q = q.where(u.c.id.in_(sa.select(p.c.university_id).where(p.c.id == params["program_id"])))
    if params.get("program_year_id") is not None:
        q = q.where(
            u.c.id.in_(sa.select(o.c.university_id).where(o.c.id == params["program_year_id"]))
        )
    key = text(params.get("university_query", "")).search_key
    if key:
        year = int(params.get("alias_year") or params["year"])
        alias_match = sa.exists(
            sa.select(a.c.id).where(
                a.c.university_id == u.c.id,
                a.c.approved_by != "",
                sa.or_(a.c.valid_from.is_(None), a.c.valid_from <= date(year, 12, 31)),
                sa.or_(a.c.valid_to.is_(None), a.c.valid_to >= date(year, 1, 1)),
                literal_contains(a.c.normalized_alias, key),
            )
        )
        q = q.where(
            sa.or_(
                literal_contains(u.c.normalized_name, key),
                literal_contains(sa.func.lower(u.c.university_code), key),
                alias_match,
            )
        )
    return q


def fact_query(params: dict[str, Any], *, disputed: bool = False) -> Any:
    """One row per cutoff; evidence never participates in filtering/pagination."""
    cut, s, o, p, m = (
        t[n]
        for n in [
            "cutoff_scores",
            "program_admissions",
            "program_years",
            "programs",
            "admission_methods",
        ]
    )
    q = sa.select(
        cut.c.id.label("cutoff_id"),
        o.c.id.label("offering_id"),
        o.c.program_id.label("program_id"),
        o.c.university_id.label("university_id"),
        o.c.admission_year.label("year"),
        cut.c.primary_snapshot_id,
        cut.c.verification_status.label("status"),
        m.c.code.label("method_code"),
        sa.or_(
            s.c.scoring_rule_id.is_(None),
            s.c.condition_dsl["combination_status"].astext == "source_aggregate",
        ).label("unavailable"),
    )
    q = q.select_from(
        cut.join(s, cut.c.program_admission_id == s.c.id)
        .join(o, s.c.program_year_id == o.c.id)
        .join(m, s.c.method_id == m.c.id)
    ).where(
        cut.c.is_current.is_(True),
        cut.c.verification_status.in_(["verified", "disputed"] if disputed else ["verified"]),
        s.c.data_status == "published",
        o.c.admission_year.in_(TARGET_YEARS),
        o.c.university_id.in_(university_candidates(params)),
    )
    if params.get("year") is not None:
        q = q.where(o.c.admission_year == params["year"])
    for key, column in {
        "program_id": o.c.program_id,
        "program_year_id": o.c.id,
        "method": m.c.code,
        "campus": o.c.campus_code,
    }.items():
        if params.get(key) is not None:
            q = q.where(column == params[key])
    key = text(params.get("query", "")).search_key
    if key:
        q = q.join(p, o.c.program_id == p.c.id)
        q = q.where(
            sa.or_(
                literal_contains(p.c.normalized_name, key),
                literal_contains(normalized_label(o.c.offering_name), key),
                literal_contains(normalized_label(o.c.offering_code), key),
            )
        )
    return q


def version(c: Connection) -> int:
    return int(c.scalar(sa.select(t["catalog_state"].c.dataset_version)) or 0)


def checked_after(params: Any, endpoint: str, v: int) -> tuple[str, ...] | None:
    last = cursor.after(params.cursor, cursor.binding(endpoint, params.model_dump()), v)
    if last:
        try:
            if len(last) != (1 if endpoint == "cutoffs" else 2):
                raise ValueError("arity")
            UUID(last[-1])
        except ValueError as error:
            raise HTTPException(422, detail={"code": "INVALID_CURSOR"}) from error
    return last


def page_result(
    items: list[Any], keys: list[tuple[str, ...]], params: Any, endpoint: str, v: int, more: bool
) -> dict[str, Any]:
    return dict(
        items=items,
        has_more=more,
        next_cursor=cursor.token(
            dict(
                contract="cursor/2",
                binding=cursor.binding(endpoint, params.model_dump()),
                dataset_version=v,
                after=keys[-1],
            )
        )
        if more
        else None,
    )


def coverages(c: Connection, params: dict[str, Any]) -> dict[int, dto.Coverage]:
    """Two aggregate SQL queries across all target years, no fact materialization."""
    values = params | {"alias_year": params["year"], "year": None}
    f = fact_query(values, disputed=True).subquery()
    verified = f.c.status == "verified"
    stats = {
        r["year"]: dict(r)
        for r in c.execute(
            sa.select(
                f.c.year,
                sa.func.count().filter(verified).label("canonical_cutoff_count"),
                sa.func.count(sa.distinct(f.c.university_id))
                .filter(verified)
                .label("university_count"),
                sa.func.count(sa.distinct(f.c.program_id)).filter(verified).label("program_count"),
                sa.func.count(sa.distinct(f.c.offering_id))
                .filter(verified)
                .label("offering_count"),
                sa.func.count().filter(f.c.status == "disputed").label("disputed_cutoff_count"),
                sa.func.count()
                .filter(sa.and_(verified, f.c.unavailable))
                .label("computation_unavailable_count"),
            ).group_by(f.c.year)
        ).mappings()
    }
    u = university_candidates(values).subquery()
    y = (
        sa.values(sa.column("year", sa.Integer), name="years")
        .data([(y,) for y in TARGET_YEARS])
        .alias("years")
    )
    ay = t["admission_years"]
    status = sa.func.coalesce(ay.c.status, "not_collected")
    statuses = {year: dict.fromkeys(STATUSES, 0) for year in TARGET_YEARS}
    for r in c.execute(
        sa.select(y.c.year, status.label("status"), sa.func.count().label("count"))
        .select_from(
            u.join(y, sa.true()).outerjoin(
                ay, sa.and_(ay.c.university_id == u.c.id, ay.c.admission_year == y.c.year)
            )
        )
        .group_by(y.c.year, status)
    ).mappings():
        statuses[r["year"]][r["status"]] = r["count"]
    available = [y for y in TARGET_YEARS if stats.get(y, {}).get("canonical_cutoff_count", 0)]
    names = (
        "canonical_cutoff_count",
        "university_count",
        "program_count",
        "offering_count",
        "disputed_cutoff_count",
        "computation_unavailable_count",
    )
    return {
        y: dto.Coverage(
            year=y,
            **{k: stats.get(y, {}).get(k, 0) for k in names},
            available_years=available,
            missing_years=[y for y in TARGET_YEARS if y not in available],
            admission_year_status_counts=statuses[y],
        )
        for y in TARGET_YEARS
    }


def meta(
    c: Connection,
    v: int,
    params: dict[str, Any],
    coverage_values: dict[int, dto.Coverage] | None = None,
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
        coverage=(coverage_values or coverages(c, params))[params["year"]],
        warnings=WARNINGS,
        release=dto.Release(**dict(release)) if release else None,
    )


def source_refs(
    c: Connection, selected: Any, owner: str, snapshot_id: UUID | None = None
) -> dict[UUID, list[dto.Source]]:
    """One source/evidence query restricted to page entities; no per-item DB calls."""
    f = selected.subquery()
    ev, obs, snap, src = (
        t[n] for n in ["cutoff_evidence", "observations", "source_snapshots", "sources"]
    )
    refs = sa.union_all(
        sa.select(
            f.c[owner].label("owner"),
            f.c.primary_snapshot_id.label("snapshot"),
            sa.cast(sa.null(), sa.Text).label("locator"),
        ),
        sa.select(f.c[owner], obs.c.snapshot_id, obs.c.record_locator).select_from(
            f.join(ev, f.c.cutoff_id == ev.c.cutoff_id).join(obs, ev.c.observation_id == obs.c.id)
        ),
    ).subquery()
    q = (
        sa.select(
            refs.c.owner,
            refs.c.locator,
            snap.c.id,
            snap.c.source_id,
            snap.c.source_title,
            snap.c.final_url,
            src.c.title,
            src.c.canonical_url,
            src.c.source_type,
        )
        .distinct()
        .select_from(
            refs.join(snap, refs.c.snapshot == snap.c.id).join(src, snap.c.source_id == src.c.id)
        )
        .where(
            src.c.verification_status == "verified",
            src.c.source_type.in_(
                ["university", "admission_office", "official_portal", "exam_organizer"]
            ),
        )
    )
    if snapshot_id:
        q = q.where(snap.c.id == snapshot_id).limit(1)
    grouped: dict[UUID, dict[tuple[str, str], dto.Source]] = {}
    for r in c.execute(q).mappings():
        url = r["final_url"] or r["canonical_url"]
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            continue
        locator = r["locator"].split("/review:", 1)[0] if r["locator"] else None
        ref = dto.Source(
            snapshot_id=r["id"],
            source_id=r["source_id"],
            title=r["source_title"] or r["title"],
            url=url,
            locator=locator,
            source_type=r["source_type"],
        )
        grouped.setdefault(r["owner"], {})[(str(r["id"]), locator or "")] = ref
    result = {}
    for ident, refs_by_key in grouped.items():
        located = {key[0] for key in refs_by_key if key[1]}
        result[ident] = [
            ref for key, ref in sorted(refs_by_key.items()) if key[1] or key[0] not in located
        ]
    return result


def university_rows(
    c: Connection,
    params: dict[str, Any],
    last: tuple[str, ...] | None = None,
    limit: int | None = None,
) -> list[Any]:
    u, ay = t["universities"], t["admission_years"]
    sort = u.c.normalized_name.collate("C")
    q = sa.select(
        *(u.c[k] for k in FIELDS["universities"].split()),
        sort.label("sort_key"),
        sa.func.coalesce(ay.c.status, "not_collected").label("data_status"),
    )
    q = q.select_from(
        u.outerjoin(
            ay, sa.and_(ay.c.university_id == u.c.id, ay.c.admission_year == params["year"])
        )
    ).where(u.c.id.in_(university_candidates(params)))
    if params.get("method") or params.get("campus"):
        f = fact_query(params).subquery()
        q = q.where(sa.exists(sa.select(f.c.cutoff_id).where(f.c.university_id == u.c.id)))
    if last:
        q = q.where(sa.tuple_(sort, u.c.id) > sa.tuple_(last[0], UUID(last[1])))
    q = q.order_by(sort, u.c.id)
    if limit is not None:
        q = q.limit(limit)
    return list(c.execute(q).mappings())


def university_items(
    c: Connection, rows: list[Any], params: dict[str, Any]
) -> list[dto.University]:
    if not rows:
        return []
    f = fact_query(params).subquery()
    ids = [u["id"] for u in rows]
    counts: dict[UUID, Any] = {
        r["university_id"]: r
        for r in c.execute(
            sa.select(
                f.c.university_id,
                sa.func.count(sa.distinct(f.c.program_id)).label("program_count"),
                sa.func.count(sa.distinct(f.c.offering_id)).label("offering_count"),
                sa.func.count().label("cutoff_count"),
            )
            .where(f.c.university_id.in_(ids))
            .group_by(f.c.university_id)
        ).mappings()
    }
    refs = source_refs(
        c, fact_query(params).where(t["program_years"].c.university_id.in_(ids)), "university_id"
    )
    return [
        dto.University(
            id=u["id"],
            name=u["name"],
            code=u["university_code"],
            slug=u["slug"],
            province=u["province_code"],
            type=u["university_type"],
            selected_year=params["year"],
            data_status=u["data_status"],
            updated_at=u["updated_at"],
            sources=refs.get(u["id"], []),
            **{
                k: counts.get(u["id"], {}).get(k, 0)
                for k in ("program_count", "offering_count", "cutoff_count")
            },
        )
        for u in rows
    ]


def search_universities(c: Connection, params: dto.Universities) -> dict[str, Any]:
    v = version(c)
    last = checked_after(params, "universities", v)
    values = params.model_dump() | {"university_query": params.query, "query": ""}
    rows = university_rows(c, values, last, params.limit + 1)
    selected = rows[: params.limit]
    return meta(c, v, values) | page_result(
        university_items(c, selected, values),
        [(r["sort_key"], str(r["id"])) for r in selected],
        params,
        "universities",
        v,
        len(rows) > params.limit,
    )


def university_detail(c: Connection, ident: UUID, year: int) -> dict[str, Any]:
    v = version(c)
    values = {"year": year, "university_id": ident}
    rows = university_rows(c, values)
    if not rows:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Không có trường này."})
    item = university_items(c, rows, values)[0]
    f, m = fact_query(values).subquery(), t["admission_methods"]
    methods = [
        dto.Method(**dict(r))
        for r in c.execute(
            sa.select(m.c.id, m.c.code, m.c.name)
            .where(m.c.code.in_(sa.select(f.c.method_code)))
            .order_by(m.c.code)
        ).mappings()
    ]
    return meta(c, v, values) | {"item": dto.UniversityDetail(**item.model_dump(), methods=methods)}


def admission_years(c: Connection, ident: UUID) -> dict[str, Any]:
    v = version(c)
    values = {"year": 2026, "university_id": ident}
    if not c.scalar(sa.select(sa.exists(university_candidates(values)))):
        raise HTTPException(404, detail={"code": "NOT_FOUND"})
    coverage_values = coverages(c, values)
    items = [
        dto.AdmissionYear(
            year=y,
            data_status=next(k for k, n in value.admission_year_status_counts.items() if n),
            cutoff_count=value.canonical_cutoff_count,
            offering_count=value.offering_count,
        )
        for y, value in coverage_values.items()
    ]
    return meta(c, v, values, coverage_values) | {"items": items}


def offering_rows(
    c: Connection,
    params: dict[str, Any],
    last: tuple[str, ...] | None = None,
    limit: int | None = None,
) -> list[Any]:
    f = fact_query(params).subquery()
    agg = (
        sa.select(
            f.c.offering_id,
            sa.func.count().label("cutoff_count"),
            sa.func.array_agg(sa.distinct(f.c.method_code)).label("method_codes"),
        )
        .group_by(f.c.offering_id)
        .subquery()
    )
    o, p, u, m = (t[n] for n in ["program_years", "programs", "universities", "majors"])
    sort = p.c.normalized_name.collate("C")
    q = sa.select(
        *(o.c[k] for k in FIELDS["program_years"].split()),
        p.c.program_name,
        m.c.id.label("major_id"),
        m.c.name.label("major_name"),
        u.c.name.label("university_name"),
        agg.c.cutoff_count,
        agg.c.method_codes,
        sort.label("sort_key"),
    )
    q = q.select_from(
        o.join(agg, agg.c.offering_id == o.c.id)
        .join(p, o.c.program_id == p.c.id)
        .join(u, o.c.university_id == u.c.id)
        .outerjoin(m, p.c.major_id == m.c.id)
    )
    if last:
        q = q.where(sa.tuple_(sort, o.c.id) > sa.tuple_(last[0], UUID(last[1])))
    q = q.order_by(sort, o.c.id)
    if limit is not None:
        q = q.limit(limit)
    return list(c.execute(q).mappings())


def offering_items(c: Connection, rows: list[Any], params: dict[str, Any]) -> list[dto.Offering]:
    if not rows:
        return []
    refs = source_refs(
        c,
        fact_query(params).where(t["program_years"].c.id.in_([r["id"] for r in rows])),
        "offering_id",
    )
    return [
        dto.Offering(
            program_id=r["program_id"],
            program_name=r["program_name"],
            program_year_id=r["id"],
            offering_code=r["offering_code"],
            offering_name=r["offering_name"],
            year=r["admission_year"],
            university_id=r["university_id"],
            university_name=r["university_name"],
            campus=None if r["campus_code"] == "UNSPECIFIED" else r["campus_code"],
            track=None if r["track_code"] == "UNSPECIFIED" else r["track_code"],
            language=None if r["language_code"] == "UNSPECIFIED" else r["language_code"],
            major_id=r["major_id"],
            major_name=r["major_name"],
            method_codes=sorted(r["method_codes"]),
            cutoff_count=r["cutoff_count"],
            sources=refs.get(r["id"], []),
        )
        for r in rows
    ]


def search_programs(c: Connection, params: dto.Programs) -> dict[str, Any]:
    v = version(c)
    last = checked_after(params, "programs", v)
    values = params.model_dump()
    rows = offering_rows(c, values, last, params.limit + 1)
    selected = rows[: params.limit]
    return meta(c, v, values) | page_result(
        offering_items(c, selected, values),
        [(r["sort_key"], str(r["id"])) for r in selected],
        params,
        "programs",
        v,
        len(rows) > params.limit,
    )


def program_detail(c: Connection, ident: UUID, year: int) -> dict[str, Any]:
    v = version(c)
    p, u, m = (t[n] for n in ["programs", "universities", "majors"])
    r = (
        c.execute(
            sa.select(p.c.id, p.c.program_name, p.c.university_id, p.c.major_id, m.c.name)
            .select_from(p.join(u).outerjoin(m))
            .where(p.c.id == ident, u.c.verification_status == "verified")
        )
        .mappings()
        .one_or_none()
    )
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND"})
    values = {"year": year, "program_id": ident}
    return meta(c, v, values) | {
        "item": dto.ProgramDetail(
            id=ident,
            name=r["program_name"],
            university_id=r["university_id"],
            selected_year=year,
            major_id=r["major_id"],
            major_name=r["name"],
            offerings=offering_items(c, offering_rows(c, values), values),
        )
    }


def cutoff(c: Connection, r: dict[str, Any], refs: list[dto.Source]) -> dto.Cutoff:
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
        sources=refs,
        source_published_at=cut["source_published_at"],
        effective_from=cut["effective_from"],
        updated_at=cut["system_valid_from"],
    )


def search_cutoffs(c: Connection, params: dto.Cutoffs) -> dict[str, Any]:
    v = version(c)
    last = checked_after(params, "cutoffs", v)
    values = params.model_dump()
    cut, scope, off, p, u, method, scale, major = (t[n] for n in FIELDS)
    # Materialize eligible IDs once: prevents a LIMIT-driven scan of all cutoff
    # rows for empty filters (observed 808k buffer hits on the 50k fixture).
    candidates = (
        fact_query(values)
        .with_only_columns(cut.c.id.label("cutoff_id"))
        .cte("page_candidates")
        .prefix_with("MATERIALIZED")
    )
    page_query = sa.select(candidates.c.cutoff_id)
    if last:
        page_query = page_query.where(candidates.c.cutoff_id > UUID(last[0]))
    rows: list[UUID] = list(
        c.scalars(page_query.order_by(candidates.c.cutoff_id).limit(params.limit + 1))
    )
    ids = rows[: params.limit]
    q = (
        sa.select(*(t[name].c[k] for name, columns in FIELDS.items() for k in columns.split()))
        .select_from(
            cut.join(scope, cut.c.program_admission_id == scope.c.id)
            .join(off, scope.c.program_year_id == off.c.id)
            .join(p, off.c.program_id == p.c.id)
            .join(u, off.c.university_id == u.c.id)
            .join(method, scope.c.method_id == method.c.id)
            .join(scale, cut.c.score_scale_id == scale.c.id)
            .outerjoin(major, p.c.major_id == major.c.id)
        )
        .where(cut.c.id.in_(ids))
        .order_by(cut.c.id)
    )
    selected = [
        {name: {k: row[t[name].c[k]] for k in columns.split()} for name, columns in FIELDS.items()}
        for row in (c.execute(q).mappings() if ids else [])
    ]
    refs = source_refs(c, fact_query(values).where(cut.c.id.in_(ids)), "cutoff_id") if ids else {}
    items = [cutoff(c, r, refs.get(r["cutoff_scores"]["id"], [])) for r in selected]
    return meta(c, v, values) | page_result(
        items, [(str(i),) for i in ids], params, "cutoffs", v, len(rows) > params.limit
    )


def data_coverage(c: Connection, params: dto.CoverageParams) -> dict[str, Any]:
    v = version(c)
    values = params.model_dump()
    coverage_values = coverages(c, values)
    return meta(c, v, values, coverage_values) | {"items": list(coverage_values.values())}


def source_detail(c: Connection, ident: UUID, year: int) -> dict[str, Any]:
    v = version(c)
    values = {"year": year}
    refs = source_refs(c, fact_query(values), "cutoff_id", snapshot_id=ident)
    if not refs:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": "Không có nguồn đã xác minh cho năm này."}
        )
    return meta(c, v, values) | {"item": next(iter(refs.values()))[0]}
