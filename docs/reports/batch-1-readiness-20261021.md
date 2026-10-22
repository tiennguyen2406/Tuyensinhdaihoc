# Batch 1: mức sẵn sàng và quyết định còn thiếu — 21/10/2026

**Chưa có subset OU/HCMUE/UEH nào sẵn sàng publication.** Hồ sơ đủ để review
metadata/ô vật lý; authority, quyền sử dụng, canonical identity, scale/basis và
admission scope vẫn thiếu quyết định hoặc evidence. Báo cáo này không là approval,
không thay hồ sơ PTIT đã được duyệt và không cấp quyền thực thi pipeline.

Baseline được giao: nhánh `codex/crawler-pilot`, commit
`5e25c0e4568a1b472fce2920f1d2959e324abc48`. Kiểm tra trong lượt này hoàn toàn offline,
chỉ đọc artifacts có sẵn; **không kết nối DEV, HTTP, OCR, normalize, chạy/replay
persisted jobs, bootstrap, approve/apply, build/release, commit hoặc push**.

## Chứng cứ đã đối chiếu và giới hạn

Private root được ký hiệu `HCM_PRIVATE`: thư mục `deliverables/hcm-20261021/`
của project trên máy. `STATE` là `state/` của checkout operational. Hai vị trí là
local private; báo cáo và JSON kèm theo chỉ chứa IDs, hashes, locators, metadata
ngữ cảnh và trạng thái, không chứa raw bodies, điểm nguồn, source rows, full
packets, credentials hoặc dumps.

- Tính SHA-256 trực tiếp **15/15 artifacts** trong `HCM_PRIVATE/handoff-manifest.json`:
  tất cả khớp. Gồm 7 tệp ledger/coverage/preservation/validation/corroboration/counts
  và 8 tệp `pipeline/<snapshot>/review-packets.json`.
- Tính lại digest JSON của **731/731 packets** bằng quy ước
  `normalization.store.digest`, bỏ duy nhất `packet_sha256`: tất cả khớp. Đây là
  kiểm integrity của bản packet local, không là lần `checked_packets` mới với DEV.
- Chọn **8 ví dụ thật: OU 3, HCMUE 2, UEH 3**. Đọc ba raw HTML local đúng
  snapshot, tính lại SHA/byte size, resolve exact CSS cell locator bằng cùng
  BeautifulSoup `html.parser`: **8/8 cells duy nhất, raw text khớp lineage;
  8/8 packet hashes khớp**. Không chạy adapter hoặc tính lại normalization.
- Bản intake frozen cho 731 candidates dùng checkout `5243461`, parser/normalizer
  1.0.0 và resolver 1.0.9. Corrective preview 1.0.1/1.0.1/1.0.10 đã được ghi nhận
  ở báo cáo trước, giữ 731 tuples; lượt này không thực thi lại preview/replay.
- Saved intake metadata giữ canonical **3/20.000**, còn **19.997**; riêng campus
  TP.HCM đã published **1**. Đây là mốc SQL đã lưu, **không phải truy vấn live của
  lượt readiness này**. Catalog 3/audit 47/release v3 cũng là mốc đã lưu.

Kết quả chi tiết và 15 expected/actual hashes nằm ở
[JSON metadata](batch-1-readiness-20261021.json). Các parent row digests trong đó
được giữ từ packet; lượt này không chứng minh lại membership/hash bằng DB live,
không chứng minh current head/authority chưa thay đổi sau mốc capture.

## So sánh subset nhỏ đã có HTML

