# Pilot source review — 2026-10-17

Inventory gồm 12 trường/nguồn chính thức; không seed URL minh họa. Mỗi profile qua SourceProfile và JSON Schema. university_key chỉ là ID registry nội bộ, chưa phải mapping trường đã duyệt. years là phạm vi mục tiêu; observed_years là năm quan sát qua trang/link/index, không xác nhận toàn bộ nội dung của từng năm. publication_scope/evidence_urls trong CSV ghi rõ nội dung đã mở được và phần chỉ được dẫn link/index. HTML/PDF được ghi theo bằng chứng; chưa tìm thấy feed XLSX/JSON đã kiểm tra. Profiles không tự gán nguồn verified.

Hai ứng viên HUST/HaUI còn chờ mở trang gốc thành công. Các nguồn checked chỉ đã xem một phần trang/tài liệu bằng công cụ web, chưa đồng nghĩa đã đủ quyền crawl. Robots của cả 12 nguồn từng không truy cập được bằng công cụ nghiên cứu (lỗi công cụ, không phải HTTP từ chối); trạng thái thực tế của host pilot sẽ được bổ sung sau preflight. Các host/CDN khác chỉ quan sát trong liên kết được tách khỏi allowlist. Chỉ host chính xác trong profile được phép; chưa cho phép Google Drive, portal hồ sơ thí sinh hoặc CDN chưa kiểm tra.

PTIT được chọn có điều kiện vì ba trang HTML 2024/2025/2026 cùng host tuyensinh.ptit.edu.vn đã mở được. Không truy cập xettuyen.ptit.edu.vn hoặc biểu mẫu đăng nhập/đăng ký. Chỉ ba path seed và tài liệu PDF/XLS/XLSX dưới wp-content/uploads được khám phá; run budget giới hạn thêm. Không có quyền tự động tải hoặc license lưu/tái phân phối được nhà xuất bản cấp đã được tìm thấy. Hành động tải raw nội bộ giới hạn do chủ dự án yêu cầu; robots allowance chỉ là điều kiện kỹ thuật, không phải license. Raw giữ riêng, không commit/tái phân phối. Cần làm rõ quyền lưu/dùng thương mại trước khi mở rộng hoặc công bố dataset.

UEH có trang https://ueh.edu.vn/personaldata/ dẫn chính sách dữ liệu cá nhân; chưa có căn cứ cho phép crawler/snapshot từ trang đó. DUT hiển thị copyright của đội CNTT trên sổ tay, không phải giấy phép tái sử dụng. Không tìm thấy điều khoản trong phần trang đã kiểm tra không chứng minh rằng không có điều khoản khác.

Bằng chứng preflight/pilot, HTTP status, robots hash, số request/snapshot và lỗi được ghi ở reports/crawler-pilot.md sau khi bộ kiểm thử offline đạt. Không dùng dữ liệu nguồn tải về để đạt quota 20.000; không ghi canonical cutoffs.

## Direct robots preflight

2026-10-17T11:59:00Z, run `3e9e5362-d538-4512-8b36-71eb7b370a66`: 1 request trong budget 2, HTTP 200. Robots SHA-256 `e014272f6d2e2f068146055fc0ce99170f41a9e90c01f7d4c0a83cbe45482949`. Disallow /wp-admin/, Allow /wp-admin/admin-ajax.php; cả ba seed path được Protego cho phép với User-Agent TuyenSinhDaiHocPilot/0.1. Không công bố rằng được cấp quyền lưu/tái phân phối. PTIT được nâng eligible chỉ cho pilot raw nội bộ giới hạn; 11 nguồn khác giữ nguyên trạng thái. Cache hết hạn vẫn phải lấy lại robots.
