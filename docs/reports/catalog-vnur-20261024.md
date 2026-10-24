# Lưới trường, môn tổ hợp và VNUR 2026 — 24/10/2026

## Kết quả

- 292 thẻ trường, dùng năm mới nhất có dữ liệu của từng trường để đếm mã xét tuyển
  và phương thức. Bổ sung năm bắt đầu có dữ liệu nếu sau 2024.
- Lưới 3 cột desktop, 2 cột tablet, 1 cột mobile; lọc tức thì không dấu, chữ đầu
  tên trường (bỏ tiền tố loại hình), tỉnh/thành, thứ tự A–Z hoặc VNUR. Bấm thẻ mở
  bảng điểm và cuộn đến kết quả.
- 149/292 mã trường có hạng: 95 khớp trực tiếp, 54 kế thừa từ 5 đại học mẹ.
  143 mã còn lại chưa gắn hạng từ CSV Top 100; không tự suy diễn xếp hạng.
- `vnur_map.csv` bao phủ cả 100 mục trong CSV nguồn. Không còn map nào chưa chắc.
  Tên, hạng và tỉnh trong `vnur_2026.csv` do người dùng cung cấp được giữ nguyên.
- Tỉnh/thành chỉ lấy khi ghép trực tiếp vào mục VNUR; 197 mã chưa có tỉnh của chính
  đơn vị được ghi “Khác”, gồm các đơn vị kế thừa. Không dùng vị trí đại học mẹ làm
  địa điểm của mọi trường/phân hiệu.
- Tư vấn mặc định xếp theo hạng trường trong từng mức. Có hạng trước, chưa có hạng
  sau; cùng hạng hoặc chưa có hạng thì theo điểm giảm dần. Sắp xếp trước khi chia
  hạn mức, vẫn giữ ba mức và lịch sử theo tổ hợp/thang. Có lựa chọn “Theo điểm”.
  Cột và CSV xuất có hạng VNUR, tên đại học mẹ; hạng 2026 dùng tham khảo cho mọi năm.
- Ô tìm môn lọc danh sách chọn theo mã hoặc tên môn không dấu. Mã trong bảng điểm
  trường, ngành và tư vấn đều có tooltip môn học. Footer và độ phủ có nguồn VNUR.

## Ghép hạng

| Nguồn hạng | Số mã trường/đơn vị | Hạng |
| --- | ---: | ---: |
| Khớp trực tiếp | 95 | Theo CSV nguồn |
| ĐHQG Hà Nội | 12 | 1 |
| ĐHQG TP.HCM | 9 | 2 |
| ĐH Đà Nẵng | 9 | 9 |
| ĐH Huế | 13 | 14 |
| ĐH Thái Nguyên | 11 | 15 |

Các trường đổi tên cần đối chiếu thủ công đã xác minh:

- **SPK**: tên cũ “Đại học Sư phạm Kỹ thuật TP.HCM” trong CSV VNUR, tên hiện tại
  “Đại học Công nghệ Kỹ thuật TP.HCM” trong danh mục tuyển sinh; hạng 38.
  [Thông tin chính thức của trường](https://hcmute.edu.vn/ArticleId/6d145868-f100-4696-9ded-dde5bb51fafb/thong-tin-tuyen-sinh-dai-hoc-chinh-quy-nam-2026).
- **DKS**: “Đại học Kiểm sát Hà Nội” đổi thành “Đại học Kiểm sát”; hạng 64.
  [Quyết định 1483/QĐ-TTg](https://chinhphu.vn/?docid=214445&pageid=27160).
- **THV / DHV**: hạng 89 gắn với Hùng Vương Phú Thọ (**THV**), không gắn với
  Hùng Vương TP.HCM (**DHV**). Tỉnh nguồn Phú Thọ được giữ nguyên.

Nguồn xếp hạng: [VNUR 2026](https://vnur.vn/bang-xep-hang/).
Quan hệ đơn vị có thể đối chiếu tại [ĐHQG Hà Nội](https://vnu.edu.vn/),
[ĐHQG TP.HCM](https://vnuhcm.edu.vn/), [ĐH Đà Nẵng](https://www.udn.vn/),
[ĐH Huế](https://hueuni.edu.vn/), [ĐH Thái Nguyên](https://tnu.edu.vn/).
Hạng kế thừa là cách trình bày theo yêu cầu của đồ án, không phải VNUR xếp hạng riêng
cho từng trường thành viên.

## Danh mục tổ hợp và pipeline

Crawler có `--blocks-only`, kiểm robots.txt và nghỉ tối thiểu 1,5 giây giữa các
request. Đã tải API `/api/common/blocks` vào `data/raw/blocks.json` trước khi chạy web.
Không commit raw hoặc DB. Pipeline tạo bảng `combos(combo, subjects)` cùng CSV sạch.

280 mục nguồn được tách thành 298 mã/bí danh. Tách cả dấu phẩy và chấm phẩy,
giữ X02, K21, TH6, A0T, DK…; bỏ chuỗi tên môn trong ngoặc và “HSA - Khoa học”.
11 bí danh nguồn có nhiều định nghĩa: D0C, E01, H06, K01, K20, K22, TH3, TH4,
TH5, TH8, V10. Tooltip giữ đủ các định nghĩa và chú thích xung đột, không chọn ngầm một bộ môn.

Nhận diện thêm mã kiểu A0T/TH6 trong điểm tuyển sinh giúp giữ thêm 2 dòng trước đây
bị gộp khi tổ hợp bị bỏ trống: **71.011 dòng sạch**, **69.276 dòng map ngành
(97,56%)**, 292 trường, 472 ngành. Dữ liệu SNA đã dựng lại từ DB mới:
`data/network/summary.csv` có 12 hàng (4 mạng × 3 năm). G2 2026 có 249 nút,
2.531 cạnh, density 0,082, modularity Louvain 0,4822.

## Kiểm chứng và triển khai

Edge headless kiểm cả FastAPI và bản tĩnh ở 375px, 1280px: bốn lượt × 19 phép đối
chiếu JSON với API, tổng 76 phép. Mỗi lượt kiểm cả 4 tab, lưới và bộ lọc, tooltip,
tìm môn “tin hoc”, mã A00, kế thừa hạng và đổi sort. Không lỗi console/JavaScript,
không HTTP 404 hay request thất bại; bản tĩnh không gọi API hoặc CDN.
Ảnh: [catalog-20261024](catalog-20261024/).

Bản xuất: 3.046 file, 97.040.985 byte; lớn nhất
`data/advice/THPT_2025.json` 5.745.900 byte, dưới 50 MB.
Ruff check, Ruff format check, kiểm cú pháp JS và `git diff --check` đều qua.

Lệnh tái tạo:

```powershell
.venv/Scripts/python.exe -m crawler.fetch --blocks-only
.venv/Scripts/python.exe -m pipeline.clean
.venv/Scripts/python.exe -m sna.build
.venv/Scripts/python.exe scripts/export_static.py
.venv/Scripts/python.exe scripts/check_catalog.py
.venv/Scripts/python.exe scripts/check_static.py
node scripts/check_static_browser.cjs
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Workflow hiện có sẽ deploy `site/` khi push `v2-simple`. Lần chạy trước của commit
`190bd67` đã thành công và URL Pages trả 200; cấu hình environment trước đó đã được sửa.
Theo dõi lần chạy bản mới tại [GitHub Actions](https://github.com/tiennguyen2406/Tuyensinhdaihoc/actions/workflows/pages.yml).
Địa chỉ: <https://tiennguyen2406.github.io/Tuyensinhdaihoc/>.
