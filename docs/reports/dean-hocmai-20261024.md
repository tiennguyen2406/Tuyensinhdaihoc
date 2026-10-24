# Đề án tuyển sinh HOCMAI — 24/10/2026

## Phạm vi và độ phủ

- Đọc 271 bài từ REST API HOCMAI và tên term của bốn taxonomy: `nam`,
  `thanh-pho-tax`, `nhom-truong`, `phuong-thuc-xet-tuyen`.
- 268 bài ghép vào **267/292 trường (91,44%)**, có 1.190 mục phương thức.
  HCB có hai bài; khi cùng năm, chọn bài sửa gần nhất.
- 25 trường trong danh mục điểm chưa có đề án. Giao diện ghi “Chưa có dữ liệu đề án”.
- Ba bài nằm ngoài danh mục 292 trường có điểm: Đại học Anh Quốc Việt Nam,
  Đại học Công nghệ Vạn Xuân, Học viện Âm nhạc Quốc gia Việt Nam. Để trống
  `uni_code`, không ghép sang trường gần tên.
- Tỉnh/thành vẫn ưu tiên VNUR; HOCMAI bổ sung 107 trường. Còn 90 trường ghi “Khác”.
  Không lấy vị trí đại học mẹ làm vị trí mặc định của trường thành viên.
- Dữ liệu điểm và mạng không đổi: 71.011 dòng sạch, 69.276 dòng map ngành (97,56%),
  292 trường, 472 ngành; `data/network/summary.csv` có 12 dòng độ đo.

## Cách xử lý dữ kiện

Crawler kiểm robots.txt, dùng User-Agent `EduRadar-student-project/2.0` ghi rõ
đồ án sinh viên phi thương mại, nghỉ ít nhất 2 giây sau mỗi request. Chỉ chạy khi
web đã dừng. HTML gốc và taxonomy được giữ trong `data/raw/dean/`, không commit.

Pipeline dùng BeautifulSoup, loại script/style, đi theo H2/H3/H4 và chỉ lấy các mục
phương thức, thời gian, hồ sơ. Bỏ giới thiệu trường và danh sách ngành, kể cả bảng
ngành nằm trong phần quy chế. `data/clean/dean.json` là dữ liệu sinh tự động.

Tóm tắt dùng các nhãn dữ kiện được nhận diện, không xuất đoạn HTML hoặc cắt nguyên
văn bài thành bản rút gọn. Mỗi phương thức tối đa hai câu / 300 ký tự. Các ngưỡng
chứng chỉ được gắn với đúng tên, phân biệt SAT với V-SAT, giữ dấu `>` và `≥`;
không biến điểm quy đổi hoặc điểm thưởng thành điều kiện chung. Các diện hoặc điều
kiện chưa tóm tắt được dẫn người đọc về bài gốc. Tên phương thức là tên mục H3.

Thời gian/hồ sơ chỉ có mốc ngày và tên giấy tờ dạng gạch đầu dòng. Nếu bài không
có mục này thì giao diện thông báo thiếu dữ kiện, không tự bổ sung lịch tuyển sinh.

Có **91 bài** mà năm trong tiêu đề đề án khác năm tại H2 phương thức. Giữ nguyên
cả `year` và `methods_year`, hiển thị ghi chú rõ ràng. Chọn đề án gần nhất không
vượt năm bảng điểm nếu có; nếu chỉ có bài mới hơn thì hiển thị đúng năm bài và
ghi rõ khác năm bảng điểm. Không đổi dữ liệu cũ thành đề án 2026.

