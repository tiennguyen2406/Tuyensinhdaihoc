# TuyenSinhDaiHoc

Nền FastAPI/PostgreSQL cho dữ liệu tuyển sinh Việt Nam 2024–2026. Có 31 bảng nghiệp vụ theo DDL EduRadar, 3 bảng vận hành crawler bổ sung, Alembic, health checks và CI. Crawler tải raw; lát cắt T05 có parser HTML/PDF số offline và observations chưa xác minh. T06 có normalization offline có phiên bản, giữ nguyên raw observations và tạo candidates chưa xác minh. Chưa có canonical cutoffs production, Score Engine hay giao diện.

## Cài đặt (PowerShell tại gốc repository)

Cần Docker Desktop chạy Linux containers, uv 0.13.1 và Python 3.12.15. Giữ nguyên .env đã có:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
notepad .env
uv python install 3.12.15
uv sync --locked
```

Điền POSTGRES_PASSWORD riêng trong .env; không commit. API native Windows dùng POSTGRES_HOST=127.0.0.1; API trong container dùng service postgres. Biến môi trường đã export ưu tiên hơn .env. CRAWLER_RAW_DIR mặc định state/raw (bị Git bỏ qua), có thể đặt đường dẫn riêng ngoài checkout. Không đặt raw vào thư mục mã nguồn, không công khai raw khi chưa có quyền phù hợp.

## Database và API

```powershell
docker compose --env-file .env -f infra/compose.yaml up -d postgres
docker compose --env-file .env -f infra/compose.yaml ps
uv run alembic current
uv run alembic upgrade head
uv run alembic check
uv run fastapi dev services/api/main.py
```

Operator chạy migration chủ động sau khi kiểm tra DB mục tiêu. 0001_core giữ nguyên; 0002_crawler chỉ thêm crawl_runs, crawl_host_states, crawl_schedules. Không xóa bảng/dữ liệu hoặc dùng docker compose down -v. Upgrade từ 0001 và dữ liệu có sẵn được kiểm thử riêng. Downgrade phá dữ liệu bị vô hiệu hóa.

Mở http://127.0.0.1:8000/docs. /health/live độc lập DB. /health/ready kiểm tra SELECT 1 và Alembic heads; DB lỗi hoặc schema lệch trả 503 an toàn, không tự migrate. Kết nối dùng chung services/api/db/session.py. Readiness dùng transaction read-only và statement timeout 3 giây.

## Pilot raw crawler

Chạy worker trong terminal riêng; HTTP request của FastAPI không khởi chạy crawl. Inventory 12 nguồn ở docs/source-inventory.csv, profile JSON ở config/sources. candidate là URL ứng viên; checked là đã mở được một phần nguồn; eligible là đã review kỹ thuật cho pilot giới hạn. Không trạng thái nào tự cấp quyền publication hay quyền tái phân phối snapshot.

```powershell
uv run python -m services.crawler validate config/sources/ptit.json
uv run python -m services.crawler preflight config/sources/ptit.json --budget 2
uv run python -m services.crawler start config/sources/ptit.json --budget 5
```

Preflight chỉ kiểm tra robots; không tự nâng profile lên eligible. Chỉ chạy start khi đã đọc evidence và profile eligible. Robots vẫn được kiểm tra lúc chạy, cache tối đa 24 giờ. 403/CAPTCHA đưa host vào needs_review, không có chế độ bypass; operator cần kiểm tra nguồn trước khi cân nhắc một đợt mới. Quyền sao chép/tái phân phối vẫn cần xác minh riêng. Kết quả pilot thực tế trong docs/reports/crawler-pilot.md.

Mỗi start in run_id. Trong các lệnh sau, thay RUN_UUID bằng UUID đó; SNAPSHOT_UUID lấy từ bảng source_snapshots/báo cáo. Không gõ nguyên placeholder:

```powershell
uv run python -m services.crawler stats RUN_UUID
uv run python -m services.crawler stop RUN_UUID
uv run python -m services.crawler resume RUN_UUID
uv run python -m services.crawler work RUN_UUID --worker worker-2
uv run python -m services.crawler replay SNAPSHOT_UUID
```

stop ghi trạng thái bền vững; request đang tải được phép hoàn tất. Ctrl+C dừng tiến trình, lease phục hồi sau 5 phút. resume tiếp tục frontier, không tạo lại jobs đã hoàn thành. Hết budget thì pause; chỉ tăng có chủ ý bằng resume RUN_UUID --additional-budget 2. Budget tính mọi lần cấp request, gồm robots/redirect/retry; số request HTTP thực tế không vượt budget. Retry-After dài được lưu rồi worker trả quyền điều khiển; chạy work lại khi đến hạn, không busy-wait. Hai worker dùng cùng PostgreSQL chia sẻ host budget và SKIP LOCKED leases.

```powershell
uv run python -m services.crawler due config/sources/ptit.json --budget 5
```

Lệnh due tạo run cho nguồn đã đến lịch (HTML mặc định 6 giờ, attachment 24 giờ), không phụ thuộc việc HTML cha có thay đổi. Lệnh này chưa có daemon scheduler tự chạy. Manual start chủ động tải lại seeds và khám phá links. Replay đọc local blob, xác minh SHA-256 và liệt kê links HTML, không gọi Internet hoặc ghi facts; cần cùng CRAWLER_RAW_DIR đã dùng lúc tải.

Policy khởi đầu: depth 4, 1 request đồng thời/host, tối đa 0,5 request/giây (khoảng cách ít nhất 2 giây), robots có thể làm chậm thêm. Redirect tối đa 5, kiểm tra lại allowlist/DNS/public IP mỗi hop; kết nối ghim vào IP đã kiểm tra, TLS xác minh hostname. Không dùng proxy môi trường. Mỗi hop có giới hạn thời gian, body tối đa 25 MiB; robots 500 KiB. Tài liệu quá lớn hoặc encoding ngoài identity bị từ chối, không tải tiếp bằng cách lách policy.

Raw blob bất biến theo SHA-256, source_snapshots unique theo source/hash, crawl_fetches giữ lịch sử gồm 304. Chuỗi A→B→A dùng lại snapshot A nhưng có fetch mới. ETag/Last-Modified hỗ trợ conditional GET; sau 7 ngày tải unconditional để kiểm tra lại. Crawler không ghi observations hoặc canonical cutoffs. Parser T05 dưới đây trích xuất riêng từ snapshot; OCR/JS renderer chưa có.

## Parser T05: chạy offline từ snapshots

Đọc docs/parser-contract.md và docs/reports/parser-pilot.md để hiểu phạm vi và bằng chứng. Parser nằm trong services/data/parsers; dùng nguyên raw storage/metadata, không tải lại Internet, không resume crawl hoặc tăng budget. PDF scan đi review/OCR, không trích điểm từ ảnh. Public parse(SnapshotRef,SourceProfile) trả danh sách; runner.replay trả thêm issues/metrics.

```powershell
uv run python -m services.data.parsers list
uv run python -m services.data.parsers replay 19a1088e-6412-49e4-b911-73ec9146f4fa --output state/parser/preview.json
uv run python -m services.data.parsers parse 19a1088e-6412-49e4-b911-73ec9146f4fa
uv run python -m services.data.parsers replay f02f3e8f-b7bb-4e36-a60e-9a683afba099
```

replay chỉ preview/kiểm hash; --output chứa raw_fields nên chỉ lưu ở state/ bị bỏ qua hoặc ngoài checkout. parse ghi staging observations unverified và durable job; có issue thì job quarantined để review, vẫn giữ các mẩu raw trích được. Các lệnh này dùng profile PTIT mặc định; nguồn khác truyền --profile đường_dẫn_profile.json. Job ID được in khi parse; dùng job JOB_UUID để xem trạng thái. Không chạy trong FastAPI request.

Chạy lại cùng snapshot/parser/transform là idempotent. Thay code/profile/limits phải dùng namespace mới có chủ ý qua --revision 2 (đồng thời ghi version implementation thật), không cập nhật đè observations cũ. Nội dung khác dưới cùng version bị chặn. Thay vì tách mỗi tổ hợp/năm/phương thức, parser giữ quan hệ trong headers/cells/context; T05 chưa thực hiện normalization; T06 bên dưới xử lý riêng, entity resolution/publication còn chờ.

Locator HTML có dạng html:<CSS path> trên DOM gốc; lệnh inspect SNAPSHOT_UUID --locator 'html:...' trả nội dung ô/hàng để đối chiếu. PDF locators có trang/table/row hoặc line index và bbox trong raw_fields; scan trả issue theo trang. Không suy năm từ URL/tên file hoặc ngày đăng thành năm của từng điểm.

Kiểm tra số observations và trạng thái ngay trên DB hiện tại:

```powershell
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT transform_version, fact_kind, verification_status, count(*) FROM observations GROUP BY 1,2,3 ORDER BY 1,2,3;"
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT id, status, attempts, payload->>'snapshot_id' AS snapshot_id FROM ingest_jobs WHERE job_type='parse_snapshot';"
```

Không coi cutoff observations là canonical cutoffs: một observation có thể là cả hàng bảng nhiều năm/phương thức, còn giữ giá trị thô. T06–T08 và quota20.000 chưa hoàn thành. Fixtures parser hoàn toàn tự tạo, manifest trong tests/parsers/manifest.json; không đưa PDF/HTML nguồn thật, ảnh render hay thông tin liên hệ cá nhân vào Git.

## Normalization T06: preview/run/replay offline

Đọc docs/normalization-contract.md và docs/reports/normalization-pilot.md. Không resolve entity, thực thi scoring/conversion rules hoặc publish canonical. Chỉ chọn raw-only observations, không normalize lại output. Giữ 215 raw input gốc và normalized_fields={} của chúng; mỗi input tạo một envelope mới theo transform riêng. Số hàng observations sau T06 bao gồm cả raw và envelopes, không là số canonical cutoffs.

```powershell
uv run python -m services.data.normalization preview --output state/normalization/preview.json
uv run python -m services.data.normalization preview --snapshot 19a1088e-6412-49e4-b911-73ec9146f4fa
uv run python -m services.data.normalization run
uv run python -m services.data.normalization replay --job 7bc439bf-a6d7-4beb-bf03-bb47956c5383
```

preview dùng transaction read-only, không ghi jobs/observations; --output chi tiết chứa raw/display nên chỉ cho ignored state/ hoặc ngoài checkout. run ghi atomically một batch unverified envelopes và manifest job quarantined. Chạy lại cùng input/config/code/version không thêm hàng. Job UUID được in; dùng `uv run python -m services.data.normalization replay --job JOB_UUID` với UUID thực từ output để kiểm frozen replay. Không tăng revision/version chỉ để có thêm bản ghi. Thay code/config/lock cùng namespace bị từ chối, phải bump normalizer implementation version có chủ ý và review.

```powershell
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT transform_version, count(*), sum(jsonb_array_length(COALESCE(normalized_fields->'candidates','[]'::jsonb))) AS candidates FROM observations GROUP BY 1 ORDER BY 1;"
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT id, status, payload->>'normalizer_version' AS version, payload->'result' AS summary FROM ingest_jobs WHERE job_type='normalize_observations';"
```

Cutoff draft từ header2024 giữ admission_year2024 dù document_year2026. Thiếu method2025/Điểm TT/ĐGNL,ĐGTD giữ review, không đoán hoặc nhân tổ hợp. Học phí năm học2026–2027 giữ academic_year riêng và qualifiers; không là admission_year2026 hay học phí từng ngành đã xác minh. PDF scan/OCR và các issues cũ vẫn mở.

Parser HTML sửa context/footnotes ở html/1.0.1. Lệnh dry-replay đã kiểm:

```powershell
uv run python -m services.data.parsers replay 19a1088e-6412-49e4-b911-73ec9146f4fa --revision t06-context --output state/normalization/parser-context-replay.json
```

Không persist parser sửa trong đợt này;215input gốc vẫn nguyên vẹn. Nếu operator chủ động parse phiên bản mới sau này, phải chọn bộ raw input đã review để tránh normalization nhiều phiên bản cùng locator như facts mới. T06 pilot không đồng nghĩa T05 toàn bộ/T07/T08/quota20.000hoàn thành.

## Entity resolution T07: registry có phiên bản và pilot offline

Đọc [hợp đồng](docs/entity-resolution-contract.md) và [báo cáo](docs/reports/entity-resolution-pilot.md). T07 chỉ nhận normalization envelopes thuộc job đã đóng băng, phân giải từng candidate; không nhận430hàng observations như430facts. Seed config/entities/ptit-v1.json hoàn toàn pending, không có canonical UUID được duyệt. Fuzzy chỉ gợi ý review, không auto-link hoặc publish.

```powershell
uv run python -m services.data.resolution evaluate --output state/resolution/gold-evaluation.json
uv run python -m services.data.resolution preview --normalization-job 7bc439bf-a6d7-4beb-bf03-bb47956c5383 --output state/resolution/preview.json
uv run python -m services.data.resolution run --normalization-job 7bc439bf-a6d7-4beb-bf03-bb47956c5383
uv run python -m services.data.resolution affected --entry proposal:ptit --output state/resolution/affected.json
```

Pilot hiện có job `e4ede9f6-feed-4ce9-aac4-fc9237eeee56`; kiểm tra lại bằng `uv run python -m services.data.resolution replay --job e4ede9f6-feed-4ce9-aac4-fc9237eeee56`. run in job_id; replay bằng `uv run python -m services.data.resolution replay --job JOB_UUID` với UUID thật in ở run hoặc báo cáo. Replay giữ registry frozen trong manifest, không lấy alias mới để sửa lịch sử. preview/affected read-only; run/replay là transaction riêng, không chạy trong HTTP FastAPI. Chạy lại cùng versions/code/config/input không thêm hàng. Thay logic/registry/alias cần version mới có chủ ý; thay payload cùng version bị từ chối. --registry FILE chọn registry khác đã validation; approved targets còn phải tồn tại và khớp canonical DB.

--output chỉ cho ignored state/ hoặc ngoài checkout vì chứa evidence/tên nguồn. Không commit output/raw/secrets/dumps. affected trả historical_dependency và có thể potential_registry_change bảo thủ cho entry trong registry mới; đó là danh sách cần đánh giá lại, không tự thu hồi/duyệt fact. Gold280 synthetic cases là kiểm quy tắc, không chứng minh accuracy thực địa99.5%.

```powershell
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT id,status,payload->'result' AS summary FROM ingest_jobs WHERE job_type='resolve_entities';"
docker compose --env-file .env -f infra/compose.yaml exec postgres psql -U tuyensinh -d tuyensinhdaihoc -c "SELECT normalized_fields->>'schema_version' AS schema,count(*) FROM observations GROUP BY 1;"
```

Unknown year/campus/track/language/method/scale/scope giữ unknown. BVH/BVS là hai source campus labels dưới một university proposal; Program/Offering proposals không là canonical IDs. Tuition năm học không biến thành admission year hay phí từng ngành. T08 chỉ có thể nhận packets cần review; cần phê duyệt registry/taxonomy và scale/scope/rules trước publication. Crawl vẫn paused5/5; không tải thêm nguồn.

## Review và publication T08

Đọc [hợp đồng publication](docs/publication-contract.md), [quy trình review](docs/review-workflow.md) và [báo cáo pilot](docs/reports/publication-pilot.md). Module `services/data/publication` chạy local, không mở endpoint mutation. Migration additive `0003_publication` thêm guards, không đổi raw/T05–T07. Chỉ publish cutoff đã review; tuition nhóm/năm học vẫn blocked.

```powershell
uv run alembic upgrade head
uv run python -m services.data.publication list --output state/publication/list.json
uv run python -m services.data.publication inspect --resolution 97259d1b-894c-4637-9e09-8c237ce15c78 --candidate 857495c2612874e9c1e25b2705660fe920db5a76f35bbe81cade944d9b451277 --output state/publication/inspect.json
uv run python -m services.data.publication plan --resolution 97259d1b-894c-4637-9e09-8c237ce15c78 --candidate 857495c2612874e9c1e25b2705660fe920db5a76f35bbe81cade944d9b451277 --output state/publication/plan.json
```

Plan packet là read-only, chưa là approval. Sau khi người phụ trách xác minh hồ sơ và soạn ReviewCommand riêng: `uv run python -m services.data.publication plan --file state/publication/review.json`, rồi `uv run python -m services.data.publication apply --file state/publication/review.json` bằng dedicated reviewer login. Apply action publish chỉ tạo quyết định; publisher dùng `uv run python -m services.data.publication apply --decision $decision` với UUID thực, correction thêm expected revision đã duyệt. `uv run python -m services.data.publication replay --decision $decision` kiểm lại lineage/versions và idempotency. Xem workflow cho export registry, chạy T07 mới và quyền DB.

Actor lấy từ PostgreSQL session_user, không nhận reviewer tự nhập; superuser bị chặn apply. Đã có hai login kỹ thuật DEV riêng theo ủy quyền; chưa có approval nghiệp vụ thật. Xem [evidence review](docs/reports/publication-evidence-review.md) và hướng dẫn nạp credentials local trong review-workflow.md. Ba hồ sơ THPT2024 đã chuẩn bị ở ignored `state/publication/review-batch.md`; canonical cutoffs vẫn 0. Không dùng dữ liệu/approvals TEST ONLY cho pilot. Secrets, quyết định và output chứa dữ liệu nguồn luôn ngoài Git. Local role grants/guards đã có tests riêng; production OIDC/RBAC, withdrawal governance đầy đủ, refresh worker/release builder và UI còn ở các task sau.

## Kiểm thử và CI

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run alembic check
uv run pytest -q
git diff --check
```

