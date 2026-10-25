# Kiểm tra báo cáo đồ án EduRadar

Ngày kiểm: 25/10/2026 (UTC+7). Chạy `python scripts/check_report.py` để tái kiểm dữ liệu và cấu trúc.

## 1. Đối chiếu yêu cầu đề bài

| Yêu cầu | Mục | Bằng chứng và kết quả |
| --- | --- | --- |
| (1) | Chương 1 | Có bối cảnh, chủ đề, 5 câu hỏi nghiên cứu, phạm vi; trả lời ở Chương 7. |
| (2) | 2.1–2.6, Phụ lục A–C | Có nguồn, crawl, định nghĩa record, làm sạch/chuẩn hoá, chất lượng; 71.011 > 20.000; Hình2.1–2.4. Thiếu lịch sử URL/ngày truy cập/robots của một số nguồn bổ trợ được ghi rõ, không bịa. |
| (3) | 3.1–3.4 | Có 12 tiểu mục độ đo; bảng năm/top10; công thức, hàm, trọng số và giới hạn liên thông; xem bảng dưới. |
| (3') | 4.1–4.6 | Có Louvain, GN, HITS/PageRank, AA, độ nhạy, ứng dụng; AA23% là 2024→2026, đã thêm hai kiểm chứng năm liền kề. |
| (4) | Chương 5 | Có mạng, phân bố, top betweenness, scatter, độ nhạy, web tương tác. Hai ảnh Gephi còn để người thực hiện bổ sung theo yêu cầu. |
| (5) | Chương 6 | URL web thật; 5tab; ảnh1280px,375px; đề án+học phí; kịch bản demo5bước. |

## 2. Kiểm từng độ đo

| Độ đo | Mục | Định nghĩa | Công thức | Số liệu/bảng | Diễn giải |
| --- | --- | --- | --- | --- | --- |
| Degree centrality và Degree distribution | 3.2.1 | Có | Có | Có | Có |
| Betweenness centrality | 3.2.2 | Có | Có | Có | Có |
| Closeness centrality | 3.2.3 | Có | Có | Có | Có |
| Eigenvector centrality | 3.2.4 | Có | Có | Có | Có |
| PageRank | 3.2.5 | Có | Có | Có | Có |
| HITS | 3.2.6 | Có | Có | Có | Có |
| Density | 3.2.7 | Có | Có | Có | Có |
| Average shortest path length | 3.2.8 | Có | Có | Có | Có |
| Diameter | 3.2.9 | Có | Có | Có | Có |
| Clustering coefficient | 3.2.10 | Có | Có | Có | Có |
| Modularity | 3.2.11 | Có | Có | Có | Có |
| Các độ đo bổ sung | 3.2.12 | Có | Có | Có | Có |

Các hình phân bố: Hình3.2–3.7; mạng và cộng đồng: Hình5.1–5.2; betweenness: Hình5.3; PageRank: Hình5.4; độ nhạy: Hình5.5–5.6. Các độ đo toàn cục có bảng riêng, không cần thêm một hình lặp lại cùng số liệu.

## 3. Số quan trọng và nguồn đối chiếu

| Chỉ tiêu | Đọc lại từ nguồn | Mốc trong báo cáo | Nguồn | Kết quả |
| --- | --- | --- | --- | --- |
| Dòng sạch | 71011 | 71011 | DB: admissions COUNT(*) | Khớp |
| Trường có điểm | 292 | 292 | DB: admissions DISTINCT uni_code | Khớp |
| Dòng map ngành | 69276 | 69276 | DB: admissions major_code NOT NULL | Khớp |
| Dòng chưa map | 1735 | 1735 | DB: admissions major_code NULL | Khớp |
| Mã ngành | 472 | 472 | DB: majors COUNT(*) | Khớp |
| Lượt dòng–tổ hợp | 264630 | 264630 | DB: admission_combos COUNT(*) | Khớp |
| Tổ hợp đang dùng | 385 | 385 | DB: admission_combos DISTINCT combo | Khớp |
| Hạng VNUR gồm kế thừa | 149 | 149 | DB: universities vnur_rank | Khớp |
| Học phí bộ đầu | 203 | 203 | DB: tuition COUNT(*) | Khớp |
| Dòng năm 2024 | 18590 | 18590 | DB: admissions GROUP BY year | Khớp |
| Dòng năm 2025 | 24234 | 24234 | DB: admissions GROUP BY year | Khớp |
| Dòng năm 2026 | 28187 | 28187 | DB: admissions GROUP BY year | Khớp |
| Cờ ok | 69893 | 69893 | DB: admissions GROUP BY flag | Khớp |
| Cờ thang_khac_30 | 1113 | 1113 | DB: admissions GROUP BY flag | Khớp |
| Cờ diem_thap_bat_thuong | 3 | 3 | DB: admissions GROUP BY flag | Khớp |
| Cờ outlier | 2 | 2 | DB: admissions GROUP BY flag | Khớp |
| ma_7_so | 56418 | 56418 | DB: admissions.match_how | Khớp |
| dau_ten_chuan | 1182 | 1182 | DB: admissions.match_how | Khớp |
| Tác vụ tải điểm | 921 | 921 | data/raw/fetch_log.csv: số dòng | Khớp |
| Dòng thô | 76726 | 76726 | fetch_log.csv: SUM(rows) | Khớp |
| Tác vụ rỗng | 88 | 88 | fetch_log.csv: rows=0 | Khớp |
| Lỗi tác vụ | 0 | 0 | fetch_log.csv: error không rỗng | Khớp |
| Dòng summary | 12 | 12 | data/network/summary.csv: số dòng | Khớp |
| g2_uni_uni 2026 nodes | 249.0 | 249 | summary.csv: network=g2_uni_uni, year=2026, nodes | Khớp |
| g2_uni_uni 2026 edges | 2531.0 | 2531 | summary.csv: network=g2_uni_uni, year=2026, edges | Khớp |
| g2_uni_uni 2026 modularity_louvain | 0.4822 | 0.4822 | summary.csv: network=g2_uni_uni, year=2026, modularity_louvain | Khớp |
| g3_major_major 2026 nodes | 377.0 | 377 | summary.csv: network=g3_major_major, year=2026, nodes | Khớp |
| g3_major_major 2026 edges | 1412.0 | 1412 | summary.csv: network=g3_major_major, year=2026, edges | Khớp |
| g3_major_major 2026 modularity_louvain | 0.8363 | 0.8363 | summary.csv: network=g3_major_major, year=2026, modularity_louvain | Khớp |
| g4_competition 2026 edges | 9215.0 | 9215 | summary.csv: network=g4_competition, year=2026, edges | Khớp |
| g4_competition 2026 spearman_authority_vs_avg_score | 0.2343 | 0.2343 | summary.csv: network=g4_competition, year=2026, spearman_authority_vs_avg_score | Khớp |
| g4_competition 2026 spearman_pagerank_vs_avg_score | 0.6069 | 0.6069 | summary.csv: network=g4_competition, year=2026, spearman_pagerank_vs_avg_score | Khớp |
| Đề án 267/292 | 267/292 | 267/292 | docs/TONG_KET_DU_LIEU.md | Khớp |
| Học phí 285/292 | 285/292 | 285/292 | docs/TONG_KET_DU_LIEU.md | Khớp |
| Hạng trực tiếp 95 | 95 hạng trực tiếp | 95 hạng trực tiếp | docs/TONG_KET_DU_LIEU.md | Khớp |
| Hạng kế thừa 54 | 54 đơn vị kế thừa | 54 đơn vị kế thừa | docs/TONG_KET_DU_LIEU.md | Khớp |

Các bảng top10 được xuất/đối chiếu từ metrics với tên trong DB; bảng292trường, mẫu20dòng và năm×phương thức được dựng từ DB. Tỉ lệ map là độ phủ, chưa phải độ chính xác. Kiểm số không đồng nghĩa kiểm chứng từng thông báo tuyển sinh gốc.

## 4. Kiểm cấu trúc và bản Word

| Kiểm tra | Kết quả |
| --- | --- |
| Dòng sạch | Đạt |
| Trường có điểm | Đạt |
| Dòng map ngành | Đạt |
| Dòng chưa map | Đạt |
| Mã ngành | Đạt |
| Lượt dòng–tổ hợp | Đạt |
| Tổ hợp đang dùng | Đạt |
| Hạng VNUR gồm kế thừa | Đạt |
| Học phí bộ đầu | Đạt |
| Dòng năm 2024 | Đạt |
| Dòng năm 2025 | Đạt |
| Dòng năm 2026 | Đạt |
| Cờ ok | Đạt |
| Cờ thang_khac_30 | Đạt |
| Cờ diem_thap_bat_thuong | Đạt |
| Cờ outlier | Đạt |
| ma_7_so | Đạt |
| dau_ten_chuan | Đạt |
| Tác vụ tải điểm | Đạt |
| Dòng thô | Đạt |
| Tác vụ rỗng | Đạt |
| Lỗi tác vụ | Đạt |
| Dòng summary | Đạt |
| g2_uni_uni 2026 nodes | Đạt |
| g2_uni_uni 2026 edges | Đạt |
| g2_uni_uni 2026 modularity_louvain | Đạt |
| g3_major_major 2026 nodes | Đạt |
| g3_major_major 2026 edges | Đạt |
| g3_major_major 2026 modularity_louvain | Đạt |
| g4_competition 2026 edges | Đạt |
| g4_competition 2026 spearman_authority_vs_avg_score | Đạt |
| g4_competition 2026 spearman_pagerank_vs_avg_score | Đạt |
| Đề án 267/292 | Đạt |
| Học phí 285/292 | Đạt |
| Hạng trực tiếp 95 | Đạt |
| Hạng kế thừa 54 | Đạt |
| Không còn số dòng cũ | Đạt |
| Mọi hình nhúng tồn tại | Đạt |
| Đủ 20 dòng kiểm tra | Đạt |
| Có bảng đủ 292 trường | Đạt |
| Độ đo Degree centrality và Degree distribution: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Betweenness centrality: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Closeness centrality: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Eigenvector centrality: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo PageRank: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo HITS: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Density: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Average shortest path length: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Diameter: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Clustering coefficient: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Modularity: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Độ đo Các độ đo bổ sung: mục/định nghĩa/công thức/bảng/diễn giải | Đạt |
| Mục lục tự động TOC | Đạt |
| Công thức Word OMML | Đạt |
| Bảng có header lặp | Đạt |
| Bảng rộng 100% | Đạt |
| Mọi chữ trong bảng kể cả hyperlink là 9pt | Đạt |
| Phụ lục C khổ ngang | Đạt |

Có 26 tham chiếu hình nhúng, 63 bảng Word và 151 công thức OMML. Bảng được kẻ ô, 100%vùng chữ, tiêu đề lặp; công thức không phải ảnh. Hai đường dẫn Gephi dự kiến chưa được nhúng nên không gây liên kết ảnh hỏng.

### Kiểm tra hiển thị

Đã xuất thử bằng Microsoft Word thành PDF **76 trang**, cập nhật mục lục và số trang, rồi render đủ 76 ảnh trang bằng Poppler. `render_docx.py` đã được thử nhưng không chạy được vì môi trường không có LibreOffice (`soffice.exe`); dùng Word có sẵn để kiểm tra bản in.

Đã xem bố cục toàn bộ 76 trang qua bộ ảnh tổng quan; phóng lớn các trang nguồn/bảng dài, bảng độ đo, công thức ARI/NMI, hình mạng và hai trang phụ lục C. Các trang kiểm trọng điểm gồm 6–8, 20–21, 31–39, 43–49, 51–54, 68–76. Không thấy bảng/công thức bị cắt hoặc hình tràn trang trong các trang kiểm. Phụ lục C giữ khổ ngang ở cả hai trang, bỏ cột URL; hàng tiêu đề lặp lại.

Kiểm tra hộp chữ trên PDF bằng pdfplumber: **0 từ nằm ngoài biên trang**. Kiểm XML bản Word cuối: **63 bảng**, **151 công thức OMML**, **26 hình nhúng**, mọi chữ trong bảng kể cả hyperlink là 9pt. Bộ ảnh web chụp lại từ URL công khai gồm 5 tab ở 1280px và ảnh 375px; lượt chụp không có lỗi JavaScript.

Đã sửa hai lỗi qua vòng kiểm: hướng mũi tên sơ đồ chiếu và cỡ chữ trong hyperlink của bảng. Rà soát độc lập đối chiếu toàn bộ ô số Bảng 3.25–3.28 với summary, các bảng top 10 Bảng 3.2–3.15 với metrics, và kiểm lại global bổ sung/local clustering/temporal AA: không phát hiện chênh lệch. Tệp PDF và ảnh trang chỉ phục vụ QA, không nằm trong bộ commit.

## 5. Những chỗ người thực hiện cần tự điền

- Trang bìa: [Họ tên — MSSV], [Lớp], [Giảng viên], [Ngày nộp].
- Mục2.6.2 và Phụ lụcC: kết quả __/20; để trống toàn bộ cột Đúng/Sai cho đến khi đối chiếu nguồn.
- Mục5.4: xuất hai hình Gephi G2/G3 theo hướng dẫn, lưu docs/fig/gephi_g2_2026.png và gephi_g3_2026.png rồi thay hai khối đánh dấu, dựng lại Word.
- Nếu hồ sơ nguồn gốc còn giữ: bổ sung ngày truy cập, URL từng bài đề án/học phí và nội dung robots.txt/Content-Signal lịch sử còn thiếu ở2.1. Các mục này chưa đủ bằng chứng trong nguồn số được phép dùng; không tự điền từ suy đoán.

## 6. Phạm vi thay đổi

Không crawl, không sửa raw/clean/DB hoặc tính lại đè data/network; chỉ thêm báo cáo, hình và script. Không commit raw, DB, .venv hoặc tmp. Thực nghiệm bổ sung được tính đọc từ DB, không thay bộ summary gốc.
