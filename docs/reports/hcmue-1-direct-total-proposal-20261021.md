# HCMUE-1: đề xuất hợp đồng direct-total cho một scope — 21/10/2026

**Đã chọn hướng chuẩn bị hợp đồng direct-total có evidence, độc lập evaluator;
mọi field approval vẫn pending. HCMUE-1 tiếp tục unsupported.** Reviewer nghiệp vụ
có trách nhiệm chưa được chỉ định; không có nguồn mới, quyền mới hoặc basis mới
được duyệt trong dossier này. Đây là hồ sơ review, không là executable command,
approval, feature flag hoặc đường positive eligibility cho API.

Liên kết [ma trận batch 1](batch-1-readiness-20261021.md) và
[binding metadata HCMUE-1](batch-1-readiness-20261021.json). Dossier này bổ sung
diễn giải evidence của raw đã có; không sửa hai tệp đó hoặc frozen packet.

## Binding duy nhất được đề xuất

| Thành phần | Giá trị metadata bất biến |
|---|---|
| Snapshot `S0` | `74ea2ce3-eecf-4a45-9cac-53b7d4fdea49` |
| Raw SHA-256 | `9f243d01dd9f7018f3174f77af5ed759c4d939b3c9fcd21da57ddb59f24db9fd` |
| Raw bytes | 16029 |
| Source ID | `df4a4683-a8c1-474c-8a2f-12f2c1ce93b7` |
| Candidate key | `2782d6771643c2fc63a4805e76155e3e0f4479ec9c92d1e6ff3b881dbba3e1ea` |
| Packet SHA-256 | `01ec56ad23954d5c2dcbe9d31381161d19fc33850b665b5037335ec92283c534` |
| Resolution ID | `54d8c6d9-8d96-4978-9cca-ef1048166dc4` |
| Ngữ cảnh đề nghị review | HCMUE / năm 2026 / cơ sở chính / phương thức kết quả thi THPT / thông báo đợt 2 / physical row 2, score column 4 |
| Source URL đã cache | `https://tuyensinh.hcmue.edu.vn/index.php?option=com_content&view=article&id=27833&Itemid=9677&lang=vi&site=183` |

Không đưa điểm nguồn, tên/mã raw của dòng, body HTML hoặc packet dump vào tài liệu.
Mọi số thứ tự row/cell là vị trí vật lý, không là canonical scope/Offering identity.
HCMUE-2 ở column 5, hai dòng phân hiệu ngoài TP.HCM, các năm/notice khác đều ngoài
đề xuất này. Không lấy method kết hợp ĐGNLCB làm basis của HCMUE-1.

## Bộ locator để reviewer mở đúng bằng chứng

Các ký hiệu dưới đây là **nối chuỗi locator**, không là CSS alias đã có trong ứng
dụng. Mọi locator trong bảng field mang snapshot `S0` và raw hash nêu trên.

```text
A = html:html:nth-of-type(1) > body:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1)
H = A > table:nth-of-type(1) > tr:nth-of-type(1) > td:nth-of-type(1) > h2:nth-of-type(1)
B = A > table:nth-of-type(2) > tr:nth-of-type(2) > td:nth-of-type(1)
T = B > table:nth-of-type(1) > tbody:nth-of-type(1)
```

| Evidence pointer | Exact suffix sau khi mở rộng A/B/T | Ý nghĩa metadata, không trích raw text |
|---|---|---|
| E01 | `H` | Tiêu đề notice nêu năm/đợt/hệ đào tạo; tiêu đề chung gồm cả đại học/cao đẳng |
| E02 | `B > p:nth-of-type(1)` | Đoạn mở đầu xác định institutional publisher, năm và thông báo kết quả đợt 2 |
| E03 | `T > tr:nth-of-type(1) > td:nth-of-type(4)` | Header cột THPT, có năm kỳ thi |
| E04 | `T > tr:nth-of-type(2) > td:nth-of-type(3)` | Program source row và dấu chỉ địa điểm đào tạo tại trụ sở chính |
| E05 | `T > tr:nth-of-type(2) > td:nth-of-type(4)` | Ô score vật lý của exact candidate; không chép giá trị ở đây |
| E06 | `T > tr:nth-of-type(1) > td:nth-of-type(1)` và `T > tr:nth-of-type(2) > td:nth-of-type(1)` | Header/cell mã tuyển sinh của dòng |
| E07 | `T > tr:nth-of-type(1) > td:nth-of-type(2)` và `T > tr:nth-of-type(2) > td:nth-of-type(2)` | Header/cell mã ngành; đây là cột mà frozen candidate giữ làm offering_code |
| E08 | `B > p:nth-of-type(5)` | Ghi chú điểm theo tổ hợp gốc, dẫn tới thông tin độ lệch tổ hợp và kỳ thi khác |
| E09 | `B > p:nth-of-type(5) > span:nth-of-type(1) > a:nth-of-type(1)` | Link nguồn tới bài độ lệch các tổ hợp, article ID 27822 |
| E10 | `B > p:nth-of-type(5) > span:nth-of-type(1) > a:nth-of-type(2)` | Link nguồn tới bài độ lệch bài thi ĐGNLCB, article ID 27829 |
| E11 | `B > p:nth-of-type(6)` | Thông tin tra cứu/nhập học; giờ mở tra cứu không là hiệu lực score basis |

