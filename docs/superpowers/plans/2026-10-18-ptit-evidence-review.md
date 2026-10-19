# PTIT T08 evidence review implementation plan

**Goal:** Prepare a verifiable human review batch for three THPT2024 candidates; no business approval or canonical write.
**Architecture:** Reuse frozen T05/T06/T07 packets, Crawler/Store/RawStorage, existing ReviewCommand and PostgreSQL role grants. Keep evidence outputs and credentials in ignored state/.
**Spec:** User request 2026-10-18; EduRadar Desktop Overview; publication and T05-T07 contracts.

## Constraints
- Existing pilot paused5/5; supplemental allocation max20 wire requests INCLUDING robots, redirects/retries/attachments. No budget increase.
- Read old raw first; only targeted official evidence via existing policy/transport, no alternative downloader or portal authentication.
- No overwrite of raw/envelopes/manifests; classify cache/fetch/role changes separately.
- Dedicated DEV logins are technical identities, never business approval. Passwords never in stdout/history/Git.
- No bootstrap/publication, T09, ScoreEngine, frontend or quota expansion.

## Tasks
- [x] Capture HEAD/schema/row-level before proof, verify six raw blobs and run baseline checks.
- [x] Inspect HTML cells/context/footnotes and cached PDF pages; construct per-field evidence inventory with real locators.
- [x] Use a narrow reviewed SourceProfile and a separate20request run to fetch only missing official documents. Stop when enough or budget exhausted. Record every request and snapshot digest.
- [x] Compare unresolved fields with spec/schema/validator; fix only proven defects with regression checks; otherwise document precise gaps.
- [x] Provision existing NOLOGIN groups/grants and dedicated reviewer/publisher DEV logins; protect ignored local credential storage; verify real least privileges, no business write.
- [x] Prepare private ReviewCommand drafts/readonly plans or explicit per-field blocker manifests; preserve previous packet files.
- [x] Verify old immutable rows/digests, request accounting, role rights and health. Update review report/workflow/private batch, stage reviewed public files, commit/push and check exact-SHA CI.

## Review focus
Budget cap across every HTTP hop; visual-only PDF evidence is not approval; 2026 page vs2024 cells; aggregate combination scope is not a wildcard; secrets and source outputs remain outside Git.

User explicitly authorized direct execution and requires a concrete final approval question only after preparation; no intermediate approval pause for this plan. Native execution in existing branch.

## Actual refinement and outcome
The initial run spent1 request but its frozen path filter excluded the nested2024 result. Its cap was reduced to1; a new frozen profile/run received only the remaining19. Combined cap20, used5, both paused. Review batch contains a concrete 10-operation identity/source bootstrap preview plus evidenced cutoff gaps; no business apply. Exact commit/CI result is reported in handoff after push.
