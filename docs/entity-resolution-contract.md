# Hợp đồng entity resolution T07 — entity-resolution/1

## Phạm vi và interface

`resolve(ResolutionInput, EntityRegistry) -> EntityResolution` tại services/data/resolution/resolve.py là hàm thuần. ResolutionInput bao gồm UUID envelope T06, typed NormalizedObservation, source_id và final_url của snapshot. Store chỉ nhận output thuộc một normalization job đã đóng băng; raw-only hoặc resolution output không là input hợp lệ. Một envelope có thể chứa zero/nhiều candidates; mỗi candidate có kết quả, truy vấn và lineage riêng.

Pipeline pilot: job T06 → kiểm hash/membership/lineage → registry frozen + đề xuất pending → resolver → observations namespace riêng + ingest_jobs manifest. Không tải Internet, OCR, normalize lại raw hoặc ghi canonical. Không thay kiến trúc, bảng hay migrations đã áp dụng.

## Các lớp và khóa

| Entity type | Ý nghĩa / ràng buộc |
|---|---|
| university | Trường/học viện; domain chỉ là bằng chứng, code phải có hệ mã và phạm vi |
| major | Taxonomy ngành liên trường; major code không lấy từ mã xét tuyển |
| program | Thuộc university; tên giống ở hai trường không là một Program |
| offering | Thuộc Program và cùng university, theo admission_year/campus/track/language; code xét tuyển có hệ mã/hiệu lực riêng |
| method | Phương thức có ngữ nghĩa xác định; source-specific/composite giữ nguyên nhãn và owner/year |
| scope | Phạm vi tuyển sinh gồm offering, combination, round, population, conditions và score basis; cần evidence riêng |

Registry DTOs ở registry.py, curated seed ở config/entities/ptit-v1.json. Entity giữ key/name, parent refs, attributes, code bindings, domains, review và canonical_id tùy trạng thái. Alias giữ target/value/kind, code_system, owner, hiệu lực, attributes và review. Code giữ system/value/from_year/to_year/attributes/evidence. Không có phép đồng nhất code ở các hệ khác nhau. Unknown là null hoặc absent, không điền MAIN/GENERAL/Chính quy/campus/language mặc định.

Từ resolver/1.0.1, pending University của nguồn bổ sung khai báo explicit
attributes.table_program_code_system (ví dụ dut:table-program-label). Cùng helper dùng
cho generated Offering proposals và EntityQuery; không mặc định nguồn mới vào namespace
PTIT. Chỉ key PTIT đã biết hoặc existing PTIT campus-code binding giữ legacy fallback.
Thiếu namespace ở owner khác: không sinh Program/Offering pair, Offering unresolved
với OFFERING_CODE_SYSTEM_MISSING; namespace sai bị từ chối. Đây là code-system metadata
review-only, không xác minh source/canonical mapping hoặc biến offering code thành Major.
Không sửa manifests/outputs resolver1.0.0 lịch sử; namespace mới có replay/idempotency
riêng. Không khẳng định executable replay namespace cũ tương thích với code mới.

UEH pilot uses resolver/1.0.2 because the implementation digest includes the new
normalization module. Matching logic remains unchanged. A pending UEH owner explicitly
uses `ueh:admission-code`; PT6 is a source/year-specific method proposal. University,
Program/Offering and Major remain unapproved; source admission code suffixes are not
taxonomy. Footnotes and unresolved round/scale/basis/conditions survive T07 lineage.
Only new UEH namespaces are replayed with current code; historical manifests stay frozen.

Approved yêu cầu canonical UUID và reviewer/date/evidence; pending/revoked không được mang canonical UUID. Đây là kiểm tra tính đầy đủ của hồ sơ, **không xác thực chữ ký hoặc tự cấp quyền review**. Store còn kiểm approved UUID thực sự tồn tại trong đúng bảng, university verified, các parent/context/method semantics khớp DB. Synthetic registry bị từ chối ở project store. Approved Offering phải có admission_year và khai báo campus/track/language (null được giữ unknown); metadata này đối chiếu DB, null chỉ tương thích sentinel UNSPECIFIED của DDL. Sentinel không là bằng chứng campus chính.

