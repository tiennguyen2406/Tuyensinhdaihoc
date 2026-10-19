# Bootstrap invalidation và bounded multisource intake — 19/10/2026

Baseline branch `codex/crawler-pilot`, HEAD/origin cùng
`511290f68ea0c34e0494266189576b689f5c52cb`; không reset. Đã đọc contractsT03–T10,
WBS và kế hoạch/báo cáo T10. Bản Desktop Overview đối chiếu lại SHA-256
`c3745329543e433bd62cf58e4a6df4c827ea54b5876f48f8c42e33d5aabf04c5`, theo
schema-provenance.md. Không có AGENTS ở root/parents; apps/web không sửa trong task.
Kế hoạch trước sửa: plans/2026-10-19-bootstrap-invalidation-intake.md.

**Serving invalidation đã sửa và kiểm chứng. Intake mới chỉ đạt staging/review gates;
chưa đạt mục tiêu5–10cutoff candidate packets.** Không dùng FAQ, ảnh hoặc enrollment
counts để tạo điểm giả. Không approval/bootstrap nghiệp vụ/publication/release mới.

## Serving-change policy và regression

Lỗi: alias_affects_serving() dựa vào trường có cutoff nên bỏ sót T10 đang phục vụ
verified University, admission_years status và Program detail ngay khi chưa có cutoff.
Policy chung `services/data/publication/serving.py` nay dùng từ operations() cho cả
plan/apply, trên values đã resolve @parents, bao gồm parent tạo trong cùng transaction.

| Mutation được hỗ trợ | Khi nào tăng version |
|---|---|
| University create | Được bootstrap verified, dù chưa có fact/năm |
| Program create | Parent University verified, vì detail được phép tra cứu |
| Admission-year create | Parent verified, năm2024–2026 |
| University alias create | Approved, parent verified, validity overlap năm mục tiêu |
| Source link | Verification đổi làm source reference hợp lệ xuất hiện trên current verified published fact, primary/supporting |
| Internal-only registry link, year/alias ngoài phạm vi, no-fact Offering, source authority metadata | Không tự tăng version |

Toàn bootstrap transaction chỉ có delta0/1. Audit/canonical rows/catalog increment/
refresh_serving outbox giữ cùng transaction; enqueue lỗi rollback tất cả. Cursor cũ
409 DATASET_CHANGED; không sửa visibility endpoint để che lỗi. Replay cùng request
trả frozen result cũ, không thêm version/job/audit; không sửa approval/result lịch sử.

RED:7expected failures trước fix,1internal-metadata test đã pass; bổ sung negative cases
thành12PostgreSQL regressions. GREEN gate16tests =12new +4corepublication assertions
đã sửa. Bootstrap fixture tạo visible identities nay là version1; cutoff đầu version2,
ba publication version4; rollback publication giữ bootstrap1; alias thêm một refresh.
Giữ kiểm replay/idempotency. Những số này thuộc synthetic DB mới, không viết lại PTIT.
Full repository615tests đạt sau thay đổi.

## Chọn nguồn và giới hạn kỹ thuật

UIT/DUT profiles ban đầu checked/robots unknown/verifiedfalse; HUST candidate và lịch sử
direct timeout. Chọn UIT trước vì first-party admissions đã có inventory; TLS certificate
verification failed ngay robots, giữ lỗi, không bypass. DUT là trường thứ2/fallback;
không mở trường thứ3. Profiles cũ và inventory lịch sử giữ nguyên; profiles mới có ID
riêng trong config/sources, max_depth0/max_discovery_urls1, concurrency1/0.5rps/burst1.

DUT robots200 cho phép, raw được lấy qua downloader/RawStorage/frontier hiện có.
Narrow profiles chỉ nhận URLs đã quan sát, một task leased/download/stop, không chạy
discovery worker tự do. DNS/public-IP pinning/TLS/redirect/retry/size limits giữ nguyên.
Host DUTmain/archive2025 được nav chính dẫn rõ; Drive có exact official iframe relation,
được preflight document host và chỉ tải public preview. Không login/CAPTCHA bypass,
không tải hồ sơ thí sinh, không mở Google hosts khác hoặc CDN trang trí.

