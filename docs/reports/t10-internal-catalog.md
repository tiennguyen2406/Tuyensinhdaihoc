# T09 corrections và T10 internal catalog — 19/10/2026

Baseline `codex/crawler-pilot` / `5bbafa52b1e471d469996689338d78e8bcf9dcaf` được kiểm
trước sửa, không reset. Kế hoạch/endpoints trước code ở
`../plans/2026-10-19-t10-internal-catalog.md`; contract/runbook ở `../catalog-contract.md`.
Lát cắt tra cứu nội bộ đã triển khai, không mở rộng crawler hoặc thay A2/B/C/D/facts.

## Hai findings T09

A tái hiện bằng synthetic PostgreSQL test có combination_id và đủ ba subjects:
query subject_id sai cột thất bại trước sửa. Query dùng combination_subjects.subject_code
→ subjects.code, giữ position và nested code/name trong artifact. Test kiểm subjects,
unique count, verify/replay; source_aggregate vẫn chạy và không nhân fact.

B tái hiện bằng manifest builder cũ cùng supported contract: verifier trước sửa từ chối
chỉ vì builder khác. Sau sửa builder_version là provenance nonempty; schema/filter
compatibility độc lập. Tests vẫn từ chối unsupported schema/checksum sai. Bốn regression
mới, tổng27release tests đạt. Không sửa schema hoặc bytes/provenance của release3.

DEV verify và read-only replay bằng implementation đã sửa:

| Thuộc tính | Kết quả |
|---|---|
| Release ID | 396ccd8b-1193-43dd-a08a-bb19e639dd56 |
| Version / SQL / export / manifest count | 3 / 3 / 3 / 3 |
| Manifest SHA-256 | b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90 |
| Manifest local | state/releases/canonical/version-3/manifest.json |
| verify/replay | verified=true, cached=true; replay read_only=true |
| Registration/facts/publication/jobs | không thêm hoặc thay đổi |

Không chạy build/rebuild version3. Manifest vẫn mang builder commit lịch sử
4b7cc538a4e2d24ff20b52cab48b7711702b6f62; code mới không viết lại provenance cũ.
Refresh1/2 vẫn succeeded/coalesced→3, refresh3 succeeded/built; không giả releases1/2.

## API và UI thực tế

Tám endpoints GET trong `../catalog-contract.md` hoạt động, prefix/api/v1. Filters
year/query/university/method/campus và program/Offering ở đúng endpoint, unknown422.
Program canonical tách Offering theo năm/campus. Search có dấu/không dấu/mã/approvedalias.
Mỗi response RO RR, live dataset_version và release reference chỉ khi version khớp.
List envelope/cursor HMAC bind filter/sort/version; tamper/mismatch422, changed409.
DTO allowlist, Decimal strings, không source body/private paths/jobs/audit/reasons.

apps/web Next.js/TypeScript/pnpm: SSR search và detail, URL chứa filters/year; loading,
error/retry, empty, coverage, Offering cards và cutoff table. Điều kiện TTNV nguyên văn
hiện theo dòng và chỉ áp dụng tại biên bằng cutoff; scale/basis/DSL và locators trong
native details, official source links có nhãn. Không form nhập điểm hoặc đánh giá hồ sơ.
Đổi năm xóa ngay kết quả, abort + generation guard ngăn response sai thứ tự; initial
multi-response detail cũng chặn mixed dataset versions. Hash-only anchor giữ dữ liệu
và chuyển tới bảng; regression từ phát hiện browser thực tế đã thêm.

DEV HTTP thật (không chỉ TestClient), API8000/web3000 loopback:

- health/live + health/ready200; universities search/detail/admission-years200;
  programs và hai Program details200; cutoffs/coverage/source200.
- PTIT2024 có một trường, hai Program, ba Offering và ba cutoff THPT:
  QTKD BVH25.17/TTNV<=13, QTKD BVS18.4/TTNV<=3, CNTT BVH7480201 26.4/TTNV<=5.
