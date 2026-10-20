# T09 — Toàn bộ bảng PT6 UEH August 2024

Baseline local và remote đối chiếu: `52ca366316ee9827ab50421032dda29b75818ecd`,
branch `codex/crawler-pilot`. Handoff untracked cũ mô tả `3accf48`; các commit UEH/audit
sau đó đã có ở baseline mới, không reset hoặc sửa bàn giao. Task này chỉ batch intake
kỹ thuật từ snapshot sẵn có: **0 HTTP nguồn, 0 approval, 0 canonical publication**.

## Nguồn và đối soát toàn bộ DOM

Official URL:
<https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/>.

RawStorage kiểm **284975 bytes**, snapshot `67f11fe2-3a23-4d3a-8d67-fb468f66ec54`,
SHA-256 `09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207`.
Source ID `81eefdb2-c1fb-4880-a109-973c41a836d6`; date metadata 17/08/2024.
Không refresh robots/TLS/URL; profile mới chỉ offline parser, không xác lập host
eligibility, authority, quyền xử lý hoặc tái phân phối.

Business root duy nhất: `.elementor-widget-theme-post-content > .elementor-widget-container`.
Inventory được lập từ bytes trước khi viết adapter, sau đó đối chiếu đủ từng physical cell.
Indices cột dưới đây tính từ 0, gồm cả STT; mọi bảng cutoff có hai physical header rows.

| Bảng trực tiếp trong article | Physical rows | Program rows | Total rows | Cột combinations / PT6 | Existing / mới / blocked |
|---|---:|---:|---:|---|---|
| 1: báo chí dẫn tin | 20 | 0 | 0 | Không thuộc appendix | Loại 20 non-cutoff rows |
| 2: KSA chính | 57 | 54 | 1 | 7 / 8 | 0 / 54 / 0 |
| 3: KSA ISB/ASEAN Co-op | 5 | 2 | 1 | 6 / 7 | 0 / 2 / 0 |
| 4: KSV | 18 | 15 | 1 | 7 / 8 | 6 / 9 / 0 |

**71 relevant rows = 65 typed mới + 6 typed cũ + 0 blocked.** Tổng DOM100 rows;
6 header rows; ledger94 nonheader rows = 71 cutoff + 3 `TOTAL_ROW` +
20 `PRESS_LINKS_OUTSIDE_APPENDIX`. Không dùng totals/quota để tính cutoff denominator.

KSA PT3/PT4/PT5 cột4/5/6; ISB chỉ PT3/PT4 cột4/5. Các giá trị này không đi vào PT6.
Hai code ISB giữ nguyên `ISB_CNTN` (27.15), `ASA_Co-op` (25.30). Không ép code sang số
hoặc Major taxonomy. Các ô availability tiếng Anh/Việt chỉ là evidence, không tăng
số Offering/cutoff. Mỗi combination-list vẫn một published value, không fan-out.

## Implementation và namespace

- Một `parsers/ueh_batch.py` dùng lại `html.table_rows`, physical origin/span grid,
  locators và UEH evidence helper; ba cấu hình header/section dùng chung row loop.
- `normalization/ueh_batch.py` giữ Decimal, full code/name, campus riêng, context
  và raw score. Generic rules và hai adapters UEH cũ giữ nguyên.
- Dispatch thêm vào parser registry/normalizer; profile offline riêng
  `config/sources/ueh-2024-pt6-full-parser-20261020-v1.json`.
- Parser `html-ueh-2024-pt6-batch/1.0.0+full-1`, normalizer
  `normalizer/ueh-2024-pt6-batch/1.0.0`, resolver `resolver/1.0.4`.
  Resolver chỉ tăng version vì implementation digest chứa normalization module mới;
  thuật toán matching/proposal không đổi. Không sửa namespace/manifests lịch sử.

Guard kiểm unique article/date, explicit year/method/training/campus headings,
adjacent table và toàn header hierarchy. Group sai layout bị chặn riêng, vẫn giữ ledger;
score/code/name/combinations phải là original unspanned cells. Narrative nhắc KSV trước
appendix không được coi là campus boundary; regression đã bắt và sửa trường hợp này.

August có generic note `(*)`: factor2, quy thang30; không có named subject/formula.
Factor2 chỉ được ghi khi đúng note THPT2024/factor2/30. Note khác vẫn giữ nguyên với
factor unknown. Chỉ starred rows nhận applied footnote: KSA14/KSV3; ISB không thừa kế
note KSA-main hoặc KSV. Section note vẫn giữ làm context cho review. Không dùng named
English/Math formulas của September để bổ sung August, không kích hoạt computation.

## Persistence, dedup và hồ sơ review

Một job T05 tạo71 raw observations trong namespace mới. Sáu rows đã có từ August
được gắn `technical_reextraction`, không đi tiếp T06/T07. Selection dựa snapshot/hash,
physical score cell, full code, campus, year, PT6 và notice context; không dùng tên gần
giống hoặc cùng điểm. Logical hash chỉ phục vụ reconciliation, không canonical identity.

