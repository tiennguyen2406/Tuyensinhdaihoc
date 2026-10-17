# TuyenSinhDaiHoc

Nền FastAPI/PostgreSQL cho hệ thống tuyển sinh Việt Nam 2024–2026. Hiện có schema 31 bảng theo tài liệu EduRadar được cung cấp, Alembic, health checks và CI nền; chưa có crawler, dữ liệu tuyển sinh thật, Score Engine hay giao diện.

## Cài đặt (PowerShell, tại thư mục gốc repository)

Cần Docker Desktop chạy Linux containers, uv 0.13.1 và Python 3.12.15. Khởi tạo cấu hình lần đầu, giữ nguyên .env nếu đã có:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
notepad .env
uv python install 3.12.15
uv sync --locked
```

Điền POSTGRES_PASSWORD riêng trong .env; không commit tệp này. POSTGRES_HOST=127.0.0.1 là API native Windows; khi chạy API trong container phải dùng hostname service postgres. Các biến môi trường đã export ưu tiên hơn .env.

## Database, migrations và API

```powershell
docker compose --env-file .env -f infra/compose.yaml up -d postgres
docker compose --env-file .env -f infra/compose.yaml ps
uv run alembic current
uv run alembic upgrade head
uv run alembic check
uv run fastapi dev services/api/main.py
```

Migration là thao tác operator chủ động. Kiểm tra DB mục tiêu trước khi upgrade; không sửa revision đã áp dụng. Baseline thêm bảng, không seed ví dụ tuyển sinh. Downgrade phá dữ liệu bị vô hiệu hóa; không dùng docker compose down -v. Engine/session dùng chung tại services/api/db/session.py, models tại services/api/db/models.py.

Mở http://127.0.0.1:8000/docs. /health/live chỉ kiểm tra tiến trình. /health/ready thực hiện SELECT 1 và so sánh tập Alembic heads trong DB với ứng dụng; DB lỗi hoặc schema thiếu/lệch trả 503 an toàn. Endpoint không tự migrate. Readiness dùng transaction read-only, statement timeout 3 giây; connect/pool timeout 3 giây mỗi giai đoạn. Hiện chưa có migration cũ nên đường nâng cấp là base→0001_core; nâng cấp lặp lại và dữ liệu có sẵn được kiểm thử riêng.

## Kiểm thử và chất lượng

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
```

Tests cần PostgreSQL thật và tài khoản có CREATEDB; cùng credential .env nhưng tự tạo DB riêng tên tuyensinh_test_<loại>_<UUID>. Fixtures chỉ nằm trong test DB, transaction dữ liệu được rollback. Các database test mới được giữ lại theo ràng buộc không xóa của đợt này; không có DROP DATABASE/DROP TABLE trong suite. CI dùng container riêng, không crawl Internet. Tài khoản app hiện tại là tài khoản development của Docker, chưa phải mô hình phân quyền production.

GitHub Actions: .github/workflows/ci.yml, có PostgreSQL service, lock sync, lint/format/type checks, migration + kiểm tra metadata và tests. Chưa chạy Actions trên GitHub vì đợt này không push.

## Tài liệu và trạng thái

- docs/schema-provenance.md: nguồn DDL, checksum và tài liệu gốc còn thiếu.
- docs/data-contract.md: identity, quota, source/rule verification và giới hạn validator.
- docs/data-dictionary.md: toàn bộ cột, kiểu dữ liệu, constraints/indexes; sinh lại bằng uv run python scripts/data_dictionary.py.
- docs/reports/database-foundation.md: bằng chứng nghiệm thu và công việc còn lại.

T01 chưa đủ nguồn đã duyệt. T02 có baseline kỹ thuật được đối chiếu; cần review tài liệu gốc, role/publisher và gates nghiệp vụ trước nghiệm thu toàn bộ. T19 mới có CI nền, chưa có staging, performance, restore/security audit hay production release.
