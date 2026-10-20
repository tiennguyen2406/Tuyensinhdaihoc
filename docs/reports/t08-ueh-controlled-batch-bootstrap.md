# T08 — Controlled registry integration và UEH batch bootstrap preparation

Baseline local/remote: `771c7241eda611b6773d62ce302a8d0e1e1558da`, branch
`codex/crawler-pilot`. Handoff untracked cũ giữ nguyên. **Task chỉ đọc DEV:**
0HTTP nguồn,0approval,0bootstrap/canonical write,0audit mới,0publication/release/deploy.
Apply simulations chỉ dùng PostgreSQL test DB riêng, giữ lại DB theo policy.

## Blocker thực tế và thay đổi tối thiểu

`ReviewService.registry()` chọn latest global registry head (PTIT). UEH pending keys
chỉ có ở frozen T07 jobs; `bootstrap.operations()` đòi key có trong seed. Offering
validation dùng một packet cho toàn command nên không thể an toàn xử lý hai campus/
codes/notices trong cùng batch. Alias bootstrap hiện chỉ hỗ trợ University, không đủ
để hợp thức hóa việc nhiều Program proposals cùng một canonical ID.

Thêm một module `publication/integration.py`, dùng lại registry models, packet builder,
resolver manifests, review transactions/audit. Không thêm migration/framework hoặc alias
engine; không sửa resolver/normalizer namespaces hay outputs lịch sử.

1. `prepare_integration`: đọc packets/bindings thật, kiểm frozen T07 parent set/hash,
   registry/entity/alias hashes, source host/owner/method/code-system và exact
   name/code/year/campus/training/track/language. Chỉ import pending entities được
   packet hỗ trợ; không lấy fuzzy options làm lineage. Duplicate/conflicting keys,
   owner domains, parents, approved-ID collisions hoặc orphan keys bị từ chối.
2. Overlay giữ exact approved PTIT entities/aliases và alias version, thêm150pending
   keys theo thứ tự deterministic. Không import aliases, không thay global head.
   `proposal-integration/1` chứa base hash/heads, từng key→bindings, parent manifests,
   diff, conflicts và stable manifest hash. `proposal_only=true`, `execution_ready=false`.
3. `ReviewCommand` thêm optional `proposal_integration`, `operation_bindings` theo
   operation key. Serializer bỏ riêng hai defaults mới để giữ nguyên hashes của mọi
   command cũ; tám historical DEV review command hashes đã đối chiếu chính xác.
4. `operations()` kiểm từng operation bằng chính packets được bind: code/campus/year,
   original Program parent, primary snapshot, owner, metadata và evidence locators.
   Không reparent hoặc đổi frozen source identity metadata để merge proposals. Method
   chỉ được thêm canonical method-code binding phù hợp operation được review.
5. Source authority batch bắt buộc narrow publication bindings và đúng owner/year/
   method/campus/code/snapshot; không thêm foreign University hoặc broad years. Quyền
   dữ liệu vẫn là human/legal gate riêng; validator kỹ thuật không cấp license.
6. `checked_packets` kiểm đầy đủ parent manifests, cache normalization-parent validation
   trong một batch call. Cached apply replay vẫn kiểm secondary packets/registry bodies;
   không dùng kết quả cũ để bỏ qua tampering. Cache không tồn tại qua calls/transactions.

CLI thật: `python -m services.data.publication integrate --file <IntegrationRequest>`.
Command này luôn `SET TRANSACTION READ ONLY`, kiểm expected registry/alias/base hash,
không ghi registry head. `--file-sha256` kiểm exact file bytes trước DB authentication;
future batch `apply --file` bắt buộc flag này. Output integration không overwrite
immutable output path đã có. Commands PTIT cũ giữ luồng cũ.

## Batch thật và identity reconciliation

Hai snapshot giữ nguyên: August `67f11fe2-3a23-4d3a-8d67-fb468f66ec54`, September
`ce858dfc-707a-4e2d-ad3d-a5439807fa1c`. Reuse exact71August packets (đã gồm6KSV cũ)
và6September packets; không tính6technical T05re-extractions vào batch này.

**77/77 bindings và packets khớp frozen;150/150 pending keys có lineage hợp lệ:**
1University/1Method/74Program/74Offering. Không có UEH approved entities hoặc eligible facts.
Base vẫn `registry/ptit-scale/20261018-c1`, aliases
`aliases/ptit-identities-authority/20261018-r2`. Overlay proposed version
`registry/ueh-controlled-proposal/20261020-r1`, manifest SHA-256
`b363ed837e17d51b7191c552c034e831660b8a4f79907ded119dbbe8d6c6223b`.
Giữ exact72base entries (7approved/65pending) và6aliases; không gọi mọi entry trong
reviewed head là approved entity.

Curated layer không tự chọn UUID: **63 code review families**, không khẳng định có63
persistent canonical Programs. Outcome52`proposed_distinct_program_or_offering` cho
source rows riêng,3`proposed_same_persistent_program` cho exact same-label/code/campus
qua hai notices,8`unresolved_requires_review`. Có71year/campus/code Offering-context
groups; ba nhóm KSV có source-label variants vẫn unresolved. Pending keys gốc giữ đủ.

