# T09 — internal DEV release contract / runbook

`canonical-release/1`, `release-builder/1.0.0`; migration additive `0004_releases`.
Một catalog version chỉ có một dataset release toàn bộ, không filtered releases.
Đây là snapshot canonical nội bộ, không public distribution hoặc Phase 1 acceptance.

## Snapshot và dữ liệu

Builder lấy session advisory lock riêng T09, commit lock acquisition rồi mở transaction
REPEATABLE READ READ ONLY. Catalog version/changed_at, `count_canonical_cutoffs()`,
facts, labels, scales/rules, evidence/source metadata, lineage và coverage cùng snapshot.
Predicate đúng helper: current + verified + published scope + offering year 2024–2026.
Không join evidence khi count; SQL count = exported unique cutoff IDs = manifest count.
Publication đồng thời được phép: snapshot cũ giữ version cũ, không đọc version mới để đổi nhãn.
Không tái dựng version 1/2 từ current data. Snapshot không giới hạn theo ba UUID PTIT.

`cutoffs.json` đóng băng cutoff IDs/revisions/fingerprints/payload/publication times,
University–Program–Offering, method, scale/basis, scope/conditions, optional scoring rule,
combination/subjects nếu được tham chiếu, source URLs/snapshot hashes/locators và lineage.
Không thực thi rules. `source_aggregate` giữ một fact và
`computation_status=unavailable_aggregate_scope`. Major nullable; DDL sentinel
UNSPECIFIED vẫn giữ ở offering, semantic track/language unknown biểu diễn thêm null.
Không xuất actor/review reason, toàn jobs/audit, raw fields hoặc source bodies.
Lineage chỉ chọn IDs, versions, hashes và field evidence; parser extraction provenance
và chữ ký T06/T07/registry/alias giữ căn cứ từ observations/manifests thật.

JSON UTF-8 NFC, sorted keys, compact separators, LF cuối file; Decimal chuỗi chính xác,
null nguyên nghĩa; records và các references sắp ổn định theo IDs. `coverage.json`
được tính từ frozen records, verify cũng tính lại từ artifact; không query live facts.
Counts theo university/year/method/campus/Program/Offering; canonical/group/evidence/
revisions tách biệt. Missing years nghĩa chưa thu thập/chưa xác minh, không là không tuyển.

Manifest ghi schema/builder/filter/counts, file size/SHA-256, snapshot digest, Git commit,
relevant code hashes/dirty flag/lock và input provenance. `artifact_built_at` khác fact
`system_valid_from` và release DB `published_at` (registration). Manifest không chứa hash
của chính nó; `dataset_releases.manifest_sha256` là SHA-256 bytes manifest thật.

## Files, registration và recovery

Mặc định ignored `state/releases/canonical/version-N/` có `cutoffs.json`, `coverage.json`,
`manifest.json`. Có thể chọn private root ngoài checkout. Ghi exclusive vào staging UUID,
flush/fsync, verify rồi atomic directory rename; fsync directory trên Unix. Windows dùng
fsync file + atomic same-volume directory rename, chưa kiểm power-loss durability.
Không overwrite final directory; giữ staging nếu crash. OS-level storage administrator
là trust boundary, file mất/hỏng sau registration là integrity incident.

Completed orphan cùng version phải khớp snapshot digest nếu retry current snapshot;
reuse bytes/timestamp/provenance ban đầu. Nếu catalog đã tiến, `build --version N` chỉ
recover completed verified orphan N, không tái dựng từ current. Không có artifact cũ thì
integrity conflict. Registered releases luôn verify manifest hash, files, counts, snapshot
binding và coverage trước trả kết quả; thiếu/hỏng dừng, không tự sửa hoặc xóa lịch sử.

Sau files hợp lệ, builder claim due queued/retry_wait hoặc expired leased refresh jobs
<= snapshot version bằng SKIP LOCKED, token mới, attempts+1, lease 5 phút và audit.
Claim commit riêng; register + job finalization + audits cùng transaction sau verify lần nữa.
Register/finalize lỗi: rollback release/success, chuyển leases còn hợp lệ sang retry_wait,
error code an toàn. Process chết: lease hết hạn cho build sau recover. Build cached vẫn
phục hồi due/expired jobs; `replay` chỉ đọc, không phục hồi jobs.

Version gốc trong job payload không đổi. Result ghi requested_version, actual_version,
release_id/hash và `built` nếu bằng version, `coalesced` nếu requested thấp hơn. Cả hai dùng
schema status `succeeded`; không có enum superseded và không giả releases lịch sử.
Jobs future hoặc chưa đến hạn/live lease giữ pending, build sau phục hồi; không coi việc
verify artifact thành xác nhận tất cả jobs hoàn tất. Một builder DEV tại một thời điểm;
lock timeout 10 giây có thể yêu cầu retry, chưa kiểm throughput đa host.

## Quyền và vận hành

Owner chỉ migrate/provision. Dedicated application login có `eduradar_release_builder`
NOLOGIN group, không owner/SUPERUSER/CREATEDB/CREATEROLE/BYPASSRLS. Không kế thừa reviewer/
publisher. Group có SELECT các bảng input, INSERT release/audit, USAGE audit sequence,
UPDATE các cột refresh lease/status/payload cần thiết. DB trigger chặn mutate jobs khác,
requested version/identity immutable, yêu cầu audit cùng transaction và release binding
trước success. Release UPDATE/DELETE bị trigger chặn và application roles không có grants.
ORM guard cũ vẫn từ chối DatasetRelease; builder dùng SQLAlchemy Core + DB guards theo
publication pattern. Không tăng catalog hoặc tạo cutoff/revision/job mới.

```powershell
uv run alembic upgrade head
uv run python -m scripts.provision_release_roles
```

Provision tạo group/grants và một audit; không tạo login/password, không đổi `.env`.
Operator cấu hình dedicated DEV login riêng; private credentials ở
`state/releases/access/local-dev-credentials.json`, ACL chỉ user hiện tại. Không in file,
password/DSN, đưa credentials vào argv hoặc commit. Nạp `RELEASE_DB_USER` và
`RELEASE_DB_PASSWORD` vào môi trường tiến trình cùng lúc; unset sau khi chạy.

```powershell
uv run python -m services.data.releases plan --output state/releases/plan.json
uv run python -m services.data.releases build --root state/releases/canonical --output state/releases/build.json
uv run python -m services.data.releases inspect --version 3
uv run python -m services.data.releases verify --version 3
uv run python -m services.data.releases replay --version 3
uv run python -m services.data.releases build --version 3 --root state/releases/canonical
```

`plan`, `inspect`, `verify`, `replay` dùng read-only transaction; output files optional,
exclusive create, chỉ private ignored/outside checkout. Plan cần lineage input read grants;
reader có thể inspect/verify/replay từ dataset_releases + local artifact read access.
Build từ chối owner và reader, yêu cầu schema current; không tự migrate/provision/fetch.
Login kỹ thuật không tự là approval mới; task chỉ materialize facts đã được duyệt.

## Kiểm chứng

Tests riêng `tests/releases` dùng synthetic PostgreSQL DB và dedicated logins, không pilot DB.
Full pytest gồm publication/health/crawler regressions. Migration upgrade từ 0002/0003
giữ dữ liệu và Alembic metadata check. Xem `reports/t09-release-pilot.md` cho các lệnh,
release/hash/counts/replay/CI và những giới hạn thực tế của lần chạy DEV.
