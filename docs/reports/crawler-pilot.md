# T01/T03/T04 — bằng chứng triển khai 2026-10-17

## Hiện trạng và giới hạn

Baseline trước thay đổi: 30 tests passed. Nền database được tách commit `d0393b8` trên lịch sử origin/main (Initial commit `ced23a7`), không ghép lịch sử không liên quan. Không sửa 0001_core hoặc thư mục sources/. Đối chiếu DDL/checksum do chủ dự án xác nhận đã được phân biệt với việc agent xác minh toàn bộ tài liệu trong schema-provenance.md.

Đã áp dụng 0001_core → 0002_crawler trên DB development tuyensinhdaihoc, chỉ thêm 3 bảng vận hành, tổng 31 bảng nghiệp vụ + 3 bảng crawler. Alembic check không phát hiện khác biệt. /health/live và /health/ready trả 200 sau nâng cấp. observations/cutoff_scores/dataset_releases vẫn có 0 hàng. Không deploy production.

## Thay đổi

- services/crawler/{urls,state,transport,raw,downloader,__main__}.py: chuẩn URL/DNS, frontier PostgreSQL, shared host budget, HTTP ghim IP/TLS, raw bất biến, conditional GET, CLI độc lập API.
- 0002_crawler.py/.sql + models: crawl_runs (profile/budget/status), crawl_host_states (lease/pacing/robots/blocks), crawl_schedules (nguồn/loại/chu kỳ/due/unconditional). Không thay đổi các bảng gốc.
- config/sources/*.json + SourceProfile/JSON Schema: 12 profile thật, metadata review tách khỏi publication; giới hạn depth4/concurrency1/RPS0.5.
- docs/source-inventory.csv, source-review.md, data-contract.md, schema-provenance.md, data-dictionary.md: nguồn, truy vết, quota/raw boundary và dictionary sinh từ metadata. Bộ sinh dictionary loại khoảng trắng dư.
- tests/crawler và tests hiện có: fixtures tự tạo, fake server local, migration additive/metadata parity/health, queue/host cạnh tranh và downloader/recovery.
- pyproject.toml/uv.lock thêm Protego 0.7.0, mypy bao gồm toàn bộ services; README/.env.example ghi cách vận hành. Raw/state/.env nằm ngoài commit.

## Kiểm chứng thực tế

Các lệnh đã chạy:

```powershell
uv run pytest -q                         # baseline: 30 passed; suite sau triển khai: 71 passed trong 63.50 s
uv run ruff check .                     # passed
uv run ruff format --check .            # 42 files formatted (sau sửa một dòng trống test)
uv run mypy                            # 18 source files, passed
uv lock --check                         # 75 packages, passed
uv run alembic current                 # trước: 0001_core
uv run alembic upgrade head            # additive; thành công
uv run alembic check                   # No new upgrade operations detected
git diff origin/main --check           # passed
```

Tests PostgreSQL dùng DB mới riêng, tên tuyensinh_test_*; giữ lại DB test, không xóa DB hiện có. Tests và CI mặc định không dùng Internet. Đã kiểm: upgrade DB trống và 0001 có dữ liệu; 31 bảng gốc và constraints/Decimal/health; URL business params/loops/Unicode; allowlist/public-IP/multicast/DNS pin; robots wildcard; hai workers/leases/fencing; limiter giữa runs; Retry-After giây/ngày HTTP; 403/CAPTCHA; 304 HTML tiếp tục khám phá attachment; lịch riêng; A→B→A; unconditional7ngày; retry sau snapshot commit; size/MIME/truncation/deadline/storage hash và chặn thư mục source.

Không coi unit/fake-server tests là bằng chứng tải HTTP của mọi trường. Không có load test, restore drill, phân quyền production hoặc browser adapter. Code review độc lập qua filesystem không chạy được vì sub-agent chờ quyền đọc. Review trực tiếp các đoạn transport/lease/limiter tìm thấy lỗi lease hết retry làm worker thoát sớm dù còn task sẵn sàng; đã tái hiện bằng test thất bại và sửa thành tiếp tục chọn task. Đây là review giới hạn các đoạn code, không phải nghiệm thu toàn repository.

## Pilot có giới hạn

Host duy nhất: tuyensinh.ptit.edu.vn. Preflight run `3e9e5362-d538-4512-8b36-71eb7b370a66`, budget2, dùng1request robots HTTP200. Robots không cấm ba seed, SHA-256 e014272f6d2e2f068146055fc0ce99170f41a9e90c01f7d4c0a83cbe45482949. Nội dung robots và trạng thái lưu riêng trong host cache/raw. Robots không phải giấy phép snapshot/tái phân phối.

Content run `6ee6fd0d-60ae-4858-94ef-733967012bf5`, budget5, dùng đúng5 requests, tất cả HTTP200: 3 HTML năm2024/2025/2026 và 2 PDF khám phá trên host đã allowlist. Tổng cả preflight: 6 fetch, 6 snapshot, 2.274.721 bytes. Đã đọc lại cả6 blobs và kiểm hash/kích thước. Raw được lưu dưới state/raw bị Git bỏ qua.

Run dừng ở paused/budget_exhausted: 5 jobs succeeded, 3 queued, 1 retry_wait. Bốn task chưa tải được giữ để resume có chủ ý; không tăng budget tự động. Không lỗi mạng/HTTP trong pilot. Hai PDF mới là attachment raw chưa xác minh phạm vi/nội dung; một tên file có “thuong-xuyen”, cần reviewer phân loại trước khi ingest. Không coi mọi link trên một trang là dữ kiện tuyển sinh chính quy đã xác minh.

| URL | MIME | Bytes | Snapshot UUID | SHA-256 |
|---|---|---:|---|---|
| https://tuyensinh.ptit.edu.vn/robots.txt | text/plain | 122 | 6755f9a2-bd3c-4481-994a-53bc89d1b390 | e014272f6d2e2f068146055fc0ce99170f41a9e90c01f7d4c0a83cbe45482949 |
| https://tuyensinh.ptit.edu.vn/thong-tin-tuyen-sinh-dai-hoc-chinh-quy-nam-2025/ | text/html | 133045 | f24ff931-d2c7-4761-8cc0-b60d91d75348 | 4055770100438ed935348e7e89b7728624211fde6354f832558b8c1eec829d72 |
| https://tuyensinh.ptit.edu.vn/de-an-tuyen-sinh/de-an-2024/ | text/html | 136022 | ce670b50-64dc-41b3-b25f-c7509bdb3b95 | 199a58f9dca0095596e8c710379daaf9d31eb615c6760eccfa1d25c1db85dd0a |
| https://tuyensinh.ptit.edu.vn/de-an-tuyen-sinh/thong-tin-tuyen-sinh-dai-hoc-chinh-quy-nam-2026/ | text/html | 240945 | 19a1088e-6412-49e4-b911-73ec9146f4fa | 03a243b651c18fd2e89beb89676e2adb9722c66922d8e1758138c6c1bb7b7586 |
| https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2025/05/6.-Thong-tin-tuyen-sinh-DHCQ-nam-2025-1.pdf | application/pdf | 1099134 | f02f3e8f-b7bb-4e36-a60e-9a683afba099 | 11515001282b4626f76ba32c72cf2bd7a89a5fa677dc10ae63b9ad091f37786b |
| https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2026/04/QD1192.-Thong-tin-TSDH-thuong-xuyen-1.pdf | application/pdf | 665453 | 4522117e-4068-4559-a9cf-5bb2e9374ac2 | 7b4b7c433e4c78c77f65ca11c5ceb85bbc8c707f2f2e030c7ab26a01820c62f6 |

Replay đã chạy không gọi Internet:

```powershell
uv run python -m services.crawler replay f24ff931-d2c7-4761-8cc0-b60d91d75348
# hash_valid=true, byte_size=133045, facts_written=0
```

## Đánh giá từng task

- T01: có inventory12nguồn và validation; 2 candidate,9 checked,1 eligible cho pilot nội bộ. 11 robots chưa kiểm trực tiếp; quyền dùng thương mại/lưu/tái phân phối, mapping trường, coverage đầy đủ và kiểm chứng facts còn thiếu. Không đánh dấu hoàn tất T01.
- T03: nền frontier/leases/public-network policy/robots/shared host budget/redirect/retry đã có bằng chứng offline và pilot. Chưa nghiệm thu vận hành quy mô lớn; chưa có JS adapter/daemon scheduler, metric/dashboard và distributed fault/load tests. Không tuyên bố hoàn tất mọi nội dung T03 của WBS.
- T04: downloader HTTP và raw immutable/validators/304/attachment schedule/A→B→A/recovery/replay đã kiểm chứng. Chỉ hai PDF được tải thật; XLSX/JSON thực tế, encoding ngoài identity, remote object storage/backup-restore và review nội dung còn thiếu. Không có parser nghiệp vụ; không tăng quota.
- T19: workflow nền đã có, dùng PostgreSQL riêng và fixtures offline. Kết quả Actions sau push phải kiểm tra trên đúng commit; tại thời điểm viết báo cáo chưa push nên chưa có kết luận CI GitHub. Trạng thái thực tế được bàn giao trong hội thoại/Actions.

## Kiểm tra lại

Dùng README để cài dependency, upgrade migration và chạy bộ checks. Không chạy start nếu chỉ muốn kiểm tra local. stats/replay không crawl Internet. Run pilot hiện đang paused; xem:

```powershell
uv run python -m services.crawler stats 6ee6fd0d-60ae-4858-94ef-733967012bf5
uv run python -m services.crawler replay f24ff931-d2c7-4761-8cc0-b60d91d75348
```

Chỉ khi muốn tải tiếp, chạy resume với additional-budget rõ ràng theo README. Bước tiếp theo là review quyền/coverage/các attachment và định nghĩa parser T05–T08, vẫn giữ raw tách biệt khỏi canonical publication.
