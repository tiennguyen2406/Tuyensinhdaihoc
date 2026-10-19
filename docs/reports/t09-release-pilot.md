# T09 internal DEV smoke release — 19/10/2026

Implementation: `services/data/releases`, migration additive `0004_releases`, dedicated
release capability và CLI. Contract/runbook: ../release-contract.md; kế hoạch:
../plans/2026-10-19-t09-release-pilot.md. Không đổi facts hoặc approvals A2/B/C/D.

Baseline kiểm thực tế: branch codex/crawler-pilot, HEAD4ad84c3cd0878a85d8fd0ac809e09c1e7e091747,
origin đúng repository; chỉ .vscode/ untracked trước implementation. Spec gốc SHA-256
c3745329543e433bd62cf58e4a6df4c827ea54b5876f48f8c42e33d5aabf04c5 khớp provenance.
Schema0003, catalog3, canonical3 đúng ba UUID publication, observations863/jobs55/audit36,
releases0, refresh1/2/3 queued. Private baseline giữ row/file digests.

Tests T09 synthetic riêng đã kiểm snapshot/count/fidelity, publication race, concurrent
workers, replay, checksum/missing file, write/register/finalization failures, orphan recovery,
expired lease/fencing, registered-release job recovery, DB guards và real CLI/reader denial.
Review độc lập đã xác nhận các sửa recovery/NULL guards/provenance; không còn blocker.

## Kết quả DEV thật

Đã migrate/provision, chạy plan/build/verify/replay/build retry qua CLI. Release nội bộ:

- ID: `396ccd8b-1193-43dd-a08a-bb19e639dd56`; version **3**.
- URI: `file:///C:/Users/HUYNH%20HAU/Documents/ChatGPT/DiemThiDaiHoc/state/releases/canonical/version-3/manifest.json`.
- Manifest SHA-256: `b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`.
- Code commit trong manifest: `4b7cc538a4e2d24ff20b52cab48b7711702b6f62`, relevant tree clean,
  có hashes từng implementation file. Lock SHA-256:
  `fad74eacacc0e8b1075f8120a3c7b97023b7d6cce4bc324fa25b82557098642f`.
- Build time `2026-10-18T23:38:19.208268+00:00` = **19/10/2026 06:38:19 UTC+7**;
  không là publication time của facts. Các publication timestamps cũ giữ nguyên.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| cutoffs.json |60240|ae1667793562be7018ffcfabcf382894dc234604d8d33bb4ac2d351c537d7173|
| coverage.json |1566|33cef8d1d126c1b5ecdbc08319157c7ed6289ae0a93ebee823fb0d2efcc4339a|
| manifest.json |28778|b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90|

Files cùng directory manifest, ignored/private; không đưa source bodies hoặc secrets vào Git.
Manifest checksum tính trên bytes thật, không có checksum tự tham chiếu. Registered row
metadata khớp manifest; SQL count/export unique IDs/manifest count đều **3**. Builder dùng
counting helper trong cùng REPEATABLE READ snapshot, không hardcode PTIT IDs làm filter.
Đối chiếu hậu kiểm ba IDs với bàn giao chỉ là assertion về pilot thực tế.

## Coverage frozen và quota

Một PTIT, năm2024, THPT; hai Program (QTKD/CNTT), ba Offering. BVH2 cutoffs, BVS1.
QTKD2/CNTT1; mỗi Offering1. Ba canonical rows, ba publication groups, ba evidence rows,
ba exported revisions (mỗi cutoff revision1). Không nhân source_aggregate theo tổ hợp.
Major/track/language unknown ở cả3facts; không scoring rules được tham chiếu, cả3 giữ
`unavailable_aggregate_scope`. Condition payloads/fingerprints và TTNV13/3/5 nguyên nghĩa.
2025/2026 chưa có verified data trong release, không suy không tuyển sinh.

**3/20.000, còn thiếu19.997** theo counting policy. Smoke release chưa đạt pilot đa nguồn,
chưa nghiệm thu toànT09 hoặc Phase1; không có score/conversion evaluator/admission guarantee.

## Refresh, expected/actual và audit

| Requested version / job ID | Status | Outcome | Actual release version |
|---|---|---|---:|
|1 / 1e1bfa99-0905-44b1-96c0-f622e4a30aeb|succeeded|coalesced|3|
|2 / 6e23b47e-a989-483f-ae36-e429c08cd4a6|succeeded|coalesced|3|
|3 / db3948a9-0bca-47c9-b1f8-cb01d1d760d0|succeeded|built|3|

Mỗi job attempts1, lease được clear, requested dataset_version1/2/3 giữ nguyên, result
ghi release ID/hash/actual_version3. Không có releases1/2 và không tạo jobs mới.

