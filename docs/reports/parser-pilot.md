# Parser pilot T05 — 2026-10-17

## Baseline và ranh giới

Nhánh codex/crawler-pilot, baseline e77385f8e314f1be484716eb22530164acf2c051, working tree sạch trước triển khai. Không có AGENTS.md trong repository hoặc các thư mục cha đã kiểm tra. Đã đọc README, data contract, source-review/crawler-pilot, schema SourceProfile/observations/jobs và mục2.9/2.10/WBS T05 của tài liệu thiết kế. Baseline71tests passed trong63.92s. DB ở0002_crawler; observations/cutoffs/releases ban đầu0.

Không chạy crawler/preflight, không resume run hoặc tăng budget. Không sửa migration, models DB, health endpoint hoặc sources/. Chỉ dùng bytes local đã hash-verified. Review nội dung không đồng nghĩa publisher cấp license hoặc source trở thành verified. Không đưa raw/ảnh render/text trích đầy đủ/thông tin liên hệ cá nhân vào Git.

## Review sáu snapshots

Phạm vi dưới đây dựa nội dung HTML và review ảnh PDF local, không dựa tên file/ngày đăng. Các ảnh scan render bằng bundled PDFium, không chạy OCR. Đã kiểm tất cả25trang PDF không có digital text; review trực quan overview và các trang1/2/5/9/10/13–15 liên quan, không tuyên bố đã chép/kiểm tay từng con số.

| Snapshot UUID | MIME / SHA-256 | Review nội dung / phạm vi | Extracted observations |
|---|---|---|---:|
| 6755f9a2-bd3c-4481-994a-53bc89d1b390 | text/plain / `e014272f6d2e2f068146055fc0ce99170f41a9e90c01f7d4c0a83cbe45482949` | Robots/plain text, không phải tài liệu tuyển sinh; không có school/year fact. | 0 |
| f24ff931-d2c7-4761-8cc0-b60d91d75348 | text/html / `4055770100438ed935348e7e89b7728624211fde6354f832558b8c1eec829d72` | PTIT, thông tin tuyển sinh 2025, Chính quy, BVH/BVS từ nội dung. Có phương thức, điều kiện/ngưỡng, chỉ tiêu, chính sách học phí/học bổng và phần kết quả hai năm trước bằng ảnh. Không gán điểm ngưỡng thành điểm trúng tuyển. Các đoạn gộp chính sách giữ catalog/review. | 6 |
| ce670b50-64dc-41b3-b25f-c7509bdb3b95 | text/html / `199a58f9dca0095596e8c710379daaf9d31eb615c6760eccfa1d25c1db85dd0a` | PTIT, đề án 2024; nội dung II Chính quy. Khung III Vừa học vừa làm/IV Từ xa có heading nhưng không đủ nội dung. Nhiều bảng là link ảnh không nằm trong sáu raw blobs; không tải ảnh hoặc đoán các giá trị đó. | 3 |
| 19a1088e-6412-49e4-b911-73ec9146f4fa | text/html / `03a243b651c18fd2e89beb89676e2adb9722c66922d8e1758138c6c1bb7b7586` | PTIT, tài liệu tuyển sinh 2026 nhưng section II Chính quy và section III Thường xuyên là phạm vi khác nhau. Quota/phương thức/chính sách hiện hành tách khỏi mục11 kết quả 2024–2025. Hai bảng Chính quy có header đầy đủ tạo41rawrowobservations (28BVH,13BVS); hai bảng Thường xuyên có Điểm TT được giữ catalog và issue viết tắt, không tự diễn giải. | 206 |
| f02f3e8f-b7bb-4e36-a60e-9a683afba099 | application/pdf / `11515001282b4626f76ba32c72cf2bd7a89a5fa677dc10ae63b9ad091f37786b` | PDF scan15trang. Đọc ảnh trang1 xác nhận PTIT, 2025, Chính quy, BVH/BVS. Trang2–4 phương thức/điều kiện, trang5 ngưỡng và chỉ tiêu, trang5–8 bảng ngành, trang8–10 chính sách, trang10–15 có kết quả 2023–2024. Năm2023 ngoài phạm vi quota; không đổi thành2025. Parser không lấy điểm từ ảnh; cần OCR/manual review. | 0 |
| 4522117e-4068-4559-a9cf-5bb2e9374ac2 | application/pdf / `7b4b7c433e4c78c77f65ca11c5ceb85bbc8c707f2f2e030c7ab26a01820c62f6` | PDF scan10trang. Trang2 ghi rõ PTIT, Thông tin tuyển sinh năm2026, Hình thức đào tạo: Thường xuyên, BVH/BVS. Trang4 có ngưỡng đầu vào; trang4–6 chỉ tiêu/phương thức, trang9 học phí, trang10 kết quả2024–2025 cho Vừa làm vừa học/Từ xa. Giữ ngoài pilot Chính quy, không gọi là tài liệu điểm chuẩn2026;0observations, chờOCR/review. | 0 |

## Locators bằng chứng

