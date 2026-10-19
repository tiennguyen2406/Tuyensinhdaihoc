# T06 normalization pilot — 2026-10-17

## Baseline và phạm vi

Branch codex/crawler-pilot; baseline commit9be46c31d490ba40570f769f74a16760bb5b2270, working tree sạch. Origin đúng repository chủ dự án; không có AGENTS.md trong repository/các thư mục cha đã kiểm tra. Đã đọc README/data-contract/parser-contract/parser-pilot, source-review và schema observations/ingest_jobs. Thiết kế tham chiếu mục3.1–3.3 của Overview Detailed Software Rules.md; không sửa tài liệu tham chiếu/migrations.

Baseline chạy thực tế98 passed trong71.14s; Alembic0002_crawler(head).215 raw observations unverified, normalized_fields={},6 parse jobs quarantined/69 document issues; canonical0/catalog version0/releases0. Hai PDF scan không có observations. Run6ee6fd0d-60ae-4858-94ef-733967012bf5 paused,budget5/used5,4taskchờ. Không crawl/resume/budget increase/OCR hoặc source download.

## Phần triển khai

Module services/data/normalization gồm contract.py, values.py, normalize.py, store.py và CLI __main__.py. Không thêm dependency/migration. Xem ../normalization-contract.md cho schema/semantics đầy đủ.

- Raw-only input gate; NFC display/search keys riêng, giữ raw, campus/language/track/form trong nhãn.
- Decimal từ chuỗi, null statuses, operators/ranges/currency/billing units; không round hoặc convert credit→year.1.200 thiếu grammar evidence bị chặn. Timestamp UTC giữ source precision, kể cả9fraction digits; date-only không thành timestamp.
- Header-local admission year/method, physical cell origin, scope và lineage; không Cartesian expansion/nhân tổ hợp. Method là nhãn nguồn, chưa registry UUID; không thực thi rules hoặc xác nhận scale.
- Versioned insert-only normalized envelope trong observations, giữ nguyên hàng raw và full raw_fields. Parent input UUID/digest; namespace pin code/config/lock; advisory transaction lock, atomic manifest/output, idempotent replay; tất cả unverified/quarantined.
- Candidate blockers tách khỏi warnings về phần khác của tài liệu. Các draft còn thiếu canonical scope components/scale vẫn needs_review, không đủ điều kiện publish.

## Parser regression và replay riêng

Hai lỗi được tái hiện bằng failing regression tests: heading2.5của phương thức2026 còn treo dưới chapter11kết quả lịch sử vì font h4/h5 không đúng cấp nội dung; footnotes bảng điểm thưởng đi qua h5 sang học bổng. Đã sửa HTML implementation thành html/1.0.1, không sửa payload html/1.0.0 cũ.

Dry-replay snapshot19a1088e-6412-49e4-b911-73ec9146f4fa bằng html/1.0.1+t06-context:206 observations trong output riêng,41 cutoffrows;0stale-method contexts trong41rows và0scholarship notes lạc vào bảng bonus. SHA implementation f53b1b14486085f8ddd0d35d923051344309261aa2e845191aec6fcdd45d470f. Output và proof nằm state/normalization bị Git bỏ qua. **Không persist** replay parser sửa;215 raw input và69 issues/jobs cũ vẫn nguyên vẹn. Normalizer không kế thừa method từ context cũ; normalization output vẫn truy đúng raw parser version gốc.

## Kết quả offline trên inputs thật

Input215 gồm catalog145,cutoff41,scoring_rule11,conversion_rule2,scholarship8,tuition8. Preview và batch đã persist cho95 draft candidates từ38 inputs;177 inputs không có candidate. Các input vẫn có Unicode display/search normalization;166 input ngoài mapping cutoff/tuition có STRUCTURED_MAPPING_REQUIRED và chưa giả lập typed facts cho chúng.

| Fact kind | Admission year | Academic year | Method label nguồn | BVH | BVS | Tổng |
|---|---|---|---|---:|---:|---:|
| cutoff |2024|null|Dựa vào kết quả thi tốt nghiệp THPT|22|12|34|
| cutoff |2024|null|Xét tuyển Tài năng|19|8|27|
| cutoff |2024|null|Xét tuyển kết hợp|19|11|30|
| tuition |null|2026–2027|null|—|—|4|

