# Database foundation implementation plan

Execution: native, directly authorized by the user; keep the current uncommitted workspace. No push/deploy or deletion of existing databases. Sources: docs/schema-provenance.md and user requirements.

- [ ] T01: data contract, source profile schema and pending inventory; distinguish verified design from unverified source/rule inputs.
- [ ] T02: frozen baseline SQL, complete static SQLAlchemy mappings, connection/session reuse, Alembic, cross-table validators.
- [ ] Health: DB connectivity plus exact application Alembic heads, safe 503, liveness independent, no automatic migration.
- [ ] Tests: isolated newly created PostgreSQL databases; empty/base-to-head, existing unrelated data preservation, all required invariants, Decimal and readiness states.
- [ ] T19 foundation: locked dependencies, Ruff/mypy/pytest, PostgreSQL GitHub Actions, README and generated data dictionary.

Verification: baseline 2 tests passed before editing. Inspect migrations/tables before upgrade. Run targeted RED tests, implement, then lint/type checks and full test suite. Compare static model metadata against the migrated real database. Re-run Alembic on existing data without rewriting revisions. Test databases created by the suite are retained (no DROP DATABASE) per this run's no-delete constraint.

Decisions: no new checkout because all project files are uncommitted and user explicitly requests working in this repository. Existing sync SQLAlchemy/psycopg engine retained for native Windows compatibility. Publication transactions, DB role provisioning, reviewed source inventory and score DSL remain separate milestones; validators never evaluate DSL or infer authoritative rules.

## Execution ledger

- Baseline verified: 2/2 health tests, 0 public tables, no migrations.
- T01 contract/profile schema/inventory delivered; real source/rule verification remains pending.
- T02 frozen 31-table DDL, static mappings, Alembic/session/guards implemented; compare_metadata passed against PostgreSQL.
- Health schema RED→GREEN, read-only 503 states verified; actual API live/ready/docs200.
- Schema/validator/immutability/Decimal regressions RED→GREEN; full suite30/30 passed.
- Ruff, mypy, lock check passed; CI foundation written and pinned, GitHub run not performed.
- Local development additive upgrade from empty schema to 0001_core; no destructive actions and no sample admissions seeded.
- Final limitations and rulings are in docs/reports/database-foundation.md; whole T01/T02/T19 are not marked complete.
