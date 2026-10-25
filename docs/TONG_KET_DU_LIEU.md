# Tổng kết dữ liệu EduRadar V2

Ngày chạy pipeline: **25/10/2026 (UTC+7)**; `meta.updated_on = 2026-10-25`.
Các số dưới đây được đọc sau khi chạy lại clean → tuition_import → dean → sna.build → export_static từ raw có sẵn. Không crawl lại trong lượt này.

## Điểm chuẩn và tổ hợp

| Chỉ số | Giá trị |
| --- | ---: |
| Mục trong API danh mục trường gốc (mọi loại hình) | 587 |
| Trường đại học được chọn từ nguồn (`level = 2`) | 307 |
| Trường có điểm, dùng làm mẫu số của web | 292 |
| Trường nguồn chưa có điểm | 15 |
| Dòng điểm sạch | 71.011 |
| Dòng map được mã ngành chuẩn | 69.276 (97,56%) |
| Dòng chưa map ngành | 1.735 |
| Ngành chuẩn khác nhau trong toàn bộ ba năm | 472 |
| Năm | 2024, 2025, 2026 |
| Mã tổ hợp xuất hiện trong dữ liệu | 385 |
| Lượt gắn tổ hợp với dòng điểm | 264.630 |
| Mã có tên môn trong danh mục API blocks | 298 |
| Mã vừa có tên môn vừa xuất hiện trong dữ liệu | 253 |
| Mã xuất hiện nhưng chưa có tên môn trong danh mục nguồn | 132 |

| Năm | Dòng điểm | Trường | Ngành chuẩn |
| --- | ---: | ---: | ---: |
| 2024 | 18.590 | 279 | 428 |
| 2025 | 24.234 | 278 | 434 |
| 2026 | 28.187 | 276 | 429 |

Trong 307 trường đại học được chọn từ nguồn, 292 có điểm và 15 chưa có điểm. Số trường/ngành theo năm không cộng thành tổng vì có các mã xuất hiện nhiều năm. Một dòng điểm là trường × năm × phương thức × chương trình × nhóm tổ hợp, sau làm sạch và gộp điểm gốc/quy đổi.

Đã chuẩn hóa chữ O/số 0 trong phần số của mã, chữ hoa và khoảng trắng; BO3 → B03, BO0 → B00, AO1 → A01. Mã chưa có tên môn vẫn nằm trong dữ liệu và truy vấn, chỉ không hiện trong ô chọn. Danh sách chọn lấy đúng phương thức/năm và sắp theo số dòng sử dụng giảm dần. Ví dụ THPT 2026: D01 4.042, A00 3.468, A01 3.459 dòng.

Mã có nhiều định nghĩa chọn định nghĩa có `school_count` lớn nhất trong API blocks. Các định nghĩa và số trường của nguồn nằm trong tooltip; nhãn chọn chỉ có mã và tên môn đã chọn. Không tự bổ sung tên môn cho 132 mã thiếu trong danh mục.

Ngày thu thập điểm trong raw: 23/10/2026, từ 13:51:00 đến 14:20:27 theo trường `crawled_at`. Ngày chạy pipeline là ngày xử lý lại dữ liệu, không phải ngày mọi nguồn vừa được thu thập.

## Đề án HOCMAI

- **267/292 trường (91,44%)** có đề án; 25 trường chưa có.
- 271 bài nguồn; 268 bài ghép vào 267 mã trường, có một mã có hai bài. Ba bài ngoài danh mục điểm được để chưa ghép trong `dean_map.csv`.
- 1.190 mục phương thức; 8.208 gạch đầu dòng trong các nhóm dữ kiện phương thức và phần dùng chung.
- 91 bài có năm tiêu đề khác năm H2 phương thức. Giữ cả hai mốc và ghi chú trên web; không đổi đề án cũ thành năm 2026.
- Chỉ xuất dữ kiện theo heading và link bài gốc, bỏ phần giới thiệu/danh sách ngành; không xuất HTML gốc. Thời gian và hồ sơ chỉ hiện khi nguồn có dữ kiện.