Tests cần PostgreSQL thật và tài khoản CREATEDB; cùng credential .env nhưng tạo DB riêng tuyensinh_test_<loại>_<UUID>. Các DB test mới được giữ lại theo ràng buộc không xóa; không DROP. Dữ liệu fixture là tổng hợp, không phải tuyển sinh thật. Fake HTTP servers chỉ bind loopback trong tests; không có cờ CLI cho phép crawler Internet truy cập private IP. Tests mặc định và CI không dùng Internet/crawl nguồn thật.

GitHub Actions .github/workflows/ci.yml chạy lock sync, Ruff, mypy, Alembic upgrade/check và toàn bộ tests với PostgreSQL 17 riêng. Kết quả chạy thực tế được bàn giao cùng commit push; không suy từ việc có workflow thành CI thành công.

## Tài liệu

- docs/schema-provenance.md: checksum, bằng chứng đối chiếu DDL và phần tài liệu chưa xác minh độc lập.
- docs/data-contract.md: identity, quota, provenance và ranh giới raw/publication.
- docs/data-dictionary.md: cột, constraints/indexes; sinh bằng uv run python scripts/data_dictionary.py.
- docs/source-inventory.csv và docs/source-review.md: URL, năm, định dạng và trạng thái truy cập.
- docs/reports/database-foundation.md: báo cáo lịch sử baseline 30 tests, trước crawler.
- docs/reports/crawler-pilot.md: bằng chứng đợt crawler, kết quả tải và giới hạn T01/T03/T04.
- docs/parser-contract.md và docs/reports/parser-pilot.md: hợp đồng T05, review tài liệu, locator, observations và giới hạn.

T01 cần mở rộng review robots/quyền dùng/coverage trước ingest production. T03/T04 hiện là nền raw HTTP; các adapter và vận hành quy mô lớn cần bổ sung sau. T19 mới là CI nền, chưa có staging/production release.