Node-text SHA-256 được tính bằng UTF-8 của `BeautifulSoup.get_text()` nguyên trạng
trên đúng node, không phải hash của display text đã làm sạch:

| Pointer | Node-text SHA-256 |
|---|---|
| E02 | `bc0278a14adc20dc04302bf4d79173049e9bb84792988753d6ba950b20475e31` |
| E03 (p con đầu tiên trong header cell) | `a7b3f8321067015743c02d8a76b9f99ca6934298d5cb41fcf78abd1df76e0d23` |
| E04 (p con đầu tiên trong Program cell) | `1e0fbcf1d86bb31083814f9bff0e5126228bc8d5524c6149989c8f43cf43fbfa` |
| E08 | `08dd360107e2e6cbb932e9f230a172b973ef3dc706bcdfa1a26d3740104c1e98` |

Chỉ snapshot/hash/locators và mô tả metadata được đưa vào dossier. Reviewer có
quyền truy cập raw riêng dùng chúng để đọc nội dung, không dựa hash làm phê duyệt
ý nghĩa. Không mở link đích, portal tra cứu, bản PDF/print hoặc đăng nhập.

## Ma trận field cần signoff

“Có evidence nguồn” dưới đây chưa có nghĩa approved canonical mapping hoặc đã đủ
direct-total. “Không thấy” chỉ giới hạn trong snapshot S0/business region B và H
đã đọc, không kết luận tài liệu chính thức khác không tồn tại.

