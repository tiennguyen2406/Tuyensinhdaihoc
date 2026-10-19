# T08 — PTIT publication evidence review, 18/10/2026

Lô này hoàn thành phần đối chiếu evidence và chuẩn bị quyết định độc lập; **chưa approval/bootstrap/publication dữ liệu thật**. Ba cutoff vẫn blocked. T08 toàn bộ, T09 và quota 20.000 chưa hoàn thành.

## Hiện trạng và phạm vi xác minh

Bắt đầu tại `codex/crawler-pilot`, HEAD `8c3d6fa09e4b6a331d1ca14dc566fb6cb2e9c515`, origin `https://github.com/tiennguyen2406/Tuyensinhdaihoc.git`, working tree sạch. PostgreSQL ở `0003_publication (head)`. Đã đọc README/config/contracts T05–T08, models/validators/SourceProfile, hồ sơ pilot, Overview/WBS trên Desktop theo provenance hiện hữu. Không có AGENTS.md trong repo/các thư mục cha được kiểm tra. Không sửa tài liệu tham chiếu hoặc migrations đã áp dụng.

Baseline: 645 observations, 17 jobs, sáu snapshots/blobs; canonical cutoffs/catalog version/releases = **0/0/0**. Sáu raw blobs đã kiểm hash/kích thước trước xử lý. Ba packet T07 cũ vẫn giữ binding và digest. Không dùng 645 observations như 645 facts, không giải phóng 118 blocked attempts hoặc 166 inputs chưa typed adapter của T06.

Đọc raw HTML trước; PDF scan 2025 được render bằng PDFium qua pdfplumber và đọc trực quan các trang liên quan, không OCR. Đây là review nội dung của agent, không phải người phụ trách ký duyệt hoặc xác thực chữ ký tài liệu.

## Request budget và evidence thực tế

Dùng đúng Crawler/Store/Transport/RawStorage hiện hữu, cùng shared host budget (concurrency1, 0,5 request/giây), robots/cache TTL, allowlist, pinned public IP/SSRF, TLS và size limit. Không dùng search engine/snippet hoặc downloader thay thế. Chỉ truy cập `tuyensinh.ptit.edu.vn`; không portal/login/CAPTCHA.

| Run bổ sung | Allocation hiện tại | Đã dùng | Trạng thái |
|---|---:|---:|---|
| `8693513c-b7bb-4377-a4cf-ef8981c2088d` | 1 | 1 | paused, chuyển phần chưa dùng sau khi phát hiện path filter quá hẹp |
| `4adcf376-29cb-47d5-a633-43ab5678a278` | 19 | 4 | paused, đã đủ để lập lô review/gap cụ thể |
| Tổng | **20** | **5** | **15 chưa dùng, không tiếp tục tự tải** |

Run đầu ban đầu có cap20, sau request đầu giảm cap xuống đúng1 đã dùng; run mới chỉ nhận19 còn lại, không cộng thêm quota. Profile cũ/manifests gốc được giữ. Hai profile công khai trong config/sources/ ghi căn cứ access/robots và giới hạn; `verified=false`, eligible chỉ về kỹ thuật. Quyền tải để review nội bộ không là quyền thương mại/tái phân phối toàn văn.

Năm requests đều HTTP200: ba truy vấn WordPress discovery JSON và hai trang HTML nội dung. Robots còn cache hợp lệ nên không phát sinh request robots mới; không redirect/retry/attachment request mới. Budget đếm mọi request thực tế, không chỉ URL thành công. Có ba task discovery còn queued; mọi run bổ sung đã paused. Run pilot cũ `6ee6fd0d-60ae-4858-94ef-733967012bf5` vẫn paused5/5; run preflight cũ paused1/2, nguyên trạng.

### Evidence đọc được và phạm vi authority đề xuất

