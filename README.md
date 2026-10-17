# TuyenSinhDaiHoc

Nền FastAPI/PostgreSQL cho dữ liệu tuyển sinh Việt Nam 2024–2026. Có 31 bảng nghiệp vụ theo DDL EduRadar, 3 bảng vận hành crawler bổ sung, Alembic, health checks và CI. Crawler hiện chỉ tải raw; chưa có canonical cutoffs production, Score Engine hay giao diện.

## Cài đặt (PowerShell tại gốc repository)

Cần Docker Desktop chạy Linux containers, uv 0.13.1 và Python 3.12.15. Giữ nguyên .env đã có:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
notepad .env
uv python install 3.12.15
uv sync --locked
```

Điền POSTGRES_PASSWORD riêng trong .env; không commit. API native Windows dùng POSTGRES_HOST=127.0.0.1; API trong container dùng service postgres. Biến môi trường đã export ưu tiên hơn .env. CRAWLER_RAW_DIR mặc định state/raw (bị Git bỏ qua), có thể đặt đường dẫn riêng ngoài checkout. Không đặt raw vào thư mục mã nguồn, không công khai raw khi chưa có quyền phù hợp.

## Database và API

```powershell
docker compose --env-file .env -f infra/compose.yaml up -d postgres
docker compose --env-file .env -f infra/compose.yaml ps
uv run alembic current
uv run alembic upgrade head
uv run alembic check
uv run fastapi dev services/api/main.py
```

Operator chạy migration chủ động sau khi kiểm tra DB mục tiêu. 0001_core giữ nguyên; 0002_crawler chỉ thêm crawl_runs, crawl_host_states, crawl_schedules. Không xóa bảng/dữ liệu hoặc dùng docker compose down -v. Upgrade từ 0001 và dữ liệu có sẵn được kiểm thử riêng. Downgrade phá dữ liệu bị vô hiệu hóa.

Mở http://127.0.0.1:8000/docs. /health/live độc lập DB. /health/ready kiểm tra SELECT 1 và Alembic heads; DB lỗi hoặc schema lệch trả 503 an toàn, không tự migrate. Kết nối dùng chung services/api/db/session.py. Readiness dùng transaction read-only và statement timeout 3 giây.

## Pilot raw crawler

Chạy worker trong terminal riêng; HTTP request của FastAPI không khởi chạy crawl. Inventory 12 nguồn ở docs/source-inventory.csv, profile JSON ở config/sources. candidate là URL ứng viên; checked là đã mở được một phần nguồn; eligible là đã review kỹ thuật cho pilot giới hạn. Không trạng thái nào tự cấp quyền publication hay quyền tái phân phối snapshot.

```powershell
uv run python -m services.crawler validate config/sources/ptit.json
uv run python -m services.crawler preflight config/sources/ptit.json --budget 2
uv run python -m services.crawler start config/sources/ptit.json --budget 5
```

Preflight chỉ kiểm tra robots; không tự nâng profile lên eligible. Chỉ chạy start khi đã đọc evidence và profile eligible. Robots vẫn được kiểm tra lúc chạy, cache tối đa 24 giờ. 403/CAPTCHA đưa host vào needs_review, không có chế độ bypass; operator cần kiểm tra nguồn trước khi cân nhắc một đợt mới. Quyền sao chép/tái phân phối vẫn cần xác minh riêng. Kết quả pilot thực tế trong docs/reports/crawler-pilot.md.

Mỗi start in run_id. Trong các lệnh sau, thay RUN_UUID bằng UUID đó; SNAPSHOT_UUID lấy từ bảng source_snapshots/báo cáo. Không gõ nguyên placeholder:

```powershell
uv run python -m services.crawler stats RUN_UUID
uv run python -m services.crawler stop RUN_UUID
uv run python -m services.crawler resume RUN_UUID
uv run python -m services.crawler work RUN_UUID --worker worker-2
uv run python -m services.crawler replay SNAPSHOT_UUID
```

stop ghi trạng thái bền vững; request đang tải được phép hoàn tất. Ctrl+C dừng tiến trình, lease phục hồi sau 5 phút. resume tiếp tục frontier, không tạo lại jobs đã hoàn thành. Hết budget thì pause; chỉ tăng có chủ ý bằng resume RUN_UUID --additional-budget 2. Budget tính mọi lần cấp request, gồm robots/redirect/retry; số request HTTP thực tế không vượt budget. Retry-After dài được lưu rồi worker trả quyền điều khiển; chạy work lại khi đến hạn, không busy-wait. Hai worker dùng cùng PostgreSQL chia sẻ host budget và SKIP LOCKED leases.

```powershell
uv run python -m services.crawler due config/sources/ptit.json --budget 5
```

Lệnh due tạo run cho nguồn đã đến lịch (HTML mặc định 6 giờ, attachment 24 giờ), không phụ thuộc việc HTML cha có thay đổi. Lệnh này chưa có daemon scheduler tự chạy. Manual start chủ động tải lại seeds và khám phá links. Replay đọc local blob, xác minh SHA-256 và liệt kê links HTML, không gọi Internet hoặc ghi facts; cần cùng CRAWLER_RAW_DIR đã dùng lúc tải.

Policy khởi đầu: depth 4, 1 request đồng thời/host, tối đa 0,5 request/giây (khoảng cách ít nhất 2 giây), robots có thể làm chậm thêm. Redirect tối đa 5, kiểm tra lại allowlist/DNS/public IP mỗi hop; kết nối ghim vào IP đã kiểm tra, TLS xác minh hostname. Không dùng proxy môi trường. Mỗi hop có giới hạn thời gian, body tối đa 25 MiB; robots 500 KiB. Tài liệu quá lớn hoặc encoding ngoài identity bị từ chối, không tải tiếp bằng cách lách policy.

Raw blob bất biến theo SHA-256, source_snapshots unique theo source/hash, crawl_fetches giữ lịch sử gồm 304. Chuỗi A→B→A dùng lại snapshot A nhưng có fetch mới. ETag/Last-Modified hỗ trợ conditional GET; sau 7 ngày tải unconditional để kiểm tra lại. Không có parser tuyển sinh/OCR/JS renderer, không ghi observations hoặc canonical cutoffs.

## Kiểm thử và CI

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run alembic check
uv run pytest -q
git diff --check
```

