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
71.011 dòng sạch, 292 trường, 472 ngành chuẩn, 94% dòng có `major_code` (mã 7 số Bộ GD&ĐT).
Bảng `admissions`: id, uni_code, year, method (THPT, HOCBA, DGNL_HCM, DGNL_HN, DGTD, DGNL_SPT, KETHOP,
CCQT, UTXT, KHAC), method_name, sub_method, program_code, major_code, program_name, program_type,
combos ("A00;A01"), score, scale_max, score_equiv, note, flag, match_how, source_url, crawled_at.
Bảng khác: universities, majors, admission_combos, tuition.

## Tab Tư vấn: độ hot (webapp/main.py `hot_index`, `hot_parts`)
Kết quả ≤ điểm + mốc, xếp độ hot giảm dần, trang 50 dòng (`offset`, `limit`).
hot = 0,5 × điểm trường + 0,3 × điểm ngành + 0,2 × điểm xu hướng (mỗi phần 0–1):
- điểm trường: hạng VNUR trực tiếp (101 − hạng)/100 (1 → 1,0 … 100 → 0,01); kế thừa đại học mẹ × 0,8; chưa xếp hạng 0.
- điểm ngành: percentile mức tăng bậc nút ngành G1 (`data/network/metrics/g1_uni_major_{2024,2026}.csv`);
  10% ngành cao nhất gắn "Ngành hot 2026"; dòng chưa có major_code = 0.
- điểm xu hướng: percentile (trong cùng phương thức) thay đổi điểm chuẩn 2025 → 2026 của cùng
  (trường, mã chương trình, phương thức, thang); thiếu một năm = 0,5.

## Đề án và học phí
- `pipeline/dean.py` → `data/clean/dean.json`: mỗi phương thức có `fields` {audience, conditions, formula,
  bonus, quota, notes} (gạch đầu dòng ≤ 240 ký tự), `common` (ý lặp ở ≥ 2 phương thức), `timeline` [{date, event}],
  `documents`. Kiểm: `python scripts/check_dean.py`.
- `data/manual/tuition.csv` (uni_code, year = năm bắt đầu năm học, min_mil, max_mil, unit_note, text, source_url,
  source_type official|press|aggregator, confidence). 0–0 = miễn học phí (hệ quân sự/công an). Quy đổi:
  tín chỉ × 30/năm, học kỳ × 2 (FPT × 3), tháng × 10. `data/manual/tuition_checked.csv` ghi trường đã tìm.
- 89 trường còn lại: `data/manual/hoc_phi_bo_sung_89_truong_20261024.md` → `python -m pipeline.tuition_import`
  → `data/clean/tuition_extra.json` (giữ đơn vị gốc, không quy đổi; mục không chắc ghi nguyên văn và liệt kê ở
  `data/interim/tuition_extra_review.csv`, `docs/hoc-phi-bo-sung-xem-tay.md`). Web dùng khi trường không có dòng trong tuition.csv.

## Quy tắc
- Sau khi sửa, tự chạy lệnh liên quan để kiểm (clean/sna/uvicorn) và báo con số trước–sau.
- Không thêm quy trình duyệt/receipt/hash/chính sách bản quyền nội bộ. Dữ liệu công khai, dùng học tập, có ghi nguồn.
- Không sửa trực tiếp `data/clean/` hay `data/eduradar.db`; sửa code hoặc `data/manual/` rồi chạy lại pipeline.
- SQLite trên ổ này: web mở DB `mode=ro&immutable=1`; pipeline dựng DB ở thư mục tạm rồi chép sang.
- Git: làm trên nhánh `v2-simple`; được commit code, `data/manual/`, báo cáo `docs/*.md`; không commit `data/raw/`, `data/eduradar.db`, `.venv`, `_to_delete/`.
