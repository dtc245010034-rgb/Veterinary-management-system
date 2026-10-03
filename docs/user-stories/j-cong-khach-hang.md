# J. Cổng khách hàng

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

**Nhóm này nằm ngoài đề bài gốc** — đề bài chỉ có ba vai trò nhân viên. Cổng khách là phần mở rộng của phase P9
([kế hoạch](../plans/2026-09-25-p9-cong-khach-hang.md)), viết **sau khi** đã cài đặt từng chặng, nên mỗi tiêu chí dưới
đây đều truy được tới test có thật (cột **US** của mục S → X trong `test-cases.md`).

**Vai trò mới:** `khach` — chủ nuôi tự đăng ký tài khoản. Khách ở **bảng riêng `customers`**, không phải `users`, và
cookie phiên riêng: không có đường nào để cookie khách trở thành người dùng nhân viên.

**Ba nguyên tắc xuyên suốt nhóm này:**

1. **Khách chỉ thấy dữ liệu của chính mình.** Id của người khác và id không tồn tại cho **cùng một** phản hồi 404, từng
   chữ — khách không dò được id nào có thật.
2. **Khách không tự nhận hồ sơ.** Tài khoản mới chưa thấy gì cho tới khi **lễ tân duyệt** việc nối với hồ sơ chủ nuôi.
3. **Mọi việc khách xin đều do nhân viên chốt.** Lịch khách xin chỉ thành lịch hẹn sau khi lễ tân duyệt.

### US-29 — Khách đăng ký tài khoản bằng email

#### Mục tiêu

**Là** chủ nuôi, **tôi muốn** tự đăng ký tài khoản bằng email, **để** xem thú cưng và lịch hẹn của mình mà không phải gọi cửa hàng.

#### Tiêu chí chấp nhận

- Given email chưa có tài khoản, When đăng ký, Then hệ thống gửi đúng một thư chứa liên kết xác minh và **chưa** tạo dòng nào trong `customers`.
- Given liên kết trong thư còn hạn (24 giờ), When khách mở liên kết, đặt họ tên và mật khẩu hợp lệ, Then tài khoản được tạo và khách vào thẳng cổng khách.
- Given liên kết dựng từ `APP_ORIGIN`, When thư được gửi qua một proxy có `Host` giả, Then liên kết trong thư vẫn trỏ về địa chỉ công khai thật.

#### Điều kiện biên

- Given email đã có tài khoản, When đăng ký, Then phản hồi **giống từng chữ** với email mới (không lộ email nào đã đăng ký), **không** tạo dòng thứ hai và gửi thư báo không kèm liên kết.
- Given liên kết đã dùng, hết hạn, sai mục đích hay bịa ra, When mở hoặc gửi, Then cùng một thông báo 400; chỉ `POST` mới đốt token, mở liên kết bằng `GET` thì không.
- Given họ tên trống hoặc mật khẩu ngắn hơn 8 ký tự, When đặt mật khẩu, Then bị từ chối **trước khi** đốt token để khách sửa lại được.
- Given một IP đăng ký liên tiếp quá số lần cho phép, When gửi tiếp, Then bị 429 kèm `Retry-After`.
- Given lỗi gửi thư, When đăng ký, Then khách vẫn nhận phản hồi như thành công và lỗi không lộ ra ngoài.

### US-30 — Khách đăng nhập, đăng xuất và lấy lại mật khẩu

#### Mục tiêu

**Là** chủ nuôi, **tôi muốn** đăng nhập, đổi và lấy lại mật khẩu của riêng mình, **để** tài khoản không bị người khác dùng.

#### Tiêu chí chấp nhận

- Given tài khoản khách hợp lệ, When đăng nhập đúng email và mật khẩu, Then vào `/khach` và cookie phiên khách được cấp.
- Given khách quên mật khẩu, When xin đặt lại, Then nhận thư có liên kết hiệu lực 1 giờ và đặt được mật khẩu mới.
- Given khách đã đăng nhập, When đổi mật khẩu đúng mật khẩu cũ, Then mật khẩu mới có hiệu lực và mọi phiên cũ bị thu hồi.
- Given khách đăng nhập, When đăng xuất, Then cookie cũ không còn dùng được.

