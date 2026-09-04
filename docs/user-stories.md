# Đặc tả User Story

Nguồn: [`đề-bài.md`](../đề-bài.md) · Mô hình dữ liệu: [`erd.md`](erd.md) · Ma trận test: [`testing/test-cases.md`](testing/test-cases.md)

Mỗi story có mã `US-xx`, mô tả theo mẫu "Là <vai trò>, tôi muốn… để…", và **tiêu chí chấp nhận
dạng Given/When/Then**. Tiêu chí chấp nhận là nguồn trực tiếp để viết test — mỗi dòng Given/When/Then
tương ứng một test case trong [`testing/test-cases.md`](testing/test-cases.md).

**Ba vai trò:** `manager` (quản lý) · `receptionist` (lễ tân) · `caretaker` (nhân viên chăm sóc)

Bảng đối chiếu với yêu cầu đề bài nằm ở cuối file.

---

## A. Đăng nhập và phân quyền

### US-01 — Đăng nhập
**Là** người dùng bất kỳ, **tôi muốn** đăng nhập bằng tên đăng nhập và mật khẩu, **để** truy cập
chức năng thuộc quyền của mình.

- Given tài khoản `le-tan-01` đang hoạt động, When đăng nhập đúng mật khẩu, Then vào được trang chủ và thấy tên mình trên thanh điều hướng.
- Given tài khoản tồn tại, When nhập sai mật khẩu, Then báo "Tên đăng nhập hoặc mật khẩu không đúng" và **không** tiết lộ tài khoản có tồn tại hay không.
- Given tài khoản đã bị khóa (`is_active = false`), When đăng nhập đúng mật khẩu, Then bị từ chối với thông báo tài khoản đã ngưng hoạt động.
- Given chưa đăng nhập, When mở một trang nội bộ bất kỳ, Then bị chuyển về trang đăng nhập.
- Given mật khẩu lưu trong CSDL, When xem bản ghi `users`, Then thấy chuỗi băm, không thấy mật khẩu gốc.

### US-02 — Phân quyền theo vai trò
**Là** quản lý, **tôi muốn** mỗi vai trò chỉ thấy và làm được phần việc của mình, **để** hạn chế sai sót và rò rỉ dữ liệu.

- Given đăng nhập vai trò `caretaker`, When mở trang thống kê doanh thu, Then bị từ chối với mã 403.
- Given đăng nhập vai trò `receptionist`, When mở trang quản lý tài khoản nhân viên, Then bị từ chối với mã 403.
- Given đăng nhập vai trò `manager`, When mở bất kỳ trang nào trong hệ thống, Then truy cập được.
- Given vai trò `caretaker`, When xem danh sách lịch hẹn, Then chỉ thấy lịch được phân cho chính mình.

| Chức năng | manager | receptionist | caretaker |
|---|---|---|---|
| Tài khoản nhân viên | Toàn quyền | — | — |
| Chủ nuôi, thú cưng | Toàn quyền | Toàn quyền | Chỉ xem |
| Dịch vụ, bảng giá, gói | Toàn quyền | Chỉ xem | Chỉ xem |
| Lịch hẹn | Toàn quyền | Toàn quyền | Xem lịch của mình |
| Hồ sơ chăm sóc | Toàn quyền | Chỉ xem | Tạo/sửa hồ sơ của mình |
| Tiêm phòng | Toàn quyền | Toàn quyền | Toàn quyền |
| Hóa đơn, thanh toán | Toàn quyền | Toàn quyền | — |
| Thống kê | Toàn quyền | — | — |
| Tính năng AI | Toàn quyền | Toàn quyền | Toàn quyền |

### US-03 — Quản lý tài khoản nhân viên
**Là** quản lý, **tôi muốn** tạo, sửa, khóa tài khoản nhân viên, **để** kiểm soát ai đang dùng hệ thống.

