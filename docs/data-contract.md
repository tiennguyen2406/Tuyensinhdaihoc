# Hợp đồng dữ liệu T01

Căn cứ: docs/schema-provenance.md, DDL mục 4 và INV-01–10 của bản thiết kế được cung cấp. Đây là hợp đồng kỹ thuật đã triển khai; không xác nhận một nguồn, scale hay công thức tuyển sinh thực tế nào.

## Identity và năm

Chuỗi: universities → admission_years → programs/program_years → program_admissions → cutoff_scores → cutoff_evidence → observations → source_snapshots → sources.

- majors: ngành chuẩn hóa theo (code_system, major_code), dùng liên trường; không dùng tên giống nhau để hợp nhất.
- programs: identity chương trình dài hạn của một trường, theo (university_id, canonical_key).
- program_years: offering theo năm, mã xét tuyển, campus/track/language. Business key: (university_id, admission_year, offering_code, campus_code, track_code, language_code).
- program_admissions: (program_year_id, method_id, combination_id, round_key, population_key, condition_key). NULL combination phải có trạng thái có căn cứ: confirmed_none hoặc source_aggregate được công bố cùng điểm theo Offering; không phải wildcard. Aggregate có rule/evidence riêng trong condition_dsl/condition_key, không mở rộng thành mọi tổ hợp. Unknown không được publish; NULLS NOT DISTINCT ngăn trùng.
- score_scales: method + admission_year + code + exam_version. Không suy tương đương từ max_score bằng nhau.
- cutoff_scores: admission scope + revision. Một current cutoff/scope; học phí, học bổng, URL và thời điểm crawl không thuộc identity này.

Publication và quota chỉ cho 2024, 2025, 2026. DDL giữ miền 2000–2100 theo đặc tả để lưu lịch sử; validator publication giới hạn phạm vi dự án. Năm không có dữ liệu là unknown; không bù bằng năm khác.

## Định nghĩa 20.000

Chỉ đếm cutoff_scores.is_current=true AND verification_status='verified', scope.data_status='published', offering.admission_year IN (2024,2025,2026). Hàm thực thi: db.validators.count_canonical_cutoffs(). Không join evidence/học phí/học bổng để đếm. Không tính URL, fetch, snapshot, observation, evidence, revision cũ hoặc dữ liệu test. Báo riêng publication groups trước khi tách tổ hợp và coverage theo trường/năm/phương thức. DEV pilot hiện có3canonical PTIT2024 đã duyệt và1internal smoke release version3;3/20.000,thiếu19.997. Chưa có production deployment hoặc release đạt quota. Xem release-contract.md và reports/t09-release-pilot.md.

## Giá trị và provenance

Điểm: Decimal/NUMERIC(12,5); tiền: Decimal/NUMERIC(18,2); JSON decimal là chuỗi, không float/NaN/Infinity. Timestamp dùng timezone; date/unknown precision giữ riêng. Không đoán min/max, score rule, rounding hay quy đổi. Snapshot có SHA-256, raw_uri, final_url; observation có locator, parser_version và transform_version. OCR chưa duyệt không đủ điều kiện công bố.

## Quy ước adapter đang triển khai

SourceProfile schema tại config/sources/profile.schema.json; 12 profile URL thật nằm trong cùng thư mục. Trạng thái candidate/checked/eligible và bằng chứng được ghi riêng trong docs/source-inventory.csv. allowed_hosts là hostname chính xác; seed HTTPS, robots=obey. verified trong cấu hình chỉ là metadata cần reviewer xác nhận, không cấp quyền publication cho client.

Để validator chấp nhận nguồn verified: sources.university_id phải đúng trường hoặc authority_scope.universities chứa UUID trường; authority_scope.years chứa admission_year; authority_scope.fact_kinds chứa loại fact. Đây là quy ước adapter bổ sung cho JSONB authority_scope, cần được reviewer nguồn xác nhận trước ingest thật. Hiện chỉ chấp nhận nguồn first-party/official đã verified; nguồn báo chí cần quy trình review T08/T11, chưa được tự coi authoritative.

normalized_fields.canonical_fact của evidence phải chứa payload chuẩn hóa có schema_version để so với cutoff.fact_payload. Primary/supporting phải cùng payload, observation verified; primary snapshot phải đúng; conflicting không được có payload giống nhau. Đây là quy ước nội bộ cho parser tương lai; chưa tuyên bố adapter nguồn nào hỗ trợ.

Combination chuẩn phải có đủ 3 subject. Adapter required_components hiện chỉ hỗ trợ danh sách mã môn; DSL khác hoặc tương thích chéo năm bị chặn, chờ rule/compatibility có nguồn (T12/T13). Không chạy eval hoặc tự quy đổi tuyến tính.

## Ranh giới bảo vệ và phần còn thiếu

SQL constraints bảo vệ FK/unique/check trong mọi đường ghi. SessionFactory bổ sung guard trước flush cho ORM: scope/rule/year/nguồn/Decimal/evidence; chặn DELETE và sửa in-place offering/scope/facts/rules đã lưu. Khi tạo đồ thị mới bằng ORM, phải flush cha trước khi validate con; chưa có ingestion/publisher API. Bulk/Core SQL dùng bởi migration/test là đường đặc quyền, không tự có guard ORM.

T08 phải bổ sung transaction publication: khóa scope, retire + revision mới, evidence + audit + refresh job + tăng catalog version; DB roles không DELETE, bảo vệ payload đã dùng, manifest checksum và release nhất quán. Hiện guard từ chối tạo DatasetRelease và mọi sửa cutoff/rule đã lưu cho đến khi có đường publisher được audit. Không giả lập phần này bằng sửa DB tay.

