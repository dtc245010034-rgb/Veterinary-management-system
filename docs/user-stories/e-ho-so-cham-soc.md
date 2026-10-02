# E. Hồ sơ chăm sóc

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-15 — Ghi hồ sơ sau buổi chăm sóc

#### Mục tiêu

**Là** nhân viên chăm sóc, **tôi muốn** ghi lại tình trạng thú cưng và việc đã làm, **để** lần sau có căn cứ và chủ nuôi nắm được.

#### Tiêu chí chấp nhận

- Given một lịch hẹn của mình đang `booked`, When ghi hồ sơ chăm sóc, Then hồ sơ được lưu gắn với lịch hẹn và lịch chuyển trạng thái `done`.
- Given một lịch hẹn của nhân viên khác, When cố ghi hồ sơ, Then bị từ chối.

#### Điều kiện biên

- Given một lịch đã có hồ sơ, When ghi hồ sơ lần hai cho cùng lịch đó, Then bị từ chối — mỗi lịch hẹn chỉ một hồ sơ.
- Given form hồ sơ, When bỏ trống phần ghi chú tình trạng, Then bị từ chối.

### US-16 — Xem lịch sử chăm sóc

#### Mục tiêu

**Là** lễ tân, **tôi muốn** xem toàn bộ lịch sử chăm sóc của một thú cưng, **để** trả lời khi chủ nuôi hỏi.

#### Tiêu chí chấp nhận

- Given thú cưng đã qua nhiều buổi dịch vụ, When mở lịch sử chăm sóc, Then thấy danh sách theo thứ tự thời gian giảm dần, mỗi dòng có ngày, dịch vụ, nhân viên và ghi chú tình trạng.

#### Điều kiện biên

- Given thú cưng chưa từng dùng dịch vụ, When mở lịch sử, Then hiện trạng thái rỗng.