| Field | Observed metadata | Exact snapshot + locator | Proposed representation nếu evidence đủ | Missing evidence / quyết định reviewer |
|---|---|---|---|---|
| Year | Năm tuyển sinh/thi 2026 có ngữ cảnh nguồn | `S0#E01/E02/E03` | `admission_year=2026`; kỳ thi THPT cùng năm là source context | Reviewer xác nhận hiệu lực đúng notice; không dùng năm trang làm bằng chứng cho nguồn khác |
| Campus | Dòng được đánh dấu đào tạo tại trụ sở chính | `S0#E04` | Giữ source campus label; canonical campus binding pending | Xác nhận trụ sở chính tương ứng campus TP.HCM tại mốc 2026 và đúng Offering; không suy từ footer |
| Method / exam | Header cột4 chỉ kết quả thi tốt nghiệp THPT 2026, khác cột5 kết hợp | `S0#E03`; cột5 chỉ dùng đối chứng ngoài scope | Source-local THPT2026, không tạo canonical method ID/exam-version token mới | Chốt method semantics, organizer/exam identity/version và hiệu lực; không dùng PTIT THPT2024 |
| Round | Title/đoạn đầu có nhãn đợt 2 | `S0#E01/E02` | Giữ source round label; canonical `round_key` chưa chọn | Chốt business key/đợt áp dụng; không suy ordinal hoặc dùng current crawl time để ưu tiên correction |
| University / Program / Offering / code system | Institutional attribution và một source row; hai cột mã có header khác nhau | `S0#E02/E04/E06/E07` | Giữ frozen candidate/binding; canonical IDs vẫn null | Reviewer quyết định persistent Program, Offering năm/campus và code system. Frozen offering_code lấy cột “mã ngành”; không tự coi đó là approved Offering key hoặc Major taxonomy; không sửa packet |
| Training / degree / track / language | Notice chung chính quy, gồm cả đại học và cao đẳng; row riêng phải được xét | `S0#E01/E02/E04` | Đề nghị review training mode theo context; degree/track/language giữ đúng mức evidence | Không lấy tiêu đề mixed degree để áp toàn bảng. Candidate training_mode null không được tự biến thành approved; track/language thiếu giữ unknown |
| Combination / tổ hợp gốc | Có ghi chú publication theo tổ hợp gốc và link độ lệch; không nêu identity tổ hợp gốc cho exact row ngay tại đây | `S0#E08/E09` | `combination_status=unknown`; base-combination identity chưa có; giữ note provenance | Cần exact original combination/membership/applicability cho row. Không gán A00/A01, `confirmed_none`, hoặc `source_aggregate`. Không coi cùng ô score là cùng cutoff cho mọi tổ hợp |
| Priority | Không thấy chính sách điểm đã gồm/chưa gồm ưu tiên, cộng điểm hoặc applicability cho exact row | `S0#B`, E03/E05/E08 là vùng đã xét | `priority_status=unknown` | Cần evidence tổng cuối cùng gồm/chưa gồm những ưu tiên nào, người dùng phải nhập S ở bước nào; điều kiện và hiệu lực; không suy none vì không có footnote |
| Weighting | Không thấy định nghĩa tổng môn, hệ số/môn nhân hoặc khẳng định không nhân hệ số | `S0#E03/E05/E08`, business region B | `weighting_status=unknown` | Cần quy định áp dụng đúng row/tổ hợp gốc. Không suy tổng ba môn hệ số1 hoặc nhân/chia để đưa về30 |
| Unit | Header là điểm trúng tuyển, không xác định đầy đủ đơn vị/basis của tổng S | `S0#E03` | Giữ source score như một Decimal có provenance; canonical unit pending | Chốt đơn vị và ý nghĩa tổng đã công bố; nhãn điểm không đủ chứng minh cùng unit/basis với S |
| Domain / min / max / precision / rounding | Không có explicit min/max/precision/rounding trong header/notes đã đọc | `S0#E03/E05/E08`, B | Domain/scale ID null; không tạo bounds hoặc rule | Cần miền hợp lệ và precision/rounding từ evidence. Không suy max30 hoặc min0 từ giá trị ô/cách gọi THPT; không clamp/round |
| Basis / version / offsets | Có dấu chỉ tổ hợp gốc và độ lệch, chưa có basis formula/identity/version/application cho row | `S0#E08/E09`; E10 là nhánh method khác cần tách | `basis_version=null`; `direct_total_supported=false` | Cần raw/final/converted status, original combination basis, độ lệch có áp không, priority/weighting/domain và hiệu lực. Không đặt basis UUID/version cho “đủ schema” hoặc thực thi quy đổi |
| Population / eligibility / conditions / tie-break | Notice kết quả không trình bày đầy đủ phạm vi hồ sơ, điều kiện, predicate hoặc tie-break riêng row | `S0#E02/E04/E08/E11` | Population/conditions/eligibility/tie-break unknown | Cần evidence applicability hoặc quyết định confirmed-none đúng field. Không dùng `GENERAL`, `MAIN`, `conditions={}`; giờ tra cứu/nhập học không chứng minh eligibility |
| Effective scope / publication precision | Có context notice2026/đợt2; không có hiệu lực basis rõ ràng | `S0#E01/E02/E11` | Giữ provenance, timestamp/hiệu lực chưa xác lập không tự điền | Chốt basis applies-to, effective dates/notices và supersession; không dùng giờ mở portal làm publication/effective timestamp |
| Authority | First-party attribution/domain có evidence; saved source vẫn unverified | `S0#E02` cùng source ID trong binding | Proposal narrow authority chỉ exact source/year/campus/method/row/snapshot | Reviewer nguồn xác nhận cutoff authority; scale/basis supporting source authority tách riêng. Cấu hình profile không là approval |
| Rights | Không có grant/căn cứ quyền được snapshot và intake dossier chứng minh | `S0#H/B`, [source review](../source-review.md) | Rights pending, không suy permission | Cần căn cứ lưu raw/xử lý, thương mại, tái công bố và attribution theo mục đích; owner direction không cấp quyền thay publisher |

**Finding cần giữ trong review:** packet hiện có `footnotes=[]` và
`source_scale_raw=null`, nhưng raw E08 là note nghiệp vụ thật ngoài bảng. Đây là
giới hạn của nội dung packet, không bằng chứng “không có điều kiện/độ lệch”.
Dossier bổ sung pointer này; không normalize lại, sửa packet hoặc đóng issue.

## Đặc tả đề xuất direct-total — chưa có hiệu lực

Hợp đồng chỉ có thể nhận **một tổng S đã hoàn chỉnh**, không nhận điểm từng môn
hoặc chạy chuyển đổi. Để đủ tư cách so trực tiếp, reviewer phải xác nhận bằng
evidence rằng S và cutoff của **exact approved admission scope** cùng:

1. Method/year/exam identity/version, University/Offering/campus/round và đối tượng.
2. Original-combination identity hoặc phạm vi được xác nhận; S đã ở đúng basis
   công bố. Chưa biết tổ hợp gốc thì tiếp tục unsupported.
3. Đơn vị/miền/precision, priority included/excluded, weighting, offsets và
   rounding đã được xác định. Nếu cần conversion/evaluation mà chưa có kết quả
   hợp lệ thì unsupported, không để người dùng tự khai “cùng basis” để vượt gate.
4. Conditions/eligibility/tie-break đã có representation và policy nhận đủ đầu
   vào, hoặc được reviewer xác nhận none bằng evidence đúng field. Không có
   evaluator không đồng nghĩa được bỏ conditions hoặc mặc định thỏa.
