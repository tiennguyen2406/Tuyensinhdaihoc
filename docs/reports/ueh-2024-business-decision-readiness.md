# T08/T11 — UEH 2024: audit evidence và sẵn sàng quyết định nghiệp vụ

Baseline local/remote đã đối chiếu:
`ea7fa64ca8d8c90c9c832afc4c60e13f71b0a46e`, branch `codex/crawler-pilot`.
Không production code changes. Task chỉ audit/read-only, private dossier và docs/WBS;
**0 HTTP nguồn, 0 business approval, 0 canonical/bootstrap/publication/release writes**.
Không sửa `.vscode/`, handoff untracked, source profiles, frozen packets hoặc approvals cũ.

## Kết quả dành cho chủ dự án

**12/12 packet nguyên và kiểm được; 23/23 proposal IDs/evidence giữ nguyên.** Điều đó
chứng minh nguồn gốc dữ liệu, không xác nhận các diễn giải nghiệp vụ đã đúng/được duyệt.
Đủ hồ sơ để xem từng field; chưa có bootstrap/fact ReviewCommand hợp lệ để thực thi.

| Readiness của 23 proposals | Số | Proposal IDs |
|---|---:|---|
| `evidence_supported` | 1 | `S:weighting`, chỉ bảo toàn evidence đúng môn/chương trình/notice |
| `needs_business_decision` | 13 | `I:university`, `I:method`; Program/Offering của 7220201,7480107,7480201,7810201; `S:round:august`, `S:round:september`, `S:combinations` |
| `needs_external_evidence` | 8 | Hai `A:authority:*`; Program/Offering của7340201_03,7620114; `S:scale-basis`, `S:population-conditions` |
| `blocked` | 1 | `P:readiness`: dependencies/IDs/heads/tooling chưa đủ |

Các labels không là registry review.status, không approval. Ngay `evidence_supported`
cũng không duyệt scoring rule/scale hoặc cho phép publish. Chỉ đề xuất giữ named note và
formula September đúng nơi, không hồi tố August, đã được source bytes hỗ trợ.

Private dossier mới: `state/review/ueh-2024-decision-readiness/`. Entry point `review-index.md`;
23 standardized records trong `decisions.json`; giữ exact IDs/order và original proposal
digests, affected bindings, evidence/versions, alternatives, missing fields, reviewer role,
downstream effect và execution blockers. Sáu gap thêm trong `additional-decisions.json`,
không merge/xóa/đánh số lại23proposals gốc. Hồ sơ gốc ở `state/intake/` không đổi.

## Sáu nhóm identity cần quyết định

Cả hai nguồn: UEH, 2024, KSV, chính quy, PT6. Canonical identity đều pending.
Code system `ueh:admission-code`, không Major taxonomy; `_03` giữ nguyên.

| Code | August17 | September30 | Pending Program/Offering mỗi loại | Quyết định còn mở |
|---|---|---|---:|---|
| 7220201 | Tiếng Anh thương mại (*) | Tiếng Anh thương mại (**) | 2 | Marker thay đổi; không suy named English weight cho August |
| 7340201_03 | Thuế | Thuế (S) | 2 | Song ngành có tạo material curriculum/Offering difference? |
| 7480107 | Robot và Trí tuệ nhân tạo (hệ kỹ sư) | cùng nhãn | 1 | Cùng tên/code/context vẫn cần review persistent identity |
| 7480201 | Công nghệ và đổi mới sáng tạo (*) | cùng nhãn | 1 | September Toánx2; không backfill named subject vào August |
| 7620114 | Kinh doanh nông nghiệp | Kinh doanh nông nghiệp (S) | 2 | Song ngành/track/curriculum chưa có bằng chứng đối chiếu |
| 7810201 | Quản trị khách sạn | cùng nhãn | 1 | Điểm đổi không là Program mới/correction |

