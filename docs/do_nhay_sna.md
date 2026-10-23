# Phân tích độ nhạy tham số mạng SNA

Phụ lục của [`bao_cao_sna.md`](bao_cao_sna.md). Báo cáo chính dùng hai tham số chọn tay:
- ngưỡng Jaccard $J \ge 0{,}25$ cho G2 (Trường – Trường) và G3 (Ngành – Ngành);
- khoảng điểm $0 < s_B - s_A \le 2$ cho G4 (mạng cạnh tranh).

Tài liệu này đo xem các số liệu và kết luận thay đổi thế nào khi đổi hai tham số đó.

## 1. Thiết lập

- **Cấu hình chạy.** Mỗi lần chỉ đổi một tham số, tham số kia giữ mức chuẩn:
  - Jaccard ∈ {0,15; 0,25; 0,35}, khoảng điểm = 2;
  - khoảng điểm ∈ {1; 2; 3}, Jaccard = 0,25.
  - Thêm hai ngưỡng 0,20 và 0,30 (chỉ năm 2026) để khoanh vùng điểm chuyển của thành phần liên
    thông lớn nhất (LCC).
- **Năm.** 2026 là năm phân tích chính. Năm 2024 được chạy kèm để kiểm hai kết luận cần hai mốc
  thời gian: dấu của Spearman(authority) và kiểm chứng Adamic–Adar 2024 → 2026.
- **Cách chạy.**
  `python -m sna.build --years 2024 2026 --jaccard 0.15 --gap 2 --out <thư mục tạm>`.
  Tham số `--out` mới được thêm vào `sna/build.py` để không ghi đè `data/network/`. Cấu hình chuẩn
  (0,25; 2) cho kết quả **trùng khớp** với `data/network/summary.csv`, nên mọi khác biệt dưới đây
  là do tham số.
- **Độ ổn định cộng đồng** đo bằng Adjusted Rand Index và Normalized Mutual Information giữa hai
  phân hoạch Louvain, tính trên các đỉnh có mặt ở cả hai mạng:

  $$\mathrm{ARI} = \frac{\sum_{ij}\binom{n_{ij}}{2} - \Big[\sum_i \binom{a_i}{2}\sum_j \binom{b_j}{2}\Big]/\binom{n}{2}}{\tfrac12\Big[\sum_i \binom{a_i}{2} + \sum_j \binom{b_j}{2}\Big] - \Big[\sum_i \binom{a_i}{2}\sum_j \binom{b_j}{2}\Big]/\binom{n}{2}}, \qquad \mathrm{NMI} = \frac{2\,I(X;Y)}{H(X) + H(Y)}.$$

  ARI = 1 nghĩa là hai phân hoạch trùng khít, ARI ≈ 0 nghĩa là giống nhau như ngẫu nhiên. Vì
  Louvain có yếu tố ngẫu nhiên, ARI giữa các ngưỡng được so với **mức dao động nội tại**: chạy lại
  Louvain 20 lần với seed khác nhau trên cùng mạng 0,25.

## 2. G2 và G3 theo ngưỡng Jaccard (năm 2026)

Cột in đậm là ngưỡng dùng trong báo cáo; 0,20 và 0,30 là hai ngưỡng bổ sung.

**G2 Trường – Trường**

| Độ đo | 0,15 | 0,20 | **0,25** | 0,30 | 0,35 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Số đỉnh | 261 | 258 | **249** | 237 | 218 |
| Số cạnh | 7.453 | 4.437 | **2.531** | 1.326 | 717 |
| Mật độ | 0,220 | 0,134 | **0,082** | 0,047 | 0,030 |
| Số thành phần | 5 | 6 | **8** | 15 | 24 |
| LCC (số đỉnh / %) | 249 / 95,4% | 244 / 94,6% | **231 / 92,8%** | 198 / 83,5% | 141 / 64,7% |
| Độ dài đường đi TB (LCC) | 2,20 | 2,63 | **3,25** | 3,66 | 3,94 |
| Clustering TB | 0,656 | 0,608 | **0,549** | 0,524 | 0,429 |
| Modularity Louvain | 0,260 | 0,360 | **0,482** | 0,614 | 0,702 |
| Số cộng đồng | 11 | 11 | **20** | 23 | 30 |

**G3 Ngành – Ngành**

