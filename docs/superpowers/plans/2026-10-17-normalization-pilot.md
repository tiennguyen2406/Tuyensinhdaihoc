# T06 Versioned Normalization Implementation Plan

> For agentic workers: use superpowers:executing-plans task by task. The user explicitly requested direct implementation and commit/push after verification.

**Goal:** Normalize existing raw-only observations offline without overwriting evidence or publishing canonical facts.
**Architecture:** Pure normalize(observation, context), Decimal/text/date helpers and versioned DTOs. One new observation envelope per raw input reuses the extraction unique key with a normalization transform namespace. Candidate arrays reference physical cells; rejected attempts are separate, never counted as candidates. Batch persistence is atomic and serialized with PostgreSQL advisory transaction lock; completed results replay identically.
**Tech stack:** Existing Python, Pydantic, SQLAlchemy/PostgreSQL and stdlib only.
**Spec:** User T06 request supplied 2026-10-17; design sections 3.1–3.3 and existing parser/data contracts.

## Global constraints
- Keep branch codex/crawler-pilot and all old raw observations/migrations/jobs immutable.
- Target years 2024–2026; document year and academic year never supply missing admission year.
- No crawl/OCR, entity UUID resolution, fuzzy merge, scoring execution, canonical writes or dataset version/release changes.
- Decimal from strings; missing is not zero; ambiguous headers/methods/numbers block mapping.
- New output is unverified; aliases/resolver remain none. Input must have exact raw-only transform and empty normalized_fields.
- Namespace pins configuration/code digest; logic/config drift under the same version is rejected.

## Review focus
- Year-only headers and stale 2026 method context cannot supply a historical method.
- Score spans across columns/rows cannot duplicate a physical value or guess applicability.
- A generic assessment label mentioning both DGNL/DGTD cannot become one exam method.
- Related-document OCR/image warnings remain open without blocking unrelated explicit HTML cells.
- Concurrent runs, modified input and changed version must preserve all old envelopes and lineage.

## Tasks
- [x] Write failing golden tests for Unicode/Decimal/null/operators/ranges/money/date precision.
- [x] Implement pure lexical helpers without dependencies, run tests.
- [x] Write failing synthetic HTML mapping/lineage/spans/ambiguity/scope tests; implement DTOs and normalizer.
- [x] Write failing PostgreSQL immutable namespace/idempotency/version/atomicity tests; implement store and offline CLI.
- [x] Run real preview on the 215 raw inputs; inspect selected physical cells and all blocked reasons before persist.
- [x] Run complete suite, Ruff/format/mypy/lock/Alembic/diff; persist and replay unchanged results, verify invariants and health.
- [ ] Complete final staged review, commit/push and follow CI on exact SHA (actual outcome in handoff).

## Verification ledger

- Baseline98passed;49normalization +2parser regressions added; final full suite149passed in79.04s.
- Ruff/format/mypy/lock/Alembic checks passed; normalizer code/config frozen before first real persist.
- Three important snippet-review findings fixed via RED→GREEN, then full149tests. Reviewer coverage is snippets only; no deferred findings.
- Persisted215envelopes/95candidates, replay0new/cached; unchanged full-row raw/parse-job hashes, canonical/version/releases0 and health200.
- New HTML parser only dry-replayed, old215raw input rows untouched. No canonical/scoring/entity/crawl operations.
