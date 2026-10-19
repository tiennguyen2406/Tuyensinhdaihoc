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

Catalog version cũng invalidates khi bootstrap thay đổi identity/year status/search alias
đang được T10 phục vụ dù chưa có cutoff. Policy chung cho plan/apply nằm trong
publication/serving.py, liệt kê ở publication-contract.md. Registry metadata-only không
tự tăng version; một bootstrap transaction tăng tối đa một lần, atomic cùng audit và
refresh job. Cursor trước mutation nhận409. Không đổi endpoint visibility hoặc sửa
historical versions/results/releases vì policy mới.

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
input sai/missing year/filter lạ422; list rỗng200. Method là mã, campus là label;
cả hai dùng exact equality, phân biệt hoa/thường (ví dụ THPT/BVH/BVS). Search dùng tên/mã trường/alias approved, bỏ dấu
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

### Trạng thái năm tách khỏi facts

`University.data_status` và `AdmissionYear.data_status` đọc admission_years.status trong
cùng snapshot: unknown/partial/published/verified. Không có admission-year row trả
`not_collected`; có row unknown giữ unknown. Không sửa/nâng status DB vì số cutoff.
Cutoff.verification_status vẫn verified độc lập, và counts chỉ là facts hiện có.

| Dữ liệu trong DB | data_status năm | Cutoff count | Ý nghĩa |
|---|---|---:|---|
| admission-year partial,3cutoffs verified | partial | 3 | mới thu thập một phần, dù từng fact đã xác minh |
| admission-year verified,2cutoffs verified | verified | 2 | trạng thái được ghi nhận; không chứng minh thu thập toàn bộ tuyển sinh |
| admission-year partial,không cutoff eligible | partial | 0 | có trạng thái năm, chưa có facts trong tập lọc |
| admission-year unknown,không facts | unknown | 0 | trạng thái chưa xác định |
| không admission-year row | not_collected | 0 | chưa thu thập năm này, không suy không tuyển sinh |

Coverage thêm `admission_year_status_counts` với đủ năm keys unknown/partial/published/
verified/not_collected. Đây là counts của **candidate university identities** từ search
tên/mã/alias hoặc selected university/program/Offering parent; độc lập method/campus
và việc có facts. Query alias dùng thời hạn theo năm request, candidate scope này cố
định khi báo available/missing years. Counts canonical/Program/Offering vẫn theo đúng
tập facts đã lọc; không dùng trạng thái năm để tự loại verified facts của năm partial.
UI ghi nhãn năm riêng và hiển thị số cutoff/verification riêng, không nâng partial→verified.

List page limit mặc định50, hợp lệ1–200. SQL keyset `sql_keyset/2`:
universities theo universities.normalized_name COLLATE C + UUID;
Offerings theo programs.normalized_name COLLATE C + Offering UUID; cutoffs theo UUID.
Tên Program gốc và Offering label có thể khác; sort được định nghĩa theo identity Program.
Cursor `cursor/2` HMAC-SHA256 bind endpoint, normalized filters, limit, sort,
dataset version và last key. Tampering/sai filters422; cursor đúng chữ ký nhưng
catalog version tiến trả409 `detail.code=DATASET_CHANGED`; client tải lại từ đầu.
Cursor/1 cũ trả422 `UNSUPPORTED_CURSOR` với yêu cầu bắt đầu lại, không đổi sort ngầm.
Cursor được kiểm ngay sau catalog version, trước DTO/sources/coverage queries.
`CATALOG_CURSOR_SECRET` dùng chung mọi worker và giữ ổn định qua restart. Không có key
thì fallback key ngẫu nhiên chỉ phù hợp một process DEV, restart vô hiệu cursor cũ.

Ngoài lát cắt: province/type, verification override, major/combination/track/language,
fee/currency/scholarship/facilities, score ranges, fuzzy/trigram ranking, lịch sử revisions.
API từ chối filters ngoài allowlist. UI chỉ hiện query/year/method/campus đang hoạt động;
detail không hiện search filter sẽ bị bỏ qua. Lọc/keyset/limit+1 trong PostgreSQL trên
unique entities, sau đó chỉ hydrate DTO và batch sources/evidence của trang trả về.
Không LIMIT trên evidence join. Cutoff gate materialize eligible IDs bằng SQL CTE trước
wide detail joins để tránh plan quét toàn50k khi filter rỗng. Coverage dùng aggregate SQL
cho cả ba năm, không trả facts về Python; cutoff count(*) trên base1:1, entity IDs DISTINCT.
University/alias search dùng normalized columns và indexes sẵn có; alias approved và
valid_from/valid_to overlap năm request. %, _ và backslash là literal, SQL tham số hóa.
Offering labels/codes không có normalized column trong DDL: fallback SQL hỗ trợ tiếng Việt
(NFD/bỏ dấu/đ), whitespace/invisible U+200B/FEFF, ß và các display entities thông dụng.
Fallback này không là HTML5 decoder/full Unicode casefold cho mọi ký tự; normalized Program
name vẫn là đường chính. Không thêm cột/backfill business labels hoặc search engine.
Benchmark/recovery và giới hạn hiệu năng: `reports/t10-sql-year-status.md`.

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
admission_years chỉ university_id/admission_year/status nếu provisioning độc lập,
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

Pilot hiện chạy hidden processes, web PID/command/time và logs ở ignored
`state/catalog/t10-20261019/web-process.json` / `web-dev.log`; API mới nhất ở
`state/catalog/t10-sql-20261019/api-process-final.json` / `api-dev-final.log`. API8000/web3000
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

Compose/CI PostgreSQL có shm512MiB. Default Docker64MiB đã gây lỗi cấp phát shared
memory và backend crash trên lịch sử test DB được giữ lại + aggregate concurrency.
Không giảm fsync, tắt guards/checks hoặc xóa DB để chạy benchmark. Thay shm cần recreate
container bằng `docker compose --env-file .env -f infra/compose.yaml up -d --no-deps postgres`;
giữ nguyên named volume, kiểm health và digests trước/sau; không down-v. Tăng shared memory
là headroom cho DEV/CI, không tự chứng minh mục tiêu p95 hoặc backup/restore acceptance.

Chưa nghiệm thu toàn T10: load/SLO, production auth/network hardening, các filters còn
ngoài slice, rich admissions/tuition/scholarship, đa nguồn và dữ liệu20.000 vẫn mở.
