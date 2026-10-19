# T09 — UEH 2024 supplemental + cross-round review preparation

Ngày thực hiện: 20/10/2026. Baseline local/tracking/remote cùng
`9524a7482fdf1386528da74971579af6c75141d7`, branch `codex/crawler-pilot`.
Đọc handoff, contracts và implementation thật trước khi thay đổi. `.vscode/` và
`docs/handoff-current.md` là untracked từ trước, giữ nguyên và không stage.
Baseline DEV khớp checkpoint cuối task trước ở cả 34 bảng; không sửa dữ liệu để ép khớp.

Kết quả: **6 ứng viên PT6 bổ sung thật**, cộng **6 ứng viên tháng 8 giữ nguyên**, thành
12 packet conditional/unverified có binding thật. Có 23 đề xuất quyết định A/I/S/P.
Không approval, bootstrap, publication, release registration hoặc scoring execution.
T09/T11/Phase 1 và quota vẫn chưa hoàn tất; canonical vẫn 3/20.000.

## Nguồn và ngân sách HTTP

Nguồn duy nhất được fetch trong task:

<https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-trung-tuyen-dot-xet-tuyen-bo-sung-khoa-50-dai-hoc-chinh-quy-tai-phan-hieu-vinh-long-ma-truong-ksv/>

Không thử lại URL sai `...ma-ksv/`, không tìm URL khác hoặc tải attachment.
Nguồn tháng 8 chỉ được đọc lại từ snapshot cũ, không HTTP:

<https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/>

Profile mới `ueh-2024-supplemental-20261020-v1` giới hạn exact host/path, một seed,
depth 0, discovery 1, concurrency/burst 1, 0,5 request/giây; không JS/document hosts.
Inventory UEH, fallback profile và output cũ không đổi. Eligibility chỉ là kỹ thuật,
không phải source-authority hay quyền lưu trữ/tái phân phối.

Safe downloader giữ TLS verification, SSRF và robots. Robots cache còn hạn theo đồng
hồ/policy thật: checked `2026-10-19T15:42:16.269875Z`, expires
`2026-10-20T15:42:16.269875Z`, SHA-256
`208dd58a297578f35c6720e6af0fad603116374a8c18f37ffef5a19a470e185a`.
Policy cho phép URL; interval tối thiểu 2 giây. Không dùng web research làm input pipeline.

| Run | Mục đích | Wire requests | Kết quả |
|---|---|---:|---|
| `1ccd8258-91a9-4823-ae70-2cbbd16d1b34` | preflight | 0 | valid cached robots, allowed; paused |
| `c833e3b8-63ad-4ba1-80d5-5b29873b04b3` | exact content | 1 | HTTP 200; paused |

**1/8 requests**, còn 7 không dùng; robots wire 0, redirect 0, retry 0, failed wire 0.
Fetch ID 44; budgets UEH cũ 3/12 và UIT/DUT 17/30 giữ nguyên, không resume run lịch sử.
Profile fetch và parser riêng có hash trong private accounting/frozen jobs.

| Snapshot | ID | Bytes | Raw SHA-256 |
|---|---|---:|---|
| September 30, mới | `ce858dfc-707a-4e2d-ad3d-a5439807fa1c` | 193572 | `51b52957dc76a054a804e93dfc3f13defca46ddbe119c6890bdb1d042c6f4b1d` |
| August 17, cũ | `67f11fe2-3a23-4d3a-8d67-fb468f66ec54` | 284975 | `09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207` |

Source mới `82434dcd-49e1-409f-9182-f58308b986f3`. Snapshot thật được kiểm lại
byte size/SHA và từng raw score/locator; không dùng synthetic fixture thay dữ liệu thật.

## Chẩn đoán và thay đổi tối thiểu

Trang bổ sung khác fallback: table đầu tiên, một hàng header TH, sáu cột, PT6 ở cột 6;
fallback có nhiều tầng header/table khác. Generic classifier không tự hiểu PT6.
Năm 2024/method nằm ở paragraph riêng, campus ở article title, ngày ở article metadata.
DOM thực có NBSP sau dấu gạch trước method; keyword matching chuẩn hóa whitespace cục bộ,
không thay raw evidence. Không suy năm/method từ URL, ngày hoặc khoảng điểm.

