# T09 — PTIT2026: toàn bảng, nhiều phương thức

Baseline local/remote `fdf5c8cfab5eb42230a724c5fe61be18223d624c`, branch
`codex/crawler-pilot`. Handoff untracked vẫn mô tả mốc3accf48; đối chiếu Git và DEV
thật, không reset hoặc sửa handoff/.vscode. Task chỉ technical intake và review
preparation, không approval/bootstrap/publication/scoring/release/deploy.

## Thu nguồn, cache và HTTP

Ba exact URLs đều chưa có immutable cache trước task. Dùng existing crawler,
URLPolicy/DNS/SSRF/TLS, shared host limiter0.5rps/concurrency1/burst1, RawStorage và
frontier depth0; không portal/login, browser, mirror, attachment hoặc broad discovery.
**4/6 requests**: robots và3HTML, tất cảHTTP200,0redirect,0retry. Mọi run mới paused;
budget độc lập các task cũ, không resume lịch sử hoặc chuyển2requests dư sang nguồn khác.

| Nguồn | Exact URL | Snapshot | Bytes |
|---|---|---|---:|
| Cutoff10/08/2026 | https://tuyensinh.ptit.edu.vn/thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2026/ | `a9759f37-854c-4958-a592-bdb10cd6b272` | 224570 |
| Conversion10/07/2026 | https://tuyensinh.ptit.edu.vn/thong-bao-bang-quy-doi-tuong-duong-giua-cac-phuong-thuc-xet-tuyen-dai-hoc-he-chinh-quy-nam-2026/ | `712a8cea-9093-460d-ae45-5d7d1d1d8590` | 112862 |
| Method03/04/2026 | https://tuyensinh.ptit.edu.vn/thong-baophuong-thuc-tuyen-sinh-dai-hoc-he-chinh-quy-nam-2026/ | `28f8196e-8730-4f25-be58-87009c2ab8d0` | 132541 |

SHA-256 lần lượt:

- Cutoff: `083f7dca450323a567f178c8e8f41a6028d3f1cc78015c82cab56461d4e25b24`.
- Conversion: `36c1ddcadb7270266940835dac5266db622589fb78c1592d395e10817a0659f9`.
- Method: `50dd1c8c43dee305390d948b332a2fa182ca974e95fa55833b308afee28fe96c`.

Robots122bytes, SHA-256 `e014272f6d2e2f068146055fc0ce99170f41a9e90c01f7d4c0a83cbe45482949`,
cho phép exact paths; snapshot cũ được tái sử dụng theo content hash. Optional April
notice được lấy vì các acronym trong cutoff/conversion chưa đủ organizer/eligibility.
Mọi publication date giữ date-only precision. HTTP/access allowance không là source
authority approval hoặc quyền xử lý/tái phân phối thương mại.

## Kiểm kê và reconciliation

Inventory từ actual bytes được lập trước adapter. Một `article.post-wrap` duy nhất,
hai bảng có3header rows mỗi bảng, multi-level score-family/instrument/scale paths.
Campus được xác lập bởi preceding OL riêng, không lấy từ footer hoặc năm2024.

| Campus | Physical rows | Program rows | Section headings | Numeric / dấu– |
|---|---:|---:|---:|---:|
| BVH | 51 | 44 | 4 | 356 / 40 |
| BVS | 25 | 19 | 3 | 163 / 8 |
| Tổng | 76 | 63 | 7 | **519 / 48** |

Sáu header rows và bảy section headings không là facts. Khu đại trà, chất lượng
cao/đặc thù, tài năng–tích hợp thạc sĩ/cử nhân, liên kết quốc tế giữ exact source
section, code và label. Không fan-out theo ngôn ngữ hoặc combinations.

| Cột/phương thức điểm | Nominal scale nguồn | BVH numeric | BVS numeric | Tổng |
|---|---:|---:|---:|---:|
| THPT2026 | 30 | 44 | 19 | 63 |
| Hồ sơ năng lực/tài năng | 100 | 39 | 18 | 57 |
| SAT | 1600 | 39 | 18 | 57 |
| ACT | 36 | 39 | 18 | 57 |
| TSA | 100 | 39 | 18 | 57 |
| HSA | 150 | 39 | 18 | 57 |
| V-ACT | 1200 | 39 | 18 | 57 |
| SPT | 30 | 39 | 18 | 57 |
| Kết hợp | 30 | 39 | 18 | 57 |