| Nguồn | Snapshot / SHA-256 | Locator và điều chứng minh |
|---|---|---|
| [Đề án 2024](https://tuyensinh.ptit.edu.vn/de-an-tuyen-sinh/de-an-2024/) — cached | `ce670b50-64dc-41b3-b25f-c7509bdb3b95` / `199a58f9dca0095596e8c710379daaf9d31eb615c6760eccfa1d25c1db85dd0a` | `#dao_tao_chinh_quy`, direct text nodes: nguyên tắc theo ngành/tổ hợp, cùng điểm giữa tổ hợp, ba môn thang10/tổng tối đa30, ưu tiên và xử lý bằng điểm. Eligibility chung có, phạm vi population của từng cutoff chưa đủ |
| [Thông tin 2025 PDF](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2025/05/6.-Thong-tin-tuyen-sinh-DHCQ-nam-2025-1.pdf) — cached | `f02f3e8f-b7bb-4e36-a60e-9a683afba099` / `11515001282b4626f76ba32c72cf2bd7a89a5fa677dc10ae63b9ad091f37786b` | Visual p1: một Học viện, BVH/BVS Bắc/Nam, chính quy. Phần lịch sử 2024: p10 QTKD BVH25.17/30; p11 CNTT BVH26.40/30; p13 QTKD BVS18.40/30. Không dùng bảng tổ hợp tuyển sinh 2025 cho 2024 |
| [Thông tin 2026 HTML](https://tuyensinh.ptit.edu.vn/de-an-tuyen-sinh/thong-tin-tuyen-sinh-dai-hoc-chinh-quy-nam-2026/) — cached | `19a1088e-6412-49e4-b911-73ec9146f4fa` / `03a243b651c18fd2e89beb89676e2adb9722c66922d8e1758138c6c1bb7b7586` | Section chính quy, bảng6 BVH/bảng7 BVS, cột lịch sử THPT2024. Chỉ đề xuất authority cho thông tin lịch sử2024 này, không gán năm trang2026 cho ô |
| [Điểm trúng tuyển 2024](https://tuyensinh.ptit.edu.vn/gioi-thieu/xem-diem-cac-nam-truoc/diem-trung-tuyen-2024/) — mới | `e851f5d0-64dd-4477-b77a-1b7a0c2dc217` / `5204c9abdfb819ae947235e9053c2fd31c9aed75aad1c612c0be8cc1109fb528` | Root `[data-elementor-id="3730"]`, table1: tr7/td4 QTKD BVH; tr7/td8 QTKD BVS; tr17/td4 CNTT BVH, kèm header BVH/BVS và THPT(100). Có TTNV mà bảng lịch sử khác không hiển thị |
| [Thông báo ngưỡng THPT2024](https://tuyensinh.ptit.edu.vn/thong-bao-nguong-dam-bao-chat-luong-dau-vao-trinh-do-dai-hoc-he-chinh-quy-dot-1-nam-2024-theo-phuong-thuc-xet-tuyen-dua-vao-ket-qua-thi-tot-nghiep-thpt-1721278152754/) — mới | `4b1ed251-85b2-4faf-a020-4ad730ea4d23` / `ec77e69ef5b27a389f11b65a9bf9ec83ec4cc9d11290b90a10dc13f7856efcbb` | `article.post-wrap div.post-content`, p1–4: ngưỡng BVH22/BVS18, chính quy đợt1, A00/A01/D01, gồm ưu tiên. **Không là điểm trúng tuyển**; không chuyển đợt1 hoặc mọi tổ hợp sang ba cutoff |

Ba discovery JSON được lưu có checksum nhưng không là evidence nghiệp vụ: snapshots `4dd7bad3-f231-4388-b204-87c83d75daa2`, `f96c0348-b003-45a4-83c9-900d39983e58`, `3356fa7f-586f-4ada-a5db-ecc68b7ed6ad`. Journal private giữ URL/status/hash/byte size và request accounting từng bước. Không tải các kết quả hệ từ xa/vừa làm vừa học không đúng phạm vi.

Ma trận private `state/publication/evidence-review-20261018/field-matrix.json` chứa 20 fields mỗi hồ sơ và 14 evidence refs: proposed value, nguồn, snapshot/hash, CSS cụ thể/ô và header, text-node index/excerpt hash hoặc PDF page/bbox thủ công, confidence/conflicts và tác động gate. Direct text-node index đếm zero-based NavigableString con trực tiếp **kể cả whitespace-only**, strip node để đối chiếu excerpt. Không giả PDF OCR cell locator. Mọi CSS resolve được; hash/kích thước và số trang đã kiểm lại.

## Bảng duyệt ba hồ sơ

| Hồ sơ THPT2024 | Giá trị và điều kiện nguồn | Evidence hỗ trợ | Phạm vi đề nghị và tình trạng |
|---|---|---|---|
| Quản trị kinh doanh /7340101/BVH | Decimal25.17; literal `25.17 TTNV<=13` | HTML2024 tr7/td4; PDF2025 p10 cột2024/30; HTML2026 bảng6 cột2024 | Một Offering2024 BVH; chưa approve fact hoặc điều kiện |
| Quản trị kinh doanh /7340101/BVS | Decimal18.4; literal `18.4 TTNV<=3` | HTML2024 tr7/td8; PDF2025 p13 cột2024/30; HTML2026 bảng7 cột2024 | Một Offering2024 BVS riêng; không gộp với BVH |
| Công nghệ thông tin /7480201/BVH | Decimal26.4; literal `26.4 TTNV<=5` | HTML2024 tr17/td4; PDF2025 p11 cột2024/30; HTML2026 bảng6 cột2024 | Một Offering2024 BVH; chưa approve fact hoặc điều kiện |

Số điểm khớp giữa ba nguồn, confidence nội dung cao, **không phải fact verified**. TTNV là thông tin bổ sung đáng kể; không bỏ footnote để tạo unconditional cutoff. Cách ánh xạ TTNV và khi nào điều kiện áp dụng vẫn cần người phụ trách xác nhận theo văn bản gốc. Không đưa chữ ký PDF thành chữ ký của reviewer.

| Nhóm fields của cả ba hồ sơ | Đề xuất / phần còn thiếu | Tác động |
|---|---|---|
| University/code system/campus | Một PTIT; BVH/BVS là mã tuyển sinh theo cơ sở Bắc/Nam. PTIT là khóa registry nội bộ đề xuất, không thay thế hệ mã nguồn | Đủ để trình bootstrap riêng; chưa canonical trước apply |
| Program, Offering, mã ngành/mã xét tuyển | Giữ tên và mã nguồn 7340101/7480201 đúng năm/campus. Không coi source code tự động là Major ID. Cần quyết định Program QTKD dùng chung hai campus hay hai Program trong cùng trường; dự kiến ba Offering khác nhau | Chưa có Program/Offering UUID và binding T07 mới. Chặn publication; không bịa target IDs |
| Track, language, training mode, Major | Track/language unknown/UNSPECIFIED theo schema; chính quy có evidence; Major có thể NULL | Unknown optional không tự chặn. Không điền MAIN/GENERAL/ngôn ngữ giả hoặc ép taxonomy campus |
| Method/authority | THPT100 có tên/ngữ nghĩa trực tiếp; internal key đề xuất PTIT_THPT_2024_100. Bốn source được đề nghị authority years2024 theo fact_kind phù hợp | Chưa reviewer approval. Authority của tài liệu, quyền sử dụng và duyệt fact là ba quyết định khác nhau |
| Scale/basis | Max30 có câu nguồn và mẫu số PDF rõ, ba môn thang10. Min0 chỉ là proposal cận kỹ thuật theo numeric invariant/DDL, nguồn chưa riêng biệt công bố lower endpoint | Cần review cận dưới và verified scale/basis; không suy max từ độ lớn điểm. Ngưỡng18/22 không phải min_scale |
| Combination | Nguyên tắc cùng điểm giữa các tổ hợp trong cùng ngành có evidence. Đề xuất source_aggregate, một fact không nhân tổ hợp; membership từng Offering chưa resolve | Aggregate scope có thể được review theo source; không là confirmed_none/wildcard. A00/A01/D01 của ngưỡng chung không chứng minh từng Offering |
| Round/population | Chưa rõ round của bảng cutoff. Eligibility chung có nhưng population chính xác cho ba cutoff chưa ánh xạ | Chặn publication. Không chuyển round1 từ thông báo ngưỡng hoặc điền GENERAL |
| Conditions/footnotes | Giữ ba TTNV literal; đề án có nguyên tắc xử lý bằng điểm | Chặn đến khi canonical predicate/applicability được review; không conditions rỗng hoặc confirmed_none |
| Scoring rule | Có văn bản nguyên tắc/ưu tiên, chưa typed DSL được duyệt; T08 không thực thi | Thiếu rule riêng chỉ chặn tính/so sánh, không tự chặn cutoff đã đủ scale/basis/scope; aggregate luôn unavailable_aggregate_scope |
| Publication/effective time | Chưa xác định thời điểm công bố gốc; năm fact2024 rõ theo header | Optional unknown cho initial reviewed fact. Không gán ngày ký2025 thành ngày hiệu lực2024 |

Đã đọc đề án2024, bảng cutoff2024, phần lịch sử PDF2025/HTML2026 và thông báo ngưỡng2024. Chưa tìm được trong các nội dung đã đọc văn bản công bố cutoff gốc gắn rõ round/population và diễn giải điều kiện. Đây là gap trong tập evidence đã kiểm, không tuyên bố không có tài liệu trên Internet. Dừng ở5/20 để trình gap và bước xử lý cụ thể, chưa cần tiêu hết budget.

## Quyết định A có thể duyệt độc lập

Private `bootstrap-identities.draft.json` là ReviewCommand hợp lệ, request/binding/digests và expected versions đã đóng băng; không có actor tự nhập/chữ ký/approval. Binding T07 thực `97259d1b-894c-4637-9e09-8c237ce15c78`, candidate key `857495c2612874e9c1e25b2705660fe920db5a76f35bbe81cade944d9b451277`, packet SHA `aed252aa06294031dd08c3f4784599985051804d6f53aa0f2844f0c8e7ef2fd3`.

Expected registry/alias: `registry/ptit-pilot/1`, `aliases/ptit-pilot/1`; đề xuất mới `registry/ptit-reviewed-identities/20261018-r1` và `aliases/ptit-reviewed-identities/20261018-r1`.

Plan đọc bằng dedicated reviewer trả `preview_only=true`, `can_apply=true`, **10 operations** có thứ tự: tạo một University PTIT; một method THPT2024; một admission-year2024 statuspartial; link bốn nguồn (HTML2026 lịch sử, đề án2024, PDF2025 lịch sử, bảng cutoff2024); tạo ba university aliases từ proposals hiện hữu (tên đầy đủ, PTIT, domain tuyển sinh). BVH/BVS giữ hệ mã/campus có provenance, không tạo hai University hoặc aliases mã toàn cục giả.

Authority link đề xuất scope years2024, cutoff cho ba bảng lịch sử/cutoff; scoring_rule/catalog cho đề án2024 để phục vụ basis evidence. **Chưa approve rule hay mọi fact của các nguồn.** Runtime authority scope kiểm year/fact_kind, không có allowlist ô hoặc method; giới hạn nghiệp vụ chi tiết phải giữ trong decision reason/evidence và review fact sau đó.

Nếu người phụ trách duyệt và áp dụng ở lượt sau: **6 catalog rows mới** (University1, method1, year1, aliases3), **4 source rows cập nhật**, **2 jobs registry/review**, **11 audit events**. **0 Program, Offering, scale, scope, cutoff, refresh; dataset_version không tăng.** Program/Offering sau này dự kiến ba Offering; số Program2 hoặc3 còn là quyết định chưa duyệt, không gộp ngầm.

Precheck độc lập đã kiểm required columns/enums, unique keys hiện tại, source tồn tại và snapshot của chính source, nguồn chính thức cùng publisher/host, ordered parent refs, hash/locators/pages. Preview không chạy tất cả SQL constraints/triggers như apply; `can_apply` không là business approval hoặc cam kết SQL apply đã được diễn tập. Preview registry có metadata dự kiến được approve là **mô phỏng**, không được export/sử dụng như registry đã duyệt.

Không tạo ReviewCommand publication cho ba fact: fake UUID/default round/population/conditions sẽ khiến nó chắc chắn fail hoặc sai nghiệp vụ. `publication-gaps.json` ghi exact fields thiếu. Bước nhỏ nhất: (1) người phụ trách quyết định riêng A; (2) quyết định Program/ba Offering có evidence, canonical parents và T07 replay version mới; (3) nối thông báo cutoff gốc/diễn giải TTNV với round/population, review scale-min và predicate; (4) tạo ba fact drafts mới gắn binding/evidence mới. Không sửa envelopes/manifests cũ; không cần chế DSL để vượt gate.

## Hai điều chỉnh gate có căn cứ

Đối chiếu DDL/EduRadar về nullable combination/Major và nhiều evidence/source, cùng yêu cầu không nhân tổ hợp của lô này:

- Gate cũ chỉ cho bootstrap source của packet, khiến tài liệu basis chính thức đã cache nhưng không có T07 candidate không thể được review authority. Nay cho supporting source **cùng publisher/domain**, official type, evidence phải là snapshot của chính nó; vẫn cần reviewer/audit/versions. Không tự nhận cross-host hoặc quyền thương mại. Regression positive và ba negatives (snapshot sai, foreign host, press).
- Gate cũ chỉ có specified/confirmed_none nên không biểu diễn đúng một mức điểm chung cho nhiều tổ hợp. Thêm source_aggregate nội bộ với NULL combination, evidence combination_aggregation riêng, basis đóng băng trong condition_key, không mở unknown/default. Một fact, không Cartesian expansion; computation unavailable, từ chối combination-specific rule. Regression một fact/replay và thiếu evidence bị chặn.

Logic dùng `publication/1.1.0`; không migration/dependency/lockfile mới và không viết lại provenance/outputs1.0.0. RED trước sửa:2fail/4pass; GREEN sau sửa:6pass. Các guards khác và history giữ nguyên. Reviewer agent đã đọc ba modules, test diff và callers liên quan, không có actionable findings trong phạm vi; review read-only, không chạy tests/đọc private raw/credentials. Đây là review mã tách biệt với review nghiệp vụ, không là đánh giá toàn bộ hệ thống.

## Accounts DEV và dữ liệu bất biến

Đã chạy `uv run python -m scripts.provision_publication_roles` và cơ chế local provision. Hai LOGIN `eduradar_dev_reviewer`/`eduradar_dev_publisher` lần lượt chỉ thuộc group tương ứng. Không superuser/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS. Kết nối thật kiểm capability đúng, capability đối diện bị từ chối, không DELETE history; reviewer không INSERT cutoff trực tiếp. Không ghi approval thử vào database dự án.

Password ngẫu nhiên lưu trong ignored `state/publication/access/local-dev-credentials.json`, Windows ACL owner/SYSTEM, không stdout/history/report/Git; SQL nhận SCRAM verifier. `.env` giữ nguyên hash/các giá trị. Workflow chỉ đọc credentials vào process env để chạy plan rồi xóa biến. Đây là danh tính kỹ thuật development, chưa production authentication hoặc người phụ trách duyệt.

| Bảng/đối tượng | Trước → sau | Giải thích |
|---|---:|---|
| observations | 645→645 | Toàn bộ rows cũ giữ nguyên PK/full-row digest |
| ingest_jobs | 17→25 | +8 raw_fetch jobs, 5 fetch đã thực hiện và3 queued; 17 jobs cũ không sửa |
| source_snapshots / sources / crawl_schedules | 6→11 mỗi bảng | +5 theo supplemental fetches |
| crawl_fetches | 6→11 | +5 HTTP200 |
| crawl_runs | 2→4 | Hai run bổ sung ở trên; hai run cũ nguyên trạng |
| crawl_host_states | 1→1 | Một row coordination/limiter đổi do fetch, không gọi là bất biến |
| Canonical entities/scopes/cutoffs, audit/quality issues, catalog/release | Không có business delta | Cutoffs/catalog version/releases vẫn **0/0/0** |

Private baseline và verification-proof đối chiếu PK/hash từng row của34bảng: không mất hoặc sửa old observations/jobs/raw snapshots/sources/catalog; chỉ host coordination row cũ đổi hợp lệ. Các files packet/manifests lịch sử không bị ghi đè; review-batch cũ được sao lưu trước tạo batch mới. Mười một raw blobs sau bổ sung đều khớp SHA-256 và kích thước. Không tuyên bố toàn database không đổi; role grants/logins là thay đổi riêng ngoài các bảng ứng dụng.

## Kiểm chứng và chạy lại

| Lệnh/kiểm tra | Kết quả thực tế |
|---|---|
| `uv run pytest -q` baseline | 506 passed,184.09s |
| `uv run pytest -q` sau sửa logic | 512 passed,171.25s; precommit chạy lại sau import fix:512 passed,182.44s; database test riêng, fixtures offline |
| `uv run ruff check .` | Pass sau sửa import order hai test |
| `uv run ruff format --check .` | Pass,126files |
| `uv run mypy` | Pass,55sourcefiles |
| `uv lock --check` | Pass,87packages, không đổi dependencies |
| `uv run alembic current` / `uv run alembic check` | 0003_publication(head) / no new upgrade operations |
| `uv run python -m services.crawler validate <profile>` cho hai profile thật | Pass |
| CLI publication plan với dedicated reviewer | Exit0,10ops,preview_only/can_apply true; không apply |
| `/health/live`, `/health/ready` local | HTTP200, statusok/databaseconnected |
| Raw/evidence, old-row digest, role checks | Pass theo proof private; giới hạn kiểm tra nêu ở trên |
| `git diff --check` | Pass |

Docker/PostgreSQL hiện hữu được khởi động lại, không xóa volume; API local được chạy tại127.0.0.1:8000 để kiểm health. Xem docs/review-workflow.md để chạy lại **plan** bằng credential local mà không nhập password vào history. Các lệnh CLI apply trong workflow chung **chưa được thực hiện trên lô này**.

Commit chỉ code, profiles và tài liệu vận hành; raw, source excerpts/outputs, private decisions, credentials và dumps nằm ngoài Git. Sau push sẽ kiểm GitHub Actions trên đúng SHA; kết quả/link cuối cùng ghi trong bàn giao, không suy CI từ local tests. Không merge main/deploy production.

Đủ bàn giao review/gap có evidence. Quyết định người phụ trách có thể đưa ra ngay là **duyệt hoặc yêu cầu sửa Draft A về identities/source authority**, không là duyệt ba cutoff hoặc các field chưa rõ. Mọi thay đổi nghiệp vụ thật phải ở lượt sau theo quyết định cụ thể.
