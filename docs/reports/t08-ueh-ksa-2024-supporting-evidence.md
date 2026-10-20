# UEH KSA PT6 2024 — supporting evidence và decision-gap addendum

Baseline local/remote `90735c62728e61c1a423e77187eeff9de30a451c`, branch
`codex/crawler-pilot`. Handoff untracked cũ được giữ nguyên. Không production code,
parser/normalizer/resolver/publication contract hay migration thay đổi. Không tạo
cutoff candidates, approval, canonical entities, scoring execution hoặc release.

## Hai lead đã trở thành snapshot thật

Cache ban đầu không có hai exact URLs. Existing Store/frontier/Crawler/Transport/
RawStorage thu độc lập từ official host; không dùng web research làm input dữ liệu.

| Source | Ngày nguồn, precision day | Snapshot | Bytes | Raw SHA-256 |
|---|---|---|---:|---|
| A: recruitment/catalogue | 15/02/2024 | `b3d25076-9c5d-4796-9de0-2306a6100081` | 236278 | `caba8f7a8b8fd9b308ef3c9b524eb7af8ef93b6455119bab3b909f7ee09ad668` |
| B: entrance-quality threshold | 19/07/2024 | `dc57c75d-a090-45b7-a78d-b0240d6eb6ec` | 182108 | `f540b6f1559937859d2cb6451a7c1b97e12166d1440d4b292be36d48be46f947` |

Exact official URLs:

- A: <https://tuyensinh.ueh.edu.vn/bai-viet/dai-hoc-kinh-te-tp-ho-chi-minh-khoi-dong-mua-tuyen-sinh-2024-on-dinh-chi-tieu-phuong-thuc-mo-02-nganh-hoc-moi-da-dang-linh-vuc-ho-tro-dinh-huong-tang-nhieu-co-hoi-lua-chon-nghe-nghiep-phu-hop/>
- B: <https://tuyensinh.ueh.edu.vn/bai-viet/tuyen-sinh-dai-hoc-2024-ve-viec-xac-dinh-nguong-dam-bao-chat-luong-dau-vao-doi-voi-phuong-thuc-xet-tuyen-dua-vao-ket-qua-thi-tot-nghiep-thpt-nam-2024-khoa-50-dai-hoc-hinh-thuc-dao-tao-chinh-quy-c/>

**2/6 wire requests**, cả hai HTTP200/text/html; redirects0/retries0/failures0.
Preflight dùng robots cache hợp lệ, không request mới: hash
`208dd58a297578f35c6720e6af0fad603116374a8c18f37ffef5a19a470e185a`, hết hạn
20/10/2026 15:42:16 UTC. Cả hai exact paths allowed. Preflight run
`46a8faf2-246d-4af0-9530-15aa19fc07b8`, fetch run
`62fb88d4-94e4-4de3-ad0c-15eda2203e0b` đều paused. Không resume run cũ.

Profile versioned riêng trong private package và frozen crawl_runs: chỉ exact
host/two seeds, depth0/discovery2, concurrency1, burst1, 0.5rps. Task-local
ExactPolicy giữ nguyên URLPolicy/SSRF/DNS/TLS/size/MIME/timeouts và chỉ cho hai
URLs/robots, không follow URL khác. Không attachment/ảnh/JS hoặc mirror. HTTP
accounting độc lập các budget trước. Không có quyền dữ liệu được cấp từ preflight.

## Evidence mới và giới hạn áp dụng

Business root duy nhất như các nguồn UEH trước. A có 10 DOM tables: main catalogue
73 physical rows/54 programs; ISB13 rows; KSV32 rows; các bảng còn lại về tổ hợp và
phương thức. Reuse `html.table_rows` physical origins/spans, không parser mới hay
DB parse jobs. B là DOM text, không cần OCR: không có table score cần ánh xạ.

Date lấy đúng article time node, không sidebar dates 2025/2026. Private evidence
giữ source IDs/snapshots/raw hashes, raw text, exact locators, field type,
publication date/precision, scope, interpretation uncertainty và version
`ueh-support-review/1.0.0`. Có **247 evidence records** đã kiểm toàn bộ locators.

