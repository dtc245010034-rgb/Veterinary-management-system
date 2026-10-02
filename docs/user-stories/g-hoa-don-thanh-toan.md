# G. Hóa đơn và thanh toán

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-19 — Lập hóa đơn

#### Mục tiêu

**Là** lễ tân, **tôi muốn** lập hóa đơn từ lịch hẹn đã hoàn thành, **để** thu tiền khách.

#### Tiêu chí chấp nhận

- Given một lịch `done` chưa có hóa đơn, When lập hóa đơn, Then hóa đơn được tạo với dòng dịch vụ tương ứng, đơn giá **chốt tại thời điểm lập**, trạng thái `unpaid`.
- Given hóa đơn có nhiều dòng, When xem tổng tiền, Then tổng bằng đúng tổng các dòng `qty * unit_price`.

#### Điều kiện biên

- Given một lịch chưa `done`, When lập hóa đơn, Then bị từ chối.
- Given một lịch đã có hóa đơn, When lập hóa đơn lần hai, Then bị từ chối.
- Given một lịch đã `cancelled`, When lập hóa đơn, Then bị từ chối kèm lý do nói rõ **buổi đã hủy** — không báo nhầm thành "chưa ghi hồ sơ chăm sóc", vì hai tình huống đó cần hai cách xử lý khác nhau.

> **Ghi chú phạm vi P5, ngày 2026-09-06.** Ở P5 mỗi hóa đơn lập từ đúng một lịch hẹn nên bảng
> `invoice_items` **luôn chỉ có một dòng**: tiêu chí "tổng bằng tổng các dòng" đúng nhưng cộng đúng
> một số hạng, không kiểm được phép cộng nhiều số hạng. Tiêu chí giữ nguyên vì nó vẫn là luật đúng;
> TC-066 thì viết lại cho khớp thứ kiểm được thật — `total_amount` bằng `qty × unit_price` của dòng
> dịch vụ, và không đọc lại `services.price` khi hiển thị. Lý do giữ bảng: xem quyết định 8 trong
> [`plans/2026-09-06-p5-hoa-don-va-thanh-toan.md`](../plans/2026-09-06-p5-hoa-don-va-thanh-toan.md).

### US-20 — Ghi nhận thanh toán

#### Mục tiêu

**Là** lễ tân, **tôi muốn** ghi nhận tiền khách trả, kể cả trả một phần, **để** theo dõi công nợ.

#### Tiêu chí chấp nhận

- Given hóa đơn 500.000đ trạng thái `unpaid`, When ghi nhận thanh toán đủ 500.000đ, Then trạng thái chuyển `paid`.
- Given hóa đơn 500.000đ, When ghi nhận 200.000đ, Then trạng thái chuyển `partial` và còn nợ 300.000đ.
- Given hóa đơn còn nợ 300.000đ, When ghi nhận tiếp 300.000đ, Then trạng thái chuyển `paid` và số nợ bằng 0.

#### Điều kiện biên

- Given hóa đơn 500.000đ, When ghi nhận 600.000đ, Then bị từ chối vì vượt số phải trả.
- Given số tiền thanh toán nhỏ hơn hoặc bằng 0, When ghi nhận, Then bị từ chối.

### US-21 — Chặn hủy lịch đã lập hóa đơn

#### Mục tiêu

**Là** quản lý, **tôi muốn** không cho hủy lịch đã phát sinh hóa đơn, **để** sổ sách không lệch.

#### Tiêu chí chấp nhận

- Given một lịch đã có hóa đơn còn hiệu lực, When hủy lịch, Then bị chặn với thông báo nêu rõ mã hóa đơn liên quan và bảo hủy hóa đơn trước.

#### Điều kiện biên

- Given hóa đơn đó đã bị hủy, When hủy lịch, Then hóa đơn không còn là lý do chặn nữa; lịch được xét theo chính trạng thái của nó.

> **Ghi chú phạm vi P5, ngày 2026-09-07.** Tiêu chí thứ hai viết ở KT1 là *"hóa đơn đã hủy thì hủy
> lịch được chấp nhận"*, khi còn giả định hóa đơn lập được cho lịch chưa xong. Quyết định 1 của P5
> chốt **hóa đơn chỉ lập từ lịch `done`**, mà `done` là cửa một chiều — không đường nào đưa lịch về
> lại `booked`. Nên lịch đã có hóa đơn thì luôn `done`, và luôn bị `huy_lich` từ chối vì trạng thái,
> kể cả sau khi hủy hóa đơn. Tiêu chí được viết lại cho đúng thứ hệ thống bảo đảm thật: hai lớp chặn
> độc lập, lớp hóa đơn nhả ra khi hóa đơn bị hủy, lớp trạng thái vẫn giữ. Cho hủy lịch `done` sẽ để
> lại hồ sơ chăm sóc nói buổi đã diễn ra gắn với một lịch nói không diễn ra — ngoài phạm vi P5.
> Xem [`plans/2026-09-06-p5-hoa-don-va-thanh-toan.md`](../plans/2026-09-06-p5-hoa-don-va-thanh-toan.md).
