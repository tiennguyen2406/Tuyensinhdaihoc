# T08 — UEH KSA 2024 PT6: bàn giao quyết định 54 dòng

Baseline local/remote đã đối chiếu: `f986b928dfb4ef91c40ef29f21d05e4f7af7299d`,
branch `codex/crawler-pilot`. CI baseline:
<https://github.com/tiennguyen2406/Tuyensinhdaihoc/actions/runs/39360700958>.
Task chỉ đọc DEV, chuẩn bị quyết định và draft chưa duyệt; không apply/bootstrap,
publication, release, deployment hay cấp quyền sử dụng. Không sửa production code,
contracts, frozen packets hoặc overlay 77 candidates.

## Phạm vi đã kiểm đủ

Snapshot `67f11fe2-3a23-4d3a-8d67-fb468f66ec54`, 284975 bytes, raw SHA-256
`09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207`.
Nguồn:
<https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/>.

Chọn table thứ 2 trong business region duy nhất
`.elementor-widget-theme-post-content > .elementor-widget-container`:
57 physical rows = 2 headers + **54 programs + 1 total**. Đối chiếu 54/54 original
T08 packets bằng `checked_packets`, immutable parents, raw score/Decimal, full code,
name, combination, physical score cell, PT6 header/year/KSA/chính quy. Các cell
code/name/combination/score được chọn đều là cell vật lý; không fan-out theo tổ hợp
hoặc cột ngôn ngữ. Không reprocess hoặc thêm observation/job/candidate.

Loại khỏi tranche 23 logical candidates: 2 ISB + 15 KSV August + 6 September.
Không giao nhau với published PTIT snapshot hoặc cutoff evidence observations.
Tranche manifest giữ exact 54 bindings, row hashes, current heads và parent jobs;
phụ lục parser/T06/T07 payload hashes được ghi riêng, không sửa manifest lịch sử.

Existing chain: parser `c158decc-bb90-4fbd-845f-b073a99a2d6e`, normalization
`c2051e7d-40fa-4445-96d8-233309329204`, resolution
`d5923cc7-8cd5-4792-9fed-9981a37cdc30`. Global head vẫn
`registry/ptit-scale/20261018-c1`, alias
`aliases/ptit-identities-authority/20261018-r2`.

## Quyết định có giá trị cụ thể

Private dossier: `state/review/ueh-2024-ksa-pt6-signoff/owner-decision-sheet.md`.
Phiếu tiếng Việt có bảng 54 chương trình/điểm, phương án identity từng dòng,
19 quyết định chung và SHA-256 bytes của từng artifact; không bắt owner đọc JSON.
Mỗi quyết định giữ affected set/bindings, proposed value, alternatives,
prerequisites, evidence locators/hash, phần thiếu và tác động duyệt/từ chối.

| Readiness của quyết định chung | Số | Nội dung cần xử lý |
|---|---:|---|
| `source_evidence_complete` | 3 | KSA-01 bản chép/context; KSA-05 note 14 dòng (*); KSA-09 ngày/context August |
| `reviewer_confirmation_required` | 8 | University, Method, authority cutoff, authority scale evidence, combination aggregate, round semantics, Offering/language, Program identity |
| `external_evidence_required` | 7 | Formal scale/basis, population/conditions và 5 quyền sử dụng tách biệt |
| `technical_blocker` | 1 | Chưa đủ prerequisites để lập 54 fact commands |

Thêm **54 quyết định P01–P54** về identity từng dòng, đều chờ reviewer. Không có
quyết định mới được phê duyệt. `field-evidence.csv` có 972 field records:
446 source-complete, 270 reviewer-required, 162 external, 54 technical, 40
not-applicable. Các số này không phải số facts hoặc approvals.

## Program khác Offering; đính chính identity

54 full codes và 54 source labels được giữ làm đề xuất, không suy tự động 54
canonical Programs. Các họ `_01/_02/_03` không được gộp theo code prefix hay gán
Major taxonomy. Matrix giữ pending Program/Offering keys, training mode,
language availability, original labels/markers và bằng chứng xung đột.

Có **13 cặp KSA–KSV** cùng tên chương trình sau khi bỏ marker để so sánh và cùng
official program-profile href ngay trong snapshot: đây là cơ sở đề xuất cùng
persistent Program, với campus-specific Offerings riêng, vẫn cần người duyệt.
Không fetch profile đích, không tự gộp UUID. Một cặp Kinh doanh quốc tế chỉ có tên
tương đồng, không có shared profile href, tiếp tục để mở. Context September `(S)`
và biến thể curriculum không được nhập vào scope KSA-main. Chi tiết links,
locators và phương án nằm trong `identity-evidence.json`/`program-identity.csv`.

