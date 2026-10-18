# T08 — reviewed transactional publication pilot

Ngày 18/10/2026 (Asia/Bangkok). Tiếp tục `codex/crawler-pilot` từ T07 `04feb369bca81c983c475d1cd3f5ee6fe57c0282`, không reset lịch sử. Không có AGENTS.md trong repo/ancestors hoặc thư mục sources/ trong checkout này; đọc đặc tả Desktop được tham chiếu, không sửa tài liệu nguồn. Provenance/lockfile/manifests lịch sử T05–T07 giữ nguyên.

## Số liệu dữ liệu thật

| Chỉ số | Trước T08 | Sau implementation/preview |
|---|---:|---:|
| Raw / normalization / resolution envelopes | 215 / 215 / 215 | 215 / 215 / 215 |
| Candidate results (cutoff / tuition) | 95 (91 / 4) | 95 (91 / 4), unresolved |
| Pending entity / alias proposals | 72 / 6 | 72 / 6 |
| Hồ sơ được chọn cho lô review | 0 | 3 private preview files |
| Review decisions / registry versions T08 | 0 / 0 | 0 / 0 |
| Canonical entities tạo hoặc link | 0 | 0 |
| Resolution runs mới / publication attempts đã apply | 0 / 0 | 0 / 0 |
| Current cutoffs / tổng cutoff revisions / evidence | 0 / 0 / 0 | 0 / 0 / 0 |
| Publication conflicts / audit events / quality_issues | 0 / 0 / 0 | 0 / 0 / 0 |
| Tổng jobs / publication_request / refresh_serving | 17 / 0 / 0 | 17 / 0 / 0 |
| dataset_version / dataset_releases | 0 / 0 | 0 / 0 |
| Raw snapshots / fetches | 6 / 6 | 6 / 6 |
| Crawl pilot | paused, used 5/5 | paused, used 5/5 |

Input vẫn là T06 job `7bc439bf-a6d7-4beb-bf03-bb47956c5383`, T07 job `e4ede9f6-feed-4ce9-aac4-fc9237eeee56`. 118 blocked attempts và 166 inputs chưa typed adapter vẫn giữ nguyên trong frozen T06; không tự giải phóng numeric/header/scope ambiguity. Issues, raw và preflight crawl paused 1/2 giữ nguyên. Không OCR/download/resume/crawl thêm; quota canonical vẫn 0.

Private proof `state/publication/invariants-before.json` đối chiếu full rows theo PK của **34 bảng** trước/sau migration và sau PostgreSQL recovery: counts/SHA-256 bằng nhau. Không tính alembic_version vào invariant nghiệp vụ. Đây là kiểm sorted-row mới, không viết lại provenance T06/T07. Observations 645 rows SHA `b1c6381528ce0ddff0b5971a2f06c8be14876c2d9f283d994a11512e3147b49b`; ingest_jobs 17 rows SHA `95d65ad9bd51e1f55a4ef61102bf87d47c7675d83383b1eef7844798531ed809`. Sáu raw blobs đạt kiểm hash và byte_size, không tải lại.

## Yêu cầu → implementation → nghiệm thu

| Yêu cầu | Module tái sử dụng / phần bổ sung | Tests |
|---|---|---|
| Packet lineage / expected versions / actor | T06/T07 stores + publication packets/access/review | tampering, stale versions, privileged/pending/revoked approval blocked |
| Bootstrap không circular / registry immutable | canonical models/validators + bootstrap/review | từ zero entities tạo parents/Offering/registry; retry; bad UUID/parent/campus rollback; alias có DB actor |
| Gates / Decimal / ba khóa | validators + contract/validate | Major NULL; unknown scope/scale/evidence blocked; tuition không ép year; không float/URL/fee trong identity; predicate phải có cấu trúc |
| Transaction publisher | publish + cutoff/evidence/jobs/catalog hiện có | first scope; ba nguồn một current/ba evidence; concurrent/replay; correction/stale; conflict/late press; basis replacement; fee independence; rollback side effects |
| Core/history/quyền | roles + additive 0003 guards | reader/reviewer-only/publisher-only; forged approval/legacy-marker blocked; audit/history immutable; reader đọc Alembic head |
| Migration/health | Alembic/session/main giữ kiến trúc | empty→head; 0002→head với legacy row; replay migration; readiness/live regressions |

