# EduRadar V2 — bối cảnh cho Claude Code

Đồ án môn SNA: web tra cứu điểm chuẩn đại học 2024–2026, tư vấn theo điểm, phân tích mạng xã hội.
Hạn nộp ~06/11/2026. Ưu tiên: chạy được, đủ yêu cầu đề bài, báo cáo rõ ràng. Trả lời bằng tiếng Việt.

## Kiến trúc V2 (KHÔNG thêm tầng mới, KHÔNG dùng lại hệ thống v1)
- `crawler/fetch.py` — gọi API công khai diemthi.tuyensinh247.com (`/api/school/search`,
  `/api/common/cutoff-score?school_id=&year=`), lưu JSON vào `data/raw/cutoff/<năm>/<MÃ>.json`.
- `pipeline/clean.py` — làm sạch/chuẩn hoá → `data/clean/*.csv`, `data/eduradar.db` (SQLite),
  `data/clean/quality_report.md`, `data/interim/major_unmatched.csv`, `data/interim/conflicts.csv`.
- `sna/build.py` — mạng G1 (Trường–Ngành), G2 (Trường–Trường, Jaccard), G3 (Ngành–Ngành),
  G4 (cạnh tranh có hướng) → `data/network/` (JSON cho web, GEXF cho Gephi, metrics CSV, PNG, summary.csv).
- `webapp/main.py` (FastAPI) + `webapp/static/` (index.html, app.js, style.css, vanilla JS, vis-network).
- Sửa dữ liệu bằng tay: `data/manual/major_map.csv` (name_key,major_code), `data/manual/tuition.csv`.
- Thư mục `services/`, `apps/`, `infra/`, `config/`, `docs/reports/` là hệ thống v1 cũ: chỉ đọc tham khảo.

## Lệnh (PowerShell, venv đã có pandas, networkx, fastapi, uvicorn)
```
.venv\Scripts\python.exe -m crawler.fetch          # chạy lại được, bỏ qua file đã tải
.venv\Scripts\python.exe -m pipeline.clean         # ~30 giây
.venv\Scripts\python.exe -m sna.build              # ~1 phút
.venv\Scripts\python.exe -m uvicorn webapp.main:app --reload   # http://127.0.0.1:8000
```

## Dữ liệu (23/10/2026)
71.008 dòng sạch, 292 trường, 472 ngành chuẩn, 94% dòng có `major_code` (mã 7 số Bộ GD&ĐT).
Bảng `admissions`: id, uni_code, year, method (THPT, HOCBA, DGNL_HCM, DGNL_HN, DGTD, DGNL_SPT, KETHOP,
CCQT, UTXT, KHAC), method_name, sub_method, program_code, major_code, program_name, program_type,
combos ("A00;A01"), score, scale_max, score_equiv, note, flag, match_how, source_url, crawled_at.
Bảng khác: universities, majors, admission_combos, tuition.

## Quy tắc
- Sau khi sửa, tự chạy lệnh liên quan để kiểm (clean/sna/uvicorn) và báo con số trước–sau.
- Không thêm quy trình duyệt/receipt/hash/chính sách bản quyền nội bộ. Dữ liệu công khai, dùng học tập, có ghi nguồn.
- Không sửa trực tiếp `data/clean/` hay `data/eduradar.db`; sửa code hoặc `data/manual/` rồi chạy lại pipeline.
- SQLite trên ổ này: web mở DB `mode=ro&immutable=1`; pipeline dựng DB ở thư mục tạm rồi chép sang.
- Git: làm trên nhánh `v2-simple`; được commit code, `data/manual/`, báo cáo `docs/*.md`; không commit `data/raw/`, `data/eduradar.db`, `.venv`, `_to_delete/`.
