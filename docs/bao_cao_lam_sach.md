# Báo cáo thu thập và làm sạch dữ liệu điểm chuẩn

Đồ án SNA — EduRadar V2. Số liệu lấy từ `data/raw/fetch_log.csv`, `data/raw/cutoff/`,
`data/clean/` và `data/clean/quality_report.md` của lần chạy ngày 23/10/2026.

**Tóm tắt:** 921 request tới API công khai của diemthi.tuyensinh247.com (307 trường đại học ×
3 năm 2024–2026) cho 76.726 dòng thô. Sau làm sạch còn **71.008 dòng** của **292 trường**;
**97,56%** số dòng được gán mã ngành chuẩn 7 chữ số (472 ngành).

## 1. Nguồn dữ liệu và cách thu thập

| Mục | Giá trị |
| --- | --- |
| Nguồn | diemthi.tuyensinh247.com — trang tổng hợp điểm chuẩn (không phải cổng của Bộ GD&ĐT hay của trường) |
| API danh sách trường | `GET /api/school/search` — 1 request, 587 trường; giữ 307 trường đại học (`level = 2`) |
| API điểm chuẩn | `GET /api/common/cutoff-score?school_id=…&year=…` — trả JSON, mỗi trường × năm 1 request |
| Số request điểm | 921 = 307 trường × 3 năm (không request nào phải chạy lại) |
| Thời gian chạy | 1 đợt, 23/10/2026 13:51:00 → 14:20:33 (**29 phút 33 giây**) |
| Nhịp request | nghỉ 1,5 s + ngẫu nhiên 0–0,5 s; trung vị thực tế 2,0 s/request; mỗi request thử tối đa 3 lần khi lỗi mạng |
| Trang rỗng (0 dòng) | **88** (2024: 28, 2025: 29, 2026: 31); 15 trường rỗng cả 3 năm nên chỉ còn 292 trường có dữ liệu |
| Lỗi | **0** lỗi mạng, 0 phản hồi `success = false` |
| Dòng thô | **76.726** |

Công cụ là `crawler/fetch.py`, chỉ dùng thư viện chuẩn Python. Mỗi phản hồi được lưu nguyên văn
vào `data/raw/cutoff/<năm>/<mã trường>.json`, kèm thời điểm tải (`fetched_at`) và địa chỉ trang
nguồn (`source_url`). Mỗi request được ghi một dòng nhật ký (thời gian, trường, năm, số dòng, lỗi)
vào `data/raw/fetch_log.csv`. File đã tải sẽ được bỏ qua khi chạy lại, nên crawl có thể tiếp tục
nếu bị ngắt giữa chừng.

## 2. Các bước làm sạch và chuẩn hoá

Toàn bộ nằm trong `pipeline/clean.py` (`python -m pipeline.clean`); dữ liệu gốc không bị sửa.

