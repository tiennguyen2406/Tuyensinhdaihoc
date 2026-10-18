# T08 — hợp đồng review và publication pilot

Phạm vi `publication/1.0.0`: review local có xác thực PostgreSQL, bootstrap registry bất biến và publisher **cutoff** có giao dịch. Tái sử dụng 34 bảng hiện có; không dựng publisher học phí/học bổng, Score Engine, release builder hoặc API mutation. Đọc cùng contracts T05–T07; entity resolved không thay thế fact verified.

## Gates theo loại fact

| Fact | Định danh và dữ liệu bắt buộc | Unknown được giữ | Evidence/review và trạng thái |
|---|---|---|---|
| cutoff | University, Program, Offering đúng năm/campus/context, method; combination được xác nhận hoặc confirmed_none; round, population, conditions; Decimal score, verified scale và basis version | Major nullable; scoring rule, ngày hiệu lực/ngày công bố có thể thiếu; track/language chưa biết được biểu diễn rõ theo registry, không suy mặc định | Authority đúng trường/năm/fact_kind; review từng trường và đúng ô điểm; thiếu scale/basis/scope chặn publication |
| tuition | Schema hiện tại cho Offering nullable nhưng admission_year bắt buộc | Giữ academic_year và phạm vi nhóm chương trình từ T06 | Chưa có publisher tuition trong lát cắt này. Nhóm/năm học 2026–2027 bị chặn, không tạo admission_year hay chia phí từng ngành |
| scholarship, exam_schedule | Dùng schema/dictionary hiện có khi xây validator riêng | Không bổ sung giả các trường thiếu | Review-only, chưa có typed publication gates/CLI trong đợt này |
| scoring/conversion rule | Cần method, scale/basis, hiệu lực và evidence riêng | Không suy từ max_score giống nhau | Không chạy DSL hay phê duyệt rule qua publisher cutoff; triển khai sau |

Một cutoff có nguồn và scale/basis/scope đã duyệt có thể được publish khi thiếu scoring_rule: `computation_status=unavailable_rule`. Có rule chỉ mang `rule_available_not_evaluated`; T08 không thực thi/tuyên bố so sánh được. Major thiếu giới hạn taxonomy/SNA, không chặn cutoff. `conditions={}`/unknown không là “không áp dụng”; confirmed_none phải có quyết định và evidence. Conditions có schema_version=conditions/1: kind=none chỉ gồm version/kind, hoặc kind=predicate có expression JSON object không rỗng. Expression là mapping canonical do reviewer xác nhận, chưa được Score Engine diễn giải; nhãn predicate/text đơn thuần không đủ tạo identity. Không tự coi các biểu thức khác nhau là đồng nghĩa.

## Input và review binding

Packet chọn **một candidate** trong T07 envelope, kiểm manifest raw → T06 → T07, input row/snapshot digests, candidate key, normalizer/registry/alias/resolver versions. Source identity thuộc binding; authority và canonical environment được kiểm lại và đóng băng khi duyệt fact. Input/environment/version đổi thì cần review mới, không sửa quyết định cũ. Không đọc raw-only như một normalized fact hoặc lấy output publisher làm input vòng lặp.

`ReviewCommand` gồm request_id, action, Binding(resolution_id, candidate_key, packet_sha256), expected_registry_version/expected_alias_version, reason và operations/fact tùy action. Actor lấy từ `session_user`, JSON không có trường reviewer tự nhập. File chỉ ở ignored `state/` hoặc ngoài checkout.

`ValidatedDraft` giữ decision ID/digest, actor, packet digest, scope, admission identity, canonical payload, CutoffSpec, snapshot/raw observation IDs và computation status. `Publisher.publish(draft, expected_revision)` luôn dựng lại draft từ approval, không tin DTO của caller. Expected revision phải khớp quyết định và current row.

## Bootstrap không phụ thuộc vòng

Một quyết định bootstrap tạo/liên kết theo thứ tự phụ thuộc: trường/phương thức/ngành/năm/subjects/combination → Program → Offering → scale → alias; kiểm canonical parents bằng validator hiện có. Program.major có thể NULL. Tạo UUID theo request/key để retry ổn định, chỉ trở thành canonical sau transaction thành công. Link không ghi đè entity đang có. Source link chỉ đúng source của packet và scope authority đã review. Evidence phải tham chiếu snapshot tồn tại và locator không rỗng; kiểm ý nghĩa evidence thuộc trách nhiệm reviewer.

Entity operations nhận các proposal keys hiện có; đường alias canonical hiện hỗ trợ `university_aliases`. General program/method alias governance và UI tạo proposal mới chưa hoàn thiện. Không ép BVH/BVS thành hai trường; đối chiếu campus/code system/context trong review. Không ép Tài năng/Kết hợp vào enum phương thức khác. Scale không suy từ độ lớn số.

