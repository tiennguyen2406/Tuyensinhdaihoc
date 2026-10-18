# Review workflow T08 — CLI quản trị local

Đã provision hai danh tính kỹ thuật DEV theo ủy quyền 18/10/2026; bản thân provisioning không tạo approval. Người dùng sau đó đã duyệt riêng A2/B1/B2/B3 đúng hash/request; đã apply/replay/export, chi tiết ở các mục cập nhật cuối tài liệu. C1/C2/D chưa được duyệt. Không dùng tài khoản kỹ thuật như bằng chứng người phụ trách đã duyệt. Đọc publication-contract.md trước khi thực hiện; fixtures tests không dùng làm hồ sơ thật.

## Quan sát và preview

```powershell
uv run alembic upgrade head
uv run python -m services.data.publication list --output state/publication/list.json
uv run python -m services.data.publication inspect --resolution 97259d1b-894c-4637-9e09-8c237ce15c78 --candidate 857495c2612874e9c1e25b2705660fe920db5a76f35bbe81cade944d9b451277 --output state/publication/inspect.json
uv run python -m services.data.publication plan --resolution 97259d1b-894c-4637-9e09-8c237ce15c78 --candidate 857495c2612874e9c1e25b2705660fe920db5a76f35bbe81cade944d9b451277 --output state/publication/plan.json
```

Migration là lệnh operator rõ ràng, health/CLI không tự migrate. list/inspect/plan/export chạy read-only. Plan packet chỉ nêu needs_decision và tác động hiện tại 0; chưa là kế hoạch có UUID đã duyệt. Ba packet pilot chi tiết nằm ngoài Git tại `state/publication/review-batch.md` và `pilot-1.json`…`pilot-3.json`, gồm source URL/cell/header/locator.

## Thiết lập quyền trước apply dữ liệu thật

Migration owner có thể chạy `uv run python -m scripts.provision_publication_roles` sau khi kiểm schema head. Lệnh chỉ tạo NOLOGIN groups/grants, không tạo tài khoản hoặc gán memberships. Người quản trị phải chọn và provision dedicated PostgreSQL login(s) cho reviewer/publisher qua quy trình quản lý secrets của mình, rồi GRANT group tương ứng. Không dùng tài khoản migration superuser để review. Không nhập password trong command history hoặc commit file secrets.

CLI nhận cặp biến môi trường `PUBLICATION_DB_USER`/`PUBLICATION_DB_PASSWORD` từ phiên shell bảo mật; cả hai có giá trị hoặc cùng unset. Chúng override username/password của DB URL hiện có, không đổi host/database. `.env.example` chỉ ghi biến trống; không lưu credentials vào quyết định JSON. Script grants đã được chạy trên database development ngày18/10/2026. Hai login kỹ thuật riêng eduradar_dev_reviewer/eduradar_dev_publisher có group tương ứng; chưa là danh tính reviewer production hoặc approval nghiệp vụ.

## Bootstrap và phiên bản registry

Reviewer soạn file riêng theo `ReviewCommand` trong `services/data/publication/contract.py`. Các trường bắt buộc: request_id UUID mới, action bootstrap, binding nguyên từ inspect, expected versions, reason cụ thể, new_registry_version/new_alias_version và operations. Mỗi operation có key proposal, kind, mode create/link, values, registry_fields và evidence `snapshot:<UUID>#<locator>`. Refs `@<key>` liên kết operation trong cùng batch. Không dùng canonical UUID dự kiến trong plan như entity đã tồn tại.

```powershell
$reviewFile = 'state/publication/bootstrap-review.json'
uv run python -m services.data.publication plan --file $reviewFile --output state/publication/bootstrap-preview.json
uv run python -m services.data.publication apply --file $reviewFile --output state/publication/bootstrap-result.json
```