- Thêm hai versioned SourceProfile: exact fetch và parser-only; không sửa profile frozen.
- `parsers/html.py`: tùy chọn explicit score columns dùng sau source-specific header/context
  validation; mặc định generic và adapter August giữ nguyên. Tái dùng physical grid/span/locator.
- `parsers/ueh_supplemental.py`: unique article/title/date/section anchors; đúng table/header;
  PT4/PT6 riêng; physical code/name/combination/value cells; giữ scope/eligibility/priority,
  marker và footnotes/formula với locators. DOM/context lệch thì fail closed.
- `normalization/ueh_supplemental.py`: typed Decimal, explicit 2024/PT6/KSV/chính quy,
  nguyên admission code `_03`, label và scope evidence. Round key chỉ proposal,
  ordinal unknown; population/conditions/scale/combination identity vẫn unresolved.
- Glue registry/normalizer chọn đúng version mới. Resolver `1.0.3` cho implementation
  digest mới; không đổi thuật toán match, bật fuzzy auto-link hay sửa resolver outputs cũ.
- `tests/normalization/test_ueh_supplemental.py`: synthetic HTML được gắn nhãn rõ;
  tests scope, physical cells, source separation, weighting, PG replay và provenance.

Không taxonomy hóa suffix, không PTIT BVH/BVS assumptions, không nhân bản combinations.
`(*)` chỉ gắn Toán cho `7480201`; `(**)` chỉ gắn Tiếng Anh cho `7220201`, theo exact
code/name/marker và named formula evidence. Review độc lập phát hiện marker đơn lẻ chưa
đủ; thêm bốn RED→GREEN regressions chặn marker sai/ngành khác/tên khác/thiếu marker.
Named formula “Công nghệ đổi mới sáng tạo” được giữ nguyên dù table có thêm “và”.
`(S)` là metadata song ngành, không là score weight hoặc Major taxonomy.

## Output thật và locators

T05 job `db7af33a-25fb-44ad-b170-bc9f3d73d420`:
**6 raw cutoff rows**, 0 parser issues; version
`html-ueh-supplemental-2024/1.0.0+ueh-supp-1`.

T06 job `7f6d90ab-4640-48b1-9c14-58d66a5deb60`:
**6 typed candidates**, 0 blocked attempts; status quarantined;
`normalizer/ueh-supplemental-2024/1.0.0`.

T07 job `3fe9c88c-d372-44f9-bfe6-9f8df5c02719`:
**6 envelopes/6 unresolved candidates**, 0 publication eligible;
`resolver/1.0.3`, `registry/ueh-cross-round/20261020-r1`.
Reuse pending UEH registry/code system; aliases giữ head pending cũ vì entries không đổi.
Không entity nào mới được approved/canonical UUID. Các label variants tạo pending
proposals để review, không được coi thành Programs mới đã xác nhận. Compiled pending
registry có 1 University/1 Method/9 Program/9 Offering proposals: ba label variants mới
chưa được merge hoặc coi là identity khác. Review package nhóm thành sáu cặp code.

Đặt `B` là full business-root locator trong `parser-run.json`:

```text
html:html:nth-of-type(1) > body:nth-of-type(1) > div:nth-of-type(2) > section:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > section:nth-of-type(3) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(4) > div:nth-of-type(1)
```

Mỗi ô điểm là `B > table:nth-of-type(1) > tbody:nth-of-type(1) > tr:nth-of-type(R) > td:nth-of-type(6)`.
Header PT6 có locator riêng trong packet; code/name/combination lần lượt là td 2/3/4
của cùng physical row. Raw score là chuỗi `20` hoặc `17`, không bị thay bằng reference.

| Admission code | Nhãn nguồn September | PT6 | R | Năm / campus / round |
|---|---|---:|---:|---|
| 7220201 | Tiếng Anh thương mại (**) | 20 | 1 | 2024 / KSV / bổ sung, ordinal unknown |
| 7340201_03 | Thuế (S) | 20 | 2 | 2024 / KSV / bổ sung, ordinal unknown |
| 7480201 | Công nghệ và đổi mới sáng tạo (*) | 17 | 3 | 2024 / KSV / bổ sung, ordinal unknown |
| 7480107 | Robot và Trí tuệ nhân tạo (hệ kỹ sư) | 17 | 4 | 2024 / KSV / bổ sung, ordinal unknown |
| 7620114 | Kinh doanh nông nghiệp (S) | 17 | 5 | 2024 / KSV / bổ sung, ordinal unknown |
| 7810201 | Quản trị khách sạn | 20 | 6 | 2024 / KSV / bổ sung, ordinal unknown |