| Nhánh nguồn đã kiểm | Bằng chứng và disposition |
|---|---|
| UIT admissions | robots TLS failure; không snapshot nội dung |
| DUT handbook HTML | First-party FAQ;9catalog observations, không có bảng cutoff |
| DUT report2024 HTML/PDF |12pages; images+text layer lỗi, nội dung số lượng nhập học; không coi đó là cutoff hoặc giả parse scan |
| DUT handbook PDF literal từ HTML | Request failed network_or_body_policy/ValueError; không có snapshot, không suy chính xác size/network cause từ error code chung |
| DUT cutoff hai năm |3same-host JPEGs trong business root; parser ghi3image_requires_review,0observations; không OCR |
| DUT cutoff chính quy2026 | Official title/iframe; parser attachment_not_embedded_text,0observations; drawing-exam fallback PDF khác nghĩa không tải làm cutoff |
| DUTmain archive2024 | robots TLS failure, không bypass |
| DUT archive2025 | robots200, content500 rồi đúng một retry đã đến hạn cũng500; giữ jobretry_wait và runpaused, không reset retry |
| DUT old footer admission-info |404; current menu info2026 được kiểm riêng, embeds Drive viewers |
| Linked public Drive cutoff2026 | Robots200 allows exact preview; HTML title là cutoff PDF nhưng body chỉ viewerJS/loading/login link; không login, không reverse-engineer/download URL chưa có evidence |

Technical eligible không là source authority, canonical mapping, rule approval hay license
tái phân phối.16sources mới đều unverified và university_id null. Không lưu/công bố
raw trong Git. Dừng ở đây với13requests còn lại vì những nhánh đã quan sát không cung
cấp supported typed cutoff; không dùng phần budget còn lại để crawl ngẫu nhiên hoặc
vượt giới hạn2trường. Cần nguồn HTML/PDF số phù hợp hoặc task riêng về OCR/source fallback.

## Budget và accounting

**17/30wire requests,13remaining**, gồm robots/discovery/content/failures và một retry.
17new crawl runs đều paused; có một run configuration failed trước HTTP, requests_used0,
được giữ để truy vết (document path chưa admit; profilev2 thu hẹp đúng path rồi mới tải).
Không sửa run/budget từ task cũ.

Private operator journal `http-allocations.jsonl` + từng http-RUN.json + retry record.
Mỗi lần chạy xác nhận tất cả run task trước paused/needs_review, cộng requests_used,
và cấp current run ceiling không quá30-used. Chỉ một operator/request luồng hoạt động;
host limiter vẫn do Store.acquire bảo vệ. Tổng các **ceilings lịch sử46** không phải
46wire requests: phần chưa dùng nằm ở paused runs, không được tự resume. Không chạy
work/resume thủ công các runs này mà bỏ task accounting. Actual17 reservations khớp
17new crawl_fetches, IDs24–40; không có hidden browser/search HTTP ngoài journal.

11snapshots mới/10distinct raw hashes (hai DUT robots snapshots cùng blob), hash/size
đều verify. Full snapshots IDs/URLs/hash/size nằm trong private snapshot-index.json;
bảng hash ở cuối báo cáo. Không coi HTTP200 là verified source.

## Parser, normalization, resolution và gói review

Không thêm OCR/SPA/adapter suy điểm mới. Existing html/1.0.1 với source business selector
riêng và revisions dut-faq-1/dut-images-1/dut-cutoff26-1 được replay trên actual snapshots.
Tất cả9FAQ raw locators resolve lại DOM gốc và raw_text bằng nhau; không lấy footer/nav.
Raw values/header/context giữ nguyên; không gán admission_year từ URL/ngày đăng.

| Stage | New records / result |
|---|---|
| Raw snapshots |11snapshots/10hashes; không tính failed HTTP là snapshot |
| T05 FAQ |9catalog observations unverified;11image review issues |
| T05 cutoff image/2026 iframe |2quarantined jobs,0observations;3image issues/1attachment issue |
| T06 |9envelopes;0typedcandidates;0numeric blocked_attempts;9inputs có STRUCTURED_MAPPING_REQUIRED |
| T07 |9envelopes;0candidates/states/publicationeligible;108issue occurrences inherited, không là108facts |
| Review batch |9staging-review-gate records;0T08 candidate fact packets |

T06 namespace `normalizer/dut-review/1.0.0`, require_campus=false chỉ giữ unknown null;
không giải phóng typed mapping. Job c3a6e760-6502-4a7c-80fa-075b2238df2f.
T07 resolver/1.0.1, registry/dut-intake/1, aliases/dut-intake/1; job
05ed9205-b3b2-47a9-9a79-656d70d7fe53. Private pending University proposal:dut không có
canonical ID; không map shared Drive host thành University. Không tạo Program/Offering
proposals từ FAQ hoặc dùng preview UUID như canonical parent.