| Subset | Mẫu kiểm thật | Evidence sẵn có | Dependencies còn thiếu đáng kể | Đánh giá cho batch 1 |
|---|---:|---|---|---|
| OU 2024, THPT, một notice | 3/44 candidates | Một năm/một method label; score/header/cell rõ, không OCR | Campus và training mode trong candidate null; University/Program/Offering/method pending; không source scale; authority/rights/scope | Đơn giản về layout, thêm blocker campus; không suy TP.HCM từ tên trường |
| HCMUE 2026, đợt 2, cơ sở chính | 2/6 candidates toàn notice; đúng 2 source-explicit HCM | Hai cells của cùng một source row/Offering-context; năm/campus/đợt rõ | Hai methods khác nhau; method kết hợp cần basis riêng; canonical identity, authority/rights/scale/scope đều pending | **Nếu tối thiểu dependencies tuyệt đối: chỉ HCMUE-1 THPT**; HCMUE-2 giữ làm đối chứng, không bắt buộc đưa vào batch |
| UEH KSA 2024, PT6, KSA-main, ba dòng không (*) | 3/54 tranche | Dossier 19 shared decisions + 54 identity decisions; campus/năm/method/training/source aggregate evidence đã lập | Ba Program/Offering identities chưa duyệt; 40 dòng không (*) không được suy scale 30; rights/authority/formal basis/population/conditions/round | Nếu cần batch **2–3 candidates**, ưu tiên ba ví dụ này cho review cùng ngữ cảnh; chuẩn bị sâu nhất, không có nghĩa ít canonical entities nhất |

Một candidate HCMUE-1 có một University, một method, một Program và một Offering
cần xử lý; cùng ba lớp scope/scale/authority dùng chung. Không thêm method kết hợp,
không nhập Long An/Gia Lai, không mở 2024–2025. Đề xuất này chỉ chọn **đơn vị review
nhỏ nhất**, chưa thể lập fact command hợp lệ hoặc bảo đảm có đủ evidence ngoài.

Nếu owner chọn batch 2–3 dòng UEH, tái dùng dossier hiện hữu và giữ đúng ba dòng
đã chọn; không kéo ISB/KSV/September/PT3–5 vào scope. Các dòng không (*) tránh suy
môn nhân hệ số nhưng **không giải quyết** lỗ hổng formal scale/basis. Không tạo
Program mới chỉ vì khác điểm/năm/round, không merge code/name giữa campuses.

UEH 2025 giữ một candidate aggregate PT2,3,4,5 cho mỗi ô, không nhân bốn; UEH 2026
PT2 tích hợp không thành THPT/30. Hai nhóm này có thêm method/basis decisions, không
được ưu tiên chỉ vì có nhiều candidates mới. PTIT 2025 method-null và ảnh chưa có
trusted transcription cũng không thay thế subset HTML rõ ngữ cảnh.

## Binding và locator cho từng ví dụ

`rN/cN` dưới đây là suffix `tr:nth-of-type(N) > td:nth-of-type(N)` của exact
physical locator; **full original locator, resolution ID và full hashes** có trong
JSON metadata, không dùng suffix đơn lẻ để vận hành. Candidate/packet hash trong
bảng được rút gọn 12 ký tự chỉ để đọc; JSON giữ đủ 64 ký tự.

| Ví dụ | Snapshot | Physical cell | Candidate key → packet SHA (prefix) | Năm/campus/method theo source metadata |
|---|---|---|---|---|
| OU-1 | `67618851-c8c6-48ae-8ddf-759159a698cc` | table 1, r2/c3 | `f65f35582c31` → `1b9edf486899` | 2024 / unknown / THPT, namespace `ou:2024` |
| OU-2 | cùng snapshot OU | table 1, r3/c3 | `3e47fd7c4af1` → `b8d982c5b6a3` | 2024 / unknown / THPT |
| OU-3 | cùng snapshot OU | table 1, r4/c3 | `c902da0ee3a3` → `f0efdceddd1a` | 2024 / unknown / THPT |
| HCMUE-1 | `74ea2ce3-eecf-4a45-9cac-53b7d4fdea49` | nested business table 1, r2/c4 | `2782d6771643` → `01ec56ad2395` | 2026 / cơ sở chính / THPT, namespace `hcmue:2026`; source đợt 2 |
| HCMUE-2 | cùng snapshot HCMUE | cùng physical row, r2/c5 | `104275288848` → `17610a5743f3` | 2026 / cơ sở chính / học tập THPT kết hợp ĐGNLCB; source đợt 2 |
| UEH-1 | `67f11fe2-3a23-4d3a-8d67-fb468f66ec54` | KSA-main table 2, r2/c9 | `a3a55e4eb924` → `54abdbea5199` | 2024 / KSA / PT6, chính quy; dossier P02 |
| UEH-2 | cùng snapshot UEH | table 2, r3/c9 | `f23521fb6fad` → `514d252f91fa` | 2024 / KSA / PT6, chính quy; dossier P03 |
| UEH-3 | cùng snapshot UEH | table 2, r4/c9 | `58f255adc0ef` → `6e9da3c3879e` | 2024 / KSA / PT6, chính quy; dossier P04 |

