# T09 — UEH 2024 KSV HTML pilot, chỉ chuẩn bị review

Baseline local/tracking/remote thực: `3accf48c4a5d9cbb2cb010436ec3dbfde3cc65f5`,
nhánh `codex/crawler-pilot`. `git ls-remote` đã đối chiếu trước sửa. Không tracked
changes ban đầu; giữ `.vscode/` và `docs/handoff-current.md` untracked, không stage.
Đã đọc contracts T03–T08, release/source review/WBS và implementation hiện hành.

**Có sáu typed cutoff candidates thật từ fallback, chưa xác minh; cả sáu conditional.
Chưa đạt mục tiêu cutoff đợt bổ sung:** primary trả404. Fallback là công bố kết quả
thông thường17/08/2024; không gán nó thành đợt bổ sung hoặc ordinal1. Không business
approval/bootstrap/publication, source authority approval, release registration hay DSL.

## Nguồn, preflight và ngân sách riêng

Primary được phép:
https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-trung-tuyen-dot-xet-tuyen-bo-sung-khoa-50-dai-hoc-chinh-quy-tai-phan-hieu-vinh-long-ma-ksv/

Fallback được phép:
https://tuyensinh.ueh.edu.vn/bai-viet/ueh-cong-bo-diem-chuan-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-2024-ke-hoach-nhap-hoc-va-chuong-trinh-hoc-bong-tin-dung-hoc-tap/

Chỉ `tuyensinh.ueh.edu.vn`, TLS mặc định có kiểm chứng, safe downloader/public-IP
pinning/host limiter/frontier/RawStorage hiện có. Một university, concurrency1,
0.5request/s, burst1, max_depth0/max_discovery_urls1; exact path regex, không document
host, BFS, browser, login, third-party fetch, retry hoặc redirect. Inventory/profile
UEH cũ không đổi. Technical eligibility không xác nhận authority/license lưu/tái phân phối.

| Run | Thao tác | Wire requests | Kết quả |
|---|---|---:|---|
| `1d163a47-4317-4333-93d1-a551ad727675` | Primary preflight |1| Robots200, allowed, minimum interval2s |
| `d151ec87-db75-4817-8316-38934341fc4b` | Primary fetch |1|404; không snapshot nội dung, job failed |
| `78e014f8-6878-476f-9e50-828fe24ae38f` | Fallback preflight |0| Valid robots cache, exact fallback allowed |
| `49cd0acf-95fe-4ec7-91c4-dd6ab397cfbe` | Fallback fetch |1|200,284975bytes, HTML |

**3/12requests;9không dùng**, dừng sau khi đủ bảng fallback. Không dùng13requests của
UIT/DUT; tất cả4runs UEH paused, các runs/budgets cũ nguyên. Journal riêng
`state/intake/ueh-20261019/http-allocations.jsonl`; allocations3/11/1/10 là ceilings
tuần tự, không phải25requests. Trước mỗi run cộng actual requests_used của runs task
đã pause; ceiling của run hoạt động không vượt12−used. Fetches mới IDs41–43 khớp3wire
reservations, không hidden source HTTP. Không automatic retry; retry count0.

| Snapshot | SHA-256 | Bytes |
|---|---|---:|
| Robots `bfaa5322-fa81-441d-a59d-5813419f2d54` |`208dd58a297578f35c6720e6af0fad603116374a8c18f37ffef5a19a470e185a`|323|
| Fallback `67f11fe2-3a23-4d3a-8d67-fb468f66ec54` |`09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207`|284975|

Fallback source ID `81eefdb2-c1fb-4880-a109-973c41a836d6`; tất cả3sources mới
unverified/unmapped. Không commit raw HTML, source reports, secrets hoặc private outputs.

## Diagnosis và thay đổi nhỏ nhất

T05 generic đã giữ physical cells/span references. Nhưng UEH dùng hai hàng header
`td/strong`, DOM Elementor không có article/main/h1. T06 generic yêu cầu năm/method ở
header và campus BVH/BVS, nên không được nới luật để nhận PT6/KSV. T07 đã hỗ trợ explicit
owner table_program_code_system và pending Program/Offering, có thể dùng nguyên.

Adapter `services/data/parsers/ueh.py` chỉ hỗ trợ exact fallback URL và unique business
root. Nó kiểm explicit publication2024/Chính quy, định nghĩa PT6, heading cutoff,
section2.2Vĩnh Long/KSV và statement bằng điểm giữa tổ hợp/nguyện vọng. Chọn bảng ngay
sau heading KSV và sáu mã pilot từ15program rows thật. Không tải links của bảng.
`html.table_rows` nhận optional header_row_count, mặc định0 giữ behavior cũ; dùng2ở
UEH mà không sửa DOM/locators. Header PT6 có colspan2, ô điểm thực riêng ở column8;
PT3/PT4/PT5, tổng chỉ tiêu và combination list không là PT6 score.

