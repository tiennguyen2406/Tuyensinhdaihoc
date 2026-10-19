# PTIT: publication pilot D1–D3 — 18/10/2026

Ba cutoff đã được người dùng duyệt riêng đúng file/hash/request, rồi review và publication tuần tự D1→D2→D3 qua CLI hiện có. Đây là lát cắt publication pilot có dữ liệu thật, chưa nghiệm thu toàn T08, Phase 1 hoặc dataset20.000. Không đổi code/schema/resolver, tải nguồn hoặc xây release T09.

## Approval và revalidation

Baseline: codex/crawler-pilot, HEAD987edbf56192e6a0784822c24e0c255315e8b804, origin đúng repository; chỉ .vscode/ chưa tracked. C2 được duyệt riêng SHA335f124fd2da7261e9e5b0c4ed8505b2001a39c897bc850c2d67e3d0595a840d/requestb72d93e4-d0a8-4cac-b166-84e23ddd87c4, ghi nhận private,0DBwrites. Sau đó từng D được duyệt riêng. Exact bytes/reason/request/binding giữ nguyên; chữ DRAFT/pending là nội dung tại lúc tạo đã được người dùng duyệt, không sửa để cập nhật thời điểm.

Trước mỗi D: kiểm schema0003_publication, expected registry/alias heads, actual parents, T07/raw/T06 row digests, environment digest, scale/basis, source authority và upstream approvals còn active/không revoked; reselect HTML locators, xác minh snapshot SHA/size. Plan dedicated reviewer giống bản đã trình. Reviewer/publisher riêng, không superuser/CREATEROLE/CREATEDB/BYPASSRLS hoặc membership chéo. Không dùng SQL mutation hoặc DTO tự tạo để vượt gates.

Registry head giữ registry/ptit-scale/20261018-c1, alias aliases/ptit-identities-authority/20261018-r2, T07job75f10ef6-57a1-4fb2-a331-ec6334912819. Scale76ea9a26-6e77-594c-94f7-fae053e0c148 thuộc THPT/2024.

## Expected/actual

| Mốc | Observations | Jobs | Audit | Scopes/cutoffs/evidence | Catalog version | Releases |
|---|---:|---:|---:|---|---:|---:|
| Baseline |860|46|24|0/0/0|0|0|
| D1 — expected = actual |861|49|28|1/1/1|1|0|
| D2 — expected = actual |862|52|32|2/2/2|2|0|
| D3 — expected = actual |863|55|36|3/3/3|3|0|

Mỗi D: reviewer thêm1review_decision job/1audit, chưa tăng catalog. Publisher thêm1scope/1current cutoff revision1/1primary evidence/1validated observation/1publication_request+1refresh job/3audit và catalog+1. Tổng+3observations/+9jobs/+12audit; Program/Offering/scale giữ2/3/1, scoring_rules0. Rows publisher/catalog/audit/outbox có cùng xmin transaction; không D thất bại hoặc cần rollback.

## IDs canonical thật

| D | Fact2024/THPT | Decision ID | Scope ID | Cutoff ID | Catalog / refresh job |
|---|---|---|---|---|---|
|D1|QTKD/BVH 25.17;TTNV≤13 khi bằng cutoff|e073fd09-a667-5402-b5d1-148fe32d8c6f|5b12453f-420f-44a4-b605-0fbd079d145c|1076f528-0bab-4ac6-8840-714c6cfd77b6|1 / 1e1bfa99-0905-44b1-96c0-f622e4a30aeb|
|D2|QTKD/BVS 18.4;TTNV≤3 khi bằng cutoff|3415734f-4b13-52c2-a7a2-654b607be322|accfaee3-58d8-4a73-bc8a-4af732aa2d31|a5ced261-5a4d-4c20-91f6-bb28a646e8a2|2 / 6e23b47e-a989-483f-ae36-e429c08cd4a6|
|D3|CNTT/BVH 26.4;TTNV≤5 khi bằng cutoff|c151870c-34c3-5f11-a88d-e3bc1cadcfc4|16a4ed99-0b01-4a9a-ab45-91fb76cb5937|4fd7c322-cd05-4102-a6c4-956d3313258e|3 / db3948a9-0bca-47c9-b1f8-cb01d1d760d0|

Evidence có composite PK (cutoff_id,observation_id), không có UUID evidence riêng. Cả3 là primary, mỗi cutoff1evidence row. Supporting field refs giữ đầy đủ trong immutable review command, không đếm mỗi ref thành fact/evidence row mới.