Registry thật có1University/1Method/9Program/9Offering pending, khôngcanonicalUUID.
Ba label variants giải thích9→6groups, không chứng minh merge/split. Từng mã giữ ba
alternatives: **A** một Program/một Offering qua hai admission contexts; **B** một Program,
Offering riêng nếu có material difference và business key đúng; **C** giữ unresolved.
A/B/C là Offering options dưới giả thuyết cùng Program; persistent identity vẫn giữ
alternative **khác Programs nếu evidence mới được review chứng minh khác biệt thật**.
Chọn unresolved/request_more/reject không cần chờ evidence ngoài; evidence mới cần để
giải quyết kết luận identity. Không alternative nào được chọn thay reviewer. B không thể chỉ khác round/score hoặc
điền track/language giả để vượt unique Offering key. T07 fuzzy options ngoài code group
không được coi là identity matches; matrix dùng exact code bindings và parent proposal keys.

PT6 có định nghĩa THPT2024 từ nguồn; existing canonical THPT của PTIT chỉ là alternative
cần semantic/year/code review. Max30 giống không chứng minh tương đương. Method alias
approval cũng chịu giới hạn governance hiện tại, không tự link/relabel PTIT method.

## Authority, quyền sử dụng và scope

Hai notices có first-party UEH self-identification, explicit2024/KSV/PT6 và physical
cutoff cells. Source DEV vẫnunverified/unmapped. Đề xuất narrow publication bindings
riêng từng source, chính snapshot, sáu full Offering codes, campusKSV/year2024/PT6.
University UUID/method_code còn unresolved trong non-executable proposal, không fake IDs.

Robots allowance, TLS/HTTP200, official-looking host và owner-authorized pilot không
là license. Cả quyền storage/internal processing lẫn commercial use/republication chưa
được hồ sơ chứng minh. Cần UEH/chủ thể có quyền hoặc qualified legal review xác lập
căn cứ và giới hạn từng mục đích; owner không cấp quyền thay UEH. Không network/legal
lookup hoặc gửi yêu cầu ra ngoài trong task này. Quyền sử dụng là gate riêng, không
được T08 authority validator tự động enforce.

August là thông báo kết quả2024, không tự gắn Round1. September explicit bổ sung,
ordinal unknown. Evidence-context keys đề xuất `ueh:ksv:2024:notice-20240817` và
`ueh:ksv:2024:notice-20240930`; chưa canonical admission round. September round proposal
gốc `ueh:ksv:2024:supplemental:notice-20240930`; August có option named-notice scope để
review, canonical round vẫnnull. Không coi ba cặp đổi điểm là correction/revision.

| Code | August17 | September30 bổ sung |
|---|---:|---:|
| 7220201 | 17.00 | 20 |
| 7340201_03 | 17.00 | 20 |
| 7480107 | 17.00 | 17 |
| 7480201 | 17.00 | 17 |
| 7620114 | 17.00 | 17 |
| 7810201 | 18.00 | 20 |

Có **3 changed/3 unchanged**. Không ghi facts hoặc scope nào. Source ngày17/08 và30/09
chỉ có day precision. Giữ source date trong provenance, `source_published_at=None` là
option hợp lệ; không tạo midnight/timezone/effective_from. Thiếu timestamp không phải
absolute publication blocker của CutoffSpec, nhưng mất khả năng dựa vào timestamp để
machine-order correction; cần policy đượcreview, không đoán thời điểm hiệu lực.

September general formula, English7220201/Math7480201 weighted2 và normalized30,
eligibility/priority/method-preference prose được giữ riêng. August chỉ có generic
starred factor2/30 note; không có named subject/formula. Old August footnote trên mọi
packet là table context, không quyền áp weight cho unmarked rows. Numeric scale identity,
minimum/domain và formal basis/application chưa approved; thiếu evidence cho mọi basis
August. Basis families ordinary/English/Math September và starred-unspecified/ordinary-
unconfirmed August chỉ là review labels, không canonical versions hoặc executable rules.

