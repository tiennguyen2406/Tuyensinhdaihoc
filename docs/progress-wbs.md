# Tiến độ EduRadar T01–T19 — T09 DEV release smoke 19/10/2026

Phase hiện tại: **Phase 1 — Data**. Lát cắt publication pilot PTIT có ba current verified published canonical cutoffs sau approval riêng C2/D1/D2/D3, apply/replay thực tế. Chưa nghiệm thu toàn T07/T08/Phase1/quota20.000. Chi tiết: reports/ptit-publication-pilot.md; không quy đổi tests/envelopes thành phần trăm hoàn thành.

T09 đã materialize release nội bộ version3, SQL/export/manifest count3, verify/replay đạt;
jobs1/2coalesced vào3, job3built. Chi tiết reports/t09-release-pilot.md. Smoke3facts chưa
nghiệm thu toànT09 hoặc đa nguồn; catalog3/observations863/jobs55/audit45/releases1.

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
| T09 | RR release builder, frozen export/coverage/manifest/hash, CLI, roles/guards và lease/coalescing |1internal DEV release version3/count3; jobs1/2coalesced3,job3built; verify/replay không đổi34tables | SQL/export/manifest3;23T09tests và full548 đạt; dữ liệu/raw/history giữ nguyên | Chưa pilot đa nguồn/load/restore/remote storage hoặc quota20.000; mới3facts/thiếu19.997, chưa toànT09 |
| T10 | Nền API/health, chưa search/catalog API | Chưa search trên release | Chưa | Search/filter/detail/year/coverage/SSR; bắt đầu khi có releasepilot ổn định, không phải đợi20.000 |
| T11 | DEV roles và local CLI review có audit | Reviewer/publisher riêng;3immutable fact decisions từ exact human approvals và3publisher transactions | Chỉ nền local T08, không giả reviewer production | OIDC/RBAC production, admin UI, correction/withdrawal governance |
| T12 | Schema scale/rule/validators, chưa evaluator | THPT2024scale[0,30] và3TTNV predicates đã lưu; computation unavailable_aggregate_scope | Chỉ evidence/semantic scope phục vụ publication, không tính/so sánh điểm | DSL execution/priority/eligibility/rounding/traces/golden rules |
| T13 | Schema conversion và kiểm scale/method/year/authority | Chỉ fixtures ràng buộc, không quy đổi nguồn thật | Chưa | Registry kỳ thi/version và official conversion execution |
| T14 | Chưa | Chưa | Chưa | Historical recommendation API/buckets/paging/explanations |
| T15 | Chưa | Chưa | Chưa | Form/frontend/mobile/E2E tư vấn |
| T16 | Schema SNA runs, chưa graph builder | Chưa | Chưa | Graph theo release/năm/major/typed edges/export |
| T17 | Chưa algorithms | Chưa | Chưa | Centrality/Louvain/metrics/sensitivity/reproducibility |
| T18 | Chưa analytics/dashboard | Chưa | Chưa | Analytics API/dashboard/Gephi/methodology/report |
| T19 | Compose, CI lint/type/migrations/integration, health, local roles | T09 full548tests trên DB test riêng; lint/type/lock/schema0004pass; ASGI200, không xác nhận HTTPserver | Checks local có bằng chứng; CI exact SHA xem checkpoint bàn giao sau push | Staging/E2E/security/load/SLO/backup-restore/rollback/public release |

## Mốc chuyển tiếp

1. A2–C1 bootstrap đã apply; C2 scope được ghi private, không tự ghi DB. D1/D2/D3 đã duyệt riêng, reviewer apply và publisher apply tuần tự; expected/actual khớp, replay cả hai pha không ghi thêm.
2. Sau T09:863observations/55jobs/45audit,2Program/3Offering/1scale,3scopes/3canonical revision1/3evidence,catalog3,1release.9audit kỹ thuật mới giải thích trong báo cáo; raw/history giữ nguyên.
3. Release pilot version3/ID396ccd8b-1193-43dd-a08a-bb19e639dd56 verified, frozen coverage và replay; jobs1/2coalesced vào3,job3built. Không tạo releases1/2.
4. T10 có thể bắt đầu trên release pilot ổn định đồng thời mở rộng data. Release ba facts chưa thay WBS pilot vài trăm facts/10–15trường.
5. Chỉ nghiệm thu dataset khi đủ≥20.000 current verified published canonical cutoffs; không cộng URL/observations/revisions/evidence. Không đóng Phase1/T08/T09 từ số tests.