Parser registry/jobs chọn version riêng `html-ueh-2024/1.0.0+ueh-ksv-1` qua parser-only
profile `ueh_2024_html`. Hai fetch profiles vẫn raw_http, profile parser-only không
được crawler start chấp nhận. Không thêm framework/schema/dependency hoặc migration.

`services/data/normalization/ueh.py` chỉ dispatch trong namespace
`normalizer/ueh-2024-ksv/1.0.0`. Kiểm snapshot/table binding, exact header paths của mã,
program, combination và PT6 score; physical origin/nonblank/unspanned Decimal. Không
fallback sang PT4, không strip suffix `_03`, không map mã xét tuyển thành Major.
Year2024 từ nội dung nguồn, không URL/ngày đăng. Campus KSV/Chính quy/method source-specific
đều có section locators. Scope/scale/basis còn review, không confirmed_none/conditions={}
hoặc công thức THPT mặc định. Round/population/conditions/combinations/scale IDs giữnull.

Note ngay sau bảng nói chương trình có dấu(*) dùng hệ số2/quy về30; giữ nguyên note,
program marker và locators, không tự áp dụng weighting cho mọi program. **Fallback
không nêu môn Toán/Tiếng Anh cụ thể hoặc weighted formula**, nên chúng giữunknown.
Statement cùng cutoff giữa tổ hợp được giữ bằng chứng; không nhân một row thành nhiều facts.
Thông báo bổ sung và ngưỡng nhận hồ sơ18.00 nằm sau bảng/note, không áp vào bảng cutoff này.

Resolver logic không đổi; bump `resolver/1.0.2` vì digest implementation bao gồm T06.
Seed pending riêng UEH + PT6/2024, code-system `ueh:admission-code`; compiled registry
có6Program/6Offering proposals, chưa xác nhận Program bền vững xuyên năm. Không approved
UUID, fuzzy auto-merge hoặc namespace PTIT. Old manifests/rows nguyên; executable replay
của namespace lịch sử cần code lịch sử, không claim tương thích với digest mới.

## Kết quả pipeline và private T08

| Stage | Kết quả thật |
|---|---|
| T05 job `7276fb51-7aa1-4f87-9592-f3964b1f4b11` |6physical raw rows, quarantined;4empty-score diagnostics và1total-row-without-value giữ trong job |
| T06 job `178f1673-781a-4d1d-81f0-a78b2a2a9c0f` |6envelopes/6typed cutoff values,0blocked numeric attempts, unverified/needs_review |
| T07 job `5442ee77-1298-4611-a8df-873cd531a188` |6envelopes/6unresolved candidates,0publication eligible; UEH/Program/Offering/method có pending suggestions |
| T08 private inspect |6real digest-bound packets; ready0/conditional6/blocked0;0business commands/approvals |

Total-row issue vẫn mở; source-specific T06 giữ diagnostic nhưng không chặn ô độc lập ở
physical row khác. Không giải phóng unknown parser errors hoặc thay global validators.
T07 giữ30input issue occurrences, không30facts. Replays cached; T06/T07 inserted0,
mọi table digest trước/sau replay giống nhau. Cached parser summary giữ initial inserted6,
không phải delta replay.

| Admission code | Raw program label | PT6 raw | Năm | Campus | Round | Gates |
|---|---|---:|---:|---|---|---|
|7220201|Tiếng Anh thương mại (*)|17.00|2024|KSV|unknown; fallback thông thường|A/I/S|
|7340201_03|Thuế|17.00|2024|KSV|unknown; fallback thông thường|A/I/S|
|7480201|Công nghệ và đổi mới sáng tạo (*)|17.00|2024|KSV|unknown; fallback thông thường|A/I/S|
|7480107|Robot và Trí tuệ nhân tạo (hệ kỹ sư)|17.00|2024|KSV|unknown; fallback thông thường|A/I/S|
|7620114|Kinh doanh nông nghiệp|17.00|2024|KSV|unknown; fallback thông thường|A/I/S|
|7810201|Quản trị khách sạn|18.00|2024|KSV|unknown; fallback thông thường|A/I/S|

A: source authority/use rights; I: University, persistent Program, Offering2024/KSV và
source/year-specific PT6; S: scale/basis, weighting applicability, round/population,
conditions, combination aggregation và publication review. Major/track/language chưa
xác định, không gán default. Bảng research primary không dùng làm output hoặc sửa điểm.

Entry point private: `state/intake/ueh-20261019/review-index.md`, `review-batch.json`,
`review-record-01.json`…`06.json`. Mỗi packet có actual source/snapshot/raw/T06/T07 IDs,
hashes, candidate_key, raw score, row/header/cell/section locators, footnote/combination
evidence, pending mappings, versions, blockers và proposed next decision. Đã resolve
locators lại raw DOM, kiểm text và SHA. `inspect_packet`/`binding_for`/`checked_packet`
đạt; packet_plan read-only có impacts0/can_publish=false. Ghi current approved heads
thật để review sau; không giả draft command/UUID khi còn dependency decisions.

