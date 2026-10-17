# HTML/PDF parser pilot implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement the user-authorized T05 slice: review cached PTIT documents, extract unverified observations offline with deterministic provenance, and commit/push after verification.

**Architecture:** services/data/parsers holds contract, HTML and digital-PDF adapters, registry, isolated process runner and PostgreSQL observation/job persistence. Reuse immutable RawStorage and existing observations/ingest_jobs unique keys. No migrations, crawl/resume, entity resolution, normalizing scores, publication or catalog/release writes. SnapshotRef plus SourceProfile selects an explicit parser; invalid/scan/ambiguous resources yield issues and review state rather than fabricated facts.

**Tech Stack:** Existing Python3.12/SQLAlchemy/PostgreSQL; BeautifulSoup for local DOM/CSS; pdfplumber for digital PDF text/tables/bboxes; psutil for child RSS monitoring; reportlab only for synthetic test fixtures.

- [x] Verify clean codex/crawler-pilot,0002_crawler,zero observations/cutoffs; baseline71pass. Read design sections2.9/2.10 and contract. Hash all6cachedblobs; inspect HTML and PDF renderings. Both pilot PDFs have zero text on every page (15/10pages); frequent-study PDF p2 explicitly says Thuong xuyen.
- [x] Contract/tests first: immutable SnapshotRef/ExtractedObservation/ParseIssue; fact_kind DB enum; identity(snapshot,locator,parser_version,transform_version); issues/scope in raw_fields, normalized_fields empty. Raw strings remain strings; confidence Decimal; all observations unverified.
- [x] HTML tests then adapter: explicitly selected business root; headings/captions/header paths/footnotes; expand spans as origin references; blanks stay blanks; no combination multiplication. XPath locator resolves original snapshot. Use conservative table/section classification; entry thresholds stay catalog, not cutoff. Ambiguous evidence gets issue.
- [x] Digital PDF tests then adapter: page/bbox locators, text blocks, table/cell origins, repeated headers/continuation only with evidence; ambiguous layouts flagged. Scan pages return OCR issue, no OCR facts. Preserve text and headers across pages. Bound25MiB/200pages/200kgridcells/60s/512MiB RSS; parser subprocess, no API request execution.
- [x] Persistence/replay tests: durable parse job unique key/version, leases/fencing, insert-only observations on existing key; repeated same-version different payload raises version-mismatch instead of overwrite. Transaction outcome+observations atomic, stale lease rejected. CLI preview/parse/replay/inspect; default dry replay, explicit persist; existing crawl budget and canonical tables unchanged.
- [ ] Review real cached pages and scope evidence; parse eligible HTML; quarantine scans/other MIME; write parser-pilot report with actual counts/issues. FullofflineCIchecks, raw/secrets/stagedreview, commit/push samebranch, verifyremoteSHAandActions. T06-T08 and fullT05 remain incomplete.

Evidence: 98tests passed; preview/persist6snapshots;215unverifiedobservations,41rawcutoffrows;all6jobsquarantined;repeatcached/noadditionalrows;canonical/catalog/release0;rawfetch/snapshot6 andcrawlbudget5/5pausedunchanged. Final commit/push/CI result is recorded in the handoff, not presumed from plan checkboxes.

The final checklist item remains open at commit preparation because push/remote verification/CI have not run yet; content review and local verification portions are complete.
