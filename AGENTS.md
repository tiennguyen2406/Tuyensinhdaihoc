# Quy tắc làm việc EduRadar V2 (cho người và AI)

Mục tiêu: đồ án môn SNA — web tra cứu điểm chuẩn 2024–2026 + tư vấn theo điểm + phân tích mạng.
Hạn nộp khoảng 06/11/2026. Ưu tiên chạy được và đủ yêu cầu đề bài, không ưu tiên quy trình.

- Giao tiếp tiếng Việt. Giữ nguyên tên file, lệnh, đường dẫn.
- Kiến trúc cố định, KHÔNG thêm tầng mới:
  `crawler/fetch.py` → `data/raw/` → `pipeline/clean.py` → `data/eduradar.db` (SQLite, 4 bảng)
  → `webapp/` (FastAPI + HTML/JS tĩnh) và `sna/build.py` → `data/network/`.
- Đánh giá mỗi phiên làm việc bằng kết quả đo được: số dòng sạch, tỉ lệ map ngành,
  chức năng web chạy được, độ đo SNA có trong `data/network/summary.csv`.
- Không thêm quy trình duyệt từng fact, receipt, hash, chính sách bản quyền nội bộ.
  Dữ liệu là điểm chuẩn công khai, dùng cho học tập phi thương mại, có ghi nguồn trên web.
- Crawl lịch sự: nghỉ ≥ 1,5 giây giữa các request, tôn trọng robots.txt, không chạy crawl khi mở web.
- Sửa dữ liệu bằng tay qua `data/manual/*.csv`, không sửa trực tiếp `data/clean/` hay DB.
- Code hệ thống cũ (v1) vẫn còn trong `services/`, `apps/`, `docs/` để tham khảo; không phát triển tiếp.
- Commit: chỉ code + `data/manual/`; không commit `data/raw/`, `data/eduradar.db`, `.venv`.