Explicit year/method: B/p 1 và 3; cutoff section p 5; aggregate applicability p 6;
weighting p 7/8; `(S)` p 9; general formula p 19, English p 20, Math p 21;
PT6 priority p 31–35/table 4, riêng PT4; eligibility/method-preference có adjacent UL.
Không lấy narrative formulas, ngày, priority/threshold/quota thành cutoff values.
Title/date locators ở article widgets, không lấy sidebar date.

## So sánh hai nguồn, không coi là correction

| Code | August 17 | September 30 bổ sung | Cần review identity |
|---|---:|---:|---|
| 7220201 | 17.00 | 20 | `(*)` → `(**)`: marker convention/identity |
| 7340201_03 | 17.00 | 20 | Thuế → Thuế (S): Program/Offering context |
| 7480201 | 17.00 | 17 | same-name Program proposal; distinct unreviewed scopes |
| 7480107 | 17.00 | 17 | same-name Program proposal; distinct unreviewed scopes |
| 7620114 | 17.00 | 17 | thêm (S): Program/Offering context |
| 7810201 | 18.00 | 20 | same-name Program proposal; distinct unreviewed scopes |

Snapshot thật cho **3 changed / 3 unchanged**, khác reference “4 changed / 2 unchanged”.
Không ép test/dữ liệu theo reference. August không bị gắn “Round 1”. September proposal
`ueh:ksv:2024:supplemental:notice-20240930`, chưa canonical/approved, ordinal null.
Cùng năm/Program/method không đủ để kết luận correction; không sửa/revise fact nào.
Ba exact labels có thể cùng persistent Program, ba label/marker variants cần review;
chưa có bằng chứng buộc tách Programs/Offerings, và chưa scope nào được business-reviewed.

## Private review package và các gates

Ignored `state/intake/ueh-2024-cross-round-review/` chứa 12 full packets, review index,
machine batch, six-pair comparison, 23 field-level decisions, nguồn/IDs/hash/locators,
frozen registry, accounting, baseline/after/preservation và replay/verification evidence.
Không commit HTML, full evidence/private report hay credentials.

Phân nhóm: ready không điều kiện 0; **conditional 12**; blocked thiếu typed evidence 0.
Cả 12 đủ để bắt đầu field-level evidence review; business approvals 0, publishable 0.
T08 binding thật được inspect/checked; không tạo fake UUID hoặc executable command.
Packet-plan chỉ đọc, impact 0. Login/can-apply không được coi là business approval.

- **A**: first-party UEH authority cho từng exact notice/snapshot, năm 2024/KSV/PT6/cutoff;
  scope và quyền storage/redistribution vẫn cần chủ dự án quyết định.
- **I**: UEH University, sáu nhóm persistent Programs, sáu nhóm 2024 KSV Offerings,
  PT6 year-specific/code system; `(S)`, marker, track/language và aliases còn pending.
  Admission code không tự nhận diện Major taxonomy.
- **S**: source có 30-point normalization và công thức/priority, nhưng formal scale/basis
  chưa approved. September named weights không được backfill vào generic starred note
  August. Round identity/ordinal, population/eligibility/conditions, combination aggregate
  và weighting applicability cần quyết định riêng; không `confirmed_none`/`conditions={}`.
- **P**: sau A/I/S approvals mới có thể freeze registry/alias heads và rerun T07 mới, rồi
  lập T08 draft có dependencies/bindings thật trong task được phép riêng. Review và publish
  là các bước nghiệp vụ riêng; hiện không apply/bootstrap/publish/register release.

Mỗi đề xuất có evidence/hashes, candidate value, proposed interpretation, alternatives,
missing evidence, downstream effect và owner-approval-required. Materializable commands rỗng.

## DEV trước/sau và bảo toàn