Chỉ chạy sau người phụ trách đối chiếu evidence, values và quyền. Plan không ghi; can_apply=false nếu login không đủ quyền. Preview bootstrap không thực thi toàn bộ SQL constraints bằng transaction giả; apply vẫn có thể bị constraints chặn và rollback nguyên tử. Apply cùng request/body trả lại kết quả cũ, body khác bị chặn. Audit ghi actor DB thực, reason, before/after; registry mới bất biến trong ingest_jobs. Query job_type=registry_version để lấy UUID của manifest vừa tạo (liên kết decision_id trong payload):

```powershell
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT id,payload->>'decision_id' AS decision_id,payload->'registry'->>'version' AS registry_version FROM ingest_jobs WHERE job_type='registry_version' ORDER BY created_at DESC;"
```

Gán `$registryJob` bằng UUID thực rồi export và chạy resolution mới; không ghi đè T07 cũ:

```powershell
uv run python -m services.data.publication export --registry-job $registryJob --output state/publication/registry.json
uv run python -m services.data.resolution preview --normalization-job 7bc439bf-a6d7-4beb-bf03-bb47956c5383 --registry state/publication/registry.json --output state/publication/resolution-preview.json
uv run python -m services.data.resolution run --normalization-job 7bc439bf-a6d7-4beb-bf03-bb47956c5383 --registry state/publication/registry.json
```

## Review fact, apply và replay

Inspect candidate trong output T07 mới, không tái sử dụng binding cũ. Reviewer soạn action publish với fact `CutoffSpec`, expected versions/revision và field evidence. Phải có scope/scale/basis/authority đã xác minh; Decimal trong JSON là chuỗi. Không mặc định round/population/conditions hoặc max_score. Thiếu scoring rule không giả công thức; output ghi unavailable_rule.

```powershell
$publicationFile = 'state/publication/cutoff-review.json'
uv run python -m services.data.publication plan --file $publicationFile --output state/publication/cutoff-preview.json
uv run python -m services.data.publication apply --file $publicationFile --output state/publication/cutoff-decision.json
```

Apply file này chỉ tạo approval bất biến, chưa ghi cutoff. Gán `$decision` bằng decision_id thực được trả về. Dùng login publisher để áp dụng; publication lần đầu không truyền expected revision, correction truyền revision đã duyệt, ví dụ revision 1:

```powershell
uv run python -m services.data.publication apply --decision $decision --output state/publication/published.json
uv run python -m services.data.publication replay --decision $decision --output state/publication/replayed.json
# Chỉ khi quyết định là correction và đã duyệt expected_revision=1:
uv run python -m services.data.publication apply --decision $decision --expected-revision 1
```

Replay dùng expected revision đóng băng trong approval và vẫn kiểm auth/input/version/environment; có thể bị chặn nếu context đã đổi. Không migrate/download trong transaction. Kiểm result status/revision/evidence_added/dataset_version/refresh_job_id; queued refresh chưa được builder T09 xử lý.

Reject/request_more là ReviewCommand cùng binding/expected versions/reason, ghi quyết định và quality issue mới, không xóa issues T05/T06. Revoke cần revokes_decision_id; chỉ chưa-applied approval được phép theo conservative guard. Fact đã serving cần workflow withdrawal riêng, không sửa SQL trực tiếp để vượt guard.

## Các quyết định còn cần cho ba hồ sơ thật

1. Chỉ định người phụ trách nghiệp vụ; hai dedicated login DEV đã provision là danh tính kỹ thuật, không tự gán reviewer theo tài khoản Windows/Git.
2. Xác nhận University canonical code/system và BVH/BVS là campus labels trong nguồn; Program/Offering năm 2024, mã xét tuyển, track/language/training mode. Unknown giữ unknown; Major có thể để NULL.
3. Xác nhận authority của nguồn đối với chính các ô lịch sử 2024 và method THPT, không duyệt mọi thông tin của trang 2026.
4. Cung cấp evidence đã cache cho scale/basis, combination/confirmed_none/source_aggregate có căn cứ, round, population, conditions. Không suy 30 từ điểm. Lô bổ sung 18/10 đã tải có giới hạn 5/20 requests; những field còn thiếu vẫn blocked, không tự tăng budget.
5. Review score/cell và publication cụ thể. Chưa có quyết định nào trong các mục trên được apply trên dữ liệu thật.

