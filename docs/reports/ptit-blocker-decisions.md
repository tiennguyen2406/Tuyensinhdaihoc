# PTIT — gỡ blocker và lô quyết định A2/B/C/D

Ngày18/10/2026, tiếp tục `codex/crawler-pilot` từ `a07370527c4634a7f4d99e0bf32e48a818fa599b`, origin đúng repository người dùng chỉ định, working tree sạch lúc bắt đầu. Không reset/merge/main/deploy. Phase1 — Data, chưa approval/publication canonical. Bảng tiến độ từng T01–T19: [progress-wbs.md](../progress-wbs.md).

## Hiện trạng và approval

PostgreSQL ở0003_publication(head). Baseline645observations/25jobs/11snapshots; canonical cutoffs/catalog version/releases0/0/0. Dedicated DEV reviewer/publisher tồn tại, không privileged, đọc schema/role đúng; không tạo/reset credentials. Không có AGENTS.md trong repo/cha được kiểm; đã đọc Overview/WBS Desktop, provenance/dictionary/contracts T05–T08, workflow/báo cáo/private packets và DraftA.

**Không nhận approval nghiệp vụ nào.** Prompt tiếp tục, reports, can_apply hoặc technical login không là approval. DraftA cũ giữ nguyên SHA `eb2e08b6da932da939d0af9cf95f3d694a1a865588f424dc471d91176273f650`. Draft mới A2 có requestID/versions/hash mới; không dùng approval của bản khác. Không bootstrap thật, export registry preview thành approved, chạy resolver persist mới hoặc publisher thật trong đợt này.

## Evidence mới, accounting và locator

Tổng allocation bổ sung **17/20 requests**, còn3, không cấp thêm15 vào cap cũ. Từ baseline5 đã dùng thêm12requests:4discovery/content API ở tuyển sinh, robots404 host tài liệu+PDF200, robots200 portal chính+3API200+2HTML200. Không redirect/retry/login/portal cá nhân/CAPTCHA; không truy cập các đường tra cứu thí sinh được nêu trong thông báo. Raw200 lưu bất biến; robots404 ghi fetch nhưng không tạo blob200 giả.

| Run (UUID prefix; đầy đủ trong private manifest) | Cap | Used | Lý do chuyển allocation |
|---|---:|---:|---|
|8693513c|1|1|Run đầu của đợt trước|
|4adcf376|8|8|Cap19 giảm về8 đã dùng, chuyển11 chưa dùng|
|06ce2f6f|1|1|Robots document host; chuyển10 chưa dùng|
|ca3d7ab0|1|1|PDF gốc; chuyển9 chưa dùng|
|dadb882d|1|1|Robots portal chính; chuyển8 chưa dùng|
|49928398|8|5|API và hai thông báo cutoff; dừng khi đủ evidence để review|
|Tổng|**20**|**17**|Sáu run paused; không tăng tổng cap|

Old pilot6ee6fd0d… vẫn paused5/5; old preflight3e9e5362… paused1/2. Không sửa frozen profiles; có profiles mới theo host/phase. Crawler/Transport/RawStorage cũ giữ shared limiter, robots/TTL, allowlist, public-IP pinning/SSRF/TLS/size checks. Host mới có quan hệ từ nguồn đã đọc trước tải: API tuyển sinh id3432 liên kết PDF `apiquanlydaotao.ptit.edu.vn`; PDF2024p1 và cached HTML2026 liên kết portal `ptit.edu.vn`. Profiles checked trước robots, eligible sau preflight; trạng thái này không là quyền thương mại/tái phân phối hoặc fact approval.

