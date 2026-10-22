# Quyết định và evidence còn thiếu — 21/10/2026

Cập nhật lúc **21:36 Asia/Bangkok**. Baseline code `5e25c0e…`; thay đổi mới
chưa commit. Phân biệt yêu cầu đã chốt, lựa chọn hướng chuẩn bị và approval dữ liệu.

| Mục | Trạng thái / quyết định | Hệ quả trong increment |
|---|---|---|
| D1 | **Đã chốt** strict `cutoff < S + 1`, **không cận dưới** | Decimal/NUMERIC; test S22 và S25 đúng biên. Không mở lại `<`/`<=`. |
| D2 | Đã chốt tổ hợp là optional filter chỉ khi có evidence/scope | Không manufacture tổ hợp; aggregate vẫn bị loại dù request có combination. |
| D3 | Năm phải explicit; không fallback | API bắt year2024/25/26; context scale khác năm unsupported, năm trống no_data. |
| D4 | Tier B **OFF**, chưa được public/advice/quota | Chỉ canonical current/verified/published được xét; 731 candidates vẫn unverified. |
| D5 / roster | **Thiếu evidence và owner decision** | Bảy technical leads không là roster >50 pháp nhân; denominator còn unknown. Tách parent institution/campus. |
| D6 / tuition | Contract đích optional, đúng unit/currency/scope/admission-year/academic-year | 0 canonical rows; publisher/serving chưa làm, null khác 0. Không quy tín chỉ → năm. |
| D7 / nghiên cứu | SNA T16–T18 **được bảo toàn**; ngoài increment | Chờ rubric/câu hỏi nghiên cứu trước graph/metrics/dashboard. Không lấy việc bỏ form môn học làm lý do bỏ SNA. |
| Hướng HCMUE-1 | **Người dùng đã chọn** chuẩn bị direct-total có evidence cho một scope, giữ unsupported đến reviewer duyệt | Đã lập dossier field-level. Đây không là approval scale/basis/rights/identity hoặc lệnh thực thi. Không hỏi lại hướng này. |
| Reviewer / rights | **Chưa có người chịu trách nhiệm được chỉ định** trong evidence của task | Dossier DT-01–07 yêu cầu từng field và applicability, không ký thay owner. |
| Major | Chỉ dùng binding canonical hiện có; taxonomy mới pending | Không seed Major, không suy từ tên/mã ngành; `/majors` là backlog. |
| PTIT approvals | **Giữ nguyên** approvals trước và exact hashes | Không xin lại vì filename có `draft`; không mở rộng approval sang năm/trường khác. |

## Các lựa chọn kỹ thuật đã thực hiện trong phạm vi được giao

- Thêm diagnostics/validation chỉ đọc `/advice/cutoffs`, có context/version và lý do
  loại; hiện **không có positive eligibility path**. Rule UUID không thay đánh giá
  priority/weighting/conditions/hiệu lực. Không thêm bypass flag.
- SQL helper ngưỡng/keyset được thực thi và kiểm độc lập trên synthetic canonical
  rows. Không nối helper vào đường serving bằng một eligibility giả; bước nối cần
  hợp đồng direct-total đã được review và triển khai gate tương ứng.
- Score nhận decimal string dấu chấm, tối đa 5 số lẻ. Không nhận dấu phẩy/exponent/
  whitespace. Known scale kiểm bounds trước compatibility: ngoài miền luôn 422,
  kể cả đồng thời sai method/year/exam. Unknown scale unsupported, không đoán bounds.
- UUID keyset tái dùng catalog/cursor; mọi input/S/filters/limit/version được bind.
  Không cần sort theo khoảng cách hoặc `abs(delta)`.
- Reader riêng được kiểm capability, session identity, privileged attributes,
  ownership và quyền ghi. Không provision/grant trên DEV hoặc trong web request.
- Không migration: `0001_core.sql` đã có pg_trgm, university/program trigrams,
  program_year_filter và current_verified_cutoff. Không thêm index trùng hoặc
  cột `majors.normalized_name` không tồn tại. Chưa tối ưu/benchmark, không có SLO claim.
- Sửa mô tả T08/T09 cũ trong data contract. **Hoãn runtime marker**
  `release_builder='not_implemented_T09'`: payload/job consumers, frozen hashes và
  compatibility cần một task kiểm riêng. Không đổi lịch sử jobs hoặc gọi đây docs-only.

## Những đề xuất chưa được duyệt

HCMUE-1 là review unit nhỏ nhất so với OU campus-unknown và UEH dossier rộng hơn.
Đề xuất direct-total chỉ mở sau evidence exact original combination, final-score
basis, domain, priority/weighting/conditions/effective scope và authority/rights.
Raw có note/link độ lệch mà packet không mang vào footnotes; không suy none.
Header mã tuyển sinh/mã ngành cũng cần reviewer chốt identity/code system trước
canonical binding. Xem [dossier](hcmue-1-direct-total-proposal-20261021.md).

Quota toàn dự án hiện **3/20000**, riêng HCM campus published1. Chuyển quota thành
HCM-only, định nghĩa địa giới/mốc roster, sampling/reviewer capacity, rights public/
commercial, rollout Tier B và lịch nhân sự đều chưa có quyết định đủ evidence.
23 tuần/week11 trong clau là giả định đề xuất, không là cam kết của phiên này.

Không bootstrap, approve/apply, build release, crawl/OCR, commit/push/merge/deploy.
Release3 giữ nguyên; không gán cứng release4 cho công việc tương lai. Không tuyên bố
P0–P4, public readiness, SLO/RPO/RTO, quota hoặc nghiên cứu đã hoàn tất.