Bộ seed pilot hoàn toàn pending, không reviewer/date/approval giả. BVH/BVS cùng trỏ proposal:ptit trong hệ `ptit:campus-admission-label`, hiệu lực2024, có evidence heading từng cơ sở; không là hai trường. Hệ `ptit:table-program-label` của Offering chỉ ghi nhãn trong bảng nguồn, không tuyên bố đó là taxonomy ngành hay mã chính thức toàn quốc.

`propose_registry` bổ sung source/year-local Program/Offering review proposals từ candidates cutoff có evidence. Hash đề xuất bao gồm owner/name/code/year/campus/track/language/form; không là khóa canonical Program bền vững xuyên năm. Khi review phải quyết định quan hệ Program lâu dài, Offering từng năm và taxonomy riêng. Full compiled registry chứa tên nguồn nên chỉ ở manifest DB/private outputs; không commit dữ liệu nguồn hàng loạt.

## Quyết định và matching

Mỗi CandidateResolution ghi input_envelope_id, candidate_key, raw_observation_id, snapshot_id, đầy đủ cell/header/parser/normalizer lineage, fact_kind, admission_year và academic_year riêng. EntityResolution ghi schema/normalizer namespace/registry/alias/resolver versions. Queries, options/top candidates, phương pháp, evidence, conflicts, missing, blocked_entities, dependency keys, score/margin và reasons được giữ để giải thích.

| Trạng thái | Định nghĩa |
|---|---|
| resolved | Tất cả sáu lớp đã chọn canonical entity theo policy; không đồng nghĩa fact verified hoặc publication |
| partial | Có ít nhất một canonical entity được chọn, còn lớp khác unresolved; không có ambiguity |
| ambiguous | Có xung đột mã/ngữ cảnh hoặc nhiều ứng viên deterministic/contextual, hay fuzzy tie cần review |
| unresolved | Chưa chọn canonical entity; vẫn có thể có pending proposals/fuzzy suggestions |

Trạng thái từng entity dùng resolved/ambiguous/unresolved; partial là tổng hợp candidate. `entity_key` của kết quả chosen khác `proposal_key` trong options. UUID có trong option approved là danh tính ứng viên, chỉ canonical_id ở kết quả match đã chọn mới là quyết định liên kết. Pending proposals luôn canonical_id=null. Candidate luôn verification_status=unverified và publication_eligible=false trong T07.

Thứ tự: exact code đúng system/owner/year/context → approved alias → contextual evidence → fuzzy suggestion. Exact name giữ dấu/NFC/casefold; fuzzy search key bỏ dấu, token-sort rồi stdlib SequenceMatcher(autojunk=False). Không cần dependency mới/RapidFuzz ở quy mô pilot; đổi algorithm phải tăng resolver version và đánh giá lại.

Blocking theo kind, university, program, year/campus/track/language/form/province khi cả hai phía biết. Metadata thiếu không là mismatch. Với Offering, query có context mà canonical registry không biết thì giữ option/missing và chặn auto-link. Code binding/alias có validity hoặc qualifiers chưa biết cũng không đủ auto-link. Xung đột approved name/domain với code chặn liên kết. Không union-find/bắc cầu tên tương tự.

Score =0.60×name similarity +0.25×approved alias similarity +0.15×context feature (có ít nhất một match đã biết). Đây là heuristic để xếp gợi ý, không là xác suất đúng/trúng tuyển. Top10 được xếp theo eligibility, tầng phương pháp, score và stable key; margin là score(top1)−score(top2), có thể âm giữa các tầng khác nhau. Không diễn giải margin này như confidence. Fuzzy tie cùng tầng dùng name similarity≥0.85 và gap<0.08 để yêu cầu review. Ngưỡng0.97 của thiết kế không bật auto-link; fuzzy_auto_link=false cố định. Không có precision field claim99.5%.