HTML dùng CSS locator với prefix html:, được html.locate/CLI inspect resolve trên DOM gốc. Các selector rút gọn dưới đây đã được kiểm tra tồn tại; observations giữ đường nth-of-type đầy đủ.

- `f24ff931-d2c7-4761-8cc0-b60d91d75348` → `html:article#post-4346 > h1`.
- `ce670b50-64dc-41b3-b25f-c7509bdb3b95` → `html:#main-content .ova_dir_content > section#dao_tao_chinh_quy > h3`.
- `ce670b50-64dc-41b3-b25f-c7509bdb3b95` → `html:#main-content .ova_dir_content > section#vua_hoc_vua_lam > h3`.
- `19a1088e-6412-49e4-b911-73ec9146f4fa` → `html:#main-content .ova_dir_content > section#dao_tao_chinh_quy > h3`.
- `19a1088e-6412-49e4-b911-73ec9146f4fa` → `html:#main-content .ova_dir_content > section#dao_tao_chinh_quy > h5:nth-of-type(11)`.
- `19a1088e-6412-49e4-b911-73ec9146f4fa` → `html:#main-content .ova_dir_content > section#dao_tao_chinh_quy > h6:nth-of-type(20)`.
- `19a1088e-6412-49e4-b911-73ec9146f4fa` → `html:#main-content .ova_dir_content > section#dao_tao_chinh_quy > h6:nth-of-type(21)`.
- `19a1088e-6412-49e4-b911-73ec9146f4fa` → `html:#main-content .ova_dir_content > section#dao_tao_chinh_quy > table:nth-of-type(6) > thead`.
- `19a1088e-6412-49e4-b911-73ec9146f4fa` → `html:#main-content .ova_dir_content > section#vua_hoc_vua_lam > h3`.

PDF (595×841 points, tọa độ từ góc trên trái):
- f02f3e8f-b7bb-4e36-a60e-9a683afba099: `pdf:p1`, bbox[55,75,550,265] tên/năm/hình thức và BVH/BVS; `pdf:p5` ngưỡng đầu vào; `pdf:p10`, bbox[40,445,570,800] tiêu đề kết quả và headers2023/2024; `pdf:p13`, bbox[40,580,570,800] bắt đầu Cơ sở phía Nam. Xem tiếp các trang11–15 để review toàn bảng.
- 4522117e-4068-4559-a9cf-5bb2e9374ac2: `pdf:p2`, bbox[40,65,565,260] hình thức Thường xuyên và tên/năm/mã cơ sở; `pdf:p4` ngưỡng; `pdf:p9` học phí; `pdf:p10`, bbox[35,25,580,490] headers2024/2025 và nhóm Vừa làm vừa học/Từ xa. Các bbox này là vùng review thủ công, không phải kết quả OCR.
- Scan issues có locator trang tương ứng; không dựng locator ô giả khi chưa có OCR/digital table.

## Contract và implementation

Xem ../parser-contract.md. Module services/data/parsers gồm contract/common/html/pdf/registry/runner/worker/persistence/jobs/CLI. Tận dụng SourceProfile với parser_options, RawStorage, source_snapshots, observations và ingest_jobs hiện có. Không thêm/sửa migration. Cùng(snapshot,locator,parser_version,transform_version) là no-op nếu payload giống, khác payload bị chặn; namespace version mới giữ hàng cũ.

HTML giữ business root/heading stack/caption/header nhiều tầng/cell origins/spans/footnotes. Không forward-fill điểm, không nhân tổ hợp. PDF số giữ trang/table/row/cell bbox, header lặp/tiếp nối và ambiguity; PDF scan không phát sinh OCR facts. Process replay có byte/page/cell/time/RSS/output guards; RAM là giám sát định kỳ, chưa phải OS/container sandbox. Chỉ nhận diện fact_kind, không thực thi rule hoặc resolve entity.

Các lỗi đã tái hiện bằng test và sửa: Windows stdout CP1252 làm CLI lỗi khi xuất tiếng Việt; heading campus tương lai lọt context; học bổng có nhắc học phí bị phân loại sai; hàng header PDF chỉ gồm năm bị coi data; output khác snapshot/version và stale lease bị chặn; hàng điểm trống không được tính cutoff; đoạn nhiều mục chính sách bị ép một fact_kind. Review độc lập chỉ ở mức đoạn code do quyền đọc filesystem của reviewer bị chặn trước đó; không coi là review đầy đủ repository.

## Kết quả persist và idempotency

Đã chạy parse CLI trên sáu snapshot, rồi chạy lại từng lệnh cùng revision1: cả6trả cached=true. Tổng observations vẫn215, không thêm hàng lặp; cả6parse jobs quarantined vì có issues. Phân bố:

| fact_kind | observations | verification_status |
|---|---:|---|
| catalog | 145 | unverified |
| conversion_rule | 2 | unverified |
| cutoff | 41 | unverified |
| scholarship | 8 | unverified |
| scoring_rule | 11 | unverified |
| tuition | 8 | unverified |

