# Tiến độ EduRadar T01–T19 — bootstrap invalidation / bounded intake 19/10/2026

Phase hiện tại: **Phase 1 — Data**. Lát cắt publication pilot PTIT có ba current verified published canonical cutoffs sau approval riêng C2/D1/D2/D3, apply/replay thực tế. Chưa nghiệm thu toàn T07/T08/Phase1/quota20.000. Chi tiết: reports/ptit-publication-pilot.md; không quy đổi tests/envelopes thành phần trăm hoàn thành.

T09 đã materialize release nội bộ version3, SQL/export/manifest count3, verify/replay đạt;
jobs1/2coalesced vào3, job3built. Chi tiết reports/t09-release-pilot.md. Smoke3facts chưa
nghiệm thu toànT09 hoặc đa nguồn. T10 sửa hai release regressions và thêm live canonical
API/Next.js tra cứu trường→Offering→cutoff đúng năm trên DEV. Catalog3/observations863/
jobs55/audit47/releases1; hai audit thêm chỉ là provision/configure reader. Chi tiết
reports/t10-internal-catalog.md và catalog-contract.md.

Lát cắt tiếp theo sửa admission-year partial/unknown/missing độc lập cutoff verification;
SQL filters/keysets/limit+1, page-scoped batch evidence và aggregate coverage thay Python
materialization. Benchmark synthetic20k/50k riêng, không vào quota. Chi tiết và giới hạn
hiệu năng/recovery/checks: reports/t10-sql-year-status.md. Không thêm release/publication.

Task mới sửa bootstrap serving invalidation theo T10 DTO, có12PostgreSQL regressions;
full615backend pass. Intake UIT/DUT dùng17/30requests, mọi runpaused. DUT FAQ có9raw
catalog→9T06→9T07 envelopes,0typedcutoffs/0T08factpackets;9private staging review gates.
Mục tiêu5–10cutoff records **chưa đạt** doTLS/ảnh/viewerJS/archive500; không tựOCR,
approval/bootstrap/publication. Sau intake:catalog3/canonical3,observations890,jobs71,
audit47,releases1,raw snapshots33; mọi hàng/files cũ nguyên. Chi tiết
reports/bootstrap-invalidation-intake.md. Không đổi quota3/20.000 hoặc lịch sửT08/T09.