Nguồn và quyết định ghép: `data/raw/dean/`, `data/manual/dean_map.csv`; kết quả sinh ra tại `data/clean/dean.json` và `site/data/dean.json`.

## Học phí theo loại nguồn

**285/292 trường (97,60%) có mức học phí tham khảo**; không có nghĩa tất cả là mức chính thức 2026. Phải giữ năm học, khóa, ngành, loại đơn vị và mức độ bằng chứng tại từng thẻ.

| Loại nguồn | Bộ đầu | Bộ tra tay bổ sung | Tổng mã trường |
| --- | ---: | ---: | ---: |
| Chính thức | 17 | 53 | 70 |
| Văn bản chính thức, bản lưu bên thứ ba | 0 | 4 | 4 |
| Báo chí | 30 | 0 | 30 |
| Trang tổng hợp | 156 | 0 | 156 |
| Tham khảo thứ cấp trong bộ bổ sung | 0 | 25 | 25 |
| Chưa xác minh được mức tiền | 0 | 7 | 7 |
| Tổng số trường trong hai bộ | 203 | 89 | 292 |

Hai bộ không trùng mã trường. 285 trường có mức = 203 bộ đầu + 82 bộ bổ sung có số tiền; bảy mục chưa xác minh có thông báo nhưng không hiện mức tiền. Bảy mã này là **DBH, DKT, DNB, HFH, NHP, NLG, SDU**.

Bộ đầu lưu khoảng triệu đồng/năm, gồm các trường hợp ước tính quy đổi có ghi rõ ở thẻ. Bộ bổ sung giữ nguyên đồng/tín chỉ, học kỳ, tháng, năm, toàn khóa hoặc khoản thu; không quy đổi thành năm.

Đã đọc và ghi overrides cho đủ **32 mục** tại `data/manual/tuition_extra_overrides.json`, chỉ dựa trên mục Mức học phí và Giới hạn trong file người dùng. Importer còn 0 mục cần xem tay; 13 mục nhỏ khác vẫn bỏ bảng theo ngành khi chưa tách được, giữ tóm tắt.

- HHA giữ “gần 700.000 đồng/tín chỉ”, tách mức tiên tiến tiếng Việt/Anh.
- MDA giữ từng nhóm ngành và miễn học phí kỹ sư tài năng đúng năm 2026–2027; không dùng mức cũ.
- KTA, DVB, TDB giữ đơn vị riêng cho từng dòng, không cộng hoặc nhân hai cách thu.
- NTS chỉ có mức tiêu chuẩn ghi đủ đơn vị 28–32 triệu đồng/năm; các khoảng viết tắt sau đó được giữ nguyên số và ghi “không ghi đơn vị trong nguồn”. Bảng là bảng chung FTU, chưa khẳng định mọi chương trình mở ở Phân hiệu TP.HCM; không dùng i-Hons 88 triệu làm trần của NTS.
- SIU ghi rõ biểu đã gồm ưu đãi học bổng và giảm theo cách thanh toán, không gắn nhãn “chưa trừ ưu đãi”.

## VNUR và độ hot

**149/292 trường có hạng**, gồm **95 hạng trực tiếp và 54 đơn vị kế thừa**; 143 trường chưa gắn hạng. Hạng 2026 dùng tham khảo cho mọi năm. Đơn vị kế thừa không được coi là VNUR xếp hạng riêng, huy hiệu và cột tư vấn đều ghi tên đại học mẹ.

`Độ hot = 0,5 × điểm trường + 0,3 × điểm ngành + 0,2 × điểm xu hướng`.

