# A. Đăng nhập và phân quyền

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-01 — Đăng nhập

#### Mục tiêu

**Là** người dùng bất kỳ, **tôi muốn** đăng nhập bằng tên đăng nhập và mật khẩu, **để** truy cập
chức năng thuộc quyền của mình.

#### Tiêu chí chấp nhận

- Given tài khoản `le-tan-01` đang hoạt động, When đăng nhập đúng mật khẩu, Then vào được trang chủ và thấy tên mình trên thanh điều hướng.
- Given mật khẩu lưu trong CSDL, When xem bản ghi `users`, Then thấy chuỗi băm, không thấy mật khẩu gốc.

#### Điều kiện biên

- Given tài khoản tồn tại, When nhập sai mật khẩu, Then báo "Tên đăng nhập hoặc mật khẩu không đúng" và **không** tiết lộ tài khoản có tồn tại hay không.
- Given tài khoản đã bị khóa (`is_active = false`), When đăng nhập đúng mật khẩu, Then bị từ chối với thông báo tài khoản đã ngưng hoạt động.
- Given chưa đăng nhập, When mở một trang nội bộ bất kỳ, Then bị chuyển về trang đăng nhập.

### US-02 — Phân quyền theo vai trò

#### Mục tiêu

**Là** quản lý, **tôi muốn** mỗi vai trò chỉ thấy và làm được phần việc của mình, **để** hạn chế sai sót và rò rỉ dữ liệu.

#### Tiêu chí chấp nhận

- Given đăng nhập vai trò `manager`, When mở bất kỳ trang nào trong hệ thống, Then truy cập được.
- Given vai trò `caretaker`, When xem danh sách lịch hẹn, Then chỉ thấy lịch được phân cho chính mình.

#### Điều kiện biên

- Given đăng nhập vai trò `caretaker`, When mở trang thống kê doanh thu, Then bị từ chối với mã 403.
- Given đăng nhập vai trò `receptionist`, When mở trang quản lý tài khoản nhân viên, Then bị từ chối với mã 403.

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

#### Mục tiêu

**Là** quản lý, **tôi muốn** tạo, sửa, khóa tài khoản nhân viên, **để** kiểm soát ai đang dùng hệ thống.

#### Tiêu chí chấp nhận

- Given đang là `manager`, When tạo tài khoản mới với vai trò hợp lệ, Then tài khoản dùng đăng nhập được ngay.
- Given một nhân viên đã nghỉ việc, When khóa tài khoản, Then tài khoản không đăng nhập được nữa **nhưng** hồ sơ chăm sóc và lịch hẹn cũ do người đó tạo vẫn còn nguyên.
- Given một tài khoản đang dùng, When sửa họ tên hoặc vai trò, Then thay đổi có hiệu lực ngay; **tên đăng nhập không sửa được** vì đó là khóa tra cứu trong nhật ký.
- Given đang là `manager` và một nhân viên quên mật khẩu, When đặt lại mật khẩu cho họ, Then nhân viên đăng nhập được bằng mật khẩu mới mà không cần mật khẩu cũ.

#### Điều kiện biên

- Given tên đăng nhập đã tồn tại, When tạo tài khoản trùng tên, Then bị từ chối với thông báo rõ ràng.
- Given đang đăng nhập với bất kỳ vai trò nào, When tự đổi mật khẩu, Then phải nhập đúng mật khẩu hiện tại; mật khẩu mới ngắn hơn 8 ký tự bị từ chối.
