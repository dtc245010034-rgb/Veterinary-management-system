# B. Chủ nuôi và thú cưng

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-04 — Quản lý chủ nuôi

#### Mục tiêu

**Là** lễ tân, **tôi muốn** thêm, sửa, xem thông tin chủ nuôi, **để** liên hệ và tra cứu khi khách đến.

#### Tiêu chí chấp nhận

- Given form thêm chủ nuôi, When nhập họ tên và số điện thoại hợp lệ, Then chủ nuôi được lưu và hiện trong danh sách.
- Given một chủ nuôi đã lưu, When sửa họ tên, số điện thoại, email, địa chỉ hoặc ghi chú, Then thông tin mới hiện ngay trên trang chi tiết; bỏ trống họ tên hoặc số điện thoại thì bị từ chối.

#### Điều kiện biên

- Given form thêm chủ nuôi, When bỏ trống họ tên hoặc số điện thoại, Then bị từ chối kèm thông báo trường bắt buộc.
- Given số điện thoại đã tồn tại trong hệ thống, When thêm chủ nuôi mới cùng số đó, Then cảnh báo trùng và hỏi có phải khách cũ không.
- Given chủ nuôi đang có thú cưng, When xóa chủ nuôi, Then bị chặn với thông báo phải xử lý thú cưng trước.
- Given số điện thoại không phải số Việt Nam 10 chữ số, When lưu chủ nuôi, Then bị từ chối; số gõ dạng `+84` hay `84`, hoặc có dấu cách, chấm, gạch, được **chuẩn hóa về 10 chữ số trước khi lưu và trước khi kiểm trùng**, nên `+84912345678` và `0912345678` là cùng một khách.
- Given email sai định dạng, When lưu chủ nuôi, Then bị từ chối; ô email **để trống vẫn hợp lệ** vì đây không phải trường bắt buộc.
- Given họ tên, địa chỉ hoặc ghi chú dài quá trần của ô đó, When lưu chủ nuôi, Then bị từ chối kèm thông báo nêu rõ trần — SQLite không tự ép độ dài nên đây là ràng buộc thật sự duy nhất.
- Given bất kỳ phép kiểm nào ở trên, When **sửa** chủ nuôi thay vì thêm mới, Then luật áp dụng y như nhau.

### US-05 — Quản lý thú cưng

#### Mục tiêu

**Là** lễ tân, **tôi muốn** quản lý thú cưng gắn với chủ nuôi, **để** biết đang chăm sóc con vật nào của ai.

#### Tiêu chí chấp nhận

- Given một chủ nuôi đã tồn tại, When thêm thú cưng với tên, loài, giống, ngày sinh, Then thú cưng hiện trong danh sách thú cưng của chủ nuôi đó.
- Given một thú cưng đã lưu, When sửa tên, loài, giống, giới tính, ngày sinh hoặc cân nặng, Then thông tin mới hiện ngay; các phép kiểm ngày sinh và cân nặng áp dụng y như lúc thêm mới.
- Given một thú cưng, When mở trang chi tiết, Then thấy thông tin chủ nuôi, lịch sử chăm sóc và lịch tiêm.

#### Điều kiện biên

- Given form thêm thú cưng, When nhập ngày sinh ở tương lai, Then bị từ chối.
- Given form thêm thú cưng, When nhập cân nặng âm hoặc bằng 0, Then bị từ chối.
- Given cân nặng quá 200 kg hoặc ngày sinh cách nay quá 40 năm, When lưu thú cưng, Then bị từ chối — đây là chặn số gõ nhầm, không phải giới hạn sinh học.
- Given giới tính không nằm trong danh sách cho phép, When lưu thú cưng, Then bị từ chối; ô chọn trên giao diện **dựng từ chính danh sách đó** nên giao diện và phép kiểm không thể lệch nhau.

### US-06 — Tra cứu nhanh

#### Mục tiêu

**Là** lễ tân, **tôi muốn** tìm chủ nuôi hoặc thú cưng theo tên hoặc số điện thoại, **để** phục vụ khách ngay tại quầy.

#### Tiêu chí chấp nhận

- Given khách đọc số điện thoại, When tìm theo số đó, Then thấy chủ nuôi kèm danh sách thú cưng.
- Given tìm theo một phần tên thú cưng, When gõ "mun", Then thấy mọi thú cưng có tên chứa "mun", không phân biệt hoa thường và dấu.

#### Điều kiện biên

- Given từ khóa không khớp gì, When tìm, Then hiện trạng thái rỗng có hướng dẫn, không phải trang trắng hay lỗi.