| Field/gap | Kết quả mới | Điều chưa được suy ra |
|---|---|---|
| PT6 method | A nêu năm2024 và source method code100 | Không tự link Method PTIT hoặc chọn canonical code/ID |
| Named weighting | A p38: (*) Toán; p39: (**) tiếng Anh; đều hệ số2/quy30 | Chưa có complete formula/domain/rounding/priority hoặc approved Scale/Basis |
| Curriculum markers | A p37: (S) có lựa chọn song bằng tích hợp; p40: (***) yêu cầu chứng chỉ ngoại ngữ | Không tự split/merge Program hay áp điều kiện cho mọi language track |
| Registration eligibility | A bảng10/row4: tốt nghiệp THPT/tương đương, thi2024 và có điểm tổ hợp UEH | Chưa đủ toàn bộ final conditions/population/priority |
| KSA entrance threshold | B p2–5:20,00, liệt kê54main names; ISB tách p6–7 | Đây không phải cutoff; không thay August score hoặc bảo đảm admission |
| Threshold numeric/population basis | B p11: khu vực3, không trọng số, 3môn/bài thi thang10 | Không backfill thành basis/population của final cutoff có trọng số |

KSV threshold16 tại B p9–10 ngoài tranche. Không thấy mức KSA khác20 trong notice;
ISB ngoài tranche vẫn được giữ scope riêng. Source discipline/classification và
language descriptions A được giữ như metadata nguồn, không ánh xạ Major taxonomy.

## Reconciliation đủ 54 và xung đột thật

54 full codes và base labels khớp A/August; so sánh marker riêng, không xóa marker
trong raw hoặc coi match là approved identity. Campus attribution A được đề xuất
từ p3 KSA cohort + KSV catalogue riêng sau p41; caption bảng đầu nhắc cả KSA/KSV
nên không được dùng caption/code đơn lẻ làm mapping campus. July/August nêu KSA
rõ; linkage catalogue vẫn cần reviewer xác nhận. Mỗi row giữ university/campus/
year/PT6/code/name/context evidence và binding gốc, không fuzzy merge.

B không in codes: 53 names khớp trực tiếp, code được corroborate qua A/August.
Một dòng `7480107_02` thêm qualifier hệ kỹ sư trong July: applicable threshold
giữ null, chỉ có proposal20 chờ xác nhận Offering/track; không âm thầm bỏ qualifier.
54 combination lists A/August đồng nhất sau giải span origins, không fan-out.

**14 August starred rows:** 13 có cùng (*) và cùng full code/tên gốc trong A,
hỗ trợ đề xuất Toán hệ số2/quy30; vẫn chưa được business approve. Dòng `7220201`
ở February là (S)(**) nhưng August là (*). Giữ cả hai: source A hỗ trợ tiếng Anh
cho context February, không chứng minh August(*) là Toán. Chưa gán named subject
cho candidate này; không dùng September để sửa August. Bảng riêng14 dòng ở addendum.

Có **8 row-level marker changes**: 7 labels(S) không còn trong August
(7220201,7310102,7320106,7340204,7340301_03,7340403,7620114), cùng việc (***) của
7340301_01 biến mất. English(**)→(*) nằm trong dòng7220201 đó, không đếm thêm row.
Yêu cầu chứng chỉ của7340301_01 tháng2 cần kiểm applicability cuối cùng; p5 August
mô tả profile đầu vào không thay thế quy định. Không coi marker mất là chương trình
đã ngừng hoặc điều kiện đã bãi bỏ. Combo-note (*) IELTS và (**) vẽ tại A p46–47
khác section program-weighting p38–39, không được leak ý nghĩa.

## Hazard 2023/2024 đã được cô lập

A là recruitment2024, catalogue/quota header2024; nhưng ba historical cutoff
headers ghi **2023**, phương thức PT3/PT4/PT5/PT6. **257 numeric physical cells**
được giữ dạng `historical_cutoff_reference`, score_year2023 và header/cell lineage,
đều excluded khỏi intake2024. Blank/span references và ô nói chương trình mới2024
không tạo giá trị. Header-year checker từ chối thiếu/đa năm hoặc quota header;
không fallback article year. New cutoff candidates0, observations từ hai nguồn0.

