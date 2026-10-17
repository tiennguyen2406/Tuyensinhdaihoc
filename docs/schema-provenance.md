# Căn cứ schema

Nguồn đã đọc: `Overview Detailed Software Rules.md`, tiêu đề EduRadar — System Architecture & Data Algorithms, v1.0 ngày 16/10/2026.
SHA-256 toàn bộ tệp nguồn: `c3745329543e433bd62cf58e4a6df4c827ea54b5876f48f8c42e33d5aabf04c5`.
DDL mục 4.2–4.5 (31 bảng) được trích nguyên văn vào `services/api/alembic/versions/0001_core.sql`; chỉ bỏ BEGIN/COMMIT để Alembic quản lý transaction.
Kế hoạch đối chiếu: `Software Development Plan.md` trên Desktop, WBS T01–T19.

Repository chưa có `EduRadar_System_Design_Implementation_Plan(1).md` hay `EduRadar_tom_tat_du_an_va_dac_ta.md`. Bản Overview có cùng tiêu đề/phiên bản và toàn bộ DDL được kế hoạch dẫn chiếu, nhưng chưa thể xác nhận byte-identical với tệp mang tên gốc. Cần cung cấp các tệp đó để đối chiếu cuối cùng. Không chỉnh sửa sources/.

Đây là baseline kỹ thuật theo DDL được cung cấp, không phải xác nhận nguồn tuyển sinh, scale, scoring/conversion rule hay quyền publication. Không seed dữ liệu ví dụ; catalog_state=0 là trạng thái vận hành duy nhất được khởi tạo theo DDL.
