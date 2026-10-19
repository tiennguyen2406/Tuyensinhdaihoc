# T10 — trạng thái năm, SQL pagination và benchmark nội bộ

Ngày kiểm chứng: 19/10/2026. Baseline `codex/crawler-pilot` tại
`204aedb13e79ab73fa8d1f3d99e9db550e15c726`; tiếp tục trên nhánh này, không reset.
Đặc tả có provenance theo `docs/schema-provenance.md` và bản Desktop đã đối chiếu SHA-256
`c3745329543e433bd62cf58e4a6df4c827ea54b5876f48f8c42e33d5aabf04c5`.
Kế hoạch trước implementation: `../plans/2026-10-19-t10-sql-year-status.md`.

Đã hoàn thành lát cắt sửa trạng thái năm và đưa filtering/pagination/materialization xuống
SQL, giữ luồng tra cứu nội bộ. **Chưa đạt mục tiêu search p95 <500 ms tại 50.000 rows /
20 người dùng đồng thời.** Không nghiệm thu toàn T10, T09 hay Phase 1 từ kết quả này.

## Trạng thái năm và contract

Lỗi cũ suy `data_status=verified` từ sự tồn tại của cutoff verified. Regression RED đã
tái hiện năm `partial` + cutoff verified bị nâng sai. List trường, chi tiết, admission-years
và coverage nay đọc `admission_years.status` trong cùng snapshot response:

| Dữ liệu trong snapshot | Trạng thái response | Ý nghĩa |
|---|---|---|
| Admission-year partial, có 3 cutoff verified | partial / Đã thu thập một phần | Verification của từng fact độc lập trạng thái năm |
| Admission-year verified, có hoặc không có facts | verified / Đã xác minh | Giữ đúng status đã lưu; không chứng minh dữ liệu toàn trường đầy đủ |
| Admission-year unknown, không có facts | unknown / Chưa xác định | Có hàng năm nhưng chưa xác định status |
| Không có admission-year, có hoặc không có facts | not_collected / Chưa thu thập năm này | Thiếu bản ghi năm; không suy trường không tuyển sinh |

`published` cũng được giữ nguyên. Coverage thêm `admission_year_status_counts` với đủ
năm keys: unknown/partial/published/verified/not_collected. Đây là số trường canonical
verified trong phạm vi candidate search/parent, độc lập method/campus và sự có mặt của
facts; counts canonical/Program/Offering vẫn theo đúng filters facts. Available/missing
years phản ánh facts, không tự nâng status năm. Ví dụ PTIT2024: partial=1, verified=0,
canonical=3; PTIT2025/2026: not_collected=1, canonical=0.

Contract response vẫn `catalog/1`; cursor chuyển sang signed `cursor/2`, binding revision
`sql_keyset/2`. Cursor/1 có chữ ký hợp lệ bị từ chối rõ `422 UNSUPPORTED_CURSOR` để bắt đầu
lại, không diễn dịch khóa sort cũ. Tampering/filter/limit mismatch:422;
dataset version đổi:409 DATASET_CHANGED. Cursor được kiểm ngay sau đọc version, trước
DTO/source/coverage. Limit mặc định50, min1, max200; rỗng200, UUID không tồn tại404,
input sai422. Mọi query response ở transaction read-only REPEATABLE READ.

Serving đọc canonical live và catalog version cùng snapshot; release metadata chỉ gắn
khi version khớp. Release3 là baseline kiểm chứng, không khóa serving ở3.
DTO allowlist không có jobs/audit/reasons/raw bodies/paths/credentials. Source URL có
userinfo credentials bị loại. Decimal vẫn string chính xác; null taxonomy/track/language,
phí/học bổng giữ unknown. TTNV chỉ ở biên bằng cutoff; computation unavailable như cũ.

## SQL, keyset và batch nguồn

Tám GET routes hiện có giữ nguyên: universities, universities/{id},
universities/{id}/admission-years, programs, programs/{id}, cutoffs, data-coverage,
sources/{snapshot_id}. Filters/year/unsupported-filter rejection theo `../catalog-contract.md`.

- University search dùng normalized_name/approved normalized_alias và mã trường;
  alias valid_from/valid_to phải overlap năm request. `%`, `_`, backslash là literal trong
  LIKE tham số hóa. Không gộp tên gần giống. Method/campus là exact equality.
- SQL sort universities = normalized_name COLLATE C + UUID; programs endpoint trả
  Offering, sort canonical Program normalized_name COLLATE C + Offering UUID;
  cutoffs sort UUID. Cursor khóa đúng tuple SQL, ổn định khi tie.
