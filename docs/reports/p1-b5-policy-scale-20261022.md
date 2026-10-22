# P1-B5 · Chính sách DEV, scale PTIT2026 và cohort tiếp theo

Baseline đã xác minh: `codex/crawler-pilot`, HEAD
`581404225f076fb8e3e94b26736e22473c6d8de0`, không tracked diff ban đầu;
11file untracked có sẵn được giữ riêng. Đây là increment chuẩn bị, **0fact mới,
quota không tăng**, không sửa active policy, canonical, registry hoặc release.
[Index/phiếu chính sách](p1-b5-policy-scale-20261022.json) chứa hai phương án chưa
chọn và hashes của tài liệu private. S1/I1/C1 đã xác nhận theo
[receipt](p1-x2-confirmation-20261022.json), cả3hash được kiểm lại; không sửa payload
và không hỏi lại. Các approval PTIT2024 không chuyển sang2026.

## Quyền sử dụng: kết luận có giới hạn

Giả thuyết được hỗ trợ **trong hồ sơ đã kiểm**: không tìm thấy PTIT source-rights
grant cho năm nào; ba facts2024 đã vào catalog nội bộ khi quyền tái phân phối còn
unresolved. Không khẳng định không có tài liệu ở bất kỳ nơi nào khác. Đã dừng tìm
historical grant; hai acquisition mới chỉ phục vụ scale/amendment.

| Lớp | Bằng chứng và ý nghĩa |
|---|---|
| Chính sách ghi trong docs | [Source review](../source-review.md) hạn chế pilot/raw riêng, robots không license; [A2/blocker decisions](ptit-blocker-decisions.md) duyệt authority2024, không cấp license. [Review workflow](../review-workflow.md) và [publication contract](../publication-contract.md) tách fact/bootstrap khỏi rights; [release contract](../release-contract.md) chỉ internal DEV. Chưa có quyết định vận hành xuyên nguồn rõ cho derived-fact serving |
| Code thực sự kiểm | `services/api/db/validators.py::validate_source`, `services/data/publication/validate.py::active_source_review/build_draft` kiểm source/year/method/Offering authority, review còn hiệu lực, roles, identity, scale/basis/scope và evidence/digests. Không có legal-rights approval field/guard riêng trong path đã kiểm |
| Nhãn và biên vận hành | `services/data/releases/builder.py::register` ghi reason “internal DEV”; `artifacts.py` đặt `visibility=internal_dev_only`. Hai nhãn không ngăn copy/file exposure hoặc public bind. API reader/read-only và launcher loopback là biên vận hành, không giấy phép; không coi external distribution đã được chặn kỹ thuật toàn diện |
| Hồ sơ đã xem | Base/variants `config/sources/ptit*.json` tiếp tục ghi restricted internal/no grant.9targeted saved decisions/receipts/release plan đã kiểm nội dung/hash ở private audit; không tìm grant trong chúng. Không dùng sự vắng mặt field để chứng minh một kết luận pháp lý |

Catalog “publication” là ghi canonical có review, khác phát hành Internet. Raw
republication, factual extraction, internal serving và public/commercial distribution
là những mục đích khác nhau. Source authority không license. Task không đưa ra kết
luận pháp lý hoặc tự chọn A/B; explicit source restrictions không bị owner policy
miễn trừ. Trường hợp hạn chế/xung đột hoặc căn cứ không rõ cần qualified rights/legal
review phù hợp, và permission nếu route đó đòi hỏi.

## Phiếu P · D-P1B5-DEV-POLICY-20261022-v1

Payload là `policy_decision` trong index công khai đã niêm phong cùng hashes hỗ trợ.
SHA-256 được tính trên exact Git-blob bytes ở commit/path bàn giao, UTF-8/noBOM/LF.
Hai phương án **đều chưa chọn**; không thay active policy trong lượt này.