## Lô evidence review 18/10/2026

Xem reports/publication-evidence-review.md và private `state/publication/review-batch.md`. Không overwrite pilot-1/2/3.json hoặc manifests T05–T07. Draft độc lập ở `state/publication/evidence-review-20261018/bootstrap-identities.draft.json`; actual read-only plan ở bootstrap-identities.cli-plan.json, expected impacts ở bootstrap-identities.readiness.json. Trong đợt này chưa apply.

Credentials ngẫu nhiên lưu tại `state/publication/access/local-dev-credentials.json`, ignored và ACL chỉ owner/SYSTEM. .env giữ nguyên. Để chạy lại **plan** mà không đưa mật khẩu vào command history/stdout:

```powershell
$localAccess = Get-Content -Raw -Encoding UTF8 state/publication/access/local-dev-credentials.json | ConvertFrom-Json
$env:PUBLICATION_DB_USER = $localAccess.accounts.reviewer.user
$env:PUBLICATION_DB_PASSWORD = $localAccess.accounts.reviewer.password
try {
    uv run python -m services.data.publication plan --file state/publication/evidence-review-20261018/bootstrap-identities.draft.json --output state/publication/evidence-review-20261018/bootstrap-plan-recheck.json
} finally {
    Remove-Item Env:\PUBLICATION_DB_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\PUBLICATION_DB_USER -ErrorAction SilentlyContinue
    $localAccess = $null
}
```

Publisher dùng account publisher tương ứng sau khi có quyết định hợp lệ, không thể tự tạo approval. Không chia sẻ/commit file credentials; đây là storage local có ACL, chưa là secrets manager/SSO production.

Scope aggregate chỉ dùng khi có đoạn nguồn nói rõ cùng điểm giữa các tổ hợp của cùng Offering. `source_aggregate` + evidence `combination_aggregation` giữ một fact; không dùng confirmed_none cho nguồn có nhiều tổ hợp, không suy membership từ thông báo ngưỡng chung. Aggregate vẫn chưa dùng để tính/so sánh.

Nguồn bổ trợ cùng publisher/host có thể được review từ snapshot chính nó trong cùng bootstrap batch; không cần parse/normalize/resolve thêm envelopes chỉ để duyệt authority. Điều này không tự duyệt nguồn khác host hoặc quyền thương mại/tái phân phối.


## Lô A2/B/C/D mới — chưa có approval

Bản A cũ và batch18/10 trước được giữ nguyên làm lịch sử, không apply A thay A2. Xem [PTIT blocker decisions](reports/ptit-blocker-decisions.md), [WBS](progress-wbs.md), private state/publication/review-batch.md và blocker-review-20261018/decision-readiness.json. A2 dùng THPT canonical, source100 chỉ metadata scoped, authority7sources có publication_bindings; phạm vi chỉ identities/authority.

Nạp dedicated credentials như ví dụ ở trên rồi chạy **plan**:

```powershell
uv run python -m services.data.publication plan --file state/publication/blocker-review-20261018/decision-a2.draft.json --output state/publication/blocker-review-20261018/decision-a2.plan-recheck.json
```

Trước apply ở lượt được duyệt: so file SHA, input/evidence checksums/locator, expected registry/alias heads và DB role. Nếu đổi nội dung phải request/version mới, giữ bản cũ, xin duyệt đúng bản mới. Không gọi apply từ prompt “tiếp tục”. B1/B2/B3/C1 là typed conditional commands với @refs, chưa plan/apply được trước A2 và từng parent head. Không dùng preview IDs để điền canonical_id. Sau bootstrap thực mới export registry/T07 namespace mới trên jobT06cũ; D recipes phải materialize ReviewCommand mới bằng IDs/binding thực và approval riêng từng cutoff. Named-notice round ở C2 là lựa chọn identity cần duyệt, không claim round1.

