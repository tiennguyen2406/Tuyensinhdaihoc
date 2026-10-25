# EduRadar / Tuyensinhdaihoc

> **Lưu trữ:** README của hệ thống cũ (v1), chuyển từ thư mục gốc khi dự án chuyển sang V2.
> README hiện hành: [`../README.md`](../README.md).

Web tra cứu thông tin tuyển sinh Việt Nam theo trường, tên ngành/chương trình và năm2024–2026. Backend FastAPI/Python, frontend Next.js/React/Node.js, PostgreSQL17. Pipeline thu thập → trích xuất → chuẩn hóa → phân giải → review/publication là workflow operator riêng, không chạy khi mở web.

**Bản clone mới khởi động với catalog rỗng.** Không kèm DB, raw, approvals private hoặc secrets của máy DEV cũ. Trang rỗng có thông báo tiếng Việt là trạng thái hợp lệ, không phải lỗi cài đặt. Không tự crawl, seed facts, chạy publisher hoặc mở tư vấn F2 để tạo dữ liệu mẫu. Xem [HANDOVER.md](../HANDOVER.md) và chính sách P-B bên dưới.

## Bắt đầu với Docker

Cần Git, Docker Desktop chạy Linux containers và Docker Compose v2 hỗ trợ `service_completed_successfully` (khuyến nghị v2.20+). VS Code dùng để sửa code; cài extensions được gợi ý khi mở folder. Cần Internet lần build đầu. Khi chỉ chạy Docker không phải cài Python/Node/pnpm/uv trên máy host.

```powershell
git clone --branch codex/crawler-pilot https://github.com/tiennguyen2406/Tuyensinhdaihoc.git
cd Tuyensinhdaihoc
Copy-Item .env.example .env
```

Trên macOS/Linux dùng `cp .env.example .env`. Chỉ copy nếu chưa có `.env`; không ghi đè secrets đang dùng. Điền ba giá trị riêng, khác nhau trong `.env`: `POSTGRES_PASSWORD`, `CATALOG_DB_PASSWORD`, `CATALOG_CURSOR_SECRET`. Có thể tạo mỗi giá trị bằng cách nối hai GUID mới trong PowerShell:

```powershell
([guid]::NewGuid().ToString('N')) + ([guid]::NewGuid().ToString('N'))
```

Không dùng giá trị ví dụ, mật khẩu cũ hoặc đưa kết quả vào Git. Sau đó chạy:

```powershell
docker compose up -d --build
docker compose ps -a
docker compose logs --tail=100 init api web
```

Lệnh Compose v2 là `docker compose`; nếu máy có alias tương thích thì `docker-compose up -d --build` tương đương. Không cần chạy migration hoặc cài dependencies thủ công: image Python dùng `uv sync --frozen`; image Node dùng `pnpm install --frozen-lockfile` và `pnpm build`. `requirements.txt` được xuất từ `uv.lock`, không quản lý dependency bằng hai danh sách độc lập.

Chuỗi startup: PostgreSQL healthy → `init` chạy migration trên DB được chọn và tạo dedicated reader → API healthy → web. `init` kết thúc mã0 và hiển thị Exited là bình thường. Mỗi lần chạy lại init có thể thêm technical provisioning audit; không thêm business facts. API/web chạy bằng OS user không phải root; API chỉ nhận credential reader, không nhận password migration owner. PostgreSQL không publish cổng ra host.

