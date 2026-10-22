# HCMUE-1: membership mới, final S và conflict phiên bản — 22/10/2026

**Đã giải quyết membership A01 từ nguồn HCMUE; đã tìm và thu attachment MoET, nhưng
chưa chứng minh được nó là bản ban hành có hiệu lực.** Contract mới tách comparison,
calculation và admission explanations; không yêu cầu xây toàn bộ scoring algorithms.
Publication và positive advice vẫn **NO-GO**, không có business approval.

## Evidence thực mới và applicability

Tìm cache trước HTTP: live SQL READ ONLY REPEATABLE READ kiểm toàn bộ76 snapshots
baseline, chưa có snapshot/source body27812. Một occurrence
27812 ở raw HCMUS là chuỗi không chứng minh tài liệu HCMUE đã có. Trước khi đọc,
kiểm SHA/bytes từ raw_uri thực, không giả vị trí checkout.

Article27812 thu đúng URL được owner giao bằng existing Crawler/Store/RawStorage,
profile mới exact seed+robots, depth0, concurrency1, rate0.5/s, verified=false.
Snapshot `aba9b95d-47dc-4e7a-9409-f37ebc954d90`, 110741 bytes, raw SHA
`ec0cd10bc99ac3cf9234a48dc7cd414a358240b3722039e139d3c13e90ff972c`.
Full URL/locators ở [manifest](hcmue-1-final-s-20261022.json).

Tiêu đề còn “dự kiến”, displayed date14/4/2026. Bảng tại business region:
physical row45 (TT44), c2 mã xét tuyển7480201, c4 mã ngành7480201, c7 mục4 THPT
xác định A01 là **Toán, Vật lí, Tiếng Anh**. Không lấy A01TO trong mục3 kết hợp
ĐGNLCB làm A01. Section cha là đào tạo tại trụ sở chính. Không dùng chỉ tiêu dự
kiến làm quota/threshold hoặc chép toàn source row ra public report.

Applicability là đề xuất có chuỗi đối chiếu, không silently promote dự kiến:
article27812 nêu membership; PDF offset thu trước, SHA
`4cbe360fdcf5915b215376ae92f79bdf925983ef2f9a097efbf2f8f8b092c779`,389713 bytes/8
trang, p1 section SPS và p6 TT302–305 xác định original A01 cùng mã/ngành/method.
S0 kết quả THPT2026/đợt2 trực tiếp dẫn S1 về original-combination offsets, S1 dẫn
đúng PDF này. S2 đợt2 cùng row/campus trực tiếp dẫn article27804 về phương thức.
Các chứng cứ sau củng cố A01 của exact scope, nhưng không tự chứng minh mọi nội
dung dự kiến, membership revision hoặc supersession đã được người phụ trách duyệt.

Article27804 được tái dùng đúng loại **browser DOM text excerpt**, không gọi là
registered raw/snapshot. Hash excerpt
`876a89c123a4fb10a55e67aa188e83e5f0652ba5cafd3af884cb4b516984101b` khớp; p24–29
mô tả final ĐXT gồm tổng ba môn và ưu tiên, làm tròn2. Offset PDF không tải lại;
frozen packet/candidate/parent hashes giữ nguyên.

## Một tài liệu bổ sung: MoET và conflict cần giữ

Tra cứu official sources xác định cổng MoET niêm yết đúng `06/2026/TT-BGDĐT`,
ban hành/hiệu lực15/02/2026, khớp số/năm mà article27804 viện dẫn. Công cụ web
trích cổng trả403; normal Edge mở được cổng và trang detail. Đó là lỗi extraction
path quan sát được, không chứng minh origin từ chối normal public access. Không
login, thay identity, bypass robots/TLS/CAPTCHA hoặc dùng URL download tự chế.

Dùng attachment control hiển thị `Thong_tu_06_2026_QuyCheTuyenSinh.pdf`. File thực
1268693 bytes/32 trang có text, SHA
`572a0769048a3c6859012bf6e9f0e6a1f7ca4074fe753905cf070e1d213221c6`. Đã lưu bằng
RawStorage, hash read-back, extract và nhìn trực tiếp p1,p7,p10. Đây là **browser
downloaded PDF, chưa đăng ký DB snapshot**; không invent UUID/HTTP headers/revision.
Bộ chờ download timeout nhưng completed file cục bộ được kiểm bytes; không tải lại.

**Conflict:** p1 thực để trống số trước `/2026/TT-BGDĐT`, ngày ban hành và ngày hiệu
lực tại Điều2; không có số/ngày được đóng thêm trong ảnh. Portal lại niêm yết đầy
đủ số/ngày. Không khẳng định đây chắc chắn là bản cuối hoặc sửa metadata để hợp
thức hóa. Nội dung p7 Điều6.2(d) có trần final score, p10 Điều7.4 có ưu tiên giảm
dần, nhưng **chưa dùng chúng làm rule/domain có hiệu lực2026**. Không thay bằng
rule2022/2025 từ trí nhớ và không mở thêm document để vượt giới hạn một rule bổ sung.

Thiếu implementation ưu tiên/rounding không phải blocker tự thân cho một S đã
final. Blocker thật hiện là xác minh version/hiệu lực và semantic validation domain,
cùng approved scope/basis/identity/authority/rights. Không suy max30 từ component
maxima hoặc nhãn filename; không chuyển nguồn tuyển/threshold thành cận dưới D1.