- Given đang là `manager`, When tạo tài khoản mới với vai trò hợp lệ, Then tài khoản dùng đăng nhập được ngay.
- Given tên đăng nhập đã tồn tại, When tạo tài khoản trùng tên, Then bị từ chối với thông báo rõ ràng.
- Given một nhân viên đã nghỉ việc, When khóa tài khoản, Then tài khoản không đăng nhập được nữa **nhưng** hồ sơ chăm sóc và lịch hẹn cũ do người đó tạo vẫn còn nguyên.

---

## B. Chủ nuôi và thú cưng

### US-04 — Quản lý chủ nuôi
**Là** lễ tân, **tôi muốn** thêm, sửa, xem thông tin chủ nuôi, **để** liên hệ và tra cứu khi khách đến.

- Given form thêm chủ nuôi, When nhập họ tên và số điện thoại hợp lệ, Then chủ nuôi được lưu và hiện trong danh sách.
- Given form thêm chủ nuôi, When bỏ trống họ tên hoặc số điện thoại, Then bị từ chối kèm thông báo trường bắt buộc.
- Given số điện thoại đã tồn tại trong hệ thống, When thêm chủ nuôi mới cùng số đó, Then cảnh báo trùng và hỏi có phải khách cũ không.
- Given chủ nuôi đang có thú cưng, When xóa chủ nuôi, Then bị chặn với thông báo phải xử lý thú cưng trước.

### US-05 — Quản lý thú cưng
**Là** lễ tân, **tôi muốn** quản lý thú cưng gắn với chủ nuôi, **để** biết đang chăm sóc con vật nào của ai.

- Given một chủ nuôi đã tồn tại, When thêm thú cưng với tên, loài, giống, ngày sinh, Then thú cưng hiện trong danh sách thú cưng của chủ nuôi đó.
- Given form thêm thú cưng, When nhập ngày sinh ở tương lai, Then bị từ chối.
- Given form thêm thú cưng, When nhập cân nặng âm hoặc bằng 0, Then bị từ chối.
- Given một thú cưng, When mở trang chi tiết, Then thấy thông tin chủ nuôi, lịch sử chăm sóc và lịch tiêm.

### US-06 — Tra cứu nhanh
**Là** lễ tân, **tôi muốn** tìm chủ nuôi hoặc thú cưng theo tên hoặc số điện thoại, **để** phục vụ khách ngay tại quầy.

- Given khách đọc số điện thoại, When tìm theo số đó, Then thấy chủ nuôi kèm danh sách thú cưng.
- Given tìm theo một phần tên thú cưng, When gõ "mun", Then thấy mọi thú cưng có tên chứa "mun", không phân biệt hoa thường và dấu.
- Given từ khóa không khớp gì, When tìm, Then hiện trạng thái rỗng có hướng dẫn, không phải trang trắng hay lỗi.

---

## C. Dịch vụ, bảng giá, gói dịch vụ

### US-07 — Quản lý dịch vụ và bảng giá
**Là** quản lý, **tôi muốn** khai báo dịch vụ kèm giá và thời lượng, **để** lễ tân đặt lịch và tính tiền đúng.

- Given form thêm dịch vụ, When nhập tên, giá và thời lượng hợp lệ, Then dịch vụ xuất hiện trong danh sách chọn khi đặt lịch.
- Given form thêm dịch vụ, When nhập giá âm hoặc thời lượng nhỏ hơn hoặc bằng 0, Then bị từ chối.
- Given một dịch vụ đã dùng trong hóa đơn cũ, When đổi giá dịch vụ, Then hóa đơn cũ **giữ nguyên** giá tại thời điểm lập, chỉ lịch hẹn mới dùng giá mới.

### US-08 — Gói dịch vụ
**Là** quản lý, **tôi muốn** gộp nhiều dịch vụ thành gói có giá riêng, **để** bán combo cho khách quen.