| Độ đo | 0,15 | 0,20 | **0,25** | 0,30 | 0,35 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Số đỉnh | 406 | 399 | **377** | 337 | 275 |
| Số cạnh | 3.461 | 2.164 | **1.412** | 917 | 589 |
| Mật độ | 0,042 | 0,027 | **0,020** | 0,016 | 0,016 |
| Số thành phần | 3 | 4 | **7** | 21 | 52 |
| LCC (số đỉnh / %) | 402 / 99,0% | 392 / 98,2% | **364 / 96,6%** | 215 / 63,8% | 23 / 8,4% |
| Độ dài đường đi TB (LCC) | 3,29 | 4,03 | **5,66** | 12,87 | 1,72 |
| Clustering TB | 0,542 | 0,537 | **0,518** | 0,491 | 0,515 |
| Modularity Louvain | 0,685 | 0,773 | **0,836** | 0,880 | 0,899 |
| Số cộng đồng | 14 | 15 | **19** | 33 | 52 |

Ở G3 có một **bước chuyển kiểu thẩm thấu (percolation)** giữa 0,25 và 0,35:
- LCC giảm từ 96,6% (0,25) xuống 63,8% (0,30) rồi còn 8,4% (0,35);
- ngay trước khi vỡ (0,30), độ dài đường đi TB vọt lên 12,87 vì LCC chỉ còn nối với nhau qua vài
  "sợi" mảnh;
- ở 0,35, giá trị 1,72 không còn ý nghĩa, vì nó chỉ tính trên một cụm 23 ngành.

Năm 2024 cho cùng bức tranh:
- G2: Q = 0,242 / 0,451 / 0,672 và LCC = 251 / 219 / 163 đỉnh (ở 0,15 / 0,25 / 0,35);
- G3: Q = 0,720 / 0,839 / 0,912 và LCC = 394 / 358 / 28 đỉnh.

## 3. G4 theo khoảng điểm

| Độ đo | Năm | 1 điểm | **2 điểm** | 3 điểm |
| --- | --- | ---: | ---: | ---: |
| Số đỉnh | 2026 | 224 | **226** | 226 |
| Số cạnh | 2026 | 6.098 | **9.215** | 11.492 |
| Mật độ | 2026 | 0,122 | **0,181** | 0,226 |
| Số thành phần liên thông mạnh | 2026 | 50 | **35** | 23 |
| Spearman(PageRank, điểm TB) | 2026 | 0,527 | **0,607** | 0,664 |
| Spearman(authority, điểm TB) | 2026 | 0,233 | **0,234** | 0,248 |
| Số cạnh | 2024 | 7.107 | **10.541** | 12.731 |
| Spearman(PageRank, điểm TB) | 2024 | 0,450 | **0,567** | 0,634 |
| Spearman(authority, điểm TB) | 2024 | −0,384 | **−0,401** | −0,309 |

Top 10 PageRank năm 2026 có 6/10 trường trùng với mốc chuẩn khi khoảng điểm là 1, và 9/10 khi là 3.
Với top 10 authority, các con số tương ứng là 5/10 và 8/10.

## 4. Độ ổn định cộng đồng Louvain (năm 2026)

| So sánh | G2: ARI / NMI | G3: ARI / NMI |
| --- | --- | --- |
| 0,15 so với 0,25 (đỉnh chung: G2 249, G3 377) | 0,610 / 0,745 | 0,593 / 0,748 |
| 0,35 so với 0,25 (đỉnh chung: G2 218, G3 275) | 0,676 / 0,835 | 0,485 / 0,792 |
| 0,15 so với 0,35 | 0,504 / 0,715 | 0,408 / 0,748 |
| *Mức nền:* 20 seed Louvain so với seed 42, cùng ngưỡng 0,25 | TB 0,813 (thấp nhất 0,612) / TB 0,904 | TB 0,923 (thấp nhất 0,849) / TB 0,964 |

- **Mức độ thay đổi:** đổi ngưỡng làm phân hoạch thay đổi nhiều hơn đổi seed (ARI 0,49–0,68 so
  với mức nền 0,81–0,92), nhưng vẫn còn rất xa mức ngẫu nhiên (NMI ≥ 0,72 ở mọi cặp). Khung các
  khối lớn được giữ; khác biệt nằm ở việc các khối này **tách nhỏ hoặc gộp lại**: G2 có 11 cộng
  đồng ở 0,15 nhưng 30 ở 0,35.