1. Điểm trường: `(101 − hạng)/100`; hạng trực tiếp giữ nguyên, hạng kế thừa nhân 0,8, chưa có hạng = 0.
2. Điểm ngành: percentile mức tăng bậc nút ngành G1 từ 2024 đến 2026, tức thay đổi số trường mở ngành. Tập so sánh có **466 ngành** xuất hiện ở ít nhất một trong hai mạng; chọn `ceil(10% × 466) = 47 ngành` để gắn nhãn “Ngành hot 2026”. Dòng không có điểm ngành trong tập này = 0.
3. Điểm xu hướng: percentile chênh lệch điểm chuẩn 2026 − 2025, so trong cùng phương thức; ghép theo trường, mã chương trình, phương thức và thang điểm. Lấy MAX(score) của từng năm với flag rỗng; có **12.914 khóa** có đủ hai năm. Thiếu một trong hai năm = 0,5.
4. Percentile dùng hạng trung bình khi bằng nhau: `(L + R + 1)/(2N)`, L là số giá trị nhỏ hơn, R là số giá trị nhỏ hơn hoặc bằng; làm tròn bốn chữ số. Độ hot cuối cũng làm tròn bốn chữ số.

Độ hot là chỉ số tham khảo cố định theo bộ dữ liệu 2026, không phải xác suất trúng tuyển hoặc dự báo điểm chuẩn. Thứ tự tư vấn hiện tại là độ hot giảm dần; mức Thử sức/Vừa sức/An toàn vẫn tính theo điểm và thang của phương thức.

## Độ phủ tỉnh

**292/292 trường có tỉnh, còn 0 “Khác”**; bao phủ 30 tỉnh/thành theo tên sau sắp xếp hành chính 2025.
Nguồn tỉnh: **90 địa chỉ chính thức** trong `province_map.csv`, **95 VNUR**, **107 HOCMAI**. Không lấy tỉnh đại học mẹ gán cho mọi trường thành viên/phân hiệu.

VJU/QHQ/QHY → Hà Nội; QSA → An Giang. Phân hiệu ĐHTN tại Hà Giang → Tuyên Quang, tại Lào Cai → Lào Cai; Phân hiệu ĐH Đà Nẵng tại Kon Tum → Quảng Ngãi; Phân hiệu ĐHQG-HCM tại Bến Tre → Vĩnh Long. Với mã có nhiều cơ sở, bộ lọc chỉ có một tỉnh theo địa chỉ chính đã đối chiếu, không mô tả đầy đủ mọi cơ sở.

| Tỉnh/thành | Số mã trường |
| --- | ---: |
| An Giang | 2 |
| Bắc Ninh | 7 |
| Cà Mau | 1 |
| Gia Lai | 4 |
| Hà Tĩnh | 1 |
| Hưng Yên | 6 |
| Khánh Hoà | 8 |
| Lào Cai | 1 |
| Lâm Đồng | 3 |
| Nghệ An | 5 |
| Ninh Bình | 5 |
| Phú Thọ | 5 |
| Quảng Ngãi | 3 |
| Quảng Ninh | 2 |
| Quảng Trị | 2 |
| Sơn La | 1 |
| Thanh Hoá | 2 |
| Thành phố Cần Thơ | 6 |
| Thành phố Huế | 14 |
| Thành phố Hà Nội | 94 |
| Thành phố Hải Phòng | 8 |
| Thành phố Hồ Chí Minh | 63 |
| Thành phố Đà Nẵng | 16 |
| Thái Nguyên | 10 |
| Tuyên Quang | 2 |
| Tây Ninh | 2 |
| Vĩnh Long | 5 |
| Đắk Lắk | 5 |
| Đồng Nai | 7 |
| Đồng Tháp | 2 |