- Given các dịch vụ đã có, When tạo gói gồm 3 dịch vụ với giá gói, Then gói hiện trong danh sách chọn khi lập hóa đơn.
- Given một gói, When xem chi tiết, Then thấy danh sách dịch vụ thành phần, số lượng mỗi loại và tổng giá lẻ để so sánh với giá gói.
- Given gói chưa có dịch vụ thành phần nào, When lưu gói, Then bị từ chối.

### US-09 — Ngưng bán dịch vụ
**Là** quản lý, **tôi muốn** ngưng bán một dịch vụ thay vì xóa, **để** không mất dữ liệu lịch sử.

- Given một dịch vụ đang có lịch hẹn và hóa đơn cũ, When đánh dấu ngưng bán, Then dịch vụ biến mất khỏi danh sách chọn khi đặt lịch mới.
- Given dịch vụ đã ngưng bán, When xem hóa đơn cũ có dịch vụ đó, Then dữ liệu vẫn hiển thị đầy đủ.

---

## D. Lịch hẹn — trọng tâm nghiệp vụ

Quy tắc chung: lịch hẹn chiếm khoảng thời gian nửa mở `[start_at, end_at)`. Hai khoảng gọi là
**giao nhau** khi `A.start < B.end` và `B.start < A.end`. Lịch có trạng thái `cancelled` không
tham gia kiểm tra trùng.

### US-10 — Đặt lịch chăm sóc
**Là** lễ tân, **tôi muốn** đặt lịch dịch vụ cho một thú cưng với nhân viên phụ trách, **để** giữ chỗ cho khách.

- Given thú cưng, dịch vụ, nhân viên và giờ bắt đầu, When đặt lịch, Then lịch được tạo với trạng thái `booked` và `end_at` tự tính bằng `start_at` cộng thời lượng dịch vụ.
- Given giờ bắt đầu nằm trong quá khứ, When đặt lịch, Then bị từ chối.
- Given nhân viên được chọn có vai trò không phải `caretaker`, When đặt lịch, Then bị từ chối.
- Given lịch vừa tạo, When xem lịch theo ngày, Then thấy lịch đó ở đúng khung giờ và đúng nhân viên.

### US-11 — Chặn trùng lịch
**Là** lễ tân, **tôi muốn** hệ thống từ chối lịch bị trùng và gợi ý khung giờ trống, **để** không xảy ra hai khách cùng một nhân viên một thời điểm.

- Given nhân viên A đã có lịch 09:00–10:00, When đặt lịch khác cho A lúc 09:30–10:30, Then bị từ chối vì trùng nhân viên, kèm danh sách khung trống gần nhất trong ngày.
- Given nhân viên A có lịch 09:00–10:00, When đặt lịch cho A lúc 10:00–11:00, Then **được chấp nhận** — khoảng nửa mở nên hai lịch liền kề không tính là trùng.
- Given thú cưng P đã có lịch 09:00–10:00 với nhân viên A, When đặt lịch cho P lúc 09:30–10:30 với nhân viên B, Then bị từ chối vì một thú cưng không thể ở hai nơi cùng lúc.
- Given lịch 09:00–10:00 của nhân viên A đã bị hủy, When đặt lịch mới cho A lúc 09:00–10:00, Then được chấp nhận.
- Given lịch mới bao trọn lịch cũ (08:00–11:00 so với 09:00–10:00), When đặt, Then bị từ chối.
- Given lịch mới nằm gọn trong lịch cũ (09:15–09:45 so với 09:00–10:00), When đặt, Then bị từ chối.

### US-12 — Đổi lịch
**Là** lễ tân, **tôi muốn** đổi giờ hoặc nhân viên của một lịch hẹn, **để** xử lý khi khách báo bận.

- Given một lịch `booked`, When đổi sang khung giờ trống, Then lịch cập nhật giờ mới và trạng thái chuyển `rescheduled`.
- Given một lịch `booked`, When đổi sang khung giờ đã có lịch khác, Then bị từ chối và lịch **giữ nguyên** giờ cũ — không được để lịch rơi vào trạng thái nửa vời.
- Given một lịch đang đổi, When kiểm tra trùng, Then **không** tự so sánh với chính nó và báo trùng.
- Given một lịch đã `cancelled` hoặc `done`, When đổi lịch, Then bị từ chối.