T07 fix nhỏ cần cho nguồn bổ sung: bỏ implicit PTIT table-program code system cho mọi
owner; helper chung đọc explicit owner.attributes.table_program_code_system, PTIT known
owner/bindings giữ legacy fallback, owner khác thiếu namespace unresolved. RED6failures,
new-source pending namespace/store replay regressions đạt; không đổi schema/framework.
Bump resolver version vì implementation hash thay đổi. Old manifests/output nguyên;
không chạy mutation replay namespace cũ hoặc khẳng định executable compatibility.

Private review entry point: `state/intake/multisource-20261019/review-index.md`, bảng9rows
liên kết review-record-01..09.json; review-batch.json chứa full raw/T06/T07 IDs/digests,
source/snapshot/hash/locator, versions/signatures, blockers và quyết định tiếp theo.
Mỗi record có candidate_values/year/method/campus/scale/basis/scope/conditions=null,
canonical IDs null, materializable_commands=[], request_id/hash=null. Đây là conditional
staging review, **không ghi plan đạt**. Chưa đủ typed candidate/parents cho T08Binding;
không tạo fake command hoặc tự approve để có5–10factpackets. Current expected canonical/
catalog impact0. Future impact phải plan lại bằng real heads/parents sau quyết định nguồn.

Các topics của9raw records: new specializations,2025 applicant eligibility, application
methods/priority, prior graduates, thresholds, quota và follow-up steps. Những topics này
là source context để phân loại, không thay score/cutoff facts. Không tính quota là cutoff.

## Replay, history và DEV

Replay3parser jobs cached; parser cached result giữ original inserted9 của initial run,
không phải delta retry. So toàn bộ table digests before/after replay cho thấy0mutation.
T06/T07 replay cached=true/inserted0, không thêm jobs/audit/version. Release3 verify lại
read_only/cached/verified=true, không rebuild; SQL/export/manifest count3.

| DEV | Before | After | Giải thích delta |
|---|---:|---:|---|
| Catalog/canonical |3/3 |3/3 |Không business bootstrap/publication |
| Observations |863 |890 |+9raw catalog,+9T06,+9T07 |
| Jobs |55 |71 |+11raw_fetch,+3parse_snapshot,+1normalize,+1resolve |
| Audit/releases |47/1 |47/1 |Không approval/provision/release registration |
| Sources/snapshots |23/22 |39/33 |Unverified public source metadata/+11snapshots |
| Crawl fetches/runs |23/8 |40/25 |17wire records,17runs gồm0request configuration run |
| Host states/schedules |3/22 |8/33 |5new hosts,11snapshot scheduling metadata |

Mọi PK/column digest của34tables trước task vẫn nguyên;364historicalfiles cùngSHA;
PTIT2Program/3Offering/3cutoffs/3evidence giữ nguyên, approvals/A2/B/C/D không đổi.
Refresh requested1/2coalesced3 và3built giữ nguyên. Không tạo releases1/2 hay4.

Release ID396ccd8b-1193-43dd-a08a-bb19e639dd56 version3; manifest
state/releases/canonical/version-3/manifest.json, SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
DEV web3000/API8000 processes giữ nguyên, health/actual HTTP200, PTIT partial2024 với
25.17/18.4/26.4,2025/2026rỗng; serving version3/release3 khớp. Không restart hoặc start
duplicate processes. Runtime/run commands theo catalog-contract.md.

## Checks và chạy lại

Backend615passed/294.93s; one existing Starlette TestClient deprecation warning.
Ruff check/format,mypy69sources,uv lock87packages,Alembic0004_releases/check pass.
Web local lint/format/typecheck/18unit pass; frontend source/versions/locks không đổi.
Build và6desktop/mobileE2E được kiểm bởi CI exact SHA sau push, kết quả lưu final handoff;
không gọi local unit là build/E2E. Không tắt checks, giảm coverage hoặc benchmark50k lại.
InitialRAMavailable2.31GiB, dưới tải kiểm còn1.96GiB; diskfree284.9GiB. Không xóa DB/files,
down-v hoặc đổi Docker/global config. T19 SLO50k/20users p95=2625.4ms vẫn chưa đạt500ms;
coverage aggregate/temp spill còn bottleneck, chỉ đo lại khi có thay đổi liên quan/môi
trường cô lập. Báo cáo T10 cũ giữ nguyên như evidence.