## Phiếu field-level để reviewer có trách nhiệm xem

Reviewer chưa được chỉ định; mọi dòng dưới là proposal/pending, không ký unknown.

| Proposed field/value | Evidence/applicability | Alternatives | Consequence / reviewer role |
|---|---|---|---|
| Original A01 = Toán/Vật lí/Tiếng Anh | 27812 row45/c7 mục4 + offsetPDF p6 + S0→S1 | Xác nhận applicability bằng evidence version; hoặc giữ pending khi có correction chưa rõ | Comparison context và publication combination; reviewer nghiệp vụ/basis |
| S là ĐXT cuối cùng đã gồm ưu tiên, precision2 | DOM27804 p24–29; S2 dẫn cho đợt2; S0 original basis | Final ĐXT cùng basis; tổng thô/ĐGNLCB/tổ hợp khác unsupported | Không tính lại S hoặc cần Score Engine; reviewer basis |
| Domain final S chưa active | Portal06/2026 so với PDF p1 để trống promulgation fields | Xác minh đúng bản ban hành/hiệu lực và bounds; hoặc giữ unsupported | Chặn validator/comparison, không ký max30/none; reviewer rule/hiệu lực |
| Điều kiện chỉ để giải thích khi không đổi basis/scope | S2 population, DOM27804 xét giảm dần; không có full tie-break cho exact scope | Historical-comparison policy với unknown disclosures; hoặc condition phân scope chuyển thành gate A | Không tuyên bố eligibility/admission; reviewer product/scope |
| Canonical identity/code-system và authority/rights | S0/S2/PDF/source relationship, capture riêng không cấp quyền | Review mapping/căn cứ use rights; hoặc từ chối phạm vi sử dụng | Publication/serving tiếp tục đóng; reviewer identity và người phụ trách quyền |

[Contract final-S tối thiểu](../hcmue-1-final-s-contract.md) ghi chi tiết A/B/C và
bindings. Không có supported semantic interval active; transport syntax hiện có
không thay domain approval. Không thêm gate/projection/framework/DDL/UI/options.

## Accounting, preservation và giới hạn công khai

Controlled HTTP **1/8**: một GET27812/HTTP200;0 redirects/retries/robots wire vì
existing robots cache còn hợp lệ và được crawler kiểm. Một ledger mới, run mới
`24f72c32-8bb9-4a80-81ad-c51bed98e8a6` paused dùng1/8. Hai old runs không resume.
Browser riêng: mở cổng MoET, click detail chưa đổi state, navigate đúng href đã
quan sát, một attachment Download. Hai locator inspection timeouts không phải
download/network retries. Không quan sát browser subrequest/delivery URL nên không
báo tổng wire HTTP. Web-search/extraction là provider events riêng, không cộng giả
vào Store counter hoặc gọi traffic đó là0. Không thực hiện controlled HTTP thứ2.

Live before/after READ ONLY REPEATABLE READ so34 bảng và hashes: canonical,
observations3644, audit47, approvals/prior jobs, catalog3, quota3/20.000, một release
giữ nguyên. 637 frozen files và76 raw blobs cũ nguyên bytes/hash. Expected/actual
delta: +1 source/snapshot/job/fetch/schedule/run, chỉ host-state HCMUE cập nhật;
after sources84/snapshots77/jobs156. Hai PDF/HTML mới là supporting evidence,
không tăng quota. Release v3 kiểm actual bundle checksum, không rebuild.

MoET PDF nằm private RawStorage với receipt; không ghi source/snapshot/fetch/job
cho nó bằng metadata tự chế. Capture có ghi acquisition metadata vận hành cho
27812, **không phải toàn task read-only**. Không OCR, T05–T07 re-ingest, bootstrap,
reviewer/publisher apply hoặc canonical eligibility mutation. Protected untracked
settings/handoff và mọi historical report giữ nguyên.

Public chỉ đưa metadata/diễn giải tối thiểu này cùng contract/manifest; raw bodies,
source rows đầy đủ, DOM excerpts, PDF, images/extraction, packets, approvals,
runtime dumps/credentials/signed URLs và các reports deferred vẫn local. Việc push
báo cáo không là data rights hoặc approval. Không rerun application suites chỉ vì
Phase B docs/evidence; kiểm JSON/hash/locators/preservation/links và actual index.

## Quyết định và một bước kế tiếp

**Publication NO-GO:** identity/scale/basis/scope/source authority/rights/fact review
chưa đủ; không cần executable Score Engine chỉ để xem publication fact.
**Advice NO-GO:** membership đã có evidence mới, final-S contract đã thu hẹp,
nhưng domain/hiệu lực/approved context và trusted gate chưa đủ. API vẫn fail-closed.

Ưu tiên tiếp theo: owner chỉ định reviewer nghiệp vụ/hiệu lực xử lý **một conflict
cụ thể portal06/2026 versus attachment chưa điền số/ngày**, xác minh bản ban hành
đúng và domain final S cho THPT2026 trước khi xem gate implementation. Không yêu
cầu người dùng tự tìm lại membership đã thu; không yêu cầu xây thuật toán ưu tiên.
Sau domain/applicability mới review identity/authority/rights và gate theo nhiệm vụ
riêng. Tuition/Major/roster/SNA(rubric)/operations tiếp tục backlog, D1 strict không
cận dưới giữ nguyên.