| # | Bước | Cách làm | Số dòng ảnh hưởng | Còn lại |
| ---: | --- | --- | ---: | ---: |
| 1 | Đọc dữ liệu thô | gộp 921 file JSON, gắn mã trường, năm, `source_url`, `crawled_at` | — | 76.726 |
| 2 | Điểm | ép kiểu số; bỏ dòng không có điểm hoặc điểm ≤ 0 | −69 | 76.657 |
| 3 | Văn bản | chuẩn Unicode NFC, bỏ ký tự lỗi `U+FFFD` (74 tên), bỏ tiền tố "(1)", "(2)"… ở đầu tên (273 tên), bỏ dấu cách trong mã chương trình (655 mã), gộp khoảng trắng; bỏ dòng không có tên ngành | 0 dòng bị bỏ | 76.657 |
| 4 | Phương thức | `mark_type` của nguồn → 10 mã chuẩn (THPT, HOCBA, DGNL_HCM, DGNL_HN, DGTD, DGNL_SPT, KETHOP, CCQT, UTXT, KHAC); 3.192 dòng có `mark_type` 13–17 chưa rõ nghĩa được xếp vào KHAC | 3.192 xếp vào KHAC | 76.657 |
| 5 | Tổ hợp | tách cột `block` theo mẫu `[A-Z]\d{2}` (VD "A00; A01") thành danh sách tổ hợp | 54.452 dòng thô có `block` | 76.657 |
| 6 | Gộp điểm gốc + điểm quy đổi | nguồn trả 2 dòng cho cùng một ngành khi có điểm quy đổi; dòng quy đổi được gộp vào dòng gốc (cột `score_equiv`) | −4.959 | 71.698 |
| 6b | (lỗi đã biết) | 3 dòng có `is_converted_score = 26` (khác 0/1) bị bỏ ở bước gộp — SP2, 2026, Sư phạm Khoa học tự nhiên, 25,57 điểm | −3 | 71.695 |
| 7 | Thang điểm và cờ | gán thang theo phương thức; nếu điểm vượt thang mặc định hoặc phương thức không có thang thì suy ra thang nhỏ nhất trong {30, 40, 100, 150, 1200, 1600} chứa được điểm (xem mục 6). Gắn cờ `thang_khac_30` (1.113), `diem_thap_bat_thuong` (THPT < 12: 3), `outlier` (> 1600: 2) | 0 dòng bị bỏ, 1.118 dòng có cờ | 71.695 |
| 8 | Trùng lặp | bỏ dòng trùng hoàn toàn (cùng khoá và cùng điểm) | −687 | **71.008** |
| 8b | Trùng khoá khác điểm | giữ cả hai, ghi ra `data/interim/conflicts.csv` để xem tay | 631 dòng giữ lại | 71.008 |
| 9 | Loại chương trình | nhận diện từ tên + mã: CHUAN 62.615, TIENG_ANH 3.111, LIEN_KET 1.510, TIEN_TIEN 1.290, CLC 1.287, PHAN_HIEU 1.079, TAI_NANG 116 | 8.393 dòng không phải CHUAN | 71.008 |
| 10 | Mã ngành chuẩn | xem mục 4 | 69.273 dòng có mã | 71.008 |

Bảng sạch cuối cùng: **71.008 dòng** (2024: 18.590; 2025: 24.232; 2026: 28.186), 292 trường,
337 tổ hợp, 4.938 dòng có điểm quy đổi. Đầu ra gồm `data/clean/admissions.csv`,
`universities.csv`, `majors.csv`, `admission_combos.csv` (260.230 cặp dòng–tổ hợp) và
SQLite `data/eduradar.db`.

Số dòng theo năm × phương thức (từ `quality_report.md`):

| Phương thức | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: |
| THPT — điểm thi THPT | 5.988 | 7.908 | 6.762 |
| HOCBA — học bạ | 5.539 | 5.227 | 4.518 |
| DGNL_HCM — ĐGNL ĐHQG-HCM | 2.422 | 2.672 | 3.000 |
| DGNL_HN — ĐGNL ĐHQG-HN (HSA) | 1.035 | 1.594 | 2.008 |
| DGTD — Đánh giá tư duy (TSA) | 712 | 1.021 | 1.306 |
| DGNL_SPT — ĐGNL ĐHSP HN | 231 | 803 | 903 |
| KETHOP — xét tuyển kết hợp | 1.124 | 1.887 | 7.053 |
| CCQT — chứng chỉ quốc tế | 512 | 984 | 700 |
| UTXT — ưu tiên / xét thẳng | 670 | 655 | 284 |
| KHAC — khác | 357 | 1.481 | 1.652 |

## 3. Định nghĩa một record

Một dòng của bảng `admissions` là **một mức điểm chuẩn** của **một chương trình đào tạo** tại
**một trường**, trong **một năm**, theo **một phương thức xét tuyển**, với **một nhóm tổ hợp** như
nguồn công bố.

Khoá xác định một record: `(uni_code, year, method, sub_method, program_code, program_name,
combos, note)`. Các cột chính:

| Cột | Ý nghĩa |
| --- | --- |
| `uni_code`, `year` | mã trường (VD `BKA`), năm tuyển sinh |
| `method`, `method_name`, `sub_method` | phương thức chuẩn hoá, tên hiển thị, phương thức con do nguồn ghi (VD `10.01`) |
| `program_code`, `program_name` | mã và tên chương trình **như trường công bố** |
| `major_code` | mã ngành chuẩn 7 chữ số (rỗng nếu chưa map) |
| `program_type` | CHUAN / CLC / TIEN_TIEN / LIEN_KET / TIENG_ANH / PHAN_HIEU / TAI_NANG |
| `combos` | danh sách tổ hợp, ngăn bởi `;` (tách riêng ở `admission_combos`) |
| `score`, `scale_max`, `score_equiv` | điểm chuẩn, thang điểm, điểm quy đổi (nếu có) |
| `note`, `flag`, `match_how` | ghi chú của nguồn, cờ chất lượng, cách gán mã ngành |
| `source_url`, `crawled_at` | trang nguồn và thời điểm tải |

