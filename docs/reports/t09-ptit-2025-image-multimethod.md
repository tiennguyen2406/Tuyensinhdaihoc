# T09/T08 — PTIT 2025 image tables: bounded evidence intake, feasibility blocked

Baseline local/remote đã đối chiếu `84b783de1096758a41c8bc9ab9435ef4db8d1cd9`,
nhánh `codex/crawler-pilot`. Kết quả task: **thu đủ bốn ảnh chính thức, inventory đủ
410 ô score, nhưng chưa có transcription đủ tin cậy để tạo numeric candidates**.
0 T05/T06/T07 image jobs, 0 image T08 packets, 0 approval/bootstrap/publication/release.
Không tuyên bố hoàn thành numerical acceptance của cả hai objectives.

## Acquisition và frozen provenance

Đã xác minh bốn exact URLs trong business region của HTML B/C bất biến, bằng `<img src>`
và locator gốc; không chỉ dựa vào research lead hoặc domain. Parent B:
`204ec544-89df-456a-a2ba-6eb9b82396db`, hash
`8eba337c282e63d8df2ded36f9c5038ccf188ad53a249365e33d772195708fc9`;
parent C: `d50d1e1c-592a-48da-9698-4d084c1d01c1`, hash
`c7b810ecf4f84d739766459cd971ac94c0d01fdc46c86ffc858c634f13ffe6bd`.

Cả bốn ảnh cache-miss. Existing crawler/frontier/RawStorage/URLPolicy/DNS/SSRF/TLS,
host limiter concurrency1/0,5rps/burst1, exact URL allowlist, depth0 được dùng nguyên.
**4/6 wire requests**, bốn HTTP200, 0 redirect/retry; robots cache24h còn hạn nên0robots
request mới. Một preflight và bốn fetch runs đều paused; không resume run cũ.
Không browser, mirror, portal, link discovery hoặc attachment khác. Tổng2.085.750bytes.

| Asset chính thức | Snapshot | MIME / dimensions | Bytes | SHA-256 |
|---|---|---|---:|---|
| [B1 BVH](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2025/08/diem-Bac.png) | `43735377-f69d-4807-991b-e64370d3958e` | PNG 467×764 | 60414 | `279b9fb194af76fa6dd3a887dbd32c36ee77c9ca40f6182ff44cb8e97656ffad` |
| [B2 BVS](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2025/08/Anh-man-hinh-2025-08-22-luc-23.55.58.png) | `d6dc7f06-3bfd-4dd9-a6ca-5f63cf0c898b` | PNG 1542×1232 | 649850 | `f0f5dd0fe27c252134a2896601a47311760e75152a8bd6c32112227a3e76eff1` |
| [C1 BVH](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2025/08/p1j3b5tjm91v9s1oon1ea8dnv12mf4-0-scaled.jpg) | `f3cb7533-795f-4866-b202-8f38709b9f65` | JPEG 2147×2560 | 840288 | `e10204f441ffea02e6d8e61e0994b77d637c03263588b11bdc7e6a33c5c8e175` |
| [C2 BVS](https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2025/08/p1j3b5tjm91v9s1oon1ea8dnv12mf4-1-1-scaled.jpg) | `5f6d27d5-5c55-4a2c-95e7-07ec4d09be89` | JPEG 2560×1758 | 535198 | `6d099bc67ab8c346d74cee355d882b08d0fc1fcec54ed403d709536346a25b55` |

Ảnh ở content-addressed RawStorage, không commit ảnh/crop. Manifest riêng giữ source ID,
parent URL/ID/hash/link locator, raw URI/path, MIME/dimensions/hash và retrieval accounting.
Nguồn first-party/robots allowance không tạo license lưu/chuyển đổi/tái phân phối thương mại.

## Feasibility gate và hạn chế chính xác

Local có Pillow sẵn qua locked dependencies và Windows.Media.Ocr với duy nhất language
`en-US` trong recognizer list. Không thấy Tesseract ở PATH/hai install paths thông dụng;
không có pytesseract/tesserocr/easyocr/paddleocr/cv2 trong environment hiện tại. Không cài
package, model, subscription hoặc gọi cloud OCR/vision API.

