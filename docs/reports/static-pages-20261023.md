# EduRadar tĩnh trên GitHub Pages — 23/10/2026

`site/` là bản xuất từ SQLite, được commit và deploy trực tiếp. FastAPI vẫn chạy như cũ.
Không crawl khi xuất hoặc mở web. Mỗi lần cập nhật DB hoặc giao diện, cần xuất lại `site/`.

## Chạy và cập nhật

```powershell
.venv/Scripts/python.exe scripts/export_static.py
.venv/Scripts/python.exe scripts/check_static.py
node scripts/check_static_browser.cjs
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Bài kiểm Edge dùng `@playwright/test` đã cài trong `apps/web/node_modules`, không sửa code v1.
Script tự mở `python -m http.server`, tạo đường dẫn con giả lập
`/Tuyensinhdaihoc/`, mở thêm FastAPI để đối chiếu rồi đóng các tiến trình do nó tạo.
Ảnh kiểm giao diện nằm trong [pages-20261023](pages-20261023/).

Chạy FastAPI riêng:

```powershell
.venv/Scripts/python.exe -m uvicorn webapp.main:app --reload
```

## Kết quả kiểm

- 71.009 dòng sạch; 69.274 dòng đã map ngành (97,56%); 292 trường; 472 ngành chuẩn.
- Độ phủ đối chiếu 307 trường đại học trong danh mục nguồn, liệt kê 15 trường chưa có điểm.
  Ngày thu thập theo `admissions.crawled_at`: 23/10/2026.
- 3.046 file trong `site/`, tổng 91.708.902 byte (91,71 MB); lớn nhất
  `data/advice/THPT_2025.json`: 5.111.959 byte. Không file nào đạt 50 MB.
- Edge headless ở 375px và 1280px: BKA 2026 (83 hàng chương trình), ngành 7480201
  năm 2025 (270 dòng THPT), tư vấn THPT 24 A00 năm 2026, mạng G2 2026 đều hiển thị.
  Trang độ phủ có 292 hàng trường và 15 trường nguồn chưa có điểm; liên kết trường
  mở đúng năm ghi trong URL dù trước đó đã tra một năm khác.
- Mỗi kích thước có 17 phép so sánh toàn bộ JSON với FastAPI: meta, trường, ngành,
  chương trình chưa map, ngành tương tự, mạng, tìm kiếm không dấu và tư vấn.
  Tư vấn bao gồm THPT, HOCBA, DGNL_HCM, DGNL_HN, KETHOP, tổ hợp viết thường,
  hạn mức riêng, margin riêng và trường hợp không có lựa chọn.
- Không lỗi console/JavaScript, không HTTP 404 hoặc request thất bại; mọi request
  của bản tĩnh nằm dưới `/Tuyensinhdaihoc/`, không thử gọi `/api` và không phụ thuộc CDN.
- FastAPI tại máy vẫn tra BKA 2026 và tư vấn THPT 24 A00 được; chế độ dữ liệu là API.
- `ruff check .`, `ruff format --check .`, `git diff --check` và kiểm cú pháp JS đều qua.
- Bộ pytest cũ không qua vì PostgreSQL không kết nối được. Lệnh
  `PGCONNECT_TIMEOUT=5 python -m pytest -x -q --tb=short` (đặt biến môi trường theo shell)
  ghi nhận 1 passed, 1 error tại
  `tests/catalog/test_advice.py::test_sql_numeric_threshold_has_strict_upper_bound_and_no_lower_bound[22-want0]`,
  lỗi setup `psycopg.errors.ConnectionTimeout`. Không thay đổi hệ thống v1 để xử lý lỗi này.

`data/network/summary.csv` hiện có các độ đo của 4 mạng × 3 năm. Dữ liệu JSON SNA
và bảng ngành tương tự được chép vào `site/data/network/`. G2 năm 2026 có 249 nút,
2.531 cạnh, density 0,082 và modularity Louvain 0,4822.

## Cách dữ liệu tĩnh giữ logic API

JSON theo trường (cả trường `tuition`), ngành, chương trình và meta gọi trực tiếp
hàm tương ứng trong `webapp/main.py`. Xuất đủ từng năm, kể cả kết quả rỗng, để đổi
năm không gây 404. Tên chương trình chưa map dùng ID file được ghi trong chỉ mục ngành.

Tư vấn lấy thang điểm phổ biến bằng hàm `advice`, dùng chung `advice_candidates`
với API để giữ đúng thứ tự các điểm bằng nhau. Dữ liệu gói theo cột, kèm tổ hợp từ
`admission_combos` và lịch sử MAX theo trường/chương trình/thang/tổ hợp. Trình duyệt
lọc theo điểm + margin, chia ba mức và chia hạn mức giống API; điểm năm tham chiếu
luôn lấy đúng dòng đang hiển thị. Tìm trường/ngành chạy phía trình duyệt ở cả hai chế độ.

HTML xuất có `data-mode="static"`; bản FastAPI tự gọi API. Đường dẫn tài nguyên và
dữ liệu đều tương đối. Thư viện `vis-network` 9.1.9 dùng bản đi kèm, có giấy phép gốc.

## Cấu hình GitHub

Repo: <https://github.com/tiennguyen2406/Tuyensinhdaihoc>.

1. Mở **Settings → Pages → Build and deployment → Source**, chọn **GitHub Actions**.
   Workflow đã có sẵn; không cần chọn branch/folder tại trang này.
2. Environment `github-pages` hiện có quy tắc chặn `v2-simple`. Mở **Settings →
   Environments → github-pages → Deployment branches and tags**, cho phép `v2-simple`
   (Selected branches and tags → Add deployment branch or tag rule → Branch → `v2-simple`).
   Repo mặc định dùng `main`, nên quy tắc chỉ cho `main` sẽ chặn workflow này.
3. Workflow `.github/workflows/pages.yml` tự deploy khi push `v2-simple`. Nếu push
   đầu diễn ra trước khi bật Pages, vào **Actions → Deploy EduRadar to GitHub Pages**,
   mở lần chạy của `v2-simple` và chọn **Re-run all jobs**.
4. Nếu Actions đang bị tắt hoặc bị giới hạn, bật GitHub Actions và cho phép các action
   do GitHub phát hành trong **Settings → Actions → General**.

Địa chỉ sau khi deploy thành công: <https://tiennguyen2406.github.io/Tuyensinhdaihoc/>.
Workflow chỉ upload `site/`; không cần SQLite hoặc crawl trên GitHub runner.

Sau khi push commit tính năng `528d63b`, [lần chạy 39982979020](https://github.com/tiennguyen2406/Tuyensinhdaihoc/actions/runs/39982979020)
bị GitHub từ chối trước khi bắt đầu các step. Annotation xác nhận nhánh `v2-simple`
không được phép deploy vào `github-pages` do environment protection rules. URL Pages
hiện trả 404, chưa thể coi là đã online. Cần chủ repo sửa Settings ở bước 1–2,
sau đó re-run lần chạy mới nhất. Tài khoản connector hiện có quyền push nhưng không có quyền admin.

Tài liệu GitHub: [cấu hình nguồn xuất bản](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site),
[workflow Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