#### Điều kiện biên

- Given sai mật khẩu hoặc email lạ, When đăng nhập, Then cùng một thông báo, không lộ email có tồn tại; tài khoản bị khóa không vào được.
- Given một IP đăng nhập hoặc xin đặt lại sai liên tiếp, When vượt ngưỡng, Then bị 429 kèm `Retry-After`; ba bộ đếm (đăng ký, quên mật khẩu, đăng nhập) tách nhau và tách khỏi đăng nhập nhân viên.
- Given cookie khách, When mở route nhân viên (`/owners`, `/invoices`), Then bị đưa về trang đăng nhập nhân viên; cookie nhân viên mở `/khach` cũng bị đưa về đăng nhập khách.
- Given một trình duyệt đang giữ phiên bên này, When đăng nhập bên kia, Then phiên bên này bị xóa: **một cookie không mang hai danh tính**.
- Given cổng chạy công khai (`SESSION_HTTPS_ONLY`), When khởi động với `MAIL_PROVIDER=console` hoặc thiếu `APP_ORIGIN`, Then ứng dụng từ chối khởi động (liên kết xác minh không được nằm trong log).

### US-31 — Khách liên kết tài khoản với hồ sơ chủ nuôi

#### Mục tiêu

**Là** chủ nuôi, **tôi muốn** xin nối tài khoản của mình với hồ sơ tại cửa hàng, **để** thấy đúng thú cưng và lịch hẹn của mình.

#### Tiêu chí chấp nhận

- Given khách chưa nối hồ sơ, When gửi số điện thoại và ghi chú, Then tạo một yêu cầu `pending` và khách thấy trạng thái "đang chờ".
- Given yêu cầu đang chờ, When lễ tân chọn đúng hồ sơ chủ nuôi (kể cả hồ sơ mang số khác số khách nhập) và duyệt, Then tài khoản khách được nối và trang chủ khách chuyển sang "đã liên kết".
- Given yêu cầu đang chờ, When lễ tân từ chối kèm lý do, Then khách đọc được lý do và gửi được yêu cầu mới.
- Given khách đã liên kết, When lễ tân gỡ liên kết, Then khách về lại "chưa liên kết" và hồ sơ nối lại được cho khách khác.

#### Điều kiện biên

- Given số khách nhập trùng một chủ nuôi thật, When gửi yêu cầu, Then **không** tự nối, và phản hồi giống từng chữ với số lạ (khách không dùng được màn này để dò số điện thoại).
- Given số sai định dạng, ghi chú quá 500 ký tự, khách đã nối hoặc đang có yêu cầu chờ, When gửi, Then bị từ chối.
- Given hồ sơ đã thuộc khách khác, When lễ tân duyệt cho khách thứ hai, Then bị chặn và không đổi gì; duyệt hai lần hoặc duyệt yêu cầu đã từ chối cũng bị chặn.
- Given từ chối không có lý do (trống, chỉ khoảng trắng, quá dài), When gửi, Then bị chặn.
- Given `caretaker`, When mở bốn route duyệt, Then 403; khách đã đăng nhập mở hoặc POST vào màn lễ tân thì bị đưa về `/login` và không tự duyệt cho mình.
- Given chủ nuôi đang nối với tài khoản khách, When xóa hồ sơ chủ nuôi, Then bị chặn kèm thông báo.

### US-32 — Khách xem thú cưng, lịch hẹn và hóa đơn của mình

#### Mục tiêu

**Là** chủ nuôi đã liên kết, **tôi muốn** xem thú cưng, lịch hẹn và hóa đơn của mình, **để** nắm lịch chăm sóc và khoản còn nợ.

#### Tiêu chí chấp nhận

- Given khách đã liên kết, When mở danh sách, Then chỉ thấy thú cưng, lịch hẹn và hóa đơn thuộc chủ nuôi đã nối, đúng thứ tự.
- Given một thú cưng của khách, When mở chi tiết, Then thấy lịch sử tiêm phòng và lịch hẹn của thú cưng đó.
- Given một hóa đơn của khách, When mở chi tiết, Then thấy tổng tiền, đã trả và còn nợ.

#### Điều kiện biên