- **Cụm y dược:** cụm này được giữ nguyên ở mọi ngưỡng. Lấy 10 trường y dược làm mẫu (QHY, YDN,
  DDY, DHY, QSY, TYS, YDS, YHB, YPB, DTY): cả 10 luôn rơi vào cùng một cộng đồng. Tỉ lệ cạnh từ
  cộng đồng đó ra ngoài là 24,1% (0,15), 6,9% (0,25) và 0% (0,35).

## 5. Vì sao chọn Jaccard 0,25 và khoảng 2 điểm

**Jaccard 0,25** là ngưỡng **lớn nhất** mà cả hai mạng chiếu vẫn giữ trên 90% số đỉnh trong
LCC (G2 92,8%, G3 96,6%).
- **Ngưỡng thấp hơn** (0,15–0,20): G2 gần như trở thành một khối.
  - Mật độ 0,13–0,22, bậc TB 57 ở 0,15, tức mỗi trường "giống" khoảng 1/5 số trường còn lại.
  - Modularity chỉ 0,26–0,36, cộng đồng mờ.
  - Các ngành đại trà kéo mọi trường lại gần nhau, nên mạng phản ánh "ai cũng mở Quản trị kinh
    doanh" hơn là phản ánh đặc thù của từng trường.
- **Ngưỡng cao hơn** (0,30–0,35): G3 vỡ vụn (LCC 63,8% rồi 8,4%), nên các độ đo dựa trên đường đi
  (closeness, betweenness, độ dài đường đi, đường kính) mất ý nghĩa.
- **Kết luận:** 0,25 nằm ngay trước bước chuyển thẩm thấu của G3. Đây là điểm cân bằng giữa giữ
  liên thông và giữ được cấu trúc cộng đồng (Q của G2 tăng từ 0,26 lên 0,48).

**Khoảng 2 điểm** khớp với mức dao động thực tế của điểm chuẩn. Với cùng một ngành tại cùng một
trường (điểm THPT cao nhất, như cách dựng G4), mức thay đổi tuyệt đối giữa hai năm liền kề:
- có trung vị khoảng 1 điểm (1,00 cho 2024 → 2025; 0,95 cho 2025 → 2026);
- **76–80%** không vượt quá 2 điểm (55–61% nếu lấy 1 điểm; 88–89% nếu lấy 3 điểm).

Như vậy hai trường cách nhau trong 2 điểm hoàn toàn có thể đổi chỗ vào năm sau, tức là đang thực
sự cạnh tranh cùng một nhóm thí sinh.
- **Khoảng 1 điểm** bỏ sót gần một nửa trường hợp đó, làm G4 rời rạc hơn (50 thành phần liên thông
  mạnh, so với 35).
- **Khoảng 3 điểm** bắt đầu nối các trường ở mức điểm khác hẳn nhau (mật độ 0,23).

## 6. Kết luận nào đứng vững, kết luận nào nhạy

