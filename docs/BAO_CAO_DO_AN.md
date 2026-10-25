---
title: "EduRadar — Phân tích mạng Trường – Ngành trong tuyển sinh đại học Việt Nam 2024–2026"
subtitle: "Báo cáo đồ án môn Phân tích mạng xã hội"
lang: vi
---

**Sinh viên thực hiện:** [Họ tên — MSSV] · **Lớp:** [ ] · **Giảng viên:** [ ] · **Ngày nộp:** [ ]

Mã nguồn: nhánh `v2-simple` của repository `tiennguyen2406/Tuyensinhdaihoc`. Mọi số liệu trong
báo cáo được sinh lại được bằng các lệnh ở Phụ lục B.

# 1. Giới thiệu chủ đề và lý do chọn

Mỗi năm, thí sinh Việt Nam chọn nguyện vọng trong khoảng 300 trường đại học, gần 500 mã ngành và
khoảng 10 phương thức xét tuyển. Thông tin điểm chuẩn đã công khai, nhưng nằm rời rạc theo từng
trường, nên khó trả lời các câu hỏi mang tính *quan hệ*:

- Trường nào có danh mục ngành giống trường nào? Hệ thống đại học chia thành những nhóm nào?
- Ngành nào thường đi cùng ngành nào? Thí sinh thích ngành A thì có thể cân nhắc ngành nào?
- Ở cùng một ngành, trường nào cạnh tranh trực tiếp với trường nào về điểm chuẩn, và trường nào
  là "đích đến" của thí sinh điểm cao?

Đây là những câu hỏi tự nhiên của phân tích mạng: độ tương đồng, cộng đồng, trung tâm, cạnh tranh
có hướng và dự đoán liên kết. Đề tài được chọn vì ba lý do:
1. Dữ liệu thật, công khai, đủ lớn: 71.009 mức điểm chuẩn của 292 trường trong 3 năm.
2. Cấu trúc tự nhiên là **mạng hai phía Trường – Ngành**, cho phép áp dụng đầy đủ các kỹ thuật
   của môn học: phép chiếu, độ đo trung tâm, phát hiện cộng đồng, HITS, PageRank và dự đoán liên
   kết.
3. Kết quả dùng được ngay qua một ứng dụng web tra cứu và tư vấn chọn ngành.

Đồ án gồm 4 phần nối tiếp nhau: thu thập → làm sạch → phân tích mạng → web. Kiến trúc được giữ cố
định và đơn giản: `crawler/` → `data/raw/` → `pipeline/` → SQLite → `sna/` và `webapp/`.

# 2. Thu thập và làm sạch dữ liệu

## 2.1. Nguồn và cách thu thập

| Mục | Giá trị |
| --- | --- |
| Nguồn | diemthi.tuyensinh247.com, trang tổng hợp điểm chuẩn công khai |
| API | `GET /api/school/search` (1 request: 587 trường, giữ 307 trường đại học) và `GET /api/common/cutoff-score?school_id=…&year=…` (JSON) |
| Phạm vi | 307 trường đại học × 3 năm (2024, 2025, 2026) = **921 request** |
| Thời gian | 1 đợt, 23/10/2026 13:51:00 → 14:20:33 (**29 phút 33 giây**); nghỉ 1,5 s + ngẫu nhiên 0–0,5 s, trung vị 2,0 s/request |
| Kết quả | **76.726 dòng thô**; 88 trang rỗng (28 / 29 / 31 theo năm); **0 lỗi** |
| Lưu trữ | JSON nguyên văn từng trường × năm, kèm thời điểm tải và `source_url`; nhật ký `fetch_log.csv` |

15 trường không có dữ liệu ở cả 3 năm, nên bảng sạch còn 292 trường. Crawler chỉ dùng thư viện
chuẩn Python, bỏ qua file đã tải (chạy lại được khi bị ngắt), và thử lại tối đa 3 lần khi lỗi
mạng.

## 2.2. Các bước làm sạch

| # | Bước | Cách làm | Ảnh hưởng | Còn lại |
| ---: | --- | --- | ---: | ---: |
| 1 | Đọc dữ liệu thô | gộp 921 file JSON | — | 76.726 |
| 2 | Điểm | ép kiểu số; bỏ dòng không có điểm hoặc điểm ≤ 0 | −69 | 76.657 |
| 3 | Văn bản | chuẩn Unicode NFC; bỏ ký tự lỗi (74 tên); bỏ tiền tố "(1)…" (273 tên); bỏ dấu cách trong mã (655 mã) | 0 dòng bị bỏ | 76.657 |
| 4 | Phương thức | `mark_type` → 10 mã chuẩn (THPT, HOCBA, DGNL_HCM, DGNL_HN, DGTD, DGNL_SPT, KETHOP, CCQT, UTXT, KHAC); `mark_type` 13–17 chưa rõ nghĩa → KHAC | 3.192 dòng xếp vào KHAC | 76.657 |
| 5 | Tổ hợp | tách mã dạng `[A-Z]\d{2}` từ cột `block` | 54.452 dòng thô có tổ hợp | 76.657 |
| 6 | Gộp điểm gốc + quy đổi | nguồn trả 2 dòng khi có điểm quy đổi; gộp thành 1 dòng (`score_equiv`). `is_converted_score = 1` là điểm gốc, mọi giá trị khác coi là quy đổi | −4.961 | 71.696 |
| 7 | Thang điểm và cờ | thang mặc định theo phương thức; nếu điểm vượt thang hoặc phương thức không có thang thì suy ra thang nhỏ nhất trong {30, 40, 100, 150, 1200, 1600} chứa được điểm. Cờ `thang_khac_30` (1.113), `diem_thap_bat_thuong` (3), `outlier` (2) | 1.118 dòng có cờ | 71.696 |
| 8 | Trùng lặp | bỏ trùng hoàn toàn; trùng khoá nhưng khác điểm thì giữ cả hai (631 dòng, ghi ra `conflicts.csv`) | −687 | **71.009** |
| 9 | Loại chương trình | nhận diện từ tên và mã: CHUAN 62.616, TIENG_ANH 3.111, LIEN_KET 1.510, TIEN_TIEN 1.290, CLC 1.287, PHAN_HIEU 1.079, TAI_NANG 116 | — | 71.009 |
| 10 | Mã ngành chuẩn | xem mục 2.4 | 69.274 dòng có mã | 71.009 |

Kết quả: **71.009 dòng sạch** (2024: 18.590; 2025: 24.232; 2026: 28.187), 292 trường, 472 mã
ngành, 337 tổ hợp, 4.940 dòng có điểm quy đổi. Dữ liệu được lưu thành CSV và SQLite
(`admissions`, `universities`, `majors`, `admission_combos`).

Trong khi viết báo cáo, nhóm phát hiện 3 dòng (SP2, 2026) có `is_converted_score = 26` bị bỏ âm
thầm ở bước 6. Lỗi đã được sửa, và giờ các bước cộng trừ khớp: 76.726 − 69 − 4.961 − 687 = 71.009.

Số dòng theo năm × phương thức:

| Phương thức | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: |
| THPT — điểm thi THPT | 5.988 | 7.908 | 6.763 |
| HOCBA — học bạ | 5.539 | 5.227 | 4.518 |
| DGNL_HCM — ĐGNL ĐHQG-HCM | 2.422 | 2.672 | 3.000 |
| DGNL_HN — ĐGNL ĐHQG-HN (HSA) | 1.035 | 1.594 | 2.008 |
| DGTD — Đánh giá tư duy (TSA) | 712 | 1.021 | 1.306 |
| DGNL_SPT — ĐGNL ĐHSP HN | 231 | 803 | 903 |
| KETHOP — xét tuyển kết hợp | 1.124 | 1.887 | 7.053 |
| CCQT — chứng chỉ quốc tế | 512 | 984 | 700 |
| UTXT — ưu tiên / xét thẳng | 670 | 655 | 284 |
| KHAC — khác | 357 | 1.481 | 1.652 |