- Cutoffs2025 và2026 rỗng200, không fallback2024; coverage ghi chưa thu thập/chưa xác minh.
- Browser thật đi search PTIT→detail→bảng ba cutoff. Đổi2025 hiện loading rồi empty,
  không giữ điểm2024. Sau sửa anchor, click chuyển thẳng tới bảng không loading lại.
  Screenshot private: state/catalog/t10-20261019/browser-2024.png.

API hidden launcher PID9704 (Python worker16744), web launcher14664; kiểm actual
listener/PID trước thao tác vì PID có thể đổi sau restart. Command/time/logs đã lưu
`state/catalog/t10-20261019/{api,web}-process.json`, `*-dev.log`. Cách nạp private reader,
khởi động/dừng và tránh process trùng ở runbook. Browser/ports chạy được; mobile và
keyboard/error/delayed-response được kiểm E2E với synthetic API riêng3801/web3800,
không seed vào DEV pilot. Windows sandbox chặn Playwright taskkill teardown; chỉ
cleanup đúng test PIDs để runner hoàn tất, giữ DEV processes.

## Checks và bảo toàn dữ liệu

Backend full **565 passed**, một warning Starlette/TestClient deprecation hiện hữu;
PostgreSQL fixtures riêng, không pilot DB. Trong đó27release và13catalog tests gồm:
ba Bách khoa gần tên không gộp, accents/alias, campusOffering, no crossyear/fee fallback,
evidence fan-out, cursor/tamper/mismatch/version409, input422/404, DTO allowlist,
publication xen giữa version/data reads, reader denied raw_fields/jobs/audit/mutations.
Test source/effective date/aggregate scope và cross-year empty coverage cũng đạt.

Backend Ruff/format/mypy/uv lock/Alembic current/check đạt; head0004_releases,
không migration mới. Frontend lint/format/typecheck, **10unit/component**, production build
và **6Playwright desktop/mobile** đạt (42.7s); CI exact SHA lưu ở checkpoint bàn giao sau push.
CI thêm web job frozen lock/Node24.22.0/pnpm11.25.0/Chromium; không tắt checks hoặc giảm
coverage. CI phải được đọc tại SHA push cuối, không suy từ kết quả local.

Đối chiếu expected/actual bằng per-primary-key digests toàn34tables và364historicalfiles:

| Chỉ tiêu | Trước | Sau | Giải thích |
|---|---:|---:|---|
| Catalog / canonical count | 3 / 3 | 3 / 3 | không publication mới |
| Observations | 863 | 863 | nguyên tất cả hàng |
| Jobs | 55 | 55 | nguyên cả55hàng, gồm refresh1/2/3 |
| Releases | 1 | 1 | nguyên bytes/hashes/registry row |
| Audit | 45 | 47 | hai technical audits phía dưới,45hàng cũ nguyên |
| Raw snapshots | 22 | 22 | raw và metadata lịch sử nguyên |
| Historical files | 364 | 364 | SHA-256 nguyên, gồm release/private outputs/.vscode |

Hai audit hợp lệ: provision_catalog_reader (SELECT grants tối thiểu) và
configure_catalog_dev_login (non-superuser login chỉ reader, credentials private ACL).
Không approval nghiệp vụ mới, release mutation hoặc crawler request. Synthetic test DBs
tách khỏi pilot; không xóa lịch sử DB/files. Chi tiết ignored checkpoint
`state/catalog/t10-20261019/history-final.json`, baseline.json, http-api.json, backend logs.

## Phạm vi còn mở

Đủ cho lát cắt T10 nội bộ trên dữ liệu pilot hiện hành. Chưa nghiệm thu toànT10:
filters rich/tuition/scholarship/facilities, fuzzy ranking, pagination tải lớn/index tuning,
SLO/load/security/production auth và vận hành nhiều workers chưa có bằng chứng thực địa.
Không làm T12–T18 hoặc deploy/merge main. T09 vẫn smoke release ba facts, chưa đa nguồn.
Dataset **3/20.000, còn19.997**, không hoàn thành Phase1 hoặc quota nhờ tests/UI.
