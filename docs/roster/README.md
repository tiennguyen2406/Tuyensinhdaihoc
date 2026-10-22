# Roster institution/campus TP.HCM — P1-X1

**Partial, needs_review; as-of 22/10/2026.** Đây là dữ liệu proposal để review,
không là danh sách pháp nhân được duyệt, roster đầy đủ hay coverage admissions.

Baseline đã kiểm: checkout vận hành, origin `tiennguyen2406/Tuyensinhdaihoc`, branch
`codex/crawler-pilot`, HEAD/remote `0bef5a95f2d9587fa04f1721a619d040bf13e36d`;
không tracked/staged diff đầu task. 11 file untracked cũ, inventory/config/sources
và read-only `sources/` được lưu fingerprints và kiểm bảo toàn, không stage.

[CSV](hcm-institutions.csv) có **29 dòng thật**, không fixtures: 12 đơn vị từ inventory,
6 tên tác giả tham luận trong mục lục chính thức, 3 đơn vị mẹ và 8 địa điểm/đơn vị
tuyển sinh có evidence cache. Tổng loại đề xuất: **13 institution, 5 member_unit,
3 umbrella, 8 campus, 0 unknown**. `entity_kind` không chứng nhận tư cách pháp nhân.

[sources.json](sources.json) chứa URL, snapshot/hash/size đã recheck khi có raw,
locator, thời điểm và giới hạn. [validation.json](validation.json) chứa phép đếm
tái lập và kết quả kiểm. [decision.json](decision.json) là đúng payload D5 cần owner
chọn; không có signoff. Không có canonical UUID, approval command hay DB write.

## Nguồn và giới hạn phụ lục

