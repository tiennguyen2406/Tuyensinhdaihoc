"""Read-only advice foundation. Numeric threshold is independent of approval gates."""

from decimal import Decimal
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.engine import Connection

from services.api.catalog import dto, queries

t = queries.t


def threshold_page(candidates: Any, params: dto.AdviceParams, last: tuple[str, ...] | None) -> Any:
    """Filter before keyset/LIMIT; caller must supply eligibility-filtered IDs."""
    cut = t["cutoff_scores"]
    q = sa.select(cut.c.id.label("cutoff_id"), cut.c.score).where(
        cut.c.id.in_(candidates), cut.c.score < Decimal(params.score) + Decimal("1")
    )
    if last:
        q = q.where(cut.c.id > UUID(last[0]))
    return q.order_by(cut.c.id).limit(params.limit + 1)


def classified_candidates(params: dto.AdviceParams) -> Any:
    """One reason per fact; no rule or missing context silently becomes eligibility."""
    cut, scope, p = (t[n] for n in ("cutoff_scores", "program_admissions", "programs"))
    dsl = scope.c.condition_dsl
    combination = dsl["combination_status"].astext
    conditions = dsl["conditions"]
    reason = sa.case(
        (combination == "source_aggregate", "AGGREGATE_SCOPE"),
        (t["admission_methods"].c.code != params.method, "METHOD_MISMATCH"),
        (scope.c.score_scale_id != params.scale_id, "SCALE_MISMATCH"),
        (dsl["basis_version"].astext != params.basis_version, "BASIS_MISMATCH"),
        (
            sa.or_(
                sa.func.coalesce(dsl["basis_version"].astext, "") == "",
                sa.func.coalesce(combination, "").not_in(["specified", "confirmed_none"]),
                sa.func.coalesce(conditions["schema_version"].astext, "") != "conditions/1",
                sa.func.coalesce(conditions["kind"].astext, "").not_in(["none", "predicate"]),
                sa.and_(combination == "specified", scope.c.combination_id.is_(None)),
                sa.and_(combination == "confirmed_none", scope.c.combination_id.is_not(None)),
            ),
            "MISSING_CONTEXT",
        ),
        (conditions["kind"].astext == "predicate", "CONDITIONS_NOT_EVALUATED"),
        (scope.c.scoring_rule_id.is_(None), "UNAVAILABLE_RULE"),
        # No approved direct-total compatibility contract exists yet. In particular,
        # a rule UUID does not validate priority/weighting/eligibility/effective scope.
        else_="RULE_NOT_EVALUATED",
    )
    # Method is classified rather than silently filtered; physical filters define
    # the candidate universe, never include another year or unverified staging.
    values = params.model_dump() | {"method": None}
    q = queries.fact_query(values).with_only_columns(
        cut.c.id.label("cutoff_id"), reason.label("reason")
    )
    if params.major_id:
        q = q.join(p, t["program_years"].c.program_id == p.c.id).where(
            p.c.major_id == params.major_id
        )
    if params.combination_id:
        # Aggregate remains visible in diagnostics, never manufactured as a combination.
        q = q.where(
            sa.or_(
                scope.c.combination_id == params.combination_id, combination == "source_aggregate"
            )
        )
    return q


def search_advice(c: Connection, params: dto.AdviceParams) -> dict[str, Any]:
    v = queries.version(c)
    queries.checked_after(params, "advice", v)
    scale, method = t["score_scales"], t["admission_methods"]
    context = (
        c.execute(
            sa.select(scale, method.c.code.label("method_code"))
            .select_from(scale.join(method, scale.c.method_id == method.c.id))
            .where(scale.c.id == params.scale_id)
        )
        .mappings()
        .one_or_none()
    )
    unsupported = []
    if context is None:
        unsupported.append("SCALE_NOT_FOUND")
    else:
        if not context["min_score"] <= Decimal(params.score) <= context["max_score"]:
            raise HTTPException(
                422,
                detail={"code": "SCORE_OUT_OF_SCALE", "message": "Điểm nằm ngoài thang đã chọn."},
            )
        for matches, reason in [
            (context["admission_year"] == params.year, "CROSS_YEAR_UNSUPPORTED"),
            (context["method_code"] == params.method, "METHOD_MISMATCH"),
            (context["exam_version"] == params.exam_version, "EXAM_VERSION_MISMATCH"),
        ]:
            if not matches:
                unsupported.append(reason)
    candidates = classified_candidates(params).cte("advice_candidates")
    excluded: dict[str, int] = dict(
        c.execute(
            sa.select(candidates.c.reason, sa.func.count()).group_by(candidates.c.reason)
        ).all()
    )
    # No approved direct-total eligibility path exists. Numeric query development
    # is independent; do not execute it with an invented approval or bypass flag.
    return queries.meta(c, v, params.model_dump()) | dict(
        items=[],
        next_cursor=None,
        has_more=False,
        context=dto.AdviceContext(**params.model_dump(exclude={"limit", "cursor"})),
        status="unsupported" if unsupported or excluded else "no_data",
        unsupported_reasons=unsupported,
        excluded_summary=excluded,
        explanation="Chưa có dữ liệu/ngữ cảnh đủ căn cứ để tư vấn cá nhân. "
        "Ngưỡng đối chiếu là cutoff < S + 1, không có cận dưới; không bảo đảm trúng tuyển.",
    )
