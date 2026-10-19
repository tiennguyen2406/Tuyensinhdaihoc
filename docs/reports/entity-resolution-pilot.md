# T07 entity resolution pilot — 2026-10-17

## Hiện trạng đã xác minh

Nhánh codex/crawler-pilot, HEAD trước đợt này7e1c4b6cce0eb6a54a2fb82e812fef07ba7d7574; origin đúng tiennguyen2406/Tuyensinhdaihoc, remote branch cùng SHA qua git ls-remote. Không reset/rewrite lịch sử, không migrations mới. Không tìm thấy AGENTS.md ở repo/các thư mục cha đã kiểm tra. Đã đọc README/pyproject/tests, models/validators/SourceProfile, data-contract/dictionary/schema-provenance, parser/normalization contracts và pilot reports; đọc Overview Detailed Software Rules.md đang tham chiếu cùng WBS T01–T19. Giữ nguyên provenance phân biệt đối chiếu31bảng DDL do chủ dự án xác nhận với xác minh toàn bộ bản tài liệu tên gốc; không sửa tài liệu tham chiếu hoặc migrations. sources/ không tồn tại trong checkout.

Baseline chạy thực tế149 passed trong77.51s; Alembic0002_crawler(head).215raw+215normalization envelopes, job T06 7bc439bf-a6d7-4beb-bf03-bb47956c5383,95unverified draft candidates(91cutoff2024/4tuition2026–2027),118blocked attempts,166inputs chưa typed adapter. Các bảng canonical universities/aliases/majors/programs/program_years/methods đều rỗng; canonical cutoffs0/catalog version0/releases0.6snapshots/6fetches;6parse jobs quarantined/69 document issues. Crawl run6ee6fd0d-60ae-4858-94ef-733967012bf5 paused,budget5/used5,4tasks chờ; run preflight cũ paused2/used1 cũng giữ nguyên. Không tải nguồn/OCR/crawl mới.

## Bản đồ yêu cầu và tệp thay đổi

