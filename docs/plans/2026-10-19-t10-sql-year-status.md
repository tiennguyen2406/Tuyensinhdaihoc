# T10 year status, SQL pagination and synthetic scale verification

Baseline204aedb on codex/crawler-pilot. Authorized implementation in current checkout;
preserve .vscode, private files, all business rows/release3. No facts/approval/crawler changes.

1. Capture34table per-PK/file digests and verify release3/count3/hash; inspect runtime.
2. RED regressions: partial admission_year + verified cutoff across list/detail/years/coverage;
   missing/unknown/published/verified year semantics. No DB status upgrade.
3. SQL predicates and stable keysets; limit+1 unique entity IDs before DTO/evidence;
   batch source/evidence by page IDs. SQL aggregate counts/coverage, same RO RR snapshot.
4. UI typed year status labels/examples and tests; preserve SSR/URL/stale-response guards.
5. Synthetic DB >=20k then50k if resources permit: retained DB, seed timing/size/config,
   baseline/new query counts, plans, warm latency,20concurrent users. No pilot fixtures.
6. Full backend/web checks, DEV HTTP/browser, release/history comparison, docs/WBS,
   commit/push and CI exact SHA. Report measured ceilings; propose T09 multi-source/T11 next.

## Contract delta

University/AdmissionYear.data_status is admission_years.status verbatim:
unknown/partial/published/verified; no row => not_collected. Facts count and each cutoff's
verification remain independent; even verified year does not assert all admissions collected.
Coverage adds admission_year_status_counts for candidate verified universities (identity search/
selected university/program/Offering parents), independent of fact availability/method/campus;
counts still reflect exactly filtered eligible canonical facts. All five status keys present.
Missing facts never means no admissions; no cross-year fallback.

Keep catalog/1 envelope, additive status details. Sort revision sql_keyset/2 and cursor/2:
universities normalized_name COLLATE C + UUID; Offerings parent Program normalized_name
COLLATE C + Offering UUID; cutoffs UUID. Explicitly reject old cursor/1 as
UNSUPPORTED_CURSOR (422, restart list). Signed binding includes endpoint/normalized filters/
limit/sort/version; validated immediately after version read, before DTO/sources/coverage.
Offering search uses existing programs.normalized_name plus exact/escaped literal substring
offering_code/name via deterministic PostgreSQL normalization expression (no extension/framework).
University/alias search uses existing normalized columns/trigram indexes; alias year intervals
overlap Jan1–Dec31, approved only. Literal %, _ and backslash are escaped for LIKE.

Parallel independent ownership: main backend/docs/DEV; frontend agent apps/web only;
benchmark agent scripts/tests benchmark utilities only, no services edits or pilot writes.
No index migration unless measured EXPLAIN/latency comparison proves need.