Pending parent độc nhất có thể thu hẹp danh sách con để review, nhưng không cho phép auto-link con. T06 adapter chưa có taxonomy/basis evidence nên major và scope trả unresolved rõ lý do; đây là phần còn thiếu, không tạo giả Major/Scope. Method Tài năng/Kết hợp giữ source label và proposal composite, không đổi enum công khai. THPT chỉ là proposal subjects theo nhãn nguồn, chưa approved. Không suy scale từ25.17/72.52/max_score, không tính conversion/scoring/priority.

Cutoff giữ admission_year2024 theo ô nguồn; tuition giữ academic_year2026–2027 và admission_year=null, không map nhóm chương trình thành Offering. Các trường scale/round/population/conditions/combinations/scoring_rule/priority/basis chưa rõ vẫn unresolved, issues T05/T06 được sao chiếu và blocked attempts không được giải phóng.

## Persistence, version và replay

Dùng nguyên observations/ingest_jobs; không migration mới. Unique(snapshot_id,record_locator,parser_version,transform_version) và advisory transaction lock bảo đảm pilot hai workers không tạo hai batch. Namespace `resolution/1;resolver/1.0.0;REGISTRY;ALIASES;input=DIGEST_NORMALIZER_NAMESPACE`. Envelope mới raw_fields chỉ giữ parent-envelope/job IDs, normalized_fields là EntityResolution, extraction_method=entity_resolution; không sửa215raw hoặc215normalization envelopes.

Manifest job resolve_entities quarantined đóng băng215input IDs/full-row SHA, normalizer namespace, compiled registry/aliases, versions/config/code/lock digests, legacy T06 lock digest, git HEAD và dirty flag lúc chạy. Hash T06 bao gồm raw fields/normalized fields/lineage; không chỉ đếm số hàng. Re-read input trước ghi, transaction output+manifest atomic, khác payload dưới cùng namespace bị chặn. Cùng input/versions/config replay inserted=0/cached=true. Code/config/lock thay đổi cần resolver version mới; entities hoặc alias thay đổi cần version tương ứng, giữ lịch sử. Không đổi version chỉ để tăng số lượng.

`affected --entry KEY --registry FILE` trả historical_dependency từ options/blocked entities/alias features. Khi entry tồn tại trong registry được cung cấp, còn trả conservative `potential_registry_change` cho các candidate cũ khác: alias mới chưa thể có trong historical dependencies. Đây là tập ảnh hưởng tiềm năng an toàn, có thể dư, không phải kết luận mọi candidate đổi kết quả. Review/replay version mới để xác định tác động thật; không sửa hoặc merge/unmerge lịch sử. Dependency lookup chưa thay thế governance thu hồi alias và phản hồi publication của T08.

Không ghi cutoff_scores, catalog_state hoặc dataset_releases. Registry canonical approval/seeding cần quy trình review có người chịu trách nhiệm; API CLI hiện không cấp phép duyệt. Health endpoints giữ nguyên và không tự migrate.

## Nghiệm thu và giới hạn

Gold tests/resolution/gold.json có280 synthetic cases do tác giả fixture khai báo expected trước scoring, không lấy resolver output làm nhãn. 80calibration/200evaluation, tách family và tên fuzzy holdout. Generator build_gold.py không gọi resolver. Đây là coverage kiểm quy tắc tham số hóa, không280 thực thể thật được người độc lập xác minh. UUID/code/reviewer fixture đều synthetic; không dùng production.

Test riêng bao phủ BVH/BVS có evidence từ seed, ba Bách khoa khác nhau, owner/campus/track/language/year/code conflicts, alias collision/withdrawal, missing context, ties, methods, max_score, tuition, lineage/tampering/version/concurrency/replay. PostgreSQL test DB riêng; không network trong tests/CI. Báo precision/recall deterministic theo expected canonical link, review rate và fuzzy top10 hit riêng; không suy độ chính xác thực địa từ bộ synthetic.

T07 chuẩn bị review packets cho T08, chưa là publication. Chưa đủ nguồn taxonomy/code authority, reviewer phê duyệt entity/alias, scale/rules/conditions và phạm vi từng fact; T05 scan/adapters và T06 blocked mappings vẫn mở. Không thay quota20.000 canonical đã xác minh bằng số envelopes/mappings/tests.