Mở [web /majors](http://127.0.0.1:3000/majors?year=2024), [danh sách trường](http://127.0.0.1:3000/universities), [API docs](http://127.0.0.1:8000/docs), [readiness](http://127.0.0.1:8000/health/ready). Mặc định chỉ bind loopback. Không mở LAN/tunnel/public deployment bằng bộ cấu hình DEV này.

## Biến môi trường

`.env.example` liệt kê keys nhưng không chứa giá trị thật. Compose dùng các default sau cho key tùy chọn để trống:

| Key | Ý nghĩa/default Docker |
| --- | --- |
| POSTGRES_PASSWORD | Bắt buộc: password owner cho postgres/init, không đưa cho API |
| CATALOG_DB_PASSWORD | Bắt buộc: password reader riêng |
| CATALOG_CURSOR_SECRET | Bắt buộc: secret ký cursor, nên ít nhất32 ký tự ngẫu nhiên |
| POSTGRES_USER / POSTGRES_DB | `eduradar_owner` / `eduradar` |
| CATALOG_DB_USER | `eduradar_app_reader`, khác owner và group `eduradar_reader` |
| API_PORT / WEB_PORT | `8000` / `3000` trên host |
| POSTGRES_HOST / POSTGRES_PORT | Chỉ native: phải điền host/port thật; Docker tự đặt `postgres:5432` |
| API_INTERNAL_URL | Chỉ native Node: API origin, không có `/api/v1`; Docker tự đặt `http://api:8000` |
| CRAWLER_RAW_DIR | Chỉ workflow operator; Docker API đặt `/app/state/raw`, không nạp raw máy cũ |
| NEXT_TELEMETRY_DISABLED | Native Node có thể đặt `1`; image Docker đã tắt telemetry |
| PUBLICATION_DB_USER / PUBLICATION_DB_PASSWORD | Tùy chọn, operator riêng; không tự provision hoặc chạy publisher |
| RELEASE_DB_USER / RELEASE_DB_PASSWORD | Tùy chọn, operator riêng; không tự provision hoặc build release |

File env trống dành cho Compose. Nếu chạy native, điền các key kết nối cần thiết; chuỗi trống không phải default trong mọi hàm Python. Next.js native không tự đọc `.env` ở root: export `API_INTERNAL_URL` vào process trước khi chạy trong `apps/web`. Không cần `NEXT_PUBLIC_*` hay API key trả phí cho web hiện tại.

## Cấu trúc cốt lõi

```text
apps/web/                   Next.js UI, proxy server, unit/browser tests
services/api/               FastAPI, catalog, DB models, Alembic migrations
services/crawler/           Crawler operator có kiểm robots/budget
services/data/              Parser, normalization, resolution, publication, releases
scripts/docker_bootstrap.py Init schema và reader cho Docker mới
config/                    Source profiles và registry tham chiếu
tests/                     Backend tests; fixtures dùng DB test riêng
docs/                      Contracts, reports, roster và hướng dẫn operator
infra/compose.yaml         Compose PostgreSQL lịch sử, giữ nguyên cho DEV cũ
docker-compose.yml         Stack bàn giao đầy đủ, project/volume riêng
Dockerfile                  Image Python có công cụ dev/test
HANDOVER.md                 Hiện trạng, WIP, bugs và checklist tiếp nhận
```

## Lệnh vận hành và kiểm thử

```powershell
docker compose logs -f api web
docker compose exec api sh
docker compose exec web sh
docker compose exec postgres sh
docker compose exec api python -m ruff check .
docker compose exec api python -m mypy
docker compose exec web pnpm test
docker compose exec web pnpm typecheck
docker compose exec web pnpm lint
```

Backend tests tạo các DB test riêng và cần owner có CREATEDB. Không chạy fixture vào API reader hoặc DB DEV đã có dữ liệu. Với **stack bàn giao mới, isolated**, chạy:

```powershell
docker compose run --rm --no-deps init python -m pytest -q
```

Lệnh này dùng init environment owner để fixtures tự tạo DB mới; nó không chạy `scripts/docker_bootstrap` vì command đã được override. DB test được giữ theo policy của suite, có thể tốn dung lượng. CI GitHub dùng PostgreSQL disposable riêng. Playwright CI là mock browser tests, không phải real-data advice E2E. Xem [checklist kiểm chứng](handover/VERIFICATION.md).

```powershell
docker compose stop
docker compose start
docker compose down
```

`down` giữ volume. **Không dùng `down -v` trên môi trường cần giữ dữ liệu.** Project mặc định `eduradar-handover` tạo volume riêng; không đổi tên project/volume để trỏ vào `infra_postgres_data` cũ. Đổi PostgreSQL password trong env không tự đổi password trong volume đã khởi tạo; credential rotation cần operator riêng. Sau đổi reader password, chạy lại init rồi recreate API bằng quy trình đã kiểm.

Nếu cổng bận, đặt `API_PORT=18000`, `WEB_PORT=13000` trong `.env` rồi chạy lại; API origin nội bộ không đổi. Nếu init lỗi, xem log init đã được làm sạch, kiểm biến bắt buộc và DB mục tiêu; không bypass bằng chạy API owner. Nếu cần nâng migration trên DB có sẵn, review migration/backup trước; đường một-lệnh này được kiểm cho cài đặt mới.

## Dữ liệu, quyền và giới hạn

Owner đã chọn P-B: chưa thêm fact mới vào serving, kể cả DEV, khi chưa có documented applicable rights basis. Ba facts PTIT2024 ở máy cũ có quyết định xử lý riêng còn pending; clone mới không chứa chúng. K chỉ xác nhận đề xuất scale/basis cho pilot PTIT2026, không cấp publication hoặc cohort approval. F2 vẫn deferred/fail-closed; học phí chưa được phục vụ trong slice hiện có. Đọc [receipt K/P-B](reports/p1-b5-confirmation-20261022.json) và [bàn giao quyền hiện tại](reports/p1-b5-existing-rights-20261022.md).

Clone code + ZIP không chuyển quyền truy cập DB/raw/accounts và không phải production deployment. Secrets/private evidence được bàn giao riêng qua kênh được owner cho phép, không gửi trong ZIP này. Quy trình pipeline/operator lịch sử được giữ tại [docs/operator-pipeline.md](operator-pipeline.md); trạng thái mới nhất tại [progress](reports/progress-20261022.md) và HANDOVER.

## Cập nhật GitHub

Xem [lệnh Git và đóng gói ZIP](handover/COMMANDS.md). Chỉ stage danh sách file công khai của task; không dùng `git add .`. Không merge main/force push/deploy từ bộ bàn giao. Khi sửa dependency: cập nhật lockfile bằng tool/version của project, xuất lại requirements, build và kiểm CI đúng SHA.
