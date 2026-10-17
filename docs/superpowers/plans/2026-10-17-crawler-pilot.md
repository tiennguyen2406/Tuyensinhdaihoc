# T01/T03/T04 implementation ledger

Scope: preserve the 31-table baseline and immutable 0001; add a standalone HTTP crawler, durable PostgreSQL frontier/shared host budget and content-addressed raw storage. No facts/observations/cutoffs are published.

1. Baseline 30 tests passed; origin inspected; branch follows existing main; foundation commit separated.
2. Write offline behavioral tests first: URL/DNS/robots, leases and host coordination, fake-server conditional downloads and attachments.
3. Add reviewed source profiles/inventory, additive 0002 crawler state, CLI and downloader. Enforce depth 4, one request/host, >=2-second spacing, bounded run budget.
4. Run lint, type checks, migration parity/upgrade and all tests. Then inspect robots and perform one limited, recorded Internet pilot if allowed.
5. Update provenance/runbook/results. Review explicit staging, commit and push current branch; inspect remote SHA and CI.

Raw blobs live outside Git; no deletion/downgrade of existing data. Publication/access evidence and DDL verification have distinct statuses. Browser rendering, content extraction and canonical publication are deferred.

Completed evidence: baseline30; raw pilot6 fetches/6 snapshots including robots, content run paused at5/5; all blob hashes verified and canonical facts remain0. Additive0002 applied; Alembic parity and local health200 verified. Reviewer filesystem access was unavailable; limited snippet review found an exhausted-lease drain bug, reproduced/fixed with regression test. Final verification and remote/CI results are recorded in reports/crawler-pilot.md and handoff.