41 cutoff observations là41hàng bảng raw trong HTML2026 có headers ghi điểm trúng tuyển của2024/2025; không phải41canonical cutoffs. Mỗi hàng còn giữ nhiều năm/phương thức, chưa biết đầy đủ scope/scale/rules. Header năm2026 trên trang không gán thành năm điểm. normalized_fields={} và transform_version ghi rõ normalizer/resolver/aliases=none. Các heading nguồn chưa luôn có hệ cấp chuẩn, còn context dư cần reviewer kiểm trước normalization.

Issues theo các lần parse đầu tiên (69occurrences; số dưới đây gồm document issues, không đếm lặp issues gắn lại vào từng hàng):

| code | occurrences |
|---|---:|
| ambiguous_abbreviated_cutoff_header | 2 |
| entry_threshold_not_cutoff | 4 |
| image_requires_review | 31 |
| mixed_narrative_fact_kinds | 1 |
| mixed_threshold_cutoff_context | 2 |
| narrative_cutoff_requires_structured_evidence | 3 |
| ocr_required | 25 |
| unsupported_media_type | 1 |

| Snapshot | Parse job | Inserted lần đầu | Trạng thái |
|---|---|---:|---|
| 6755f9a2-bd3c-4481-994a-53bc89d1b390 | c36ba018-4a4a-4b95-9d63-681a38c8143a | 0 | quarantined |
| f24ff931-d2c7-4761-8cc0-b60d91d75348 | ae40a71d-e877-4231-b9ec-e41171b60466 | 6 | quarantined |
| ce670b50-64dc-41b3-b25f-c7509bdb3b95 | 1ce8461f-1c44-4620-b018-f4f40df9f441 | 3 | quarantined |
| 19a1088e-6412-49e4-b911-73ec9146f4fa | 66f6ff94-b490-4551-a77b-a7dba9eecd17 | 206 | quarantined |
| f02f3e8f-b7bb-4e36-a60e-9a683afba099 | 0b9f802e-cc0b-4d93-959f-b32425b26b65 | 0 | quarantined |
| 4522117e-4068-4559-a9cf-5bb2e9374ac2 | 416a7757-e114-42ed-87c4-7df0f8928485 | 0 | quarantined |

Counter sau persist: source_snapshots=6, crawl_fetches=6, cutoff_scores=0, catalog_state.dataset_version=0, dataset_releases=0. Crawl run6ee6fd0d-60ae-4858-94ef-733967012bf5 vẫn paused/budget_exhausted, budget5/used5,4taskcrawlchờ; không chạy network. Chỉ snapshot metadata/raw local được đọc lại.

## Kiểm chứng và kiểm tra lại

Đã chạy:

```powershell
uv run pytest -q --tb=short  # 98 passed, 69.16s (baseline71 + parser27)
uv run ruff check .         # passed
uv run ruff format --check . # 64 files formatted
uv run mypy                # 30 source files, passed
uv lock --check            # 87 packages, passed
uv run alembic current     # 0002_crawler (head)
uv run alembic check       # No new upgrade operations detected
git diff --check
uv run python -m services.data.parsers list
uv run python -m services.data.parsers replay 19a1088e-6412-49e4-b911-73ec9146f4fa --output state/parser/preview.json
uv run python -m services.data.parsers parse 19a1088e-6412-49e4-b911-73ec9146f4fa
uv run python -m services.data.parsers job 66f6ff94-b490-4551-a77b-a7dba9eecd17
```

parse ghi unverified staging; chạy lại namespace1 trả cached. Đừng tăng revision chỉ để tăng số hàng. New revision/idempotency được kiểm bằng synthetic fixtures trong DB test riêng; không tạo duplicate version production chỉ để demo. JSON đầy đủ/raw render nằm trong state/ bị bỏ qua. SQL kiểm counters/observations ở README. Health được kiểm sau persist; không có migration mới. CI GitHub sẽ được theo dõi trên đúng SHA push và bàn giao kết quả thực tế, không suy từ local pass.

## Mức hoàn thành

Hoàn thành lát cắt T05 HTML và nền PDF số có fixtures, registry/versioning, process guards, durable staging/replay và review thật. PDF số chưa có tài liệu số thật trong pilot vì cả2PDF đều scan; chứng cứ PDF số hiện là fixtures tự tạo. HTML2024/2025 còn bảng ảnh chưa tải. Điểm TT/continuation/font/scan/scope và các hàng chưa rõ cần human review.

XLSX, JSON/API, SPA, OCR, adapters đa trường, ký duyệt nguồn/facts và OS/container sandbox/load tests còn thiếu. T05 toàn WBS chưa hoàn tất. T06 normalization, T07 entity resolution, T08 publication/revisions/releases chưa triển khai; không đạt quota20.000 bằng observations. Quyền lưu/tái phân phối/commercial vẫn cần xác minh. Không merge main/deploy; không sửa nguồn tham chiếu hoặc xóa DB/dữ liệu.

Post-persist read-only checks: /health/live=200,/health/ready=200; head0002_crawler; duplicate extraction keys0; non-unverified observations0; normalized_fields nonempty0;6parse jobs.
