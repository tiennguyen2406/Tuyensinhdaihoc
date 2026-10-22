# Quy trình hoàn tất nhiệm vụ EduRadar

- Giao tiếp và báo cáo cho người dùng bằng tiếng Việt; giữ nguyên identifiers,
  commands và paths khi cần. `sources/` chỉ đọc.
- Sau mỗi nhiệm vụ, cập nhật bản tiến độ/bàn giao công khai ngắn: công việc thực,
  checks đã chạy, giới hạn và bước tiếp theo. Blocker bên ngoài phải được ghi thật.
- Người dùng đã cho phép tự đồng bộ GitHub: review và stage **đúng từng file công
  khai thuộc nhiệm vụ**, kiểm actual index/line endings/links, commit với mô tả đúng,
  normal non-force push lên task branch đã xác minh. Không hỏi lại commit/push.
- Xác minh remote branch SHA bằng commit đã push và push-triggered GitHub Actions
  đúng SHA; cả `checks` và `web` phải success mới gọi integration đã kiểm chứng.
  Sửa failure do thay đổi gây ra bằng corrective commit/push và kiểm lại.
- Nếu auth/network/branch protection chặn, giữ local commit và báo blocker đã làm
  sạch; không gọi local-only là pushed. Không tạo vòng commit tài liệu chỉ để nhúng
  SHA/CI của chính commit đó. Không tự merge main, force-push, rewrite hoặc deploy.
- Bảo toàn công việc có sẵn; không reset/clean/stash hoặc stage việc không liên quan.
  Không commit settings cá nhân, credentials, private state/raw/packets/dumps/signed
  URLs. Dùng exact allowlist, không `git add .` hoặc stage rộng thư mục.
- Đồng bộ GitHub không cấp business approval, data rights, canonical publication
  hoặc direct-total eligibility. Giữ API fail-closed khi chưa đủ approved gates.
- Dùng checks phù hợp; full DB suite chạy trong disposable CI PostgreSQL, không
  dùng DEV làm fixture hoặc đòi DEV khỏe để đồng bộ code đã có. Giữ frozen evidence,
  approvals và release v3; đọc thêm `apps/web/AGENTS.md` trước khi sửa web.

Chính sách trên ghi nhận ủy quyền thường trực ngày 22/10/2026, thay các lệnh cấm
commit/push theo nhiệm vụ trong hồ sơ cũ; các giới hạn bảo mật/nghiệp vụ vẫn giữ.
