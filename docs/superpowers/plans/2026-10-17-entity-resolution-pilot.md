# T07 entity resolution pilot implementation plan

**Spec:** User T07 request, EduRadar section3.4, existing T05/T06 contracts.
**Goal:** Resolve each T06 candidate against a versioned, auditable registry without modifying old evidence or publishing.
**Architecture:** Pure registry/query matcher + envelope adapter; JSON registry candidates and reviewed aliases separated from canonical DB identities. Existing observations and ingest_jobs hold immutable derived resolution envelopes/manifests; no migration or dependency required. stdlib token-sort SequenceMatcher scoring is explicitly versioned and fuzzy never auto-links.

| Requirement | Existing module | Addition | Acceptance |
|---|---|---|---|
| Candidate lineage | normalization.contract | resolution contract wrapping envelope UUID and candidate key | lineage/input tamper tests |
| University/major/program/offering/method/scope separation | DB models + source profiles | registry DTO, scoped codes, approvals/validity and pending proposals | synthetic gold280cases incl three Bách khoa/BVH/BVS |
| Deterministic then fuzzy review | normalization.values.text | typed blocking/matcher, top10/features/margin/conflicts | held-out decisions separate from calibration |
| Version/replay | normalization.store + observations/jobs | pinned T06 job membership/digests; atomic resolution namespace and affected lookup | PostgreSQL idempotency/concurrency/version/rollback |
| Pilot/statistics | existing offline CLI pattern | resolution preview/run/replay/affected/evaluate | actual95candidates, freeze original430rows/jobs |
| Handoff | README/reports + CI | contract/report, reviewed commit/push | fullchecks/health/CIexactSHA |

## Constraints

- Keep codex/crawler-pilot, existing migrations, all430observations, review states and crawl paused budget5/5 unchanged.
- Use T06 job7bc439bf-a6d7-4beb-bf03-bb47956c5383 after verification. Only its normalization output envelopes are input, not raw or resolver output.
- Live catalogs empty; registry proposals remain pending with canonical_id=null. No forged approval/reviewer. Actual source names/program outputs stay private except curated registry identity metadata.
- Code system/owner/year/campus/track/language/form constraints; missing is unknown. No major/offering-code equivalence or program global-name key.
- No fuzzy auto-link, scoring/conversion/scale inference, publisher or canonical/catalog/release writes.
- Preserve all earlier manifests, including lock digest; use existing stdlib so lock does not change.

## Tasks
- [x] Read/verify baseline, full old-row/jobs/crawl hashes and reference schema.
- [x] Write RED registry/matcher/gold tests then implement DTO/validation/matching.
- [x] Write RED envelope/proposal tests then implement pure resolve adapter and pending pilot registry.
- [x] Write RED DB namespace/idempotency/tamper/replay tests; implement store/CLI and impact lookup.
- [x] Evaluate280independently labelled synthetic gold cases, calibration/evaluation split; no claim of real-world precision.
- [x] Preview real pilot, inspect evidence/options, full149baseline+newtests/lint/type/lock/Alembic, review code with honest coverage.
- [x] Persist/replay and compare immutable baselines, health, finalize documentation.
Delivery: commit/push and exact-SHA CI are verified separately in the final handoff.

Implementation/pilot verified; commit/push/CI remain delivery steps until exact-SHA result is read. T07 business approvals remain pending; see docs/reports/entity-resolution-pilot.md.
