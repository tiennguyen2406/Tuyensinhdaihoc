# Báo cáo nền database — 17/10/2026

## 1. Hiện trạng và căn cứ

Trước thay đổi: repository chưa có AGENTS.md, README, models, Alembic, CI hoặc tài liệu tham chiếu; toàn bộ tệp đang uncommitted, chưa có commit. Không tìm thấy AGENTS.md ở các thư mục cha đã kiểm tra. PostgreSQL development có 0 bảng public. Baseline `uv run python -m unittest discover -s tests/integration -p test_*.py -v`: 2/2 pass.

Đã đọc cả hai tài liệu Desktop do người dùng cung cấp. Nguồn DDL thực tế và SHA-256 tại ../schema-provenance.md. Chưa có hai tệp mang tên gốc EduRadar_System_Design_Implementation_Plan(1).md và EduRadar_tom_tat_du_an_va_dac_ta.md trong repo/các file Markdown Desktop đã kiểm kê. Không tự xác nhận hai bản là byte-identical.

Sau triển khai: Python 3.12.15, Alembic 0001_core (head), 31 bảng nghiệp vụ + alembic_version; catalog_state.dataset_version=0; canonical published verified cutoffs=0. HTTP thực tế: live=200, ready=200 với database=connected, docs=200. API vẫn chạy bằng FastAPI dev. Không push, không deploy, không sửa nguồn tham chiếu hoặc .env, không seed dữ liệu tuyển sinh vào development.

## 2. Tệp và thay đổi

- services/api/db/models.py: static SQLAlchemy Core metadata + 31 ORM mappings từ DDL, không reflection DB lúc import.
- services/api/db/session.py: tái dùng engine/credential hiện có, session factory và dependency; cấu hình Alembic/head, root .env; giữ sync psycopg phù hợp Windows.
- services/api/db/validators.py: kiểm năm/method/scale, combination, rule, min/max/Decimal, authority scope, evidence, registry điều kiện, cách đếm; guard ORM immutable/delete/release.
- services/api/main.py: liveness độc lập, readiness transaction read-only và schema heads; timeout an toàn, không tự migrate hay trả exception/DSN.
- alembic.ini và services/api/alembic/: baseline frozen SQL, env tích hợp metadata/session, template revision; downgrade phá dữ liệu bị vô hiệu hóa.
- services/api/source_profiles.py, config/sources/profile.schema.json, docs/source-inventory.csv: SourceProfile có kiểm tra allowlist/năm/robots, inventory còn trống chờ reviewer.
- tests/: giữ hai hành vi health cũ, chuyển sang pytest để dùng database test riêng, thêm schema/validator/readiness regression tests.
- .github/workflows/ci.yml: PostgreSQL riêng, uv/Python pin, lock sync, lint/format/type, migration và tests; action commits khóa theo hướng dẫn uv chính thức.
- pyproject.toml, uv.lock, .python-version và package __init__.py: dependencies, công cụ chất lượng, editable package/import ổn định.
- README.md, docs/data-contract.md, docs/data-dictionary.md, docs/schema-provenance.md, scripts/data_dictionary.py: hướng dẫn chạy và hợp đồng/dictionary/provenance thực tế.

## 3. Schema, constraints, migration

Baseline 0001_core trích mục 4.2–4.5 của tài liệu được cung cấp. Nhóm bảng:

- Danh mục (9): universities, university_aliases, majors, programs, program_aliases, admission_methods, subjects, combinations, combination_subjects.
- Nguồn (4): sources, source_snapshots, crawl_fetches, observations.
- Năm/offering/scales/rules/scope (7): admission_years, university_year_features, program_years, score_scales, scoring_rules, conversion_rules, program_admissions.
- Điểm/evidence (2): cutoff_scores, cutoff_evidence.
- Chính sách/sự kiện (3): tuition, scholarships, exam_events.
- Vận hành (3): ingest_jobs, quality_issues, audit_events.
- Release/SNA (3): dataset_releases, catalog_state, sna_runs.

Giữ nguyên UUID/business keys, composite FK đúng trường và scale-method/scoring context, NULLS NOT DISTINCT, partial unique current indexes, NUMERIC(12,5)/(18,2), JSONB, timestamptz, pgcrypto và pg_trgm. Metadata được đối chiếu với PostgreSQL thật: compare_metadata và alembic check đều không có sai khác. Không chỉ kiểm tra tên bảng.

Không có revision cũ tại baseline nên không thể kiểm thử nâng cấp từ một revision nghiệp vụ cũ chưa tồn tại. Đã kiểm base→head trên DB mới; DB test có dữ liệu/bảng không liên quan vẫn nguyên vẹn; upgrade head lặp lại giữ dữ liệu. Development chỉ được migrate sau khi kiểm lại không có bảng public. Không stamp schema suy đoán, không sửa SQL baseline sau khi áp dụng.

## 4. Bằng chứng kiểm chứng