```powershell
# Read-only actual snapshot replay; không HTTP, không publish.
uv run python -m services.data.parsers replay 0374e539-54b6-48de-817a-08b005335b18 --profile config/sources/dut-intake-20261019-parser-faq-v1.json --revision dut-faq-1
uv run python -m services.data.resolution replay --job 05ed9205-b3b2-47a9-9a79-656d70d7fe53
# Task-local private replay uses existing T06/T07 Store APIs, records DB digests.
.venv/Scripts/python.exe -X utf8 state/intake/multisource-20261019/replay-check.py
# replay-check.py writes a new unique private evidence filename each time.
uv run pytest -q --tb=short --basetemp=<NEW_TEMP_OUTSIDE_CHECKOUT>
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv lock --check
uv run alembic check
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
```

Không chạy intake start/work/resume lại như replay: đó là network mutation, budget và
new-source gates phải được kiểm riêng. Không có command approval/publication đủ điều
kiện materialize trong batch mới. `.vscode/`, secrets/raw/privateoutputs ngoàiGit.

## WBS và quyết định tiếp theo

Đạt fix consistency và bounded technical staging; **chưa đạt pilot cutoff đa nguồn**.
Cần một official HTML/PDF số đọc được hoặc phạm vi mới cho OCR/source fallback để có
typed candidates, sau đó authority/University–Program–Offering/scale/basis/scope review
cụ thể qua T08/T11. Không biến9staging gates thành9business approvals. Admin mutation
API/OIDC và governance còn thiếu; không thêm framework để che thiếu dữ liệu.
Canonical vẫn3/20.000, thiếu19.997; không cộng candidates/envelopes/synthetic. Không đóng
toànT09/Phase1 hoặc chuyểnT12/T13 khi thiếu rules/scales/golden evidence. Sau approval/
publication mới dùng catalog version thực để build release mới; release3 bất biến.

## Snapshot checksums

| Snapshot ID | Media / bytes | SHA-256 |
|---|---|---|
| 7a3c1499-bf97-4ebb-9176-459a8436fa5c | text/plain / 73 | f5230e917f2f6ed23e0c20a1803552c5ac992f24fb958dab50c05a4d7cb4fe3d |
| 0374e539-54b6-48de-817a-08b005335b18 | text/html / 58135 | 7aef936bee6156ba0b62a5f52e3dab88625fe57729affcecc4b55c4fb874943f |
| 7449df3b-71ab-4cfb-892b-af15b66dd316 | text/html / 50546 | 85f4afca36b3f6c76718372f7a96054fe54a5683149705ec1c7dea1f6b3aa743 |
| 402e8c14-876e-4e1e-b3af-9bf4c1219c18 | application/pdf / 3510518 | 48f848ae8e3ef2b38f9f871c7c660a4d674db23061995373d8515b4dcb892bf8 |
| 85947e7c-45de-4676-8718-d6bf909e6b1c | text/html / 66151 | 7a5e94dcc4cdb635633eebdee086500197b415a8563349f024fd70479e89a1c2 |
| d8598671-ed16-4654-baf0-901bc1372a3a | text/html / 44908 | 4909e6a1f54a97e856ffaaa868683c81745901cb29338c22a182d15aa73de12c |
| 36448ed7-c81b-4ac8-ac3b-8170adaf2187 | text/html / 39689 | 98a9d0f602609df8f3467b97881c82fbac6a160da634d91fdb3cfcf82d75f5e0 |
| f6be65d8-0ad5-4cd2-a68e-8c69855c0e3e | text/plain / 73 | f5230e917f2f6ed23e0c20a1803552c5ac992f24fb958dab50c05a4d7cb4fe3d |
| a5166a56-e0dc-427d-b719-614cb216e00d | text/html / 47372 | 09f453d4c2e86015dae41b2d9de628295f208b4567ce0f8fe23bdfe630e211d0 |
| 4c3606ce-187d-4bf8-81cb-482b7c273d64 | text/plain / 600 | 87cecc58fb663a3f8650a3a88eb59c1ecaae20d063dcd6d50ab39f73167d4af4 |
| 2e1bea55-eaba-43f5-bc1a-77468f53b7f4 | text/html / 85625 | cc3263dd4fa8e5170ac27ece105859add6c28e1a25323ed8a35fd7052ca32280 |
