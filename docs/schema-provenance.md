# Căn cứ schema

Agent đã đọc `Overview Detailed Software Rules.md`, tiêu đề EduRadar — System Architecture & Data Algorithms, v1.0 ngày 16/10/2026, và `Software Development Plan.md` trên Desktop (WBS T01–T19).
SHA-256 toàn bộ bản Overview: `c3745329543e433bd62cf58e4a6df4c827ea54b5876f48f8c42e33d5aabf04c5`.
DDL mục 4.2–4.5 (31 bảng) được trích vào `services/api/alembic/versions/0001_core.sql`; chỉ bỏ BEGIN/COMMIT để Alembic quản lý transaction.

Đối chiếu bổ sung ngày 17/10/2026 do chủ dự án cung cấp: DDL trong 0001_core.sql khớp 31 bảng của `EduRadar_System_Design_Implementation_Plan(1).md` sau khi bỏ comment, khoảng trắng và BEGIN/COMMIT; SHA-256 bản gốc là `C3745329543E433BD62CF58E4A6DF4C827EA54B5876F48F8C42E33D5AABF04C5`, trùng checksum phía trên. Đây là bằng chứng đối chiếu DDL/checksum do người dùng xác nhận, khác với việc agent tự đọc và xác minh toàn bộ tài liệu mang tên gốc.

Tệp mang tên gốc và `EduRadar_tom_tat_du_an_va_dac_ta.md` chưa hiện diện trong repository; chưa xác minh độc lập toàn bộ nội dung ngoài DDL giữa các bản. Không sửa 0001 đã áp dụng hoặc sources/ chỉ vì tên tài liệu khác nhau.

`0002_crawler` mở rộng vận hành T03/T04: crawl_runs, crawl_host_states, crawl_schedules. Ba bảng này không được tính vào 31 bảng DDL gốc. Migration chỉ thêm bảng; metadata và upgrade từ 0001 được kiểm thử riêng.

Đây là baseline kỹ thuật, không xác nhận nguồn tuyển sinh, scale, scoring/conversion rule hay quyền publication. Không seed dữ liệu ví dụ tuyển sinh. catalog_state=0 là trạng thái vận hành được khởi tạo theo DDL; crawler chỉ ghi raw metadata và giữ sources unverified.

## T08 — additive guards, không thay DDL gốc

`0003_publication` thêm PostgreSQL functions/triggers bảo vệ audit/manifests và T08-managed publication history. Không thêm bảng, sửa 0001/0002 hoặc chuẩn hóa dữ liệu cũ. Metadata vẫn 34 bảng (31 core + 3 crawler); review decisions, registry versions, publication requests và queued refresh dùng ingest_jobs hiện có. Schema diff Alembic không tự phản ánh trigger semantics; tests publication dùng non-superuser roles kiểm riêng. Căn cứ DDL/checksum phía trên vẫn là hồ sơ lịch sử, không được viết lại theo HEAD T08.