Chạy một lần OCR native mỗi ảnh (4 cached passes), rồi 8 bounded-row crops: B1/C1 lấy
hàng AIoT và UDU, B2/C2 lấy CNTT và CNTT CLC. Mỗi notice có hai hàng mỗi campus; mẫu có
THPT, SAT/ACT và TTNV hiển thị. Crop giữ bbox gốc, scale/padding, hash và raw words/bboxes.

**Gate failed cho unattended factual extraction**:

- B1 nhỏ467×764: raw OCR `VDV` thay `UDU`, mất code digits/underscore và nhiều điểm/toán tử.
- Các crop B/C đọc được nhiều số, nhưng bỏ TTNV; C2 có chuỗi `TTNV<` kèm ký tự lỗi/bound rời.
- Một số TTNV đọc được ở C2-2 không chứng minh đủ mọi phương thức. Cờ probe chỉ là
  `contains_any_parseable_TTNV`, không gọi là complete.
- Ảnh C lớn nhìn rõ layout; blocker là độ tin cậy engine hiện có, không kết luận mọi ảnh
  đều thiếu resolution. Assistant xem pixels để kiểm layout không phải human confirmation.

Không đoán sửa I/O/S thành1/0/5, không nối suffix/method từ2026 hoặc điền số từ archive.
Không tiếp tục full numerical intake sau gate thất bại. Raw OCR toàn ảnh là hypotheses
có cache để chuẩn bị manual review, không phải verified transcription.

## Full pixel accounting và archive reconciliation

| Ảnh | Program rows | Score columns | Score slots | Verified / already represented | Manual |
|---|---:|---:|---:|---:|---:|
| B1 BVH | 28 | 1 | 28 | 0 / 0 | 28 |
| B2 BVS | 13 | 1 | 13 | 0 / 0 | 13 |
| C1 BVH | 28 | 9 | 252 | 0 / 0 | 252 |
| C2 BVS | 13 | 9 | 117 | 0 / 0 | 117 |
| Tổng | 82 | — | **410** | **0 / 0** | **410** |

Invariant410=0validated+0represented+410manual+0confirmed-missing+0invalid.
369 C slots không có nghĩa369valid numeric cells; số ô thiếu thực sự chưa xác lập bằng
independent transcription. Không coi OCR không đọc được là source missing. Header regions
và hai section headings mỗi ảnh được tách riêng; C giữ ba header bands trong một region.

Source-specific grid dùng pixel rule projections; ảnh B2 scanned hơi nghiêng dùng conservative
rectangles đã xem layout. Mỗi ô có image SHA, row/column, absolute/normalized bbox, code/name/
header/TTNV boxes, raw OCR words, recognition status. Row alignment với41HTML catalogue chỉ
là proposed_by_physical_order; tên/mã HTML được ghi rõ reference, không giả là text OCR ảnh.

41 hàng HTML có đầy đủ candidate key/packet SHA cũ, score/TTNV HTML và ảnh B liên quan.
**32 unverified OCR numeric readings trùng Decimal HTML; 9 chưa đủ reading phù hợp**.
Chưa hàng nào được coi corroboration hoàn chỉnh do còn code/name/TTNV verification.
41original methods vẫnNone, không sửa envelope/packet, không tạo lại candidate.

C1 có cột TTNV riêng: phạm vi áp dụng giữa các methods còn review, không tự fan-out.
C2 gắn TTNV trong từng ô phương thức: giữ riêng, không dùng archive TTNV cho cả chín cột.
Cross-source relation của41families hiện `unresolved`; 0 verified merge/correction,
0 new unique business facts. Logical source-cutoff inventory vẫn939, canonical vẫn3.

## Method/scale và contract boundary

Thứ tự cột C được giữ theo pixels: THPT2025/30; hồ sơ năng lực–tài năng/100;
SAT/1600; ACT/36; HSA/150; TSA/100; SPT/30; **APT/1200**; kết hợp/30.
Đây là nominal source-header context, không phải approved Scale/basis hoặc applicant
comparability. Không alias APT sang V-ACT2026, không convert hoặc thực thi T12/T13.

