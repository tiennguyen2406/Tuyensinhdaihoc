# T09 — UEH August 2024: toàn bộ PT3/PT4/PT5

Baseline local và remote: `a60e5cb7ce27d614d408d973fd069fa8b3839bec`, branch
`codex/crawler-pilot`. Handoff untracked cũ và `.vscode/` giữ nguyên. Task chỉ intake
kỹ thuật offline: **0 HTTP nguồn, 0 approval/bootstrap, 0 canonical publication,
0 scoring execution, 0 release mới**.

## Nguồn và đối soát 100% ô vật lý

Official URL:
<https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/>.

RawStorage snapshot `67f11fe2-3a23-4d3a-8d67-fb468f66ec54`, **284975 bytes**,
SHA-256 `09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207`;
source `81eefdb2-c1fb-4880-a109-973c41a836d6`, publication date 17/08/2024.
Không fetch/refresh robots hoặc tạo crawl run. Profile mới chỉ dispatch parser offline,
verified=false; không cấp authority/rights hoặc mở rộng eligibility của host.

Inventory lập từ bytes trước khi mở rộng adapter, rồi kiểm lại từng ô sau persistence.
Article root duy nhất `.elementor-widget-theme-post-content > .elementor-widget-container`.
Toàn DOM có4tables/100physical rows: bảng báo chí20; KSA-main57; ISB5; KSV18.
Ba bảng cutoff có6header rows,71program rows và3total rows. Cả23non-cutoff rows
đều có locator/reason riêng, không tăng denominator ô cutoff.

| Bảng | Program rows | PT3 cột4 | PT4 cột5 | PT5 cột6 | Numeric cells |
|---|---:|---:|---:|---:|---:|
| KSA-main | 54 | 54 | 54 | 54 | 162 |
| KSA ISB/ASEAN Co-op | 2 | 2 | 2 | Không có cột | 4 |
| KSV | 15 | 15 | 15 | 15 | 45 |
| Tổng | 71 | 71 | 71 | 69 | **211** |

Cột tính từ0; runtime kiểm đầy đủ hierarchy và physical origins, không chỉ vị trí.
**211 source cells = 211 typed mới + 0 existing + 0 blocked + 0 non-cutoff values**.
Hai ISB/PT5 là `method_not_offered`, nằm ngoài211. Không có blank/invalid/span score
ở snapshot thật; fixtures vẫn kiểm fail-closed các trường hợp này.

## Mở rộng nhỏ, giữ namespace cũ

- `parsers/ueh_pt345.py` dùng lại `ueh_batch.parse_batch`, physical grid/headers,
  source/date/campus/section guards và locators. Một wrapper cho ba methods; không
  sao chép parser theo phương thức, không sửa file PT6 cũ. Kiểm original score cell,
  unspanned origin cùng row/cột, exact method definition và full code/name.
- `normalization/ueh_pt345.py` tạo tối đa3candidates/physical row, ISB2; Decimal/raw
  riêng từng method. Scope giữ explicit2024/KSA-KSV/chính quy/code/name/method và
  early context. Không lấy PT6 combinations hoặc footnotes làm evidence cho PT345.
- Parser registry/normalizer dispatch và profile offline mới; resolver version tăng
  vì implementation digest bao gồm normalization files, không đổi matching algorithm.
  Không dependency, migration, crawler, validator publication hay frontend feature mới.

Namespaces: `html-ueh-2024-pt345/1.0.0+full-1`,
`normalizer/ueh-2024-pt345/1.0.0`, `resolver/1.0.5`.
Frozen registry pending `registry/ueh-pt345/20261020-r1`; alias giữ
`aliases/ueh-2024-ksv/20261019-r1`. Old manifests/output/signatures không rewrite.

## Method, thang điểm và context lịch sử

August p34/p35/p36 xác định lần lượt PT3 học sinh Giỏi; PT4 quá trình học tập theo tổ
hợp môn; PT5 ĐGNL **ĐHQG TP.HCM đợt1 năm2024**. P31 xác nhận2024/chính quy.
P41 nói PT2–PT5 đã công bố danh sách đủ điều kiện ngày **20/6/2024**; 09/7 áp dụng
PT1. Giữ August17 là document carrier; không tự tạo round mới/Round1/MAIN hoặc
correction theo thời gian snapshot. Chưa có typed UEH PT345 trước task: kiểm đủ
77historical UEH candidates theo source owner/schema; tất cảPT6.

Cached February supporting source được tham khảo riêng: snapshot
`b3d25076-9c5d-4796-9de0-2306a6100081`, SHA-256
`caba8f7a8b8fd9b308ef3c9b524eb7af8ef93b6455119bab3b909f7ee09ad668`, tables6/7/8.
Exact locators/raw text nằm trong private `method-scale-evidence.json`; không đưa
historical2023 score columns vào pipeline và không ghi đè August numeric values.

| Method | Source basis để review | Khoảng quan sát, không phải approved scale |
|---|---|---|
| PT3 | Điểm quy đổi từ học lực bắt buộc và các tiêu chí bổ sung; không phải tổng3môn học bạ | 48–83 |
| PT4 | Điểm quy đổi từ quá trình học tập theo tổ hợp và tiêu chí bổ sung; không tự là học bạ/30 | 40–85 |
| PT5 | Tổng điểm kỳ thi ĐGNL ĐHQG TP.HCM đợt1/2024; giữ organizer/year | 550–995 |

