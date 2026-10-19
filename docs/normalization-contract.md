# T06 normalization contract

## Ranh giới và interface

`services.data.normalization.normalize.normalize(observation: RawObservation, context: NormalizationContext) -> NormalizedObservation` là hàm thuần. RawObservation thêm UUID của hàng DB vào contract raw T05. Chỉ nhận transform `raw-only/1;normalizer=none;resolver=none;aliases=none` và normalized_fields={}; không normalize lại output. Không tải Internet, OCR, resolve entity UUID, fuzzy merge, chạy score/conversion DSL hoặc publish.

Version đầu: normalizer/1.0.0; namespace output `normalization/1;normalizer/1.0.0;resolver=none;aliases=none`. Context đóng băng target_years=(2024,2025,2026), training_modes=(Chính quy,), require_campus=true cho pilot BVH/BVS. Scope rules hiện là adapter pilot PTIT, không phải bộ nhận diện đa trường. Header method chỉ giữ nhãn NFC/search key, chưa phải ID/method registry đã duyệt. Không tự mở rộng viết tắt HN/ĐH/Điểm TT.

Một input tạo một **envelope**, có zero hoặc nhiều **candidates** và các **blocked attempts**. Envelope không phải fact/canonical cutoff. Candidate là draft ánh xạ một giá trị vật lý, vẫn needs_review/unverified; không đồng nghĩa đã đủ scope/scale để publish. Missing round/population/condition/combination và scale được giữ null cùng issues, không gán default hay wildcard. T07/reviewer phải bổ sung bằng chứng trước T08. Một hàng raw nhiều cột năm/phương thức có thể tạo nhiều candidates chỉ khi mapping từng cột rõ.

## Unicode và lexical values

Raw nguyên vẹn. TextValue giữ raw, display NFC và search_key casefold/NFD bỏ dấu/đ→d. Unescape entities một lần; chuẩn hóa NBSP/CRLF/whitespace; bỏ U+200B/U+FEFF, giữ ZWJ/ZWNJ có thể có nghĩa. Không bỏ các từ quốc tế/chất lượng cao/phân hiệu/Tiếng Anh. display_fields lưu JSON pointers tới các chuỗi nghiệp vụ, không thay raw_fields.

NumericValue giữ raw, status, Decimal value hoặc minimum/maximum, operator, unit/currency, evidence và rule_version. JSON Decimal luôn là string. 24,50 và24.50→24.50; không float/rounding. Một dấu phân cách với3chữ số sau như1.200/1,200 là NUMERIC_AMBIGUOUS nếu chưa có grouping grammar kèm evidence. number(...,grouping='.',evidence='locator/rule') chỉ chấp nhận grammar được cung cấp rõ; normalizer cutoff pilot không truyền grammar suy đoán từ giá trị/max scale.

Rỗng→missing; dash→not_reported; N/A→not_applicable; tất cả value=null, không bằng0. 0là giá trị. Giữ >=/≤ và khoảng; khoảng ngược/mơ hồ bị chặn. Không xác nhận thang điểm từ độ lớn số. 'điểm' giữ unit=point.

money() giữ multiplier/đơn vị/currency/range;25.000.000 đồng/năm→25000000,VND,academic_year bằng grammar nhiều nhóm;1.200 đồng/tín chỉ vẫn mơ hồ.25–30triệu/năm giữ min/max,1,2triệu/tín chỉ giữ credit, không nhân thành năm. Nhiều loại tiền/đơn vị hoặc narrative không parse trọn vẹn bị review. TUITION_MULTIPLE_RANGES chặn đoạn có nhiều khoảng giá thay vì lấy khoảng đầu tiên. Adapter tuition chỉ lấy khoảng có 'triệu đồng', năm học và đơn vị explicit trong cùng đoạn; giữ các qualifier dự kiến/trung bình/khoảng và statement nhóm chương trình, không nhân ra từng ngành. Năm học2026–2027 không tạo admission_year2026. Lộ trình phần trăm, ngưỡng từ một mức và nhóm Thường xuyên chưa có mapping đủ điều kiện trong pilot.

TimeValue giữ raw/precision year,month,date,minute,second,fraction. Timestamp có offset chuyển UTC nhưng giữ độ chính xác; date-only không gán00:00 hoặc timezone. Timestamp thiếu timezone→TIMEZONE_MISSING; ngày sai→TIME_AMBIGUOUS. Helper thời gian được golden-test; chưa có adapter exam_event thực tế. Ngày đăng không là admission year.

## Mapping, scope và provenance

Chỉ chọn cells dưới header rõ 'Điểm trúng tuyển/Điểm chuẩn' và năm tuyển sinh của chính header path. Không lấy document year/method từ heading ngoài bảng. Giữ document_year riêng từ h1, admission_year từ header, academic_year riêng. Năm2023→YEAR_OUT_OF_SCOPE, không đổi năm. Điểm sàn/ngưỡng/điều kiện hồ sơ và Điểm TT chưa đủ nghĩa→block/review.