T05 hiện chỉ chấp nhận `html_dom`, `pdf_text`, `pdf_table`; registry không có image adapter.
Task không thêm extraction method chưa dùng hoặc giả pixel thành HTML cell. Raw OCR và
pixel ledger lưu private staging. Chỉ sau trusted transcription mới đáng triển khai adapter
hẹp với genuine image snapshot/bbox, parent hash binding, frozen parameters và T08 inspection.
0 new Program/Offering/Method proposals, không đổi global registry/aliases/2026 pending.

## Minimal implementation và verification

Chỉ thêm `services/crawler/images.py`: PNG/JPEG strict MIME-to-decoder format, full validation,
static-frame requirement,25MiB/40Mpixel/16384dimension caps, decompression-bomb safeguards.
`downloader.media_type` gọi helper trước khi RawStorage persist. SVG/animation/corrupt/mismatched
MIME bị chặn; không bật image discovery, OCR hoặc parser tự động. Một profile versioned chỉ
bốn exact assets. Không dependency/migration/framework mới.

9 focused synthetic tests cho MIME/signature/corruption/limits/static frames/dimensions và image
không fallback thành HTML parser. Crawler download và PTIT2025 regressions cùng đạt36tests;
**740 full backend tests đạt** trong339,44giây. Ruff check/format, mypy83files, frozen offline
lock và Alembic head/check đạt. Backend/frontend CI exact pushed SHA được kiểm lúc bàn giao,
lưu private `github-ci-final.json`.
Không benchmark50k, không giảm validator hoặc sửa CI. Real validation dùng bốn ảnh thật,
410uniquepixel boxes,41original checked_packets, full DB/file digests và replay cache.

Native full OCR tổng1,643giây,8crop probes tổng0,474giây (chi tiết stopwatch trong JSON);
đây không phải throughput của verified candidates. Token/SQL-read counters không có, không ước lượng.

## DEV, replay và correction tài liệu cũ

| Chỉ tiêu | Trước | Sau |
|---|---:|---:|
| Sources | 52 | 56 |
| Raw snapshots | 45 | 49 |
| Observations | 1841 | 1841 |
| Ingest jobs | 104 | 108 |
| Canonical / catalog / audit | 3 / 3 / 47 | 3 / 3 / 47 |
| Immutable release / facts v3 | 1 / 3 | 1 / 3 |

Tăng đúng4fetchjobs;0T05/06/07imagejobs,0newimageT08packets. Đã kiểm lại41HTMLpacket hash
và parent manifests bằng checked_packets readonly; methodsNone nguyên. Hai lần đọc exact cache
và image validation cho kết quả bằng nhau,0HTTP/0insert, mọi table digest nguyên trong replay.
Không tuyên bố T05/T06/T07 image replay khi chưa có image pipeline hợp lệ.

Mọi hàng cũ34tables và **1.515historical files** giữ digest, chỉ host limiterPTIT đổi do
acquisition. Releasev3 ID`396ccd8b-1193-43dd-a08a-bb19e639dd56`, hash
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`,3exports nguyên.
PTIT2024/2026 và UEH frozen inputs/outputs, approvals và registry heads giữ nguyên;
PTIT2026 attempt1 artifact/replay limitation không bị rewrite. Không restart/delete data.

Report trước có một dòng BVS thừa giá trị13, hiển thị Existing sai. Đã đối chiếu DB,
frozen validation/CSV: BVS13new,0existing. Chỉ sửa dòng table này để Existing=0 và đúng
số cột; đây là documentation correction, không phải data change.

## Handoff tiếp theo

Private `state/intake/ptit-2025-image-multimethod/` có đủ21deliverables, raw OCR/crop probes,
request accounting và full verification. `review-index.md` hướng dẫn tiếng Việt, CSV lọc được
campus/image/row/method/code reference/status. Không commit source ảnh hoặc packet dumps.

Bước nhỏ nhất: một verifier độc lập xác nhận chính xác code/score/TTNV của8crop mẫu bằng
image hash+bbox và ghi competing readings. Sau đó mới xét hoàn tất transcription410ô và
T05image contract task. Vẫn phải có source authority/rights, method/basis, identity/Offering2025,
round/population/conditions review riêng trước publication. Không dùng signoff kỹ thuật này
để tự approve/bootstrap/publish; numerical objectives hiện vẫn blocked.
