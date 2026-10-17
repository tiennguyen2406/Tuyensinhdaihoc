# Hợp đồng dữ liệu T01

Căn cứ: docs/schema-provenance.md, DDL mục 4 và INV-01–10 của bản thiết kế được cung cấp. Đây là hợp đồng kỹ thuật đã triển khai; không xác nhận một nguồn, scale hay công thức tuyển sinh thực tế nào.

## Identity và năm

Chuỗi: universities → admission_years → programs/program_years → program_admissions → cutoff_scores → cutoff_evidence → observations → source_snapshots → sources.

- majors: ngành chuẩn hóa theo (code_system, major_code), dùng liên trường; không dùng tên giống nhau để hợp nhất.
- programs: identity chương trình dài hạn của một trường, theo (university_id, canonical_key).
- program_years: offering theo năm, mã xét tuyển, campus/track/language. Business key: (university_id, admission_year, offering_code, campus_code, track_code, language_code).
- program_admissions: (program_year_id, method_id, combination_id, round_key, population_key, condition_key). NULL combination là một phạm vi không tổ hợp, không phải wildcard; NULLS NOT DISTINCT ngăn trùng.
- score_scales: method + admission_year + code + exam_version. Không suy tương đương từ max_score bằng nhau.
- cutoff_scores: admission scope + revision. Một current cutoff/scope; học phí, học bổng, URL và thời điểm crawl không thuộc identity này.

Publication và quota chỉ cho 2024, 2025, 2026. DDL giữ miền 2000–2100 theo đặc tả để lưu lịch sử; validator publication giới hạn phạm vi dự án. Năm không có dữ liệu là unknown; không bù bằng năm khác.

## Định nghĩa 20.000

Chỉ đếm cutoff_scores.is_current=true AND verification_status='verified', scope.data_status='published', offering.admission_year IN (2024,2025,2026). Hàm thực thi: db.validators.count_canonical_cutoffs(). Không join evidence/học phí/học bổng để đếm. Không tính URL, fetch, snapshot, observation, evidence, revision cũ hoặc dữ liệu test. Báo riêng publication groups trước khi tách tổ hợp và coverage theo trường/năm/phương thức. Hiện có 0 bản ghi tuyển sinh production được xác minh; chưa có release đạt quota.

## Giá trị và provenance

Điểm: Decimal/NUMERIC(12,5); tiền: Decimal/NUMERIC(18,2); JSON decimal là chuỗi, không float/NaN/Infinity. Timestamp dùng timezone; date/unknown precision giữ riêng. Không đoán min/max, score rule, rounding hay quy đổi. Snapshot có SHA-256, raw_uri, final_url; observation có locator, parser_version và transform_version. OCR chưa duyệt không đủ điều kiện công bố.

## Quy ước adapter đang triển khai

SourceProfile schema tại config/sources/profile.schema.json; chưa có profile thật được duyệt. allowed_hosts là hostname chính xác; seed HTTPS, robots=obey. verified trong cấu hình chỉ là metadata cần reviewer xác nhận, không cấp quyền publication cho client.

Để validator chấp nhận nguồn verified: sources.university_id phải đúng trường hoặc authority_scope.universities chứa UUID trường; authority_scope.years chứa admission_year; authority_scope.fact_kinds chứa loại fact. Đây là quy ước adapter bổ sung cho JSONB authority_scope, cần được reviewer nguồn xác nhận trước ingest thật. Hiện chỉ chấp nhận nguồn first-party/official đã verified; nguồn báo chí cần quy trình review T08/T11, chưa được tự coi authoritative.

normalized_fields.canonical_fact của evidence phải chứa payload chuẩn hóa có schema_version để so với cutoff.fact_payload. Primary/supporting phải cùng payload, observation verified; primary snapshot phải đúng; conflicting không được có payload giống nhau. Đây là quy ước nội bộ cho parser tương lai; chưa tuyên bố adapter nguồn nào hỗ trợ.

Combination chuẩn phải có đủ 3 subject. Adapter required_components hiện chỉ hỗ trợ danh sách mã môn; DSL khác hoặc tương thích chéo năm bị chặn, chờ rule/compatibility có nguồn (T12/T13). Không chạy eval hoặc tự quy đổi tuyến tính.

## Ranh giới bảo vệ và phần còn thiếu

SQL constraints bảo vệ FK/unique/check trong mọi đường ghi. SessionFactory bổ sung guard trước flush cho ORM: scope/rule/year/nguồn/Decimal/evidence; chặn DELETE và sửa in-place offering/scope/facts/rules đã lưu. Khi tạo đồ thị mới bằng ORM, phải flush cha trước khi validate con; chưa có ingestion/publisher API. Bulk/Core SQL dùng bởi migration/test là đường đặc quyền, không tự có guard ORM.

T08 phải bổ sung transaction publication: khóa scope, retire + revision mới, evidence + audit + refresh job + tăng catalog version; DB roles không DELETE, bảo vệ payload đã dùng, manifest checksum và release nhất quán. Hiện guard từ chối tạo DatasetRelease và mọi sửa cutoff/rule đã lưu cho đến khi có đường publisher được audit. Không giả lập phần này bằng sửa DB tay.

Registry condition_key kiểm được tính nhất quán JSON chuẩn hóa; các cách diễn đạt đồng nghĩa vẫn cần T07/reviewer. Chưa có 10–15 nguồn thật, quyền lưu snapshots, robots review, bộ fixtures được cấp phép hoặc golden rules tuyển sinh; các mục này giữ trạng thái pending, T01 chưa hoàn tất.

CI action commits được khóa theo hướng dẫn chính thức https://docs.astral.sh/uv/guides/integration/github/ tại thời điểm triển khai; uv khóa 0.13.1. Chưa thực thi workflow trên GitHub.