| Task | Đã triển khai kỹ thuật | Kiểm chứng dữ liệu thật | Điều kiện nghiệm thu đã có | Còn thiếu/chưa bắt đầu |
|---|---|---|---|---|
| T01 | Contract/dictionary/count policy, inventory12trường, SourceProfile có phiên bản | Authority pilot PTIT2024 đã duyệt theo7source bindings;3facts có evidence | Checksum/locators và canonical count3 kiểm SQL | Quyền thương mại/tái phân phối và các nguồn khác chưa được suy thành approved |
| T02 | 31core+3crawler tables, migrations0001–0004, sessions/validators/health | PostgreSQL hiện hữu, migration empty/upgrade và constraints qua fixtures DB riêng | Nền DB có bằng chứng kỹ thuật;0004 thêm release/refresh guards, không rewrite dữ liệu | Không tự suy rằng schema/rules nghiệp vụ đã được duyệt; operation hardening thuộcT19 |
| T03 | Frontier/lease/recovery, URL/robots/SSRF/shared limiter | Run PTIT có cap và pause; host policy cả portal/PDF | Đạt lát cắt raw HTTP pilot có logs; fixture policy/concurrency | Chưa nghiệm thu vận hành đa nguồn/tải thực lớn hoặc mọi adapter |
| T04 | Raw/hash/fetch/schedule, ETag/Last-Modified/304, replay/recovery |22snapshots,23fetches hiện có; PDF gốc có validators/checksum | Hash/kích thước/replay và fixture A→B→A có bằng chứng | Chưa vận hành dài hạn/đa nguồn; không coi fixture304 là nguồn thật đã trả304 |
| T05 | HTML/digitalPDF adapters, locators/footnotes/resource limits/review |215raw observations pilot; scan2024/2025 đọc trực quan có ghi nhãn | Lát cắt HTML/PDF có lineage và giữ raw | XLSX/JSON typed/OCR/SPA và source adapters còn thiếu; scan visual không là OCR pipeline |
| T06 | NFC/search/Decimal/year/unit/method/scope envelopes có version |215envelopes,95draft candidates (91cutoff2024+4tuition academic2026–27) | Pilot giữ năm/locale và ambiguity |118blocked attempts,166untyped inputs và fact review chưa xử lý xong |
| T07 | Registry/aliases/resolver/version/replay/impact; gold synthetic | Frozen T07 vẫn91partial/4ambiguous/0eligible;3facts có approved mapping được T08 review riêng | Namespace/lineage giữ nguyên; B1/B2 xác định D2 BVS về Program QTKD thật | Không sửa auto-resolution hoặc giải phóng118blocked attempts; taxonomy/đa nguồn còn thiếu |
| T08 | Review/auth/audit, publisher transaction/revisions/evidence/catalog/outbox |3scopes/3current verified published cutoffs revision1/3evidence, catalog3; tổng863observations/55jobs/36audit | Exact approvals, roles riêng, từng field/fingerprint/lineage/xmin, reviewer+publisher replay0mutation và SQLcount3 | Chỉ đạt lát cắt publication pilot; governance withdrawal/correction thực địa, đa nguồn và toànT08 chưa nghiệm thu |
| T09 | RR builder/immutable artifacts/CLI/guards; bounded intake trên pipeline hiện có |1DEV release3/count3/hash nguyên; UIT/DUT17requests, DUT9staging gates nhưng0cutoff candidates mới | Verify/replay release3 và staging idempotency; lịch sử nguyên; không rebuild release3 | Pilot intake còn blocker format/access, chưa có5–10factpackets/đa nguồn canonical/load/restore/remote storage/quota20.000;3facts/thiếu19.997 |
| T10 | Live RO RR API catalog/1; year status từ admission_years; SQL filtering/keyset/cursor2, page batch sources/SQL aggregate coverage; SSR/URL/stale guard | PTIT2024 partial+3verifiedcutoffs,2025/26missing; synthetic20k/50k tách DEV, SQL11/10/11 mỗi trang,30HTTP requests/browser DEV đúng |596backend/44catalog,18frontend unit/6E2E; fullchecks/build pass, CI exact SHA xem checkpoint bàn giao | Mới lookup+SQL/yearstatus slice;50k/20concurrent TCP search p95=2625,4ms chưa đạt500ms; coverage aggregate/temp spill còn là bottleneck; rich filters/fees/fuzzy/security/auth production/đa nguồn còn mở |
| T11 | DEV roles/local CLI review; shared bootstrap serving-change policy cho plan/apply |3immutable fact decisions giữ nguyên;9private DUT staging review gates với lineage/hash/blocker, không có T08candidate binding mới |12PG regressions: no-cutoff university/year/alias/Program/source refs,1bump/tx,cursor409,replay/rollback/internalmetadata; full615 | Sourceformat/authority/canonical/scale/basis decisions trước fact review; OIDC/RBAC production/admin UI/correction/withdrawal governance |
| T12 | Schema scale/rule/validators, chưa evaluator | THPT2024scale[0,30] và3TTNV predicates đã lưu; computation unavailable_aggregate_scope | Chỉ evidence/semantic scope phục vụ publication, không tính/so sánh điểm | DSL execution/priority/eligibility/rounding/traces/golden rules |
| T13 | Schema conversion và kiểm scale/method/year/authority | Chỉ fixtures ràng buộc, không quy đổi nguồn thật | Chưa | Registry kỳ thi/version và official conversion execution |
| T14 | Chưa | Chưa | Chưa | Historical recommendation API/buckets/paging/explanations |
| T15 | Chưa | Chưa | Chưa | Form/frontend/mobile/E2E tư vấn |
| T16 | Schema SNA runs, chưa graph builder | Chưa | Chưa | Graph theo release/năm/major/typed edges/export |
| T17 | Chưa algorithms | Chưa | Chưa | Centrality/Louvain/metrics/sensitivity/reproducibility |
| T18 | Chưa analytics/dashboard | Chưa | Chưa | Analytics API/dashboard/Gephi/methodology/report |
| T19 | Compose/CI backend+web checks; shm512MiB sau bằng chứng default64MiB cạn/crash; health/local reader | Recovery giữ34table digests/364files, không xóa DB; benchmark giữ config/plans/latency/querycost | Local/CI exact SHA và checks cuối xem report/checkpoint bàn giao | Staging/security/SLO/backup-restore/rollback/public release; recovery hiện hữu không là restore acceptance |

## Mốc chuyển tiếp

1. A2–C1 bootstrap đã apply; C2 scope được ghi private, không tự ghi DB. D1/D2/D3 đã duyệt riêng, reviewer apply và publisher apply tuần tự; expected/actual khớp, replay cả hai pha không ghi thêm.
2. Sau T09:863observations/55jobs/45audit,2Program/3Offering/1scale,3scopes/3canonical revision1/3evidence,catalog3,1release.9audit kỹ thuật mới giải thích trong báo cáo; raw/history giữ nguyên.
3. Release pilot version3/ID396ccd8b-1193-43dd-a08a-bb19e639dd56 verified, frozen coverage và replay; jobs1/2coalesced vào3,job3built. Không tạo releases1/2.
4. T10 đã có internal lookup slice từ baseline release3, phục vụ live canonical cùng version response; không khóa serving vĩnh viễn ở3. Hai reader audits đưa tổng47, mọi hàng cũ/364historicalfiles nguyên. Release ba facts chưa thay WBS pilot vài trăm facts/10–15trường.
5. Chỉ nghiệm thu dataset khi đủ≥20.000 current verified published canonical cutoffs; không cộng URL/observations/revisions/evidence. Không đóng Phase1/T08/T09 từ số tests.
6. Bước tiếp theo đề xuất: T09 pilot đa nguồn có source/authority/review gates trên pipeline hiện có và nhu cầu T11 review/admin (plans/2026-10-19-t09-multisource-next.md). Không chuyển thẳng T12 khi thiếu căn cứ rules/scales; DEV vẫn3/20.000, còn19.997.
7. Bounded intake mới chỉ đạt staging/review-gate evidence, chưa đạt cutoff fact packet mục tiêu. Cần nguồn official HTML/PDF số đọc được hoặc task riêng được cho phép cho OCR/source fallback; không coi9FAQ/envelopes là9facts. Catalog version khi business bootstrap/publication tiếp theo phải dùng policy mới và version thật để xây release mới, giữ release3 nguyên.
