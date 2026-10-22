# HCMUE-1: contract đề xuất cho một tổng final S

Ngày22/10/2026; **proposal để review, chưa active**. Bổ sung cách phân loại yêu cầu
cho [advice/0.1](advice-contract.md); không đổi DTO, API hoặc publication contract.
[Báo cáo evidence](reports/hcmue-1-final-s-20261022.md) và
[manifest](reports/hcmue-1-final-s-20261022.json) giữ exact bindings/giới hạn.

## A. Điều kiện để so sánh lịch sử

Chỉ đề xuất một phạm vi HCMUE-1: tuyển sinh2026, kết quả thi tốt nghiệp THPT2026,
trụ sở chính, Công nghệ thông tin, source admissions-code `SPS`, source major-code
`7480201`, thông báo kết quả đợt2, S0 physical row2/c4. Hai hệ mã không tự trở thành
University/Program/Offering/Major IDs. Không mở HCMUE-2, campus hoặc năm khác.

| Field đề xuất | Giá trị/ý nghĩa | Evidence và giới hạn |
|---|---|---|
| Combination | Original A01: Toán, Vật lí, Tiếng Anh | PDF offset p6 TT302 xác định gốc; article27812 row45/c7 mục4 nêu membership. Title27812 còn “dự kiến”; reviewer phải xác nhận applicability qua chuỗi evidence sau đó. |
| Method/exam/year | Kết quả THPT2026; không học bạ/ĐGNLCB | Header S0 c4, S2 và article27804 mục2; method/exam/version canonical chưa approved. |
| Basis của S | ĐXT cuối cùng, đã gồm ưu tiên hợp lệ, ở original A01 của exact scope | Article27804 DOM p24–29, S0 note original basis và PDF. Không nhận tổng ba môn thô hoặc tổng tự chuyển từ tổ hợp khác. |
| Precision | Giá trị final ở độ chính xác hai chữ số thập phân theo nguồn | Đề xuất kiểm `S × 100` là số nguyên bằng Decimal, không làm tròn để đạt điều kiện; `22.5` và `22.50` cùng giá trị. Đây là proposal, không thay generic DTO hiện nhận tối đa5 số lẻ. |
| Validation domain | **Chưa có semantic min/max đủ căn cứ đã review; không có supported interval active** | Component thang10 không chứng minh trần final S. PDF MoET thu mới có đoạn trần điểm nhưng số/ngày/hiệu lực để trống, xung đột metadata portal. Không dùng nó để duyệt max30 hoặc đặt min theo ngưỡng nhận hồ sơ. |
| Offering/round/population/basis version | Phải là exact server-trusted reviewed context, không suy từ client string | Giữ packet/bindings. Scope-defining condition nào làm thay đổi ý nghĩa cutoff/S vẫn là comparison gate; unknown không thành none. |
| Fact/evidence/decision validity | Current/verified/published, đúng scope/basis/evidence revision và active review | Publication riêng không chứng minh so sánh được. Source authority, rights và canonical identities chưa được duyệt. |

Server phải xác minh compatibility từ evidence/decisions đáng tin cậy; client chỉ
chọn context được hỗ trợ và nhập S. Không lấy matching max/scale/rule UUID hoặc
basis string làm approval, không tin checkbox “final” để vượt gate. API hiện chưa
có trusted direct-total lookup hay exact-scope serving path: đây là dependency của
task triển khai gate sau, không giả đã có endpoint/options/schema đó.

Khi tất cả A được chứng minh và gate được giao riêng: một phép lọc
**`cutoff < S + 1`, strict, không cận dưới**, dùng Decimal/NUMERIC và JSON decimal
strings; SQL lọc trước limit/keyset. Cursor bind dataset_version và toàn context/S,
decision validity; một response READ ONLY REPEATABLE READ có timeout. Không trộn
versions, không fallback năm, không đổi campus hoặc fan-out aggregate.

## B. Những việc chỉ cần nếu ứng dụng tính S

Không nhận điểm từng môn trong lát cắt này. Vì nhận ĐXT cuối cùng đã có, không cần
triển khai thuật toán ưu tiên, xác định khu vực/đối tượng, weighting từng môn,
quy đổi tổ hợp hoặc tie rounding để **tính lại** ĐXT. Không cần T12/T13 trước review.

Vẫn cần biết S đang ở bước cuối nào, priority đã gồm gì, precision và domain nào
để tránh so tổng thô với cutoff final. Rule tính chi tiết có thể là evidence để
chứng minh domain/basis; thiếu implementation thuật toán không tự chặn comparison,
nhưng thiếu căn cứ cho domain/basis thì vẫn chặn. Không chạy DSL, convert, clamp,
round S hoặc cộng ưu tiên lần nữa. Không dùng ngưỡng nhận hồ sơ S2 làm cutoff S0.

## C. Giải thích tuyển sinh, không kết luận eligibility

Đề xuất sản phẩm chỉ cung cấp đối chiếu lịch sử với cutoff trong context đã duyệt,
không kết luận thí sinh đủ điều kiện hay có xác suất/bảo đảm trúng tuyển.

Graduation/population, điều kiện đăng ký, nguồn tuyển, tie-break, chỉ tiêu và ưu
tiên nguyện vọng phải có provenance hoặc hiển thị unknown. **Không cần thu toàn bộ
đầu vào eligibility chỉ để sắp một kết quả so sánh số**, nếu reviewer xác nhận các
điều kiện đó không làm thay đổi basis hoặc scope của cutoff đang so. Nếu một điều
kiện thực sự phân chia population/basis/score thì chuyển lại A và giữ unsupported
khi thiếu context; không gán `conditions=none` hoặc giả đã đánh giá predicate.

Không dùng trần/domain validator để lọc theo ngưỡng nộp hồ sơ hoặc thêm cận dưới
cho D1. Tình huống đồng điểm/điều kiện riêng được giải thích, không tự suy quyết định
trúng tuyển từ S. Phân tách A/B/C này là proposal policy cần reviewer có trách nhiệm
xác nhận; không miễn các publication/serving gates hiện hữu.

## Readiness và việc phải chốt

Đủ evidence mới để đề xuất A01 membership và diễn giải final ĐXT; chưa đủ domain/
hiệu lực/authority/rights/identity để activate. **Publication NO-GO; advice NO-GO**.
API vẫn `items=[]`, unsupported/no_data. Không triển khai registry/projection,
migration, trusted gate, advice/options/UI, Score Engine hoặc SNA trong task này.

Ưu tiên reviewer xác minh đúng bản ban hành có số/ngày/hiệu lực của rule2026 và
domain final S; ghi quyết định field-level với exact evidence hashes. Sau đó mới
quyết định scope/basis/identity/rights và giao task gate. Chưa có reviewer, signature,
approval date hoặc canonical IDs được tạo.
