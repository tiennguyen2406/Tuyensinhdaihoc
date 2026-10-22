# F1 · Tra cứu ngành/chương trình — 22/10/2026

Subtask `P2-F2-F1-NAME` của `P2-F2`: `/majors` dùng proxied `GET /programs`
hiện có, tìm theo tên xuyên trường. Tên khớp không xác lập canonical Major.
Trang hiển thị university, program/Offering, năm, campus, method codes và số mốc
điểm chuẩn; link chi tiết trường giữ năm đang chọn. Catalog vẫn chỉ phục vụ
Offering có cutoff đã công bố. Không gọi cutoff theo từng hàng hoặc thêm tuition.

## Hành vi đã triển khai

- Dùng chung year selector với `/universities`, default2024; không fallback năm.
- Draft tách truy vấn đã gửi; button/Enter kiểm min2 sau trim cho validation,
  max120 ký tự nguyên bản. Query gửi giữ nguyên cả dấu, hoa/thường và khoảng trắng.
- `limit=20`, cursor API; render đúng thứ tự và giữ cả hàng trùng API trả về.
- Đổi năm xóa ngay kết quả/cursor, abort + invalidate response cũ, chạy lại đúng
  một lần query đã gửi; không dùng draft. Chưa submit hoặc đã xóa input: không search.
- Submit mới reset pagination. Không ghép dataset versions; 409 hoặc version
  mismatch restart từ trang đầu tối đa một lần, sau đó hiển thị lỗi/retry.
- Guidance, loading, API empty và failure tách rõ; empty không kết luận trường
  không tuyển sinh. Missing campus/method không thay bằng 0 hay campus khác.

## Kiểm chứng thực chạy

Baseline đầu task: nhánh `codex/crawler-pilot`, HEAD
`a90169fbdb3d2afb77fd5cdf25241d5fc2302de0`; remote khớp, không staged/tracked diff,
11 file untracked cũ được giữ nguyên. Fingerprints trước task lưu private.

| Kiểm tra | Kết quả và giới hạn |
|---|---|
| Vitest | **17 mới / 41 tổng**, 5 test files pass; fixtures hư cấu hai trường |
| Playwright | **2 mới / 8 tổng** pass; một test mới chạy hai viewport projects; API mock |
| ESLint / Prettier | Pass toàn `apps/web` |
| Next typegen / TypeScript | Pass |
| Next production build | Pass, có route `/majors` |
| 360px | Đã xem ảnh thẻ kết quả, form/navigation; body không vượt viewport. Trang lỗi API thật: body/document/viewport đều360px |

Local dùng binaries cài sẵn. Chromium bundled chưa có nên lần thử đầu không launch
được; dùng Edge đã cài, không thêm dependencies. Các cases pass; lượt attached-server
kết thúc exit0, 8 passed. Local config/screenshot/receipts giữ trong ignored state.
Runner có warning `NO_COLOR`/`FORCE_COLOR`. CI dùng Chromium theo workflow hiện có;
kết quả push run đúng SHA được kiểm riêng, không viện dẫn CI cũ.

## Hai smoke dữ liệu thật: chưa xác minh

Built page chạy với cấu hình API hiện có; không có listener API hoặc reader được
cấu hình khả dụng. Không tự chạy API bằng owner, cấp quyền hoặc tạo fixture DEV.

1. Discovery: đúng **một** `/universities?year=2024&limit=20` qua proxy trả502.
   Không lấy được PTIT nên không gửi discovery `/programs` hoặc đoán tên ngành.
2. Expected-empty: UI submit `zz_no_match_eduradar_f1_20261022` gửi đúng một
   `/programs` search, trả502; UI hiển thị lỗi và nút thử lại. **Không phải empty pass**.
3. Expected-match PTIT2024: chưa có tên thật từ bounded discovery nên **không gửi
   search**, chưa xác minh. Không seed, broad retry hay thay bằng mock.

Mock tests không chứng minh accent-insensitive matching backend, coverage nhiều
trường thật, browser→FastAPI→PostgreSQL hoặc acceptance vận hành/nghiệp vụ.

## Bảo toàn, trạng thái và bước tiếp

Chỉ đổi web UI/tests và public progress. Không đổi backend/proxy/schema/roles,
dependencies, raw/packets/approvals, canonical eligibility hoặc release. Không chạy
DB suite local, không đo SQL mới; số **3/20.000, catalog3, release v3** là lần kiểm
trước đã ghi trong progress, không phải số live của task này. Không tăng quota.

Settings/handoff và 9 reports private/unselected cũ giữ local. `sources/` chỉ đọc.
Dashboard chính thức nằm ở gói `deliverables/dashboard-20261022`, cập nhật tại đó,
không tạo master thứ hai trong Git. `P2-F2` giữ **partial**, subtask chờ review;
chưa có business acceptance. F2, advice gate, Score Engine và SNA chưa triển khai.

Đúng bốn việc tiếp theo theo Plan sửa: `P1-X1` roster pháp nhân/campus có nguồn;
`P1-B5` inventory/phân loại nguồn (không dựng script triage thiếu); `P1-B3`
taxonomy pilot có provenance; `P1-B4` binding proposal phụ thuộc taxonomy.
Ưu tiên **P1-X1**: roster phân biệt trường/campus, có hiệu lực và pending gaps;
không bịa đủ hơn50 trường. Smoke thật F1 còn phụ thuộc API reader khả dụng.

Review exact public paths → commit → normal push task branch → remote SHA match
→ kiểm push-triggered `checks` và `web`. Không merge/deploy hoặc xác nhận nghiệp vụ.
