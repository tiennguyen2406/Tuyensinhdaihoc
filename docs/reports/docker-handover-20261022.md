# Bàn giao Docker cho kỹ sư mới — 22/10/2026

Baseline `b59c414ac6cdb58ee18a4a4cd0bccfb9d456a069`, branch `codex/crawler-pilot`.
Owner đã xác nhận thiết kế: DB mới tách biệt → init migration/reader → API → Next.js;
không mang dữ liệu/secrets DEV cũ. Checkout build/test riêng, không sửa volume cũ.

## Đầu ra

- Root docker-compose.yml và Dockerfile Python/Node, startup theo health/completion.
- Python3.12.15/uv0.13.1 và Node24.22.0/pnpm11.25.0; dùng lockfiles hiện có.
- requirements.txt xuất từ uv.lock; không có source dependency thứ hai quản lý tay.
- .env.example mọi giá trị thật để trống, ba secrets bắt buộc, các default trong README.
- .gitignore/.dockerignore, LF cho Docker/web, extensions VS Code portable.
- README/HANDOVER hiện trạng có template tiếp nhận, lệnh operator/Git/checks.
- README pipeline trước được bảo toàn ở docs/operator-pipeline.md, ghi rõ lịch sử.
- CI bổ sung docker-handover để build/start/smoke stack rỗng và kiểm bootstrap.

Init là operator one-shot, không chạy trong API request. Chỉ nó nhận owner DB;
API chỉ nhận credential reader, cả API/web chạy OS user không root. Postgres không
publish host port; web/API chỉ loopback. Đây là bộ DEV, không public deployment.

## Kiểm chứng và phạm vi

Local Docker build dùng nguồn clone, không host node_modules/.env/raw. Phát hiện
và sửa COPY thiếu pnpm-workspace.yaml (allowBuilds hiện có), không mở tất cả scripts.
Test proxy được cô lập API_INTERNAL_URL để unit test không phụ thuộc origin Docker.
LF scope apps/web khắc phục khác biệt Windows checkout với Prettier trong Linux;
không thay nội dung các frozen business artifacts hoặc lockfiles.

Stack test `eduradar-handover-verify` dùng volume mới, host ports18000/13000.
Up --wait đạt DB/API/web healthy và init exit0. Smoke live/ready, direct programs,
web proxy programs và /majors HTTP200; items=[] trên catalog mới. Không seeded facts,
không dùng dữ liệu PTIT hoặc mock để làm smoke này. Không real-data advice E2E.

Test mới kiểm reader provisioning lặp lại, quoted password, không superuser/
CREATEDB/CREATEROLE/BYPASSRLS, có SELECT và không mutation/private jobs; chặn reuse
owner. Test trên PostgreSQL riêng, không fixture DEV. API UID10001/reader xác minh
trong container. Ruff check/format158files và mypy86sources đạt trong image API.
Web image cuối:41unit tests, ESLint, Prettier và Next build/TypeScript đạt; smoke
HTTP trên final web image đạt lại. Init đã chạy lại thành công trên cùng volume test,
không thêm facts. CI sau cùng ghi ở final bàn giao và exact-SHA Actions, không tạo
vòng commit nhúng SHA của chính report.

Kiểm chứng installation rỗng không thay nghiệm thu F1/F2/nghiệp vụ hoặc khẳng định
quota đã tăng. Quyết định K/P-B/S1/I1/C1 giữ nguyên; rights vẫn procedural hold,
existing3facts disposition pending. Catalog/release máy cũ không được đo lại.

## Đồng bộ và ZIP

Stage exact public task files, không .vscode/settings.json, .env, raw/packets/private
state/dumps hoặc các handoff/reports cũ đang untracked. Các thay đổi public trước
đó đã nằm trong baseline Git. Không dùng git add . hoặc zip nguyên working tree.

ZIP được tạo từ exact Git blobs của commit bàn giao, gồm tài liệu/config/entrypoints,
dependency manifests/locks và manifest SHA256 từng file. Người nhận clone đúng commit;
ZIP không chứa toàn source hoặc dữ liệu, không cần chép đè khi clone đúng phiên bản.
Secret/DB/private evidence phải được owner bàn giao theo quyền và kênh riêng.

Dashboard ngoài Git: subtask Docker-handover thuộc P0-4, technical verification riêng,
parent vẫn needs_review; không đóng F1 hoặc tăng metrics dữ liệu. Bốn next giữ các
việc hiện hữu: disposition3facts → ownerrights basis → remainingcohort review/
publication conditional → nationaltranche. Không lấy việc Docker chạy được thay
business approval.