- Given id thú cưng, hóa đơn hay lịch hẹn của người khác, When mở, Then 404 **giống hệt** id không tồn tại; không bao giờ 200 hay 500.
- Given khách chưa liên kết hoặc vừa bị gỡ liên kết, When mở bất kỳ trang dữ liệu nào, Then danh sách rỗng, mở chi tiết là 404 kể cả với id đúng; hiệu lực ngay ở yêu cầu kế tiếp.
- Given mọi trang cổng khách, When kiểm nội dung, Then không lộ ghi chú nội bộ (`note` của thú cưng / lịch / tiêm / hóa đơn), `cancel_reason` của lịch nhân viên đặt, hồ sơ chăm sóc, tên nhân viên, địa chỉ hay thông tin chủ nuôi khác.
- Given người chưa đăng nhập hoặc nhân viên đã đăng nhập, When mở `/khach/*`, Then bị đưa về `/khach/dang-nhap`.

### US-33 — Khách xem giờ trống của nhân viên

#### Mục tiêu

**Là** chủ nuôi đã liên kết, **tôi muốn** xem nhân viên nào còn trống giờ nào cho thú cưng và dịch vụ tôi chọn, **để** xin đúng giờ mà không phải hỏi cửa hàng.

#### Tiêu chí chấp nhận

- Given khách chọn thú cưng, dịch vụ và ngày, When xem giờ trống, Then các khung giờ được nhóm theo nhân viên đang hoạt động, bước 30 phút trong giờ mở cửa.
- Given một khung giờ, When khách bấm vào, Then form xin đặt lịch được điền sẵn thú cưng, dịch vụ, nhân viên, ngày và giờ đó.
- Given lịch chờ duyệt của khách khác, When tính khung trống, Then khung đó vẫn bị giữ chỗ (không hiện).

#### Điều kiện biên

- Given ngày đã qua, When xem giờ trống, Then danh sách rỗng, không lỗi.
- Given ngày sai định dạng, When xem, Then 400 kèm thông báo; không có tham số thì chỉ hiện form.
- Given dịch vụ đã ngưng bán hoặc không tồn tại, When xem, Then báo lỗi nghiệp vụ (ngưng bán) hoặc 404 (không có).
- Given thú cưng của người khác hoặc id không tồn tại, When xem, Then cùng một 404 từng chữ; khách chưa liên kết cũng 404.
- Given trang giờ trống, When kiểm nội dung, Then không có tên thú cưng, chủ nuôi hay số điện thoại của người khác, và ký tự đặc biệt được thoát.

### US-34 — Khách xin đặt lịch

#### Mục tiêu

**Là** chủ nuôi đã liên kết, **tôi muốn** xin một lịch chăm sóc trực tiếp trên cổng, **để** đặt lịch ngoài giờ làm việc của cửa hàng.

#### Tiêu chí chấp nhận

- Given khách chọn thú cưng, dịch vụ, nhân viên, ngày giờ hợp lệ, When gửi, Then tạo lịch trạng thái `pending` gắn tài khoản khách và lịch hiện "Chờ duyệt" cho cả khách lẫn lễ tân.
- Given lịch `pending`, When tính trùng lịch, Then **giữ chỗ**: chặn trùng nhân viên và trùng thú cưng, hai khách xin cùng khung thì người đến sau bị chặn.
- Given lịch `pending` quá 24 giờ chưa ai duyệt, When tính trùng lịch, Then hết giữ chỗ (không cần ai quét) và lịch chuyển `cancelled` khi bị quét.

#### Điều kiện biên

- Given khách đang có 3 lịch chờ duyệt, When xin lịch thứ tư, Then bị chặn kèm thông báo "tối đa"; đếm riêng từng khách và lịch hết hạn không tính.
- Given giờ ngoài giờ mở cửa hoặc đã qua, When gửi, Then bị từ chối bằng đúng phép kiểm của lễ tân.
- Given ngày giờ sai định dạng, When gửi, Then 400 và giữ lại các ô đã nhập.
- Given thú cưng của người khác hoặc id không tồn tại, When gửi, Then cùng một 404 và **không** tạo lịch; khách chưa liên kết không xin được.
- Given lịch `pending`, When lập hóa đơn hoặc ghi hồ sơ chăm sóc (dù giờ hẹn đã qua), Then bị chặn với thông báo "chờ duyệt".

