# P9 chặng 5 — Lịch chờ duyệt (`pending`)

Kế hoạch tổng: [`2026-09-25-p9-cong-khach-hang.md`](2026-09-25-p9-cong-khach-hang.md), mục chặng 5 (5.1–5.3). Người dùng duyệt hướng đi ngày 02/10/2026 ("tiếp tục P9 đi").

## Quyết định thiết kế (và phản biện)

1. **`pending` nằm trong `appointments`**, không dựng bảng `booking_requests` riêng: lịch chờ duyệt phải **giữ chỗ** trong phép chống trùng và hiện trên lưới của lễ tân; hai bảng thì phải hợp hai nguồn ở mọi truy vấn trùng lịch.
2. **Cái giá mà kế hoạch tổng chưa tính:** ràng buộc `CHECK (status IN (...))` và `created_by NOT NULL` nằm trong định nghĩa bảng. `nang_cap_schema` chỉ `ADD COLUMN`, không sửa được ràng buộc → `petcare.db` dựng từ bản cũ sẽ **từ chối chèn `pending`**. Cần thêm một bước dựng lại bảng `appointments` (quy trình 12 bước của SQLite) và test trên CSDL cũ có dòng thật.
3. `created_by` thành nullable (khách không phải `users`); thêm `customer_id` (người xin) và `decided_by` (lễ tân duyệt/từ chối).
4. **Hạn tự hủy tính lười:** lịch `pending` quá `HAN_CHO_DUYET_GIO` (24 giờ) **không còn giữ chỗ** ngay lập tức (điều kiện nằm trong truy vấn trùng lịch), còn việc đổi trạng thái sang `cancelled` do một hàm quét chạy khi có người xem/duyệt/gửi. Đúng đắn không phụ thuộc vào việc có ai chạy quét hay không.
5. **Trần** `TRAN_LICH_CHO_MOI_KHACH = 3` lịch chờ còn hạn mỗi khách.
6. Lý do từ chối **hiện cho khách** nhưng chỉ với lịch do chính khách xin (`customer_id` có giá trị). Lý do hủy của lịch nhân viên tạo vẫn ẩn (phép quét rò rỉ ở 4c giữ nguyên).
7. Khách chọn nhân viên trong form (chặng 6 sẽ nhóm khung trống theo nhân viên) → tên nhân viên chăm sóc **có chủ đích** hiện ở form đặt lịch.

## Checklist

- [x] 5.0 Dựng lại bảng `appointments` cho CSDL cũ (CHECK có `pending`, `created_by` nullable) + cột `customer_id`, `decided_by`.
      → verify: test trên CSDL cũ có hóa đơn tham chiếu lịch; chạy lại lần hai không đổi gì.
- [x] 5.1 Thêm `pending` vào `TRANG_THAI`; liệt kê và kết luận từng chỗ dùng trạng thái lịch (dán vào log phiên).
      → verify: mỗi chỗ có test; `ghi_ho_so` và `lap_hoa_don` từ chối lịch `pending` (đỏ trước khi sửa).
- [x] 5.2 `pending` giữ chỗ; hạn tự hủy; trần số lịch chờ.
      → verify: hai khách xin cùng khung · quá hạn · chạm trần.
- [x] 5.3 Khách gửi yêu cầu (form `/khach/dat-lich`), qua cổng chặn chủ; lễ tân duyệt/từ chối (`/lich-cho-duyet` — đổi từ `/appointments/cho-duyet` vì router `appointments` đã có `/{id}`).
      → verify: lịch bị từ chối trả lại khung giờ cho người khác; thú cưng của người khác → 404 như nhau.
- [x] 5.4 Phép canh kiến trúc phủ hàm mới; đột biến; tài liệu; chạy toàn bộ test; kiểm thử tay bằng Chrome.