| Bảng | Trước | Sau |
|---|---:|---:|
| admission_methods | 1 | 1 |
| admission_years | 1 | 1 |
| audit_events | 47 | 47 |
| catalog_state | 1 | 1 |
| combination_subjects | 0 | 0 |
| combinations | 0 | 0 |
| conversion_rules | 0 | 0 |
| crawl_fetches | 43 | 44 |
| crawl_host_states | 9 | 9 |
| crawl_runs | 29 | 31 |
| crawl_schedules | 35 | 36 |
| cutoff_evidence | 3 | 3 |
| cutoff_scores | 3 | 3 |
| dataset_releases | 1 | 1 |
| exam_events | 0 | 0 |
| ingest_jobs | 76 | 80 |
| majors | 0 | 0 |
| observations | 908 | 926 |
| program_admissions | 3 | 3 |
| program_aliases | 0 | 0 |
| program_years | 3 | 3 |
| programs | 2 | 2 |
| quality_issues | 0 | 0 |
| scholarships | 0 | 0 |
| score_scales | 1 | 1 |
| scoring_rules | 0 | 0 |
| sna_runs | 0 | 0 |
| source_snapshots | 35 | 36 |
| sources | 42 | 43 |
| subjects | 0 | 0 |
| tuition | 0 | 0 |
| universities | 1 | 1 |
| university_aliases | 3 | 3 |
| university_year_features | 0 | 0 |

Catalog **3→3**, current verified published **3→3**, audit **47→47**.
Release count **1→1**, version **3**, export count **3** (không phải ba release rows).
ID `396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
`verify_bundle`/registered release binding đạt; tất cả 36 raw snapshots đúng bytes/hash.

So sánh digest mọi hàng cũ ở 34 bảng: chỉ operational row
`crawl_host_states['tuyensinh.ueh.edu.vn']` đổi theo limiter/lease lần fetch mới.
Mọi hàng cũ khác, toàn bộ PTIT University/Program/Offering/cutoff/evidence IDs,
frozen approvals/audits/releases và input/output UEH August nguyên. **476 file lịch sử**
(bao gồm bộ cũ, intake/raw và `.vscode/`) giữ digest; handoff không chỉnh sửa.
6 historical packet objects/row hashes nguyên và 6 catalog API response bodies khớp
handoff trước; health live/ready 200 qua current app/read-only DEV DB.
Không restart service, xóa database, đổi Docker global hoặc sửa migration đã áp dụng.

Technical deltas: 1 raw-fetch + 1 parser + 1 normalizer + 1 resolver job;
6 raw + 6 T06 + 6 T07 observations; 1 snapshot/source/fetch/schedule và 2 paused runs.
Replay T05 cached, T06/T07 inserted 0; toàn bộ table digests trước/sau replay giống nhau.
Implementation hashes frozen job khớp mã hiện tại. Jobs chạy từ baseline dirty worktree;
không giả nhận đã chạy ở commit sau. Final commit/CI ghi trong private handoff sau push.

## Verification và bước tiếp theo

TDD RED→GREEN cho source adapter, NBSP thực và named formula applicability. **40 focused
UEH tests** (25 mới + 15 August giữ nguyên) qua. Ruff check/format (174 files), mypy
(73 sources), frozen uv lock (87 packages), Alembic `0004_releases`/check không phát sinh
operations đều đạt. Frontend lint/format/typecheck và 18 unit tests đạt bằng npm với
dependencies hiện có; CI policy vẫn chạy build/E2E. Không đổi lock, CI, assertions,
validators hoặc chạy benchmark 50k. Full backend trên cây mã cuối: **655 passed**, 309,70
giây, một Starlette deprecation warning hiện có; dùng PostgreSQL test DB riêng, không
xóa retained databases. Exact pushed-SHA CI được ghi nhận ở private checkpoint cuối và
phản hồi bàn giao; không lấy kết quả baseline làm kết quả commit mới.

Chủ dự án review 23 đề xuất A/I/S/P theo từng field, đặc biệt source authority/rights,
Program/Offering variants và hai admission scopes. Đây là bước review tiếp theo;
không task nào hiện tại cho phép approval/apply/publication/T12/T13/deployment.