- Baseline unittest: 2 passed.
- RED trước readiness schema: DB trống trả 200 thay vì 503; sau sửa GREEN.
- RED trước validators: thiếu validators và ORM cho sửa cutoff; sau sửa GREEN.
- Regression RED→GREEN: Decimal tận cùng 0, sửa scope conditions, sửa offering year và thiếu payload schema_version.
- `uv run pytest -q`: 30 passed trong 15.00s, PostgreSQL thật và database test riêng.
- `uv run ruff check .`: All checks passed.
- `uv run ruff format --check .`: 26 tệp Python đúng format sau thay đổi cuối.
- `uv run mypy`: Success, 9 source files.
- `uv lock --check`: thành công, 74 packages được resolve nhất quán.
- `uv run alembic check`: No new upgrade operations detected.
- `uv run alembic current`: 0001_core (head).
- CI YAML parse thành công. Chưa chạy GitHub Actions/Linux runner; không có push trong đợt này.
- .env được git check-ignore xác nhận; không có secret thật trong mẫu/workflow. Password CI chỉ dùng cho container dùng một lần.

Các tests kiểm NULL combination, sai trường, sai scale-method, hai current cutoffs, Decimal điểm/tiền và ORM round-trip, authority/year/combination/evidence guards, immutable history, quota không cộng evidence/revisions, DB lỗi, DB chưa migrate, unknown revision và liveness độc lập. Readiness không tạo bảng trên DB chưa migrate. Fixtures dùng example.invalid/TEST ONLY trong database test, không giả dữ liệu production.

Database test do suite tạo có tên tuyensinh_test_<loại>_<UUID>; được giữ lại theo ràng buộc không xóa database. Dữ liệu từng test schema được rollback; suite không DROP DATABASE/TABLE. Chạy lại sẽ tạo thêm database test mới.

## 5. Cách kiểm tra lại

Thực hiện lệnh ở README tại thư mục gốc. Các lệnh chính: uv sync --locked; docker compose --env-file .env -f infra/compose.yaml up -d postgres; uv run alembic current; uv run alembic upgrade head; uv run alembic check; uv run ruff check .; uv run ruff format --check .; uv run mypy; uv run pytest -q. Mở /health/live, /health/ready và /docs ở localhost:8000. Nếu API đang chạy thì không mở server thứ hai trên cùng cổng.

## 6. Trạng thái nghiệm thu và ranh giới

T01: đã có data contract, định nghĩa identity/quota/year/provenance, source profile schema + tests, dictionary và inventory. Chưa có 10–15 nguồn thật được reviewer duyệt, robots/quyền lưu, quota pilot, fixtures nguồn được cấp phép hoặc rule/scale có nguồn chính thức. T01 chưa hoàn thành.

T02: baseline kỹ thuật 31 bảng + full metadata/index/constraint parity, sessions, Alembic và các tests yêu cầu đã được kiểm chứng. Chưa ký hoàn tất toàn bộ T02: cần đối chiếu tệp thiết kế tên gốc và quyết định nghiệp vụ nguồn; các quy tắc publication liên transaction ở mục 4.6 phải được hoàn tất cùng T08/T11/T12. Adapter authority_scope/canonical_fact và required_components là quy ước triển khai được ghi rõ trong contract, chưa phải nguồn tuyển sinh/rule đã xác minh.

Ma trận mục 4.6: (1) year compatibility fail-closed, chờ T13; (2) đủ 3 môn + danh sách required_components, DSL khác chờ T12; (3) min/max Decimal và verified scoped source đã kiểm; (4) primary/supporting payload và conflicting role đã kiểm; (5) cutoff sửa/retire bị chặn cho đến audited publisher T08; (6) ORM facts/rules/offering/scope immutable và DELETE bị chặn, nhưng DB role/permissions còn thiếu; (7) atomic publication/evidence/audit/job/catalog counter/manifest còn T08/T09, hiện từ chối tạo release qua ORM; (8) registry kiểm exact canonical JSON, semantic alias cần T07/reviewer.

ORM guards áp dụng qua SessionFactory, không phải lớp phân quyền thay thế PostgreSQL; bulk/Core SQL và migration/test là đường đặc quyền. Chưa có API ghi/publication; trước khi mở đường ghi thật phải provision app/reviewer/publisher roles không DELETE và hoàn thành publisher transaction/race/audit/manifest tests. Chưa triển khai crawler, Score Engine hoặc frontend.

T19: CI nền, lock/tooling và README đã có; workflow chưa thực chạy trên GitHub. Staging, role hardening, scanners, performance/SLO, backup/restore và production release chưa làm. Không đánh dấu T19 toàn bộ hoàn thành.

Quyết định thực thi: làm trực tiếp trong workspace đang có vì toàn bộ mã ban đầu chưa commit và user yêu cầu giữ repository; giữ sync engine Windows; chỉ thêm baseline không phá dữ liệu; giữ lại test DB để tuân thủ no-delete. Các lựa chọn này cần được xem lại khi chuyển sang deployment/async workers và khi muốn dọn test DB.

Rà soát độc lập: đã thử giao reviewer đọc các tệp thay đổi, nhưng sandbox không khởi tạo được và lệnh đọc nâng quyền bị dừng. Reviewer chưa đọc được tệp nào, nên không có kết luận review độc lập. Bằng chứng ở trên là kiểm thử thực tế và rà soát trực tiếp của người triển khai.