Địa chỉ cũ được quy về tên tỉnh năm 2025 theo [danh mục đơn vị cấp tỉnh](https://xaydungchinhsach.chinhphu.vn/bang-danh-muc-va-ma-so-cua-34-tinh-thanh-moi-cac-don-vi-hanh-chinh-cap-xa-moi-11925070418263625.htm). Mỗi mã bổ sung có URL nguồn chính thức tại `data/manual/province_map.csv`.

## Mạng SNA sau chạy lại

`data/network/summary.csv` có đủ **12 dòng** (G1–G4 × ba năm). File này sinh ở máy; các summary tương ứng có trong JSON mạng đã commit ở `site/data/network/`.

| Mạng | Năm | Nút | Cạnh | Modularity Louvain |
| --- | --- | ---: | ---: | ---: |
| g1_uni_major | 2024 | 707 | 4447 | — |
| g2_uni_uni | 2024 | 251 | 2566 | 0.4511 |
| g3_major_major | 2024 | 387 | 1360 | 0.8394 |
| g4_competition | 2024 | 259 | 10541 | — |
| g1_uni_major | 2025 | 712 | 4680 | — |
| g2_uni_uni | 2025 | 250 | 2455 | 0.4939 |
| g3_major_major | 2025 | 387 | 1431 | 0.846 |
| g4_competition | 2025 | 260 | 10789 | — |
| g1_uni_major | 2026 | 705 | 5058 | — |
| g2_uni_uni | 2026 | 249 | 2531 | 0.4822 |
| g3_major_major | 2026 | 377 | 1412 | 0.8363 |
| g4_competition | 2026 | 226 | 9215 | — |

G2 năm 2026: 249 nút, 2.531 cạnh, density 0,0820, modularity Louvain 0,4822; ngưỡng Jaccard 0,25. Thời gian tính và kết quả đo trên mẫu có thể thay đổi giữa các lượt chạy, không dùng thay cho số nút/cạnh hoặc modularity toàn mạng.

## Kiểm chứng và phát hành

- Chạy toàn bộ pipeline từ raw sẵn có và export thành công.
- `check_static`, `check_dean`, `check_catalog` qua cả chế độ máy và `--committed`. Chế độ committed đã được chạy trong bản sao không có raw/DB/clean/network.
- Ruff check, Ruff format check toàn repo và kiểm cú pháp JavaScript đều qua.
- Edge headless ở **375px và 1280px**, cả **5 tab**, trên FastAPI và bản tĩnh dưới `/Tuyensinhdaihoc/`: **100 phép đối chiếu JSON** đều khớp; kiểm thêm bộ lọc tổ hợp theo năm/phương thức, tỉnh, sáu trường học phí, ngày cập nhật; không lỗi console/HTTP.
- Sau deploy, kiểm trực tiếp GitHub Pages ở cả hai kích thước: **50 phép đối chiếu JSON** đều khớp FastAPI mới, không lỗi console/HTTP.
- Bản xuất: **3.047 file, 105.851.078 byte**; lớn nhất `data/advice/THPT_2025.json` **5.986.351 byte**, không file nào vượt 50 MB.
- Đã gỡ đúng 334 file v1 đã theo dõi và 10 file chưa theo dõi được yêu cầu; xoá state/, _to_delete/ và phần Node v1. .claude/ được ignore. Code v1 còn trong lịch sử nhánh codex/crawler-pilot.

[Web công khai](https://tiennguyen2406.github.io/Tuyensinhdaihoc/) · [Deploy bản dữ liệu đã kiểm](https://github.com/tiennguyen2406/Tuyensinhdaihoc/actions/runs/40147434125) · [CI V2](https://github.com/tiennguyen2406/Tuyensinhdaihoc/actions/runs/40147434258).

Trigger Pages đã đổi sang push nhánh **main** trên v2-simple; cấu hình này có hiệu lực sau khi gộp vào main. Bản công khai đã được kiểm sau deploy commit 1223b4c; các commit tổng kết/cấu hình tiếp theo không đổi site/. Hướng dẫn tạo PR bằng nút GitHub có trong README.

Các số liệu là độ phủ của tập dữ liệu đã thu thập, không phải toàn bộ cơ sở giáo dục hoặc thông báo tuyển sinh đang có trên mạng. Học phí, đề án và hạng có năm/phạm vi khác nhau, phải đọc ghi chú của từng trường.