| Đại lượng | Baseline | Expected = actual sau T09 |
|---|---:|---:|
|catalog version|3|3|
|current verified published canonical|3|3|
|observations|863|863|
|ingest jobs|55|55|
|audit events|36|45|
|dataset releases|0|1|
|scope/cutoff/evidence|3/3/3|3/3/3|

9audit mới:37 capability provision;38 dedicated DEV login configuration;39–41 leases;
42 register_release;43–45 refresh_succeeded. Đây là audit kỹ thuật theo task authorization,
không approval nghiệp vụ mới. Provision roles và login có2audit riêng để truy vết quyền.
Register release + finalize3jobs + audit42–45 cùng xmin **40584**; durable claim trước đó
là transaction riêng. Không tăng catalog, sửa scores/scopes/conditions/authority hoặc A2/B/C/D.

Login `eduradar_dev_release_builder` chỉ có release group, không reviewer/publisher,
không owner/SUPERUSER/CREATEDB/CREATEROLE/BYPASSRLS. SQL xác nhận INSERT release=true,
UPDATE/DELETE=false; reader INSERT/UPDATE/DELETE=false. Credentials mới riêng và ACL hạn chế;
không sửa credential file publication hiện hữu. Guard và ORM boundary giữ nguyên.

## Integrity, replay và bảo toàn

Verify/replay read-only và build retry đều verified/cached=true, cùng release/hash/artifacts.
Row digests **cả34tables không đổi giữa after-build và after-replay**: không thêm releases,
jobs/audit hoặc catalog version. Hậu kiểm baseline từng PK: chỉ3refresh job rows cũ thay đổi
theo contract; mọi863observations/52jobs khác/36audit cũ/canonical parents/facts/source/crawl
history giữ nguyên. Không chỉnh frozen T05/T06/T07 envelopes/manifests.

22source snapshots đã đọc lại local blobs, SHA/size đều khớp. Intake baseline326files
(303publication +22raw +1.vscode) nguyên SHA. Bổ sung đối chiếu **357historical private files**
từ baseline D trước đó, gồm cả normalization/resolution và các checkpoint khác:357/357khớp.
Không xóa hoặc ghi đè old files. Các checkpoint T09 mới ở state/releases/t09-20261019/.

## Lệnh và checks thực tế

Migrate/provision qua operator owner trong một transaction; application build dùng login
riêng. CLI subprocess nạp credentials vào environment, không có password trên argv/stdout.
Các invocation thật (sau nạp RELEASE_DB_USER/RELEASE_DB_PASSWORD từ private ACL storage):

```powershell
uv run --offline python -m services.data.releases plan --output state/releases/t09-20261019/plan.json
uv run --offline python -m services.data.releases build --root state/releases/canonical --output state/releases/t09-20261019/build.json
uv run --offline python -m services.data.releases verify --version 3 --output state/releases/t09-20261019/verify.json
uv run --offline python -m services.data.releases replay --version 3 --output state/releases/t09-20261019/replay.json
uv run --offline python -m services.data.releases build --version 3 --root state/releases/canonical --output state/releases/t09-20261019/build-retry.json
uv run --offline python -m services.data.releases inspect --version 3 --output state/releases/t09-20261019/inspect.json
```

Local full pytest: **548passed208.38s**, gồm23T09tests và publication/health regressions.
Fixtures synthetic dùng PostgreSQL test riêng, không pilot DB; test DBs được giữ lại.
Ruff check/format, mypy62sourcefiles, uv lock87packages đạt; Alembic current0004head,
check:No new upgrade operations detected; git diff checks đạt. Không dependency mới.
ASGI health/live và ready200; không dùng kết quả này để claim HTTP server đang chạy.

Các lượt đầu chưa đạt đã được giữ log: test temp trong checkout bị raw-storage guard;
refresh guard coi superuser là member mọi role, ảnh hưởng crawler/parser/normalization và
publication tests; hai assertions Alembic head cũ. Đã sửa nguyên nhân và full suite cuối đạt.
Review phát hiện cached job recovery, NULL lease/actual_version, unrelated DELETE và parser/
dirty provenance; các sửa có tests thực thi, reviewer cuối không còn blocker.

CI exact SHA của commit bàn giao được kiểm **sau push**, lưu checkpoint riêng ci-final.json;
không suy CI success từ local tests hoặc nội dung báo cáo trước khi push.

## Giới hạn và T10

Đủ điều kiện bắt đầu **T10 trên release smoke nội bộ**: consumer có stable version,
immutable facts/labels/source references/coverage, verified checksums và replay. Không còn
blocker T09 cho lát cắt Search này; consumer phải hiển thị unknown/missing years và aggregate
computation unavailable. Chưa xây T10 trong task này.

Chưa kiểm throughput/multi-host load, power-loss durability Windows, backup/restore hoặc
remote object store, staging/public serving/production RBAC. OS storage admin là trust boundary.
Không public Internet, crawl thêm, Score Engine/SNA, deploy hoặc merge main.