Hệ quả: một chương trình có nhiều nhóm tổ hợp với điểm khác nhau thì có nhiều dòng; nhiều
chương trình (chuẩn, CLC, liên kết…) cùng chung một `major_code`.

## 4. Gán mã ngành chuẩn

Danh mục ngành được dựng từ chính dữ liệu: mỗi mã 7 chữ số xuất hiện trong mã chương trình được
gắn với tên phổ biến nhất của nó (ưu tiên chương trình chuẩn). Mỗi dòng thử các cách sau theo thứ
tự, dừng ở cách đầu tiên khớp. Các cách từ 3 trở đi so trên `name_key`: tên đã bỏ dấu, viết thường,
bỏ phần trong ngoặc và các từ chung như "chương trình", "CLC", "tiên tiến", nhưng giữ "quốc tế"
và "tiếng anh".

| # | `match_how` | Quy tắc | Số dòng | Tỉ lệ |
| ---: | --- | --- | ---: | ---: |
| 1 | `ma_7_so` | mã chương trình bắt đầu bằng 7 chữ số → dùng luôn | 56.416 | 79,45% |
| 2 | `thu_cong` | tên có trong `data/manual/major_map.csv` (201 tên đã duyệt tay) | 2.055 | 2,89% |
| 2b | `thu_cong_bo` | file thủ công đánh dấu `-` = bỏ map tự động sai (9 tên) | 55 | 0,08% |
| 3 | `ten_khop` | `name_key` trùng khớp tên đã có mã; nếu một tên ứng với nhiều mã thì chọn mã xuất hiện nhiều nhất | 9.425 | 13,27% |
| 4 | `dau_ten_chuan` | `name_key` **bắt đầu bằng** tên ngành chuẩn dài ≥ 2 từ | 1.181 | 1,66% |
| 5 | `ten_gan_dung` | tên gần giống một tên đã có mã (độ giống `difflib` ≥ 0,9) | 83 | 0,12% |
| 6 | `chua_ten_chuan` | tên **chứa** cụm tên ngành chuẩn, cụm đó chiếm ≥ 60% số từ cốt lõi | 113 | 0,16% |
| — | chưa map | không khớp cách nào | 1.680 | 2,37% |
| | **Có mã ngành** | | **69.273** | **97,56%** |

Ví dụ thật cho mỗi loại (trường | mã chương trình | tên gốc → mã ngành):

- **ma_7_so:** DVL | `7210404` | Thiết kế thời trang → 7210404 Thiết kế thời trang
- **thu_cong:** HHA | `D110` | Xây dựng công trình thủy → 7580202 Kỹ thuật xây dựng công trình thủy;
  DTT | `DK7340301` | Kế toán (song bằng 3+1) – Chương trình dự bị liên kết Đại học West of England → 7340301 Kế toán
- **thu_cong_bo:** BKA | `MS5` | Kỹ thuật in → không map (tự động từng gán nhầm vào "Công nghệ kỹ thuật điện, điện tử")
- **ten_khop:** GSA | `GSA08QT` | Logistics và Quản lý chuỗi cung ứng (Chương trình CLC … Việt-Anh) → 7510605 Logistics và quản lý chuỗi cung ứng
- **dau_ten_chuan:** KHA | `EP32` | Thống kê và Trí tuệ kinh doanh → 7460201 Thống kê
- **ten_gan_dung:** HHA | `D407` | Logistics & chuỗi cung ứng → 7510605 Logistics và quản lý chuỗi cung ứng
- **chua_ten_chuan:** BKA | `IT1` | CNTT: Khoa học Máy tính → 7480101 Khoa học máy tính
- **chưa map:** BKA | `BF-E19` | Kỹ thuật sinh học (CT tiên tiến) — ngành Kỹ thuật sinh học không có trong danh mục dựng từ dữ liệu