Một job T06 tạo65 typed envelopes; một job T07 tạo65 unresolved envelopes,0eligible.
T08 inspect71 August packets =65 mới +6 cũ; packet hash/lineage/locator được kiểm trực
tiếp với RawStorage và frozen jobs. Sáu packets cũ phải bằng exact original objects.
T05/T06/T07 rows mới là201observations,3jobs; không coi thành201cutoff candidates.

September snapshot `ce858dfc-707a-4e2d-ad3d-a5439807fa1c`, SHA-256
`51b52957dc76a054a804e93dfc3f13defca46ddbe119c6890bdb1d042c6f4b1d`, giữ nguyên
sáu candidates và context bổ sung; không parse lại, merge hoặc coi là correction.
Tổng UEH đã biết sau batch:71August +6September =77 logical candidates unverified.

T07 dùng seed UEH pending đã khóa, source owner/code-system `ueh:admission-code`.
Giữ nguyên approved PTIT head; pending UEH không tự thành canonical parent. Matching
token có campus/year/raw name: cùng code khác campus hoặc wording tạo review alternatives,
không chứng minh persistent Program khác nhau. Không tạo Program mới vì đổi cutoff/round.
Compiled registry có1University/1Method/74Program/74Offering pending: giữ9Program và
9Offering cũ, thêm65mỗi loại. Tám full codes xuất hiện ở cả KSA/KSV, vẫn giữ riêng
Offering/campus; đây là identity review groups, không duplicate cutoff facts.
Controlled registry integration và Program alias governance vẫn là blocker đã biết;
task này không dựng merge framework hoặc ép pending keys vào approved registry.

Private output: `state/intake/ueh-2024-pt6-full-batch/`:
`source-table-inventory.json`, `row-ledger.csv`, `typed-candidates.csv/json`,
`blocked-rows.csv`, `batch-validation.json`, `review-index.md`, `review-batch.json`,
`replay-verification.json`, `before-after.json`, `efficiency-metrics.json`.
Exact job/envelope IDs, bindings, packet hashes, code/name/combination/score/header/note
locators, registry/alias parents và row blockers nằm tại JSON, không đưa raw/private packet vào Git.

Mọi typed packet vẫn **conditional**, không business-approved hoặc publication eligible.
Shared decisions gom authority/rights, UEH/PT6 identity, campus/year, scale/basis,
August-round/population/conditions, source-aggregate và registry integration; row-specific
Program/Offering alternatives giữ riêng. Không sinh executable command khi thiếu IDs/fields.

## Bảo toàn DEV và replay

| Chỉ tiêu | Trước | Sau |
|---|---:|---:|
| Verified published cutoffs / catalog version | 3 / 3 | 3 / 3 |
| Audit events | 47 | 47 |
| Sources / snapshots | 43 / 36 | 43 / 36 |
| Observations / ingest jobs | 926 / 80 | 1127 / 83 |
| Releases / v3 exported cutoffs | 1 / 3 | 1 / 3 |

Toàn bộ existing rows của34tables và598historical files được đối chiếu digest,
không có host-state exception. PTIT University/Program/Offering/cutoff/evidence IDs,
approved decisions, registry/alias histories và hai UEH frozen inputs/outputs giữ nguyên.
Release ID `396ccd8b-1193-43dd-a08a-bb19e639dd56`; v3 manifest SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
Replay batch mới: cached T05, T06/T07 inserted0, mọi table digest không đổi. Không chạy
executable replay namespace cũ dưới implementation hash mới. Không tạo crawl run mới.

## Kiểm chứng và bước tiếp theo

Focused synthetic UEH tests:57pass, gồm17tests mới và40tests cũ nguyên. Tests cover
ba layouts, fail-closed context/header/span/blank, scope separation, PT6-only, weighted
note applicability, raw-only guard, PostgreSQL insert/replay/T08 và business preservation.
Synthetic fixtures ghi nhãn rõ; live evidence dùng full71/71 cells, không thay bằng fixture.
Full backend **672pass** trong324.44s, một Starlette deprecation warning có sẵn.
Ruff/check-format, mypy75sources, frozen lock87packages, Alembic current/check đạt.
Exact-SHA CI run được ghi tại private verification evidence và handoff.
Không thay CI, validator assertions, migration hoặc dependency lock; không benchmark50k.

Ba stage thực tế mất khoảng2.42s parser (gồm final dry-run),2.05s normalization,
2.81s resolution trên DEV; T08 inspection/validation và wall time ghi riêng trong metrics.
Token consumption không quan sát được; không ước lượng savings. HTTP nguồn **0/0**.

Bước tiếp theo: owner/reviewer xem grouped authority/rights và Program/Offering
alternatives theo code/campus, rồi quyết định scale/basis và admission scope bằng exact
evidence. Khi đủ phê duyệt mới xử lý controlled registry integration/export và fresh
T07/T08 bindings trong task riêng. Không tự dùng MAIN/GENERAL/conditions={}, không
đóng T09/T11/Phase1; canonical tiến độ vẫn3/20.000.
