# T09 DEV smoke release — thiết kế và kế hoạch

Yêu cầu trực tiếp ngày 19/10/2026 cho phép implementation, register release DEV,
coalesce refresh và commit/push; không publication mới hoặc public deployment.
Thực hiện inline trong checkout hiện tại, giữ `.vscode/` và private history.

## Contract được chọn

- Một version = toàn bộ current verified cutoffs của published scopes, offering
  year 2024–2026. Không filtered release. Dùng `count_canonical_cutoffs()` trong
  cùng REPEATABLE READ transaction với version, facts, labels, evidence, provenance.
- `services/data/releases`: snapshot/coverage, artifact storage, builder và CLI.
  JSON UTF-8 NFC, keys sorted, Decimal strings, null giữ nguyên; records sorted ID.
  Artifacts `cutoffs.json`, `coverage.json`, `manifest.json` tại ignored state/releases.
  SHA manifest tính từ bytes thật, không đặt SHA của chính manifest bên trong nó.
- Session advisory lock serialize DEV builders trước khi mở snapshot (publication
  vẫn hoạt động). Atomic directory rename sau ghi/fsync/verify. Staging crash được
  giữ lại; completed orphan được verify/reuse, không overwrite. Replay đọc registered
  artifacts, không tái dựng version cũ từ is_current. Integrity conflict dừng build.
- Tách snapshot/files khỏi transaction register. Claim jobs durable 5-minute lease,
  token fencing, expired/retry recovery; register + job success + audit atomic sau
  verify. Crash trước commit không có release giả; giữ files và retry sau lease.
- `0004_releases` additive guards; dedicated `eduradar_release_builder` NOLOGIN
  capability và DEV login riêng. SELECT đúng các bảng input; INSERT release/audit;
  UPDATE chỉ các cột lease/status/payload cần thiết của refresh jobs, có DB guard
  chặn jobs khác và immutable requested version. Không quyền UPDATE/DELETE release.
- Jobs <= snapshot version được succeeded với result requested/actual version,
  actual release ID/hash và outcome built/coalesced; không tạo releases 1/2.
- Manifest ghi builder/schema/filter/count/file hash/size, build time riêng publication
  times, Git/code/lock và provenance registry/alias/parser/normalizer từ lineage thật.

## Thực hiện và bằng chứng

1. [x] Git/schema/counters/IDs/spec provenance và private row/file baseline.
2. [x] Tests PostgreSQL synthetic riêng: exclusion/evidence fanout, fidelity, snapshot
   publication race, concurrency/replay, corruption, write/register/finalization crash,
   frozen coverage, roles/DB guards, coalescing. Quan sát RED trước implementation.
3. [x] Implement snapshot/coverage/storage + CLI plan/build/inspect/verify/replay;
   migration/roles/guards giữ ORM guard hiện hữu. Regression tests và lint/type/lock.
4. [ ] Full pytest, publication/health, empty/upgrade Alembic checks; review toàn diff.
5. [ ] Migrate/provision có audit, chạy DEV bằng dedicated login; verify/replay/counters,
   historical row/file digests. Expected: +1release, 0jobs mới, 3jobs updated;
   +1capability provision/+1dedicated login audit/+3lease audit/+1register audit/
   +3success audit = +9audit. Login provisioning tách audit riêng để truy vết quyền thực tế.
6. [ ] README/contract/runbook/report/WBS; commit paths đã review, push, CI exact SHA.

## Review focus

Snapshot không đổi nhãn khi publication đồng thời; stale lease không finalize;
registered corruption không auto repair; orphan retry không đổi timestamps/hash;
job history requested version bất biến; reader/owner không là application runner.

Smoke gate: 1 PTIT / 2024 / THPT / 2 Program / 3 Offering / 3 cutoffs;
3/20.000, thiếu 19.997. Chưa nghiệm thu toàn T09/Phase 1 hoặc đa nguồn.

## Execution ledger

Snapshot preflight DEV read-only đạt count3/lineage thật. 23 release tests pass, bao gồm
RED→GREEN cho cached-release recovery, NULL lease, actual_version bắt buộc và owner job
maintenance. Full regression đầu tiên phát hiện test temp sai guard và pg_has_role của
superuser, đã sửa môi trường/guard; full546 đạt, full cuối trên23 release tests đang kiểm.
Reviewer độc lập không còn blocker. Giữ checkout hiện tại theo yêu cầu; không worktree mới.