**Đính chính báo cáo controlled-batch trước:** code `7340201_02` ở **KSA là Thuế**,
ở **KSV là Tài chính**; báo cáo trước đã đảo campus khi diễn giải label sets.
KSA `_01` là Tài chính công / KSV `_01` Ngân hàng; KSA `_03` Ngân hàng /
KSV `_03` Thuế. Raw cells và frozen packets vẫn đúng, không sửa hoặc thay lịch sử.
Quan hệ Thuế/Ngân hàng/Tài chính phải xét tên và profile, không xét code đơn lẻ.

## Những gì nguồn August thực sự chứng minh

Locators đầy đủ nằm trong từng quyết định; các số p sau đây là paragraph trực
tiếp trong business region của đúng raw hash trên.

- p1/31/37/43: ngày 17/08/2024, UEH, chính quy, PT6 dựa THPT 2024 và campus KSA.
  Ngày có precision day; 14h18/08 tại p39 là giờ tra cứu, không phải publication
  timestamp. Có thể giữ `source_published_at=None`; không tự gán midnight.
- p42: cutoff từng chương trình/campus bằng nhau giữa tổ hợp và nguyện vọng.
  Đề xuất `source_aggregate`, một physical fact; chưa tự gán approved
  `combination_status`. Nếu được duyệt, computation là
  `unavailable_aggregate_scope`, không là kết luận đỗ/trượt.
- p45: đúng **14 dòng (*)** có môn hệ số 2 và quy về 30. Note không chỉ môn hay
  công thức. **40 dòng khác không được suy thang 30 từ dải điểm.** ScoreScale ID,
  formal basis/domain và applicability vẫn cần chứng cứ/quyết định. Không lấy
  named English/Mathematics formula September để backfill August, không chạy DSL.
- 39 dòng có nhiều dấu ngôn ngữ, 15 có một dấu. Ô trống không chứng minh không mở;
  đề xuất Offering full code/2024/KSA, track/language unresolved, không nhân facts
  hay khẳng định mọi biến thể dùng chung cutoff. Reviewer phải chọn representation.
- p5 mô tả profile người trúng tuyển, không là điều kiện IELTS bắt buộc; p41 nói
  PT1–5; p49–55 là KSV bổ sung. Không chuyển thành điều kiện KSA. Không dùng
  `GENERAL`, `MAIN`, `conditions={}`, `confirmed_none`, guessed rule/scale IDs.

Round proposal mô tả context `UEH/2024/PT6/KSA/thông báo 2024-08-17`; canonical
`round_key` và ordinal còn null. August không tự thành Round 1 và September không
thành correction/revision vì khác điểm.

## Authority và quyền sử dụng là hai quyết định riêng

KSA-04 chứa 54 `publication_bindings` đề xuất, mỗi binding đúng năm 2024,
campus KSA, full offering code và snapshot trên; method_code/university_id chưa
được chọn nên đây **không phải command thực thi**. Authority scale evidence
KSA-07 chỉ note 14 codes và fact kind `scoring_rule`, riêng với `cutoff`; validator
scale đòi đúng fact kind, kể cả không có executable rule.

Source vẫn unverified, không có UEH prior approval. Official publisher attribution
và technical robots history không là license. Cached footer “All Rights Reserved”
không cấp quyền. Năm gate độc lập: lưu raw nội bộ, biến đổi, thương mại, tái công
bố/trích nguồn, yêu cầu attribution. Cần permission phù hợp từ chủ thể quyền hoặc
đánh giá pháp lý có thẩm quyền; owner không cấp quyền thay UEH.

Đã inventory 3 UEH cached snapshots và links. Không có precise KSA PT6 2024
supporting-rule URL đủ căn cứ để fetch; profile/nhập học/current pages không thay
quy định basis/eligibility. **HTTP 0/6**, không refresh robots hay tải attachment.

## Một draft thật; không giả lập đủ lệnh cho cả bảng

Dùng implementation controlled integration hiện hữu, tạo slice đề xuất đúng
54 bindings/110 pending keys cần cho University draft; không sửa 77-candidate
overlay. Giữ exact approved PTIT entities/aliases/current head. Version đề xuất
được suy từ content hash tranche/decision, không thay DEV head hoặc remap parents.