Reviewer không kiêm publisher qua login migration. Bootstrap approval không cấp fact/rule/license approval. Source authorities ngoài bindings hoặc snapshot mới cần review phù hợp, không sửa SQL trực tiếp để vượt gate. Sau mỗi apply đã được duyệt: kiểm fields/parents/business unique keys/audit/jobs/catalog và replay cùng request; sau publication kiểm thêm revision/current/evidence/refresh. Không triển khai release builder trong lô này.

## Cập nhật sau approval A2

Các mục chuẩn bị phía trên là hồ sơ lịch sử. Người dùng đã duyệt đúng A2 SHA `b032e83495c619177c3aa22442f79fefc2c0405f0d4000ba70db6bbad41863fd`, request `95b1d889-09d3-40e2-8d17-1063e4a73e7a`. Đã apply bằng reviewer DEV, kiểm expected/actual và gọi lại **apply --file cùng request**: không thêm rows/jobs/audit/version. Không dùng lệnh publication replay cho bootstrap.

Manifest registry thật: `0f12e947-9355-4bc2-8a05-309474c2415f`; decision thật: `426241ec-ba2c-5923-9e96-1e8461d571b3`. Export và checkpoints private ở `state/publication/a2-approved-20261018/`; không overwrite các manifests/conditional drafts cũ. Xem reports/ptit-blocker-decisions.md về IDs, counters và ranh giới approval.

B1 mới tại `state/publication/a2-approved-20261018/decision-b1.draft.json`, request `23977c8a-d4f5-4b56-a1cc-9040d843167a`, dùng parent/head A2 thật và đã qua plan read-only. **Chưa được duyệt/apply**. Người phụ trách cần duyệt chính file/hash/phạm vi B1 trước khi apply; B2/B3/C giữ conditional. Không dùng kết quả plan hoặc approval A2 để apply B1. Sau mỗi parent được apply, materialize quyết định kế tiếp bằng IDs/head thật và request riêng, giữ bản cũ.

## Cập nhật sau approval B1

Mục B1 chờ duyệt phía trên là trạng thái lịch sử tại commit07ad75a. Người dùng đã phê duyệt riêng B1 SHA `932a5f3c215e816916fba4e79241fe5d90f6c6c913b7deecd3b1adb3be7482ea`, request `23977c8a-d4f5-4b56-a1cc-9040d843167a`. Đã đọc lại PDF cache p12/p20 và header BVH ởp11, kiểm hash/binding/head/parent/role/schema rồi apply qua CLI reviewer. Kiểm expected/actual và gọi lại apply cùng file/request không thêm dữ liệu.

Decision thật `684a8f28-1faa-54d9-a57a-cfca85820cc2`; registry manifest thật `bd0c37a0-0036-432a-9391-c5e451a4dc21`. Checkpoints và export CLI ở private `state/publication/b1-approved-20261018/`. Không tạo script vận hành mới hoặc thay CLI/framework; các thao tác ghi nghiệp vụ đều qua CLI hiện có.

B2 mới tại `state/publication/b1-approved-20261018/decision-b2.draft.json`, request `f59e9c89-a7dd-40a7-8038-5b19f612f6fb`, dùng Program ID và registry head B1 thật. Đã đọc riêng BVS PDFp13/p20 và chạy plan read-only, **chưa approval/apply**. Nếu được duyệt, kiểm lại exact file/hash/request/head/packet/evidence/role rồi mới apply; B3/C/D không được kế thừa approval. Không dùng publication replay cho bootstrap; chỉ gọi lại apply cùng request đã được duyệt để kiểm idempotency.

## Cập nhật sau approval B2

