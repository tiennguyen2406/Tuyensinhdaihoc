# T05 parser contract

Scope: raw extraction only. Public `services.data.parsers.registry.parse(snapshot: SnapshotRef, profile: SourceProfile) -> list[ExtractedObservation]` uses an isolated local worker. Use runner.replay to receive observations plus document-level issues and resource metrics. Parser never downloads linked images/PDFs and never uses FastAPI request execution. SourceProfile.parser remains the legacy raw_http fetch adapter; parser_options selects business DOM regions. MIME registry selects html/1.0.0 or pdf/1.0.0; no XLSX/JSON/OCR adapter is registered.

SnapshotRef freezes snapshot_id, optional source_id, SHA-256, raw_uri, final_url, MIME and bytes. RawStorage resolves content by hash and configured root; raw_uri is descriptive provenance, not an arbitrary file-fetch instruction. Hash/size and profile host are checked. Replays receive original bytes; no text normalization is applied to PDF or raw fields.

ExtractedObservation preserves snapshot_id/source_id, fact_kind (existing DB enum), record_locator, parser_version, transform_version, raw_fields, extraction_method, Decimal extraction_confidence, issues and unverified status. Source_id is stored through snapshot FK and redundantly in raw_fields._extraction because observations has no source_id column. Issues and implementation/profile hashes are also stored there. Job metadata retains document issues, code-module digest, lock digest, output counts and timing/RSS. Confidence 0.6000 for narrative and 0.7000 for table extraction are uncalibrated layout heuristics, not factual accuracy, publication approval or admission probability.

`transform_version=raw-only/1;normalizer=none;resolver=none;aliases=none` declares explicitly that T06/T07 are absent. normalized_fields is {}. Score/money tokens remain strings, including blanks, dashes, locale separators and units. Geometry uses numeric PDF points (top-origin). No entity UUID is resolved, no combination is multiplied and no conversion rule is executed.

One observation is a physical table data row or a text block, not a canonical cutoff. A row can retain multiple admission years and methods through its header paths. Document-title year is separate context; no implicit assignment to every value. Exact verified cutoff counting remains unchanged.

## HTML

Choose a unique configured business root, never fall back to whole body/footer. Excluded navigation/sidebar/script/style elements are not extracted. Context is the preceding heading stack within the source section, with heading-level resets; future campus headings cannot affect earlier rows. Caption, table-group labels, header paths and footnotes are retained with locators. Raw text is kept alongside display text.

Locator format `html:<CSS nth-of-type path>` selects the original snapshot DOM using BeautifulSoup html.parser. `html.locate` and CLI inspect resolve it. Physical cell origins retain their exact raw text/span/row/column. Expanded span slots reference the original locator and carry text=None; they do not copy score values. Physical empty cells remain empty strings. No forward-fill is performed.

Classification uses local header/caption evidence, then relevant heading context only when needed. Entry thresholds remain catalog with an issue; narrative references to admission cutoffs do not become cutoff observations. Ambiguous abbreviated headers (e.g. Điểm TT) are retained for review instead of expanded without evidence. Mixed/noisy content and linked image tables require review. All observations remain unverified even when a header explicitly labels admission cutoffs.

## Digital PDF and review

Locators `pdf:pN:tableI:rR` or `pdf:pN:lineL` use one-based pages and zero-based table/row/line indexes. raw_fields retain page/table/row/cell bboxes, raw cells, header paths, context and footnotes. PDF geometry is measured in points from top-left. A digital re-extraction with the same version resolves the indexed table/cell and bbox. Header-only year rows are retained in headers and flagged for layout verification. Repeated headers are kept as context. Continuation is linked only with adjacent matching columns/header and an explicit continued marker; otherwise an issue preserves the separation.

No usable text with page images yields ocr_required, no observations from that page; sparse mixed image pages also require review. Empty pages, bad fonts, numeric ambiguity, missing/merged cell boundaries and layout errors produce issues. PDF errors or resource exhaustion do not commit partial output. OCR is neither invoked nor published.

Limits from design: <=25MiB input, <=200 PDF pages, <=200,000 logical table cells, <=60s per extraction child. Added conservative bounds: sampled child RSS512MiB and output32MiB, checked every20ms. Parent kills process on breach. RSS sampling is a guard, not an OS/container memory security boundary; production isolation/load testing remains pending. Child receives no DB credentials, disables standard TCP/DNS connection functions, and does not evaluate scripts/macros/actions. This is not an OS network sandbox.

## Persistence/version/replay

Existing unique key `(snapshot_id,record_locator,parser_version,transform_version)` is reused. Inserts are unverified. Conflict with same payload is a no-op; changed payload with same versions is rejected and the transaction rolled back. Raw extraction never overwrites an old reviewed/normalized observation. parser version is `implementation/version+revision`; a new explicit revision may reprocess the same body while retaining prior rows. It is an output namespace, not evidence that a new implementation was written.

Existing ingest_jobs stores parse_snapshot tasks with unique snapshot/parser/transform key, frozen configuration and implementation/lock digests. Source/profile/code/budget changes require a new revision. Claim uses row lock,5minute lease,30second heartbeat and token fencing. Observation inserts and job completion are one transaction. All output must match the leased snapshot/versions. Retried completed jobs return their original summary; expired leases can recover. Any issue quarantines the job for review while preserving unverified extracted rows. No quality issues are erased to hide failures.

No migrations changed. No writes to crawl_runs, cutoff_scores, catalog_state or dataset_releases. T06–T08 publication/normalization/entity logic is out of this slice. Fixtures in tests/parsers/manifest.json are synthetic, generated locally; no real raw/image/PDF or personal contact data is committed.


## T06 context correction

HTML implementation now html/1.0.1. Regression tests cover numbered business chapter resets even when HTML heading levels are inconsistent, and footnotes stopping at h5/h6 boundaries. T06 dry-replay uses revision t06-context with this version and records local result/provenance; no old raw observation/parse job is overwritten or closed. Historical T05 report/version remains historical. Normalization of the215original raw inputs never inherits a historical method from the stale2026method context. See normalization-contract.md and reports/normalization-pilot.md.