| Kết luận trong báo cáo SNA | 0,15 | 0,25 | 0,35 | Đánh giá |
| --- | --- | --- | --- | --- |
| Mọi kết luận về G1 (đuôi dài, ngành đại trà, ngành "nóng" 2024 → 2026) | — | — | — | **Vững**: G1 không phụ thuộc ngưỡng |
| G2 là mạng thế giới nhỏ (đường đi ngắn, clustering ≫ mật độ) | L 2,20; C/mật độ 3,0 | L 3,25; C/mật độ 6,7 | L 3,94; C/mật độ 14,2 | **Vững** về định tính; độ lớn thay đổi |
| G3 có cụm lĩnh vực rất rõ (modularity cao) | Q 0,69 | Q 0,84 | Q 0,90 | **Vững** (Q ≥ 0,69); con số cụ thể nhạy |
| Cộng đồng G2 có ý nghĩa thực tế, cụm y dược tách riêng | 10/10 trường y cùng cụm | 10/10 | 10/10 | **Vững** |
| Số cộng đồng (G2 20, G3 19) | 11 / 14 | 20 / 19 | 30 / 52 | **Nhạy** |
| Top bậc / eigenvector / PageRank G2 là trường tư đa ngành phía Nam | trùng 5 / 8 / 7 trên 10 | — | trùng 6 / 8 / 7 trên 10 | **Khá vững** (eigenvector, PageRank); bậc nhạy hơn |
| Top betweenness G2 (Võ Trường Toản, Hải Phòng…) | trùng 4/10 | — | trùng 2/10 | **Nhạy** |
| Sinh học là cầu nối số 1 của G3 (betweenness) | hạng 24 | hạng 1 | hạng 78 | **Nhạy**: chỉ đúng ở 0,25 |
| Top bậc / PageRank G3 | trùng 3 / 4 trên 10 | — | trùng 3 / 1 trên 10 | **Nhạy** |
| Eigenvector G3 bị chi phối bởi một clique, không đo "tầm quan trọng" | clique 10 ngành MDA | clique 10 ngành MDA | clique các ngành sư phạm | **Vững** về bản chất; clique nào thì nhạy |
| G4: PageRank tương quan dương với điểm chuẩn | ρ 0,45–0,53 (khoảng 1) | 0,57–0,61 | 0,63–0,66 (khoảng 3) | **Vững** (cả 2024 và 2026, mọi khoảng điểm) |
| G4: authority âm năm 2024, dương năm 2026 | −0,38 / +0,23 (khoảng 1) | −0,40 / +0,23 | −0,31 / +0,25 (khoảng 3) | **Vững** theo khoảng điểm |
| Adamic–Adar dự đoán cạnh G3 tốt hơn ngẫu nhiên nhiều lần | 121/300 trúng, gấp 29 lần nền | 69/300, gấp 44 lần | 59/300, gấp 58 lần | **Vững**; tỉ lệ trúng tuyệt đối nhạy |
| 2024 → 2026: modularity G2 tăng, transitivity G3 tăng | tăng / tăng | tăng / tăng | tăng / tăng | **Vững** về chiều thay đổi |
| 2024 → 2026: G2 liên kết hơn (ít thành phần, LCC lớn hơn) | 5 → 5; LCC 251 → 249 | 12 → 8; 219 → 231 | 21 → 24; 163 → 141 | **Nhạy**: chỉ đúng ở 0,25 |
| 2024 → 2026: G3 hội tụ (ít thành phần, ít cộng đồng) | 5 → 3; 16 → 14 | 13 → 7; 28 → 19 | 43 → 52; 44 → 52 | **Nhạy**: đảo chiều ở 0,35 |

Ở bảng trên, "trùng k/10" là số phần tử chung giữa top 10 ở ngưỡng đó và top 10 ở ngưỡng 0,25.
Với G4, cột 0,15 / 0,35 được thay bằng khoảng điểm 1 / 3.

**Tóm lại:**
- **Đứng vững:** các kết luận về *cấu trúc vĩ mô*:
  - đuôi dài ở G1;
  - thế giới nhỏ ở G2;
  - cụm lĩnh vực rõ ở G3, trong đó cụm y dược tách riêng;
  - PageRank phản ánh điểm chuẩn tốt hơn authority;
  - dấu của Spearman(authority) theo năm;
  - Adamic–Adar có giá trị dự đoán;
  - chiều tăng của modularity G2 và transitivity G3.
- **Nhạy:** các kết luận ở *mức từng đỉnh* dựa trên đường đi (top betweenness, đặc biệt "Sinh học
  là cầu nối số 1"), số cộng đồng chính xác, và hai nhận định về mức liên thông của G2, G3 thay đổi
  từ 2024 sang 2026. Những kết luận này chỉ nên đọc như đặc điểm của mạng ở ngưỡng 0,25, không nên
  khái quát.

## 7. Tái lập

```powershell
# mỗi cấu hình ghi vào một thư mục riêng, không đụng data/network/
.venv\Scripts\python.exe -m sna.build --years 2024 2026 --jaccard 0.15 --gap 2 --out <tạm>\j015_g2
.venv\Scripts\python.exe -m sna.build --years 2024 2026 --jaccard 0.25 --gap 3 --out <tạm>\j025_g3
```

Các bảng ở trên lấy từ `summary.csv` và `metrics/*.csv` của từng thư mục. ARI và NMI được tính
trên cột `community` của `metrics/<mạng>_2026.csv`.