Registry condition_key kiểm được tính nhất quán JSON chuẩn hóa; các cách diễn đạt đồng nghĩa vẫn cần T07/reviewer. Đã lập 12 nguồn thật; coverage theo năm và robots/quyền lưu được ghi theo từng nguồn. Không suy từ năm mục tiêu sang năm đã kiểm chứng. Phần lớn robots và quyền tái phân phối còn pending. Fixtures crawler tự tạo, không phải dữ liệu tuyển sinh production; golden rules tuyển sinh chưa có. T01 chưa hoàn tất.

CI action commits được khóa theo hướng dẫn chính thức https://docs.astral.sh/uv/guides/integration/github/ tại thời điểm triển khai; uv khóa 0.13.1. Kết quả workflow thực tế của đợt push được ghi trong báo cáo crawler-pilot.md.

## Raw-only crawler (T03/T04)

Eligibility chỉ cho phép thử kỹ thuật có giới hạn sau review truy cập/robots, không làm sources.verification_status thành verified và không cấp quyền publication. university_key là registry nội bộ, chưa phải UUID trường đã mapping. Mọi nguồn crawler mới đều unverified, university_id=NULL cho tới quy trình mapping/review.

URL canonical giữ year/page/id, thứ tự và tham số lặp, bỏ tracking theo danh sách cụ thể. Crawl run đóng băng profile, request budget và frontier idempotency key. raw_fetch dùng lease token; lease hết hạn được nhận lại, worker cũ bị chặn ghi kết quả. Host budget dùng chung PostgreSQL cho robots/HTML/attachment/redirect. Tiến trình worker độc lập với API.

Snapshot identity là (source_id, raw_hash); blob theo SHA-256 toàn nội dung. A→B→A tạo hai snapshot, ba fetch; không cập nhật thời điểm snapshot cũ để giả snapshot mới. Representation mới nhất lấy từ crawl_fetches có snapshot theo id giảm dần. 304 tham chiếu snapshot đã có. response_validators lưu ETag/Last-Modified, URL cuối, MIME và số byte response; snapshot giữ MIME/kích thước representation. Lịch attachment có source_id/checksum/due_at riêng; không gắn vào khóa cutoff. Tải unconditional sau 7 ngày để kiểm tra lại nội dung dù validators không đổi.

Raw/fetch history là evidence kỹ thuật chưa xác minh. Không ghi observations, canonical cutoffs hoặc dataset releases. Quota 20.000 không tăng bởi URL, fetch hay snapshot trong đợt này.

## Lát cắt T05

Parser HTML/PDF số tại services/data/parsers tạo staging observations unverified từ raw đã lưu; crawler vẫn chỉ tải raw. Hợp đồng chi tiết: parser-contract.md. Giữ unique(snapshot,locator,parser_version,transform_version); metadata provenance/parse issues nằm trong raw_fields._extraction và durable parse job. normalized_fields={} với raw-only transform version; không thực thi T06/T07 hoặc publication T08.

fact_kind=cutoff trong observation chỉ có nghĩa mẩu trích từ vùng bảng được ghi rõ điểm trúng tuyển; không xác nhận một canonical cutoff. Hàng điểm trống không được tạo cutoff observation; giữ catalog/review. Các cột năm/phương thức/điểm khác nhau vẫn nằm cùng hàng raw, không dùng năm trên tiêu đề trang để gán toàn bảng và không tách tổ hợp tự động. Điểm sàn/điều kiện hồ sơ là catalog/review. PDF scan không sinh observations từ OCR trong đợt này. Canonical quota, catalog version và releases không đổi.


## Lát cắt T06

Hợp đồng chi tiết: normalization-contract.md. T06 giữ nguyên observations raw-only và thêm envelope theo transform namespace normalization riêng; không cập nhật normalized_fields của hàng raw cũ. Một envelope có zero/nhiều candidates có parent/cell/header/version lineage; tất cả unverified/needs_review, chưa resolve UUID/scale/conditions và không có canonical_fact. Canonical quota/count/publication invariants giữ nguyên. Năm tuyển sinh2024/2025 không lấy từ document year2026 hoặc năm học2026–2027. Thống kê phải tách raw input/envelope/candidate/canonical để tránh đếm dữ kiện nhiều lần.

## Lát cắt T07

Hợp đồng: entity-resolution-contract.md. Mỗi normalization candidate có resolution/lineage riêng trong envelope dẫn xuất mới; không sửa raw/T06. Registry/aliases có provenance, review và versions; pending proposal keys không phải approved canonical UUIDs. Entity recognition không xác minh fact hoặc publication. Đếm riêng raw/normalization/resolution envelopes, candidates và canonical. Không sửa cutoff_scores/catalog_state/releases; tuition academic year không là admission year, mã xét tuyển không là taxonomy major code.

## T08 publication pilot

Xem [publication contract](publication-contract.md) cho gates theo fact_kind, admission/fact/bundle fingerprints, review binding, scope basis replacement và transaction version/refresh. Chỉ canonical current verified cutoffs đủ publication mới thuộc quota; observations/evidence/review jobs không tăng quota. Major nullable không chặn cutoff nhưng thiếu scale/basis/scope vẫn chặn. Thiếu scoring rule được ghi unavailable_rule, không suy công thức. Tuition academic-year group giữ staging, chưa có publisher tương thích để điền admission_year. Registry approval qua bootstrap có DB actor/audit, không sửa pending JSON bằng tay.