| Code xuất hiện ở cả KSA/KSV | Source labels cần đối chiếu |
|---|---|
| 7220201 | Tiếng Anh thương mại; (*) August và (**) September, không suy cùng named weight |
| 7340120 | Kinh doanh quốc tế; curriculum giữa campus chưa xác lập |
| 7340122 | Thương mại điện tử (*); source spacing/marker giữ nguyên |
| 7340201_01 | **KSA Tài chính công; KSV Ngân hàng** |
| 7340201_02 | **KSA Tài chính; KSV Thuế** |
| 7340201_03 | **KSA Ngân hàng; KSV Thuế / Thuế (S)** |
| 7380107 | Luật kinh tế; persistent Program equivalence chưa duyệt |
| 7620114 | Kinh doanh nông nghiệp; September thêm(S), material variant chưa rõ |

Ba code `_01/_02/_03` chứng minh code UEH phải đi cùng campus/year/source context;
không merge theo code. Chín same-label/different-code alternatives được ghi riêng,
chưa merge theo tên. Ba stable cross-round groups là7480107/7480201/7810201: proposal
cùng persistent Program, Offering/round semantics vẫn cần review. ISB_CNTN/ASA_Co-op
giữ alphanumeric; Major taxonomy riêng. Các markers và raw labels đầy đủ trong lineage;
CSV dùng display labels để đọc, JSON giữ exact DOM raw strings/locators/hashes.

Narrow alternative cho label variants: chọn representative chỉ sau review; giữ source
label trong lineage, rồi reviewed source-specific T06 remapping ở namespace mới trước
freshT07, hoặc task alias governance hẹp. Chưa implement mapping/alias đó; hiện không
thể apply nhiều pending keys vào một canonical UUID hoặc reparent Offering qua overlay.

## Hồ sơ và ranh giới thực thi

Private: `state/review/ueh-2024-batch-bootstrap/` chứa batch manifest,77bindings,
integration diff, identity CSV/conflicts/alternatives,16shared dependencies,
77candidate dependency records, bootstrap preview, validation và preservation.
`bootstrap-preview.json` có **commands=[]**, planned canonical creates0. Không fake
ReviewCommands/UUIDs, không suy MAIN/GENERAL/conditions/scale/basis hoặc combination status.

Authority tách `cutoff` cho published value và `scoring_rule` cho primary scale snapshot
theo `validate.build_draft`, không duyệt executable rule. August chỉ generic starred
factor2/30, ISB không thừa kế notes khác section. September English/Math formulas
giữ đúng notice/program. Canonical scale/domain/basis, round/population/conditions,
aggregate applicability và storage/commercial/republication rights còn missing.

Future authorized execution đi qua ReviewService hiện có: exact command bytes/hash →
authenticated reviewer → current base heads/hash + all bound packets → ordered original
parents → existing atomic nested transaction/audit/registry-version registration.
Request ID replay idempotent, changed command rejected, stale versions rejected trước
new writes, failure rollback toàn transaction. Registry-version parent references vẫn
là approved base head, không temporary overlay. Đó là capability đã test, **không là
batch thật execution-ready hoặc authorization**. Sau bootstrap được duyệt riêng còn
export approved registry → freshT07/T08 → human fact review → publisher riêng; release riêng.

## Verification và preservation

Focused T08/PTIT/UEH suite:88pass và T07/resolution319pass, gồm13tests mới kiểm controlled integration,
exact-file hash, two-campus per-operation binding, metadata/owner/source/parent/snapshot
guards, manifest tamper, stale versions, replay và transaction rollback. Full backend
**Full backend685pass/355.49s**, một Starlette deprecation warning có sẵn. Ruff/format,
mypy76sources, frozen lock87packages, Alembic current/check đạt. Exact-SHA CI evidence
nằm ở private final handoff; không sửa CI/lock/migration.
Lượt full test đầu dừng do chọn basetemp trong checkout, bị RawStorage guard chặn đúng;
đã tái hiện bằng một test và chạy lại với basetemp mới ngoài checkout, không sửa guard.
Real77packet validation không thay bằng synthetic fixture. CLI integrate tái lập cùng
manifest77bindings/150keys, read-only. Negative probes từ chối base/result/packet hash,
stale registry/alias heads và tampering của9sealed package artifacts.

| DEV | Trước | Sau |
|---|---:|---:|
| Current verified published / catalog | 3 / 3 | 3 / 3 |
| Audit | 47 | 47 |
| Sources / snapshots | 43 / 36 | 43 / 36 |
| Observations / ingest jobs | 1127 / 83 | 1127 / 83 |
| Release rows / version / cutoff count | 1 / 3 / 3 | 1 / 3 / 3 |

Toàn34table digests và631historical files trước/sau giống hệt, gồm PTIT approvals,
registry/alias histories, hai UEH inputs/outputs, raw/release files, handoff và `.vscode/`.
Release v3 ID396ccd8b-1193-43dd-a08a-bb19e639dd56, manifest SHA-256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90` giữ nguyên.

Full read-only preparation19.67s,1129SQL reads/1130statements/0mutations; CLI repeat12.26s
riêng, negative-probe pass17.50s riêng. Không cộng các phép đo thành một throughput giả.
SQL counters chỉ bao gồm instrumented packet/integration block, không gồm inventory
checkpoints. Token usage không quan sát được; significant calls một packet batch và một
integration batch. Production diff6modules,+548/-11lines; chi tiết trong private final handoff.

Owner cần chốt theo thứ tự: (1)rights và authority exact hai notices; (2)UEH/PT6/code
system; (3)persistent Program/campus Offering alternatives, nhất là code collisions và(S);
(4)label strategy còn thiếu; (5)scale/basis,round,population/conditions,source-aggregate/
weighting applicability; (6)review exact bootstrap commands sau khi đủ real references.
Chưa xin approval fact hoặc chạy bootstrap ở task này. Canonical tiến độ vẫn3/20.000;
T08/T11/Phase1 chưa đóng.
