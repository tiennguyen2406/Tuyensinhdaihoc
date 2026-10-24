# Học phí bổ sung 89 trường — các mục cần xử lý tay

Nguồn: `data/manual/hoc_phi_bo_sung_89_truong_20261024.md`, nhập bằng `python -m pipeline.tuition_import`
(danh sách đầy đủ: `data/interim/tuition_extra_review.csv`).

## 32 mục không tách tự động được

Web hiện câu mức học phí nguyên văn từ nguồn (không đoán khoảng, không quy đổi). Muốn hiện gọn hơn thì viết lại câu đầu mục **Mức học phí** trong file Markdown theo dạng `A – B đồng/<đơn vị>` hoặc `Ngành X 1.000.000 đồng/tín chỉ; Ngành Y …`, rồi chạy lại importer.

| Mã | Lý do |
|---|---|
| DHL | không tìm thấy số tiền có đơn vị; không tách được bảng theo ngành (bỏ bảng) |
| DNC | chỉ có một số ngành nhưng không tách được tên ngành |
| DNH | có 1 số tiền không ghi đơn vị trong câu (VD 8.550.000); không tách được bảng theo ngành (bỏ bảng) |
| DQU | có 3 số tiền không ghi đơn vị trong câu (VD 1.790.000) |
| DSD | nhiều đơn vị (thang, nam) |
| DTE | có 5 số tiền không ghi đơn vị trong câu (VD 8.950.000); không tách được bảng theo ngành (bỏ bảng) |
| DTK | nhiều đơn vị (thang, tin_chi) |
| DVB | nhiều đơn vị (toan_khoa, tin_chi) |
| DVP | nhiều đơn vị (toan_khoa, hoc_ky, tin_chi) |
| GNT | có 3 số tiền không ghi đơn vị trong câu (VD 1.410.000); không tách được bảng theo ngành (bỏ bảng) |
| HHA | có 1 số tiền không ghi đơn vị trong câu (VD 942.000) |
| HLU | có 2 số tiền không ghi đơn vị trong câu (VD 1.500.000); không tách được bảng theo ngành (bỏ bảng) |
| HVC | có 1 số tiền không ghi đơn vị trong câu (VD 38.506.645); không tách được bảng theo ngành (bỏ bảng) |
| KCC | có 2 số tiền không ghi đơn vị trong câu (VD 7.020.000) |
| KTA | nhiều đơn vị (tin_chi, nam) |
| LNH | có 4 số tiền không ghi đơn vị trong câu (VD 436.000); không tách được bảng theo ngành (bỏ bảng) |
| MDA | có 3 số tiền không ghi đơn vị trong câu (VD 526.400); không tách được bảng theo ngành (bỏ bảng) |
| MTC | nhiều đơn vị (thang, hoc_ky) |
| MTS | nhiều đơn vị (nam, hoc_ky); không tách được bảng theo ngành (bỏ bảng) |
| NHB | nhiều đơn vị (tin_chi, nam) |
| NLS | có 3 số tiền không ghi đơn vị trong câu (VD 638.000); không tách được bảng theo ngành (bỏ bảng) |
| NTS | có khoảng số không ghi đơn vị (VD 34–39) |
| NTT | không tìm thấy số tiền có đơn vị; không tách được bảng theo ngành (bỏ bảng) |
| NTU | có 1 số tiền không ghi đơn vị trong câu (VD 1.000.000); không tách được bảng theo ngành (bỏ bảng) |
| QSP | không tìm thấy số tiền có đơn vị; không tách được bảng theo ngành (bỏ bảng) |
| SIU | không tìm thấy số tiền có đơn vị; không tách được bảng theo ngành (bỏ bảng) |
| SKH | có 2 số tiền không ghi đơn vị trong câu (VD 2.500.000); không tách được bảng theo ngành (bỏ bảng) |
| TDB | nhiều đơn vị (tin_chi, nam) |
| TDV | có 7 số tiền không ghi đơn vị trong câu (VD 568.000); không tách được bảng theo ngành (bỏ bảng) |
| TQU | nhiều đơn vị (tin_chi, thang) |
| TTD | nhiều đơn vị (thang, tin_chi) |
| UFA | nhiều đơn vị (thang, tin_chi) |

## 13 mục chỉ bỏ bảng theo ngành

Dòng tóm tắt tách được chắc chắn; phần liệt kê theo ngành không tách sạch nên không hiện bảng: DHC, DHV, DMT, DQT, DTD, DTP, DVD, SPH, THP, THV, UKB, UTH, VUI.

## 7 trường chưa xác minh được số tiền

Thẻ ghi “Chưa có mức học phí được xác minh” và link thông báo của trường: DBH, DKT, DNB, HFH, NHP, NLG, SDU.