Không quy đổi thang30, không link HSA/TSA/V-ACT tự động, không tạo scale/basis/rule ID.
PT3/PT4 giữ điều kiện phương thức ở supporting evidence; chưa convert prose thành
canonical eligibility/conditions hoặc scoring rule. Header combinations củaPT6 không
chứng minh applicability PT345; không fan-out theo combinations/language availability.
Markers trong source labels vẫn giữ nguyên, không gán weighted subject PT6 choPT345.

## Persistence, identity và T08

| Stage | Jobs | Envelopes/observations mới | Cutoff candidates |
|---|---:|---:|---:|
| T05 | 1 | 71 raw physical rows | Chưa là typed facts |
| T06 | 1 | 71 normalized envelopes | 211 |
| T07 | 1 | 71 resolution envelopes | 211, đều unresolved |
| T08 inspection | Không ghi job | 211 actual packets kiểm binding/hash/parents | 211 conditional,0eligible |

Jobs T05 `2cc22711-c4cc-4050-b9ae-554090f5faca`,
T06 `6352caf8-4466-45e2-9561-37e71d6b0d10`,
T07 `147605f4-cf2d-4fd3-936e-256e1f7dbf02`.
Chỉ213technical observation rows/3jobs, không phải213logical cutoffs.

Pending seed dùng lại exact74Program/74Offering entries của PT6; 211candidates link
71Program/71Offering review families cùng program-year-campus row. Chỉ thêm3Method
pending; tổng1University/4Method/74Program/74Offering, không canonical UUID. Approved
global PTIT registry/alias head không đổi; không dùng overlay77 làm approved registry.
Tám full code families cùng KSA/KSV vẫn là identity alternatives, không auto merge.
KSA7340201_01=Tài chính công, _02=Thuế, _03=Ngân hàng; KSV lần lượt Ngân hàng,
Tài chính, Thuế. `ISB_CNTN`/`ASA_Co-op` và suffix giữ nguyên; không suy Major taxonomy.

T08 dùng existing inspect/binding/checked_packets; kiểm211packet source/hash/parent,
exact raw/Decimal/name/code/method/campus/year và mọi context/header locator. Dựng lại
77oldPT6packets (71August+6September), exactobjects/hash bằng frozen originals. Không
re-ingest PT6, không merge September. Authority/rights, identities/method, scale/basis,
round/population/conditions và combination/track/language applicability vẫn review gates.
Không sinh giả ReviewCommand/CutoffSpec; không gọi apply/publisher/bootstrap/release.

## DEV và immutable history

| Chỉ tiêu | Trước | Sau |
|---|---:|---:|
| Current verified published cutoffs / catalog version | 3 / 3 | 3 / 3 |
| Audit events | 47 | 47 |
| Sources / snapshots | 45 / 38 | 45 / 38 |
| Observations / ingest jobs | 1127 / 85 | 1340 / 88 |
| Releases / v3 exported facts | 1 / 3 | 1 / 3 |

Toàn bộ old rows của34tables và833historical files giữ digest; bao gồm PTIT canonical
IDs/evidence/approvals, raw inputs, UEH frozen packets/overlays/signoff và supporting
snapshots. `.vscode/`/handoff giữ nguyên. ReleaseID
`396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
Replay: T05 cached cùngjobID; T06/T07 inserted0; mọi34table digests trước/sau replay
bằng nhau. Các historical jobs không replay dưới implementation hash mới.

## Kiểm chứng, hiệu suất và bàn giao

Focused TDD kiểm3layouts, header/method/year/campus/earlycontext, độc lập Decimal,
blank/invalid/span và origin rebinding, không PT6 leak/fan-out, PT6 regression,
PostgreSQL persistence/identity reuse/T08/replay/business preservation. Fixture synthetic
được ghi nhãn; full live211/211 raw cells được kiểm riêng. Một lỗi fullsuite lần đầu
do test mới select observations quá rộng đã sửa bằng snapshot-scoped query và assertion
sáu inputs; không đổi production output hoặc giảm validator/assertions.

Focused regression50pass; riêng16tests mới pass. Full backend **701pass** trong321.66s,
một Starlette deprecation warning hiện hữu. Ruff check/format188files, mypy78sources,
frozen lock87packages, Alembic current/check đạt. Frontend lint/format/typecheck,
18unit tests và production build đạt với cached dependencies qua npm.cmd; pnpm không
có trên PATH local, nên frozen frontend install và Playwright E2E kiểm qua workflow
CI chuẩn. Không thay execution policy hoặc global tooling. Exact-SHA GitHub CI được
ghi tại private verification checkpoint và final handoff sau push; không suy pass từ
queued/running. Không benchmark50k hoặc sửa CI.

Thời gian stage đo thực tế: T05 2.777s, T06 3.500s, T07 4.873s; T08 inspection + bulk
binding check62.028s, full-source check30.440s. Engineering wall time đến metrics
1390.671s, gồm inspection/implementation/checks, không phải thuần pipeline. HTTP **0/0**;
token consumption không quan sát được. Dùng một batch mỗi stage, một physical grid
chung; không chạy CLI riêng từng Program/method/cutoff.

Private output `state/intake/ueh-2024-pt345-full-batch/` có đủ inventory, ledgerCSV,
typedCSV/JSON, blockedCSV, scale evidence, identity reuse, T08 bindings, full validation,
replay, before-after và metrics; thêm source-DOM/duplicate-check/verification evidence.
Reviewer bắt đầu tại `review-index.md`, không phải đọc211JSON packets thủ công.

Bước giá trị cao kế tiếp: field-level review ba method/basis và early-admission scope
dựa cached evidence; chỉ thu thêm tài liệu chính thức còn thiếu trong task được cấp
budget riêng. Chưa đóng T08/T09/T11/Phase1; canonical vẫn3/20.000, không cộng211
unverified candidates vào verified published progress.