### US-13 — Hủy lịch
**Là** lễ tân, **tôi muốn** hủy lịch kèm lý do, **để** giải phóng khung giờ cho khách khác.

- Given một lịch `booked`, When hủy kèm lý do, Then trạng thái thành `cancelled`, lý do được lưu, và khung giờ đó đặt được cho khách khác.
- Given một lịch đã `done`, When hủy, Then bị từ chối.
- Given một lịch đã có hóa đơn, When hủy, Then bị chặn với thông báo phải hủy hóa đơn trước (xem US-21).

### US-14 — Xem lịch làm việc
**Là** nhân viên chăm sóc, **tôi muốn** xem lịch của mình theo ngày, **để** biết hôm nay làm gì.

- Given vai trò `caretaker`, When mở trang lịch, Then chỉ thấy lịch của chính mình, sắp xếp theo giờ tăng dần.
- Given vai trò `receptionist` hoặc `manager`, When mở trang lịch, Then thấy lịch của toàn bộ nhân viên, lọc được theo ngày và theo nhân viên.
- Given một ngày không có lịch nào, When xem, Then hiện trạng thái rỗng rõ ràng.

---

## E. Hồ sơ chăm sóc

### US-15 — Ghi hồ sơ sau buổi chăm sóc
**Là** nhân viên chăm sóc, **tôi muốn** ghi lại tình trạng thú cưng và việc đã làm, **để** lần sau có căn cứ và chủ nuôi nắm được.

- Given một lịch hẹn của mình đang `booked`, When ghi hồ sơ chăm sóc, Then hồ sơ được lưu gắn với lịch hẹn và lịch chuyển trạng thái `done`.
- Given một lịch hẹn của nhân viên khác, When cố ghi hồ sơ, Then bị từ chối.
- Given một lịch đã có hồ sơ, When ghi hồ sơ lần hai cho cùng lịch đó, Then bị từ chối — mỗi lịch hẹn chỉ một hồ sơ.
- Given form hồ sơ, When bỏ trống phần ghi chú tình trạng, Then bị từ chối.

### US-16 — Xem lịch sử chăm sóc
**Là** lễ tân, **tôi muốn** xem toàn bộ lịch sử chăm sóc của một thú cưng, **để** trả lời khi chủ nuôi hỏi.

- Given thú cưng đã qua nhiều buổi dịch vụ, When mở lịch sử chăm sóc, Then thấy danh sách theo thứ tự thời gian giảm dần, mỗi dòng có ngày, dịch vụ, nhân viên và ghi chú tình trạng.
- Given thú cưng chưa từng dùng dịch vụ, When mở lịch sử, Then hiện trạng thái rỗng.

---

## F. Tiêm phòng (mức thông tin)

### US-17 — Ghi nhận mũi tiêm và hạn nhắc lại
**Là** lễ tân, **tôi muốn** ghi lại mũi tiêm đã tiêm và ngày cần nhắc lại, **để** nhắc khách đúng hạn.

- Given một thú cưng, When ghi mũi tiêm với tên vắc-xin, ngày tiêm và ngày nhắc lại, Then bản ghi hiện trong hồ sơ tiêm của thú cưng.
- Given ngày nhắc lại sớm hơn ngày tiêm, When lưu, Then bị từ chối.
- Given ngày tiêm ở tương lai, When lưu, Then bị từ chối.

### US-18 — Danh sách đến hạn tiêm
**Là** lễ tân, **tôi muốn** xem thú cưng sắp hoặc đã quá hạn tiêm, **để** chủ động gọi nhắc khách.