- Base facts joins 1:1 cutoff–published scope–Offering–method, current/verified/2024–2026
  và trường verified. Không join evidence vào filter/count/limit. Cutoff page dùng
  MATERIALIZED identity CTE rồi keyset + limit+1; hydrate chỉ IDs thuộc trang thật.
- University/Offering DTO cũng chỉ dựng cho IDs trang trả về. Evidence + primary source
  được UNION/batch một query theo owner IDs trang, dedup/sort; không query mỗi cutoff.
- Coverage là hai aggregate SQL trên tập lọc cho ba năm. Count(*) hợp lệ trên base1:1;
  university/Program/Offering dùng DISTINCT IDs. Không tải toàn bộ facts sang Python.

Không thêm framework/dependency/migration/index. EXPLAIN chỉ ra SQL shape và coverage
aggregate là chi phí chính, chưa có bằng chứng index mới giải quyết bottleneck.
Offering display labels chưa có normalized column: fallback SQL hỗ trợ tiếng Việt NFD/đ,
whitespace/invisible U+200B/FEFF, ß và entities thông dụng. Không khẳng định fallback là
HTML5 decoder/full Unicode casefold; normalized Program name là đường chính.

Reader provisioning độc lập thêm SELECT ba cột admission_years
(university_id,admission_year,status). DEV reader đã có quyền cần thiết từ baseline;
không chạy provisioning hay thêm audit trên pilot trong task này. Kiểm quyền thực tế:
non-superuser, SELECT status được phép; SELECT jobs/audit và INSERT/UPDATE release,
UPDATE admission_years đều không được phép.

## Dữ liệu synthetic và phương pháp đo

DB riêng được giữ lại, không seed pilot, không DROP/DELETE files/DB lịch sử:

| Fixture | Facts | Seed | Kích thước DB cuối | Phân bố 2024/2025/2026 |
|---|---:|---:|---:|---|
| tuyensinh_test_t10sql_20261019_20k | 20.000 | 26,741 s | 50.525.875 B | 8.000/6.000/6.000 |
| tuyensinh_test_t10sql_20261019_50k | 50.000 | 61,207 s | 109.467.315 B | 18.000/16.000/16.000 |

Mỗi fixture:200 trường,1.000 Program,2 methods,3 campuses/years, tên tie,
approved aliases,2 evidence/fact; URL example.invalid. Seed trên shm64MiB ban đầu;
đo so sánh cuối dùng cùng DB đã giữ, cùng shm512MiB và indexes cho baseline/current.

Máy Windows11 build22000, AMD Family23 Model24,4 cores/8 logical CPUs,
RAM14.966.337.536 B; PostgreSQL17.11 Debian x86_64 container. max_connections100,
shared_buffers128MB,work_mem4MB,effective_cache_size4GB,maintenance_work_mem64MB,
max_parallel_workers_per_gather2,max_parallel_workers8,JIT on. Node24.22.0,
pnpm11.25.0,uv0.13.1; Next16.4.2/React19.3.1/TS5.9.3 unchanged.

Baseline modules cached từ đúng204aedb, có source hashes. Lượt so sánh cuối không chạy
tests khác đồng thời: old completed n=2, new n=5; page limit20, later=trang2.
Đây là warm/observed DB runs; không đo cold cache, không flush/restart để suy cold.
Số mẫu nhỏ, không là production SLO acceptance.

| Request | Old20k p50 ms | New20k p50/p95 ms | Old50k p50 ms | New50k p50/p95 ms | SQL old→new |
|---|---:|---:|---:|---:|---|
| Universities đầu | 5230,2 | 191,8/217,3 | 12764,1 | 365,6/395,1 | 412→11 |
| Universities trang2 | 5248,5 | 168,3/195,4 | 12140,5 | 337,7/454,7 | 412→11 |
| Programs đầu | aborted | 145,3/182,9 | aborted | 354,8/431,0 | >1200→10 |
| Programs trang2 | chưa đo | 157,6/220,8 | chưa đo | 366,0/390,0 | —→10 |
| Cutoffs đầu | aborted | 139,9/154,6 | aborted | 355,0/391,2 | >1200→11 |
| Cutoffs trang2 | chưa đo | 136,7/147,4 | chưa đo | 312,1/347,4 | —→11 |
| Programs text search | 3663,3 | 199,9/237,5 | 9895,7 | 401,7/476,6 | 131/331→10 |
| Programs search rỗng | 3257,7 | 151,1/165,0 | 8967,5 | 311,5/367,0 | 11→9 |

Old broad programs/cutoffs bị harness chủ ý chặn statement thứ1201 sau1200 executed;
đó là intentional500, không dùng thời gian abort làm completed latency/p95. Không có
trang2 baseline vì trang1 đã abort. New filtered universities/programs/cutoffs p50
20k=69,9/47,8/54,0 ms;50k=83,6/52,7/54,4 ms. Empty p50
20k=88,8/35,8/33,9;50k=131,4/43,5/42,2 ms; empty9SQL.

