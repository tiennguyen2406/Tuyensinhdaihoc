# EduRadar V2 — Tra cứu điểm chuẩn và phân tích mạng

Đồ án SNA: tra cứu theo trường/ngành, tư vấn theo điểm, mạng SNA và độ phủ dữ liệu.
Dữ liệu điểm chuẩn 2024–2026; đề án HOCMAI; học phí tra tay; VNUR 2026.

**Web công khai:** <https://tiennguyen2406.github.io/Tuyensinhdaihoc/>

## Cài đặt

Dùng Python 3.12 và chạy lệnh tại thư mục repo. Với `uv`:

```powershell
uv sync --locked
```

Hoặc dùng pip:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pip install ruff==0.17.1
```

`requirements.txt` được xuất từ `uv.lock`; chỉ có thư viện V2 và phụ thuộc của chúng.
`pypandoc_binary` và `python-docx` phục vụ `scripts/build_report_docx.py`.
Không cần PostgreSQL, Docker, Next.js hay cấu hình `.env` để chạy V2.

## Tạo dữ liệu theo thứ tự

Dừng web trước khi thu thập hoặc tái tạo dữ liệu. Nếu đã có raw ở máy thì bỏ qua hai
lệnh fetch, không cần gọi lại nguồn.

```powershell
# 1. Thu thập điểm, danh mục tổ hợp và đề án (bỏ qua raw đã tải)
.venv/Scripts/python.exe -m crawler.fetch
.venv/Scripts/python.exe -m crawler.fetch_dean

# 2. Làm sạch, chuẩn hoá và tạo SQLite
.venv/Scripts/python.exe -m pipeline.clean

# 3. Nhập học phí tra tay và overrides
.venv/Scripts/python.exe -m pipeline.tuition_import

# 4. Bóc tách dữ kiện đề án
.venv/Scripts/python.exe -m pipeline.dean

# 5. Dựng mạng và độ đo
.venv/Scripts/python.exe -m sna.build