Tests cần PostgreSQL thật và tài khoản CREATEDB; cùng credential .env nhưng tạo DB riêng tuyensinh_test_<loại>_<UUID>. Các DB test mới được giữ lại theo ràng buộc không xóa; không DROP. Dữ liệu fixture là tổng hợp, không phải tuyển sinh thật. Fake HTTP servers chỉ bind loopback trong tests; không có cờ CLI cho phép crawler Internet truy cập private IP. Tests mặc định và CI không dùng Internet/crawl nguồn thật.

GitHub Actions .github/workflows/ci.yml chạy lock sync, Ruff, mypy, Alembic upgrade/check và toàn bộ tests với PostgreSQL 17 riêng. Kết quả chạy thực tế được bàn giao cùng commit push; không suy từ việc có workflow thành CI thành công.

## Tài liệu

- docs/schema-provenance.md: checksum, bằng chứng đối chiếu DDL và phần tài liệu chưa xác minh độc lập.
- docs/data-contract.md: identity, quota, provenance và ranh giới raw/publication.
- docs/data-dictionary.md: cột, constraints/indexes; sinh bằng uv run python scripts/data_dictionary.py.
- docs/source-inventory.csv và docs/source-review.md: URL, năm, định dạng và trạng thái truy cập.
- docs/reports/database-foundation.md: báo cáo lịch sử baseline 30 tests, trước crawler.
- docs/reports/crawler-pilot.md: bằng chứng đợt này, kết quả tải và giới hạn T01/T03/T04.

T01 cần mở rộng review robots/quyền dùng/coverage trước ingest production. T03/T04 hiện là nền raw HTTP; các adapter và vận hành quy mô lớn cần bổ sung sau. T19 mới là CI nền, chưa có staging/production release.