Population/conditions còn unresolved; không GENERAL/MAIN/conditions={} hay confirmed_none.
August p49–55 là lời mời đăng ký bổ sung **sau bảng cutoff**, có threshold18.00; không thay
September17 hoặc kết luận eligibility đã được giải thích. Nếu formal scope phụ thuộc
threshold đó thì cần domain evidence riêng. Hai nguồn có equal-cutoff applicability
giữa tổ hợp: review option `source_aggregate`, một fact/physical cell, không fan-out.

Contract cho phép future cutoff thiếu executable rule khi các gate khác đã approved:
aggregate → `unavailable_aggregate_scope` và cấm combination-specific rule; valid
nonaggregate thiếurule → `unavailable_rule`. Không là tính điểm hay pass/fail admission.

## Giới hạn T08 đã kiểm chứng, không sửa trong audit

1. **Chặn bootstrap UEH hiện tại:** `ReviewService.registry()` chọn latest global
   registry_version;20UEHkeys không nằm ở PTIT head. `bootstrap.operations()` yêu cầu
   proposal có sẵn trong seed; CLI cóexport nhưng không import/merge proposals.
   Approval A/I/S chưa đủ để materialize current bootstrap command. Cần task hẹp cho
   controlled proposal integration bảo toàn approved PTIT history.
2. **Program aliases:** Registry cấm duplicate canonical(kind,UUID), trong khi bootstrap
   alias chỉuniversity_aliases. Không link chín keys thành sáu IDs để né governance;
   cần curated canonical-key/alias/relink strategy riêng. Không dựng alias engine ở đây.
3. **Scale authority:** `validate.build_draft()` và scale validator yêu cầu primary scale
   snapshot có authority `scoring_rule`, dù executable scoring_rule_id có thểnull.
   A cutoff-only chưa đủ; review scope basis/scale riêng, không tự widen A hay approve DSL.
4. **Rights:** authority schema không có mandatory legal-rights gate. Technical authority
   pass không chứng minh quyền lưu/xuất/tái phân phối; phải xử lý bên ngoài validator.
5. **Date precision:** CutoffSpec nhận timezone datetime/null, không source-date precision
   riêng; giữ date provenance và nulltimestamp là option hiện hữu, không ép migration.
6. **Semantic responsibility:** round/population/basis chủ yếu kiểm nonempty; predicate
   kiểmshape nhưng không evaluate; locators không tự chứng minh ý nghĩa gán cho fields.
   Human review vẫn phải đọc source. Aggregate DSL không tự tạo canonical combination list.

Căn cứ implementation: publication/{review.py:23,bootstrap.py:106,bootstrap.py:280,
bootstrap.py:318,__main__.py:75,validate.py:93,validate.py:249,contract.py:118},
resolution/registry.py:124 và api/db/validators.py:37. Các điểm này là giới hạn đã
demonstrate/code-review, không permission bypass hay lý do weakening validators.

## Audit, tests và preservation

Dùng T08 `inspect_packet`/`checked_packet` hiện có, transaction REPEATABLE READ READ ONLY.
Kiểm T05 payload hash/parse manifest, T06/T07 signatures/parents, registry/alias hashes,
source/snapshot/bytes và raw score↔Decimal; mọi row/code/name/combination/header/context/
footnote locator được resolve vào RawStorage. Hai snapshot đúng hash user giao:

- August `67f11fe2-3a23-4d3a-8d67-fb468f66ec54`,284975bytes,
  `09ad02da8c2f5b0b86cfce711017541d029d9c0731c9027ade9b317e15bc9207`.
- September `ce858dfc-707a-4e2d-ad3d-a5439807fa1c`,193572bytes,
  `51b52957dc76a054a804e93dfc3f13defca46ddbe119c6890bdb1d042c6f4b1d`.

12tampered packet hashes bịtừchối;12stale registry và12stale alias expectations được
nhận diện. Frozen packets vẫn đúng lịch sử, nhưng khác current approved global heads
`registry/ptit-scale/20261018-c1` / `aliases/ptit-identities-authority/20261018-r2`.
Không sửa expected heads cho “plan xanh”. Packet-only preview12candidates impact0,
can_publish=false; không tạo/chạy bootstrap/fact ReviewCommand, không dùng fake UUID.