## 2.3. Định nghĩa một record

Một dòng của bảng `admissions` là **một mức điểm chuẩn** của **một chương trình đào tạo** tại
**một trường**, trong **một năm**, theo **một phương thức xét tuyển**, với **một nhóm tổ hợp** như
nguồn công bố. Khoá xác định một record là `(uni_code, year, method, sub_method, program_code,
program_name, combos, note)`.

Mỗi dòng mang điểm (`score`), thang điểm (`scale_max`), điểm quy đổi (`score_equiv`), mã ngành
chuẩn 7 chữ số (`major_code`), loại chương trình, cờ chất lượng, cách gán mã (`match_how`) và
`source_url`.

## 2.4. Chuẩn hoá mã ngành

Mạng G1–G3 lấy *ngành* làm đỉnh, nên mỗi chương trình (VD "Kế toán (song bằng 3+1) – liên kết
ĐH West of England") phải được quy về một mã ngành chuẩn 7 chữ số. Danh mục ngành được dựng từ
chính dữ liệu: mỗi mã 7 chữ số được gắn với tên phổ biến nhất của nó. Mỗi dòng thử các cách sau
theo thứ tự, dừng ở cách đầu tiên khớp:

| # | Cách | Quy tắc | Số dòng | Tỉ lệ | Ví dụ thật |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `ma_7_so` | mã chương trình bắt đầu bằng 7 chữ số | 56.417 | 79,45% | DVL `7210404` Thiết kế thời trang → 7210404 |
| 2 | `thu_cong` | có trong `data/manual/major_map.csv` (201 tên đã duyệt tay; 9 tên đánh dấu bỏ map, 55 dòng) | 2.055 | 2,89% | HHA `D110` Xây dựng công trình thủy → 7580202 |
| 3 | `ten_khop` | tên đã chuẩn hoá trùng khớp; nếu một tên ứng với nhiều mã thì chọn mã phổ biến nhất | 9.425 | 13,27% | GSA "Logistics và Quản lý chuỗi cung ứng (CLC…)" → 7510605 |
| 4 | `dau_ten_chuan` | tên bắt đầu bằng tên ngành chuẩn dài ≥ 2 từ | 1.181 | 1,66% | KHA "Thống kê và Trí tuệ kinh doanh" → 7460201 Thống kê |
| 5 | `ten_gan_dung` | độ giống chuỗi ≥ 0,9 | 83 | 0,12% | HHA "Logistics & chuỗi cung ứng" → 7510605 |
| 6 | `chua_ten_chuan` | tên chứa cụm tên chuẩn chiếm ≥ 60% số từ | 113 | 0,16% | BKA "CNTT: Khoa học Máy tính" → 7480101 |
| — | chưa map | không khớp cách nào (175 tên, tính cả 55 dòng bỏ map) | 1.735 | 2,44% | BKA "Kỹ thuật sinh học (CT tiên tiến)" |
| | **Có mã ngành** | | **69.274** | **97,56%** | |

## 2.5. Kiểm tra độ chính xác

Lấy ngẫu nhiên 20 dòng (seed 42, 2 dòng cho mỗi phương thức trong 10 phương thức, đủ 3 năm) và
đối chiếu tay với trang nguồn về trường, năm, phương thức, chương trình và điểm. Danh sách 20 dòng
ở Phụ lục C.

**Kết quả: __/20 dòng đúng.**

Phép kiểm tra này đo khâu thu thập và chuẩn hoá điểm. Việc gán mã ngành bằng các cách 3–6 (15,2%
số dòng) chưa được đo riêng.

# 3. Mô hình mạng và các độ đo

Mạng chỉ dùng các dòng đã có mã ngành: 18.280 dòng (2024), 23.654 (2025), 27.340 (2026). Toàn bộ
được sinh bởi `python -m sna.build` (NetworkX 3.7).

## 3.1. Bốn mạng

| Mạng | Đỉnh | Cạnh | Trọng số | Câu hỏi trả lời |
| --- | --- | --- | --- | --- |
| **G1** Trường – Ngành (hai phía) | trường $U$, ngành $M$ | trường $u$ có tuyển ngành $m$ trong năm | số dòng điểm chuẩn | Ngành nào phổ biến, trường nào đa ngành |
| **G2** Trường – Trường | trường | hai trường có tập ngành giống nhau, $J \ge 0{,}25$ | hệ số Jaccard $J$ | Nhóm trường cùng "kiểu đào tạo", trường cầu nối |
| **G3** Ngành – Ngành | ngành | hai ngành thường được cùng các trường mở, $J \ge 0{,}25$ | hệ số Jaccard $J$ | Cụm ngành, ngành tương tự |
| **G4** Cạnh tranh (có hướng) | trường | $A \to B$ nếu cùng ngành và điểm THPT của $B$ cao hơn $A$ trong khoảng $(0;\,2]$ | số ngành có quan hệ đó | Trường nào "nhắm lên" trường nào |

G2 và G3 là hai **phép chiếu một phía** của G1. Gọi $N(x)$ là tập hàng xóm của $x$ trong G1; hai
đỉnh cùng phía được nối khi

$$J(a,b) = \frac{|N(a) \cap N(b)|}{|N(a) \cup N(b)|} \ge 0{,}25.$$

Jaccard được dùng thay vì đếm số hàng xóm chung, để các ngành đại trà (Quản trị kinh doanh có ở
157 trường) không nối với mọi thứ. G4 dùng điểm THPT thang 30 cao nhất của mỗi cặp (ngành, trường).
Đây là mạng có hướng duy nhất, nên là nơi áp dụng HITS. Cách chọn ngưỡng 0,25 và khoảng 2 điểm
được phân tích ở mục 4.4.

```
         G1 (hai phía)                      G2: J(BKA, QSB) = |{CNTT, Cơ khí}| / |{CNTT, Cơ khí, Luật}|
  BKA ──┬── CNTT ──┐                                       = 2/3 ≥ 0,25   →  BKA ── QSB
        └── Cơ khí ┤                        G3: J(CNTT, Cơ khí) = |{BKA, QSB}| / |{BKA, QSB}| = 1
  QSB ─────────────┘                                                      →  CNTT ── Cơ khí
      └──── Luật                            (sơ đồ minh hoạ cách tính, không phải dữ liệu thật)
```

## 3.2. Các độ đo

Ký hiệu: $n$ đỉnh, $m$ cạnh, $k_v$ là bậc, $d(u,v)$ là khoảng cách ngắn nhất. Đường đi,
betweenness, closeness và clustering tính không trọng số; eigenvector, PageRank, HITS và
modularity có trọng số.

| Độ đo | Công thức | Cách tính trong `sna/build.py` | Ý nghĩa với đề tài |
| --- | --- | --- | --- |
| Phân bố bậc | $P(k) = n_k/n$ | `degree()`, histogram + log–log | Ngành đại trà và ngành đặc thù |
| Mật độ | $D = \frac{2m}{n(n-1)}$; hai phía: $\frac{m}{\lvert U\rvert\lvert M\rvert}$ | `nx.density`, `bipartite.density` | Mức chồng lấn giữa các trường |
| Độ dài đường đi TB | $L = \frac{1}{n(n-1)}\sum_{u\ne v} d(u,v)$ | `average_shortest_path_length` trên LCC | Số bước "giống nhau" giữa hai trường hoặc hai ngành |
| Đường kính | $\max_{u,v} d(u,v)$ | `nx.diameter` trên LCC | Hai đỉnh "khác nhau nhất" |
| Clustering | $C_v = \frac{2T_v}{k_v(k_v-1)}$; transitivity $= \frac{3\cdot\#\triangle}{\#\text{bộ ba}}$ | `clustering`, `transitivity` | Nhóm trường hoặc ngành có khép kín không |
| Betweenness | $C_B(v)=\sum_{s\ne v\ne t}\frac{\sigma_{st}(v)}{\sigma_{st}}$ (chuẩn hoá) | `betweenness_centrality` | Trường hoặc ngành cầu nối giữa các nhóm |
| Closeness | $C_C(v)=\frac{r-1}{n-1}\cdot\frac{r-1}{\sum_u d(v,u)}$ | `closeness_centrality` (Wasserman–Faust) | Gần mọi đỉnh khác |
| Eigenvector | $x_v=\frac{1}{\lambda}\sum_u A_{uv}x_u$ | `eigenvector_centrality_numpy`, trên LCC | Nối với đỉnh quan trọng |
| PageRank | $PR(v)=\frac{1-\alpha}{n}+\alpha\sum_{u\to v}\frac{w_{uv}}{s_u}PR(u)$, $\alpha=0{,}85$ | `nx.pagerank` | G4: điểm đến của dòng thí sinh "nhắm lên" |
| HITS | $\mathbf a = A^\top\mathbf h,\ \mathbf h = A\mathbf a$ | `nx.hits` trên G4 | Authority: được nhắm tới; hub: nhắm lên nhiều trường |
| Modularity | $Q=\frac{1}{2m}\sum_{ij}\big(A_{ij}-\frac{k_ik_j}{2m}\big)\delta(c_i,c_j)$ | Louvain, `seed=42` | Mức tách cộng đồng |

## 3.3. Số liệu toàn mạng

| Mạng | Độ đo | 2024 | 2025 | 2026 |
| --- | --- | ---: | ---: | ---: |
| **G1** | số trường / số ngành / số cạnh | 279 / 428 / 4.447 | 278 / 434 / 4.680 | 276 / 429 / 5.058 |
| | mật độ hai phía | 0,0372 | 0,0388 | 0,0427 |
| | số ngành TB mỗi trường / số trường TB mỗi ngành | 15,94 / 10,39 | 16,83 / 10,78 | 18,33 / 11,79 |
| **G2** | số đỉnh / số cạnh / mật độ | 251 / 2.566 / 0,082 | 250 / 2.455 / 0,079 | 249 / 2.531 / 0,082 |
| | thành phần / đỉnh trong LCC | 12 / 219 | 9 / 229 | 8 / 231 |
| | đường đi TB / đường kính (LCC) | 2,77 / 8 | 3,40 / 13 | 3,25 / 12 |
| | clustering TB / transitivity / assortativity | 0,553 / 0,529 / 0,376 | 0,554 / 0,550 / 0,425 | 0,549 / 0,544 / 0,393 |
| | số cộng đồng Louvain / modularity | 19 / 0,451 | 19 / 0,494 | 20 / 0,482 |
| **G3** | số đỉnh / số cạnh / mật độ | 387 / 1.360 / 0,018 | 387 / 1.431 / 0,019 | 377 / 1.412 / 0,020 |
| | thành phần / đỉnh trong LCC | 13 / 358 | 12 / 361 | 7 / 364 |
| | đường đi TB / đường kính (LCC) | 5,72 / 17 | 5,62 / 14 | 5,66 / 14 |
| | clustering TB / transitivity / assortativity | 0,529 / 0,642 / 0,612 | 0,570 / 0,663 / 0,594 | 0,518 / 0,665 / 0,653 |
| | số cộng đồng Louvain / modularity | 28 / 0,839 | 27 / 0,846 | 19 / 0,836 |
| **G4** | số đỉnh / số cạnh / mật độ | 259 / 10.541 / 0,158 | 260 / 10.789 / 0,160 | 226 / 9.215 / 0,181 |
| | thành phần liên thông mạnh / tính tương hỗ | 17 / 0,342 | 13 / 0,345 | 35 / 0,338 |

Nhận xét chính:
- **G1 có phân bố bậc đuôi dài.** Năm 2026, trung vị chỉ 4 trường/ngành nhưng Quản trị kinh doanh
  có ở 157 trường; 26% ngành chỉ một trường mở; 10% ngành phổ biến nhất chiếm 49,2% số cạnh.
- **G2 là mạng thế giới nhỏ.** Đường đi TB khoảng 3 bước; clustering khoảng 0,55, gấp nhiều lần
  mật độ 0,08 (mức clustering kỳ vọng của đồ thị ngẫu nhiên cùng mật độ).
- **G3 thưa nhưng cụm rất rõ:** transitivity 0,66, modularity khoảng 0,84.
- **Assortativity dương ở cả G2 và G3:** trường đa ngành nối với trường đa ngành, ngành đại trà nối
  với ngành đại trà.
- **G4 năm 2026 ít đỉnh hơn (226)** chủ yếu do chỉ 238 trường có điểm THPT trong dữ liệu năm đó
  (so với 279 năm 2024), không phải thay đổi thật.

## 3.4. Đỉnh trung tâm (năm 2026)

"ĐH" là viết tắt của "(Trường) Đại học", "HV" của "Học viện". Bảng đầy đủ cho cả 3 năm nằm trong
`data/network/metrics/`.

**G1:**
- **Trường mở nhiều ngành nhất:** ĐH Cần Thơ (97), ĐH Phenikaa (66), ĐH Văn Lang (64), ĐH Vinh
  (64), ĐH Duy Tân (62).
- **Ngành có mặt ở nhiều trường nhất:** Quản trị kinh doanh (157), Công nghệ thông tin (154), Kế
  toán (137), Ngôn ngữ Anh (136), Tài chính – Ngân hàng (114).
- **Betweenness phía trường:** ĐH Mỏ – Địa chất đứng thứ 2 (0,0425) dù ít ngành hơn, vì trường độc
  quyền nhiều ngành địa chất – mỏ.

**G2 Trường – Trường:**

| # | Bậc | Betweenness | PageRank |
| ---: | --- | --- | --- |
| 1 | ĐH Ngoại Ngữ Tin Học TPHCM (DNT) — 72 | ĐH Võ Trường Toản (VTT) — 0,0946 | ĐH Ngoại Ngữ Tin Học TPHCM (DNT) — 0,0103 |
| 2 | ĐH Kinh Tế TPHCM – PH Vĩnh Long (KSV) — 70 | ĐH Hải Phòng (THP) — 0,0686 | ĐH Kinh Tế TPHCM – PH Vĩnh Long (KSV) — 0,0096 |
| 3 | ĐH Công Nghệ và Quản Lý Hữu Nghị (DCQ) — 67 | ĐH Quốc Tế Hồng Bàng (HIU) — 0,0618 | ĐH Ngân Hàng TPHCM (NHS) — 0,0095 |
| 4 | ĐH Hùng Vương TPHCM (DHV) — 66 | ĐH Hà Tĩnh (HHT) — 0,0539 | ĐH Công Nghệ và Quản Lý Hữu Nghị (DCQ) — 0,0091 |
| 5 | ĐH Kinh Tế Kỹ Thuật Bình Dương (DKB) — 66 | ĐH Kiến Trúc Đà Nẵng (KTD) — 0,0478 | ĐH Kinh Tế Kỹ Thuật Bình Dương (DKB) — 0,0090 |
| 6 | ĐH Ngân Hàng TPHCM (NHS) — 66 | ĐH Kiến Trúc Hà Nội (KTA) — 0,0440 | ĐH Hùng Vương TPHCM (DHV) — 0,0089 |
| 7 | ĐH Bà Rịa – Vũng Tàu (BVU) — 65 | ĐH Nghệ An (CEA) — 0,0428 | ĐH Lạc Hồng (DLH) — 0,0088 |
| 8 | ĐH Lạc Hồng (DLH) — 65 | ĐH Công nghiệp Vinh (DCV) — 0,0408 | ĐH Bà Rịa – Vũng Tàu (BVU) — 0,0087 |
| 9 | ĐH Đại Nam (DDN) — 64 | ĐH Thông tin Liên lạc – hệ dân sự (TCU) — 0,0384 | ĐH Đại Nam (DDN) — 0,0087 |
| 10 | HV Ngân Hàng (NHH) — 60 | ĐH Luật TPHCM (LPS) — 0,0373 | HV Ngân Hàng (NHH) — 0,0085 |

Bậc, PageRank, closeness và eigenvector cùng chỉ ra một nhóm: các trường tư và trường kinh tế đa
ngành phía Nam, nằm ở lõi dày đặc của G2. Betweenness thì chỉ ra các trường có danh mục ngành trải
trên nhiều khối, nên nối các cộng đồng với nhau.

**G3 Ngành – Ngành:**

| # | Bậc | Betweenness | PageRank |
| ---: | --- | --- | --- |
| 1 | Sư phạm Địa lý — 25 | Sinh học — 0,1624 | Tài chính – Ngân hàng — 0,0054 |
| 2 | Logistics và quản lý chuỗi cung ứng — 23 | Kỹ thuật vật liệu — 0,0780 | Logistics và quản lý chuỗi cung ứng — 0,0052 |
| 3 | Giáo dục Chính trị — 23 | Địa lý học — 0,0775 | Sư phạm Địa lý — 0,0050 |
| 4 | Tài chính – Ngân hàng — 22 | Khoa học đất — 0,0746 | Toán kinh tế — 0,0050 |
| 5 | Quản trị khách sạn — 22 | Vật lý y khoa — 0,0689 | Kế toán — 0,0050 |
| 6 | Giáo dục Công dân — 22 | Hán Nôm — 0,0664 | Ngôn ngữ Anh — 0,0047 |
| 7 | Truyền thông đa phương tiện — 21 | Kỹ thuật xây dựng — 0,0660 | Quản trị kinh doanh — 0,0047 |
| 8 | Sư phạm Lịch sử – Địa lý — 21 | Ngôn ngữ Đức — 0,0649 | Quản trị khách sạn — 0,0046 |
| 9 | Kỹ thuật trắc địa – bản đồ — 21 | Ngôn ngữ Pháp — 0,0602 | Công nghệ thông tin — 0,0046 |
| 10 | Công nghệ thông tin — 20 | Hải dương học — 0,0596 | Sư phạm Ngữ văn — 0,0046 |

- **Bậc G3 khác "phổ biến" ở G1:** bậc G3 cao nghĩa là ngành có tập trường giống tập trường của
  nhiều ngành khác, ví dụ các ngành sư phạm cùng được các trường sư phạm mở.
- **Eigenvector là hiệu ứng cấu trúc:** 10 ngành đứng đầu cùng giá trị 0,2965 là đúng 10 ngành
  *chỉ* ĐH Mỏ – Địa chất mở. Với nhau chúng có Jaccard = 1, tạo thành một clique đầy đủ chiếm véc-tơ
  riêng chính, nên giá trị này không đo "tầm quan trọng".

**G4 Cạnh tranh:**

| # | Authority | Hub | PageRank |
| ---: | --- | --- | --- |
| 1 | ĐH Kiến Trúc Đà Nẵng (KTD) — 0,0336 | ĐH Vinh (TDV) — 0,0141 | ĐH Cần Thơ (TCT) — 0,0243 |
| 2 | ĐH Công Đoàn (LDA) — 0,0252 | ĐH Công Nghệ TPHCM (DKC) — 0,0140 | ĐH Kinh Tế Quốc Dân (KHA) — 0,0212 |
| 3 | ĐH Sư Phạm Kỹ Thuật Hưng Yên (SKH) — 0,0236 | ĐH Đồng Tháp (SPD) — 0,0140 | ĐH Nha Trang (TSN) — 0,0165 |
| 4 | ĐH Công Nghiệp Việt – Hung (VHD) — 0,0227 | ĐH Nguyễn Tất Thành (NTT) — 0,0138 | ĐH Mở TPHCM (MBS) — 0,0160 |
| 5 | ĐH Nghệ An (CEA) — 0,0209 | ĐH Đông Á (DAD) — 0,0137 | ĐH Sài Gòn (SGD) — 0,0158 |
| 6 | ĐH Hồng Đức (HDT) — 0,0199 | ĐH Nam Cần Thơ (DNC) — 0,0132 | ĐH Sư Phạm Hà Nội (SPH) — 0,0155 |
| 7 | ĐH Vinh (TDV) — 0,0192 | ĐH Duy Tân (DDT) — 0,0132 | ĐH Phenikaa (PKA) — 0,0139 |
| 8 | ĐH Nông Lâm Thái Nguyên (DTN) — 0,0188 | ĐH Quy Nhơn (DQN) — 0,0131 | ĐH Bách Khoa Hà Nội (BKA) — 0,0137 |
| 9 | ĐH Cần Thơ (TCT) — 0,0180 | ĐH Văn Lang (DVL) — 0,0128 | ĐH Giao Thông Vận Tải (GHA) — 0,0137 |
| 10 | ĐH Quy Nhơn (DQN) — 0,0179 | ĐH Văn Hiến (DVH) — 0,0124 | ĐH Thủ Đô Hà Nội (HNM) — 0,0133 |

Năm 2024, top 5 PageRank của G4 là ĐH Y Dược TPHCM, ĐH Y Hà Nội, ĐH Tôn Đức Thắng, ĐH Ngoại
thương, ĐH Sư phạm Hà Nội, tức đúng nhóm "đích đến" của thí sinh điểm cao.

## 3.5. Cộng đồng Louvain (năm 2026)

| Mạng | Cộng đồng | Số đỉnh | Đỉnh tiêu biểu | Khối |
| --- | ---: | ---: | --- | --- |
| G2 | 0 | 59 | DNT, DCQ, DHV, DKB, BVU, DLH | trường tư đa ngành, chủ yếu phía Nam |
| G2 | 1 | 33 | ĐH Hải Phòng, Hà Tĩnh, Hùng Vương, Hải Dương, Quảng Bình, Tây Bắc | đại học địa phương |
| G2 | 2 | 31 | KSV, ĐH Ngân Hàng TPHCM, HV Ngân Hàng, ĐH Thương Mại, ĐH Tài Chính Ngân Hàng HN | kinh tế – tài chính – ngân hàng |
| G2 | 3 | 25 | Công Nghiệp Việt Trì, Kinh tế công nghệ Thái Nguyên, Kinh Tế Kỹ Thuật Công Nghiệp | công nghiệp – kỹ thuật |
| G2 | 4 | 24 | Y Dược ĐHQGHN, Y Dược Huế, Khoa học sức khỏe TPHCM, Y khoa Phạm Ngọc Thạch | y dược (163 cạnh nội bộ, chỉ 12 cạnh ra ngoài) |
| G3 | 0 | 50 | Công nghệ chế biến thủy sản, Phát triển nông thôn, Lâm nghiệp | nông – lâm – thủy sản |
| G3 | 1 | 48 | Logistics, Tài chính – Ngân hàng, Quản trị khách sạn, CNTT, Ngôn ngữ Anh | kinh tế – dịch vụ – CNTT |
| G3 | 2 | 38 | Quản lý thông tin, Hán Nôm, Ngôn ngữ Đức, Lưu trữ học, Nhân học | khoa học xã hội – nhân văn |
| G3 | 3 | 34 | Sinh học, Vật lý y khoa, Hải dương học, Toán tin | khoa học tự nhiên |
| G3 | 4 | 33 | Sư phạm Địa lý, Giáo dục Chính trị, Giáo dục Công dân, Sư phạm Ngữ văn | sư phạm (219 cạnh nội bộ, 18 cạnh ra ngoài) |

## 3.6. Thay đổi 2024 → 2026

- **Các trường mở rộng ngành:** G1 tăng từ 4.447 lên 5.058 cạnh (+13,7%); số ngành TB mỗi trường từ
  15,94 lên 18,33.
- **Ngành "nóng" lan nhanh** (số trường có tuyển, 2024 → 2026): Trí tuệ nhân tạo 22 → 47, Marketing
  56 → 77, Công nghệ tài chính 26 → 45, Khoa học dữ liệu 27 → 46, Ngôn ngữ Trung Quốc 64 → 80, Tâm lý
  học 29 → 43. Trong G3, bậc của Trí tuệ nhân tạo tăng từ 3 lên 20: ngành này đã nhập vào cụm
  kinh tế – CNTT.
- **Cấu trúc:** modularity G2 tăng (0,451 → 0,482) và transitivity G3 tăng (0,642 → 0,665). Ở
  ngưỡng 0,25, G2 liên kết hơn (thành phần 12 → 8) và G3 gộp cụm (28 → 19 cộng đồng). Hai nhận định
  sau nhạy với ngưỡng (mục 4.4).

# 4. Thuật toán và phân tích độ nhạy

## 4.1. Louvain so với Girvan–Newman

Louvain chạy trên toàn mạng. Girvan–Newman ($O(m^2n)$) chỉ chạy được trên đồ thị con gồm 60 đỉnh
bậc cao nhất, với 10 lần tách đầu tiên. Louvain được chạy lại trên cùng đồ thị con đó để so sánh
($Q$ đều tính có trọng số).

| Mạng | Năm | Louvain toàn mạng: số cộng đồng / $Q$ | Mẫu 60 đỉnh — GN: $Q$ (số cộng đồng) / thời gian | Mẫu 60 đỉnh — Louvain: $Q$ / thời gian |
| --- | --- | --- | --- | --- |
| G2 | 2024 | 19 / 0,451 | 0,0109 (9) / 6,63 s | 0,1451 / 0,015 s |
| G2 | 2026 | 20 / 0,482 | 0,0019 (11) / 6,36 s | 0,1503 / 0,011 s |
| G3 | 2024 | 28 / 0,839 | 0,6384 (7) / 0,37 s | 0,6384 / < 0,001 s |
| G3 | 2026 | 19 / 0,836 | 0,6598 (6) / 0,62 s | 0,6662 / 0,019 s |

- **Trên G3** (mẫu thưa, cụm rõ), hai thuật toán cho $Q$ gần như bằng nhau, nhưng Louvain nhanh hơn
  từ khoảng 30 lần trở lên.
- **Trên G2**, 60 trường bậc cao nhất gần như là một clique. Girvan–Newman chỉ bóc được vài đỉnh lẻ
  nên $Q \approx 0$; Louvain vẫn đạt $Q \approx 0{,}15$ và nhanh hơn 450–600 lần.

## 4.2. HITS và PageRank trên G4

| Năm | Spearman(authority, điểm THPT TB của trường) | Spearman(PageRank, điểm TB) |
| --- | ---: | ---: |
| 2024 | −0,401 | 0,567 |
| 2025 | −0,414 | 0,535 |
| 2026 | 0,234 | 0,607 |

PageRank tương quan dương ổn định với điểm chuẩn, vì "dòng nhắm lên" lan theo chuỗi và dồn về
trường điểm cao. Authority thì âm trong 2024–2025. Nhóm trường theo điểm TB cho thấy cơ chế:

| Nhóm điểm TB | 2024: số trường / authority TB | 2026: số trường / authority TB |
| --- | ---: | ---: |
| ≤ 17 | 71 / 0,0065 | 69 / 0,0031 |
| 17–19 | 35 / 0,0084 | 28 / 0,0077 |
| 19–21 | 39 / 0,0032 | 50 / 0,0065 |
| 21–23 | 34 / 0,0017 | 38 / 0,0036 |
| 23–25 | 41 / 0,0007 | 26 / 0,0030 |
| > 25 | 39 / 0,0008 | 15 / 0,0019 |

1. **Cạnh dồn về vùng điểm thấp.** Năm 2024, 1.389 trong 4.287 cặp (ngành, trường) có điểm ≤ 16,
   riêng mức 15 điểm có 885 cặp. Quan hệ "cao hơn trong vòng 2 điểm" dày đặc nhất ở dải 15–19 điểm.
2. **HITS khuếch đại lõi dày nhất.** Authority là véc-tơ riêng chính của $A^\top A$ nên tập trung vào
   khối trường điểm thấp – trung bình nhiều ngành (Spearman với in-strength 0,82; với số ngành 0,59;
   hub với điểm −0,77). Vì vậy $\rho < 0$.
3. **Năm 2026 đảo dấu**, do hai thay đổi:
   - Số cặp đúng 15 điểm tăng lên 1.431 trên 4.455. Trường ở đúng điểm sàn gần như không nhận được
     cạnh vào, nên đỉnh authority dịch lên nhóm 17–21.
   - Nhóm > 25 điểm chỉ còn 15 trường.

**Kết luận:** authority của G4 đo "mức bị cạnh tranh trực tiếp", không phải uy tín. PageRank mới
phù hợp để xếp hạng uy tín.

## 4.3. Adamic–Adar: gợi ý ngành tương tự

$$AA(x,y) = \sum_{z \in N(x)\cap N(y)} \frac{1}{\log |N(z)|}.$$

Chỉ số này được tính trên mọi cặp ngành chưa nối của G3; 300 cặp điểm cao nhất được lưu lại. Top 10
năm 2026:
1. Văn học – Giáo dục Chính trị (5,08)
2. Sư phạm Tiếng Anh – Giáo dục Công dân (5,04)
3. Kinh doanh quốc tế – Quản trị dịch vụ du lịch và lữ hành (5,00)
4. Việt Nam học – Tâm lý học giáo dục (4,84)
5. Văn học – Tâm lý học giáo dục (4,74)
6. Việt Nam học – Giáo dục Mầm non (4,70)
7. Việt Nam học – Giáo dục Thể chất (4,70)
8. Kế toán – Truyền thông đa phương tiện (4,69)
9. Công nghệ tài chính – Công nghệ thông tin (4,69)
10. Kỹ thuật Dầu khí – Kỹ thuật trắc địa – bản đồ (4,44)

Các cặp này là ngành *thường được cùng loại trường mở* (cụm sư phạm, cụm kinh tế – dịch vụ), chưa
chắc giống nhau về nội dung đào tạo.

**Kiểm chứng theo thời gian:** lấy 300 cặp dự đoán từ dữ liệu 2024, có **69 cặp (23,0%)** đã thực
sự thành cạnh của G3 năm 2026. Trong khi đó, chỉ 294 trong 56.090 cặp chưa nối (0,52%) thành cạnh,
nên Adamic–Adar tốt hơn chọn ngẫu nhiên khoảng **44 lần**.

## 4.4. Phân tích độ nhạy tham số

Toàn bộ `sna.build` được chạy lại với ngưỡng Jaccard ∈ {0,15; 0,20; 0,25; 0,30; 0,35} và khoảng
điểm G4 ∈ {1; 2; 3}, ghi ra thư mục riêng (`--out`). Cấu hình chuẩn trùng khớp với kết quả ở
mục 3.

**Theo ngưỡng Jaccard (2026):**

| Ngưỡng | G2: cạnh / thành phần / LCC% / L / Q / số cộng đồng | G3: cạnh / thành phần / LCC% / L / Q / số cộng đồng |
| --- | --- | --- |
| 0,15 | 7.453 / 5 / 95,4% / 2,20 / 0,260 / 11 | 3.461 / 3 / 99,0% / 3,29 / 0,685 / 14 |
| 0,20 | 4.437 / 6 / 94,6% / 2,63 / 0,360 / 11 | 2.164 / 4 / 98,2% / 4,03 / 0,773 / 15 |
| **0,25** | **2.531 / 8 / 92,8% / 3,25 / 0,482 / 20** | **1.412 / 7 / 96,6% / 5,66 / 0,836 / 19** |
| 0,30 | 1.326 / 15 / 83,5% / 3,66 / 0,614 / 23 | 917 / 21 / 63,8% / 12,87 / 0,880 / 33 |
| 0,35 | 717 / 24 / 64,7% / 3,94 / 0,702 / 30 | 589 / 52 / 8,4% / 1,72 / 0,899 / 52 |

**Theo khoảng điểm G4:**

| Khoảng | Số cạnh 2026 | Spearman(PageRank) 2024 / 2026 | Spearman(authority) 2024 / 2026 |
| --- | ---: | --- | --- |
| 1 điểm | 6.098 | 0,450 / 0,527 | −0,384 / 0,233 |
| **2 điểm** | **9.215** | **0,567 / 0,607** | **−0,401 / 0,234** |
| 3 điểm | 11.492 | 0,634 / 0,664 | −0,309 / 0,248 |

**Độ ổn định cộng đồng.** Độ ổn định được đo bằng ARI và NMI trên các đỉnh chung, so với mức dao
động khi chỉ đổi seed Louvain:
- Đổi ngưỡng: ARI 0,41–0,68, NMI ≥ 0,72.
- Đổi seed ở ngưỡng 0,25: ARI TB 0,81 (G2) và 0,92 (G3).

Như vậy đổi ngưỡng làm phân hoạch tách nhỏ hoặc gộp lại nhiều hơn dao động ngẫu nhiên, nhưng giữ
các khối lớn: 10/10 trường y dược mẫu luôn cùng một cộng đồng ở mọi ngưỡng.

**Lý do chọn tham số:**
- **Jaccard 0,25** là ngưỡng lớn nhất mà cả G2 và G3 vẫn giữ trên 90% số đỉnh trong LCC. Ngay sau
  đó G3 có bước chuyển kiểu thẩm thấu (LCC 63,8% ở 0,30 rồi 8,4% ở 0,35). Ở 0,15, G2 quá dày (mật
  độ 0,22, $Q$ chỉ 0,26).
- **Khoảng 2 điểm:** 76–80% chương trình có điểm chuẩn thay đổi không quá 2 điểm giữa hai năm liền
  kề (trung vị khoảng 1 điểm). Hai trường cách nhau trong khoảng đó thực sự cạnh tranh cùng một
  nhóm thí sinh.

**Kết luận đứng vững và kết luận nhạy:**

| Kết luận | Đánh giá qua các ngưỡng |
| --- | --- |
| Đuôi dài ở G1; ngành "nóng" 2024 → 2026 | Vững (G1 không phụ thuộc ngưỡng) |
| G2 thế giới nhỏ (C/mật độ 3,0–14,2; L 2,2–3,9) | Vững về định tính |
| G3 có cụm lĩnh vực rõ ($Q$ 0,69–0,90); cụm y dược của G2 luôn tách riêng | Vững |
| Eigenvector bị một clique chi phối | Vững về bản chất (clique MDA ở 0,15–0,25; clique sư phạm ở 0,35) |
| PageRank G4 dương với điểm chuẩn; authority âm 2024, dương 2026 | Vững ở cả 3 khoảng điểm |
| Adamic–Adar tốt hơn ngẫu nhiên | Vững (gấp 29 / 44 / 58 lần ở 0,15 / 0,25 / 0,35) |
| Modularity G2 và transitivity G3 tăng 2024 → 2026 | Vững về chiều thay đổi |
| Top betweenness G2, G3 ("Sinh học là cầu nối số 1") | **Nhạy**: Sinh học đứng thứ 1 / 24 / 78 ở 0,25 / 0,15 / 0,35 |
| Số cộng đồng chính xác | **Nhạy**: G2 11–30, G3 14–52 |
| "G2 liên kết hơn", "G3 hội tụ" 2024 → 2026 | **Nhạy**: đảo chiều ở 0,35 |

Các bảng đầy đủ ở `docs/do_nhay_sna.md`.

# 5. Trực quan hoá

Hình phân bố bậc được sinh bởi `sna/build.py`, hình mạng tĩnh bởi `sna/draw.py` (matplotlib).
Mỗi hình phân bố bậc gồm histogram (trái) và $P(k)$ trên trục log–log (phải).

![Hình 1. Phân bố bậc G1 năm 2026 (cả hai phía).](fig/g1_degree_2026.png)

Hình 1: $P(k)$ trên trục log–log giảm gần tuyến tính, tức phân bố đuôi dài. Từ 2024 sang 2026, số
ngành chỉ một trường mở giảm từ 140 (33%) xuống 113 (26%).

![Hình 2a. G1 phía trường: bậc = số ngành trường mở (2026).](fig/g1_uni_degree_2026.png)

![Hình 2b. G1 phía ngành: bậc = số trường mở ngành (2026).](fig/g1_major_degree_2026.png)

Hình 2 cho thấy hai phía của cùng một mạng có hình dạng rất khác nhau.
- **Phía trường:** trung vị 15 ngành/trường. 61 trường mở ≤ 5 ngành, chủ yếu là trường quân đội –
  công an, thể dục thể thao, luật, y dược. 13 trường mở ≥ 50 ngành; ĐH Cần Thơ (97) tách xa trường
  đứng sau (66).
- **Phía ngành:** đuôi dài, trung vị 4, lớn nhất 157.
- **Hệ quả:** G2 (chiếu lên trường) dày hơn G3 nhiều, vì hai trường bất kỳ dễ có chung các ngành
  đại trà.

![Hình 3. Phân bố bậc G2 Trường – Trường năm 2026.](fig/g2_uni_uni_degree_2026.png)

![Hình 4. Phân bố bậc G3 Ngành – Ngành năm 2026.](fig/g3_major_major_degree_2026.png)

Hình 3–4: G2 và G3 không có đuôi lũy thừa rõ, chỉ lệch phải vừa phải (độ lệch khoảng 1,0). Trung
vị là 18 (G2) và 6 (G3). Ngưỡng Jaccard cắt bỏ các quan hệ của ngành đại trà.

![Hình 5a. Bậc vào G4 năm 2026.](fig/g4_in_degree_2026.png)

![Hình 5b. Bậc ra G4 năm 2026.](fig/g4_out_degree_2026.png)

Hình 5: hai phân bố cùng giá trị trung bình 40,8 nhưng khác hình dạng.
- **Bậc vào:** 29 trường có bậc vào 0 và 54 trường ≤ 4. Trung vị điểm của nhóm này là 15,64, so với
  19,74 toàn mạng: đó là các trường ở điểm sàn, không ai "nhắm lên" họ.
- **Bậc ra:** một đỉnh quanh 40–60. 27 trường có bậc ra ≤ 10, trung vị điểm 23,0 (trường top).

![Hình 6. Mạng G2 năm 2026 (thành phần lớn nhất): màu là cộng đồng Louvain, kích thước theo bậc.](fig/g2_uni_uni_net_2026.png)

Hình 6: cấu trúc lõi – ngoại vi.
- 15 trường bậc cao nhất dồn vào một lõi, thuộc cộng đồng 0 (10 trường) và 2 (5 trường).
- Đại học địa phương (cộng đồng 1) bám sát lõi.
- Cụm y dược (cộng đồng 4) tách hẳn sang một bên.

![Hình 7. Mạng G3 năm 2026 (thành phần lớn nhất).](fig/g3_major_major_net_2026.png)

Hình 7: các cụm lĩnh vực tách rõ.
- 10/15 nhãn thuộc cụm kinh tế – CNTT, 4 nhãn thuộc cụm sư phạm nằm sát cạnh.
- Ở ngoại vi là các cụm nông – lâm – thủy sản, khoa học xã hội, kỹ thuật, nghệ thuật – điện ảnh,
  mỏ – địa chất.

**Gephi.** Mọi mạng được xuất thành `data/network/gexf/<mạng>_<năm>.gexf`, kèm đầy đủ thuộc tính
độ đo (degree, betweenness, PageRank, community…) để mở bằng Gephi.

> **[Chèn hình Gephi tại đây: lưu ảnh xuất từ Gephi vào `docs/fig/` và thêm dòng `![Hình 8. …](fig/<tên>.png)`.]**

Ngoài ra, ứng dụng web có tab mạng tương tác (mục 6).

# 6. Ứng dụng web

## 6.1. Kiến trúc

```
crawler/fetch.py ──► data/raw/ (JSON) ──► pipeline/clean.py ──► data/eduradar.db (SQLite)
                                                                   │
                                     sna/build.py ◄────────────────┤
                                          │                        │
                              data/network/*.json ──► webapp/main.py (FastAPI) ──► static/ (HTML + JS)
```

- **Backend** (`webapp/main.py`): FastAPI, mở SQLite ở chế độ chỉ đọc (`mode=ro&immutable=1`).
  Web không bao giờ crawl hay sửa dữ liệu.
- **Frontend** (`webapp/static/`): HTML, CSS và JavaScript thuần, không cần build. Mạng tương tác
  dùng thư viện vis-network.
- **API chính:**

| Endpoint | Chức năng |
| --- | --- |
| `GET /api/meta` | năm, phương thức, tổ hợp, thống kê tổng |
| `GET /api/universities?q=` | tìm trường (bỏ dấu, theo tên, tên viết tắt hoặc mã) |
| `GET /api/universities/{mã}/scores?year=` | bảng điểm một trường, mỗi phương thức một cột, kèm học phí |
| `GET /api/majors?q=` | tìm ngành chuẩn và cả tên chương trình gốc chưa map |
| `GET /api/majors/{mã}/scores`, `GET /api/programs/scores` | điểm theo ngành hoặc theo tên chương trình gốc |
| `GET /api/majors/{mã}/similar` | ngành tương tự (hàng xóm Jaccard cao nhất trong G3) |
| `GET /api/advice?method=&score=&combo=` | tư vấn theo điểm |
| `GET /api/network`, `GET /api/network/{mạng}?year=` | dữ liệu mạng cho tab SNA |

## 6.2. Bốn chức năng

Mọi bảng đều có nút **Xuất CSV**. Trên màn hình hẹp (≤ 640px), mỗi dòng bảng chuyển thành một thẻ.

1. **Tra cứu theo trường:** gõ tên hoặc mã trường, chọn năm. Bảng hiện mọi chương trình, mỗi
   phương thức xét tuyển một cột, kèm tổ hợp, ghi chú và điểm quy đổi.

![Hình 9. Tab "Theo trường": ĐH Bách Khoa Hà Nội, 83 chương trình năm 2026.](fig/web_uni.png)

2. **Tra cứu theo ngành:** gõ tên ngành, hoặc tên chương trình gốc chưa được map. Bảng hiện mọi
   trường đào tạo ngành đó theo phương thức, cùng các chip "ngành tương tự" lấy từ G3.

![Hình 10. Tab "Theo ngành": Công nghệ thông tin, 140 trường, điểm THPT 2026.](fig/web_major.png)

3. **Tư vấn theo điểm:** nhập phương thức, tổ hợp và điểm. Hệ thống phân loại kết quả thành *Thử
   sức* (cao hơn tối đa 1 điểm), *Vừa sức* (thấp hơn dưới 1 điểm) và *An toàn*.
   - Mốc 1 điểm tính trên thang 30, quy đổi theo thang của phương thức (ĐGNL HCM: 40 điểm).
   - Mỗi mức lấy các dòng sát điểm nhất, và hiện xu hướng điểm của chương trình qua 3 năm.

![Hình 11. Tab "Tư vấn theo điểm": THPT 24 điểm, tổ hợp A00; 3.078 lựa chọn (221 thử sức, 217 vừa sức, 2.640 an toàn).](fig/web_advice.png)

4. **Mạng SNA:** chọn mạng G1–G4 và năm. Đồ thị tương tác tô màu theo cộng đồng Louvain; bảng bên
   cạnh hiện số liệu toàn mạng và top 10 theo từng độ đo, có thể xuất CSV.

![Hình 12. Tab "Mạng SNA": G2 Trường – Trường năm 2026.](fig/web_network.png)

## 6.3. Hướng dẫn chạy

```powershell
# trong thư mục dự án, Windows PowerShell
.venv\Scripts\python.exe -m pip install pandas networkx matplotlib scipy fastapi uvicorn
.venv\Scripts\python.exe -m crawler.fetch        # ~30 phút, chạy lại được
.venv\Scripts\python.exe -m pipeline.clean       # -> data/eduradar.db
.venv\Scripts\python.exe -m sna.build            # -> data/network/
.venv\Scripts\python.exe -m sna.draw             # hình mạng tĩnh
.venv\Scripts\python.exe -m uvicorn webapp.main:app --reload   # http://127.0.0.1:8000
```

# 7. Kết luận, hạn chế và hướng phát triển

## 7.1. Kết luận

1. **Tuyển sinh đại học có cấu trúc lõi – ngoại vi rõ rệt.** Một nhóm nhỏ ngành đại trà (Quản trị
   kinh doanh, CNTT, Kế toán, Ngôn ngữ Anh, Tài chính – Ngân hàng) có mặt ở 114–157 trường. Phần lớn
   ngành còn lại là đặc thù của vài trường.
2. **Mạng trường là thế giới nhỏ có cộng đồng ý nghĩa.** Các cộng đồng là: trường tư đa ngành; đại
   học địa phương; khối kinh tế – tài chính; khối kỹ thuật; khối y dược (khép kín nhất). Mạng ngành
   tách thành các cụm lĩnh vực rõ ($Q \approx 0{,}84$). Các kết luận này đứng vững qua mọi ngưỡng.
3. **Để đo uy tín, PageRank trên mạng cạnh tranh phù hợp hơn HITS authority.** PageRank tương quan
   dương 0,45–0,66 với điểm chuẩn ở mọi cấu hình. Authority đo mức bị cạnh tranh trực tiếp và có thể
   âm.
4. **Xu hướng 2024 → 2026:** các trường mở rộng ngành (+13,7% cạnh G1), dồn vào Trí tuệ nhân tạo,
   Công nghệ tài chính, Khoa học dữ liệu, Marketing.
5. **Dự đoán liên kết có giá trị thực tế:** Adamic–Adar dự đoán cặp ngành sẽ gắn với nhau tốt hơn
   ngẫu nhiên 29–58 lần. Đây là cơ sở cho chức năng gợi ý ngành.

## 7.2. Hạn chế

1. **Chuẩn hoá mã ngành:** 2,44% dòng chưa map bị loại khỏi mạng. Danh mục ngành dựng từ dữ liệu
   nên còn mã không chuẩn và tên trùng (VD 7310120/7340120 "Kinh doanh quốc tế").
2. **Thang điểm suy ra từ giá trị khi nguồn không ghi rõ.** Ví dụ dòng 11 và 15 của mẫu kiểm tra:
   31 điểm học bạ bị suy ra thang 40; 225 điểm phương thức "Khác" bị suy ra thang 1200, nhiều khả
   năng là thang 300. 1.242 dòng "Khác" có cùng rủi ro.
3. **G4 chỉ dùng điểm THPT, lấy điểm cao nhất mỗi cặp trường–ngành**, bỏ qua tổ hợp và chương trình.
   Độ phủ 2026 thấp hơn (238 so với 279 trường).
4. **Kết luận ở mức từng đỉnh nhạy với tham số:** top betweenness, số cộng đồng (mục 4.4). Đường đi,
   betweenness và closeness tính không trọng số.
5. **Girvan–Newman chỉ chạy trên mẫu 60 đỉnh.**
6. **Nguồn dữ liệu là trang tổng hợp**, ảnh chụp ngày 23/10/2026, không phải thông báo chính thức
   của từng trường.

## 7.3. Hướng phát triển

1. Dùng *backbone extraction* (disparity filter) thay cho ngưỡng Jaccard cứng; dùng độ dài cạnh
   $1 - J$ để tính độ đo đường đi có trọng số.
2. Xây mạng nhiều lớp (mỗi phương thức một lớp) và mạng theo thời gian, theo dõi cộng đồng động.
3. Đánh giá dự đoán liên kết đầy đủ (AUC, precision@k), so sánh với Resource Allocation và
   Preferential Attachment; đưa gợi ý Adamic–Adar vào web.
4. Đối chiếu dữ liệu với đề án tuyển sinh chính thức của trường; chuẩn hoá mã ngành theo danh mục
   của Bộ GD&ĐT.

# Phụ lục A. Cấu trúc thư mục

| Đường dẫn | Nội dung |
| --- | --- |
| `crawler/fetch.py` | Thu thập từ API công khai (danh sách trường, điểm chuẩn theo trường × năm) |
| `pipeline/clean.py` | Làm sạch, chuẩn hoá, gán mã ngành; xuất CSV, SQLite, báo cáo chất lượng |
| `sna/build.py` | Dựng G1–G4, tính độ đo, Louvain, Girvan–Newman, HITS, PageRank, Adamic–Adar; xuất JSON, GEXF, CSV, PNG (`--out` để chạy thử tham số) |
| `sna/draw.py` | Hình mạng tĩnh G2, G3 cho báo cáo |
| `webapp/main.py`, `webapp/static/` | Backend FastAPI và giao diện web |
| `data/raw/` | JSON gốc và nhật ký thu thập (không đưa lên git) |
| `data/clean/`, `data/eduradar.db` | Dữ liệu sạch (không đưa lên git; sinh lại bằng `pipeline.clean`) |
| `data/manual/` | Sửa tay: `major_map.csv` (tên chương trình → mã ngành), `tuition.csv` (học phí) |
| `data/network/` | Kết quả SNA: `metrics/`, `gexf/`, `fig/`, `summary.csv` (sinh lại bằng `sna.build`) |
| `docs/` | Báo cáo: `BAO_CAO_DO_AN.md` (bản này), `bao_cao_lam_sach.md`, `bao_cao_sna.md`, `do_nhay_sna.md`, `kiem_tra_20_dong.md`, hình trong `fig/` |

# Phụ lục B. Nguồn dữ liệu và tái lập

- **Nguồn:** diemthi.tuyensinh247.com, dữ liệu điểm chuẩn công khai, thu thập ngày 23/10/2026 qua
  API JSON của trang. Trang web và mỗi bản ghi đều ghi nguồn (`source_url`). Dữ liệu chỉ dùng cho
  mục đích học tập, phi thương mại; luôn đối chiếu thông báo chính thức của trường.
- **Thu thập lịch sự:** nghỉ ≥ 1,5 giây giữa các request, không crawl khi mở web.
- **Tái lập:** chạy các lệnh ở mục 6.3. Phân tích độ nhạy:
  `python -m sna.build --years 2024 2026 --jaccard 0.15 --gap 2 --out <thư mục tạm>`.
- **Báo cáo chi tiết:** `docs/bao_cao_lam_sach.md` (làm sạch), `docs/bao_cao_sna.md` (phân tích
  mạng), `docs/do_nhay_sna.md` (độ nhạy).

# Phụ lục C. Mẫu kiểm tra 20 dòng

Seed 42, 2 dòng cho mỗi phương thức. Cột "Đúng/Sai" do người kiểm điền sau khi đối chiếu trang
nguồn. URL xem `docs/kiem_tra_20_dong.md`.

| # | Trường | Năm | Phương thức | Mã CT | Ngành / chương trình | Điểm / thang | Đúng/Sai |
| ---: | --- | ---: | --- | --- | --- | ---: | :---: |
| 1 | ĐH Tôn Đức Thắng (DTT) | 2025 | Chứng chỉ quốc tế | K7340301 | Kế toán (song bằng 3+1) – liên kết ĐH West of England | 983 / 1200 | |
| 2 | ĐH Công Nghệ Thông Tin – ĐHQG TPHCM (QSC) | 2025 | Chứng chỉ quốc tế | 7340122 | Thương mại điện tử | 1340 / 1600 | |
| 3 | ĐH Bách Khoa Đà Nẵng (DDK) | 2024 | ĐGNL ĐHQG-HCM | 7520122 | Kỹ thuật Tàu thủy | 659 / 1200 | |
| 4 | HV Hàng không Việt Nam (HHK) | 2025 | ĐGNL ĐHQG-HCM | 7840102E | Quản lý hoạt động bay (học bằng Tiếng Anh)… | 921,25 / 1200 | |
| 5 | ĐH Duy Tân (DDT) | 2024 | ĐGNL ĐHQG-HN (HSA) | 7310206 | Quan hệ quốc tế | 85 / 150 | |
| 6 | ĐH Hà Tĩnh (HHT) | 2025 | ĐGNL ĐHQG-HN (HSA) | 7340101_01 | Quản trị kinh doanh | 50 / 150 | |
| 7 | ĐH Thăng Long (DTL) | 2025 | ĐGNL ĐHSP HN (SPT) | 7480207 | Trí tuệ nhân tạo | 16 / 30 | |
| 8 | ĐH Hồng Đức (HDT) | 2025 | ĐGNL ĐHSP HN (SPT) | 7310401 | Tâm lý học | 11 / 30 | |
| 9 | HV Công Nghệ Bưu Chính Viễn Thông – TP.HCM (BVS) | 2025 | Đánh giá tư duy (TSA) | 7320104 | Truyền thông đa phương tiện | 66,52 / 100 | |
| 10 | ĐH Thương Mại (TMU) | 2025 | Đánh giá tư duy (TSA) | TM32 | Hệ thống thông tin quản lý (IPOP) | 65,48 / 100 | |
| 11 | ĐH Ngoại thương – Cơ sở II (NTS) | 2024 | Học bạ | KDQS2.1 | ĐHNNQT Logistics và Quản lý chuỗi cung ứng | 31 / 40 | |
| 12 | ĐH Kinh Tế Tài Chính TPHCM (UEF) | 2025 | Học bạ | 7220210 | Ngôn ngữ Hàn Quốc | 18 / 30 | |
| 13 | ĐH Giao Thông Vận Tải – Cơ sở 2 (GSA) | 2026 | Xét tuyển kết hợp (10.01) | GSA02 | Quản trị kinh doanh | 24,47 / 30 | |
| 14 | ĐH Hàng Hải Việt Nam (HHA) | 2025 | Xét tuyển kết hợp | D106 | Máy tàu thủy | 20,67 / 30 | |
| 15 | ĐH Duy Tân (DDT) | 2026 | Khác | 7510205_11 | Công nghệ Kỹ thuật Ô tô – Chương trình CTBT | 225 / 1200 | |
| 16 | ĐH Tiền Giang (TTG) | 2025 | Khác | 7340301 | Kế toán | 15 / 30 | |
| 17 | ĐH Cửu Long (DCL) | 2025 | Điểm thi THPT | 7540101 | Công nghệ thực phẩm | 15 / 30 | |
| 18 | ĐH CNTT và Truyền thông Việt – Hàn (VKU) | 2024 | Điểm thi THPT | 7480201DT | Công nghệ thông tin (cử nhân - Hựp tác doanh nghiệp) | 22 / 30 | |
| 19 | HV Công Nghệ Bưu Chính Viễn Thông – TP.HCM (BVS) | 2025 | Ưu tiên / xét tuyển thẳng | 7329001 | Công nghệ đa phương tiện | 42,5 / 100 | |
| 20 | ĐH Tôn Đức Thắng (DTT) | 2024 | Ưu tiên / xét tuyển thẳng | FA7310630Q | Việt Nam học (Du lịch và Quản lý du lịch) – CT đại học bằng tiếng Anh | 28 / 30 | |

Tổ hợp của từng dòng cũng nằm trong `docs/kiem_tra_20_dong.md`.