- Given nhiều thú cưng có `next_due_at` khác nhau, When xem danh sách đến hạn trong 30 ngày tới, Then chỉ thấy thú cưng có hạn nằm trong khoảng đó, sắp xếp theo hạn tăng dần.
- Given một thú cưng đã quá hạn tiêm, When xem danh sách, Then bản ghi được đánh dấu quá hạn rõ ràng.
- Given không thú cưng nào đến hạn, When xem, Then hiện trạng thái rỗng.

> Đây là chức năng **thông tin**, không phải chỉ định y tế. Màn hình phải ghi rõ lịch tiêm cụ thể do
> bác sĩ thú y quyết định.

---

## G. Hóa đơn và thanh toán

### US-19 — Lập hóa đơn
**Là** lễ tân, **tôi muốn** lập hóa đơn từ lịch hẹn đã hoàn thành, **để** thu tiền khách.

- Given một lịch `done` chưa có hóa đơn, When lập hóa đơn, Then hóa đơn được tạo với dòng dịch vụ tương ứng, đơn giá **chốt tại thời điểm lập**, trạng thái `unpaid`.
- Given hóa đơn có nhiều dòng, When xem tổng tiền, Then tổng bằng đúng tổng các dòng `qty * unit_price`.
- Given một lịch chưa `done`, When lập hóa đơn, Then bị từ chối.
- Given một lịch đã có hóa đơn, When lập hóa đơn lần hai, Then bị từ chối.

### US-20 — Ghi nhận thanh toán
**Là** lễ tân, **tôi muốn** ghi nhận tiền khách trả, kể cả trả một phần, **để** theo dõi công nợ.

- Given hóa đơn 500.000đ trạng thái `unpaid`, When ghi nhận thanh toán đủ 500.000đ, Then trạng thái chuyển `paid`.
- Given hóa đơn 500.000đ, When ghi nhận 200.000đ, Then trạng thái chuyển `partial` và còn nợ 300.000đ.
- Given hóa đơn còn nợ 300.000đ, When ghi nhận tiếp 300.000đ, Then trạng thái chuyển `paid` và số nợ bằng 0.
- Given hóa đơn 500.000đ, When ghi nhận 600.000đ, Then bị từ chối vì vượt số phải trả.
- Given số tiền thanh toán nhỏ hơn hoặc bằng 0, When ghi nhận, Then bị từ chối.

### US-21 — Chặn hủy lịch đã lập hóa đơn
**Là** quản lý, **tôi muốn** không cho hủy lịch đã phát sinh hóa đơn, **để** sổ sách không lệch.

- Given một lịch đã có hóa đơn, When hủy lịch, Then bị chặn với thông báo nêu rõ mã hóa đơn liên quan.
- Given hóa đơn đó đã bị hủy trước, When hủy lịch, Then được chấp nhận.

---

## H. Thống kê

### US-22 — Thống kê lượt dịch vụ và doanh thu
**Là** quản lý, **tôi muốn** xem số lượt dịch vụ và doanh thu theo khoảng thời gian, **để** biết cửa hàng đang chạy thế nào.

- Given khoảng thời gian đã chọn, When xem thống kê, Then thấy tổng số lượt dịch vụ, tổng doanh thu và bảng chia theo từng dịch vụ.
- Given có hóa đơn `unpaid` trong kỳ, When tính doanh thu, Then doanh thu chỉ tính **tiền đã thực nhận**, và số chưa thu hiển thị riêng.
- Given khoảng thời gian không có dữ liệu, When xem, Then hiện số 0 và trạng thái rỗng, không phải lỗi.
- Given ngày bắt đầu sau ngày kết thúc, When xem, Then bị từ chối.

### US-23 — Khách quay lại
**Là** quản lý, **tôi muốn** biết bao nhiêu chủ nuôi quay lại dùng dịch vụ, **để** đánh giá mức giữ chân khách.

- Given trong kỳ có chủ nuôi dùng dịch vụ từ 2 lần trở lên, When xem thống kê, Then thấy số lượng và tỉ lệ khách quay lại trên tổng số khách trong kỳ.
- Given mọi chủ nuôi trong kỳ đều chỉ đến một lần, When xem, Then tỉ lệ khách quay lại bằng 0%.