Mục B2 chờ duyệt phía trên là trạng thái lịch sử tại commit9b90fd2. Người dùng đã duyệt riêng B2 SHA `563d6a93777d4e7c205ce42f917871dfa50333a39d420b758e58061a4f5ed5a0`, request `f59e9c89-a7dd-40a7-8038-5b19f612f6fb`. Đã revalidate exact bytes/binding/B1 head/Program/schema/reviewer, đọc lại PDF cachep13/p20, apply đúng CLI và kiểm actual/replay cùng request không thêm dữ liệu. Không sửa reason/file đã duyệt hoặc dùng approval B2 cho B3/C/D.

Decision thật `be5546cf-4562-5d9b-8ac5-6326aad319b0`; registry manifest `8baaa2cc-a703-4563-b6a3-f4c04dea58f3`; Offering BVS `257a579f-e7a6-5a6b-8fd4-8a43f9d74ecb`. Export CLI/checkpoints private ở `state/publication/b2-approved-20261018/`. Mọi ghi nghiệp vụ qua CLI hiện hữu; không tạo script vận hành hoặc framework mới.

B3 mới tại `state/publication/b2-approved-20261018/decision-b3.draft.json`, request `c9e0bdad-e392-49e4-8d2c-0bb23cd3413f`, dùng University và expected heads thật sau B2. Đề nghị Program CNTT và Offering BVH2024/mã7480201 không hậu tố; evidencep11/p20, đối chiếu tách CLC/UDU/LK ởp12 và chương trình Việt–Nhật dự kiến ởp13. Không gán track STANDARD từ cách gọi “CNTT chuẩn”. Plan read-only đã đạt, **chưa approval/apply**; C/D còn conditional. Xem báo cáo blocker decisions về exact hash và impacts.

## Cập nhật sau approval B3

Mục B3 chờ duyệt phía trên là trạng thái lịch sử tại commitc5ff6d0. Người dùng duyệt riêng B3 SHA `1bb13962fc2b97e9eb46dec44be2dbfb3fa4dafa8cf0b93ed1447bf0a69ef578`, request `c9e0bdad-e392-49e4-8d2c-0bb23cd3413f`; đã kiểm hash/binding/head/University/schema/reviewer/evidence rồi apply qua CLI, đối chiếu actual và gọi lại apply cùng request không thêm dữ liệu. C/D không thừa hưởng approval.

Decision `4c2eb582-b43a-51a6-bbad-5cb2c137a116`; registry manifest `c4420433-a883-4ca7-8f0f-9d90b37ed0c5`; Program CNTT `c5423f44-3ffd-5c2f-91b0-e96bea3464bb`; Offering `659f29e9-911c-5db9-9af1-cdbef363df82`. Export/checkpoints mới ở private `state/publication/b3-approved-20261018/`; không thay CLI, script vận hành, migration hoặc manifests cũ.

C1 mới `decision-c1.draft.json` trong thư mục private trên, request `7025e964-946c-447f-a0a1-12c64e165587`, đã qua plan read-only, **chưa approval/apply**. Primary snapshot chuyển từ anchor HTML của conditional cũ sang PDFgốcp16 có max30; basis evidence thêm locators đúng hai thông báo gốc. Min0 được trình là derivation miền, không ngưỡng xét tuyển hoặc source quotation; không duyệt công thức/rounding/scoring DSL.

Scale schema khóa method/year, không có Offering membership FK: ba Offering IDs ghi trong command/basis_description là phạm vi đề nghị duyệt, không giả constraint mới. Khi review D vẫn cần source authority đúng context, active scale review và quyết định fact/scope riêng; không dùng can_apply của C1 như quyền publication. C2 round/population/source_aggregate/TTNV vẫn chưa duyệt; named-notice round không là “đợt1”, TTNV chỉ tại điểm bằng cutoff. Xem reports/ptit-blocker-decisions.md về hash/impact và C2.
