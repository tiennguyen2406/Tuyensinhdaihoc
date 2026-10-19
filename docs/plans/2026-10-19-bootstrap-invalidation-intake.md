# Bootstrap serving invalidation and bounded multisource intake

> For agentic workers: execute the existing-flow changes with TDD and independent agent ownership; no new subsystem or approval workflow.

Goal: make bootstrap invalidation match the live T10 serving surface, then carry one additional official source through raw/T05/T06/T07 into an actionable private review batch without approving or publishing it.

Spec: schema-provenance.md, data/parser/normalization/entity-resolution/publication/catalog/release contracts; WBS T01–T19; reports/t10-sql-year-status.md; plans/2026-10-19-t09-multisource-next.md.

Architecture: reuse ReviewService's transaction/outbox and current SQL catalog. A shared serving-change predicate examines actual bootstrap effects rather than the existence of cutoffs. Intake uses the existing downloader/frontier/raw storage and immutable parser/normalizer/resolver namespaces. Only a small evidence-backed adapter delta is permitted if a real source requires it.

Constraints: branch codex/crawler-pilot baseline511290f; preserve .vscode/private history/release3. No business bootstrap/approval/publication on DEV, no new canonical facts/version/release, no T12/T13/Score/SNA/merge/deploy. HTTP task budget30 including robots/discovery/redirect/retry, maximum2 university candidates, one request/host,<=0.5rps/maxburst1. Root alone issues external requests; prior task runs must be paused/needs_review before allocating a new run, whose ceiling cannot exceed30 minus summed requests_used. Unspent ceilings are not wire requests and cannot be automatically resumed. No DB/file deletion or global configuration changes. Synthetic tests only in separate retained DBs; no50k benchmark rerun.

## Work and verification

- [x] Capture baseline34table/file digests, runtime/resources, verify release3 hash/count and origin.
- [x] RED PostgreSQL regressions: verified university without cutoffs, admission-year addition, approved alias without cutoffs, request replay, internal-only metadata; observe API/cursor before/after.
- [x] Implement common serving-change policy for plan/apply/related mutations, one version bump and refresh per bootstrap transaction, rollback/idempotency tests. Document old assertions' actual deltas.
- [x] Inspect real candidate profiles offline; preflight exact official host, preserve frozen profile versions. Select primary/fallback from at most2 universities based on downloaded evidence, cutoff vs threshold distinction and supported format.
- [x] Keep request ledger across all runs with sum requests_used<=30 and only one active run, allocated no more than global remaining; no uncontrolled discovery worker or old-run resume. Inspect cached links before narrowing any next profile; new document host only with cached relationship evidence. Actual17/30, allruns paused.
- [x] Run existing T05/T06/T07 versioned workflows on real snapshots, preserve raw/header/year/locator/footnotes and unknown semantic fields. Existing parser used; actual9catalog envelopes remain0typedcandidates, not cutoff success.
- [ ] Obtain5–10 typed cutoff packets and materializable review plans: blocked by actual format/access. A private9record staging-gate batch exists with all lineage/blockers; no T08candidate bindings/parents or claimed plan success.
- [x] Replay each new namespace, compare original rows/files and PTIT facts; explain new raw/jobs/observations metadata deltas separately. Verify release3 and catalog3 again.
- [ ] Full CI checks/tests/backend and frontend, DEV health/lookup, docs/WBS/report, secret diff check, commit/push, exact-SHA CI. Keep500ms SLO unmet and next T09/T11/T12 gates explicit.

Review focus: registry pending is not approval; technical eligible is not source authority; source_aggregate stays one fact; missing scale/basis/year/campus stays blocked; historical results/approvals/releases remain immutable. Independent ownership: serving agent publication/tests, inventory agent offline only, root intake/docs/operations.