| Yêu cầu | Tận dụng | Bổ sung | Nghiệm thu |
|---|---|---|---|
| Candidate resolution/lineage | T06 typed envelopes và values | services/data/resolution/contract.py, resolve.py | per-candidate lineage/tuition/method/unknown tests |
| Registry/alias có version | canonical models/source metadata | registry.py, config/entities/ptit-v1.json | review/UUID/parent/code-year/context validation |
| Matching và fuzzy review | NFC/search key T06 | matching.py | code/alias/context/conflicts/top10/gold |
| Freeze/replay/impact | observations, ingest_jobs, NormalizationStore | store.py, CLI __main__.py | PostgreSQL idempotency/tamper/concurrency/history |
| Đánh giá | pytest/PostgreSQL test DB/CI hiện hữu | evaluate.py, tests/resolution/* |280synthetic gold + regression/DB/CLI tests |
| Vận hành/bàn giao | README, data contract/dictionary | entity-resolution-contract.md, báo cáo này, fixture/registry README, implementation plan | preview/run/replay/health/checks |

Không thay pyproject/uv.lock/dependencies, migrations, API health hay crawler.31bảng nghiệp vụ và3bảng crawler giữ nguyên. JSON payload T07 dùng namespace riêng; data dictionary bổ sung phần JSON, không giả có bảng registry canonical mới. Chi tiết hợp đồng tại ../entity-resolution-contract.md.

## Registry và căn cứ

Seed curated4entity proposals(1PTIT/3methods)+6alias proposals đều pending, không canonical_id/reviewer/approval. Căn cứ là snapshot19a1088e-6412-49e4-b911-73ec9146f4fa, SHA03a243b651c18fd2e89beb89676e2adb9722c66922d8e1758138c6c1bb7b7586 và HTML locators lưu trong seed; đây là evidence của hồ sơ cần review, không xác nhận nguồn/canonical publication.

BVH/BVS là hai bindings dưới cùng university proposal, scoped hệ ptit:campus-admission-label và2024, campus khác nhau theo heading BVH/BVS. Không tạo hai trường hoặc gộp campus. Nhãn chương trình tạo34Program và34Offering proposals riêng owner/year/campus/context có cell/raw-observation/envelope evidence; compiled registry72entities=1U+3methods+34Programs+34Offerings,6aliases. Tất cả pending. Các Program keys này là source/year-local review keys, cần reviewer xác lập canonical Program dài hạn, không đồng nhất major/offering/admission code.

THPT34/Tài năng27/Kết hợp30candidates giữ nhãn nguồn. THPT proposal subjects và Talent/Combined proposal composite là metadata để review compatibility với DDL hiện có, không seed admission_methods hoặc thay enum. Không suy max_score/basis/conversion từ số điểm. Major taxonomy thiếu evidence/hệ mã, scope thiếu round/population/conditions/basis nên adapter trả unresolved thay vì tạo giả entity.

## Pilot thật và persistence

Input duy nhất:215normalization envelopes thuộc job7bc439bf-a6d7-4beb-bf03-bb47956c5383, namespace normalization/1;normalizer/1.0.0;resolver=none;aliases=none.38envelopes có95candidates,177envelopes không candidate; không đọc430observations thành430facts. Resolver kiểm full raw/T06 hashes và lineage trước preview/run, không rerun normalization.

Đã persist215resolution envelopes mới, job **e4ede9f6-feed-4ce9-aac4-fc9237eeee56**, status quarantined. Resolver resolver/1.0.0; registry registry/ptit-pilot/1; aliases aliases/ptit-pilot/1. Tổng observations645=215raw+215T06+215T07;95candidate resolution results, không phải thêm95facts production. Replay hai lần đều inserted0/cachedtrue và cùng job ID; resolve_entities jobs chỉ1. affected proposal:ptit tìm95historical dependency results.

| Entity type | Resolved | Có gợi ý review | Unresolved |
|---|---:|---:|---:|
| University |0|95|95|
| Major |0|0|95|
| Program |0|91|95|
| Offering |0|91|95|
| AdmissionMethod |0|91|95|
| Admission scope |0|0|95|

Tổng candidate states: resolved0/partial0/ambiguous0/unresolved95. Các gợi ý deterministic/contextual là proposals pending, **không phải entity đã được duyệt**. Số entity đã nhận diện canonical nhưng còn publication-blocked trong pilot thật là0; toàn bộ95 vẫn bị chặn publication, ngay cả sau này đủ entity vẫn cần scale/scope/rules/evidence review. publication_eligible0, verification_statusunverified. Partial identity không thành publication đã được kiểm thử synthetic riêng.

Đã kiểm91cutoffs đều admission_year2024; gợi ý Offering khớp year/campus từngcandidate, BVH/BVS cùng một university proposal.4tuition vẫn academic_year2026–2027/admission_yearnull, không Offering/Program fee. Unknownscale/round/population/conditions/combination/scoringrule/priority/basis đều null; không điền mặc định.118attempts blocked không đổi. Summary2392original_issue_occurrences gồm issues được biểu diễn lặp qua envelopes, không phải2392document issues mới;69parser document issues/166untyped inputs giữ nguyên.

Manifest hashes:

- Input T06 full rows:6c8e42e38e86bed7cd665bdb1582daf78fa7ca9ccf60868a9fa6877187799668.
- Compiled registry:7a0f204c2622d9ab9be655937cbba0f9f43487a596dfa748d0d906db584bccc0.
- Resolver implementation:2393857d464252de7a9584bc8c15dc60306066e5d029581f61468b6f7c73218b.
- uv.lock và legacy T06 lock cùng fad74eacacc0e8b1075f8120a3c7b97023b7d6cce4bc324fa25b82557098642f; không thay lock để viết lại provenance T06.

Batch chạy trước commit: git_commit_at_execution=7e1c4b6cce0eb6a54a2fb82e812fef07ba7d7574,working_tree_dirty=true. HEAD đó không được trình bày như commit đã chứa T07; implementation digest đóng băng code thực lúc chạy. Không sửa manifest sau commit.

Sau persist/replay, full-row SHA của430observations cũ vẫn56c8106923b06a6b9791e2573c36b205f68c19f66a2db618823ea9c9ac1952bd;16jobs cũ vẫn72b19bd18b9fafb49d32e38caecce52a90ee6ffae3acf2ebbdae375d7fe80bbb. Hash của catalogs/sources/snapshots/fetches/crawl runs/host states/schedules/quality issues không đổi.6raw blobs đều SHA-256/byte_size đúng. Canonical cutoffs0, catalog dataset_version0, releases0. Health HTTP thật tại127.0.0.1:8000: /health/live200,/health/ready200.

Chi tiết/private outputs và invariants scripts ở ignored state/resolution/, không Git. Chỉ curated registry identity metadata được commit; không raw HTML/PDF/source table outputs/secrets/dumps.

## Gold, matching metrics và giới hạn

280synthetic cases=14families×20variants,80calibration/200evaluation tách family; fuzzy holdout dùng tên khác. Expected decisions khai báo từ yêu cầu trước scoring bằng build_gold.py, không lấy output resolver làm ground truth. Không có reviewer nghiệp vụ độc lập gán nhãn. Đây là bộ rule coverage tham số hóa, nhiều biến thể tương quan; không280cặp thực địa độc lập. Code/UUID/approval fixture giả có nhãn rõ, không production.

| Split | N | Correct decisions | Deterministic TP/FP | Precision/recall synthetic | Review | Fuzzy top10 hit | Fuzzy auto |
|---|---:|---:|---|---|---|---|---:|
| calibration |80|80|40/0|1.0/1.0|40/80=50%|40/40=100%|0|
| evaluation |200|200|70/0|1.0/1.0|130/200=65%|40/40=100%|0|

Deterministic metrics chỉ tính expected canonical links; fuzzy top10 hit là có target labels trong danh sách, không phải chọn đúng/precision. Wilson95% của deterministic precision: calibration[0.9124,1],evaluation[0.9480,1]; còn không đáp ứng giả định mẫu độc lập thực địa. Không chứng minh99.5%, không bật fuzzy auto-link. Chưa benchmark quy mô20.000/multi-source hoặc đánh giá nghiệp vụ độc lập.

## Review và regression

Có review độc lập **chỉ trên các đoạn mã thực tế được cung cấp**; reviewer không đọc được filesystem repository, không tự chạy tests. Không coi là full-repository review. Finding UUID approved-null đã được xác minh là model hiện chặn, thêm regression chứng minh; không giả có bug đã sửa. Ba vấn đề thật được tái hiện RED→GREEN: code bindings phụ thuộc thứ tự chọn binding thiếu qualifier, approved Offering thiếu year/context, và affected lookup bỏ sót alias mới. Đã sửa bằng chọn binding có ít missing nhất, validation/context gates, và potential_registry_change bảo thủ. Các tests ràng buộc này đạt trước persist.

## Lệnh và kết quả thực tế

```powershell
uv run pytest -q                         # 461 passed, 86.27s
uv run ruff check .                      # All checks passed
uv run ruff format --check .             # 96 files already formatted
uv run mypy                              # 44 source files, no issues
uv lock --check                          # 87 packages, unchanged lock
uv run alembic current                   # 0002_crawler (head)
uv run alembic check                     # No new upgrade operations
git diff --check                         # passed
uv run python -m services.data.resolution evaluate --output state/resolution/gold-evaluation.json
uv run python -m services.data.resolution preview --output state/resolution/preview.json
uv run python -m services.data.resolution run
uv run python -m services.data.resolution replay --job e4ede9f6-feed-4ce9-aac4-fc9237eeee56
uv run python -m services.data.resolution affected --entry proposal:ptit --output state/resolution/affected.json
```

Baseline149+312T07 tests=461. Tests dùng PostgreSQL thật trong DB test riêng, không Internet. Migration từ empty/0001→0002 và health unavailable/schema mismatch/live independent nằm trong suite giữ nguyên. Không drop DB test hoặc production. Toàn bộ checks bắt buộc đã chạy; health HTTP thực đã kiểm sau persist. Truy vấn kiểm chứng ban đầu dùng sai tên cột request_budget đã thất bại read-only; sửa thành url_budget và chạy thành công, không ảnh hưởng dữ liệu. Không có check bắt buộc bị bỏ qua.

Workflow GitHub Actions hiện hữu được cấu hình chạy toàn suite, lint/type/migrations với PostgreSQL riêng khi push; kết quả trên đúng commit T07 cần đọc từ Actions sau push, không suy từ local tests. SHA/link/CI thực tế được bàn giao ở phản hồi cuối sau khi xác minh. Không merge main/deploy.

## Mức đạt T07 và chuyển T08

Đạt lát cắt kỹ thuật pilot: versioned registry/aliases và validation, per-candidate review resolution, scoped deterministic matching, explainable fuzzy suggestions, immutable manifests/replay/impact, gold/regression/offline PostgreSQL tests. **Chưa hoàn tất T07 nghiệp vụ:** chưa canonical approvals/registry taxonomy đầy đủ, chưa entity/alias review độc lập/multi-source evaluation, Major/Scope adapter chưa có evidence để resolve. Số mappings/tests không thay bằng chứng đúng nghiệp vụ.

T08 có thể tiếp nhận95review packets và frozen lineage để thiết kế review/publication transaction. **Hiện0candidate đủ điều kiện publish.** Công việc tiếp: người có trách nhiệm review PTIT/BVH/BVS và program/code system/year/campus, taxonomy Major, phương thức THPT/Tài năng/Kết hợp; xác minh scale/formula/conditions/round/population/priority và xử lý numeric/header ambiguities ở T05/T06 trước khi cấp approval. Sau đó mới tạo registry/alias version mới, replay/đánh giá tác động rồi tiến tới publisher có evidence/audit/revisions. Không tự sửa/giải phóng118blocked attempts hoặc166untyped inputs. T08/T09 và quota20.000 chưa hoàn thành; T01/T19 toàn bộ cũng không được coi đã đạt từ đợt này.