| Snapshot | Raw SHA-256 | Bytes |
|---|---|---:|
| OU | `ea9cbad021c0d7452fe4d9165231991e6c3d601e76c5cb8494a0d3b988ed6a6d` | 106733 |
| HCMUE | `9f243d01dd9f7018f3174f77af5ed759c4d939b3c9fcd21da57ddb59f24db9fd` | 16029 |
| UEH | `09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207` | 284975 |

## Quyết định field chính xác: passed evidence khác approved

Ký hiệu **E**: evidence vật lý/context đã kiểm offline; **R**: cần reviewer chọn
đúng mapping; **X**: thiếu evidence hoặc căn cứ quyền/formal basis; **N**: không bắt
buộc để publish cutoff. Không ký hiệu nào trong bảng là review.status=approved.

| Candidate/packet | Năm/campus/method | University–Program–Offering identity | Major | Scale/basis | Admission scope | Authority và quyền | Publication |
|---|---|---|---|---|---|---|---|
| OU-1 | E2024; Xcampus; Rmethod THPT | R: cả ba canonical IDs null | N: unresolved/null | X: score_scale/basis null, source max null | X: round/population/conditions/combinations/priority null | Rauthority; Xrights | blocked |
| OU-2 | E2024; Xcampus; Rmethod THPT | R: từng Program/Offering riêng cần chốt, không dùng tên/code làm Major | N: null | X như OU-1 | X như OU-1 | Rauthority; Xrights | blocked |
| OU-3 | E2024; Xcampus; Rmethod THPT | R: canonical IDs null; không suy track/language | N: null | X như OU-1 | X như OU-1 | Rauthority; Xrights | blocked |
| HCMUE-1 | E2026/cơ sở chính/source đợt 2; Rcanonical method | R: University/Program/Offering null; campus evidence không tự là canonical campus binding | N: null | X: score_scale/basis/source max null | Rround theo đợt 2; Xpopulation/conditions/combinations/priority | Rauthority; Xrights | blocked |
| HCMUE-2 | E2026/campus; Rmethod kết hợp riêng | R: cùng source Offering-context với HCMUE-1, chưa approved mapping | N: null | X: basis kết hợp, không dùng scale THPT thay | Rround; X các scope fields còn lại | Rauthority; Xrights | blocked |
| UEH-1/P02 | E2024/KSA/PT6/chính quy; Rcanonical method | R: P02 và KSA-02/03/12/13; UUID null | N: null | Xbasis KSA-06/Rauthority KSA-07; dòng không (*) không có evidence tự khẳng định max30 | Raggregate KSA-08/round KSA-10; Xpopulation/conditions KSA-11 | R KSA-04; X KSA-14–18 | blocked |
| UEH-2/P03 | E như UEH-1 | R: P03; không suy cùng Program từ tên/code gần nhau | N: null | X như UEH-1 | R/X như UEH-1 | R/X như UEH-1 | blocked |
| UEH-3/P04 | E như UEH-1 | R: P04; track/language representation KSA-12 còn mở | N: null | X/R như UEH-1 | R/X như UEH-1 | R/X như UEH-1 | blocked |

Các tám packets thực đều `unverified`, sáu entity kinds `unresolved`, không có
canonical IDs được chọn, `publication_eligible=false`. `basis`, `round`, `priority`,
`conditions`, `population`, `score_scale`, `combinations`, `scoring_rule` đều null
trong T07 unresolved fields. Tách source đợt 2 khỏi canonical round: không điền
round chỉ để làm validator xanh. Major null được contract cho phép; không lấy mã
xét tuyển thành taxonomy. Thiếu executable rule không tự chặn một fact đã đủ các
gate khác, nhưng không chữa được thiếu scale/basis/scope.

Source IDs: OU `e57f4e58-5df4-4979-be86-38bde98baa7d`, HCMUE
`df4a4683-a8c1-474c-8a2f-12f2c1ce93b7` và UEH
`81eefdb2-c1fb-4880-a109-973c41a836d6`; xem JSON để đối chiếu exact identity thay vì
dựa tên host. Bản saved source của cả ba vẫn `unverified`. OU/HCMUE có cấu hình
years2024–2026/fact kinds cutoff,catalog; UEH years2024/cutoff. Những JSON scope
metadata này chưa có approved mapping/bindings, không phải grant authority.