Transaction ghi canonical rows, audit trước/sau, immutable `registry_version` và `review_decision` jobs. Registry/alias mới có provenance actor/thời điểm/evidence; pending seed và frozen T07 cũ không đổi. Export registry mới rồi chạy T07 namespace mới trên T06 input đã chọn trước khi review publication. Version mới không tự giải phóng blocked numeric/header/scope attempts của T06.

## Ba loại khóa

- Admission identity lấy các business fields của scope: Offering/năm, method, combination kể cả NULL, round, population và condition_key. Basis/scale version nằm trong canonical scope conditions; đổi basis tạo scope mới, không sửa basis đã dùng.
- Fact fingerprint là SHA-256 canonical payload trong identity, gồm score/scale/basis và các trường fact; không chứa URL, crawl time, tuition hoặc scholarship. Decimal chuẩn hóa chuỗi, Unicode NFC, JSON key order ổn định; float bị từ chối. Hash không thay unique constraints/kiểm payload.
- Bundle fingerprint gộp identity và fingerprints tuition/scholarship đã sắp xếp. Helper chỉ định nghĩa contract; chưa có bundle serving/release builder. Phí đổi không tự tạo cutoff revision.

## Giao dịch publication

Không HTTP/OCR trong transaction. Shared registry advisory lock ngăn bootstrap đổi context; logical-family lock serialize cùng phạm vi kể cả basis replacement. DB business unique/NULLS NOT DISTINCT/partial current indexes vẫn có hiệu lực.

1. Xác thực publisher, kiểm approval chưa revoked, versions/digests/authority/scale/evidence/context và expected revision.
2. Tạo hoặc lấy admission scope đã validation, có audit. Không yêu cầu scope phải tồn tại trước lần publish đầu.
3. Không current: insert verified revision 1 và evidence. Cùng payload: giữ revision, chỉ thêm evidence chưa có. True replay không thêm rows/version.
4. Correction khác score cần supersedes_cutoff_id, expected revision và correction evidence: retire old, insert revision kế tiếp trong cùng scope. Nguồn công bố cũ đến muộn không rollback current.
5. Official conflict chưa rõ hiệu lực: giữ giá trị current, đánh disputed, ghi quality issue/evidence; không lấy trung bình hoặc chọn theo crawl time. Press thiếu authority bị từ chối trước publication.
6. Thay basis/scale: yêu cầu replaces_scope_id và basis version mới, retire current/withdraw scope cũ rồi tạo current trong scope mới. Lịch sử giữ nguyên; không UPDATE liên kết scale/rule tại chỗ.
7. Evidence envelope mới có namespace `validated/1;publication/1.0.0`, liên kết raw/decision; không sửa raw/T05/T06/T07.
8. Fact/evidence/audit/publication_request, catalog increment và queued `refresh_serving:<version>` cùng transaction. Rollback/crash không để fact thiếu refresh. Refresh pending chưa là release T09.

Serving thay đổi khi thêm fact, correction, conflict/dispute, evidence công khai mới hoặc alias của trường đã có current cutoff; tăng dataset_version một lần và enqueue refresh. Bootstrap nội bộ/approval chưa publication/alias của trường chưa serving/replay no-op không tăng version. Request ID retry idempotent; cùng ID khác nội dung bị từ chối. Conflict governance nhiều quyết định độc lập không thay thế workflow giải quyết/withdrawal đầy đủ.

## Quyền và lịch sử

Ba NOLOGIN group roles: `eduradar_reader`, `eduradar_reviewer`, `eduradar_publisher`. Migration owner provision grants riêng; không tạo login/password hoặc tự gán người dùng. CLI apply từ chối superuser/CREATEROLE, yêu cầu session_user có group phù hợp. Reviewer tạo quyết định, publisher chỉ áp dụng quyết định đã duyệt; tests dùng cả hai login riêng. Reader chỉ SELECT catalog và Alembic revision phục vụ readiness, không đọc private jobs/audit/observations hoặc ghi lịch sử.

Migration additive `0003_publication` chỉ thêm functions/triggers: audit append-only; review/registry/publication manifests bất biến; T08 cutoff/scopes, approved scale/Program/Offering và validated observations có guard. Core SQL vẫn gọi validator; DB chặn forged approval, legacy-marker bypass của non-superuser và sửa/xóa lịch sử T08. Owner vẫn là maintenance trust boundary; đây là quyền quản trị local, chưa là production RBAC/OIDC/SECURITY DEFINER sealed API.

Revocation là quyết định append-only. Approval đã áp dụng publication hoặc bootstrap khi có current fact không được revoke âm thầm; CLI từ chối cho đến khi có workflow withdrawal có kiểm dependencies/version/refresh. Source authority đã dùng cũng không bị ghi đè tùy tiện. Gate hiện bảo thủ trên toàn bộ current cutoffs; chưa có merge/unmerge/withdrawal đầy đủ.