| Phương án | Giá trị/điều kiện đề xuất | Tác động và ba facts2024 hiện hữu |
|---|---|---|
| A | Owner cho phép workflow F1 chỉ nội bộ DEV: owner và dev/reviewer được chỉ định, máy được kiểm soát, API/web loopback; derived facts phải đủ mọi gate nghiệp vụ. Raw/packets riêng, không Git/full-text republication; giữ attribution publisher/notice/URL/year/snapshot/hash/locator/lineage. Không LAN/tunnel/public endpoint/dataset/commercial distribution. Áp xuyên profiles chỉ sau source-specific access/authority review, loại explicit restrictions/xung đột chưa giải quyết; không mở allowlists/portal | Với covered sources: “public-use rights unresolved; internal use permitted within owner policy”, không blanket F1-internal blocker. ChọnA bao gồm **tiếp tục phục vụ nội bộ ba facts2024 từ thời điểm receipt**, trong biên/ngoại lệA; không license hồi tố, không phê duyệt lại fact hay rewrite releasev3. Phát hiện restriction thì owner quyết disposition riêng |
| B | Trước mọi fact mới served, kể cả DEV, cần văn bản permission từ chủ thể có thẩm quyền hoặc documented applicable rights basis được qualified reviewer xác nhận. Document phải nêu nguồn/notice/year, raw storage/processing, factual extraction/internal serving, users/access boundary, attribution/retention, thời hạn và ngoại lệ. Owner cung cấp ref/provenance hoặc giao reviewer đủ chuyên môn; chưa gửi yêu cầu tới institution | M-RIGHTS tiếp tục block fact mới. Ba facts2024 cần **decision disposition riêng**: tiếp tục tạm trong nội bộ với hạn review cụ thể hoặc task được ủy quyền hạn chế/ngừng serving. B không tự phê duyệt tiếp tục, không tự withdraw/xóa/sửa; task này giữ trạng thái hiện hữu |

Ở cả hai route: owner operating policy không phải third-party permission; quyền
public/commercial chưa được xác lập. Identity/authority/scale/scope/fact approval và
execution authorization vẫn riêng. Nếu cần xin phép theo route đã chọn, bước sau
chuẩn bị request đúng fields trên, không gửi thông điệp trong task này.

## Scale: bằng chứng mới và phiếu K

Tái dùng4HTML cache, kiểm raw hashes/bytes. April C.5 có công thức ba môn + điểm cộng
+ ưu tiên; giới hạn bonus10% không đủ chứng minh tổng≤30. July p6/p7 xác lập THPT gốc
và cutoff bằng nhau giữa tổ hợp; nội suy giữa phương thức khác không áp vào THPT gốc.
Primary header30 chỉ corroboration. Đã kiểm actual CSS bằng selector duy nhất;
flattened paragraph index không được chuyển thành `nth-of-type`.

Hai PDF được lấy qua allowlist PTIT/uploads hiện hữu, đều scan, đọc ảnh trực tiếp:

| Tài liệu | Snapshot / bytes / SHA-256 | Locator và kết quả |
|---|---|---|
| [QĐ1192](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2026/05/QD1192.-Thong-tin-TSDHCQ-1.pdf), ký29/04/2026 | `4ce7666c-e962-48dc-8cfb-d52cc8f285e5` ·1222295B · `769c9465a636692dcb85be6dc53b36c50e59832bba9d78520099c0af23290a48` | PDF5:method5/THPT2026;10–11:bonus; **PDF13/trang in12,II.7(b)/chú thích(*)**: tổng đạt được gồm ba môn không hệ số + bonus, vượt thang thì quy về tối đa; công thức ưu tiên giảm dần từ22.5 |
| [QĐ1547 sửa đổi](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2026/04/QD1547.-Sua-doi-bo-sung-de-an-tuyen-sinh.pdf), ký01/06/2026 | `8828b2ee-f0ed-4a86-b5f8-edb999061ce0` ·440499B · `a3e1b43099228f89a94309a55daf2026317f127a4156a9963089e38a9557dcaf` | Đọc đủ6trang; Điều1 sửa mụcII.4 bảng chỉ tiêu. PDF2/STT14 là QTKD7340101/BVH; không sửaII.7. Không suy ngày văn bản từ thư mụcURL2026/04 hoặc Last-Modified |

