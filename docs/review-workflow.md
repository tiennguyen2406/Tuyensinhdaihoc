# Review workflow T08 — CLI quản trị local

Đã provision hai danh tính kỹ thuật DEV theo ủy quyền 18/10/2026; chưa gán một người phụ trách nghiệp vụ hoặc tạo approval. Không dùng tài khoản kỹ thuật như bằng chứng người phụ trách đã duyệt. Đọc publication-contract.md trước khi thực hiện; fixtures tests không dùng làm hồ sơ thật.

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