| 20 users,60 measured requests | p50 ms | p95 ms | max ms | Errors |
|---|---:|---:|---:|---:|
| 20k ASGI mixed lists | 1050,5 | 1601,9 | 1673,0 | 0 |
| 50k ASGI mixed lists | 1886,4 | 2782,2 | 3003,5 | 0 |
| 50k ASGI text search | 2026,0 | 2941,2 | 3366,8 | 0 |
| 50k actual TCP text search | 1752,1 | 2625,4 | 2832,2 | 0 |

ASGI pool20; TCP uvicorn thực trên loopback3802, dedicated non-superuser reader và
default pool5+10, warmups trước60requests. TCP elapsed6,103s, workerCPU5,140625s,
RSS115.146.752B; ASGI50k search CPU host87,12%, poolpeak20. TCP process đã dừng,
port3802 đóng. **Không đạt500ms concurrent search** dù sequential p95 dưới500ms.

EXPLAIN ANALYZE BUFFERS50k: coverage Aggregate208–251ms,3rows,3359shared hits,
0reads,454/455temp read/write blocks (~3,6MiB); program identity Limit21 thêm~116ms.
University source batch có fan-out hợp lệ trong IDs trang:1640rawrows,~72,9ms;
cutoff source60rawrows,~1,455ms. Page fetch21 IDs/hydrate20DTO; limit1 tests dựng1DTO,
không tải nguồn facts ngoài trang. Query count11/10/11 không tăng khi ngoài trang tăng
200→20.000 facts. Aggregate vẫn phải đọc tập lọc lớn nên không coi SQLcount cố định là
latency cố định. Hướng tối ưu tiếp: coverage aggregate/temporary spill và request concurrency;
phải đo lại trước cam kết SLO, chưa tự thêm cache/framework/index.

Một plan trung gian của rewrite cutoff empty mất2,779s/808653bufferhits, đã sửa bằng
identity gate; không gán đó là baseline204aedb (old empty50k117,8ms).

## Sự cố shared memory và phục hồi

Default Docker /dev/shm64MiB gây bốn lỗi allocation khi benchmark; sau đó PostgreSQL
backend SIG11 lúc synthetic fixture insert, postmaster recovery,14 fixture setup errors
ở lượt test đó (12passed). Log06:11Z/06:17:30Z ngày19/10; disk còn~1TB,
OOMKilled=false/restartcount0, không phải volume hết chỗ. Giữ logs private.

Compose thêm shm_size512mb, CI postgres thêm --shm-size512m. Recreate duy nhất postgres
với cùng named volume infra_postgres_data, không down-v/xóa DB/giảm fsync/tắt guards.
Startup fsync lịch sử test catalogs mất~578s, healthy06:30:18Z. Đối chiếu sau recovery
và cuối task:34table digests/364historicalfiles nguyên. Rerun matched baseline/current
trên512MiB và full596tests đạt. Các lượt64MiB/shared-load/diagnostic lưu riêng, không
trộn vào số cuối. Đây là recovery vận hành, chưa là nghiệm thu backup/restore.

## Checks, HTTP và browser

- Backend:596passed/290,21s; riêng catalog44passed/64,66s. Một warning Starlette TestClient
  httpx deprecation hiện có; không đổi dependencies/checks để che warning.
- Ruff check,format161files,mypy68sourcefiles,uv lock87packages:pass.
  Alembic head0004_releases/check no new upgrade operations; không migration mới.
- Web lint/Prettier/typecheck/build:pass;18unit/component tests trong3files;
  Playwright6/6 desktop/mobile, production test server3800/synthetic API3801.
  Windows sandbox chặn taskkill teardown; cleanup đúng PIDs test rồi runner exit0,
  không dừng DEV. Versions và lockfiles không đổi.
- Regression covers all year statuses/empty/missing, signed cursor/old format/mismatch/
  version change, first/middle/final/limit1/50/200, ties/evidence/campus, alias date/
  accent/wildcards, DTO/source fence, query/materialization cost, concurrent publication.
  Publication fixture có verified new university và year-status mutation sau version read:
  response cũ giữ version/facts/status cũ; response sau thấy snapshot mới.
- UI tests giữ AbortController/request identity và clear-on-year-change; response đến
  sai thứ tự không hiện dữ liệu cũ, partial không bị nâng verified. Verified label có
  note coverage chưa đầy đủ. Missing/unknown riêng, mobile/keyboard/loading/error/empty.
- 30HTTP requests thật qua API8000:8routes, accent/unaccent/code, filters, pagination3facts,
  cursor tamper/limit/year mismatch422, UUID404, unsupported filter422, exact Decimal và
  coverage/year status. Tất cả expected status/counts khớp.