**D-P1B5-SCALE-20261022-v1** đề xuất `min_score="0"`, `max_score="30"`, basis
THPT2026 dùng tổng đã quy trần rồi cộng ưu tiên giảm dần. Đây là **supported
interpretation pending owner review**, chưa scale/bootstrap/fact/publication approval.
Artifact private `state/triage/p1-b5-policy-scale-20261022/decision-scale-v1.json`,
SHA256 `a938fa218e78eb4db808671a7774d802eb84cca1d30c2f7f729050dd651c3655`.

Lập luận cận, không phải scoring engine: S là tổng ba môn thang10, không âm; bonusB
không âm và≤3. S+B có thể>30 nên không lấy tổng thô làm cận cuối. Đọc chú thích(*)
là quy tổng dùng trong ĐXT thành R=min(S+B,30). Ưu tiên cơ sởP có cận bảo thủ
0≤P≤2.75. Khi R<22.5, T=R+P<25.25; khi R≥22.5,
T=R+(30−R)P/7.5≤30. Do đó0≤T≤30 theo các premises này. Cận0 không là điểm sàn đủ
điều kiện;22.5 là mốc giảm ưu tiên, không cutoff/eligibility threshold.

Cần review rõ cách hiểu **quy trần áp cho tổng dùng trong ĐXT**, không chỉ một biến
để tính ưu tiên. Đây là diễn giải từ QĐ1192, không công thức ĐXT đầy đủ trích nguyên
văn. Nếu reviewer không chấp nhận cách hiểu đó, giữ scale blocked và cần PTIT làm rõ
đúng PDF13/II.7(b): tổng ĐXT có dùng S+B đã quy trần hay không, hoặc amendment sau
QĐ1192/QĐ1547. Không dùng yes/no chữa thiếu điều khoản, không cần gửi lại toàn PDF.
Không chứng minh không có amendment khác chưa được kiểm. PTIT2024 min0 chỉ là
precedent lập luận; không chuyển approval. Không mở F2/applicant evaluation.

## Từ pilot sang cohort

Private manifest `next-cohort-manifest-v1.json`, SHA256
`2347b7bf2bb02aa4740dec27de3ad35cf1f04e36b4e8cd45014df00666f1b4b2`,
chuẩn bị **6cells/6packets**, gồm pilot1 và5đề xuất thêm: cùng notice2026/BVH/THPT/
đại trà/business-group. Đó là QTKD và năm dòng7340101LG/7340122/7340115/7340301/
7340201DL; actual scores, exact code/name/cell/tie locators, packets/parents và
exceptions giữ private. TTNV khác từng dòng, có `=1` khác `<=`; không dùng một
predicate cho cả cohort. Ba facts2024 loại trừ, không split aggregate cell. Hiện
**0publication-ready**, tối đa6fact mới nếu đủ gates, không phải6facts đã được duyệt.

Một human cohort confirmation sau này phải bind exact manifestSHA, tất cả candidates/
packets, proposed values/shared refs, exclusions/allowed actions, và từng commandSHA
khi đã materialize. Đổi manifest/command cần xác nhận mới. Dùng per-fact validators,
roles, transactions/audit hiện hữu; không hứa atomic multi-fact, không bulk service.
S1 chỉ chọn pilot; không tự mở rộng approval sang5dòng này.

Checkpoints đề xuất: **1fact pilot → ≤10cùng context (hiện chuẩn bị6) →3trường →
đo và chia tranche hướng10/25/50institutions**. Tranche3trường có refs thật PTIT≤6,
UEH-1≤1 và HCMUE-1≤1 từ dossier trước; hai trường sau chưa ready, không tự chọn HCMUE
làm lượt tiếp. Outliers/missing basis/scale/scope giữ loại trừ, ready work được đi
trước. Phương án này tái dùng inventory12profiles, không deep-audit lại.