Lead [pack hội nghị125trang](https://f1.hcm.edu.vn/data/doc/2026/hoidonghieutruong/2026_1/6/5-tai-lieu-hoi-nghi_61202618.pdf):
bìa ghi08/01/2026. TOC phân biệt báo cáo/kế hoạch **dự thảo** với Quyết định1399
ngày11/09/2025 và1559 ngày16/09/2025. Không lấy ngày hội nghị làm ngày hiệu lực,
không dùng các trang tổng hợp/Wikipedia làm legal evidence. Sáu tên mới chỉ được
đọc ở **TOC và nhãn tác giả tham luận**, chưa được xác nhận thành viên hội đồng.

Không có bản pack trong metadata/cache đọc được. Hai lần Python dừng TLS chain
verification, một lần Windows HTTP client lỗi receive; không nhận raw PDF, không
tắt TLS. Một browser navigation tới đúng URL hiện blank; không download thành công.
Công cụ nghiên cứu trả text từ cache PDF cũ5ngày, nhận diện125trang; mở lại qua
connector dùng cùng representation. Không trích text local lần nào, không OCR.
Sau đó remote open cũng timeout. **Hash/size pack để null**, không gán snapshot.
Đây không chứng minh provider từ chối truy cập hoặc mọi global cache đều thiếu.

Hai kênh kiểm ảnh không trả ảnh đọc được: native screenshot batch physical112–117
và một diagnostic physical114; connector probe physical114–116 rồi batch112–117.
Outputs chỉ references/`ImageDisplayed`, không có image content. Không nhận các
lượt gọi đó là đã nhìn trang. **0 trang PDF được kiểm trực quan thành công**.
Không tải hoặc lặp extraction để bù lỗi công cụ.

Cửa sổ bao trùm chuẩn bị/extraction/verification bắt đầu **13:16:56 +07:00**,
kết thúc **13:29:30 +07:00**, ngày22/10, dưới20phút; timer riêng được ghi13:18:35.
Đã đọc text excerpts bìa/TOC/chương trình, draft headers, mở đầu1559; không chứng
nhận toàn bộ125trang. Main appendix ứng viên **physical112–117** (index111–116)
chưa đọc được, TOC dẫn printed105; chưa xác minh page footer. Physical118–125 chưa
kiểm đầy đủ; phần4–111 không được whole-page review. Không tiếp tục PDF sau timebox.

Đối soát sequence **BLOCKED**: verified member rows0, expected sequence/count,
missing/duplicate/discontinuous numbers đều **unknown/null**, không phải “không có”.
29 CSV rows không phải29 appendix rows hoặc29 trường. Cột `appendix_sequence`
để trống, không tự cấp STT. P1-X1 chưa hoàn tất phần appendix/exhaustiveness.

Để khép blocker cần **đúng pack PDF ở link trên hoặc bản official institutional
copy, có pages112–117/appendix1399 và các STT đọc được**. Chưa xin mở OCR; raw giữ
private, kiểm bytes/hash trước khi dùng. Bản đã có text là lựa chọn tốt hơn nếu
appendix là ảnh; việc chuyển tự động/OCR cần phạm vi riêng.

## Identity, profile và ngày

`row_id` provisional, không là University ID. `official_name` là tên đề xuất giữ
`source_name`, chưa “officially approved”. Aliases giữ profile labels/tên đang có;
không tự bổ sung lịch sử đổi tên từ trí nhớ. Member units/campus giữ parent đề xuất
có locator; parent chain không phải legal ownership approval. Đặc biệt BVH/BVS
giữ **một mẹ PTIT**, không thành hai parent institutions. UEH KSA/Mekong và các
địa điểm HCMUS/OU cũng không tạo pháp nhân mới. Mã admissions có provenance riêng.

Giữ đủ12 profile IDs: `uit,nlu,ueh,hcmus,ptit,ou,hcmue,uet,hust,ctu,dut,haui`.
`uet,hust,ctu,dut,haui` vẫn **needs_review** cho HCM: inventory gợi địa danh ngoài
HCM nhưng chưa đủ để loại trừ campus HCM tại as-of. Không tự suy campus tương lai.
Nguồn DUT đã có text tên đơn vị mẹ, chưa có chứng cứ địa chỉ đầy đủ. 51 JSON files
trong `config/sources` gồm schema và50 variants/evidence/config, không là50 trường.

`source_document_date`, `checked_at`, `valid_from/to` tách riêng. Chưa có căn cứ
legal/temporal đủ nên validity để trống + `unverified`, không điền ngày thu thành
ngày hiệu lực. Footer hiện tại trên bài2024/2025 không chứng minh địa điểm cùng năm.
Không suy sự tồn tại2024/2025 từ pack2026. Bản cache chỉ được kiểm integrity offline.

## Hai phương án địa giới và đơn vị đếm đề xuất

[Nghị quyết202/2025/QH15](https://vanban.chinhphu.vn/?docid=213930&pageid=27160)
ban hành/hiệu lực **12/06/2025**; chính quyền mới hoạt động **01/07/2025**.
[Nội dung Chính phủ](https://baochinhphu.vn/nghi-quyet-cua-quoc-hoi-ve-sap-xep-don-vi-hanh-chinh-cap-tinh-102250612191145158.htm)
mục16 xác nhận HCM mới gồm HCM cũ, Bình Dương, Bà Rịa–Vũng Tàu. Attachment ký
được nhận diện5trang, chưa đọc ảnh; không nhận đây là đã đọc toàn văn ký.

Hai option cùng as-of **22/10/2026**, cùng counting policy:

- **A:** footprint TP.HCM cũ.
- **B:** footprint mở rộng gồm cả Bình Dương và Bà Rịa–Vũng Tàu cũ.

Một đơn vị đào tạo chỉ vào N khi có **legal status + validity evidence riêng** và
local presence thuộc option. Campus quy về đơn vị mẹ đúng một lần; mẹ ngoài HCM
có campus HCM vẫn có thể được tính một lần. Umbrella không cộng cùng leaf.
Member_unit có legal status evidence riêng được xét như teaching unit độc lập,
không mặc định là campus; hiện chưa có dòng nào đủ evidence này. Disposition của
option là đánh giá **địa lý**, không tự chọn scope hoặc cấp rights/publication.

| Phép đếm | A: HCM cũ | B: HCM mở rộng |
|---|---:|---:|
| Geographic in_scope rows | 2 | 12 |
| Trong đó institution/member_unit/umbrella/campus | 1/0/0/1 | 5/1/0/6 |
| Out_of_scope rows | 2 campus | 2 campus |
| Geographic needs_review rows | 25 | 15 |
| Các teaching-unit candidates có presence, chưa legal/temporal qualified | 1 | 6 |
| **N supported theo toàn bộ policy đề xuất** | **0** | **0** |
| Đạt50 / gap_to_50 | chưa / **50** | chưa / **50** |
| Đạt hơn50 (minimum51) / gap_to_51 | chưa / **51** | chưa / **51** |

**N0 là lower bound evidence-ready của gói này**, không nói TP.HCM không có trường.
Chưa có đủ hồ sơ pháp nhân/temporal; không nhận các candidates thành verified để
đạt mục tiêu. HCMUE địa chỉ nguồn có Quận5 hỗ trợ footprint cũ; các địa chỉ current
HCM khác thiếu mapping historical boundary nên A còn pending. Không tự gán Đông
Hòa/Phú Lợi sang tỉnh cũ chỉ từ trí nhớ. BVH tại Hà Nội, UEH Mekong–Vĩnh Long nằm
ngoài cả hai footprints theo địa điểm nguồn; đây không loại trừ mẹ có presence khác.

D5 phải chọn scope/counting policy, hoặc giao mở rộng national riêng nếu thiếu.
Chọn A/B không làm đầy legal/temporal gaps, không xác nhận đạt51. Tổng29 cũng không
được dùng làm mẫu số trường. Unknown geography và identity vẫn cần evidence.

## Kiểm dữ liệu, bytes review và Excel

Đã kiểm CSV/JSON parse, unique row/source IDs, parent/source references/cycles,
enum, locators/reasons, code provenance, validity ordering và12profiles. Đếm lại
hai options theo đúng predicates; review duplicate candidates, không auto-merge.
Phần sequence là blocked riêng, không ghi tất cả validation pass. Không tạo/test
`triage_sources.py`, không thêm framework hoặc chạy application suite cho dữ liệu.
CI vẫn chạy checks ứng dụng cấu hình sẵn sau push, không là roster business review.

Tái lập N và gaps từ CSV bằng Python stdlib (chạy tại repo root):

```python
import csv
from pathlib import Path

rows = list(
    csv.DictReader(Path("docs/roster/hcm-institutions.csv").open(encoding="utf-8", newline=""))
)
for option in ("A", "B"):
    n = len(
        {
            r["row_id"]
            for r in rows
            if r["option_" + option] == "in_scope"
            and r["entity_kind"] in ("institution", "member_unit")
            and r["legal_status"] == r["validity_status"] == "evidenced"
        }
    )
    print(option, n, max(0, 50 - n), max(0, 51 - n))
```

Text mới **UTF-8 không BOM, LF, có final newline**. `.gitattributes` chỉ áp dụng
`docs/roster/*.csv`, `*.json`, `*.md`; giữ bytes inventory cũ. Excel: **Data → From
Text/CSV → chọn65001: Unicode (UTF-8), delimiter comma**; không dựa vào double-click.

SHA review lấy từ **bytes Git blob tại commit/path**, capture nhị phân bằng Python
`subprocess.check_output(['git','cat-file','blob',commit+':'+path])`, rồi SHA-256;
không dùng Git object ID, PowerShell text redirection hoặc working-tree CRLF.
`decision.json` không chứa hash chính nó; bind CSV/sources/validation/README bằng
hash. Commit của quyết định cũng định danh dependency files. Sau commit kiểm lại
blob hashes, ghi receipt private và hiển thị commit/path/content SHA cho owner.
Payload/dep đổi cần review hash mới. Pending không tự là approval, không ký thay.

## Batch F1 nhỏ tiếp theo

Đề xuất **P1-X2: HCMUE-1 đúng một scope THPT2026/đợt2/địa điểm chính**, vì cached
S0 có address + row identity và supporting A01/offset đã có; không tải lại PDF.
Candidate `2782d6771643c2fc63a4805e76155e3e0f4479ec9c92d1e6ff3b881dbba3e1ea`,
packet `01ec56ad23954d5c2dcbe9d31381161d19fc33850b665b5037335ec92283c534` giữ nguyên.
Chuẩn bị cho F1 review, không mở F2. Blockers: identity/parent/effective scope,
authority/rights và field-level publication gates; domain final-S còn task F2 riêng.
Không yêu cầu Score Engine để review publication và không coi published là advice-ready.

Bốn next: **P1-B5** inventory/triage với roster; **P0-4** subtask khởi động API reader
và khép hai F1 smoke; **P1-X2** chọn batch nhỏ; **P1-X3** owner review từng field.
Đã có quyền start API loopback/web, dùng receipt private và runbook catalog; phải
kiểm PID/credentials/capabilities, không owner fallback/reset/seed. Không chạy API
trong task roster này. F1 vẫn partial, F2 deferred. Không DB/crawler/bootstrap/
publish/migration/release rebuild; roster rows **không tăng cutoff quota**.
