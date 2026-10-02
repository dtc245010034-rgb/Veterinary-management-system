# H. Thống kê

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-22 — Thống kê lượt dịch vụ và doanh thu

#### Mục tiêu

**Là** quản lý, **tôi muốn** xem số lượt dịch vụ và doanh thu theo khoảng thời gian, **để** biết cửa hàng đang chạy thế nào.

#### Tiêu chí chấp nhận

- Given khoảng thời gian đã chọn, When xem thống kê, Then thấy tổng số lượt dịch vụ, tổng doanh thu và bảng chia theo từng dịch vụ.
- Given có hóa đơn `unpaid` trong kỳ, When tính doanh thu, Then doanh thu chỉ tính **tiền đã thực nhận**, và số chưa thu hiển thị riêng.

#### Điều kiện biên

- Given khoảng thời gian không có dữ liệu, When xem, Then hiện số 0 và trạng thái rỗng, không phải lỗi.
- Given ngày bắt đầu sau ngày kết thúc, When xem, Then bị từ chối.

### US-23 — Khách quay lại

#### Mục tiêu

**Là** quản lý, **tôi muốn** biết bao nhiêu chủ nuôi quay lại dùng dịch vụ, **để** đánh giá mức giữ chân khách.

#### Tiêu chí chấp nhận

- Given trong kỳ có chủ nuôi dùng dịch vụ từ 2 lần trở lên, When xem thống kê, Then thấy số lượng và tỉ lệ khách quay lại trên tổng số khách trong kỳ.

#### Điều kiện biên

- Given mọi chủ nuôi trong kỳ đều chỉ đến một lần, When xem, Then tỉ lệ khách quay lại bằng 0%.