## Preservation và verification

Private `baseline.json`, `after.json`, `preservation.json`, `replay-check.json`,
`release-verify.json`, `http-dev-check.json` giữ evidence. So tất cả PK/column hashes của
34tables trước task:0historical rows changed;364historicalfiles + file bàn giao cùngSHA.
Release ID `396ccd8b-1193-43dd-a08a-bb19e639dd56`, version3, SQL/export/manifestcount3,
manifestSHA `b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90` nguyên.
Read-only release verify đạt;6DEV API responses bằng bàn giao, web/API readiness200.
Không restart services, provision technical roles, sửa approvals hoặc dữ liệu PTIT.

| Application table | Before | After |
|---|---:|---:|
|admission_methods|1|1|
|admission_years|1|1|
|audit_events|47|47|
|catalog_state|1|1|
|combination_subjects|0|0|
|combinations|0|0|
|conversion_rules|0|0|
|crawl_fetches|40|43|
|crawl_host_states|8|9|
|crawl_runs|25|29|
|crawl_schedules|33|35|
|cutoff_evidence|3|3|
|cutoff_scores|3|3|
|dataset_releases|1|1|
|exam_events|0|0|
|ingest_jobs|71|76|
|majors|0|0|
|observations|890|908|
|program_admissions|3|3|
|program_aliases|0|0|
|program_years|3|3|
|programs|2|2|
|quality_issues|0|0|
|scholarships|0|0|
|score_scales|1|1|
|scoring_rules|0|0|
|sna_runs|0|0|
|source_snapshots|33|35|
|sources|39|42|
|subjects|0|0|
|tuition|0|0|
|universities|1|1|
|university_aliases|3|3|
|university_year_features|0|0|

Catalog version3?3; current verified published canonical cutoffs3?3. New jobs:2raw_fetch +1parse_snapshot +1normalize_observations +1resolve_entities. New observations:6raw +6T06 +6T07. New snapshots:robots +fallback HTML; primary404 has none. All other table counts unchanged.

TDD: initial7expected failures; bổ sung RED cho total-row diagnostic và3scope-header
mutations, rồi GREEN.15focused UEH tests gồm physical rows/PT6/KSV/year/suffix/span/null,
no quota/threshold/narrative facts, footnote/T07 provenance, separate PG replay và business
state preservation. Existing PTIT/parser/normalizer/resolver coverage được giữ.
Independent review phát hiện scope-header gap; đã sửa/test lại và reviewer xác nhận.

Full backend trên cây mã cuối: **630passed/287.54s**, một Starlette TestClient deprecation
warning hiện có. Related T05–T07 suite409passed trước ba regressions header cuối;
15focused UEH tests sau fix đạt. Ruff check/format đạt, mypy71sources đạt,
uv frozen lock87packages đạt; Alembic0004_releases/check no new operations.
Frontend scripts hiện có chạy local bằng npm với dependencies đã cài/lock giữ nguyên:
lint/Prettier/typecheck/18unit đạt (pnpm không có trong shell PATH). Build và6E2E thuộc
required GitHub web CI; không claim local unit là build/E2E. Exact pushed SHA, workflow URL
và backend/web CI conclusions được ghi ở private `handoff-final.json`/`ci-latest.json`
và phản hồi cuối sau push. Không sửa CI/dependencies, giảm assertions hoặc nới validators;
không chạy benchmark50k.

Reproduce offline, không HTTP hay business approval:

```powershell
uv run --frozen python -m services.data.parsers replay 67f11fe2-3a23-4d3a-8d67-fb468f66ec54 --profile config/sources/ueh-2024-ksv-fallback-parser-20261019-v1.json --revision ueh-ksv-1
uv run --frozen python -m services.data.resolution replay --job 5442ee77-1298-4611-a8df-873cd531a188
# Private pipeline.py replay compares every table before/after; use new evidence filename
# for another replay rather than overwriting replay-check.json.
```

Intake jobs executed from baseline HEAD with dirty implementation, not falsely labeled
as committed code. Frozen module digests were compared against the final implementation;
all three match. Final Git/CI evidence identifies the committed equivalent bytes.

## Hành động review kế tiếp

Chủ dự án quyết định dùng sáu fallback values này cho field-level business review, hoặc
cung cấp/cho phép exact corrected official URL cho đợt bổ sung ở task bounded riêng.
Không truy tìm URL mới hoặc tự dùng phần budget còn lại. Sau đó review authority và
UEH/Program/Offering/PT6 dependencies trên heads thật; scale/basis/round/population/
conditions/aggregate cần quyết định riêng. Không coi packet inspection là approval.
Chưa hoàn tất T09/T11/Phase1; quota vẫn3/20.000, thiếu19.997; không T12/T13/Score Engine.
