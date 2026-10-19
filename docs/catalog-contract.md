# T10 — tra cứu nội bộ, contract `catalog/1`

Lát cắt live canonical PostgreSQL: tìm trường → Program/Offering → cutoff đúng năm.
Kế hoạch trước implementation: `plans/2026-10-19-t10-internal-catalog.md`.
Căn cứ đặc tả/checksum: `schema-provenance.md`; không thay counting/publication contract.

## Snapshot, DTO và giới hạn

Mỗi response mở một transaction **READ ONLY REPEATABLE READ** trước schema check,
catalog version và mọi query dữ liệu/coverage/source/release. `dataset_version` là
version đang phục vụ. `release` chỉ có `{id,version}` nếu dataset_releases chứa đúng
version đó, nếu không là null. Release3 là baseline kiểm chứng; serving4 không mang
nhãn release3. API đọc canonical hiện hành, không đọc frozen release để giả dữ liệu mới.

Chỉ current verified cutoffs thuộc published scope, Offering đúng năm2024–2026,
university verified. Disputed/noncurrent/withdrawn không xuất hiện như verified.
Explicit DTO allowlist; không serialize ORM rows hoặc raw source bodies, credentials,
private paths, jobs/audit/review reasons. Source DTO chỉ chọn URL HTTP(S) thuộc source
official/verified đã liên kết với facts được phép trong năm; không tải nguồn khi tra cứu.
Locators loại bỏ suffix review nội bộ, giữ vị trí evidence. Không expose raw storage.

Program là identity xuyên năm; Offering là program_year_id theo năm/campus, giữ
program_id riêng. Không gộp trường gần tên hoặc nhân fact theo evidence/tổ hợp.
Decimal là chuỗi JSON chính xác (`"25.17"`, `"18.4"`, `"26.4"`), không qua float.
Unknown Major/track/language giữ null; tuition/scholarships null cùng status
`not_available_in_slice`, không suy0/không có chính sách hoặc lấy năm khác.
TTNV chỉ tại biên bằng cutoff; scope/condition text và DSL được chọn trường rõ ràng,
`unavailable_aggregate_scope` giữ nguyên. Không tính/so sánh điểm hoặc kết luận trúng tuyển.

## Endpoints và filters

Prefix `/api/v1`, GET only. `year` bắt buộc đúng bốn chữ số2024/2025/2026, trừ
admission-years trả đủ ba năm. UUID input hợp lệ nhưng detail không tồn tại404;
input sai/missing year/filter lạ422; list rỗng200. Method là mã, campus là label
normalize cùng hàm text hiện có. Search dùng tên/mã trường/alias approved, bỏ dấu
tiếng Việt bằng normalization hiện có; không fuzzy auto-merge.

| Endpoint | Filters / nội dung |
|---|---|
| `/universities` | year, query, method, campus, limit, cursor |
| `/universities/{id}` | year; thông tin trường, counts, phương thức và nguồn |
| `/universities/{id}/admission-years` | không nhận filters; ba năm với trạng thái/counts |
| `/programs` | year, university_id, query, method, campus, limit, cursor; Offering DTOs |
| `/programs/{id}` | year; Program canonical và Offerings của năm đó |
| `/cutoffs` | year, university_id, program_id, program_year_id, method, campus, limit, cursor |
| `/data-coverage` | year, university_id, method, campus; ba năm, không pagination |
| `/sources/{snapshot_id}` | year; source reference đã liên kết eligible facts, hoặc404 |

List envelope: `items,next_cursor,has_more,dataset_version,coverage,warnings,release,
contract_version`. Detail thay ba trường pagination bằng `item`. Admission-years và
coverage là danh sách cố định ba năm, next_cursor=null/has_more=false. Coverage của
admission-years envelope dùng năm cuối phạm vi2026; từng item giữ năm/counts riêng.
Coverage lấy cùng live snapshot, bao gồm counts trường/Program/Offering/cutoff,
computation unavailable, available/missing years. Năm trống = chưa thu thập/chưa xác minh,
không có nghĩa trường không tuyển sinh. Frozen release coverage vẫn đọc artifact T09.

List page limit mặc định50, hợp lệ1–200. Stable keyset theo normalized tên + UUID,
cutoffs theo UUID. Cursor HMAC-SHA256 bind endpoint, normalized filters, limit, sort,
dataset version và last key. Tampering/sai filters422; cursor đúng chữ ký nhưng
catalog version tiến trả409 `detail.code=DATASET_CHANGED`; client tải lại từ đầu.
`CATALOG_CURSOR_SECRET` dùng chung mọi worker và giữ ổn định qua restart. Không có key
thì fallback key ngẫu nhiên chỉ phù hợp một process DEV, restart vô hiệu cursor cũ.

