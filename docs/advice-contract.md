# Lát cắt advice chỉ đọc — 21/10/2026

Đây là phần độc lập của H1/P1 và T14, không phải nghiệm thu tư vấn cá nhân.
D1 **đã chốt**: `cutoff < S + 1`, nghiêm ngặt, **không có cận dưới**.
Thứ tự UUID chỉ phục vụ keyset, không thay đổi membership.

## Tra cứu đích và phạm vi

Tra cứu trường dùng University → Program → Offering → admission scope đúng năm.
Major chỉ dùng `programs.major_id` đã bind qua review; không suy từ tên hoặc mã
xét tuyển. `/majors`, taxonomy/binding mới và danh mục Offering chưa có cutoff
là backlog. Năm 2024/2025/2026 phải được chọn rõ, không fallback.

Học phí đích phải giữ amount/range dạng decimal string, currency, unit, scope,
admission year và academic year riêng, campus/track và provenance. Không quy
tín chỉ → năm, không lấy phí năm/campus khác. Hiện chưa phục vụ tuition;
`tuition=null` không có nghĩa bằng 0. Publisher/serving học phí là backlog riêng.

## GET `/api/v1/advice/cutoffs`

Input bắt buộc: `year`, `method` (mã chính xác), `scale_id`, `exam_version`,
`basis_version`, `score` (một tổng S đã có). Optional: `university_id`, `campus`,
`major_id` (chỉ binding canonical), `combination_id`, `limit` 1–200 (mặc định 50),
`cursor`. Không có input từng môn hoặc conversion. Unknown query field bị từ chối.

Điểm nhận **chuỗi ASCII dùng dấu chấm**, tối đa 7 chữ số phần nguyên và 5 chữ số
thập phân; không exponent, dấu phẩy, dấu +/- hoặc whitespace. Dấu phẩy chưa được
hỗ trợ nên không có suy đoán phân cách hàng nghìn. `Decimal`/`NUMERIC` xuyên suốt;
ngoài min/max của scale đã chọn trả 422 `SCORE_OUT_OF_SCALE`, không clamp/round.
Với scale tồn tại, bounds được kiểm trước compatibility nên vẫn 422 nếu đồng
thời sai method/year/exam; với scale không tồn tại không có bounds để suy đoán.
Scale không tồn tại hoặc method/year/exam version không khớp trả unsupported.
Thiếu input/sai định dạng trả 422 theo validation envelope hiện có của FastAPI.

Output kế thừa `catalog/1` metadata: `dataset_version`, coverage, release của đúng
version, warnings, `items` kiểu Cutoff (scope, conditions, provenance), next_cursor,
has_more; thêm `advice_contract_version=advice/0.1`, `context`, `status`,
`unsupported_reasons`, `excluded_summary`, `explanation`.
Context echo giữ score là decimal string. Coverage là coverage canonical catalog,
không phải số facts đủ tư vấn. `excluded_summary` đếm một lý do đầu tiên/fact
trong tập current/verified/published của **năm đã chọn** và các bộ lọc địa lý/Major;
không đếm dữ liệu unverified hay năm khác để tạo coverage giả.

## Compatibility và giới hạn chủ ý

Scale identity kiểm method/year/exam version, min/max/basis mô tả; basis_version
của scope phải khớp. Aggregate bị loại kể cả khi truyền combination; không chế tổ hợp.
Scope thiếu combination status/basis/conditions, predicate chưa đánh giá, thiếu
rule hoặc rule chưa được đánh giá đều bị loại có mã lý do. Cùng max không đủ.

**Chưa có đường positive eligibility trong endpoint này.** Schema/code hiện chưa
có approval phục vụ một tổng S trực tiếp độc lập evaluator, gồm ưu tiên, hệ số,
điều kiện và hiệu lực. Scope có rule cũng chưa chứng minh tương thích/eligible.
Do đó endpoint hiện chỉ trả `unsupported` hoặc `no_data`, `items=[]`; không có
feature flag, request parameter hoặc fixture hook để bỏ qua gate.

Phần đã triển khai độc lập: SQL ngưỡng strict và keyset nhận tập candidate IDs,
lọc **trước LIMIT**, được kiểm bằng facts synthetic trong DB riêng. Các ca positive
17/19/20/22/22.99 không chứng minh API đã cho phép tư vấn những facts đó.
Đây là giới hạn cần review rõ, không coi query số là eligibility nghiệp vụ.

Cursor HMAC bind endpoint riêng `advice`, toàn bộ input gồm S/context/filters/limit,
dataset_version và UUID cuối. Sai context 422; version đổi 409 `DATASET_CHANGED`.
Một response dùng reader riêng, READ ONLY REPEATABLE READ, timeout 5000ms. Thiếu
reader trả 503 `READER_REQUIRED`; không fallback owner cho endpoint mới.
Không bổ sung grants/provision khi request chạy. Proxy chỉ mở đúng `advice/cutoffs`.

UI tư vấn chưa thêm. Khi triển khai phải xóa kết quả và hủy request khi đổi
year/context/S, không ghép dataset_version, xử lý 409 bằng bắt đầu lại. Các
regressions catalog hiện có tiếp tục bảo vệ hành vi đổi năm/version.

## Quyết định cần evidence trước increment tiếp theo

Đề xuất ưu tiên reviewer xác nhận một scope nonaggregate có tổng công bố cuối
cùng và basis version với evidence cụ thể: method/year/exam, đơn vị/min/max,
priority đã gồm/chưa gồm, weighting, round/population/conditions và hiệu lực.
Người dùng **đã chọn chuẩn bị hợp đồng direct-total có evidence cho một scope
HCMUE-1**, độc lập evaluator; xem [dossier field-level](reports/hcmue-1-direct-total-proposal-20261021.md).
Giữ unsupported đến khi reviewer duyệt từng field và gate tương ứng được triển khai.
Không hỏi lại hướng chuẩn bị này. Không yêu cầu T12/T13 như prerequisite; cũng
không tự coi `conditions.kind=none` hay rule UUID là đủ để chấp thuận dữ liệu.