40offline dossier safety assertions đạt; không bổ sung production logic hoặc test giả
mirroring implementation. Targeted existing PostgreSQL tests publication/resolution/UEH:
**429passed**, DB test riêng DEV. Full backend: **655passed/321,05giây**, một Starlette
deprecation warning hiện có. Ruff check/format, mypy73sources, frozen lock87packages,
Alembic0004_releases/check không phát sinh operations đều đạt; không benchmark50k.
Không thêm production logic/test chỉ để tạo diff. Exact pushed-SHA CI và final commit
được ghi ở private handoff/verification manifest sau push, không dùng CI baseline thay thế.

Đã chạy một **CLI packet-only plan thật** bằng resolution/candidate/binding hiện hữu;
preview_only=true/can_publish=false/impact0. Các12packet cũng qua packet-plan function.
Không dùng `--file` fake command, không authentication-as-approval.

Baseline business state thực: canonical3/catalog3/audit47; sources43/snapshots36/
observations926/jobs80;1releasev3 chứa3cutoffs. Toàn bộ34table row digests và523historical
file digests **trước/sau giống hệt**, không ngoại lệ operational host-state ở task read-only
này; gồm raw/intake/registry/alias/packet
history, `.vscode/`, handoff và release artifacts. Không sửa/xóa dữ liệu, DB, migration,
volume hoặc restart DEV. Release ID `396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90` được verify read-only.

| Chỉ số DEV | Trước | Sau |
|---|---:|---:|
| Current verified published cutoffs | 3 | 3 |
| Catalog dataset_version | 3 | 3 |
| Audit events | 47 | 47 |
| Sources / snapshots | 43 / 36 | 43 / 36 |
| Observations / ingest jobs | 926 / 80 | 926 / 80 |
| Dataset release rows / version / cutoff count | 1 / 3 / 3 | 1 / 3 / 3 |
| UEH typed candidates / business approvals / eligible | 12 / 0 / 0 | 12 / 0 / 0 |

PTIT cutoff IDs nguyên: `1076f528-0bab-4ac6-8840-714c6cfd77b6`,
`a5ced261-5a4d-4c20-91f6-bb28a646e8a2`, `4fd7c322-cd05-4102-a6c4-956d3313258e`.
University/Program/Offering/scope/evidence IDs và mọi immutable review/registry rows
cũng nằm trong34table digest comparison, không được đổi hoặc tạo lại.

## Thứ tự quyết định tiếp theo, không automatic execution

1. Quyền use/storage/commercial/redistribution và authority exact notices (A, X:source-rights).
2. UEH University + PT6 method/code-system semantics (I:university, I:method).
3. Sáu persistent Program decisions và sáu Offering A/B/C decisions, nhất là(S).
4. Hai round-context identities, không suy ordinal/correction (S:round:*).
5. Scale/domain/basis và authority cho scale source (S:scale-basis, X:scale-authority).
6. Population/eligibility/priority/conditions có source applicability rõ (S:population-conditions).
7. Combination aggregate và weighting applicability, không executable scoring (S:combinations/weighting).
8. Controlled registry integration/alias strategy và date-precision policy, trong task riêng.
9. Sau approvals và authorization riêng: canonical bootstrap hợp lệ, fresh registry/alias
   export → fresh T07 → fresh packet/hash/dependencies → human fact approval từng candidate.
10. Publisher transaction phải được cho phép riêng; refresh-serving và release mới cần
    task riêng, giữv3. Không thay3/20.000 bằng số candidates/proposals/tests.

Đồ thị12bước và mọi prerequisite từng candidate ở private publication-dependencies.md /
round-scope-matrix.json. Task này không ghi quyết định nào thành approved, không hoàn tất
toànT08/T11/Phase1 hoặc chuyểnT12/T13.