## 5. Kiểm tra độ chính xác

Đối chiếu tay 20 dòng chọn ngẫu nhiên (seed 42, 2 dòng cho mỗi phương thức trong 10 phương thức)
với trang nguồn; chi tiết từng dòng ở [`docs/kiem_tra_20_dong.md`](kiem_tra_20_dong.md).

Kết quả: **__/20** dòng đúng (trường, năm, phương thức, chương trình và điểm khớp với trang nguồn).

Phép kiểm tra này đo độ chính xác của khâu **thu thập và chuẩn hoá điểm**. Việc gán mã ngành tự
động (các cách 3–6 ở mục 4, chiếm 15,2% số dòng) chưa được đo riêng.

## 6. Giới hạn

1. **Thang điểm suy ra từ giá trị.** Nguồn không ghi thang điểm cho từng dòng. Pipeline dùng thang
   mặc định của phương thức (THPT/học bạ 30, HSA 150, TSA 100, ĐGNL HCM 1200). Khi điểm vượt thang
   đó, hoặc phương thức không có thang (KETHOP, CCQT, UTXT, KHAC — 17.359 dòng), thang được suy ra
   là mức nhỏ nhất chứa được điểm. Cách này có thể sai, ví dụ hai dòng trong file kiểm tra:
   - **Dòng 11** — NTS, `KDQS2.1` (ĐHNNQT Logistics và Quản lý chuỗi cung ứng), học bạ 2024,
     **31 điểm → suy ra thang 40**. Cùng chương trình có dòng học bạ 30 và 29 điểm ở thang 30, nên
     31 có thể là điểm đã cộng ưu tiên hoặc một thang khác.
   - **Dòng 15** — DDT, `7510205_11` (Công nghệ Kỹ thuật Ô tô – Chương trình CTBT), phương thức
     "Khác" 2026, **225 điểm → suy ra thang 1200** (vì > 150), trong khi rất có thể là thang 300.
     Có 1.242 dòng KHAC bị gán thang 1200 với điểm ≤ 300 — cùng rủi ro này.

   Tổng cộng 1.144 dòng THPT/học bạ/HSA/TSA có điểm vượt thang mặc định; 1.113 dòng trong số đó
   mang cờ `thang_khac_30`. Khi so sánh điểm giữa các trường, nên lọc theo `scale_max` (trang
   tư vấn của web chỉ so trong thang phổ biến nhất của mỗi phương thức).
2. **Tên chưa map ngành.** Còn **175 tên chương trình (1.735 dòng, 2,44%)** chưa có mã, gồm 55 dòng
   bị bỏ map có chủ đích; danh sách ở `data/interim/major_unmatched.csv`. Phần lớn là chuyên ngành
   hẹp, chương trình liên kết hoặc nhóm ngành gộp. Các cách map 4–6 là heuristic và có thể sai, VD
   DAD "Marketing truyền thông (\*)" đang khớp gần đúng vào 7900102 "Marketing và Truyền thông".
3. **Danh mục ngành dựng từ dữ liệu, không phải danh mục chính thức của Bộ.** Một số mã không
   chuẩn do trường công bố cũng vào danh mục (VD 7310120 bên cạnh 7340120 cho "Kinh doanh quốc
   tế", 7340002 bên cạnh 7340101 cho "Quản trị kinh doanh"); tên ngành hiển thị là tên phổ biến
   nhất trong dữ liệu.
4. **Phụ thuộc trang tổng hợp.** Toàn bộ số liệu lấy từ tuyensinh247, không phải thông báo chính
   thức của trường; sai sót hoặc thiếu sót của nguồn được kế thừa. 88 trang rỗng và 15 trường
   không có dữ liệu ở cả 3 năm. Ý nghĩa của `mark_type` 13–17 (3.192 dòng) không được nguồn mô tả
   nên xếp vào "Khác". `source_url` trỏ tới trang tổng hợp của trường, không trỏ tới văn bản gốc.
   Dữ liệu là ảnh chụp ngày 23/10/2026; nguồn có thể cập nhật sau đó.
5. **Lỗi và mâu thuẫn còn lại.** 3 dòng bị mất do `is_converted_score = 26` (mục 2, bước 6b);
   631 dòng trùng khoá nhưng khác điểm được giữ nguyên, chưa xử lý.