| D | Evidence observation ID | Fact fingerprint SHA-256 | Publication request job | Audit IDs |
|---|---|---|---|---|
|D1|8e24b33c-5bd3-4294-891b-074a86e7316f|72a1c9e0bb05711c0c1389a5fa248fe62dfc541119addfe4a2cd96a7ca2c6d36|f5899dcd-f8a6-4427-9e75-74e7f2412e9b|25,26,27,28|
|D2|3dd92396-02ad-46a9-9c82-1faa001f7257|28db4633875494ae72592db3ee29d416a8de33429b1bcde3d62147e56a48a652|e91013a6-dc54-4641-b629-7beb9f9097f3|29,30,31,32|
|D3|5f525a40-0033-47fd-8fcd-7ce8cde0714a|4dae6f2d7af5f7b1a3a7611f91330b20c81e36897323f0a3498485fb26eb4d1a|fd91148f-db84-42ae-b4c0-050f832a5880|33,34,35,36|

Đã đối chiếu từng row: University–Program–Offering thực, campus/BVH/BVS, year2024, mã7340101/7480201 không hậu tố, THPT, Decimal25.17000/18.40000/26.40000, scale[0,30], basis, condition_key/fact fingerprint, literal TTNV và predicate eq/lte, primary snapshot và validated observation lineage. Current/verified/published, revision1, system_valid_to NULL; source_published_at/effective_from vẫnNULL. Không nhân theo tổ hợp/nguồn.

C2 giữ named-notice round28701(BVH)/28700(BVS), ordinalunknown; populationPTIT_THPT2024_REGULAR_VALID_APPLICANTS, source_aggregate QTKD A00/A01/D01 và CNTT A00/A01. Thiếu preference_order tại bằng cutoff là insufficient_input; trên cutoff TTNV tại biên không áp dụng, dưới cutoff vẫn dưới. Predicate đã lưu, chưa evaluator. Computation status dựng lại qua ValidatedDraft của decision thật là unavailable_aggregate_scope; không giả cột computation_status trong cutoff_scores hoặc claim tính/so sánh/trúng tuyển.

D2 dùng Offering BVS257a579f-e7a6-5a6b-8fd4-8a43f9d74ecb thuộc Program QTKDcf5b839c-2c74-57b2-a97c-6bb563edbbf6 đã được B1/B2 duyệt. T07 vẫn91partial/4ambiguous/0eligible; proposal Program BVS pending giữ nguyên, không auto-merge/sửa resolver. T08 là review fact với approved mapping và field evidence riêng.

## Replay và bảo toàn

Đã gọi lại reviewer apply --file cùng request cho từng D: trả decision cũ. Publication replay --decision bằng actual IDs: cached=true; cả34tables không đổi ở từng replay. Cached result giữ dataset version lịch sử1/2/3 của request, global catalog vẫn3; không hiểu cached result version1 là rollback global version. Không thêm rows/jobs/audit/version.

Row digests xác nhận mọi860observations/46jobs/24audit cũ, canonical parents, nguồn, crawl runs/schedules/snapshots giữ nguyên. Chỉ catalog_state cập nhật0→3 và inserts đã duyệt;22raw snapshots nguyên SHA/size. Ba refresh_serving:1/2/3 queued đúng payload/version, release_builder=not_implemented_T09;0releases. Private outputs/manifests/drafts cũ và .vscode/ giữ nguyên.

## SQL xác nhận count canonical

```sql
SELECT count(*) AS canonical_current_verified_published
FROM cutoff_scores AS c
JOIN program_admissions AS a ON a.id = c.program_admission_id
WHERE c.is_current IS TRUE
  AND c.verification_status = 'verified'
  AND a.data_status = 'published';
```

Kết quả thực tế3. SQL chi tiết xác nhận3scopes, mỗi scope một current verified published cutoff revision1. Quota count là3 canonical rows; không cộng863observations/3evidence/revisions vào20.000. Count và catalog version là hai đại lượng khác nhau.

## Checks và mốc tiếp theo

Local: uv run pytest -q tests/publication tests/integration/test_health.py tests/integration/test_health_schema.py:62passed127.62s; fixtures tạo DB test riêng, không dùng pilot DB. Ruff check/format128files, mypy55sourcefiles, lock87packages, Alembic current0003head/check đạt; diff checks trước commit. Không đổi code, không chạy full pytest local; CI exact SHA tài liệu mới kiểm khi push.

ASGI live/ready200 với DB thật. HTTP127.0.0.1:8000 cả hai endpoint chưa kết nối (URLError); không suy có server đang chạy từ ASGI.

Đề xuất taskT09 release pilot nhỏ trên catalogversion3: immutable manifest/coverage theo năm/trường/method/scope, export checksum/count SQL khớp file, provenance/lineage và replay; xử lý/coalesce refresh jobs theo contract có audit. Chưa triển khai builder hoặc mark jobs succeeded trong task này. Release nhỏ chưa nghiệm thu pilot đa nguồn/20.000; T10 có thể theo sau release ổn định.

Private handoff: state/publication/d-approved-20261018/ giữ approval records, plans, actual rows/audit/transactions, before/after digests, reviewer/publication results/replay, SQL và health. Không commit credentials/raw/drafts/private outputs.
