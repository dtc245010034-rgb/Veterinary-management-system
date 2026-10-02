# C. Dịch vụ, bảng giá, gói dịch vụ

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-07 — Quản lý dịch vụ và bảng giá

#### Mục tiêu

**Là** quản lý, **tôi muốn** khai báo dịch vụ kèm giá và thời lượng, **để** lễ tân đặt lịch và tính tiền đúng.

#### Tiêu chí chấp nhận

- Given form thêm dịch vụ, When nhập tên, giá và thời lượng hợp lệ, Then dịch vụ xuất hiện trong danh sách chọn khi đặt lịch.
- Given một dịch vụ đã dùng trong hóa đơn cũ, When đổi giá dịch vụ, Then hóa đơn cũ **giữ nguyên** giá tại thời điểm lập, chỉ lịch hẹn mới dùng giá mới.

#### Điều kiện biên

- Given form thêm dịch vụ, When nhập giá âm hoặc thời lượng nhỏ hơn hoặc bằng 0, Then bị từ chối.
- Given giá vượt 1 tỷ đồng, hoặc ô giá gõ có phần lẻ, When lưu dịch vụ, Then bị từ chối — giá **chỉ nhận số nguyên đồng**, còn dấu chấm, phẩy và khoảng trắng đều hiểu là phân cách nghìn (`150.000` và `150000` là một).
- Given thời lượng dài hơn một ngày làm việc, When lưu dịch vụ, Then bị từ chối — dịch vụ dài hơn giờ mở cửa thì không buổi nào đặt vừa (xem US-10).

### US-08 — Gói dịch vụ

#### Mục tiêu

**Là** quản lý, **tôi muốn** gộp nhiều dịch vụ thành gói có giá riêng, **để** bán combo cho khách quen.

#### Tiêu chí chấp nhận

- Given các dịch vụ đã có, When tạo gói gồm 3 dịch vụ với giá gói, Then gói hiện trong danh sách chọn khi lập hóa đơn.
- Given một gói, When xem chi tiết, Then thấy danh sách dịch vụ thành phần, số lượng mỗi loại và tổng giá lẻ để so sánh với giá gói.

#### Điều kiện biên

- Given gói chưa có dịch vụ thành phần nào, When lưu gói, Then bị từ chối.
- Given một dòng trong gói có số lượt nhỏ hơn hoặc bằng 0, hoặc không phải số, When lưu gói, Then bị từ chối kèm thông báo nêu đúng lý do — **không** âm thầm bỏ qua dòng sai rồi báo nhầm thành "gói rỗng". Ô số lượt **để trống** vẫn là cách bỏ chọn dịch vụ đó.

### US-09 — Ngưng bán dịch vụ

#### Mục tiêu

**Là** quản lý, **tôi muốn** ngưng bán một dịch vụ thay vì xóa, **để** không mất dữ liệu lịch sử.

#### Tiêu chí chấp nhận

- Given một dịch vụ đang có lịch hẹn và hóa đơn cũ, When đánh dấu ngưng bán, Then dịch vụ biến mất khỏi danh sách chọn khi đặt lịch mới.
- Given dịch vụ đã ngưng bán, When xem hóa đơn cũ có dịch vụ đó, Then dữ liệu vẫn hiển thị đầy đủ.

#### Điều kiện biên

Chưa có điều kiện biên riêng — mọi tiêu chí của story này nằm ở mục trên.