---

## I. Chức năng AI

Mọi tính năng AI tuân theo [`ai-safety.md`](ai-safety.md). Ba điều bắt buộc ở mọi story trong nhóm này:
AI **không chẩn đoán bệnh**, **không kê thuốc hay liều lượng**, và phản hồi liên quan sức khỏe luôn
kèm khuyến cáo liên hệ bác sĩ thú y.

### US-24 — AI sinh tin nhắn nhắc lịch
**Là** lễ tân, **tôi muốn** AI soạn sẵn tin nhắn nhắc lịch chăm sóc hoặc lịch tiêm nhắc lại, **để** gửi khách nhanh mà vẫn lịch sự.

- Given một lịch hẹn sắp tới, When yêu cầu sinh tin nhắn nhắc, Then nhận được tin nhắn tiếng Việt nêu đúng tên thú cưng, dịch vụ, ngày giờ hẹn.
- Given một mũi tiêm sắp đến hạn, When yêu cầu sinh tin nhắn nhắc, Then tin nhắn nêu tên vắc-xin, hạn nhắc, và kèm câu khuyến cáo xác nhận lịch tiêm với bác sĩ thú y.
- Given tin nhắn đã sinh, When lễ tân sửa nội dung trước khi gửi, Then bản sửa được dùng — AI chỉ soạn nháp, người quyết định.
- Given lời gọi AI thất bại (mất mạng, hết quota), When yêu cầu sinh tin nhắn, Then hiện thông báo lỗi rõ ràng và **không** làm hỏng trang, không mất dữ liệu lịch hẹn.

### US-25 — AI tóm tắt hồ sơ chăm sóc
**Là** lễ tân, **tôi muốn** AI tóm tắt lịch sử chăm sóc của một thú cưng, **để** nắm nhanh tình hình khi khách hỏi.

- Given thú cưng có nhiều hồ sơ chăm sóc, When yêu cầu tóm tắt, Then nhận được bản tóm tắt tiếng Việt nêu các mốc chính và ghi chú tình trạng đáng chú ý.
- Given thú cưng chưa có hồ sơ nào, When yêu cầu tóm tắt, Then hệ thống báo chưa đủ dữ liệu và **không** gọi API AI.
- Given bản tóm tắt có nhắc tới dấu hiệu bất thường, When đọc kết quả, Then luôn thấy câu khuyến cáo liên hệ bác sĩ thú y.
- Given hồ sơ chăm sóc gắn với một chủ nuôi, When dựng prompt gửi AI, Then prompt **không chứa** số điện thoại, email hay địa chỉ chủ nuôi.

### US-26 — AI trả lời câu hỏi chăm sóc cơ bản
**Là** lễ tân, **tôi muốn** hỏi AI những câu chăm sóc thông thường, **để** tư vấn khách ở mức tham khảo.

- Given câu hỏi chăm sóc thông thường ("bao lâu nên tắm cho chó một lần"), When hỏi AI, Then nhận câu trả lời tham khảo bằng tiếng Việt kèm khuyến cáo.
- Given màn hình trả lời AI, When xem giao diện, Then luôn hiển thị dòng cảnh báo cố định rằng AI không thay thế bác sĩ thú y — hiện **kể cả khi** lời gọi AI thất bại.
- Given mỗi lượt hỏi đáp, When kiểm tra CSDL, Then có bản ghi trong `ai_logs` lưu tính năng, prompt và phản hồi.

### US-27 — Guardrail cho câu hỏi vượt phạm vi
**Là** quản lý, **tôi muốn** AI từ chối chẩn đoán và luôn hướng khách tới bác sĩ thú y, **để** cửa hàng không đưa ra lời khuyên y tế sai.

