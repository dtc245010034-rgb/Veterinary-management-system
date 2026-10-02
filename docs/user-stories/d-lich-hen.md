# D. Lịch hẹn — trọng tâm nghiệp vụ

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

Quy tắc chung: lịch hẹn chiếm khoảng thời gian nửa mở `[start_at, end_at)`. Hai khoảng gọi là
**giao nhau** khi `A.start < B.end` và `B.start < A.end`. Lịch có trạng thái `cancelled` không
tham gia kiểm tra trùng.

### US-10 — Đặt lịch chăm sóc

#### Mục tiêu

**Là** lễ tân, **tôi muốn** đặt lịch dịch vụ cho một thú cưng với nhân viên phụ trách, **để** giữ chỗ cho khách.

#### Tiêu chí chấp nhận

- Given thú cưng, dịch vụ, nhân viên và giờ bắt đầu, When đặt lịch, Then lịch được tạo với trạng thái `booked` và `end_at` tự tính bằng `start_at` cộng thời lượng dịch vụ.
- Given lịch vừa tạo, When xem lịch theo ngày, Then thấy lịch đó ở đúng khung giờ và đúng nhân viên.

#### Điều kiện biên

- Given giờ bắt đầu nằm trong quá khứ, When đặt lịch, Then bị từ chối.
- Given nhân viên được chọn có vai trò không phải `caretaker`, When đặt lịch, Then bị từ chối.
- Given buổi hẹn có phần nào rơi ra ngoài giờ mở cửa 08:00–18:00, hoặc kéo sang ngày hôm sau, When đặt lịch, Then bị từ chối kèm thông báo nêu giờ làm việc và giờ thật của buổi bị từ chối — **cả buổi** phải nằm trọn trong một ngày làm việc, không chỉ giờ bắt đầu.

### US-11 — Chặn trùng lịch

#### Mục tiêu

**Là** lễ tân, **tôi muốn** hệ thống từ chối lịch bị trùng và gợi ý khung giờ trống, **để** không xảy ra hai khách cùng một nhân viên một thời điểm.

#### Tiêu chí chấp nhận

- Given nhân viên A đã có lịch 09:00–10:00, When đặt lịch khác cho A lúc 09:30–10:30, Then bị từ chối vì trùng nhân viên, kèm danh sách khung trống gần nhất trong ngày.
- Given thú cưng P đã có lịch 09:00–10:00 với nhân viên A, When đặt lịch cho P lúc 09:30–10:30 với nhân viên B, Then bị từ chối vì một thú cưng không thể ở hai nơi cùng lúc.

#### Điều kiện biên

- Given nhân viên A có lịch 09:00–10:00, When đặt lịch cho A lúc 10:00–11:00, Then **được chấp nhận** — khoảng nửa mở nên hai lịch liền kề không tính là trùng.
- Given lịch 09:00–10:00 của nhân viên A đã bị hủy, When đặt lịch mới cho A lúc 09:00–10:00, Then được chấp nhận.
- Given lịch mới bao trọn lịch cũ (08:00–11:00 so với 09:00–10:00), When đặt, Then bị từ chối.
- Given lịch mới nằm gọn trong lịch cũ (09:15–09:45 so với 09:00–10:00), When đặt, Then bị từ chối.

### US-12 — Đổi lịch

#### Mục tiêu

**Là** lễ tân, **tôi muốn** đổi giờ hoặc nhân viên của một lịch hẹn, **để** xử lý khi khách báo bận.

#### Tiêu chí chấp nhận

- Given một lịch `booked`, When đổi sang khung giờ trống, Then lịch cập nhật giờ mới và trạng thái chuyển `rescheduled`.
- Given một lịch `booked`, When đổi sang khung giờ đã có lịch khác, Then bị từ chối và lịch **giữ nguyên** giờ cũ — không được để lịch rơi vào trạng thái nửa vời.

#### Điều kiện biên

- Given một lịch đang đổi, When kiểm tra trùng, Then **không** tự so sánh với chính nó và báo trùng.
- Given một lịch đã `cancelled` hoặc `done`, When đổi lịch, Then bị từ chối.
- Given giờ mới đưa buổi ra ngoài giờ mở cửa, When đổi lịch, Then bị từ chối — luật giờ mở cửa của US-10 áp cho đổi lịch y hệt như đặt lịch.
- Given đổi lịch nhưng giữ nguyên **cả** giờ lẫn nhân viên, When lưu, Then lịch **không** chuyển sang `rescheduled`: trạng thái chỉ đổi khi thật sự có thứ đổi.

### US-13 — Hủy lịch

#### Mục tiêu

**Là** lễ tân, **tôi muốn** hủy lịch kèm lý do, **để** giải phóng khung giờ cho khách khác.

#### Tiêu chí chấp nhận

- Given một lịch `booked`, When hủy kèm lý do, Then trạng thái thành `cancelled`, lý do được lưu, và khung giờ đó đặt được cho khách khác.

#### Điều kiện biên

- Given một lịch đã `done`, When hủy, Then bị từ chối.
- Given một lịch đã có hóa đơn, When hủy, Then bị chặn với thông báo phải hủy hóa đơn trước (xem US-21).

### US-14 — Xem lịch làm việc

#### Mục tiêu

**Là** nhân viên chăm sóc, **tôi muốn** xem lịch của mình theo ngày, **để** biết hôm nay làm gì.

#### Tiêu chí chấp nhận

- Given vai trò `caretaker`, When mở trang lịch, Then chỉ thấy lịch của chính mình, sắp xếp theo giờ tăng dần.
- Given vai trò `receptionist` hoặc `manager`, When mở trang lịch, Then thấy lịch của toàn bộ nhân viên, lọc được theo ngày và theo nhân viên.

#### Điều kiện biên

- Given một ngày không có lịch nào, When xem, Then hiện trạng thái rỗng rõ ràng.
