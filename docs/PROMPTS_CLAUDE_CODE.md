# Prompt dùng với Claude Code trong VS Code (EduRadar V2)

Dán từng prompt vào ô "Ask Claude to edit…". Chọn chế độ "Edit automatically" để Claude sửa file trực tiếp.
Claude tự đọc CLAUDE.md nên không cần giải thích lại dự án.

## 1. Lưu code lên GitHub (làm trước tiên)
Tạo nhánh v2-simple từ nhánh hiện tại, add đúng các file V2: AGENTS.md, CLAUDE.md, README_V2.md, .gitignore,
crawler/, pipeline/, sna/, webapp/, data/manual/, docs/PROMPTS_CLAUDE_CODE.md, docs/AGENTS_old_v1.md.
Không add data/raw, data/eduradar.db, .venv, _to_delete. Commit "EduRadar V2: crawler API, pipeline, web, SNA"
rồi push lên origin. Cho tôi xem git status trước khi commit.

## 2. Tăng tỉ lệ map ngành chuẩn
Mở data/interim/major_unmatched.csv (tên ngành chưa có major_code) và data/clean/majors.csv.
Với mỗi tên ngành chưa map, đề xuất major_code phù hợp nhất trong majors.csv (chỉ khi chắc chắn; không chắc thì bỏ trống).
Ghi kết quả vào data/manual/major_map.csv (cột name_key,major_code). Kiểm thêm các dòng match_how = "chua_ten_chuan"
và "ten_gan_dung" trong data/clean/admissions.csv: liệt kê các map sai rõ ràng (ví dụ "Quản lý công nghiệp" → "Quản lý công")
và thêm bản sửa vào major_map.csv. Chạy lại pipeline.clean và báo tỉ lệ map trước/sau.

## 3. Soát lỗi giao diện web
Đọc webapp/static/app.js, index.html, style.css và webapp/main.py. Chạy uvicorn và gọi thử các API
(/api/meta, /api/universities?q=bach khoa, /api/universities/BKA/scores?year=2026, /api/majors/7480201/scores?year=2025,
/api/advice?method=THPT&score=24&combo=A00). Sửa lỗi tìm được; cải thiện: hiển thị tốt ở màn hình hẹp,
thêm nút "Xuất CSV" cho mỗi bảng, ô tìm ngành cho phép tìm theo tên chương trình gốc khi ngành chưa map.

## 4. Kiểm tra độ chính xác dữ liệu
Lấy ngẫu nhiên 20 dòng từ data/clean/admissions.csv (seed 42, trải đều các phương thức), xuất bảng gồm trường, năm,
phương thức, ngành, điểm, source_url vào docs/kiem_tra_20_dong.md để tôi đối chiếu tay với trang gốc.
Thêm cột "Đúng/Sai" để tôi điền.

## 5. Viết phần báo cáo làm sạch dữ liệu
Dựa trên pipeline/clean.py và data/clean/quality_report.md, viết docs/bao_cao_lam_sach.md bằng tiếng Việt:
nguồn dữ liệu và cách thu thập (API, số request, thời gian), từng bước làm sạch và chuẩn hoá kèm số dòng bị ảnh hưởng,
định nghĩa 1 record, cách map mã ngành, giới hạn còn lại. Có bảng và số liệu thật, không bịa.

## 6. Viết phần báo cáo SNA
Dựa trên sna/build.py, data/network/summary.csv và các file data/network/metrics/*.csv, viết docs/bao_cao_sna.md:
mô tả 4 mạng G1–G4 và lý do chọn; bảng độ đo toàn mạng (density, path length, diameter, clustering, modularity…)
theo năm; top 10 theo degree, betweenness, closeness, eigenvector, PageRank, HITS kèm diễn giải ý nghĩa;
so sánh Louvain vs Girvan–Newman; nhận xét HITS authority tương quan âm còn PageRank tương quan thuận với điểm chuẩn
(giải thích và đề xuất chuẩn hoá trọng số); thay đổi 2024→2026; chèn hình từ data/network/fig/.

## 7. Thử nghiệm độ nhạy tham số SNA
Chạy sna.build với --jaccard 0.15, 0.25, 0.35 và --gap 1, 2, 3 (ghi ra thư mục riêng, không ghi đè kết quả chính).
Lập bảng so sánh số cạnh, modularity, số cộng đồng, Spearman PageRank/authority. Viết kết luận ngắn vào docs/do_nhay_sna.md.

## Mẹo
- Nếu Claude định thêm tầng/quy trình phức tạp: nhắc "theo CLAUDE.md, giữ kiến trúc V2 đơn giản".
- Mỗi lần xong, yêu cầu: "chạy lại lệnh liên quan và báo con số trước–sau".