12profiles không đạt50institutions. Tranche onboarding tiếp **5–10institution mới**
qua inventory/triage/intake hiện hữu, chưa thu trong lượt này. Năm discovery leads
đã đối chiếu tên/mã: DTT/Tôn Đức Thắng, DVL/Văn Lang, KHA/Kinh tế Quốc dân,
NTH/Ngoại thương, DKC/Công nghệTP.HCM. Directory405units chỉ là leads; NTS/campus
không thêm một trường cho NTH. Trước intake: deduplicate identity/context đủ dùng,
chọn official admissions notice/basis cho năm mục tiêu, review source restrictions/
robots/profile, budget riêng rồi raw→T05/T06/T07→dossier. Không đòi roster pháp lý/
địa lý toàn quốc hoàn chỉnh, không lấy fact evidence từ directory.

Đo institutions ready/served riêng; chỉ tính covered khi có≥1eligible fact thực sự
served, mỗiinstitution một lần, year coverage báo riêng. Đo reviewed/published/
rejected và phút owner review/fact; chưa có cohort thật nên chưa throughput estimate.
Campuses/variants không tăng institution count. Manifest expansion/hashes nằm trong
index; Major taxonomy vẫn backlog, không prerequisite cho F1-name/cutoff.

## Thực thi kỹ thuật, checks và giới hạn

3/6new wire attempts = robots+2PDF, đều200;0redirect/retry/browser network/OCR,
0old-run resume/allowlist change. Hai run mới đã paused, không dùng3request còn dư.
Technical intake delta: sources84→86, snapshots77→79, runs63→65, fetches89→92,
schedules77→79, raw-fetch jobs156→158. Sources mới vẫn unverified, không authority
approval; không chạy parser/persisted jobs trên PDF mới.

Read-only count trước/sau: cutoff_scores3→3, Offering3→3, audit47→47,
release1→1; catalog row/version3 và releasev3 row/manifestSHA không đổi. Đây là
phép đo metadata giới hạn cho acquisition, **không full canonical/file preservation**.
Quota helper3/20.000 và bundle checksum là phép đo P0-4 trước, không đo helper/bundle
lại. Không tuyên bố mọi concurrent row/file đều đã kiểm; task không thêm quota.

Dedicated reviewer hiện hữu, READ ONLY REPEATABLE READ/timeout12s, đã revalidate6
checked_packets/digests/parents/current heads; không owner fallback hoặc mở quyền
catalog reader.6unique score cells,12code/name cells và12tie cells khớp DOM; whitespace
`ĐC =0`/packet`ĐC=0` được ghi rõ, không sửa raw/packet. Hash/size4cachedHTML+2PDF,
unique actualCSS và3confirmed payloads đã kiểm. Hash không chứng minh rights/ngữ nghĩa.

API ready200/web majors200 ở lượt health nhẹ; giữ services/volume loopback. Real F1
smoke là kết quả P0-4 đã pass, không chạy lại hoặc lấy static checks/CI mock làm smoke.
Không app code/test mới, không DEV fixtures/full DB suite. Static JSON/count/hash/
provenance/links/LF và dashboard guards là checks phù hợp; CI hiện hữu chạy disposable
DB sau normal push. Final SHA/remote/checks/web kiểm lúc bàn giao, không commit vòng
lặp nhúng SHA của chính report. Private logs/raw/screenshots/review sheets không Git.

Dashboard chính thức ngoài Git cập nhật narrow P1-B5 subtask needs_review,
policy_choice_pending/scale_interpretation_pending/cohort_prepared/publication_blocked;
không đóng P1-B5/P2-X1, không nâng toàn F1/P2-F2; giữ rosterA/receipts/F2deferred.
Đúng4next trong index/tracker: **P1-B5 policy → P1-X3 scale/context/authority →
P2-X1 separately authorized pilot/cohort → P3-X1 national tranche quaP1-B5 intake**.
Chọn bốn mục vì chúng giải quyết decision thật, phần review còn lại, execution riêng
và coverage vượt12profiles; không đưa taxonomy/roster thành blocker F1 mới.