## Cải thiện readiness cụ thể

**7/19 decision dossiers được bổ sung coverage:** KSA-03/05/06/07/11/12/13.
Field-level gains: official method code54; generic registration eligibility54;
threshold exact-name53 + qualifier-held1; named subject13 + starred conflict1.
Không tăng trạng thái tổng thể của quyết định: còn prerequisites thật, nên
category promotions0, business approvals0. Đây là thu hẹp gap và phát hiện conflict,
không phải tuyên bố chốt hoàn toàn scale/conditions/identity.

Addendum mới giữ19 original IDs/SHA, exact affected sets/bindings, supporting
evidence IDs, prior/new readiness, reviewer actions và downstream effects. Các
KSA-02/KSA-08/KSA-16 giữ exact bytes/hashes; không tái dùng hash cũ cho nội dung mới.
Năm source-rights gates vẫn external_evidence_required: official pages/metadata/
robots không là storage/commercial/redistribution permission. Authority vẫn
unverified, không broaden August-only authority scope sang A/B.

## Outputs, kiểm chứng và bảo toàn

Private: `state/evidence/ueh-2024-ksa-pt6-supporting-sources/` chứa đủ requested
JSON/CSV/Markdown, reconciliation54rows, conflicts, acquisition/accounting/profile,
15 offline synthetic regression tests và task-local read-only scripts. Không raw
bodies/private packets/source excerpts được commit. Addendum SHA-256:
`20cce9bbf679aca210e09354d10cb968a12f903e6dbc1d145254be4403164660`.

Full validator: checked_packets54/54, raw/Decimal54 unchanged,247evidence locators,
257historical references,19original decision hashes,54before/after coverage
records, rights unresolved, zero source/final-year contamination; cached latest
reuses2snapshot IDs/hashes với0HTTP mới. Private extraction không ghi observations.

Tests: **15 new synthetic offline regressions pass** (RED→GREEN cho year/source/
scope/marker/threshold guards); **97 existing crawler+UEH regressions pass** qua
89initial +8rerun. Tám failure ban đầu do RawStorage từ chối test temp ngoài allowed
raw directory; rerun dùng fresh `state/raw/` temp, không sửa tests/validators hoặc
xóa cache/history. Test DB riêng giữ lại. Ruff/check-format, mypy, frozen lock và
Alembic check pass. Final exact-SHA backend/web CI và run URL lưu private
`git-ci-verification.json`, báo kết luận thật khi bàn giao; không suy từ baseline CI.

| DEV | Trước | Sau |
|---|---:|---:|
| Canonical verified published / catalog / audit | 3 / 3 / 47 | 3 / 3 / 47 |
| Sources / snapshots | 43 / 36 | 45 / 38 |
| Observations / jobs | 1127 / 83 | 1127 / 85 |
| Releases / version / cutoff count | 1 / 3 / 3 | 1 / 3 / 3 |

Additive technical rows: sources/snapshots/runs/fetches/schedules/jobs mỗi loại+2.
Existing rows33/34tables nguyên; chỉ shared UEH host limiter state đổi đúng fetch.
Không xóa row. **772 historical file hashes** nguyên, gồm signoff sheet/drafts,
54packets,77overlay,old snapshots/PTIT approvals,`.vscode/` và untracked handoff.
Release v3 manifest SHA
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90` nguyên.

Measured: offline reconciliation2.73s, full validation13.80s; preflight→addendum
1048.26s gồm đọc/triển khai/tests, chưa gồm CI. HTTP2/6, T05/T06/T07jobs0,
raw-fetchjobs2, canonical/approval0. Token usage không quan sát được.

Owner cần xác nhận proposed named-weighting/eligibility interpretations và các
variants7220201/7340301_01/7480107_02, tiếp tục rights review. Bước kỹ thuật nhỏ
nhất: đối chiếu văn bản final PT6 2024 có hiệu lực cho các marker/conditions còn
mâu thuẫn cùng formula/priority, theo exact official URLs được chỉ định trong task
riêng. Không tự crawl rộng, apply/bootstrap/publish hoặc chuyển T12/T13.