**567 physical method slots =519 typed logical mới +0 existing trước task +0 blocked
+48 not_a_cutoff_value.** `method_not_offered=0`: mọi hàng có đủ9physical score slots;
48dấu– trên6hàng tích hợp chỉ là not_reported, không chứng minh phương thức không
được cung cấp hoặc không có điều kiện. Không chuyển dash thành0/confirmed_none.
Con số519 được DOM xác nhận, không ép từ planning ceiling.

## Adapter và kiểm chứng

`parsers/ptit_2026.py` là một adapter cho hai campus/chín score columns, dùng lại
`html.table_rows`/physical origin/span/header utilities. Runtime kiểm exact source,
unique article/title/date, explicit2026cutoff publication, campus/section và đủ method
header paths. T05 một observation/physical program row; bonus/TTNV không là score.
`normalization/ptit_2026.py` giữ tối đa9candidates/row, raw+Decimal, exact code có suffix
và khoảng trắng, program section/track, method family/instrument, nominal-scale evidence,
context và tie-break. Không gán Major, scale ID, basis/rule, round/population/conditions.

Current parser `html-ptit-2026-multimethod/1.0.1+full-2`, normalizer
`normalizer/ptit-2026-multimethod/1.0.1`, resolver`resolver/1.0.7`; registry pending
`registry/ptit2026/20261020-r2`, approved alias version giữ nguyên. Resolver matching
algorithm không đổi; version tăng theo implementation digest. Không dependency,
migration, generic framework hoặc frontend feature mới.

Review độc lập phát hiện adapter bỏ lỗi resource-limit của grid helper: có thể trả
bảng BVH như complete khi BVS vượt cell budget. Regression RED xác nhận; fix propagate
issues, clear toàn observations khi global resource error và đánh dấu eligible ledger
thành blocked. Nguồn thật không chạm guard, cả hai lần đều đủ63rows/519values.

Lượt namespace1.0.0 đã persist trước phát hiện này được giữ bất biến cùng code archive
private `implementation-attempt1/`. Lượt cuối dùng namespace mới, giữ rõ519technical
re-extractions và đối soát snapshot/hash/cell/method/code/campus/year/context với lượt
đầu; **không cộng thành1038logical facts**, không correction/supersession. Mỗi lượt
T05/T06/T07 một job và63observations mỗi stage; cả task có6processing jobs/378technical
observations, cộng3raw-fetch jobs. Overhead thực được báo riêng, không che bằng count519.

Old namespace1.0.0 không được executable replay dưới current code/hash. Pure dispatcher
alias không phải compatibility guarantee; store từ chối stale implementation signature.
Replay lịch sử cần exact archived implementation. Batch bàn giao chỉ dùng1.0.1/r2 và
replay current namespace; mọi old PTIT/UEH manifests/rows/packets giữ nguyên.

## Semantics, basis và identity gates

SAT/ACT thuộc family chứng chỉ quốc tế, TSA/HSA/V-ACT/SPT thuộc family ĐGNL/ĐGTD nhưng
instrument khác nhau; không collapse thành generic canonical Method. April source nêu
organizers tương ứng ĐHBK Hà Nội/ĐHQG Hà Nội/ĐHQG TP.HCM/ĐHSP Hà Nội và năm2026.
Các ngưỡng SAT1130/ACT25/TSA50/HSA75/V-ACT600/SPT15 là eligibility supporting evidence,
không cutoff mới hoặc bảo đảm trúng tuyển. Không link UEH2024PT5 hay PTIT2024 rules.

July source xác định THPT2026 là phương thức gốc và mô tả khoảng phân vị; ba ảnh giữ
locator/src, không tải/OCR/transcribe coefficients hoặc thực thi formula. DecimalSAT/
ACT trong August giữ nguyên, không round thành discrete raw scores. Nominal scales
không xác nhận raw applicant-score comparability; canonical scale/basis/conversion,
rounding/priority/eligibility vẫn unresolved. Supporting39snippets nằm riêng, không
ghi đè physical August scores hoặc tạo thêm cutoff observations.

Tie-break giữ raw bonus/TTNV, đúng operators=,<=,≤ và missing/dash; note ưu tiên điểm
cộng thấp hơn, rồi thứ tự nguyện vọng cao hơn ở cuối danh sách. Chỉ evidence, không
copy predicates2024 hoặc chạy T12. Round/context vẫn nguồn August10, không tự Round1.