- Browser DEV thực:2024 hiển thị partial và ba verifiedcutoffs; đổi2025/2026 thấy loading
  xóa bảng cũ ngay rồi not_collected/0facts. Trả về2024 đúng dữ liệu, giữ tab để bàn giao.
  Evidence private browser-partial-status.png, browser-missing-2025/2026.png cùng HTTP JSON.

Các evidence/logs/plans/summaries đầy đủ ở ignored `state/catalog/t10-sql-20261019/`;
không commit secrets/raw/artifacts. CI exact SHA được ghi checkpoint sau push và bàn giao;
không gọi kết quả local là CI.

## DEV, dữ liệu lịch sử và chạy lại

Web `http://127.0.0.1:3000/universities?year=2024`; API `http://127.0.0.1:8000`.
Web existing launcher14664/listener12900 được giữ; API final hidden launcher7544,
PID/command trong private api-process-final.json, log api-dev-final.log. Kiểm listener
trước start/stop; `../catalog-contract.md` có lệnh nạp private reader vào env, uvicorn,
pnpm dev và dừng terminal Ctrl+C. Với hidden process, kiểm cmdline/cwd/PID rồi chỉ dừng
đúng uvicorn/node được ghi nhận; không kill toàn bộ python/node hoặc DB. API chạy reader,
không owner; loopback, không production/public deployment.

Release ID396ccd8b-1193-43dd-a08a-bb19e639dd56 version3, cutoff_count3,
manifest state/releases/canonical/version-3/manifest.json, SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
Verify và replay bằng CLI mới trả verified/cached/read_only=true; không rebuild hay
đổi bytes/provenance release. SQL/export/manifestcount vẫn3 theo counting policy.

Before/after34tables hoàn toàn cùng per-primary-key column hashes;364files lịch sử
(gồm raw/publication/release/.vscode) cùngSHA. Catalog3,observations863,jobs55,audit47,
release1,raw snapshots22,Program2,Offering3,currentverifiedpublishedcutoffs3.
Không có mutation pilot cần giải thích trong task này. Refresh requested1/2succeeded
coalesced3,requested3succeededbuilt nguyên. Không tạo releases1/2 hoặc publication mới.
Synthetic DB provisioning/audits chỉ ở DB synthetic riêng, không cộng quota dự án.

```powershell
# Tests: dùng basetemp mới ngoài checkout trên Windows; không dùng pilot làm fixture.
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run alembic current
uv run alembic check
uv run pytest -q --tb=short --basetemp=<NEW_ABSOLUTE_TEMP_OUTSIDE_CHECKOUT>
pnpm --dir apps/web lint
pnpm --dir apps/web format:check
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
pnpm --dir apps/web test:e2e

# Benchmark mới: --phase before tạo DB synthetic mới, không nhận pilot DB.
uv run python -m scripts.catalog_benchmark --phase before --database tuyensinh_test_new --facts 20000 --runtime-shm-mib 512
# Dùng DB synthetic đã seed với implementation cần đo; --phase after không seed lại.
uv run python -m scripts.catalog_benchmark --phase after --database tuyensinh_test_new --facts 20000 --repeats 5 --concurrent 20 --rounds 3 --runtime-shm-mib 512
uv run python -m scripts.catalog_benchmark --phase after --tcp --port 3802 --database tuyensinh_test_new --facts 20000 --concurrent 20 --rounds 3 --runtime-shm-mib 512

# Release CLI readonly, sau khi nạp dedicated release credentials theo release runbook.
uv run python -m services.data.releases verify --version 3
uv run python -m services.data.releases replay --version 3
```

So sánh old/new cần dùng code204aedb và code bàn giao trên cùng fixture/config; các lệnh
baseline_matched_worker.py thực tế/source hashes và toàn bảng kết quả ở final-summary.md
private. Không gọi hai lần cùng implementation là before/after cải thiện.

## WBS và bước tiếp theo

T10 chỉ thêm SQL/year-status slice; SLO/load, rich admissions/fees/scholarships,
filters ngoài phạm vi, production auth/security và đa nguồn còn mở. Dataset DEV vẫn
**3/20.000, thiếu19.997**; không cộng50.000synthetic vào quota, không đóng toàn T09/Phase1.

Đề xuất tiếp T09 mở rộng pilot đa nguồn có source/authority/review gates trên pipeline
hiện có, kèm nhu cầu T11 review/admin. Phạm vi và điều kiện trong
`../plans/2026-10-19-t09-multisource-next.md`; đó là proposal, chưa fetch/approve/publish.
Không chuyển thẳng T12 khi official rules/scales/golden cases chưa đủ căn cứ.