5. Hiệu lực, authority/rights, immutable evidence bindings và decision còn active.

Đây là checklist semantic để chuẩn bị một direct-total contract được review độc
lập evaluator. Nó **không yêu cầu xây T12/T13 trước khi reviewer xem hồ sơ**, đồng
thời không biến rule UUID, max score hoặc lời cam kết của người nhập S thành chứng
minh tương thích. Chưa tạo schema registry, basis/version ID hoặc runtime hook.

Sau khi có một hợp đồng tương thích được review và triển khai theo nhiệm vụ riêng,
quy tắc membership mục tiêu vẫn là `cutoff < S + 1`, strict, không cận dưới. Quy
tắc số học không xử lý equality tie-break/điều kiện tuyển sinh và không bảo đảm
trúng tuyển. Hiện endpoint theo [advice contract](../advice-contract.md) chưa có
positive eligibility; dossier này không đổi `items=[]`/unsupported.

## Checklist tiếp nhận source evidence và field-level signoff

| Mã review local | Hồ sơ cần nhận | Binding bắt buộc | Quyết định cần ghi rõ |
|---|---|---|---|
| DT-01 | Chỉ định reviewer nghiệp vụ và reviewer authority/rights phù hợp | Danh tính/vai trò có trách nhiệm; phạm vi exact candidate | Ai chịu trách nhiệm field nào; lựa chọn approve/reject/request_more có lý do; chưa có người được gán ở dossier này |
| DT-02 | Tài liệu THPT2026/đợt2 áp dụng row tại cơ sở chính | Snapshot/hash/locator, publisher, year/campus/method/Offering và applicability | Canonical identity/code system; không suy Major; không áp điều kiện của phân hiệu/method kết hợp |
| DT-03 | Bằng chứng tổ hợp gốc và độ lệch các tổ hợp | E08/E09 + snapshot của chính tài liệu đích nếu có sau này | Exact original combination, offset application, validity; không fan-out; không giả source_aggregate |
| DT-04 | Quy định điểm xét tuyển cuối cùng | Exact source rule/locator cho row, exam/version/effective scope | Priority, weighting, units/domain/precision/rounding và tổng S phải biểu diễn ở bước nào |
| DT-05 | Population/eligibility/conditions/tie-break | Same applicability; từng field có evidence hoặc explicit none decision | Policy thiếu input giữ unsupported; điều kiện nào ngoài khả năng direct-total phải tiếp tục chặn |
| DT-06 | Authority + rights độc lập | Exact nguồn cutoff và supporting scale/basis nguồn riêng | Phạm vi grant/authority; hạn chế lưu/xử lý/thương mại/tái công bố/attribution |
| DT-07 | Gói signoff cuối | Exact packet hash + evidence hashes + heads/context thực ở thời điểm review; nội dung/hiệu lực decisions | Mọi field required approved, không chỉ approval hướng; không dùng preview UUID. Nếu thay evidence/basis/context phải gói mới |

E09/E10 hiện chỉ là **link leads từ S0**, không là tài liệu đích đã xác minh. Saved
snapshot inventory của intake có hai HTML HCMUE (historical27810 và notice27833),
một robots snapshot; không có article27822/27829 trong inventory đó. Không khẳng
định cache global hiện tại không có chúng vì lượt này không truy vấn DEV hoặc các
store ngoài inventory đã giao. Không tự cấp network budget hay tải chúng trong task.
E10 thuộc nhánh ĐGNLCB, không bắt buộc thu cho HCMUE-1 nếu evidence applicability
không liên quan; E09 là lead có giá trị trực tiếp hơn cho tổ hợp gốc.

Mẫu field signoff cần giữ: field name → proposed meaning/value hoặc unknown →
snapshot/hash/locator → applicability exact scope → missing/competing evidence →
reviewer/role/date/decision → effect và giới hạn. Dossier có thể trả request_more
ngay; chưa đủ evidence thì không cần tạo basis ID hoặc command giả.

## Kiểm chứng của lượt chuẩn bị này

Chỉ đọc raw local đúng SHA/size, exact packet, frozen profile, saved snapshot
inventory và contracts. Resolve E01–E11 trên cùng DOM `html.parser`; raw score cell
duy nhất, không span; packet digest nguyên khớp. Hashes node text chỉ hỗ trợ integrity.
Không thêm tests/code/dependencies, không đọc credentials, kết nối DEV, crawl/OCR,
normalize/replay persisted jobs, approve/apply, release/build, commit hoặc push.

Các field để mở direct-total, canonical cutoff publication và source rights đều
**pending**. Direction lựa chọn đã chốt; không xin lại direction, không xin lại
PTIT approvals. Bước tiếp theo là tiếp nhận evidence còn thiếu và reviewer ký
từng field; chưa đủ căn cứ để có một direct-total scope được phép phục vụ.
