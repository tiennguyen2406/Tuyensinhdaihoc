# PTIT2025 official HTML corroboration — blocked before acquisition

Ngày bàn giao21/10/2026. Baseline local và actual remote đã đối chiếu:
`77554cddfbaac41f3682d6ebfb603129ae8c954e`, branch `codex/crawler-pilot`.
Chủ dự án đã chọn **bàn giao blocker hiện tại**, không tiếp tục chờ recovery.
Task chưa đạt numerical/evidence acceptance; không có source corroboration mới.

## Blocker quan sát được

Trước bất kỳ preflight/fetch hay ghi ingestion nào, truy vấn baseline DEV thất bại:
`FATAL: the database system is starting up`.
Read-only Docker diagnostics: container `infra-postgres-1` đang chạy, health `unhealthy`,
restart count0, shm512MiB; PostgreSQL đang `syncing data directory (fsync)` và log vẫn
tiến triển qua các paths khác nhau. Volume giữ4577database directories. Không xóa DB,
không restart, đổi Docker config hoặc can thiệp recovery. Không coi log fsync là bằng
chứng data corruption, cũng chưa có kết luận recovery đã xong.

Do DEV chưa nhận kết nối, không thể kiểm live inventory, exact-source cache, shared
host state hay frozen packet parents trong DB. Không bypass existing Store/crawler
để lấy nguồn bằng HTTP riêng. Đây là infrastructure blocker trước acquisition,
không phải kết luận robots/TLS hoặc nội dung nguồn PTIT bị chặn.

## Acquisition và evidence status

Exact URL vẫn là research lead chưa được EduRadar capture:
`https://ptit.edu.vn/diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2025/`.

- HTTP0/4; chưa robots preflight cho `ptit.edu.vn`, chưa fetch content/images.
- Cache status chưa xác định; không ghi là cache-miss khi chưa truy vấn được DB.
- Không có source ID/snapshot ID/hash/bytes mới; không tạo placeholder UUID.
- Chưa kiểm actual DOM, title/date, số BVH/BVS rows, TTNV, conversion ranges hoặc notes.
- Không force28corroborations hoặc kết luận BVS missing dựa vào public rendering.
- Chưa có method-applicability proposal dựa trên nguồn mới.41candidates vẫn nguyên
  `method=None`; không duplicate cutoff, không promote OCR hoặc alias APT/V-ACT.

Registry frozen trước task chỉ ghi domain `tuyensinh.ptit.edu.vn`, BVH/BVS code bindings
năm2024. Nếu sau này capture nguồn main host thành công, domain/authority năm2025 phải
được review riêng; không tự mở rộng approved registry hoặc coi official domain là reuse license.

## Phần chuẩn bị đã làm

Đã đọc contracts/reports liên quan,41review index và410image ledger; không chạy OCR.
Offline check xác nhận JSON gốc có41packets/method-null41 và bốn image RawStorage hashes
đúng. Lưu digest file packet và image ledger trong `offline-preflight.json`; đây chưa phải
`checked_packets` hoặc full before/after DB validation của lượt này.

Một probe so sánh read-only đã có15synthetic tests pass: raw-code preservation,
Decimal/TTNV conflicts, display variations cần review, campus/year-scoped code suggestions,
không fuzzy/approval. Chưa chạy với nguồn thật nên code/tests được chuyển vào private
`preparation/`, không commit thành production functionality. Private `acquire.py` giới hạn
exact main-host URL/robots và budget4 vẫn chưa dùng network.

Không chạy full pytest/Alembic trên DEV đang recovery; không tuyên bố full checks pass.
Tracked changes của bàn giao chỉ là report này và WBS; CI exact docs commit được ghi
theo trạng thái thực tế ở final handoff, không dùng baseline CI để thay thế kết quả mới.

## Preservation và giới hạn chứng minh

Last-reported DEV:56sources/49snapshots/1841observations/108jobs,939logical source-cutoff
candidates, canonical3/catalog3/audit47,1releasev3/3facts. **Chưa kiểm live trong lượt này**;
không ép DB khớp các số đó. Release hash kỳ vọng vẫn
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`, chưa kiểm live manifest.

Không có thao tác DB write, approval/bootstrap/publish/release/scoring, registry update,
hoặc sửa41packet/410box ledger. `.vscode/`, untracked handoff và historical artifacts
không bị chỉnh. Không khẳng định before/after row counts/digests đã được chứng minh bằng SQL.

## Resume nhỏ nhất

1. Chờ PostgreSQL recovery hoàn tất tự nhiên và health/read-only SQL sẵn sàng.
2. Đọc actual baseline/cache/heads; ghi nhận delta nếu có, giữ nguyên dữ liệu.
3. Reuse exact snapshot nếu có; nếu thiếu mới robots preflight độc lập và fetch exact URL
   qua existing crawler trong budget0/4 hiện chưa dùng. Không chuyển budget task cũ.
4. Inventory actual DOM rồi mới đối chiếu41rows, conversion metadata và method scope;
   kiểm lại41packet bindings, freeze addendum mới và chạy tests/CI tương ứng.

Chưa cần business approval mới để tiếp tục technical scope đã giao. T08 publication vẫn
cần source evidence, authority/rights, identity, scale/basis và admission-scope decisions
đúng hash; không thể chuẩn bị quyết định hợp lệ từ nguồn mới chưa capture.