# 6. Xuất web tĩnh giống kết quả FastAPI
.venv/Scripts/python.exe scripts/export_static.py
```

Crawler điểm nghỉ ít nhất 1,5 giây; crawler HOCMAI nghỉ ít nhất 2 giây giữa request,
đều kiểm robots.txt. Raw và SQLite không được commit. Bản clone mới có thể chạy web
ngay bằng `site/`; muốn tạo lại DB phải có raw tại máy hoặc chạy fetch.

## Chạy web

FastAPI tại <http://127.0.0.1:8000>:

```powershell
.venv/Scripts/python.exe -m uvicorn webapp.main:app --host 127.0.0.1 --port 8000
```

Bản tĩnh tại <http://127.0.0.1:8001>:

```powershell
.venv/Scripts/python.exe -m http.server 8001 --directory site
```

Mọi đường dẫn tài nguyên là tương đối, dùng được dưới `/Tuyensinhdaihoc/`.
Ngày cập nhật trên web là ngày chạy `pipeline.clean` theo múi giờ UTC+7.

## Kiểm tra

Ba lệnh `--committed` chỉ đọc dữ liệu đã commit trong `site/` và `data/manual/`,
chạy được trên CI không có raw, DB, `data/clean/` hoặc `data/network/`:

```powershell
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/python.exe scripts/check_static.py --committed
.venv/Scripts/python.exe scripts/check_dean.py --committed
.venv/Scripts/python.exe scripts/check_catalog.py --committed
```

Sau khi chạy pipeline tại máy, bỏ `--committed` để kiểm thêm dữ liệu sinh ra và đối
chiếu với các hàm FastAPI. Kiểm Edge headless cần Node.js và Microsoft Edge:

```powershell
npm install --prefix .venv/browser-check playwright@1.64.1
node scripts/check_static_browser.cjs
# Kiểm cả 5 tab trên web GitHub Pages, đối chiếu với dữ liệu FastAPI ở máy
node scripts/check_static_browser.cjs --live
```

Bộ kiểm chạy đủ 5 tab ở 375px và 1280px trên cả FastAPI và bản tĩnh dưới đường dẫn con;
kiểm lỗi console/HTTP và so JSON với API. Ảnh, kết quả kiểm được ghi vào thư mục tạm
của hệ điều hành, không tạo lại `state/` hoặc `_to_delete/`.

## Cấu trúc và sửa dữ liệu

| Đường dẫn | Nội dung |
| --- | --- |
| `crawler/` | Fetch điểm, danh mục tổ hợp và HOCMAI |
| `pipeline/clean.py` | Làm sạch, map ngành, VNUR, tỉnh và tạo SQLite |
| `pipeline/tuition_import.py` | Nhập file học phí và 32 overrides kiểm tay |
| `pipeline/dean.py` | Bóc tách dữ kiện theo heading, không xuất HTML bài gốc |
| `sna/` | Mạng G1–G4, độ đo và hình |
| `webapp/` | FastAPI và HTML/JS/CSS dùng chung |
| `scripts/` | Export, kiểm tra V2, xuất Word |
| `data/manual/` | Map ngành, trường, tỉnh, xếp hạng và học phí |
| `site/` | Web tĩnh và JSON đã commit để deploy |
| `docs/` | Báo cáo, hình V2 và hai tài liệu v1 được giữ để tham khảo |

Sửa dữ liệu thủ công trong `data/manual/`, rồi chạy lại pipeline; không sửa DB hay
`data/clean/` bằng tay. `province_map.csv` lưu tỉnh theo địa chỉ chính thức (tên tỉnh
sau sắp xếp 2025); trường có nhiều cơ sở dùng trụ sở chính, phân hiệu có mã riêng dùng
địa điểm phân hiệu. `tuition_extra_overrides.json` giữ nguyên số, đơn vị, năm và phạm vi
của file học phí người dùng; số thiếu đơn vị được ghi rõ.

Điểm tư vấn giữ thang điểm gốc và lịch sử cùng tổ hợp. Độ hot = 0,5 × điểm trường +
0,3 × điểm ngành + 0,2 × điểm xu hướng; xem giải thích từng thành phần ở tab Độ phủ.
Hạng kế thừa đại học mẹ được ghi rõ, không phải VNUR xếp hạng riêng trường thành viên.

## GitHub Pages và lịch sử v1

Trong **Settings → Pages → Build and deployment → Source**, chọn **GitHub Actions**.
Workflow `.github/workflows/pages.yml` upload và deploy thư mục `site/` đã commit.
Workflow chạy khi push vào `main`, hoặc chạy thủ công với nhánh `main`.
CI V2 không crawl và không cần DB. Các file xuất phải dưới 50 MB mỗi file.

Tạo PR gộp bản nộp: mở [main ← v2-simple](https://github.com/tiennguyen2406/Tuyensinhdaihoc/compare/main...v2-simple?expand=1),
kiểm tra **base: main**, **compare: v2-simple**, rồi bấm **Create pull request**.
Tiêu đề gợi ý: `EduRadar V2: web tra cứu, dữ liệu chuẩn hoá và bản nộp SNA`.
Sau khi PR được merge vào main, workflow Pages sẽ tự chạy từ main.

Code v1 còn trong lịch sử nhánh [`codex/crawler-pilot`](https://github.com/tiennguyen2406/Tuyensinhdaihoc/tree/codex/crawler-pilot).
Các thư mục và script v1 đã được gỡ khỏi `v2-simple`; không phát triển tiếp v1.

Nguồn: [tuyensinh247](https://diemthi.tuyensinh247.com/),
[HOCMAI](https://huongnghiep.hocmai.vn/), [VNUR 2026](https://vnur.vn/bang-xep-hang/),
và các nguồn học phí/địa chỉ được ghi tại từng mục. Dùng cho học tập phi thương mại;
luôn đối chiếu thông báo chính thức của trường.
