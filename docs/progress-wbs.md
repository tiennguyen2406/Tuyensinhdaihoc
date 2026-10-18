# Tiến độ EduRadar T01–T19 — PTIT blocker review 18/10/2026

Phase hiện tại: **Phase1 — Data**, T07/T08 chưa canonical publication. Không quy đổi số tests/mappings/envelopes thành phần trăm hoàn thành. Đây là đánh giá evidence hiện có, không ký nghiệm thu thay người phụ trách. Chi tiết đợt này: reports/ptit-blocker-decisions.md.

| Task | Đã triển khai kỹ thuật | Kiểm chứng dữ liệu thật | Điều kiện nghiệm thu đã có | Còn thiếu/chưa bắt đầu |
|---|---|---|---|---|
| T01 | Contract/dictionary/count policy, inventory12trường, SourceProfile và profiles có phiên bản | PTIT và liên kết first-party tới portal/document host, robots/raw/evidence | Hồ sơ pilot có checksum/locators; canonical counting được khóa | Duyệt nghiệp vụ/phạm vi nguồn và điều kiện sử dụng; chưa mọi nguồn đủ chạy/nghiệm thu |
| T02 | 31core+3crawler tables, migrations0001–0003, sessions/validators/health | PostgreSQL hiện hữu, migration empty/upgrade và constraints qua fixtures DB riêng | Nền DB có bằng chứng kỹ thuật theo reports/database-foundation.md và các bổ sung sau | Không tự suy rằng schema/rules nghiệp vụ đã được duyệt; operation hardening thuộcT19 |
| T03 | Frontier/lease/recovery, URL/robots/SSRF/shared limiter | Run PTIT có cap và pause; host policy cả portal/PDF | Đạt lát cắt raw HTTP pilot có logs; fixture policy/concurrency | Chưa nghiệm thu vận hành đa nguồn/tải thực lớn hoặc mọi adapter |
| T04 | Raw/hash/fetch/schedule, ETag/Last-Modified/304, replay/recovery |22snapshots,23fetches hiện có; PDF gốc có validators/checksum | Hash/kích thước/replay và fixture A→B→A có bằng chứng | Chưa vận hành dài hạn/đa nguồn; không coi fixture304 là nguồn thật đã trả304 |
| T05 | HTML/digitalPDF adapters, locators/footnotes/resource limits/review |215raw observations pilot; scan2024/2025 đọc trực quan có ghi nhãn | Lát cắt HTML/PDF có lineage và giữ raw | XLSX/JSON typed/OCR/SPA và source adapters còn thiếu; scan visual không là OCR pipeline |
| T06 | NFC/search/Decimal/year/unit/method/scope envelopes có version |215envelopes,95draft candidates (91cutoff2024+4tuition academic2026–27) | Pilot giữ năm/locale và ambiguity |118blocked attempts,166untyped inputs và fact review chưa xử lý xong |
| T07 | Registry/aliases/resolver/version/replay/impact; gold synthetic |215resolution envelopes,95candidates; registry canonical chưa apply | Lát cắt nhận diện/review có lineage; A2/B proposals cụ thể | Không có approved registry thật; cần approval→apply→export→T07 namespace mới, không ép name-only auto-link |
| T08 | Review/auth/audit, publisher transaction/revisions/evidence/catalog/outbox | A2 read-only plan13ops;0canonical/0catalog/0release | Kỹ thuật publisher qua PostgreSQL fixtures; evidence PTIT mới đối chiếu được | Chưa approval A2/B/C/D hoặc publication thật; round mapping chờ quyết định; chưa nghiệm thu toànT08 |
| T09 | Có schema releases/counters, chưa release builder |0releases; count0 | Chưa | Sau lô canonical nhỏ mới bắt đầu releasepilot/manifest/coverage; dataset20.000 còn nguyên gate |
| T10 | Nền API/health, chưa search/catalog API | Chưa search trên release | Chưa | Search/filter/detail/year/coverage/SSR; bắt đầu khi có releasepilot ổn định, không phải đợi20.000 |
| T11 | DEV roles và local CLI review có audit | Hai technical logins kiểm quyền; chưa người phụ trách duyệt | Chỉ nền local T08 | OIDC/RBAC production, quality/admin UI, correction/withdrawal governance |
| T12 | Có schema scale/rule/validators; không có evaluator | Không chạy tính điểm; TTNV chỉ đề xuất predicate phục vụ review | Chưa | DSL/priority/eligibility/rounding/traces/golden rules |
| T13 | Schema conversion và kiểm scale/method/year/authority | Chỉ fixtures ràng buộc, không quy đổi nguồn thật | Chưa | Registry kỳ thi/version và official conversion execution |
| T14 | Chưa | Chưa | Chưa | Historical recommendation API/buckets/paging/explanations |
| T15 | Chưa | Chưa | Chưa | Form/frontend/mobile/E2E tư vấn |
| T16 | Schema SNA runs, chưa graph builder | Chưa | Chưa | Graph theo release/năm/major/typed edges/export |
| T17 | Chưa algorithms | Chưa | Chưa | Centrality/Louvain/metrics/sensitivity/reproducibility |
| T18 | Chưa analytics/dashboard | Chưa | Chưa | Analytics API/dashboard/Gephi/methodology/report |
| T19 | Compose, CI lint/type/migrations/integration, health, local role grants | CI baseline a073705 success; local DB/API chạy, exact-SHA CI mới xem bàn giao | Nền checks có bằng chứng, chưa gate cuối | Staging/E2E/security/load/SLO/backup-restore/rollback/public release |

## Mốc chuyển tiếp

1. Duyệt đúng A2/file hash; revalidate rồi mới apply bằng reviewer kỹ thuật. Approval này chỉ identities/authority, không cấp approval Program/Offering/scale/cutoff.
2. Duyệt B1–B3 riêng (hai Program theo institutional catalog, ba Offering), C1 scale domain và C2 round/population/conditions; apply phần được duyệt theo phụ thuộc. Export registry **thật**, chạy T07 version mới trên input T06 đã chọn, giữ lịch sử.
3. Duyệt từng D bằng IDs/binding thật, dùng publisher apply/replay; SQL xác nhận current verified published, revisions/evidence/audit/catalog/outbox nguyên tử và health/schema đúng.
4. Khi có lô canonical nhỏ đã kiểm chứng, đề xuất triển khai T09 releasepilot manifest/coverage/checksum/count SQL=export; đây là smoke release nhỏ, chưa thay thế pilot vài trăm facts/10–15trường của WBS. T10 có thể bắt đầu trên release ổn định đồng thời mở rộng data.
5. Chỉ nghiệm thu mốc dataset khi đủ≥20.000 **current verified published canonical cutoffs**, không cộng URL/observations/revisions/evidence. Không đóng Phase1/T08/T09 từ số tests hoặc tạo đủ tên bảng.
