# EduRadar V2 — Tra cứu điểm chuẩn & phân tích mạng (đồ án SNA)

Web tra cứu điểm chuẩn đại học 2024–2026 theo **trường** và theo **ngành**, **tư vấn chọn ngành theo điểm**,
và **phân tích mạng xã hội** Trường – Ngành (centrality, cộng đồng, HITS…).

## Chạy nhanh (Windows PowerShell, thư mục dự án)

```powershell
# 0. Một lần: cài thư viện vào venv
.venv\Scripts\python.exe -m ensurepip --upgrade
.venv\Scripts\python.exe -m pip install pandas networkx matplotlib scipy fastapi uvicorn

# 1. Thu thập (≈30 phút, chạy lại được, bỏ qua file đã tải)
.venv\Scripts\python.exe -m crawler.fetch

# 2. Làm sạch + chuẩn hoá -> data/eduradar.db, data/clean/quality_report.md
.venv\Scripts\python.exe -m pipeline.clean

# 3. Phân tích mạng -> data/network/
.venv\Scripts\python.exe -m sna.build

# 4. Web -> http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn webapp.main:app --reload
```

## Cấu trúc

| Thư mục | Nội dung |
| --- | --- |
| `crawler/fetch.py` | Gọi API công khai của diemthi.tuyensinh247.com: danh sách trường + điểm chuẩn từng trường/năm |
| `pipeline/clean.py` | Làm sạch, chuẩn hoá phương thức/tổ hợp/ngành, gộp điểm gốc–quy đổi, loại trùng, xuất SQLite + báo cáo |
| `sna/build.py` | Dựng 4 mạng G1–G4, tính độ đo, Louvain, Girvan–Newman, HITS, PageRank, dự đoán liên kết; xuất JSON/GEXF/CSV/PNG |
| `webapp/` | FastAPI (`main.py`) + giao diện (`static/`) |
| `data/raw/` | JSON gốc (bằng chứng nguồn) |
| `data/clean/` | CSV sạch + `quality_report.md` |
| `data/manual/` | Sửa tay: `major_map.csv` (name_key → major_code), `tuition.csv` |
| `data/network/` | Kết quả SNA; `gexf/` mở bằng Gephi |

## Dữ liệu

- 1 record = 1 dòng `admissions`: trường × năm × phương thức × chương trình (× nhóm tổ hợp).
- Phương thức chuẩn: THPT, HOCBA, DGNL_HCM (V-ACT), DGNL_HN (HSA), DGTD (TSA), DGNL_SPT, KETHOP, CCQT, UTXT, KHAC.
- `score` = điểm theo thang của phương thức (`scale_max`); `score_equiv` = điểm quy đổi về thang 30 nếu nguồn có.
- `major_code` = mã ngành cấp IV (7 số) của Bộ GD&ĐT; `match_how` cho biết cách map (mã gốc, khớp tên, gần đúng, thủ công).

Nguồn: diemthi.tuyensinh247.com — dùng cho mục đích học tập, phi thương mại. Luôn đối chiếu thông báo chính thức của trường.