Chi tiết gates, fingerprints và version/refresh ở [publication-contract.md](../publication-contract.md); lệnh/quyền ở [review-workflow.md](../review-workflow.md).

## Tệp và migration

- `services/data/publication/{contract,access,packets,bootstrap,review,validate,publish,__main__}.py`: DTO Decimal, candidate binding, DB actor, bootstrap có thứ tự, preview/approval, revalidation và publisher transaction. Không thêm HTTP mutation.
- `0003_publication.{py,sql}`: additive **7 functions / 9 triggers**, bảo vệ append-only audit/manifests và T08-managed history. Không thêm bảng, sửa 0001/0002 hoặc xóa dữ liệu. Downgrade phá dữ liệu bị vô hiệu.
- `scripts/provision_publication_roles.py`, `publication/roles.py`: grants do operator chạy; không tạo login/password thật. `.env.example` thêm hai biến trống, .env nguyên vẹn và ignored.
- `tests/publication/`: fixtures PostgreSQL TEST ONLY; `tests/integration/test_schema.py` cập nhật expected head. Không đổi dependencies/uv.lock.
- README, publication contract/workflow/report, data-contract/schema-provenance và implementation plan: bàn giao đường chạy và giới hạn; không sửa reports/manifests lịch sử.

## Lô review thật cần quyết định

Chọn offline từ snapshot `19a1088e-6412-49e4-b911-73ec9146f4fa`:

| Packet | Mã trong nguồn / campus | Resolution envelope | Packet SHA-256 |
|---|---|---|---|
| 1 | 7340101 / BVH | 97259d1b-894c-4637-9e09-8c237ce15c78 | aed252aa06294031dd08c3f4784599985051804d6f53aa0f2844f0c8e7ef2fd3 |
| 2 | 7340101 / BVS | ed78a7bc-698e-41df-930d-d944c8e4d015 | 5968f630ad88cdcdb5ebb39349a4a6d3a425a0c313edcbdf341bac1cf2679db3 |
| 3 | 7480201 / BVH | 2b23a0d1-5e1e-4f93-9dff-a844d00bca86 | 1f4703c277a1aea9417e54c93a28bab9af9afdb70116fbe5404acaf4199c690c |

Header là THPT/năm tuyển sinh 2024, không lấy năm 2026 của trang làm admission_year. Raw cell/program/header/campus/URL/full locator/candidate key ở ignored `state/publication/review-batch.md`, `pilot-1.json`…`pilot-3.json`; không commit source outputs hoặc decision files nhạy cảm.

Preview thật: 0 entities/cutoffs/catalog delta, can_publish=false. Chưa có ValidatedDraft hoặc responsible reviewer hợp lệ, không áp synthetic approvals lên pilot. Các quyết định cần người phụ trách:

1. Chọn dedicated reviewer/publisher login, không gán tên từ Windows/Git.
2. Xác nhận University/code system, BVH/BVS campus mappings; Program/Offering 2024, mã xét tuyển, track/language/training mode. Major có thể NULL.
3. Xác nhận source authority đúng các ô lịch sử/method THPT, không duyệt toàn trang 2026.
4. Cung cấp cached evidence scale/max_score/basis, combination hoặc confirmed_none, round/population/conditions. Không suy max_score=30 hoặc mặc định MAIN/GENERAL; tài liệu chưa cache cần task tải riêng.
5. Review score/cell và publication từng packet sau bootstrap version mới + T07 mới. Thiếu scoring rule ghi unavailable_rule, không giả công thức.

## Kiểm tra thực tế

Baseline trước sửa: `uv run pytest -q` — **461 passed in 86.63s**. Implementation đạt 501 tests; sau đó thêm các ca chặn canonical predicate rỗng/unknown version và giữ structured expression trong identity. Các ca mới đã chứng minh RED trước sửa và GREEN sau sửa. Không diễn giải kết quả fixtures thành xác nhận tính đúng dữ liệu tuyển sinh thật.

