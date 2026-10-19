# T09 fixes → T10 internal catalog slice

Authorized scope: fix two reviewed T09 defects, then live canonical PostgreSQL lookup +
Next.js/TypeScript/pnpm internal DEV UI. Keep release3 bytes/hash/provenance, facts,
approvals, `.vscode/`, raw/private data; no crawl/score/SNA/production/merge.

## Execution

1. [x] Check baseline5bbafa5, spec SHA c3745329…04c5, 34table/file digests, release3/count3/hash.
2. [x] T09 RED→GREEN: non-NULL combination joins subject_code→subjects.code in position
   order; compatible old builder verifies under schema contract. Unsupported schema and
   bad hash still fail. Verify/replay existing DEV release; never build a replacement.
3. [x] Backend typed DTO/query/router with read-only REPEATABLE READ per response;
   fixtures synthetic PostgreSQL only, live publication race/cursor/fan-out/DTO tests.
4. [x] apps/web SSR search→university→Offering cutoff, URL year/filter, AbortController
   + query identity for interactive changes; unit/component + Playwright + mobile/keyboard.
5. [ ] Backend full checks/tests and frontend lint/type/tests/build/E2E; DEV HTTP/browser;
   historical DB/files/release verification, docs/WBS, commit/push and CI exact SHA.

Parallelism after shared contract: primary owns backend and CI/runbook; separate focused
agent owns T09 fixes first, then frontend agent owns apps/web only. No shared edits or
pilot fixture writes. Independent final review before commit.

## API contract `catalog/1`

Prefix `/api/v1`. Every response opens one READ ONLY REPEATABLE READ transaction before
reading catalog version and all relevant rows. `dataset_version` is live serving version;
`release` is `{id,version}` only when a registered release has that exact version, else null.
No release3 binding for serving4. Old release stays independently verifiable.

All lists: `{items,next_cursor,has_more,dataset_version,coverage,warnings,release,contract_version}`.
Detail uses `{item,dataset_version,coverage,warnings,release,contract_version}`.
`coverage`: selected `year`, canonical_cutoff_count, university_count, program_count,
offering_count, available_years, missing_years, tuition_status/scholarship_status="not_available_in_slice",
computation_unavailable_count. Empty year means not collected/not verified, never no admissions.
Warnings communicate incomplete internal data, no evaluation/admission guarantee.

| Endpoint | Accepted filters / content |
|---|---|
| GET /universities | year required2024–26, query (name/code/approved alias normalized accents), method,campus,limit,cursor |
| GET /universities/{id} | year required; summary + methods, selected-year counts/sources |
| GET /universities/{id}/admission-years | target years2024–26 with status/counts |
| GET /programs | year required,university_id,method,campus,query,limit,cursor; items are Offering DTOs with separate program_id/program_year_id |
| GET /programs/{id} | canonical Program UUID + year required; identity and current-year offerings |
| GET /cutoffs | year required,university_id,program_id,program_year_id,method,campus,limit,cursor |
| GET /data-coverage | year required,university_id,method,campus; list of per-year coverage rows, envelope coverage for selected year |
| GET /sources/{snapshot_id} | year required; safe source metadata only if linked to eligible facts in year |

Unknown filters rejected422, UUID invalid422/valid missing404; no results200. Missing year422.
Sort stable by normalized display/name + UUID (cutoffs by UUID). limit50/max200. HMAC-SHA256
opaque cursor binds endpoint/normalized filters/sort tuple/limit/catalog version; tampering
or filter mismatch422, valid cursor after version change409 DATASET_CHANGED.
Secret via CATALOG_CURSOR_SECRET; internal single-process DEV can use ephemeral random key
when unset (restart invalidates cursors); runbook uses persisted private key for stable DEV.

DTO allowlist, Decimal strings, no raw bodies/paths/jobs/audit/review reasons. Only current
verified cutoffs of published scopes and requested target year. Evidence via separate scoped
lookup, no join fanout. Programs/Offering distinct; Major/track/language nullable. Tuition/
scholarship null with explicit not-available status, no cross-year fallback. Aggregate condition
DSL/TTNV retained and computation unavailable_aggregate_scope, no score form/evaluator.

Out of slice filters: province/type/verification switches, major/combination/language/track,
fee/currency/scholarship/facility filters, score ranges, fuzzy/trigram ranking and historical
revision browsing; rejected rather than ignored. No new cache/repository framework.

## Shared frontend DTOs

University: id,name,code,slug,province,type,selected_year,data_status,program_count,
offering_count,cutoff_count,updated_at,sources; detail adds methods[{id,code,name}].
Offering: program_id,program_name,program_year_id,offering_code,offering_name,year,
university_id,university_name,campus,track,language,major_id,major_name,method_codes,
cutoff_count,tuition:null,scholarships:null,sources.
Program detail: id,name,university_id,selected_year,major_id,major_name,offerings.
Cutoff: id,program_id,program_year_id,university_id,program_name,offering_code,offering_name,
campus,year,method{id,code,name},score,max_score,scale{id,code,exam_version,min_score,
max_score,basis_description},basis_version,scope{id,combination_id,combination_status,
round_key,population_key,condition_text,conditions,aggregation_basis},revision,
verification_status,computation_status,sources,source_published_at,effective_from,updated_at.
Source: snapshot_id,source_id,title,url,locator,source_type. No private storage URI.

UI: `/universities?year=2024&query=...`, `/universities/{uuid}?year=2024&campus=...&method=...`.
Server initial fetch no-store; client interactive results cleared immediately on query change,
fetch abort + identity guard; year/filter maintained in URL. Detail shows Offering cards then
cutoff table with scale/basis, TTNV equality notice and sources. Mobile/keyboard/empty/error/
loading states; no synthetic data in DEV database.
