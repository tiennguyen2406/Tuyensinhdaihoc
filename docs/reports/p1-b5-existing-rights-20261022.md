# P1-B5 · Disposition existing facts và PTIT rights package

Baseline `codex/crawler-pilot`/`e38b244bad5069c39b00d091387f4e272a85bc47`, không
tracked diff ban đầu; giữ11file untracked có sẵn. [P-B và K](p1-b5-confirmation-20261022.json)
đã xác nhận; S1/I1/C1 giữ nguyên. Đã kiểm lại cả5binding hashes, không sửa payload.
Đây là chuẩn bị, **0newly-served facts, quota không tăng**, không chọn hoặc thực thi
disposition. [Index](p1-b5-existing-rights-20261022.json) niêm phong private artifact
hashes; không có rights grant/receipt mới. Câu hỏi disposition/deadline đã gửi trước
vẫn chưa được trả lời trong hội thoại; giữ câu hỏi đó, không tạo approval flow trùng.

## Ba facts và trạng thái truy cập thực

| FactID / revision | PTIT2024 / THPT / source_aggregate | ScopeID |
|---|---|---|
| `1076f528-0bab-4ac6-8840-714c6cfd77b6` /1 | BVH /7340101 /Quản trị kinh doanh | `5b12453f-420f-44a4-b605-0fbd079d145c` |
| `4fd7c322-cd05-4102-a6c4-956d3313258e` /1 | BVH /7480201 /Công nghệ thông tin | `16a4ed99-0b01-4a9a-ab45-91fb76cb5937` |
| `a5ced261-5a4d-4c20-91f6-bb28a646e8a2` /1 | BVS /7340101 /Quản trị kinh doanh | `accfaee3-58d8-4a73-bc8a-4af732aa2d31` |

Bounded **dedicated catalog reader**, READ ONLY REPEATABLE READ/timeout8s đã xác
minh đúng3eligible current/verified/published rows và fingerprint/revision/Offering/
scope bindings khớp release. Không owner fallback hoặc đổi grants. Catalog3, releasev3
`396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest SHA256
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90` khớp DB row và
ba artifact files local đã kiểm. Đây là kiểm giới hạn, không fullDEV preservation.

**Netstat mới, không HTTP:** chỉ thấy `127.0.0.1:5432`; không listener8000/3000.
Hai PID cũ17240/24560 không còn tồn tại; nguyên nhân process exit chưa xác lập.
Task không start/stop service và không coi process vắng là owner đã chọn pause.
Real smoke P0-4/pass và old runner receipts là lịch sử, không readiness hôm nay.

Runbook/receipts trước cấu hình API reader8000/web3000 loopback, origin8000 không
suffix; code web proxy `/api/catalog/...`→FastAPI `/api/v1/...`, có routes university/
program/cutoff/source/data-coverage. Proxy/client no-store, university SSR force-dynamic;
không có API hiện tại để HTTP-test. Data đã tải vào browser và artifacts/DB local
không tự bị revoke. Nhãn internalDEV không chứng minh ACL/shares/tunnel/public exposure
đã được audit toàn diện. Release/raw/credentials vẫn riêng; không HTTP file server mới.

## Phiếu D · Disposition chưa chọn

ID **D-P1B5-EXISTING-DISPOSITION-20261022-v1**, private
`state/triage/p1-b5-existing-rights-20261022/disposition-options-v1.json`, SHA256
`2bd3638f2f3965b999f3706d5faec518764df08abfab94a95226a3bc1e735b45`.
Exact3IDs/revisions/Offering/scope/fingerprints và release binding có trong payload;
UTF-8/noBOM/LF, hash exact private bytes. Sheet là bản chuẩn bị, không approval.

| Option | Action/consequence cần owner quyết |
|---|---|
| TEMP_CONTINUE | Ngoại lệ chỉ đúng3existing facts trong biên nội bộ owner/dev/reviewer được chỉ định, loopback, attribution/raw-private; **cần deadline+07:00 thật**. Nếu owner chọn, materialize payload mới có deadline/expiry action/operator, hash mới rồi xác nhận riêng. Hiện processes vắng nên khôi phục serving là task implementation riêng, không tự startup ở lượt này. Không cho phép newfacts/cohort hoặc cấp third-party license |
| PAUSE_API | Measure runtime tối thiểu: giữAPI8000 không listener/không restart; nếu lúc implementation cóAPI, revalidate đúng project PID/tree rồi dừng đúng tree. DirectAPI và web proxy không lấy dữ liệu mới; không chỉ ẩnUI. Proxy dự kiến502 từ code, chưa HTTP-test. API health cũng unavailable; web shell có thể tồn tại nếu web chạy. Hiện không cóAPI/web process để dừng. Không dừng DB, xóa canonical/history/approvals/audit/release hoặc revoke dữ liệu đã tải |

Expiry action **đề xuất** của TEMP_CONTINUE: pause new HTTP catalog serving nếu chưa
có decision mới hợp lệ. Owner phải duyệt deadline/action và người/task thực hiện;
deadline không tự enforce. Chưa có scheduler/automation/reminder. Nếu yêu cầu automation,
phải qua workflow hỗ trợ sau exact action/time authorization; reminder không chặn access.
Restore dùng existing hidden reader/runbook sau authorization riêng, không volume reset.
Canonical withdrawal/deletion là workflow khác, không suy từ runtime pause.