Evidence first-party attribution/host và robots/capture history giúp review nguồn,
không cấp quyền lưu/biến đổi/thương mại/tái công bố/attribution. Riêng UEH dossier
đã tách đúng năm quyết định quyền KSA-14–18, footer có reservation về bản quyền;
không tìm thấy grant trong evidence đã đọc. OU/HCMUE chưa có rights grant được
intake chứng minh. Đây là **thiếu evidence trong hồ sơ**, không phải kết luận pháp
lý về mọi quyền có thể tồn tại. Authority cutoff và authority scale evidence
(`scoring_rule` theo validator) cần review riêng, đúng year/campus/method/code/snapshot.

## PTIT: bảo toàn approvals đã có

A2/B1/B2/B3/C1, C2 và từng D1–D3 đã được duyệt riêng đúng file/hash/request; các
đoạn pending cũ trong báo cáo là lịch sử. Tên `decision-d*.draft.json` không làm
mất hiệu lực approval. Đã đọc private human approval record và publication results,
tính lại đúng ba file SHA của D1/D2/D3:

| Quyết định | File SHA-256 đã đối chiếu | Cutoff đã published theo hồ sơ |
|---|---|---|
| D1 | `09da357722b73968371904b8b5e37b54e467ead9fedef6b61f79380513361ac9` | `1076f528-0bab-4ac6-8840-714c6cfd77b6` |
| D2 | `7b96d14a30dabcb6c7b33e8d0b771797616b110d205b60e575e70151460cd51e` | `a5ced261-5a4d-4c20-91f6-bb28a646e8a2` |
| D3 | `8c72b5095b32abe2d941831ea9f7d1b51d318b5764e163a955abd173b0161ddc` | `4fd7c322-cd05-4102-a6c4-956d3313258e` |

Không xin lại, sửa bytes/reason, revoke, chạy apply/replay hoặc mở rộng các approvals.
PTIT2024 không cấp authority/basis/identity cho OU/HCMUE/UEH hay PTIT2025/2026.
HTML main-host PTIT2025 đã được intake sau recovery capture: 28 BVH scoped matches,
140 raw fields, 13 BVS chưa có counterpart; vẫn cần independent corroboration
signoff và method applicability. Báo cáo “blocked before acquisition” là mốc cũ,
không dùng nó phủ nhận snapshot mới. Giữ 41 historical candidates/method=None;
không dùng 28 matches để tạo thêm 28 facts hoặc fan-out chín methods.

## Roster và denominator TP.HCM

Không chứng minh được roster **hơn 50 legal institutions** từ bộ evidence này.
Bài danh sách kiểm định do owner đưa bị JavaScript/CAPTCHA, chưa kiểm nội dung,
membership, thời điểm hay tính đầy đủ; tiêu đề kiểm định không là danh sách mọi
trường. **Denominator legal institutions/campuses cần thu vẫn unknown**, nên
không báo phần trăm trường đã phủ hoặc tuyên bố đã thu đủ TP.HCM.

| Entry được inventory/intake hỗ trợ | Loại cần giữ riêng | Trạng thái evidence trong scope readiness |
|---|---|---|
| OU | Một institutional owner candidate; campus unknown trong 292 cutoff candidates | Pending identity/địa điểm; không suy cơ sở từ tên |
| HCMUE | Một institutional owner candidate; cơ sở chính và các phân hiệu riêng | Chỉ 36 candidates source-explicit HCM qua ba năm; ngoài TP.HCM và cao đẳng không vào coverage đại học HCM |
| UEH | Một institutional owner candidate; KSA/KSV là campus context | KSA/KSV không là hai pháp nhân/trường; khác năm/method không tạo thêm trường |
| HCMUS | Một institutional owner lead | 3 HTML/6 ảnh; 0 typed trong intake này, chưa numerical coverage |
| PTIT | Một canonical University đã duyệt; BVH/BVS là campus labels | 1 BVS published thuộc HCM; 2 BVH ngoài HCM; không đếm PTIT thành hai trường |
| UIT | Một institutional owner lead | Preflight TLS failed; không có snapshot nội dung mới |
| NLU | Một institutional owner lead | Robots trả HTML/needs_review; chưa lấy seed nội dung |

