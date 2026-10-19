# Bước tiếp theo đề xuất — T09 đa nguồn và nhu cầu T11

Đây là đề xuất sau lát cắt T10 SQL/year-status, chưa là approval nguồn/fact hoặc lệnh crawl.
DEV vẫn3/20.000; release3 bất biến. Không chuyển thẳng sang T12.

1. Chọn2–3 trường bổ sung từ inventory12, ưu tiên nguồn chính thức có bảng cutoff rõ
   năm/phương thức/campus và có thể đối chiếu độc lập. HUST/DUT/UIT là candidates để
   review, chưa có robots/storage/authority approval được suy từ PTIT. Chỉ chốt danh sách
   sau khi xem trạng thái thật của profile và quyền dùng; không mặc định mọi URL indexed
   là đủ căn cứ ingest/publication.
2. Tạo pilot có budget riêng, mục tiêu đề xuất150–300facts trên3–5trường, năm tách biệt.
   Tái sử dụng raw immutable storage, parser locators, normalization Decimal/year/scope,
   registry/aliases có thời hạn, resolution packets, publisher và refresh/release hiện có.
   Không nhân source_aggregate thành tổ hợp; ambiguity giữ review, không tự publish.
3. T11 cần hàng chờ review tối thiểu: source/snapshot/locator, University–Program–Offering
   candidates, method/year/scale/basis/scope/conditions, diff/fingerprint và blocker reason.
   Tách reviewer/publisher/operator, hiển thị exact command/hash/version và optimistic
   revision guard; mọi apply có audit. Khởi đầu tận dụng CLI/runbook, sau đó admin UI
   chỉ phục vụ thao tác đã có contract. Production OIDC/RBAC vẫn cần gate riêng.
4. Mỗi batch duyệt xác minh tay theo counting policy, kiểm namespace/idempotency/replay,
   aliases gần tên và thời hạn, no crossyear, fan-out evidence và điều kiện tie TTNV.
   Trạng thái admission-year chỉ cập nhật qua review nghiệp vụ riêng; vài facts verified
   không nâng partial→verified và không chứng minh coverage đầy đủ.
5. Sau publication thật, builder đọc snapshot/version mới thực tế, verify counts/artifacts/
   registration/refresh bằng non-superuser rồi bàn giao release pilot mới. Không sửa v3,
   không tái dựng lịch sử từ is_current, không cộng observations/evidence/synthetic vàoquota.

Gate trước T12/T13: có nguồn chính thức cho từng method/year/exam version, scale/basis,
quy tắc công thức/ưu tiên/làm tròn/conditions và phạm vi tương thích hoặc quy đổi; có
reviewer nghiệp vụ, golden cases và trace expectations. Hiện aggregate facts vẫn
unavailable_aggregate_scope; chưa có căn cứ biến chúng thành evaluator/tư vấn trúng tuyển.

Song song T19: kiểm tài nguyên PostgreSQL/shared memory, giới hạn số DB test giữ lại và
phương án archive/backup được chủ dự án chấp thuận, thử restore vào DB mới, rồi đo lại
load/SLO trên môi trường cô lập. Không tự xóa lịch sử để giảm chi phí vận hành.
