# T09 — PTIT 2025 historical full batch

Baseline local và remote đã đối chiếu:
`1447179e24b3f966b5896db7166e60c9b426d710`, nhánh `codex/crawler-pilot`.
Task tạo **41 ứng viên cutoff thật, unverified**, từ 41 ô HTML; không tạo canonical,
approval, bootstrap, scoring rule, publication hay release. `.vscode/`, handoff chưa track,
các packet/manifest PTIT 2024–2026 và UEH được giữ nguyên.

## Nguồn và ngân sách

Không có cache cho bốn URL trước task. Existing safe downloader, URL/host allowlist,
SSRF/DNS/TLS/robots/size/timeouts được giữ; concurrency 1, 0,5 request/s, burst 1,
depth 0, không discovery. **4/7 wire requests**, mỗi URL HTTP 200, 0 redirect/retry.
Robots cache 24 giờ còn hiệu lực, không có request robots mới. Cả năm run mới
(một preflight không request và bốn fetch) đã pause. Không fetch ảnh/attachment/portal,
không OCR, không browser automation. Tổng HTML 448.270 bytes.

| Nguồn chính thức | Snapshot | Bytes | SHA-256 |
|---|---|---:|---|
| [A — archive 2025](https://tuyensinh.ptit.edu.vn/gioi-thieu/xem-diem-cac-nam-truoc/diem-trung-tuyen-nam-2025/) | `819a0041-b48c-4b4a-918d-9560e4cf6adb` | 108081 | `f4e80e50de70f4226e984f91c04144643e819158bc9988007e1bd6d659d6ba44` |
| [B — notice 22/8/2025](https://tuyensinh.ptit.edu.vn/thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2025/) | `204ec544-89df-456a-a2ba-6eb9b82396db` | 120512 | `8eba337c282e63d8df2ded36f9c5038ccf188ad53a249365e33d772195708fc9` |
| [C — các phương thức 23/8/2025](https://tuyensinh.ptit.edu.vn/diem-trung-tuyen-cac-phuong-thuc-xet-tuyen-dai-hoc-he-chinh-quy-dot-1-nam-2025/) | `d50d1e1c-592a-48da-9698-4d084c1d01c1` | 109315 | `c7b810ecf4f84d739766459cd971ac94c0d01fdc46c86ffc858c634f13ffe6bd` |
| [D — quy đổi 23/7/2025](https://tuyensinh.ptit.edu.vn/bang-quy-doi-tuong-duong-diem-trung-tuyen-giua-cac-phuong-thuc-xet-tuyen-dai-hoc-he-chinh-quy-dot-1-nam-2025/) | `00855002-db81-4d5e-bf19-68392023a487` | 110362 | `0f2dd7c0b812534c40509024480d2e1b1f75a1797944f266ef854c2918b1620f` |

Đây là snapshot tự thu và kiểm hash trong RawStorage, không dùng web discovery làm
pipeline evidence. Crawl allowance/official domain không phải giấy phép tái phân phối.

## Kiểm kê vật lý và reconciliation

A có một business root `.elementor-5168 .elementor-widget-text-editor > .elementor-widget-container`
và H1 `Điểm trúng tuyển 2025`, hai bảng với heading campus riêng. Không có ngày
publication archive hay tên phương thức đủ rõ trong vùng dữ liệu.

| Campus | Hàng vật lý | Header | Phân nhóm | Ô điểm chương trình | New typed | Existing | Blocked/excluded numeric |
|---|---:|---:|---:|---:|---:|---:|---:|
| BVH | 31 | 1 | 2 | 28 | 28 | 0 | 0 |
| BVS | 16 | 1 | 2 | 13 | 13 | 13 | 0 | 0 |
| Tổng | 47 | 2 | 4 | 41 | 41 | 0 | 0 |

Invariant: **41 = 41 new + 0 existing + 0 blocked + 0 non-cutoff score cells**.
Sáu hàng header/section nằm ngoài mẫu số. Header có năm cột: TT, tên, mã, điểm công bố,
TTNV. Mọi score/code/name/TTNV/header/section/title locator đã được đối chiếu lại với
RawStorage bytes; Decimal giữ chính xác giá trị raw. Không span reference hoặc ô trống
nào tạo ứng viên. Mã gốc giữ cả khoảng trắng và suffix, gồm `7520207_ AIoT`,
`7340101_ LOG`, `7480201_ CLC`, `7480201 _UDU`, `7480201_CLC`.

## Phương thức, basis và thông báo đương thời

41 ứng viên đều **`method=None`**, `needs_review`, không canonical scale/basis/rule,
round/population/conditions/combinations. Nullable method đi qua T07/T08 bình thường,
không cần giả THPT Method. Training mode cũng chưa tự điền từ notice khác.

- B có text thang điểm 30, đã gồm ưu tiên khu vực/đối tượng; tiêu chí phụ thứ tự
  nguyện vọng khi bằng điểm cuối danh sách. Đây là supporting evidence theo notice.
- C nói điểm thi gốc riêng cho phương thức THPT 2025 và điều kiện không quy đổi
  chứng chỉ tiếng Anh/cộng điểm cộng. Chưa chứng minh cột A là đúng cột THPT của C.
- D nêu ngữ cảnh quy đổi đợt 1 và không chênh lệch giữa tổ hợp cùng ngành/chương trình;
  không có thao tác tính điểm, quy đổi hay fan-out từ đó.
- B/C/D không có bảng HTML tương ứng; có lần lượt 4/2/2 ảnh. Không fetch/transcribe
  các ảnh. Do vậy 41 hàng matrix ghi rõ chưa kiểm chứng numeric/program match B/C;
  không khẳng định số giống nhau hoặc coi khác basis là correction đã chứng minh.

TTNV giữ **36 `<=` và 5 `=`**, cùng raw predicate và locator. Header A quy định rõ
khi điểm xét tuyển **bằng** cutoff; không mở rộng sang điểm cao hơn. Parser không
thực thi tie-break. Ngày B/C/D precision=date giữ riêng; ngày A unknown, không backfill
hoặc tự gán Round 1.

## Identity 2024–2026 và T07/T08

Matrix bao phủ 41 hàng, dùng campus, full code, tên và category/track context.
Comparison key bỏ whitespace chỉ phục vụ đề xuất; mã gốc không sửa.

| Đối chiếu | Khớp scoped code/name, chỉ đề xuất review | Có code nhưng khác nhãn | Không code match |
|---|---:|---:|---:|
| Approved 2024 Offerings | 3 | 0 | 38 |
| Pending 2026 Offerings | 25 | 2 | 14 |

Ba hàng khớp 2024: BVH CNTT, BVH QTKD, BVS QTKD; không đồng nghĩa approved identity
hoặc authority năm 2025. Hai nhãn khác cần review: BVH `7480101` Khoa học máy tính
(định hướng Khoa học dữ liệu) ↔ Khoa học dữ liệu (Khoa học máy tính); BVH `7480102`
Kỹ thuật dữ liệu (ngành Mạng máy tính và truyền thông dữ liệu) ↔ Kỹ thuật dữ liệu.
Không merge Program/Offering; campus, track/language và year scope vẫn phải duyệt.

Seed là exact approved head `registry/ptit-scale/20261018-c1`, aliases
`aliases/ptit-identities-authority/20261018-r2`. Registry mới
`registry/ptit2025/20261020-r1` là pending riêng: thêm 41 Program/41 Offering proposals,
0 Method; giữ exact mọi entity/alias gốc, không thay global head. 2024-only BVH/BVS
bindings không tự mở rộng. Cả 41 T07 ambiguous, 0 publication eligible; 41 T08 packets
được `inspect_packet` và `checked_packets` xác thực hash/parent manifests.

## Thay đổi và kiểm chứng

Một adapter hai campus `parsers/ptit_2025.py` dùng `html.table_rows`, origin/span/header
utilities hiện có; normalizer source-specific tương ứng giữ method nullable và TTNV.
Dispatch thêm namespace parser `html-ptit-2025-historical/1.0.0+full-1`, normalizer
`normalizer/ptit-2025-historical/1.0.0`. Resolver bump `1.0.8` vì hash implementation
bao gồm normalizer mới; không đổi matching algorithm. Hai profile versioned giới hạn URL;
profile parser chỉ primary A. Không dependency, migration, framework hay UI mới.

T05/T06/T07 mỗi stage **một job**, mỗi job 41 bản ghi: 123 technical observations,
41 logical cutoff candidates. Bốn fetch jobs riêng; tổng tăng 7 jobs. Replay đúng
namespace trả parser cached, T06/T07 insert 0; mọi table digest giữ nguyên trong replay.
T05/T06/T07 mất 1,330/0,697/1,330 giây; kiểm 41 T08 packet 8,211 giây (tổng script review
gồm đọc/hash file 14,089 giây). Thời gian từ inventory đến snapshot accounting 1.071,342 giây;
không có token counter hoặc SQL-read counter đáng tin nên không ước lượng.

16 focused tests mới và **731 full backend tests đạt** (346,03 giây). Tests synthetic
gắn nhãn rõ; kiểm thật dùng toàn bộ 41 score cells và
RawStorage, không thay bằng synthetic. Ruff check/format, mypy 82 files, frozen/offline
lock, Alembic head/check đạt. CI backend/frontend exact pushed SHA được đối chiếu khi
bàn giao; run URL/conclusion lưu private `github-ci-final.json` và trong final handoff.

Các case gồm code whitespace, campus/year/source guards, nullable method, TTNV operator,
blank/invalid/span, resource error fail-closed, header mismatch diagnostics, T05/T06/T07
replay và T08 integrity trên PostgreSQL test riêng. Không chạy benchmark 50k; không đổi CI.

PTIT2026 attempt parser `1.0.0` giữ nguyên, không tuyên bố executable replay bằng code
`1.0.1` hay code task này. Artifact attempt1 ở private
`state/intake/ptit-2026-full-multimethod/implementation-attempt1/manifest.json`;
implementation cuối PTIT2026 là Git baseline `1447179e24b3f966b5896db7166e60c9b426d710`.
T08 inspect history không đòi thay implementation hash của jobs cũ.

## Bảo toàn DEV

| Chỉ tiêu | Trước | Sau |
|---|---:|---:|
| Sources | 48 | 52 |
| Raw snapshots | 41 | 45 |
| Observations | 1718 | 1841 |
| Ingest jobs | 97 | 104 |
| Current verified published canonical cutoffs | 3 | 3 |
| Catalog dataset_version | 3 | 3 |
| Audit events | 47 | 47 |
| Immutable releases / facts trong v3 | 1 / 3 | 1 / 3 |

Đối chiếu từng digest hàng cũ của 34 tables và **1.354 tệp lịch sử**: mọi dữ liệu,
approvals, registry/alias history, PTIT/UEH packets và snapshots nguyên; chỉ operational
limiter row host PTIT đổi theo fetch đã cấp phép. Release ID
`396ccd8b-1193-43dd-a08a-bb19e639dd56`, manifest
`b5b1669c923f171f0a6b68ef67f39a014eb80cbddcbb147c94bef4f30eba5a90`
và export count 3 không đổi. Không restart service hoặc xóa DB/files/volumes.

Logical source-candidate inventory sau dedup: **898 + 41 = 939**. 1.458 normalization
candidate instances gồm 519 technical re-extractions của PTIT2026; không đếm chúng
thành facts mới. Canonical published total vẫn **3**, không phải 939 và không gần quota
20.000 hơn theo tiêu chí canonical chỉ vì intake thành công.

## Bàn giao

Private `state/intake/ptit-2025-full-historical/` có đủ CSV/JSON inventory, ledgers,
41 typed values, TTNV, notice reconciliation, cross-year identity, bindings, validation,
replay, before/after, request logs và metrics; `review-index.md` giải thích tiếng Việt.
Không commit source bodies hay packet dumps.

Quyết định mở khóa trực tiếp nhất: xác minh và duyệt **method applicability/basis của
cột archive A** đối với thông báo gốc B/C bằng evidence đúng phạm vi. Sau đó vẫn cần
authority/quyền, identity/Offering 2025, scale/basis và admission scope/tie-break review.
Không tạo command giả; mọi apply/publish/release sau này cần ủy quyền riêng theo hash.
T08/T09/T11 và Phase 1 chưa hoàn tất.