Nguồn: [REST API HOCMAI](https://huongnghiep.hocmai.vn/wp-json/wp/v2/de-an),
[robots.txt](https://huongnghiep.hocmai.vn/robots.txt). Mỗi khối trên web có link
bài cụ thể, mở tab mới, và dòng “Nguồn: HOCMAI, tóm tắt dữ kiện”.

## Map tên trường

`data/manual/dean_map.csv` lưu đủ 271 bài với tên nguồn, mã trường và ghi chú.
Đối sánh tên không dấu và bỏ tiền tố loại hình; các ca khác tên được kiểm riêng.
Không còn ca ghép chưa chắc; ba bài ngoài danh mục được để chưa ghép có chủ ý.

Các ca cần giải thích:

- HCB/HCN: tên cũ Kỹ thuật – Hậu cần CAND, tên H2 mới của Học viện Kỹ thuật và
  Công nghệ an ninh; hai mã/phía theo danh mục điểm.
- SPK, DCA: tiêu đề cũ nhưng tên mới tại H2 khớp trường trong danh mục.
- SIU: tên nguồn thêm “Tư thục”; DTE: khác từ nối “và”.
- VLU: từ Đại học Sư phạm Kỹ thuật Vĩnh Long sang Đại học Công nghệ Kỹ thuật
  Vĩnh Long; [thông báo của trường, QĐ 2636/QĐ-BGDĐT](https://vlute.edu.vn/thong-bao-chinh-thuc-ve-viec-doi-ten-truong-theo-quyet-dinh-cua-bo-giao-duc-va-dao-tao?language=vi).
- PCH: tên nguồn cũ Phòng cháy chữa cháy phía Bắc; mã hiện tại theo danh mục điểm.
- UFA: bài 2025 của Đại học Tài chính – Kế toán, tiền thân Phân hiệu UFM tại
  Quảng Ngãi; [quyết định thành lập phân hiệu](https://ufm.edu.vn/thu-tuong-chinh-phu-quyet-dinh-thanh-lap-phan-hieu-truong-dai-hoc-tai-chinh-marketing-tai-quang-ngai-2047.html).
  Giữ năm 2025 và ghi chú tiền thân trong map.
- HTY: bài Đại học Tài chính – Quản trị kinh doanh, đơn vị tiền thân của
  Phân hiệu Học viện Tài chính tại Hưng Yên;
  [thông tin của Học viện](https://qtkd.hvtc.edu.vn/Hoc-vien-Tai-chinh-co-tan-Pho-Giam-doc-va-Lanh-dao-Phan-hieu-tai-Hung-Yen_33992.html).

## Hiển thị hạng VNUR

Giữ 149 trường có hạng: 95 trực tiếp và 54 kế thừa. Thẻ kế thừa hiển thị
“Thuộc ĐHQG HN · Top 1” (tên viết tắt tương ứng từng đại học mẹ), màu nhạt;
cột tư vấn hiển thị “1 (ĐHQG HN)”. Cùng hạng thì hạng trực tiếp đứng trước
kế thừa, rồi mới so điểm trong từng mức tư vấn. Python và JavaScript dùng cùng
thứ tự. Nguồn: [VNUR 2026](https://vnur.vn/bang-xep-hang/).

## Tái tạo và kiểm chứng

```powershell
.venv/Scripts/python.exe -m crawler.fetch_dean
.venv/Scripts/python.exe -m pipeline.dean
.venv/Scripts/python.exe scripts/export_static.py
.venv/Scripts/python.exe scripts/check_dean.py
.venv/Scripts/python.exe scripts/check_catalog.py
.venv/Scripts/python.exe scripts/check_static.py
node scripts/check_static_browser.cjs
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Edge headless kiểm FastAPI và bản tĩnh dưới `/Tuyensinhdaihoc/` ở 375px và
1280px: cả bốn tab, trang độ phủ, BKA/NTH có đề án và BVS chưa có đề án,
liên kết nguồn, giới hạn tóm tắt, huy hiệu hạng, bộ lọc tỉnh và thứ tự tư vấn.
Mỗi lượt so 21 JSON với FastAPI, tổng 84 phép đối chiếu. Không lỗi console,
JavaScript, HTTP 404 hoặc request thất bại. Ảnh: [dean-20261024](dean-20261024/).

Bản xuất có 3.047 file, tổng 98.324.164 byte. File lớn nhất là
`data/advice/THPT_2025.json`, 5.745.900 byte; không có file vượt 50 MB.
Ruff check, Ruff format check và kiểm cú pháp JavaScript đều qua.

Workflow [GitHub Pages](https://github.com/tiennguyen2406/Tuyensinhdaihoc/actions/workflows/pages.yml)
deploy thư mục `site/` khi push `v2-simple`.
Web: <https://tiennguyen2406.github.io/Tuyensinhdaihoc/>.