Kết quả cuối trước commit:

| Lệnh/kiểm tra | Kết quả |
|---|---|
| uv run pytest -q --tb=short | **506 passed in 162.37s** |
| uv run ruff check . | All checks passed |
| uv run ruff format --check . | 124 files already formatted |
| uv run mypy | No issues in 55 source files |
| uv lock --check | Đạt, dependencies/lock không đổi |
| uv run alembic current | 0003_publication (head) |
| uv run alembic check | No new upgrade operations detected |
| git diff --check / staged --check | Đạt |
| HTTP /health/live, /health/ready sau recovery | 200 / 200 |
| CLI list/inspect/plan + 34-table/raw invariants | Đạt, không ghi dữ liệu thật |

Không còn check yêu cầu nào bị bỏ qua; real apply/replay được giữ chưa chạy vì chưa có approval, đã kiểm trên fixtures. CI dùng workflow hiện hữu, PostgreSQL riêng và tests offline; chưa cần đổi workflow/dependency.

`uv run alembic upgrade head` đã áp dụng trên DB dự án; current=`0003_publication (head)`, check=`No new upgrade operations detected.` Tests migration kiểm database trống và đường nâng cấp 0002 có legacy cutoff. Databases/logins test được giữ, không DROP theo ràng buộc bảo toàn.

CLI list/inspect/plan thật exit 0; list 95 packets. Apply/replay trên dữ liệu thật không chạy vì chưa có quyết định hợp lệ; end-to-end đã chạy với TEST ONLY DB. Không provision grants/memberships cho người phụ trách trên DB dự án.

Sau khi tiếp tục phiên, Docker Desktop đang dừng: live=200, ready=503 với body an toàn database:unavailable; test kết nối khi đó lỗi setup. Khởi động lại Docker/container với volume cũ, chờ PostgreSQL crash recovery/fsync; sau recovery **live=200, ready=200**, 9 T08 triggers còn đủ và invariants 34 bảng bằng nhau. Reader role có regression test phát hiện thiếu SELECT alembic_version; đã thêm duy nhất quyền đọc revision và test đạt. Không sửa health để che lỗi DB.

## Review, giới hạn và mức hoàn thành

Reviewer agent chỉ đọc **các đoạn mã được cung cấp**; công cụ không cho đọc toàn checkout. Finding revoke approval đã publication nhưng fact vẫn serving được sửa và có regression test. Không tuyên bố full-repo independent/security review.

Non-superuser tests chứng minh boundary local. Group roles/logins TEST ONLY tồn tại ở PostgreSQL cluster/test DBs; chưa chạy grants script trên DB dự án hoặc provision danh tính người phụ trách thật. Owner là trusted maintainer; chưa có production OIDC/RBAC, sealed DB API hoặc lifecycle secrets.

Lát cắt hỗ trợ cutoff và university aliases từ proposals có sẵn. Publisher tuition/scholarship/exam/rules, program/method alias governance/new-proposal UI và dependency-level withdrawal/conflict resolution còn thiếu. Revocation đã applied hoặc bootstrap khi có current fact bị chặn bảo thủ; source authority đang serving không bị ghi đè tùy tiện. Conditions expression là canonical mapping do người review xác nhận, chưa là DSL/equivalence engine. Preview bootstrap không thực thi toàn bộ SQL constraints bằng transaction giả; apply có thể bị constraints chặn và rollback. Refresh enqueue nguyên tử, worker/release builder T09 chưa có.

T08 đạt phạm vi kỹ thuật đã có tests và chuẩn bị hồ sơ thật, chưa kết luận T07 nghiệp vụ/T08 toàn bộ/T09/quota20.000 đạt. Bước kế tiếp là responsible review, bootstrap immutable registry, T07 run mới rồi review publication; không vượt blockers bằng suy đoán.

Commit/push và CI exact SHA được xác nhận trong bàn giao cuối cuộc trò chuyện. Báo cáo được ghi trước commit nên không tự khẳng định CI đã chạy chỉ từ checks local. Không merge main hoặc deploy production.