Ngoài lát cắt: province/type, verification override, major/combination/track/language,
fee/currency/scholarship/facilities, score ranges, fuzzy/trigram ranking, lịch sử revisions.
API từ chối filters ngoài allowlist. UI chỉ hiện query/year/method/campus đang hoạt động;
detail không hiện search filter sẽ bị bỏ qua. Queries hiện materialize tập eligible đã
lọc rồi paginate ổn định trong bộ nhớ; chưa có chứng cứ tải20.000/SLO hoặc index tuning.

## Web và DEV Windows

Next.js16.4.2, React19.3.1, TypeScript5.9.3; Node24.22.0, pnpm11.25.0.
Versions/lock ở apps/web; không thêm repository/cache framework. API_INTERNAL_URL chỉ
server-side, mặc định `http://127.0.0.1:8000`. Same-origin proxy `/api/catalog/...` có
route allowlist; không phải URL proxy tùy ý. SSR force-dynamic/no-store. Client đổi
query/year/method/campus ghi URL, xóa dữ liệu cũ ngay, AbortController + request identity
chặn response cũ. Các response detail/Offering/cutoff phải cùng dataset_version mới render;
lệch version báo tải lại. Hash-only navigation không đổi query/data identity.

Owner chạy `uv run python -m scripts.provision_catalog_roles` một lần có chủ ý;
script chỉ grants SELECT cần thiết, observations chỉ id/snapshot_id/record_locator,
ghi technical audit; không tạo login/password. Dedicated login DEV là non-superuser,
chỉ kế thừa eduradar_reader, không có mutation quyền release/publication. Không dùng
owner làm runner tra cứu. Credentials không nằm trong Git hoặc argv.

Ví dụ chạy lại với private credential file đã được tạo trong pilot (không in nội dung):

```powershell
$reader = Get-Content -LiteralPath state/catalog/access/dev-reader.json -Raw | ConvertFrom-Json
$env:CATALOG_DB_USER = $reader.username
$env:CATALOG_DB_PASSWORD = $reader.password
$env:CATALOG_CURSOR_SECRET = $reader.cursor_secret
.venv/Scripts/python.exe -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
# Ctrl+C trong terminal trên, rồi xóa biến môi trường khi không dùng.
Remove-Item Env:CATALOG_DB_USER, Env:CATALOG_DB_PASSWORD, Env:CATALOG_CURSOR_SECRET
```

Terminal khác:

```powershell
npm install --global pnpm@11.25.0
pnpm --dir apps/web install --frozen-lockfile
$env:API_INTERNAL_URL = 'http://127.0.0.1:8000'
$env:NEXT_TELEMETRY_DISABLED = '1'
pnpm --dir apps/web dev --port 3000
# Ctrl+C để dừng web; không start process trùng nếu cổng đã có listener.
```

Pilot hiện chạy hidden processes, PID/command/time và logs ở ignored
`state/catalog/t10-20261019/{api,web}-process.json` / `*-dev.log`. API8000/web3000
chỉ bind loopback. Kiểm PID/cổng trước khi dừng bằng `taskkill /PID <PID> /T` trong
terminal operator; không kill theo tên python/node hoặc dừng DB. Restart dùng lệnh
terminal trên hoặc private dev.py api/web (có port guard), sau khi process cũ đã dừng.
File credentials có ACL riêng; state artifacts/screenshots/logs không commit.

## Checks

```powershell
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run alembic current
uv run alembic check
uv run pytest -q
pnpm --dir apps/web lint
pnpm --dir apps/web format:check
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
pnpm --dir apps/web exec playwright install chromium
pnpm --dir apps/web test:e2e
```

PostgreSQL tests dùng DB riêng/synthetic, không fixture từ pilot. RawStorage tests cần
pytest basetemp ngoài checkout khi môi trường Windows mặc định trỏ vào repo. E2E dùng
synthetic API3801/web3800, tách DEV8000/3000; desktop Chromium và mobile iPhone13.
CI Linux cài Chromium với --with-deps. Windows sandbox có thể chặn taskkill của
Playwright lúc teardown; chỉ cleanup đúng PIDs do test khởi tạo, không dừng DEV.

Chưa nghiệm thu toàn T10: load/SLO, production auth/network hardening, các filters còn
ngoài slice, rich admissions/tuition/scholarship, đa nguồn và dữ liệu20.000 vẫn mở.