`command-drafts/university-unapproved.json` đề xuất:
`university_code=UEH`, tên `Đại học Kinh tế Thành phố Hồ Chí Minh`, normalized name
theo helper hiện hữu, `slug=ueh`. Không có collision code/slug trong DEV.
Operation `proposal:ueh` bind đủ 54 packets thật, evidence p31, actual expected
registry/alias heads. **Read-only plan hợp lệ; `preview_only=true`, `can_apply=false`.**
Request ID content-derived và planned entity ID là preview, không UUID canonical
đã tồn tại. Không apply. Nếu sau này được ủy quyền riêng dưới đúng environment:
University verified +1, catalog version +1, audit +2, jobs +3
(registry/review/refresh), 109 UEH proposals khác vẫn pending; không thêm cutoff
hay release. Vì University có thể hiện trong catalog, không coi bootstrap này là
thay đổi metadata vô hình.

Không tạo draft Method (thiếu canonical code), Program (chưa chọn identity),
Offering (chưa duyệt parents/track/language), authority (thiếu IDs/quyền), Scale
(thiếu formal basis/authority) hoặc fact (thiếu canonical parents, scale/basis,
round/population/conditions/combination review/fresh T07/T08). `CutoffSpec` không
cho bỏ các field này bằng `unavailable_rule`. Multi-key Program merge còn vướng
no-duplicate canonical IDs/frozen parent binding và không có Program alias
governance; task không xây alias engine để né quyết định identity.

Các artifacts owner cần đối chiếu:

| Artifact | SHA-256 bytes |
|---|---|
| Owner decision sheet | `0fac86f4497b4af22c05fdd3be64fa0f548fe63f20c9beb26c7e2820b576fbe2` |
| University draft | `d9497524be6f361aa68fa9fe9a25f3fc10269de522d2438e53d12547a85b70e5` |

Hash từng quyết định riêng trong owner sheet/shared/candidate indexes. Nội dung
đầy đủ giữ riêng tại `state/review/ueh-2024-ksa-pt6-signoff/`, gồm tất cả files yêu
cầu, source inventory, parent manifests, replay/verification manifest và scripts
read-only. Không commit raw bodies, full packets hoặc private operational details.

## Kiểm chứng và bảo toàn

Full-table verifier: 54 packets, 54 unique raw/Decimal matches, 73 decision
artifacts và 972 field records, exact affected sets/locators/hashes. Sáu negative
probes từ chối tampered decision hash/set/binding, packet hash, stale registry và
alias head. Repeat checked_packets/plan giống exact output, zero inserts.

Focused regression chạy publication integration/review và ba UEH normalization
modules: 85 passed, 2 setup errors do Windows temp permission; chạy lại đúng hai
tests bằng fresh workspace temp/cache: **2 passed**. Lần chọn temp đầu thiếu parent
đã sửa bằng path trực tiếp trong `state/`, không sửa tests/validators. Tổng 87 tests
được thực thi thành công. PostgreSQL test DB riêng được giữ lại. Ruff check/format
(183 files), mypy (76 source files), frozen offline lock (87 packages), Alembic
check đều pass. Không thay production code nên không thêm tests song song logic.
Full backend/web workflow chạy trên exact pushed SHA; kết quả cuối và run URL
được lưu private `git-ci-verification.json` và báo ở bàn giao cuối, không suy từ CI
baseline hoặc gọi trạng thái đang chạy là success.

| DEV | Trước | Sau |
|---|---:|---:|
| Current verified published cutoffs | 3 | 3 |
| Catalog version | 3 | 3 |
| Audit events | 47 | 47 |
| Sources / snapshots | 43 / 36 | 43 / 36 |
| Observations / ingest jobs | 1127 / 83 | 1127 / 83 |
| Dataset releases / version / facts | 1 / 3 / 3 | 1 / 3 / 3 |

34 table row digests và 663 historical files giữ nguyên, gồm PTIT IDs/evidence,
review commands, registry history, UEH frozen inputs/outputs/77 overlay, `.vscode/`
và untracked handoff. Release ID `396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest
SHA-256 `b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`
không đổi. Không có business approval, canonical write, catalog bump/audit mới.

Đo thực tế: chuẩn bị 37.85s, full read-only verification/replay 35.69s (không gồm
thời gian nghiên cứu/CI), 54 bindings/110 imported pending keys/1 draft; không đo
SQL count hoặc token usage nên ghi unavailable. Không tạo framework/alias/UI,
không thêm dependency/migration hoặc chạy 50k benchmark.

Bước owner: trả lời theo decision ID + exact artifact hash và phương án đã chọn,
đồng thời cung cấp chứng cứ quyền/basis/conditions còn thiếu; đây chưa là apply
authorization. Bước kỹ thuật sau quyết định phù hợp: task riêng tạo lại commands
theo current heads, kiểm exact reviewed bytes, duyệt tác động catalog và xin scope
apply riêng. Sau approved parents/authority/scale/scope mới fresh T07/T08, review
fact và publication riêng; không đóng T08/T09/T11/Phase 1 từ dossier này.
