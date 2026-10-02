# F. Tiêm phòng (mức thông tin)

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

### US-17 — Ghi nhận mũi tiêm và hạn nhắc lại

#### Mục tiêu

**Là** lễ tân, **tôi muốn** ghi lại mũi tiêm đã tiêm và ngày cần nhắc lại, **để** nhắc khách đúng hạn.

#### Tiêu chí chấp nhận

- Given một thú cưng, When ghi mũi tiêm với tên vắc-xin, ngày tiêm và ngày nhắc lại, Then bản ghi hiện trong hồ sơ tiêm của thú cưng.

#### Điều kiện biên

- Given ngày nhắc lại sớm hơn ngày tiêm, When lưu, Then bị từ chối.
- Given ngày tiêm ở tương lai, When lưu, Then bị từ chối.

### US-18 — Danh sách đến hạn tiêm

#### Mục tiêu

**Là** lễ tân, **tôi muốn** xem thú cưng sắp hoặc đã quá hạn tiêm, **để** chủ động gọi nhắc khách.

#### Tiêu chí chấp nhận

- Given nhiều thú cưng có `next_due_at` khác nhau, When mở danh sách đến hạn, Then thấy mọi thú cưng có hạn **từ quá khứ tới hôm nay + 30 ngày**, sắp xếp theo hạn tăng dần; thú cưng có hạn xa hơn 30 ngày không hiện.
- Given một thú cưng đã quá hạn tiêm, When xem danh sách, Then bản ghi được đánh dấu quá hạn rõ ràng.

#### Điều kiện biên

- Given một thú cưng đã tiêm mũi tiếp theo của **cùng loại vắc-xin**, When xem danh sách, Then chỉ mũi mới nhất được tính; hạn của mũi cũ đã hoàn thành nên không hiện nữa.
- Given không thú cưng nào đến hạn, When xem, Then hiện trạng thái rỗng.

> **Sửa spec lần hai, ngày 2026-09-05 (P4 chặng 2).** Thêm tiêu chí "chỉ tính mũi mới nhất của
> mỗi loại vắc-xin". Bản gốc chỉ nói "mọi thú cưng có hạn trong khoảng", mà hiểu đúng từng chữ thì
> mũi 1 tiêm năm ngoái với hạn nhắc đã qua sẽ nằm lì trong danh sách quá hạn **vĩnh viễn**, kể cả
> khi mũi 2 đã tiêm đúng hạn. Lời nhắc đã hoàn thành mà không bao giờ tắt được thì cả danh sách
> mất tác dụng. Phát hiện lúc thiết kế chặng 2, sửa trước khi viết code.
>
> **Sửa spec lần một, ngày 2026-09-05 (P4).** Bản gốc viết "chỉ thấy thú cưng có hạn nằm trong 30 ngày tới",
> mâu thuẫn với chính tiêu chí ngay dưới nó: nếu chỉ lấy khoảng tương lai thì không bản ghi quá hạn
> nào lọt vào để mà đánh dấu, và thú cưng quá hạn biến mất khỏi màn hình đúng lúc cần gọi nhắc nhất.
> Khoảng lấy đổi thành mở về phía quá khứ. Sửa công khai ở đây thay vì lặng lẽ code khác spec.

> Đây là chức năng **thông tin**, không phải chỉ định y tế. Màn hình phải ghi rõ lịch tiêm cụ thể do
> bác sĩ thú y quyết định.