Method phải có một nhãn cột rõ; thiếu method2025 không thừa hưởng method THPT2026 đang tồn tại trong context raw cũ. Nhãn gộp ĐGNL,ĐGTD không chia thành kỳ thi hoặc tự chọn một nhãn. BVH/BVS và Chính quy/Thường xuyên có evidence riêng; không hợp nhất. Context cùng ghi BVH/BVS chặn bằng CAMPUS_AMBIGUOUS; các cột tên/mã chương trình xung đột chặn bằng PROGRAM_SCOPE_AMBIGUOUS. Tên/mã chương trình từ header định danh nguồn, không biến mã thành major_code hay canonical UUID. Campus/language/track còn nguyên trong label chương trình.

Mỗi candidate có observation_id,snapshot_id,source_id,parser/input-transform/normalizer versions,row/cell locator,column,header_path,raw_value,bbox khi có,context,footnotes và scope_evidence. candidate_key là hash lineage+namespace, không phải dedup identity canonical. Span reference không sinh giá trị; score gốc span nhiều ô/hàng bị SCORE_SPAN_AMBIGUOUS. Không Cartesian ngành×năm×method×tổ hợp; tổ hợp/điều kiện vẫn raw, chưa resolve/execute.

## Issues và review

Issue có code,level(document/row/cell/field),locator,field,blocks_candidate,detail,origin(parser/normalizer). blocks_candidate chỉ nói việc **phát sinh draft candidate** từ mapping này. Cả draft có thể phát sinh vẫn needs_review/unverified và bị chặn publication. Candidate review issues gồm scope components chưa resolve/scale chưa xác nhận, không phải cảnh báo đủ điều kiện công bố.

Document issue được lấy từ parse job của input và giữ trong envelope; issue row từ raw_fields._extraction. OCR/image ở trang/vùng khác vẫn mở nhưng không chặn ô HTML có evidence độc lập. Header/numeric/scope issue thuộc đúng ô/hàng chặn mapping. Unknown parser issue được giữ theo hướng chặn. Blocked list giữ raw/null/header/year/method và lý do; không tính vào candidates. Không xóa69issues/jobs cũ. Hai PDF scan không có raw observations nên không là input normalization;25ocr_required vẫn nằm ở parse jobs.

Các chỉ số issue trong summary phân biệt input issues dedup theo(snapshot,code,level,locator,field,blocks) với blocked/candidate occurrences. Cùng parser issue có thể có biểu diễn document vàrow; không so tổng đó như số69document issue occurrences của T05. Xem báo cáo để biết số gốc còn mở.

## Persistence, version và recovery

Schema không đổi. Mỗi raw input tạo một hàng observations mới: cùng snapshot/locator/parser, transform normalization riêng. raw_fields copy nguyên vẹn; normalized_fields là envelope có parent input_observation_id; verification_status=unverified. Unique key T05 được tái sử dụng. Extraction confidence vẫn là confidence raw parser, không là confidence normalizer hay điểm tuyển sinh. Lineage JSON chưa có FK parent riêng; store xác minh parent tồn tại/raw-only/source qua snapshot trước ghi.

Batch chạy trong engine.begin(), khóa PostgreSQL advisory transaction theo normalizer version; hai workers tuần tự và không ghi trùng. Insert outputs + ingest_jobs normalize_observations manifest trong cùng transaction. Crash/failure rollback toàn batch; không có output nửa chừng hay job giả succeeded. Quy mô pilot215rows dùng một transaction; batching/load testing20.000chưa kiểm chứng. Job quarantined vì chưa review, không sửa parse/crawl jobs.

Manifest giữ input_ids/input SHA-256, config/context/code digest/lock digest, git_commit_at_execution (trường git_commit) và working_tree_dirty. Digest code chuẩn CRLF/LF; nếu chạy trước commit thì working_tree_dirty=true, không coi HEAD cũ là bản code đã commit. Cùng namespace khác code/config/lock bị từ chối; đổi logic phải đổi implementation version có chủ ý. Không tăng version để tăng quota.

Chạy lại cùng input/config/version kiểm fingerprint và payload; no-op inserted=0,cached=true. Nội dung khác cùng unique key bị chặn; không UPDATE output/parent. Replay đọc manifest input IDs/config, không chọn lại output hoặc tải nguồn. Mặc định run chọn tất cả raw-only inputs; nếu có nhiều parser versions cùng locator, cần operator chọn bộ input đã review qua store API thay vì dùng số hàng làm số facts. Pilot này giữ đúng215input gốc, parser sửa chỉ dry-replay, không persist parser version mới.

Không ghi cutoff_scores/catalog_state/dataset_releases hoặc canonical_fact. Không coi envelopes/candidates là quota20.000. Reports chứa raw/display chi tiết chỉ lưu ignored state/ hoặc ngoài checkout. Fixtures synthetic, không đưa raw nguồn/secrets/dữ liệu cá nhân vào Git.

## Source-specific UEH draft namespace

`normalizer/ueh-2024-ksv/1.0.0` consumes only the dedicated UEH T05 binding; global
header-local-year/BVH/BVS rules are unchanged. Explicit publication/method/section
evidence supplies2024/Chính quy/PT6/KSV, bound to snapshot/table/column locators.
All mapped code/program/combination/score header paths are checked; no positional
fallback across changed semantics. Decimal values and complete admission codes remain
unverified. Local total-row-without-value diagnostics remain open without suppressing
other physical rows. Scale/basis, named weighted subjects/formula, formal round,
population/conditions/combination identities remain unreviewed/null; source evidence
survives lineage. The authorized fallback does not establish additional-round cutoffs.
Historical outputs/digests are immutable; use historical code for old executable replay.
