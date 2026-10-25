# HANDOVER — EduRadar

Ngày bàn giao: 22/10/2026 (+07:00). Đây là bản hiện trạng có chỗ để kỹ sư mới điền khi tiếp nhận; các trường [điền] chưa phải thông tin đã xác minh.

| Mục | Giá trị |
| --- | --- |
| Repository | https://github.com/tiennguyen2406/Tuyensinhdaihoc |
| Nhánh tiếp tục | `codex/crawler-pilot` |
| Baseline trước task Docker | `b59c414ac6cdb58ee18a4a4cd0bccfb9d456a069` |
| Commit bàn giao | Xem `git rev-parse HEAD`, CI đúng SHA và manifest trong ZIP |
| Người bàn giao / người nhận | [điền họ tên và kênh liên hệ riêng] |
| Máy/ngày tiếp nhận | [điền] |

## Tính năng đã có

- FastAPI/PostgreSQL, Alembic và health/readiness; catalog reader riêng.
- Next.js tra cứu trường, chi tiết Offering/cutoff và `/majors` tìm theo tên chương trình xuyên catalog theo năm. Không coi tên trùng là Major chuẩn dùng chung.
- Cursor/version, DATASET_CHANGED, hiển thị provenance và empty state; real F1 smoke PTIT2024 đã được ghi nhận ở phiên DEV trước.
- Pipeline raw → parser → normalization → resolution → review/publication, immutable internal release và audit/versioning đã có pilot. Tự động mở web không chạy pipeline.
- Bộ Docker mới: PostgreSQL → one-shot migration/reader → API → web. DB mới rỗng; bootstrap không seed facts. Dùng locks Python/Node, images chạy app user không-root.

“Đã có” không đồng nghĩa toàn F1/F2/Phase1 được nghiệm thu. Số canonical lịch sử là3/20.000, catalog3/releasev3 ở DEV cũ, **không phải phép đo mới của bản clone**. Các bài test/mock/CI không thay nghiệm thu nghiệp vụ hoặc real advice E2E.

## WIP và nhánh

| Công việc | Trạng thái / nơi tiếp tục |
| --- | --- |
| P1-B5 quyền nguồn | P-B đã chọn: phải có documented applicable permission hoặc basis được qualified reviewer xác nhận trước fact mới serving, kể cả DEV |
| Ba facts PTIT2024 ở máy cũ | Disposition riêng còn pending; runtime cũ được báo không còn listener8000/3000 ở phiên gần nhất, không coi đó là pause đã được owner duyệt |
| Scale PTIT2026 | K xác nhận đề xuất [0,30]/basis đúng pilot QTKD/BVH/THPT; chưa bootstrap, không áp tự động5dòng còn lại |
| Cohort PTIT2026 |6candidate đã chuẩn bị;0publication-ready/0new facts ở bàn giao trước; TTNV từng dòng khác nhau |
| Nguồn quốc gia |12profiles hiện hữu,5discovery leads mới; directory405đơn vị chỉ làm đầu mối, không phải405trường đã xác minh |
| Taxonomy/học phí/F2 | Taxonomy/binding chưa hoàn chỉnh; tuition DTO còn null; F2 positive advice deferred |
| Nhánh cho WIP trên | `codex/crawler-pilot`; không tự merge main |

Nguồn chuẩn: [progress](docs/reports/progress-20261022.md), [K/P-B receipt](docs/reports/p1-b5-confirmation-20261022.json), [existing rights](docs/reports/p1-b5-existing-rights-20261022.md). Public reports đủ để hiểu trạng thái; private packets/commands/approvals phải xin owner qua kênh riêng trước khi thực thi dữ liệu thật.

## API, dịch vụ và thông tin tài khoản

| Dịch vụ | Thông tin bàn giao an toàn |
| --- | --- |
| GitHub | Owner namespace `tiennguyen2406`, repoTuyensinhdaihoc. Người nhận dùng tài khoản cá nhân, owner cấp quyền collaborator riêng; không chia token/password |
| Docker | Docker Desktop Linux containers, registry Docker Hub và GHCR tải base images. Máy nhận tự đăng nhập nếu registry yêu cầu; không kèm credential registry |
| PostgreSQL mới | Owner/reader tự tạo từ `.env`; default tên trong README. Không dùng credential máy cũ |
| API/web local | API127.0.0.1:8000; web127.0.0.1:3000; đổi host ports qua env. Không có API key dịch vụ trả phí bắt buộc cho tra cứu hiện tại |
| Nguồn tuyển sinh/MoET/trường | Nguồn công khai để nghiên cứu có allowlist/robots/budget; không phải tài khoản API hoặc license tái sử dụng. Không crawl khi startup |
| Publication/release operators | Dedicated identities riêng, chưa provision trong one-command startup. Owner cấp secret/capability riêng theo runbook; không biến API thành publisher |

Secret inventory (không điền giá trị vào file này): POSTGRES_PASSWORD, CATALOG_DB_PASSWORD, CATALOG_CURSOR_SECRET; PUBLICATION_DB_* và RELEASE_DB_* nếu được giao vai trò. Người giữ secrets [điền], kênh lưu/chuyển bảo mật [điền], ngày rotation [điền]. `.env`, raw, state, dumps, private sheets không thuộc Git/ZIP.

## Bug, giới hạn và việc cần fix

| Vấn đề | Tình trạng / ưu tiên |
| --- | --- |
| Rights policy chưa là runtime guard | Procedural hold; nhãn internal_dev_only không ngăn public exposure. Không deploy public theo configDEV |
| Existing facts disposition | Cần owner chọn hướng và deadline; không tự withdrawal/xóa/sửa lịch sử |
| Dashboard overflow | Bản tracker riêng từng đo37px ở360px; không suy web `/majors` bị cùng lỗi |
| Coverage thấp | Chỉ pilot lịch sử ở DEV, clone mới rỗng; không seed dữ liệu để che empty state |
| Starlette/httpx warning | Warning lịch sử trong tests; theo dõi upstream/compatibility, chưa gọi đã fix |
| Real advice E2E/production auth | Chưa hoàn chỉnh; mock browser success không chứng minh tư vấn thật hoặc production RBAC |
| Scan/OCR và sources blocked | Cần workflow review riêng; không bypass robots/CAPTCHA/TLS/allowlist |

Bug mới khi tiếp nhận: [mô tả, cách tái hiện, môi trường, severity, owner, link issue, trạng thái].

## Checklist kỹ sư nhận bàn giao

- [ ] Clone đúng branch/commit, kiểm GitHub Actions đúng SHA.
- [ ] Tạo secrets mới, chạy `docker compose up -d --build`, init exit0, API/web healthy.
- [ ] Mở `/majors`, API readiness và catalog rỗng hợp lệ; ghi ngày/môi trường kiểm.
- [ ] Chạy test bằng DB test riêng theo README, không dùng fixture trên DEV cũ.
- [ ] Đọc P-B/K/receipts và liệt kê private material còn thiếu; không chạy business commands trước approval.
- [ ] Xác nhận quyền GitHub và nơi quản lý secrets, backup/restore được owner giao riêng.
- [ ] Ghi mục tiêu task đầu tiên, người review và tiêu chí xong; không hỏi lại quyết định đã được ghi receipt.

Backup DB/raw và onboarding dữ liệu thật là task riêng cần rights/access/owner authorization. Không có dump hoặc password trong bundle; không khôi phục volume cũ bằng hướng dẫn tự động của Docker mới.