Không có cutoff candidates2025/2026; document year2026 không lấp năm hoặc method. Các nhãn method chưa chứng minh cùng score scale hoặc eligibility giữa năm/trường.4 tuition candidates là khoảng dự kiến/trung bình cho nhóm chương trình Chính quy, không có campus cụ thể, không phân bổ thành phí từng ngành.

41 cutoffrows có205 score-column slots vật lý được xem xét:91 mapped và114 blocked; không tạo ứng viên từ chỉ tiêu/số nhập học. Đối chiếu độc lập91 cell locators với DOM raw:91giá trị Decimal khớp nội dung ô và91 unique(input observation,cell locator). Hai hàng có offering_code7340101 được đối chiếu riêng: BVH có25.17/72.52/25.37 theo đúng3cộtmethod; ĐGNL/ĐGTD18.3và2025score22.75không trở thành candidate. BVS chỉ cóTHPT18.4;2025Điểm TT17.2vẫnblocked. Đây là kiểm kỹ thuật mapping, không xác minh publication của điểm.

4 fee ranges giữ35900000–40700000,44800000–58300000,41300000–46700000,58300000–67200000 VND/academic_year; raw qualifiers và programme-group statement đi kèm, admission_year=null. Decimal JSON có thể giữ phần thập phân.0 để không tự quantize.

Tổng118 blocked attempts gồm114 cutoffcells+4 tuitionparagraphs. Reasons dưới đây có thể cùng gắn một attempt nên không cộng thành118:

| Code | Occurrences |
|---|---:|
| VALUE_NOT_REPORTED |43|
| METHOD_AMBIGUOUS |54|
| METHOD_MISSING |41|
| CUTOFF_HEADER_AMBIGUOUS |13|
| TUITION_MAPPING_REQUIRES_REVIEW |3|
| TRAINING_MODE_OUT_OF_SCOPE |3|

Method ambiguity gồm nhãn gộp ĐGNL/ĐGTD vàĐiểm TT; cột2025không cómethodlocal. Tuần tự cộtmethod2024của BVH/BVS khác nhau được giữ theoheader, không dùng cột vị trí cố định.3tuitionparagraphs thuộc Thường xuyên hoặc Vừa làm vừa học/Từ xa; không dùng tiêu đề Chính quy để ghi đèsectionscope. Những missing/bị chặn giữ NumericValue(null/status) khi có lexical amount và nguyên raw/header/reason, không thành0.

Issues parser gốc vẫn69 document occurrences: image_requires_review31,ocr_required25,unsupported_media_type1,entry_threshold_not_cutoff4,mixed_threshold_cutoff_context2,narrative_cutoff_requires_structured_evidence3,ambiguous_abbreviated_cutoff_header2,mixed_narrative_fact_kinds1.25 OCRissues không bị mất chỉ vì PDF không có input observations. Summary input issues có cả document/row biểu diễn nên khác cách đếm69; xem hợp đồng.91 cutoffdrafts đều có SCOPE_COMPONENTS_UNRESOLVED/SCORE_SCALE_UNCONFIRMED;4 fee drafts đều có TUITION_GROUP_SCOPE_REQUIRES_REVIEW.

## Persistence và invariants

Đã persist215 envelopes theo normalizer/1.0.0, job `7bc439bf-a6d7-4beb-bf03-bb47956c5383` quarantined. Replay cùng job trả inserted=0,cached=true; chỉ1normalization job. Tổng bảng observations430 hàng=215 raw+215 envelopes, **không phải430 facts**. Tất cả95 candidates và215 envelopes unverified;0duplicate candidate lineage.

Sau persist, checksum toàn bộ215 raw rows và6 parse jobs khớp baseline;69 issues vẫn mở. Canonical cutoffs0/catalog version0/releases0;6snapshots/6fetches; crawl runs hash không đổi. Đọc lại cả6 raw blobs khớp SHA-256/byte_size; /health/live=200,/health/ready=200. Code digest của manifest trùng mã hiện tại: c3cd5ad91bd1396980051c38415a287720ad6baa77494a694dd1d85def204f88.