## Gói rights theo P-B, không grant hunt lại

Private annex ghim10snapshots/URL/title/year/sourceID/snapshotID/rawSHA/bytes:
BVH/BVS notices2024, index điểm2024, QĐ545/2024 và trang thông tin2026 chứa bảng
retrospective2024; primary2026, methodsApril, equivalenceJuly, QĐ1192 và amendment
QĐ1547. Trang2026 không bị gọi nhầm là notice2024. Requested coverage khác granted
coverage: **chưa nguồn nào được grant trong package này**. Không xin riêng mỗi ô điểm.

`source-scope-annex-for-request-v1.json` là annex metadata owner có thể đính kèm,
SHA256 `c3990e0d7741354de35c8fb699aef78f441aabdb94393497fe6b978ec988cd4f`;
không raw bodies/packets/credentials/local paths. Internal annex riêng giữ provenance.
`rights-basis-package-v1.json`, SHA256
`45bf5c60569fdf103a4c9730f7443ab8057e2e7924d7e274ff7a550b148be29f`, mô tả cùng use
cho hai routes: **permission từ authorized rights holder** hoặc **applicable documented
basis được suitably qualified person review**. Không chọn recipient hoặc tự coi owner
business reviewer là qualified. Source authority không thay quyền sử dụng.

Owner có `permission-request-draft-vi.md` ngắn và `qualified-review-brief-vi.md`:
users/local access, private retention/processing, extraction, internal derived serving,
attribution, duration, restrictions, authority/contact provenance. Duration/retention/
recipient/project contact chưa chốt, cần điền trước khi gửi. Public/commercial là yêu
cầu riêng, không suy từDEV. Không gửi thông điệp hoặc tạo fake rights receipt.
Qualified review phải có capacity evidence, document/version/date/provenance, source/
use applicability, conditions/exclusions/conclusion và attributed reviewer; hash không
tự chứng minh authority/applicability. B không đòi owner duyệt thay evidence thiếu.

## Cohort và national preparation

Giữ nguyên manifest6 SHA256 `2347b7bf2bb02aa4740dec27de3ad35cf1f04e36b4e8cd45014df00666f1b4b2`;
không extraction/T07 rerun/rebuildK. Private gate matrix có6candidate/packet/resolution
refs và khác biệt từng dòng: pilotK confirmed chỉ proposal;5dòng còn lại cần own scale/
basis applicability review. I1/C1 chỉ scope gốc; source authority2026/support, identity/
complete predicates và P-B rights còn pending. TTNV`=1` của7340101LG không bị đổi
thành`<=`; values/locators/packets giữ frozen. Không fact approval trong task này.
Shared evidence có thể review theo exact manifest/command hashes; per-fact roles,
validators/transactions/audit vẫn giữ, không hứa atomic multi-fact hoặc một-fact mãi mãi.

Carry forward5leads DKC/DTT/DVL/KHA/NTH. Hiện được chuẩn bị offline inventory/dossier
từ cache: cross-check tên/mã/context, deduplicate known parent/campus, liệt kê gaps và
draft intake scope. NewHTTP/robots/redirect/retry cần budget/access review riêng, không
dùng budget dư; persisted pipeline run cần scope/version riêng. P-B giữ new-serving
hold, không tự cho phép/cấm mọi technical/offline activity. Không acquisition tranche
mới, không directory405units→405universities hoặc promise served coverage50. Taxonomy/
complete legal-geography roster/F2 không thành F1 prerequisite.

## Bàn giao và checks

P-B nay được dẫn từ current [operator catalog runbook](../catalog-contract.md) và
[publication contract](../publication-contract.md), giữ receipt/historical payloads.
Đây là **procedural hold**, không runtime license guard được triển khai. Existing3fact
disposition còn pending; process vắng không phải approval/withdrawal. F2 deferred.

Kiểm5confirmed hashes,10cached raw hashes/bytes, exact3DB/release bindings,6manifest
rows/packet references và copied gate exceptions, JSON/LF/links/private/public boundary.
Không newHTTP/crawl/OCR/business writes/registry/bootstrap/fact/publication/release build/
serving change hoặc DEV fixtures;0application tests mới. Quota helper3/20.000 là lịch
sử, không đo helper lần này; bounded3eligible facts không thay full quota measurement.
Current listener/raw/release checks không chứng nhận toànDEV/filesystem preservation.
CI disposable kiểm `checks`/`web` đúng finalSHA sau normal push, không real smoke mới;
remote/CI ghi khi bàn giao, không vòng commit nhúngSHA của chínhreport.

Private root `state/triage/p1-b5-existing-rights-20261022/` chứa disposition/request/
annex/gate matrix, runtime/read-only evidence và hashes. Chỉ report/index/operator
notes/progress đi Git; private evidence không public. Tracker chỉ cập nhật P1-B5
narrow task, parentpartial; exactly4next: **P1-X3 existing disposition → P1-B5 owner
permission/qualified basis → P2-X1 remaining cohort review (publication conditional) →
P3-X1 national intake tranche**. Owner còn cần trả lời câu hỏi pending, cung cấp route/
authority provenance hoặc qualified reviewer/basis, và duration/retention cho request.
