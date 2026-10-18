# T08 reviewed transactional publication — implementation plan

User supplied execution scope: implement directly in current codex/crawler-pilot, preserve T05–T07 and paused crawl; no real approval without responsible reviewer. Existing architecture modular monolith with SQLAlchemy Core, PostgreSQL, observations/jobs and pure T07 registry. Use existing dependencies.

## Interfaces and files

- services/data/publication/contract.py: frozen Binding, BootstrapOperation, CutoffSpec, ReviewCommand, ValidatedDraft, PublicationResult; Decimal JSON strings, no floats; canonical admission/fact/bundle fingerprints.
- packets.py: list/inspect actual T07 candidate packets, verify complete T06/T07 manifest lineage/digests; immutable binding includes input rows/snapshot/source and versions.
- access.py: database session_user identity, non-superuser reviewer/publisher membership; no caller-supplied actor. Local trusted CLI only, no HTTP mutation; separate least-privilege NOLOGIN group roles provisioned explicitly by operator.
- bootstrap.py: reviewed create/link operations, existing canonical constraints/validators, source authority and scale evidence, ordered parent refs, immutable registry/alias version job; no UUID-before-create cycle.
- review.py: read-only plan and permission-checked apply/revoke; immutable decisions stored in ingest_jobs with audits; expected current registry/alias versions and full packet digests.
- publish.py: validate approved decision again, scoped source/scale/evidence checks, scope creation, equality/expected revision/correction/conflict; insert-only verified evidence envelope, audit/version/refresh jobs atomic.
- __main__.py: list/inspect/plan/apply/replay; sensitive input/output files outside Git.
- additive 0003_publication: append-only audit/decision/registry manifests; protect T08-managed canonical history against UPDATE/DELETE, permit audited retire/dispute/withdraw only. Keep legacy migrations unchanged. No new tables needed.
- scripts/provision_publication_roles.py: explicit owner-run role grants without creating login/password or silently changing local .env.
- tests/publication/: genuine non-superuser connections in separate PostgreSQL test DB; end-to-end fixtures tagged TEST ONLY, never project pilot approvals.

## Gates

Cutoff: required university/offering/year/method, reviewed combination or confirmed-none, round/population/conditions, verified scale/basis/authority and exact cell value. Major optional per DDL. Scoring rule optional for publishing a sourced fact, but missing rule => calculation/comparison unavailable. No inferred MAIN/GENERAL/none conditions.
Tuition: offering nullable, admission_year required by existing DDL; academic-year-only group pilot remains blocked instead of inventing cohort/year. Scholarship/exam/scoring/conversion remain review-only in this cutoff publisher slice; typed gates documented separately, no false completion of all T08.

## Steps / tests (RED → GREEN)

1. Re-run 461 baseline; capture full-row invariants for all existing observations/jobs/catalogs/crawl.
2. Write failing packet digest/Decimal/fingerprint/actor tests, implement contracts/packet/auth.
3. Write failing bootstrap/review authorization/pending/revoked/stale/parent tests; implement create/link + immutable version audit and actual non-superuser test roles.
4. Write failing publication cases: first scope, 3-source evidence, replay/race, corrections/stale expected, late press/official conflict, basis replacement, money independence, validation failures and rollback of facts/evidence/audit/version/jobs. Implement narrow validated Core path invoking existing validators, never disable ORM guards.
5. Add DB guards and role privileges tests, empty/head + 0002/head upgrades and schema checks; preserve historical tests/fixtures. No DROP/reset/force.
6. Select 1–3 real THPT2024 packets offline, document exact cell/header/campus/program/source and unresolved decisions. Do not apply reviews or publication to real data. Persist review packets only if useful; private outputs state/ ignored.
7. Full pytest/Ruff/format/mypy/lock/Alembic/diff/health; report each real/test counter separately and limits of local RBAC, no production claim.
8. Review staged paths/diff/secrets; commit/push authorized branch, verify CI exact SHA. No release builder/T09, admin UI/T11, Score Engine/T12 or production deployment.

## Transaction/trust decisions

- Reviewer and publisher use distinct DB group grants; migration owner retains maintenance authority. session_user (not SET ROLE display or JSON reviewer) is actor. Superuser rejected for review/publication apply, including tests of privileged environment.
- DB group publisher is trusted local administration capability, not anonymous/untrusted client. Application read role cannot INSERT/UPDATE/DELETE canonical/audit/jobs. DB triggers protect T08-managed histories and all audit rows; service repeats validators for Core writes. Production OIDC/role lifecycle/credential distribution remains T11/T19.
- Registry bootstrap/internal review alone does not change serving state; approving a university alias for existing current cutoffs changes public information and increments version/refresh atomically. Publishing a fact, correction, public evidence or disputed/withdrawn serving state increases catalog version and enqueues pending refresh atomically. Replay no-op does not.
- Approved review decisions bind actual input/versions and selected payload; revocation is new append-only record, never editing old job. New registry version and T07 run precede fact review; aggregate six-class resolution is never publication gate.

## Execution evidence

Baseline 461 pass; final implementation reached 506 pass, including reader-readiness privilege and structured condition regression checks. Real DB migrated to 0003 with all34table row hashes unchanged. Three private packets prepared, no real approval/canonical write. Full-repo independent review unavailable; snippet reviewer finding on revocation fixed with regression. Final results and precise remaining boundaries are maintained in docs/reports/publication-pilot.md.