Batch chạy trước commit nên manifest ghi git_commit_at_execution=9be46c31d490ba40570f769f74a16760bb5b2270 và working_tree_dirty=true; implementation digest phía trên xác định chính xác code T06. Không trình bày HEAD cũ như commit đã chứa T06. SHA commit/push và CI trên đúng SHA được bàn giao sau khi push; không suy từ local tests thành CI pass.

Baseline kiểm toàn bộ raw rows SHA256=22d1ce384aeab04eab2a40ad45fcae92de425d81822ad349f6b5b22b43aecbae; parse jobs SHA256=90c7803db5e7b43d7d929e749335c063d9fe56bb2a8c2f96f2b06a02aa179422. Dùng full-row hash để kiểm không sửa created_at/confidence/raw/normalized/version/status cũ, không chỉ đếm số hàng. Check scripts/report chi tiết ở ignored state/normalization; không commit raw output.

## Lệnh kiểm chứng và vận hành

```powershell
uv run pytest -q --tb=short  # 149 passed, 79.04s
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv lock --check
uv run alembic current
uv run alembic check
git diff --check
uv run python -m services.data.normalization preview --output state/normalization/preview.json
uv run python -m services.data.normalization run
uv run python -m services.data.normalization replay --job 7bc439bf-a6d7-4beb-bf03-bb47956c5383
uv run python -m services.data.parsers replay 19a1088e-6412-49e4-b911-73ec9146f4fa --revision t06-context --output state/normalization/parser-context-replay.json
```

Ruff/format/mypy đạt (79Python files formatted,36source files typechecked); lock87packages nhất quán, Alembic0002_crawler(head)/check không có operations mới, diff check đạt.49 normalization tests mới và2 parser regression tests bổ sung vào98 baseline, tổng149 tests. Job replay và SQL kiểm envelopes/candidates trong README; reports raw/display chi tiết chỉ ghi ignored state/ hoặc ngoài checkout. Tests synthetic/offline, PostgreSQL test DB riêng; test concurrency/version/metadata tampering/rollback không tác động production DB.

## Mức hoàn thành và chuyển T07

T06 đã có nền versioned normalization/lineage/storage/replay và mapping pilot cutoff/tuition được kiểm offline. Chưa hoàn tất toàn bộ typed adapters cho catalog/scholarship/scoring/conversion/exam_event, mapping multi-source/conditions/round/population, performance20.000 hoặc review nghiệp vụ. Không tuyên bố toàn T06 hayT05hoàn thành.

Có thể chuyển95 drafts sang thiết kế T07 với source labels/program codes/campus/form/year/cell evidence; vẫn phải review source authority, phân giải scope/method/entity/alias, scale/rules và điều kiện trước T08. Không fuzzy merge hoặc UUIDentity đã tự gán trong đợt này. OCR/XLSX/JSON/SPA thuộc phần T05 còn thiếu. T07/T08 và quota20.000 chưa hoàn thành;canonical0không thay đổi. Không merge main/deploy hoặc đưa raw/secrets/dumps/dữ liệu cá nhân vào Git.


## Review độc lập và regression fixes

Reviewer không đọc được filesystem trực tiếp (sandbox provisioning lỗi; lần đọc escalated còn pending đã hủy), nên review chỉ trên các đoạn mã thực tế do implementer cung cấp. Không coi đây là review đầy đủ repository hoặc kiểm chứng tests độc lập. Reviewer xác định3 lỗi important: context campus kép giữ campus cũ; cột chương trình xung đột lấy cột cuối; đoạn học phí nhiều khoảng giá lấy khoảng đầu. Cả 3đã có tests RED→GREEN và được chặn bằng CAMPUS_AMBIGUOUS/PROGRAM_SCOPE_AMBIGUOUS/TUITION_MULTIPLE_RANGES trước persist. Không bỏ qua finding hoặc coi unverified đủ để cho phép mapping sai. Không có minor được deferred từ lượt review này.