### US-35 — Lễ tân duyệt hoặc từ chối lịch khách xin

#### Mục tiêu

**Là** lễ tân, **tôi muốn** duyệt hoặc từ chối lịch khách tự xin, **để** cửa hàng vẫn là bên quyết định lịch làm việc.

#### Tiêu chí chấp nhận

- Given lịch `pending` còn hạn, When lễ tân duyệt, Then lịch thành `booked`, ghi người duyệt, và hiện "Đã đặt" trên lưới lịch.
- Given lịch `pending`, When lễ tân từ chối kèm lý do, Then lịch thành `cancelled`, khung giờ được trả lại và khách đọc được lý do.
- Given màn lịch chờ duyệt, When mở, Then chỉ có lịch còn hạn, sớm nhất trước.

#### Điều kiện biên

- Given giờ hẹn đã qua, nhân viên bị khóa, lịch đã quá hạn hoặc không còn `pending`, When duyệt, Then bị chặn (lịch quá hạn thành `cancelled`); trên giao diện là 400, không bao giờ 500.
- Given từ chối không có lý do (rỗng, toàn dấu cách), When gửi, Then bị chặn.
- Given `caretaker`, When mở màn duyệt, Then 403; khách và người chưa đăng nhập bị đưa về trang đăng nhập tương ứng.
- Given lịch nhân viên đặt có lý do hủy nội bộ, When khách xem lịch của mình, Then lý do đó **không** hiện.

### US-36 — Khách hỏi đáp chăm sóc với AI

#### Mục tiêu

**Là** chủ nuôi đã đăng nhập, **tôi muốn** hỏi AI những việc chăm sóc thường ngày, **để** có câu trả lời tham khảo nhanh. Đây là phía khách của [US-26](i-chuc-nang-ai.md) và [US-28](i-chuc-nang-ai.md); khách **chỉ** có hỏi đáp, không có nhắc lịch hay tóm tắt hồ sơ vì hai tính năng đó đọc dữ liệu chủ nuôi.

#### Tiêu chí chấp nhận

- Given câu hỏi chăm sóc thông thường, When gửi, Then chuyển sang trang kết quả có câu hỏi, câu trả lời và câu khuyến cáo bác sĩ thú y; tải lại trang kết quả không gọi AI thêm.
- Given trang hỏi, When mở, Then luôn có dòng cảnh báo cố định (AI không chẩn đoán, không tư vấn thuốc) và số lượt còn lại hôm nay — hiện **kể cả khi** AI lỗi hoặc hết lượt.
- Given câu hỏi, When dựng prompt gửi AI, Then **chỉ nội dung câu hỏi** đi sang AI — không tên khách, email, tên chủ nuôi hay thú cưng.
- Given câu xin thuốc hoặc phản hồi lộ liều, When xử lý, Then câu xin thuốc bị chặn **trước khi** gọi API, và phản hồi lộ liều bị thay cả đoạn.

#### Điều kiện biên

- Given khách đã hỏi đủ `AI_KHACH_TOI_DA_MOI_NGAY` lượt (mặc định 10) trong ngày, When hỏi tiếp, Then 429, **không gọi API và không ghi thêm log**; sang ngày mới hỏi lại được và khách khác không bị ảnh hưởng.
- Given câu xin thuốc, When hỏi, Then vẫn tính một lượt (chặn bơm log); câu gặp lỗi AI thì không tính lượt và giữ lại câu đã gõ.
- Given câu rỗng hoặc dài quá 1.000 ký tự, When gửi, Then 400, không gọi API, không ghi log.
- Given kết quả AI của khách khác, của nhân viên hoặc id không tồn tại, When mở, Then cùng một 404 từng chữ.
- Given cookie nhân viên hoặc chưa đăng nhập, When mở `/khach/hoi-dap`, Then bị đưa về `/khach/dang-nhap`.
- Given khách chưa liên kết hồ sơ, When hỏi, Then vẫn hỏi được (câu hỏi không dùng dữ liệu hồ sơ).