Approved PTIT head có1University/1Method/2Program/3Offering approved; toàn bộ entries
và aliases giữ exact. Campus admission-code bindings BVH/BVS chỉ valid2024, nên T07
2026 không tự mở rộng approved University code scope:519ambiguous,0publication-eligible.
Seed mới thêm9pendingMethod; resolver sinh63Program/63Offering proposals cho63source
row families, không cho mỗi method. Compiled97Program/97Offering gồm34mỗi loại lịch
sử. Đề xuất có year/campus/track trong token không chứng minh persistent Programs khác
nhau. Private identity matrix ghi khả năng dùng lại Program đã approved, code/label/
section conflicts và alternatives; không tự merge, alias hoặc cấp canonical UUID.

T08 inspect và checked bindings cho519final candidates, exact parents/hashes/raw cells;
mọi packet conditional, chưa approved. Gates chung: nguồn cutoff2026, quyền sử dụng,
University campus binding, method/instrument, Program/Offering, scale/basis và scope/
tie-break/population/conditions. Quyền cutoff khác authority cho scoring/conversion;
không dùng successful login/preview làm approval. Không tạo executable fact command.

Sáu dòng có exact-name candidate relationship với approvedProgram cũ trong identity
matrix; đây là alternatives để review, không reuse đãconfirmed. Existing2024Offerings
không được biến thành2026. Bonus operators trong63rows:38`=`,11`<=`,14missing/dash;
TTNV:6`=`,25`<=`,18`≤`,14missing/dash. Không đổi inequality thành equality.

## Bảo toàn, replay và bàn giao

Before/after và replay được lưu ở private output; business state phải giữ3canonical,
catalog3/audit47,1releasev3/3facts. ReleaseID
`396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
Các operational updates cũ được giới hạn đúng PTIT host limiter và robots source/
schedule do authorized refresh; mọi old row khác và1081historical files giữ digest.
Không dịch vụ DEV bị restart; chỉ read-only task worker riêng được dừng để thay
selector lặp bằng complete DOM locator index, không giảm số record được kiểm.

| Chỉ tiêu | Trước | Sau |
|---|---:|---:|
| Current verified published canonical / catalog version | 3 / 3 | 3 / 3 |
| Audit events | 47 | 47 |
| Sources / snapshots | 45 / 38 | 48 / 41 |
| Observations / ingest jobs | 1340 / 88 | 1718 / 97 |
| Immutable releases / v3 facts | 1 / 3 | 1 / 3 |

Replay current batch: cachedT05, T06/T07inserted0, mọi34table digests trước/sau replay
bằng nhau. Overall logical source-candidate inventory **379+519=898** theo unique
snapshot/physicalscorecell/method/year;1417normalizationcandidate instances bao gồm
519technical re-extractions bị loại. Đây không phải898canonical business identities.

Lượt cuối đo T05=2.180s/T06=4.158s/T07=6.875s; T08inspection/binding/full-source
checks223.450s. Lượt đầu có stage timings riêng, không gộp mất overhead; read-only
validation worker đã dừng dùng297.918s. Engineering elapsed đến metrics1718.724s,
gồm implementation/tests/restarts; không quảng cáo time/token savings.

Focused63tests pass trước resource fix;14PTITtests cuối gồm synthetic multi-layout,
method/year/campus/header, Decimal, spans/blank/dash, bonus/TTNV, resource error,
PostgreSQL T05/T06/T07/T08/replay và business preservation. Full backend cuối715pass
trong334.99s; một Starlette warning hiện hữu. Lần full đầu bị invalidated khi codehash
đổi trong quá trình chạy, store stale-signature guards hoạt động; chạy lại full trên
code ổn định, không sửa validators/assertions. Ruff193files/mypy80sources/frozen lock87/
Alembic current/check đạt. Frontend build/E2E do existing exact-SHA CI xác nhận; link,
SHA và kết luận thực lưu private verification manifest sau push. Không benchmark50k.

Private `state/intake/ptit-2026-full-multimethod/` giữ required inventory/manifests,
row/cell CSV, typedCSV/JSON, blockedCSV, method/scale/tie evidence, identity matrix,
resolution/T08bindings, validation/replay/before-after và metrics. Candidate-count policy
dedup technical namespace re-extractions bằng snapshot+physical cell+method+year;
không coi source candidates là canonical business identities. Token usage unavailable.

Bước nguồn giá trị cao tiếp theo: official PTIT2025 cutoff lead đã có trong cached
primary HTML: `https://tuyensinh.ptit.edu.vn/gioi-thieu/xem-diem-cac-nam-truoc/diem-trung-tuyen-nam-2025/`.
Chỉ là lead, chưa crawler-verified snapshot; cần task/budget riêng. Không tự dùng request
dư hoặc coi source2026 là2025. Canonical quota vẫn3/20.000, không tăng theo519candidates.