Bảy entries trên là danh sách ưu tiên kỹ thuật có evidence trong dự án, **không
là xác nhận pháp lý đầy đủ bảy pháp nhân hoặc một roster chính thức**. Không thêm
entry thứ 8–51 từ trí nhớ. Trước khi mở coverage phải có roster có hiệu lực theo
mốc địa giới/năm, stable institution identity, campus-parent links và trạng thái
supported/pending/excluded; tách cơ sở ngoài HCM và hệ cao đẳng.

## Bước chuẩn bị nhỏ nhất tiếp theo

1. Chốt một đơn vị review: HCMUE-1 nếu giảm số parents/methods tối đa; hoặc ba
   UEH P02–P04 nếu owner cần cohort 2–3 cùng notice và tận dụng dossier sâu sẵn có.
2. Bổ sung/chốt rights evidence, authority exact source context; không dùng robots
   hoặc quyền tải nội bộ thay các quyết định này.
3. Chốt University/method/code-system rồi persistent Program và Offering đúng
   year/campus/track/language. Giữ Major null khi thiếu taxonomy.
4. Bổ sung formal scale/domain/basis cùng applicable conditions/population/round/
   combination status. Aggregate evidence giữ một fact; không fan-out hoặc suy
   `MAIN`, `GENERAL`, `conditions={}`/`confirmed_none`.
5. Chỉ trong nhiệm vụ thực thi được cho phép riêng sau đó: kiểm current heads,
   exact hashes/parents, materialize review commands đúng refs; theo workflow hiện
   có cho registry/T07/T08/fact review/publisher. Báo cáo này không chạy bước đó.

Không cần dependency mới, migration, alias engine, crawler/OCR hoặc adapter cho
lượt chuẩn bị này. Dùng lại dossier/packet bindings và checklist field; không
điền giả dữ liệu để tạo executable command. Batch mới chưa có approved fact;
quota/canonical coverage không tăng theo số examples hay số packet hashes pass.

## Tài liệu và artifacts đã đọc

- [Intake TP.HCM đầy đủ](hcm-2024-2026-intake-20261021.md),
  [source review](../source-review.md), [review workflow](../review-workflow.md).
- Contracts [data](../data-contract.md), [parser](../parser-contract.md),
  [normalization](../normalization-contract.md), [entity resolution](../entity-resolution-contract.md),
  [publication](../publication-contract.md), [catalog](../catalog-contract.md),
  [release](../release-contract.md), cùng hàm digest/packet binding trong implementation.
- UEH [business readiness](ueh-2024-business-decision-readiness.md),
  [controlled integration](t08-ueh-controlled-batch-bootstrap.md),
  [KSA PT6 signoff](t08-ueh-ksa-2024-pt6-signoff.md),
  [PT6 full batch](t09-ueh-2024-pt6-full-batch.md),
  [PT345 full batch](t09-ueh-2024-pt345-full-batch.md).
- PTIT [blocker decisions và các cập nhật approval](ptit-blocker-decisions.md),
  [publication pilot](ptit-publication-pilot.md),
  [2025 corroboration baseline](t08-ptit-2025-official-html-corroboration.md),
  [2025 image intake](t09-ptit-2025-image-multimethod.md),
  [2026 multimethod](t09-ptit-2026-multimethod-full-batch.md).
- Private HCM: handoff-manifest, typed ledger, coverage, pipeline summary,
  preservation, raw/corrective validation, 8 review-packet files, saved sources/
  snapshots metadata; ba selected raw HTML chỉ đọc local. UEH STATE: tranche,
  selected-records, candidate decisions, parent manifests/hashes, command readiness,
  validation/source-support review. PTIT STATE: exact D files, approval record và
  ba saved publication results. Không đọc credential files.

Kiểm tra lượt này là checksum/metadata/DOM, không full backend tests, CI hoặc
business review mới. Chỉ hai files readiness cùng prefix được tạo; không sửa code,
source profiles, frozen operational artifacts, `.vscode/settings.json` hoặc handoff.