| Nội dung đã đọc | Snapshot / SHA-256 | Locator/phạm vi |
|---|---|---|
|[Đề án gốc2024, nội dung QĐ545](https://apiquanlydaotao.ptit.edu.vn/data/fileUpload-1712750500244-qd_545_noi_dung_de_an_ts__h_2024.pdf)|f31d55ba-cbc7-42e0-9a02-c5a7c285abc3 / `1b1e3741108ce5711bc61823200d4acaa534082a70b769894ec61d28fbb167c3`|62pages scan/0digital chars. Visual p1 institution/BVH/BVS; p7 authorized majors; p9–10 method/eligibility; p11–13 campus offerings; p16§1.6.2b same cutoff/30/tie; p19 priority; p20 institutional catalog/combinations; p21–22 planned rounds. Không OCR/không người phụ trách duyệt|
|[Thông báo cutoff BVH2024](https://ptit.edu.vn/hoc-vien-cong-nghe-buu-chinh-vien-thong-thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-theo-phuong-thuc-xet-tuyen-dua-vao-ket-qua-thi-tot-nghiep-thpt-nam-2024-co-so-dao-tao-phia-bac-ma-bvh/)|46446cac-45b5-4e8d-9374-b3fd83bb9b17 / `acbce18768c840d37acad823e6834df53e72437a7dfbc6f4d7d95bfebb421db3`|article/table, row ngành7340101 và7480201; TTNV header, ghi chú scale30/priority/tie, nội dung công bố kết quả19/08/2024|
|[Thông báo cutoff BVS2024](https://ptit.edu.vn/thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-theo-phuong-thuc-xet-tuyen-dua-vao-ket-qua-thi-tot-nghiep-thpt-nam-2024-co-so-dao-tao-phia-nam-ma-bvs/)|3e376892-6448-49f5-bb57-05badf3e86e5 / `60e6ca663bbb0e396e281eebdf4d7cdbabe311154bcec8e62d0c6b9e08a50084`|article/table row8 ngành7340101, TTNV header và cùng ghi chú|
|API hai thông báo gốc, id28700/28701|58ffad8b-f548-4889-b224-c8eb848f894f / `a40027d784c3969d3baab0f848fee456ff087ad3540e9ba5340f64de75b89db5`|JSON pointers /0/content/rendered và /1/content/rendered; nội dung được đọc, không chỉ search snippet|
|API liên kết đề án gốc id3432|ad16df20-bc16-48e4-96dd-80ef7e19e7b6 / `365503094048e129bf7c38400d8a1cbb40bb3d32e5b838800795cf1eff70ced3`|/3/content/rendered chứa href hai PDF host tài liệu chính thức|

Các API discovery khác là evidence tìm nguồn, không là điểm chuẩn. Private journal/accounting giữ mỗi URL/status/validators/snapshot/byte size; new-evidence.json giữ CSS cụ thể từng row/đoạn và excerpt digests. PDF pages được render/đọc trực quan, không giả OCR cell bbox. Các nguồn2024/2025/2026 đã cache trước vẫn được tái sử dụng đúng năm ô, không ghi đè.

## Đối chiếu blocker thực

| Hồ sơ THPT2024 | Dữ kiện nguồn đã đối chiếu | TTNV: literal / comparator / applicability |
|---|---|---|
|QTKD7340101/BVH|25.17; table gốc row13; historical PDF2025p10/30|TTNV<=13 / lte13 / chỉ khi bằng cutoff|
|QTKD7340101/BVS|18.40=Decimal18.4; table gốc row8; PDF2025p13/30|TTNV<=3 / lte3 / chỉ khi bằng cutoff|
|CNTT7480201/BVH|26.40=Decimal26.4; table gốc row4; PDF2025p11/30|TTNV<=5 / lte5 / chỉ khi bằng cutoff|

Header nguồn mở rộng TTNV thành **Thứ tự nguyện vọng**, nêu áp dụng khi điểm xét tuyển bằng mức điểm trúng tuyển; footnote nối quy định xử lý bằng điểm ở cuối danh sách. Không bỏ điều kiện, không dùng TTNV như gate cho mọi mức điểm. Truth tables private cho mỗi hồ sơ: dưới cutoff/rank trong hoặc ngoài biên đều vẫn dưới cutoff; bằng cutoff/rank≤N thỏa tie boundary, rank>N không thỏa; trên cutoff thì TTNV boundary không áp dụng; bằng cutoff thiếu rank là insufficient. Đây là đề xuất canonical predicate cho review, không chạy T12 hoặc khẳng định trúng tuyển/eligibility hoàn chỉnh.

**Program/Offering:** PDFp7 là danh mục ngành được phép đào tạo toàn Học viện, p20 có một hàng QTKD7340101 chung; p11–13 phân bổ theo BVH/BVS. Phương ánB đề xuất một Program dài hạn QTKD ở mức ngành/chương trình chính quy của cùng PTIT, hai Offering campus khác nhau; CNTT chuẩn có Program riêng và Offering BVH. Đây là quyết định mô hình có căn cứ, **không** khẳng định curriculum/tuition/delivery tại hai cơ sở giống nhau, không merge canonical rows đang tồn tại (hiện0). BVS proposal cũ vẫn pending; Offering được reparent bằng registry version mới nếu B được duyệt. MajorNULL; track/language unknown/UNSPECIFIED đúng biểu diễn schema, không suy MAIN/GENERAL/Chính quy từ thiếu dữ liệu. Chính quy đã có evidence. Quan hệ/aliases liên năm sau không auto kế thừa từ quyết định2024.

**Scale:** thông báo gốc và PDFp16 nêu thang30; cutoff gồm ưu tiên khu vực/đối tượng nếu có. Max30 không suy từ25.17/26.4. Đề xuất min0 dựa miền ba môn[0,10] của đặc tả§5.4 và nguyên tắc tổng3môn, tương thích DDL§4 min_score≥0/default0: tổng không âm, domain declared[0,30]. Đây là **suy luận miền kỹ thuật được trình duyệt**, không trích nguyên văn nguồn hoặc tuyên bố người có0điểm đủ điều kiện. Threshold18/22 không là scale min. Việc ghi nhận scale/basis không approve công thức/rounding/priority DSL; khả năng tính/so sánh vẫn unavailable.

**Combinations:** PDFp11–13 và p20 xác nhận QTKD A00/A01/D01, CNTT chuẩn A00/A01; p16 cùng điểm trong một ngành. Giữ một source_aggregate fact, không nhân3hoặc2facts. Membership đã có evidence mới, nhưng aggregate chưa có evaluation plan/scoring rule nên computation unavailable_aggregate_scope.

**Population:** PDFp9§1.2a vàp10§1.2c, nối A của thông báo THPT2024, hỗ trợ mapping người dự tuyển chính quy bằng kết quả THPT2024, đáp ứng đối tượng/hồ sơ và môn tổ hợp. Đề xuất canonical key riêng PTIT_THPT2024_REGULAR_VALID_APPLICANTS, không DEFAULT GENERAL; các điều kiện khác/confirmation không bị bỏ. Phạm vi B của thông báo nói tất cả phương thức không được dùng để mở rộng bảng cutoff A sang Tài năng/Kết hợp.

**Round:** đề án có planned đợt1 và bổ sung, nhưng hai thông báo gốc không gọi rõ ordinal. Không lấy round1 từ thông báo ngưỡng, lịch dự kiến hoặc suy từ không tìm thấy bổ sung. C2 đưa lựa chọn có nghĩa nguồn: round key theo chính thông báo kết quả `PTIT_THPT_2024_NOTICE_28701`/`…28700`, định nghĩa nhóm xét tuyển THPT2024 của cơ sở được thông báo19/08/2024, ordinal vẫn unknown. Đây là **đề xuất quy tắc identity cần người phụ trách duyệt**, chưa là khẳng định nguồn ghi “đợt1”; nếu nghiệp vụ yêu cầu ordinal1, còn cần văn bản nối rõ ordinal. Không dùng sentinel unknown để pass. Không tạo ReviewCommand publish chắc chắn vướng field/parents, không xem C2 đã approved.

Ngày WordPress00:00 không được biến thành thời điểm công bố có timezone; giữ publication_date metadata/date-only, source_published_at vẫn unknown nếu chưa đủ giờ. Không nhập ngày ký2025 hoặc năm trang2026 vào fact2024.

## Rà soát A và giới hạn được thực thi

DraftA cũ dùng PTIT_THPT_2024_100 dễ tạo method trùng ngữ nghĩa/mất filterTHPT, và authority chỉ year/factkind. A2 thay bằng canonical `admission_methods.code=THPT`; mã nguồn100 giữ trong `ptit:admission-method-code`, hiệu lực2024 và university binding, không thành method row khác. PTIT vẫn là khóa University nội bộ, BVH/BVS là mã nguồn/campus cùng một trường. Registry method global code và metadata nguồn phân biệt; name-only T07 vẫn có thể cần review dù đã có canonical method, không nới auto-link.

Mỗi source của A2 có `publication_bindings`: year2024, method_codeTHPT, đúng offering_code/campus trong ba hồ sơ và snapshot IDs của chính source. Publication/Core cutoff/evidence/rule validators đều kiểm context này; conversion kiểm cả hai methods. Snapshot mới hoặc Talent/Kết hợp/mã-campus khác không tự nằm trong quyền. Broad legacy sources có thể không có bindings để giữ contract cũ; **A2 không dùng đường legacy**. Không tuyên bố mọi source trong hệ thống đều đã chuyển sang policy này.

Nguồn khác host cần own snapshot và typed source_relationship gồm cached parent snapshot+locator+exact target_host trong evidence được duyệt. Parent phải official type, cùng publisher/domain với packet host và final_url đúng host. Code kiểm provenance/binding này; **ý nghĩa hyperlink và authority vẫn là trách nhiệm review nội dung**, không tự chứng minh từ tên domain hoặc reason. Hai portal/PDF host của A2 đã được đọc nội dung và đối chiếu quan hệ thật trước trình duyệt. Source authority không là fact approval, license thương mại hoặc quyền tái phân phối.

Sửa lỗi phân loại evidence: score/publication/correction chỉ nhận cutoff authority; scale/basis/aggregation nhận cutoff hoặc scoring_rule; fields metadata còn lại nhận cutoff hoặc catalog theo field. Tài liệu chỉ có scoring_rule không được duyệt score. Approval environment digest đóng băng **mọi** supporting source authority, được kiểm lại lúc publication. Source/cutoff serving guards/audit/version/idempotency giữ nguyên; không migrations, schema tables hoặc dependency mới. Implementation namespace publication/1.2.0, outputs lịch sử không sửa; policy mới có thể đòi re-review decision cũ, không silently grandfather quyền rộng.

## Lô quyết định và dependencies

Files đều private dưới state/publication/blocker-review-20261018; không source outputs/decisions/secrets trong Git.

| Quyết định | Preview và phạm vi DB nếu sau này được duyệt | Điều kiện trước apply / sau apply |
|---|---|---|
|A2, decision-a2.draft.json|Actual CLI plan read-only can_applytrue/13ops. 1University,1THPT method,1yearpartial,3aliases;7source updates;2registry/review jobs,14audit.0Program/Offering/scale/scope/cutoff/catalog delta|Người dùng duyệt đúng SHA/file; revalidate input/versions/raw/evidence/role. Dedicated reviewer apply; kiểm counts/fields/audit; cùng request replay không thêm rows|
|B1→B2→B3, typed conditional JSON|2Program,3Offering tổng; B2 dùng @Program thật củaB1, không link UUID dự kiến. Mỗi bootstrap tạo2jobs, audits theoops+review;0cutoff/version|A2 phải thực apply. Expected heads nối tuyến tính. Có schema/columns/evidence/unique-context kiểm độc lập; chưa executable/read-only plan head hiện tại còn thiếu parents. Sau apply kiểm đúng university/campus/track/language và registry|
|C1, typed conditional JSON|1scale THPT2024 min0/max30, basis_description có nhãn derivation;0scoring rule/0fact|A2/B heads thật và riêng approval domain; kiểm bounds/method/year/source/audit. Không bootstrap superuser|
|C2, scope-decisions.json|Predicate TTNV, source aggregate/population và round identity proposal để người duyệt quyết định; không có scope bootstrap độc lập trong CLI hiện có|Không thêm framework/bảng. Scope thực được tạo nguyên tử cùng D khi binding/IDs/approval hợp lệ. Round named-notice còn là lựa chọn phải duyệt|
|D1/D2/D3, recipes|Mỗi hồ sơ nếu sau này valid:1scope,1current revision1,1primary cutoff_evidence, catalog+1 và queued refresh. Field-level supporting refs giữ trong review decision, **không** giả9cutoff_evidence từ3sources|Chưa là ReviewCommand publish hợp lệ: IDs/registry/T07 outputs mới chưa tồn tại. Materialize từ IDs thật sau A/B/C, export registry và T07 namespace mới, rồi review từngD riêng, publisher apply/replay|

Mọi draft giữ upstream binding/row digests/evidence refs/expected versions/request reason và dependencies. Preview registry chứa planned IDs/metadata mô phỏng không được dùng như canonical input. Không dùng raw-only/old resolver output làm input vòng lặp. Không sửa normalizer/resolver logic để ép khớp hoặc giải phóng T06 blocked issues.

## Dữ liệu, checks và giới hạn nghiệm thu

Sau fetch:645observations,35jobs,23sources,22snapshots,23fetches. So với baseline đợt này: +10raw-fetch jobs, +12sources/+12fetches, +11snapshots (robots404khôngblob), +4runs. Hai host-state rows mới; host-state cũ thay coordination. Run4adcf376 cũ đổi cap/used/stop_reason đúng accounting; old pilot/preflight nguyên trạng. Old25jobs/645observations/11snapshots/sources cùng PK/hash không sửa. Ba packet bindings kiểm lại được; DraftA cũ đúng SHA.22raws đều khớp hash/kích thước. Canonical entities/scales/scopes/cutoffs/revisions/evidence/audit/releases vẫn0; catalog_version0. Không có approvals nhận/apply mới.

Baseline `uv run pytest -q`:512passed181.01s. Regressions ban đầu5failed/3passed cho scope/related host; basis test sau sửa import fixture1failed/1passed chứng minh quyền basis khác score. Review phát hiện conversion target và unofficial relationship parent: hai regression fail trước sửa, đã sửa kiểm cảpair và official parent/finalhost. Full run trung gian521passed/1failed do test inventory đếm profile version như trường; sửa sang unique university_key, vẫn validate mọi profile. Test canonical method ban đầu kỳ vọng name-only auto-link đã sai policyT07; sửa kỳ vọng giữ canonical candidate/review, không đổi resolver để pass.

Code reviewer agent đã đọc diff/callers, kiểm lại hai findings được xử lý; không findings mới trong phạm vi, không chạy tests/raw/credentials/network hoặc duyệt nghiệp vụ. Các checks cuối và exact-SHA CI được ghi bổ sung trong bàn giao sau khi chạy; không suy từ local hoặc số tests. Health/live vàready HTTP200, PostgreSQL0003head. Dedicated roles được kết nối read-only kiểm capability/flags/noDELETE, credentials/.env không sửa.

Mốc tiếp theo là approval đúng A2, rồi các quyết định phụ thuộc; không áp dụng chỉ vì prompt tiếp tục. Khi có lô canonical nhỏ verified/current/published và replay/audit/catalog/outbox được kiểm chứng mới chuyển triển khai T09 releasepilot có manifest/coverage/checksum/count SQL=export; T10 bắt đầu trên release ổn định song song mở rộng. Chưa nghiệm thu20.000, toànT08/T09 hoặc Phase1. Không triển khai T09/T10/T12 trong đợt này.


### Kết quả kiểm chứng cuối trước commit

- `uv run pytest -q`: **525passed190.68s**, không Internet, DBtest riêng. Baseline512passed; checks mới xuất phát từ authority defects, canonicalTHPT và review findings, không dùng số tests như tiến độ.
- `uv run ruff check .`, `uv run ruff format --check .`: pass (126files); `uv run mypy`: pass55sourcefiles; `uv lock --check`:87packages/unchanged.
- `uv run alembic current`:0003_publication(head); `uv run alembic check`:no new upgrade operations. Không chạy migration mới hoặc sửa0001/0002/0003.
- A2 actual dedicated-reviewer CLI plan:preview_only/can_applytrue,13ops. B/C conditional schema/required columns/source snapshots kiểm độc lập; chưa executable do missing real parents/heads, không giả apply/replay trên pilot.
- Raw22blobs/hash/size, baT07packet digests, originalDraftA hash và old application rows đều kiểm lại; exceptions operational crawl_runs/host coordination được thống kê ở trên. Live/ready200, roles đọc-only đúng/noDELETE.
- Bốn SourceProfiles mới qua schema; kiểm kê distinct university_key thay vì cộng mỗi profile version như trường mới. `git diff --check` pass; staged secret/path audit và exact-SHA CI được kiểm ở bước Git, kết quả cụ thể trong bàn giao.

A2 review file SHA-256: `b032e83495c619177c3aa22442f79fefc2c0405f0d4000ba70db6bbad41863fd`. Scope/operations described above; approval applies only to this exact version.

## Cập nhật: A2 được duyệt và apply, B1 chờ duyệt riêng

Các mục trước ghi lại đợt chuẩn bị tại commit c22ea79, khi chưa có approval. Sau đó người dùng đã phê duyệt nghiệp vụ riêng A2 đúng file/hash phía trên và request `95b1d889-09d3-40e2-8d17-1063e4a73e7a`. Approval chỉ identities/authority; không cấp quyền tái phân phối hoặc duyệt B/C/D. Không sửa bytes/reason của A2, migrations, code hay outputs T05–T07.

Ngay trước apply đã kiểm lại SHA, request, packet binding, expected registry/alias heads, raw checksum/size, schema0003head và reviewer capability. Actor thực là `db:eduradar_dev_reviewer`, không superuser/CREATEROLE/CREATEDB/BYPASSRLS. CLI plan vẫn preview_only/can_apply=true,13operations,catalog delta0. Apply chạy qua CLI/ReviewService với transaction/audit hiện có, không ghi SQL nghiệp vụ thủ công.

| Tác động | Expected | Actual sau apply |
|---|---|---|
| University / method / admission-year partial / aliases | +1/+1/+1/+3 | +1/+1/+1/+3 |
| Sources |7updates,0new|7updates,0new; university/verified/authority_scope đúng draft, các cột khác giữ nguyên |
| Jobs / audit |+2/+14|35→37jobs;0→14audit, đúng request/actor |
| Program / Offering / scale / scope / cutoff / evidence / release |0new|Tất cả vẫn0 |
| Catalog dataset_version |0delta|0→0 |

Một University PTIT dùng khóa nội bộ; chỉ một canonical method THPT. Registry giữ mã nguồn100 trong hệ `ptit:admission-method-code`, PTIT/2024; BVH/BVS vẫn là context Offering proposals của cùng trường, chưa là canonical Offering. Bảy source authority khớp nguyên publication_bindings đã duyệt, không mở rộng năm/method/offering/campus/snapshot. Source authority không tự duyệt fact hoặc scoring rule.

IDs đã tồn tại trong DB:

- Review decision: `426241ec-ba2c-5923-9e96-1e8461d571b3`.
- Registry manifest job: `0f12e947-9355-4bc2-8a05-309474c2415f`.
- University: `d7bfe9d8-6f23-57a8-bc41-b3caa7ea2f07`; THPT method: `d391066d-0c18-579e-82fb-4398b1f9cd30`.
- Admission-year partial2024 dùng khóa ghép `(university_id=d7bfe9d8-6f23-57a8-bc41-b3caa7ea2f07, admission_year=2024)`, không có cột UUID id. UUID operation trong CLI/audit không phải canonical ID của hàng admission_years.
- Registry/alias heads: `registry/ptit-identities-authority/20261018-r2`, `aliases/ptit-identities-authority/20261018-r2`.

Chạy lại cùng A2 bằng **apply --file**, không dùng publication replay: result giống hệt; row digests của cả34tables, jobs/audit/version không đổi. Đối chiếu baseline trước apply: mọi hàng cũ giữ nguyên ngoài đúng7source updates được duyệt;645observations/35jobs cũ/22snapshots không sửa hoặc xóa.22raws vẫn khớp hash/kích thước;221tệp lịch sử private được kiểm nguyên digest. Không fetch, resume crawl, thay cap hoặc chạy T07 mới.

Export CLI từ registry manifest thật thành private `state/publication/a2-approved-20261018/registry-a2-applied.json`; registry digest khớp manifest và validate_targets khớp canonical DB. Không dùng preview registry. Checkpoints trước/sau, apply result, replay proof và B1 nằm trong cùng thư mục ignored, không đưa vào Git.

### B1 đã materialize, chưa được duyệt/apply

Draft mới giữ conditional B1 cũ nguyên bytes, có request mới và parent University thật; expected heads đúng A2. File: `state/publication/a2-approved-20261018/decision-b1.draft.json`; SHA-256 `932a5f3c215e816916fba4e79241fe5d90f6c6c913b7deecd3b1adb3be7482ea`; request `23977c8a-d4f5-4b56-a1cc-9040d843167a`.

Đề nghị tạo **một Program QTKD cấp Học viện**, canonical_key nội bộ `ptit-regular-7340101`, và **một Offering BVH/2024/mã7340101**. Evidence giữ snapshot PDF2024 `f31d55ba-cbc7-42e0-9a02-c5a7c285abc3`, p12/p20; đây là đối chiếu trực quan đã ghi nhận, không OCR. Program ở mức danh mục chính quy của Học viện, không khẳng định curriculum/tuition hai cơ sở giống nhau; việc thêm Offering BVS vẫn cần B2 riêng. MajorNULL, track/language unknown biểu diễn UNSPECIFIED trong schema và null trong registry; Chính quy có evidence.

Plan bằng dedicated reviewer: preview_only/can_apply=true,2operations,catalog delta0. Prechecks read-only kiểm parent year2024 thật, registry targets, mandatory columns, chưa trùng program/offering business keys, source catalog authority đúng context/snapshot và registry version đích chưa dùng. Đây không phải mô phỏng đầy đủ SQL insert hoặc approval. Nếu được duyệt/apply sau revalidation, expected +1Program/+1Offering/+2jobs/+3audit,0cutoff/0catalog delta; Offering ref Program tạo trong cùng transaction. UUID trong plan chưa tồn tại và không được trình như canonical IDs thật.

B2/B3/C còn conditional; D recipes chưa có IDs/binding T07 mới. Không kế thừa approval A2. Sau B/C được duyệt/apply mới export và chạy T07 version mới, materialize từng D rồi review/publish riêng. Chỉ đề xuất T09 khi có lô canonical thật đã kiểm chứng; vẫn chưa nghiệm thu toànT07/T08/Phase1 hoặc quota20.000.

Health/live vàready kiểm qua ASGI TestClient với DB hiện tại đều200; cổng HTTP8000 chưa kết nối được ở lượt kiểm trước, không báo là server đang chạy. Không thay implementation/dependencies/schema nên không có regression code mới cần viết.

Checks chạy mới trong lượt apply: `uv run pytest -q` **525passed183.28s**, fixtures dùng database test riêng; `uv run ruff check .` pass; `uv run ruff format --check .` pass128files; `uv run mypy` pass55sourcefiles; `uv lock --check`87packages, lockfile không đổi; `uv run alembic current`0003head; `uv run alembic check`no new upgrade operations; `git diff --check`pass. Không thêm tests/envelopes để tăng số lượng. Staged chỉ ba tài liệu vận hành, không credentials/raw/private decisions; exact-SHA push/CI được kiểm và ghi trong bàn giao.

## Cập nhật: B1 đã được duyệt/apply, B2 chờ duyệt riêng

Điểm xuất phát lượt này: commit07ad75a25684b55a98def7f55fa9299949812dcf, nhánh/origin đúng, chỉ .vscode/ chưa tracked. Các mục A2/B1 phía trên là hồ sơ lịch sử của lượt trước. Người dùng đã duyệt riêng B1 đúng SHA `932a5f3c215e816916fba4e79241fe5d90f6c6c913b7deecd3b1adb3be7482ea`, request `23977c8a-d4f5-4b56-a1cc-9040d843167a`; không duyệt B2/B3/C/D. File/reason đã được duyệt giữ nguyên bytes.

Đã kiểm lại provenance đặc tả, schema0003head, packet/binding/expected registry và alias heads, University ID/manifest A2 thật, dedicated reviewer không privileged/không member publisher. Raw PDF2024 snapshotf31d55ba-cbc7-42e0-9a02-c5a7c285abc3 khớp SHA1b1e3741108ce5711bc61823200d4acaa534082a70b769894ec61d28fbb167c3 và byte size; render mới từ raw và đọc trực quan p11/p12/p13/p20, không OCR hoặc HTTP. BVH header ởp11 nối bảng sangp12: QTKD7340101 row12; p20 danh mục chung row13. BVS có header riêng và QTKD7340101 row8 ởp13. Không suy curriculum/tuition hai cơ sở bằng nhau từ danh mục này.

| Tác động B1 | Expected | Actual |
|---|---|---|
| Program / Offering |+1/+1|0→1Program;0→1Offering BVH2024; không có BVS |
| Quan hệ/context |PTIT→QTKD→BVH2024/7340101|Đúng parent IDs, năm/mã/campus và business unique keys |
| Trường chưa biết |MajorNULL,track/language unknown|MajorNULL; DB UNSPECIFIED, registry null; không suy MAIN/GENERAL |
| Jobs / audit |+2/+3|37→39jobs;14→17audit, đúng request/reason/actor/evidence |
| Scale/scope/cutoff/evidence/releases |0new|Tất cả vẫn0 |
| Catalog dataset_version |0delta|0→0 |

Apply chỉ dùng CLI/ReviewService bằng `db:eduradar_dev_reviewer`, không SQL nghiệp vụ thủ công/superuser hoặc thay architecture/code/migration. Actual decision `684a8f28-1faa-54d9-a57a-cfca85820cc2`; registry manifest job `bd0c37a0-0036-432a-9391-c5e451a4dc21`; Program QTKD `cf5b839c-2c74-57b2-a97c-6bb563edbbf6`; Offering BVH `b957f9b2-ec7b-5f3f-b8ee-c1f3e9b1cf3e`; University giữ ID `d7bfe9d8-6f23-57a8-bc41-b3caa7ea2f07`. Registry head `registry/ptit-programs/20261018-b1`; alias head giữ `aliases/ptit-identities-authority/20261018-r2`. Canonical registry targets/provenance/parent/unknown metadata khớp DB.

Gọi lại cùng bootstrap request bằng **apply --file** trả result giống hệt; cả34tables/rows/jobs/audit/version không đổi. Đối chiếu trước/sau B1: mọi rows đã có, gồm645observations/37jobs/22snapshots và7source authorities A2, giữ nguyên digest;22raws khớp checksum/size;238tệp lịch sử private giữ nguyên. Chỉ thêm đúng hai canonical rows/hai jobs/ba audits được duyệt. Export CLI từ manifest thật thành private `state/publication/b1-approved-20261018/registry-b1-applied.json`, digest khớp manifest; không dùng preview registry. Không resume crawl, thay budget, fetch hoặc rerun T07.

### B2 đã materialize, chưa được duyệt/apply

File private `state/publication/b1-approved-20261018/decision-b2.draft.json`; SHA `563d6a93777d4e7c205ce42f917871dfa50333a39d420b758e58061a4f5ed5a0`; request `f59e9c89-a7dd-40a7-8038-5b19f612f6fb`. Giữ nguyên conditional draft cũ, dùng request mới, Program/University IDs và registry/alias heads thật từ B1. Packet BVS được kiểm riêng, không dùng packet BVH để bypass context.

Đề nghị **chỉ tạo Offering QTKD BVS/2024/mã7340101**, thuộc Program QTKD thật từ B1; không tạo Program mới. Track/language vẫn unknown theo biểu diễn schema/registry; không merge Offering BVH/BVS. Evidence riêng p13 row8/header BVS vàp20 row13 của PDF cache trên. B1 approval không tự duyệt Offering BVS hoặc sự tương đương curriculum. Plan dedicated reviewer read-only: can_apply/preview_only=true,1operation,catalog delta0. Prechecks kiểm parent Program cùng University, year2024, các trường bắt buộc, unique key chưa trùng và source catalog authority đúng BVS/snapshot. Không giả lập toàn bộ SQL insert.

Nếu sau này người dùng duyệt và revalidate còn hợp lệ: expected **+1Offering/+2jobs/+2audit**,0Program/scale/scope/cutoff/release/dataset delta. New registry dự kiến `registry/ptit-programs/20261018-b2`, alias không đổi. IDs trong plan chưa tồn tại; chỉ dùng IDs đã apply của B1 làm parents. Chưa apply B2/B3/C/D hoặc T09. Sau các bootstrap được duyệt mới export/T07 mới rồi materialize D theo binding thật và review từng fact. Phase1/T07/T08 chưa được đánh dấu hoàn tất.

Checks mới của lượt B1: `uv run pytest -q tests/publication tests/integration/test_health.py tests/integration/test_health_schema.py`: **62passed109.61s**, database test riêng. Không chạy lại toàn bộ pytest local vì không đổi code; con số525 của lượt A2 là lịch sử, CI trên commit tài liệu mới được kiểm riêng khi bàn giao. Ruff check/format128files, mypy55sourcefiles, uv lock87packages, Alembic current0003head/check no new operations và git diff --check đều pass. ASGI health/live vàready200 với DB thật; HTTP8000 chưa kết nối được. Sau tests,34tables vẫn đúng trạng thái sau B1; reviewer vẫn không privileged/không publisher/không DELETE Offering. Chỉ cập nhật tài liệu vận hành tracked, private decisions/raw/exports/credentials và .vscode/ không stage.

## Cập nhật: B2 đã được duyệt/apply, B3 chờ duyệt riêng

Điểm xuất phát: commit9b90fd2e2771c5c92d672f2867a29936fa20cbd8, đúng nhánh/origin, chỉ .vscode/ chưa tracked. Các mục trước là hồ sơ lịch sử. Người dùng duyệt riêng exact B2 file/hash `563d6a93777d4e7c205ce42f917871dfa50333a39d420b758e58061a4f5ed5a0`, request `f59e9c89-a7dd-40a7-8038-5b19f612f6fb`; không duyệt B3/C/D. Không sửa bytes/reason của B2.

Trước apply: checked_packet/expected registryB1 và aliasr2, Program QTKD/University IDs thật, schema0003head và dedicated reviewer không privileged/không publisher đều hợp lệ. PDF snapshotf31d55ba-cbc7-42e0-9a02-c5a7c285abc3 khớp SHA1b1e3741108ce5711bc61823200d4acaa534082a70b769894ec61d28fbb167c3/size; render lại và đọc p13 header BVS/QTKDrow8, p20row13. Không OCR/download mới. CLI plan vẫn1operation/can_applytrue/catalogdelta0.

| Tác động B2 | Expected | Actual |
|---|---|---|
| Program / Offering |0/+1|Program giữ1; Offering1→2, chỉ thêm BVS2024/7340101 |
| Parents/context |PTIT→Program QTKD thật→BVS2024|Đúng University/Program/năm/mã/campus; unique key không trùng BVH |
| Track/language |unknown|DB UNSPECIFIED/registry null; không suy mặc định |
| Jobs / audit |+2/+2|39→41jobs;17→19audit, đúng request/reason/actor/evidence |
| Scale/scope/cutoff/evidence/releases |0new|Tất cả vẫn0 |
| Catalog dataset_version |0delta|0→0 |

Apply chỉ qua CLI/ReviewService bằng dedicated reviewer. Actual decision `be5546cf-4562-5d9b-8ac5-6326aad319b0`; registry manifest `8baaa2cc-a703-4563-b6a3-f4c04dea58f3`; Offering BVS `257a579f-e7a6-5a6b-8fd4-8a43f9d74ecb`. Program giữ `cf5b839c-2c74-57b2-a97c-6bb563edbbf6`, University giữ `d7bfe9d8-6f23-57a8-bc41-b3caa7ea2f07`; Offering BVH `b957f9b2-ec7b-5f3f-b8ee-c1f3e9b1cf3e` giữ nguyên toàn row digest. Registry head `registry/ptit-programs/20261018-b2`; alias giữ `aliases/ptit-identities-authority/20261018-r2`. Export CLI thật `state/publication/b2-approved-20261018/registry-b2-applied.json` khớp manifest digest/validate_targets.

Gọi lại cùng bootstrap request qua **apply --file** trả result cũ; cả34tables/rows/jobs/audit/version không đổi. Mọi rows có trước B2 gồm645observations/39jobs/22snapshots/sources/A2/B1 entities giữ digest;260tệp lịch sử private nguyên checksum,22raws nguyên hash/size. Chỉ thêm đúng1Offering/2jobs/2audit. Không đổi crawler runs/budgets, không tải nguồn, không chạy T07 mới hoặc tạo script vận hành/framework/code/migration.

### B3 đã materialize, chưa được duyệt/apply

File private `state/publication/b2-approved-20261018/decision-b3.draft.json`; SHA `1bb13962fc2b97e9eb46dec44be2dbfb3fa4dafa8cf0b93ed1447bf0a69ef578`; request `c9e0bdad-e392-49e4-8d2c-0bb23cd3413f`. Bản conditional cũ giữ nguyên. Draft mới có University ID/head thật sau B2; Program/Offering mới còn proposal/ref trong cùng transaction, không dùng preview UUID như canonical ID.

Đề nghị **một Program CNTT cấp PTIT**, canonical_key nội bộ `ptit-regular-7480201`, MajorNULL, và **một Offering BVH/2024/mã7480201**. Track/language unknown (UNSPECIFIED trong DB/null trong registry); Chính quy theo evidence. PDFp11 có header BVH vàrow4 tên CNTT/mã7480201, p20row5 xác nhận tên/mã. Đối chiếu p12/p20 tách7480201_UDU (định hướng ứng dụng),7480201_CLC (chất lượng cao),7480201_LK (liên kết quốc tế). Ghi chúp13 nói Việt–Nhật là chương trình dự kiến có thông báo bổ sung; không lấy ghi chú đó để gán mã hoặc nhập vào B3. “CNTT chuẩn” trong bàn giao chỉ bản ghi tên/mã không hậu tố, không suy track STANDARD hoặc taxonomy/major.

Actual CLI plan dedicated reviewer read-only can_apply/preview_only=true,2operations,catalogdelta0. Prechecks parent year/University, mandatory columns, program/offering unique keys chưa trùng, packet CNTT và source catalog authority đúng7480201/BVH/snapshot đã đạt; không giả mô phỏng toàn bộ SQL insert. Nếu được duyệt và revalidate còn hợp lệ: **+1Program/+1Offering/+2jobs/+3audit**,0scale/scope/cutoff/release/datasetdelta. New registry dự kiến `registry/ptit-programs/20261018-b3`, alias giữ nguyên. C/D chưa approval; sau bootstrap được duyệt mới export/T07 mới và materialize từngD. Chưa chuyển T09, chưa nghiệm thu toànT07/T08/Phase1 hoặc quota20.000.

Checks mới lượt B2: `uv run pytest -q tests/publication tests/integration/test_health.py tests/integration/test_health_schema.py`: **62passed126.12s**, DB test riêng. Không thay code nên không chạy full pytest local; CI trên SHA mới được kiểm riêng. Ruff check/format128files, mypy55sourcefiles, uv lock87packages, Alembic current0003head/check no new operations và git diff --check đều pass. ASGI health/live vàready200 với DB thật; HTTP8000 chưa kết nối. Sau tests,34tables/old row digests vẫn đúng sau B2; reviewer không privileged/không publisher/không DELETE Offering. Chỉ stage tài liệu vận hành; private decisions/exports/raw/credentials và .vscode/ giữ ngoài commit.

## Cập nhật: B3 đã duyệt/apply, C1/C2 chờ duyệt riêng

Điểm xuất phát commitc5ff6d0563fe09b6a313d3c15622e801cd1ec538; nhánh/origin đúng, chỉ .vscode/ chưa tracked. Người dùng duyệt riêng exact B3 SHA `1bb13962fc2b97e9eb46dec44be2dbfb3fa4dafa8cf0b93ed1447bf0a69ef578`, request `c9e0bdad-e392-49e4-8d2c-0bb23cd3413f`; không duyệt C/D. Giữ nguyên file/reason đã duyệt. Revalidate packet/expected B2head/aliasr2, University, schema0003head và dedicated reviewer không privileged/không publisher ngay trước apply. PDF snapshotf31d55ba-cbc7-42e0-9a02-c5a7c285abc3 khớp hash/size; đọc lạip11/p20 và đối chiếu CLC/UDU/LK/Việt–Nhật ởp12/p13, không suy track chuẩn.

| B3 | Expected | Actual |
|---|---|---|
| Program / Offering |+1/+1|1→2Program;2→3Offering, chỉ CNTT BVH2024/7480201 không hậu tố |
| Major/track/language |unknown|MajorNULL, DB UNSPECIFIED/registry null, đúng parents và unique keys |
| Jobs / audit |+2/+3|41→43jobs;19→22audit, đúng request/reason/evidence/actor |
| Scales/scopes/cutoffs/releases |0new|Tất cả vẫn0 |
| Dataset version |0delta|0→0 |

Actual decision `4c2eb582-b43a-51a6-bbad-5cb2c137a116`; registry manifest `c4420433-a883-4ca7-8f0f-9d90b37ed0c5`; Program CNTT `c5423f44-3ffd-5c2f-91b0-e96bea3464bb`; Offering CNTT BVH `659f29e9-911c-5db9-9af1-cdbef363df82`. University PTIT giữ `d7bfe9d8-6f23-57a8-bc41-b3caa7ea2f07`. Registry head `registry/ptit-programs/20261018-b3`, alias `aliases/ptit-identities-authority/20261018-r2`; export CLI thật tại private `state/publication/b3-approved-20261018/registry-b3-applied.json`, digest/targets khớp manifest/DB.

Gọi lại bootstrap cùng **apply --file** trả result cũ; cả34tables/jobs/audit/version không đổi. Mọi rows có trước B3, gồm hai Offering/Program QTKD,645observations/41jobs/22snapshots/sources, giữ row digests.282tệp lịch sử private và22raws khớp checksum/size. Chỉ thêm hai canonical rows/hai jobs/ba audit đã duyệt. Không tải nguồn/resume crawl, không chạy T07 mới, không sửa code/migrations hoặc tạo script vận hành mới.

### C1 materialized bằng method, Offering IDs và head thật — chưa approval/apply

File private `state/publication/b3-approved-20261018/decision-c1.draft.json`; SHA `3c59223370b303878c4cacf88bdcfaf4f448e38f8c75adf5cfa45b815ef3197e`; request `7025e964-946c-447f-a0a1-12c64e165587`. Expected registryB3/aliasr2 thật; canonical methodTHPT ID `d391066d-0c18-579e-82fb-4398b1f9cd30`; packet QTKD BVH checked độc lập. New registry dự kiến `registry/ptit-scale/20261018-c1`. Conditional C1 cũ giữ nguyên; draft mới thay symbolic method ref bằng ID thật, primary snapshot từ HTML anchor sang originalPDFp16, bổ sung precise priority evidence và ba Offering IDs trong reason/basis_description. Đây chưa phải file được duyệt.

- **Max30:** PDF2024 snapshotf31d55ba… SHA1b1e3741108ce5711bc61823200d4acaa534082a70b769894ec61d28fbb167c3, locatorpdf:p16, đoạn b)Đối với Phương thức2 nêu ba môn trên thang10, tổng tối đa30. Đã render/đọc trực quan từ raw đúng hash/size; không suy30 từ giá trị cutoff.
- **Min0:** derivation miền kỹ thuật từ inputs môn[0,10] ở đặc tả§5.4 (bảnSHAc3745329…) và tổng ba môn không âm, tương thích DDLmin_score≥0. Không trích nguồn ghi “min_score=0”, không dùng ngưỡng18/22 hoặc khẳng định điểm0 đủ điều kiện. Đây là quyết định domain cần người dùng duyệt.
- **Basis đã gồm ưu tiên:** hai thông báo gốc BVH snapshot46446cac… SHAacbce18768c840d37acad823e6834df53e72437a7dfbc6f4d7d95bfebb421db3 và BVS snapshot3e376892… SHA60e6ca663bbb0e396e281eebdf4d7cdbabe311154bcec8e62d0c6b9e08a50084 có note điểm đã gồm ưu tiên Khu vực/Đối tượng nếu có. CSS locators và text digests được reselect/kiểm trong private c1-notice-evidence.json và executable draft, không chỉ URL. Không phê duyệt công thức ưu tiên, rounding hoặc scoring DSL.

Phạm vi C1 đề nghị duyệt là ba Offering2024 thật: QTKD/BVH `b957f9b2-ec7b-5f3f-b8ee-c1f3e9b1cf3e`, QTKD/BVS `257a579f-e7a6-5a6b-8fd4-8a43f9d74ecb`, CNTT/BVH `659f29e9-911c-5db9-9af1-cdbef363df82`. Đã kiểm source scoring_rule authority của primaryPDF đúng ba context và snapshot. **Schema scale khóa method/year, không có Offering membership FK**; IDs nằm trong command/basis_description không tự thành validator membership mới. Publication còn cần active reviewed scale, same method/year/bounds, scoped source authority và review C2/D riêng. Không tuyên bố C1 tạo permission publish hoặc enforce riêng exact ba UUID bằng SQL.

Plan reviewer read-only can_apply/preview_only=true,1operation,0catalogdelta; bắt buộc/FK method/snapshot/NUMERIC bounds/business unique key/version đích và authority đã kiểm độc lập. Không giả mô phỏng toàn SQL insert. Nếu duyệt/apply sau revalidation: **+1score_scale/+2jobs/+2audit**,0scoring_rule/scope/cutoff/release/datasetdelta. Scale không là entity type riêng trong T07 registry: row ởscore_scales, provenance qua review/audit; registry manifest mới giữ entities đã duyệt và version mới, không giả scale đã resolve.

### C2 còn cần duyệt trước publication

| Trường | Proposal có evidence, chưa approval | Phần cần quyết định |
|---|---|---|
| Round |Named notice28701 cho BVH,28700 cho BVS; scope đúng thông báo kết quả2024|Chấp nhận identity theo thông báo hoặc cung cấp căn cứ ordinal; ordinal vẫnunknown, không gọi đợt1 |
| Population |PTIT_THPT2024_REGULAR_VALID_APPLICANTS: đối tượng/hồ sơ theo PDFp9§1.2a và thi môn tổ hợp THPT2024 theo p10§1.2c|Duyệt mapping cụ thể, không GENERAL/empty conditions |
| Tổ hợp |source_aggregate: QTKD A00/A01/D01, CNTT A00/A01; PDFp16 cùng điểm trong ngành vàp20 membership|Một fact aggregate/Offering, không nhân tổ hợp; chưa tính/so sánh được |
| TTNV |Literal≤13 QTKD/BVH,≤3 QTKD/BVS,≤5 CNTT/BVH; comparatorlte, applies_when score==cutoff theo header/footnote gốc|Chỉ tie boundary: dưới cutoff vẫn dưới, trên cutoff không áp TTNV, bằng thiếu TTNV là insufficient; không chạy evaluatorT12 |

Private c2-pending-decisions.json giữ nguyên proposals với approvalfalse, không actor/decision giả hoặc canonical scope mới. C1 approval nếu có không duyệt C2 hay ba cutoffs. Sau C được duyệt/apply phù hợp mới export/T07 namespace mới trên T06 input, materialize D riêng bằng IDs/bindings thật; chưa T09 hoặc nghiệm thu toànT07/T08/Phase1/quota20.000.

Checks local mới:62tests publication/health passed108.51s trên DB test riêng; Ruff check/format128files, mypy55sourcefiles, lock87packages, Alembic current0003head/check và diff checks đạt. Không đổi code nên không chạy full pytest local; CI trên SHA tài liệu mới được kiểm riêng khi bàn giao. ASGI live/ready200 với DB thật; HTTP8000 chưa kết nối. Sau tests,34tables đúng trạng thái B3, reviewer vẫn không privileged/publisher/DELETE. Chỉ tài liệu vận hành tracked thay đổi; secrets/raw/private decisions/exports và .vscode/ không stage.

## Cập nhật: C1 đã apply; T07 namespace mới; C2/D chỉ preview

Baseline lượt này: commit0ba67cba9b335443456fcda55d59d3d836d38d6f, đúng nhánh/origin, chỉ .vscode/ chưa tracked. Người dùng duyệt riêng exact C1 SHA `3c59223370b303878c4cacf88bdcfaf4f448e38f8c75adf5cfa45b815ef3197e`, request `7025e964-946c-447f-a0a1-12c64e165587`; không duyệt C2/D. Không sửa bytes/reason của C1. Đã kiểm heads từ actual B3manifest, packet/method,3evidence snapshots/checksum/locators, Decimal0/30, basis/schema0003head và dedicated reviewer không privileged/không publisher ngay trước apply.

| Giai đoạn | Expected | Actual |
|---|---|---|
| Bootstrap C1 |+1scale/+2jobs/+2audit,0observations|Scale0→1,jobs43→45,audit22→24,observations645 giữ nguyên |
| C1 ngoài phạm vi |Program/Offering2/3,0rules/scopes/cutoffs/releases/catalogdelta|Đúng; min/max NUMERIC0.00000/30.00000, từng field/basis/primary snapshot đúng draft |
| Bootstrap replay |Không thêm rows/jobs/audit/version|Cùng apply --file trả result cũ;34tables giữ nguyên |
| T07 riêng |Run offline trên215T06envelopes, old outputs giữ nguyên|+215resolution observations/+1job; observations645→860,jobs45→46,audit24 giữ nguyên |
| T07 replay |0insert, không thêm job|cachedtrue/inserted0;34tables giữ nguyên |

Scale ID `76ea9a26-6e77-594c-94f7-fae053e0c148`; C1decision `b1df9c1b-6b87-5fdd-90a6-5b7e1ecdb650`; registry manifest `15dab0fb-8dc6-464e-8a5f-a0de4d855c87`. MethodTHPT giữ IDd391066d-0c18-579e-82fb-4398b1f9cd30; scale year2024/codePTIT_THPT_SUM30_2024/exam_versionTHPT2024; primary snapshotf31d55ba-cbc7-42e0-9a02-c5a7c285abc3. Registry export CLI thật ở private `state/publication/c1-approved-20261018/registry-c1-applied.json`, head `registry/ptit-scale/20261018-c1`, alias `aliases/ptit-identities-authority/20261018-r2`; digest/targets khớp actual manifest/DB.

T07job `75f10ef6-57a1-4fb2-a331-ec6334912819`, input T06job7bc439bf-a6d7-4beb-bf03-bb47956c5383. Namespace `resolution/1;resolver/1.0.0;registry/ptit-scale/20261018-c1;aliases/ptit-identities-authority/20261018-r2;input=9d6bd3816f4d1aac2ddd9ddc1fcdc252f0a33290a384a07e4212f42e135b28e4`. Resolver/config/lock không thay; git at execution0ba67cb, dirty do .vscode/ chưa tracked, ghi thật trong manifest.215inputs/95candidates,91partial/4ambiguous/0eligible; university95resolved, major95unresolved, program91unresolved/4ambiguous, offering/method/scope95unresolved.118T06blocked attempts giữ nguyên. T08 contract kiểm approved registry/field review độc lập với trạng thái tổng T07; preview không sửa resolver hoặc giả các candidates đã resolved.

Mọi rows có trước C1 gồm645observations/43jobs/canonical A–B/sources/snapshots giữ row digests;308tệp lịch sử và22raws nguyên checksum/size. Chỉ mutations C1/T07 ở bảng trên. Không tải nguồn, đổi crawl runs/budgets, scoring/evaluator, migration hoặc code/script vận hành mới. Tổng hiện860observations/46jobs/24audit,2Program/3Offering/1scale; scoring_rules/scopes/cutoffs/evidence/releases0, catalog0. Database không có approval publish nào.

### Gói C2 và ba D previews bằng bindings thật — chưa approval

Private C2file `state/publication/c1-approved-20261018/decision-c2.packet.json`, SHA `335f124fd2da7261e9e5b0c4ed8505b2001a39c897bc850c2d67e3d0595a840d`, request `b72d93e4-d0a8-4cac-b166-84e23ddd87c4`. Gói chứa scale/Offering IDs thật, registry/alias heads, T07job/namespace, row digests, environment digests và ba command hashes/bindings. Không có actor/chữ ký/approval giả. C2 approval đơn lẻ có0DBmutations, không invent CLI bootstrap scope; scope chỉ được publisher tạo khi D hợp lệ sau approval riêng.

Scope proposal giữ named notices28701(BVH)/28700(BVS), ordinalunknown, không đợt1; populationPTIT_THPT2024_REGULAR_VALID_APPLICANTS theo PDFp9/p10; source_aggregate QTKD A00/A01/D01 và CNTT A00/A01 theo PDFp16/p20. TTNV≤13/3/5 chỉ khi score==cutoff; bằng thiếu preference_order phải insufficient_input, không mặc định thỏa. Gói giữ boundary semantics/truth table là đề nghị review, chưa evaluatorT12; computation cả baD là unavailable_aggregate_scope. Source literal/row/header/priority locators được reselect từ raw HTML đúng hash, thêm exact row text digest cho từng fact trong C2packet.

| Draft private | Request | File SHA-256 | Fact / binding T07 mới |
|---|---|---|---|
|decision-d1.draft.json|fd4490e7-845d-4829-b62b-291650dd497c|09da357722b73968371904b8b5e37b54e467ead9fedef6b61f79380513361ac9|QTKD/BVH25.17,TTNV≤13; resolution4479f158-62b5-4955-b0fe-f8ceffc29f44 |
|decision-d2.draft.json|4580ff33-33d7-49b3-a972-6ebcc26b7519|7b96d14a30dabcb6c7b33e8d0b771797616b110d205b60e575e70151460cd51e|QTKD/BVS18.4,TTNV≤3; resolution68bd322c-3811-4445-8a87-c2e41db4591c |
|decision-d3.draft.json|8248f122-8389-43d1-a379-f20005b6095e|8c72b5095b32abe2d941831ea9f7d1b51d318b5764e163a955abd173b0161ddc|CNTT/BVH26.4,TTNV≤5; resolution8032958a-61fa-4515-84a4-c20a9ff219d9 |

Files cùng thư mục C2; full candidate keys/packet SHA/evidence và actual CLI plans trong packets/drafts/readiness. Tất cả plan dedicated reviewer preview_only/can_applytrue, không approval/apply. Nếu một D sau này được duyệt: review phase dự kiến+1reviewjob/+1audit, chưa cutoff/catalog; first publisher phase khi vẫn mới dự kiến+1scope/+1current cutoff revision1/+1primary cutoff_evidence/+1validated observation/+2jobs(publication_request+refresh)/+3audit/catalog+1. Field-level supporting refs không được đếm thành nhiều cutoff_evidence rows. C2 một mình không tạo ba scopes; mỗi D cần quyết định riêng, replay/current/evidence/catalog/outbox còn phải kiểm thực tế khi có quyền. Không triển khai T09 chỉ vì preview đạt.

Checks mới: `uv run pytest -q tests/publication tests/resolution tests/integration/test_health.py tests/integration/test_health_schema.py`:374passed114.31s trên DB test riêng; Ruff check/format128files, mypy55sourcefiles, lock87packages, Alembic current0003head/check và diff checks đạt. ASGI live/ready200 với DB thật; HTTP8000 chưa kết nối. Không đổi code, không chạy full pytest local; exact-SHA CI tài liệu mới kiểm riêng khi bàn giao. Một lỗi serialization ở dòng in kết quả của wrapper private sau khi cả3CLIplans đã thành công không thay DB hoặc drafts; gói C2 cuối dùng bindings JSON từ ReviewCommand đã kiểm hash/schema. Không giả lỗi ứng dụng để sửa code hoặc tăng tests.

## Cập nhật: C2 và D1–D3 đã duyệt riêng; publication pilot thật

C2 được duyệt đúng packet/hash/request, chỉ ghi private record,0DBwrites. Sau approval riêng từng D, đã revalidate/apply bằng reviewer và publisher CLI riêng tuần tự, giữ original draft bytes/reason. Ba scopes/current verified published cutoffs revision1 đã được kiểm từng field, evidence/lineage/fingerprints và transaction/catalog/refresh. Reviewer retry và publication replay không ghi thêm.

Expected/actual khớp: observations860→863,jobs46→55,audit24→36,scopes/cutoffs/evidence0→3,catalog0→3,releases0. T07 status/issues giữ nguyên; không giải phóng blocked attempts hoặc suy computation. Full IDs/evidence composite keys/fingerprints, checks và taskT09 đề xuất ở [báo cáo publication pilot](ptit-publication-pilot.md). Private outputs tại state/publication/d-approved-20261018/. Chưa hoàn tất toànT08/Phase1/quota20.000.