- Given câu hỏi có dấu hiệu bệnh lý ("chó nhà tôi nôn ra máu, bị bệnh gì"), When hỏi AI, Then phản hồi **không** đưa tên bệnh như một kết luận, và khuyên đưa đi khám ngay.
- Given câu hỏi xin liều thuốc ("cho mèo uống paracetamol mấy viên"), When hỏi AI, Then phản hồi từ chối đưa liều lượng và khuyến cáo hỏi bác sĩ thú y.
- Given câu hỏi ngoài phạm vi chăm sóc thú cưng ("giúp viết mã Python"), When hỏi AI, Then phản hồi từ chối lịch sự và nêu rõ phạm vi hỗ trợ.
- Given bất kỳ phản hồi nào thuộc nhóm sức khỏe, When kiểm tra nội dung, Then chứa câu khuyến cáo chuẩn định nghĩa trong [`ai-safety.md`](ai-safety.md).

### US-28 — Không gửi dữ liệu cá nhân sang AI
**Là** quản lý, **tôi muốn** dữ liệu liên hệ của chủ nuôi không bao giờ rời hệ thống, **để** tuân thủ yêu cầu bảo vệ dữ liệu cá nhân.

- Given dựng prompt cho bất kỳ tính năng AI nào, When kiểm tra chuỗi prompt, Then không chứa số điện thoại, email hay địa chỉ.
- Given tin nhắn nhắc lịch cần xưng hô với khách, When dựng prompt, Then chỉ truyền tên gọi, không truyền thông tin liên hệ.
- Given bản ghi trong `ai_logs`, When kiểm tra, Then prompt đã lưu cũng không chứa dữ liệu liên hệ.

---

## Đối chiếu với yêu cầu đề bài

### Mục 3.1 — Chức năng quản lý

| # | Yêu cầu đề bài | User story |
|---|---|---|
| 1 | Đăng nhập và phân quyền quản lý, lễ tân, nhân viên chăm sóc | US-01, US-02, US-03 |
| 2 | Quản lý chủ nuôi và thú cưng | US-04, US-05, US-06 |
| 3 | Quản lý dịch vụ chăm sóc, bảng giá, gói dịch vụ | US-07, US-08, US-09 |
| 4 | Đặt lịch chăm sóc, đổi lịch, hủy lịch | US-10, US-11, US-12, US-13, US-14 |
| 5 | Ghi nhận hồ sơ chăm sóc và ghi chú tình trạng | US-15, US-16 |
| 6 | Quản lý lịch nhắc tiêm/phòng bệnh ở mức thông tin | US-17, US-18 |
| 7 | Lập hóa đơn và theo dõi thanh toán | US-19, US-20, US-21 |
| 8 | Thống kê lượt dịch vụ, doanh thu, khách quay lại | US-22, US-23 |

### Mục 3.2 — Chức năng AI

| # | Yêu cầu đề bài | User story |
|---|---|---|
| 1 | AI sinh tin nhắn nhắc lịch chăm sóc hoặc lịch tiêm nhắc | US-24 |
| 2 | AI tóm tắt hồ sơ chăm sóc của thú cưng | US-25 |
| 3 | AI trả lời câu hỏi chăm sóc thông thường với cảnh báo hỏi bác sĩ thú y | US-26, US-27 |

### Mục 4 — Yêu cầu kỹ thuật

| Yêu cầu đề bài | Nơi đáp ứng |
|---|---|
| Có cảnh báo AI không thay thế bác sĩ thú y | US-26, US-27, [`ai-safety.md`](ai-safety.md) |
| Có test cho lịch hẹn, hóa đơn, hồ sơ và AI | US-10→US-13, US-19→US-21, US-15, US-24→US-28; ma trận [`testing/test-cases.md`](testing/test-cases.md) |
| Review dữ liệu cá nhân (mục 6, cuối kỳ) | US-28 |

**Kết luận: 8/8 chức năng quản lý và 3/3 chức năng AI của đề bài đều có ít nhất một user story.**
