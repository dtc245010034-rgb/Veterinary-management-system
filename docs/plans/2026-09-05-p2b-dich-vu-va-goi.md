# P2b — Dịch vụ, bảng giá và gói dịch vụ

> **Phase:** P2b · **Mốc:** KT2 · **Bắt đầu:** 2026-09-05 · **Trạng thái:** hoàn thành
> Nửa sau của P2, tiếp theo [P2a](2026-09-04-p2a-chu-nuoi-va-thu-cung.md).

## Mục tiêu

Quản lý khai báo được dịch vụ kèm giá và thời lượng, gộp thành gói, và ngưng bán mà không mất dữ
liệu lịch sử. Đây là mảnh cuối của dữ liệu nền trước khi làm lịch hẹn ở P3 — `services.duration_min`
chính là thứ P3 dùng để tính `appointments.end_at`.

**User story:** US-07, US-08, US-09 · **Test case:** TC-024 → TC-031 (8 ca)

## Checklist

- [x] 1. Model `services` + ràng buộc CSDL
- [x] 2. `app/services/catalog.py` — nghiệp vụ dịch vụ, ngưng bán
- [x] 3. Model `service_packages`, `package_items` + nghiệp vụ gói
- [x] 4. Router và giao diện `/services` — chỉ `manager` sửa, hai vai trò kia chỉ xem
- [x] 5. Bổ sung dịch vụ và gói mẫu vào `seed_basic` và `app/seed.py`
- [x] 6. Cập nhật `codebase-map.md`, `test-cases.md`, log phiên
- [x] 7. Báo cáo `testing/reports/`, smoke, commit

## Cách làm

TDD nghiêm ngặt, bốn vòng đỏ–xanh như P2a. Ngoại lệ không áp TDD: template, CSS, `app/seed.py`.

## Quyết định kỹ thuật

### 1. Tiền dùng `Numeric(12, 2)`, tuyệt đối không dùng `float`

`float` là nhị phân, không biểu diễn chính xác được số thập phân — `0.1 + 0.2 != 0.3`. Với tiền,
sai số đó tích lũy qua từng dòng hóa đơn và cuối ngày sổ sách lệch mà không ai lần ra được.

SQLAlchemy `Numeric(12, 2)` ánh xạ sang `decimal.Decimal` trong Python. Lưu ý riêng cho SQLite: nó
không có kiểu số thập phân thật, SQLAlchemy sẽ lưu dạng chuỗi và tự chuyển đổi. Cần một test khẳng
định giá trị đọc ra đúng bằng giá trị ghi vào, và phép cộng nhiều dòng không sinh sai số — nếu sau
này đổi sang PostgreSQL, test đó vẫn giữ nguyên ý nghĩa.

### 2. Ngưng bán bằng cờ `is_active`, không xóa

US-09 yêu cầu dữ liệu lịch sử còn nguyên. Xóa một dịch vụ sẽ kéo theo lịch hẹn và dòng hóa đơn cũ
tham chiếu tới nó. Cùng cách đã dùng cho tài khoản nhân viên ở P1.

Hàm `danh_sach_dang_ban()` là thứ P3 và P5 sẽ gọi khi dựng danh sách chọn; nó lọc theo `is_active`.
Nhờ tách sẵn hàm này, TC-030 kiểm được ngay ở P2b thay vì phải đợi P3.

### 3. Gói dịch vụ: lưu giá gói, không tính lại từ thành phần

Giá gói là một con số do quản lý đặt, thường thấp hơn tổng giá lẻ — đó là lý do bán gói. Tính lại từ
thành phần sẽ làm mất phần chiết khấu. Màn hình chi tiết gói hiển thị **cả hai** con số để quản lý
tự thấy mức giảm.

### 4. Phân quyền: chỉ `manager` sửa bảng giá

Theo bảng phân quyền US-02: dịch vụ và gói — quản lý toàn quyền, lễ tân và nhân viên chăm sóc chỉ
xem. Giống P2a, ẩn nút chưa đủ; phải có test gửi thẳng POST để chứng minh máy chủ cũng chặn.

## Mô hình dữ liệu thêm mới

Theo [`../erd.md`](../erd.md), ba bảng, không thêm cột nào ngoài ERD:

| Bảng | Ràng buộc đáng chú ý |
|---|---|
| `services` | `code` UNIQUE, `price` `Numeric(12,2)` CHECK ≥ 0, `duration_min` CHECK > 0, `is_active` |
| `service_packages` | `price` `Numeric(12,2)` CHECK ≥ 0, `is_active` |
| `package_items` | UNIQUE `(package_id, service_id)`, `quantity` CHECK > 0 |

## Test case và giới hạn của phase này

Ba test case không thể hoàn tất ở P2b vì phụ thuộc hóa đơn (P5). Ghi trước để không tick nhầm:

| TC | Phần làm được ở P2b | Phần chờ phase sau |
|---|---|---|
| TC-024 | Dịch vụ mới nằm trong `danh_sach_dang_ban()` | Hiện trong form đặt lịch — P3 |
| TC-026 | Đổi giá dịch vụ thành công | Hóa đơn cũ giữ giá cũ — **P5** |
| TC-027 | Tạo gói 3 dịch vụ, gói nằm trong danh sách đang bán | Hiện khi lập hóa đơn — **P5** |
| TC-030 | Dịch vụ ngưng bán biến khỏi `danh_sach_dang_ban()` | Biến khỏi form đặt lịch — P3 |
| TC-031 | — | Hóa đơn cũ vẫn hiển thị đủ — **P5** |

TC-025, TC-028, TC-029 hoàn tất trọn vẹn ở phase này.

## Definition of Done

- [x] TC-024, TC-025, TC-028, TC-029, TC-030 ✅; TC-026, TC-027, TC-031 🟡 chờ P5
- [x] `pytest` toàn bộ xanh (166 passed in 12.61s), output sạch, không test nào bị skip
- [x] `codebase-map.md` cập nhật đúng thực tế
- [x] Báo cáo trong [`../testing/reports/`](../testing/reports/) có output pytest thật
- [x] Khối smoke P2 phần dịch vụ tick đủ 11/11 trên trình duyệt thật
- [ ] Bốn ô mới bổ sung cho gói dịch vụ — chưa ai tick, xem “Điều chỉnh” bên dưới

## Ngoài phạm vi

Lịch hẹn (P3). Bán gói và lập hóa đơn (P5). Sau P2b, `/appointments` và `/stats` vẫn trả 404.

## Điều chỉnh so với kế hoạch gốc

Không có điều chỉnh về phạm vi. Hai việc phát sinh, đều ghi ở báo cáo P2b mục 5:

**Một test viết sai** — helper lấy id dịch vụ theo chỉ số trong khi danh sách sắp theo tên, làm số
lượt bị gán ngược. Sửa test, không sửa code.

**Một lỗi trong dữ liệu mẫu** — gói "Combo làm đẹp" đắt hơn tổng giá lẻ. Không test nào đỏ vì hệ
thống xử lý đúng; phát hiện nhờ nhìn con số thật trên trang.

**Checklist smoke P2 thiếu phần gói dịch vụ.** Nó được viết ở P0, trước khi biết gói sẽ trông thế
nào. Đã bổ sung bốn ô: tạo gói và xem tiền tiết kiệm, gói đắt hơn hiện số âm màu đỏ, ngưng bán làm
dòng mờ đi chứ không biến mất, và dịch vụ đã ngưng không còn trong form tạo gói. Bốn ô này **chưa
ai tick** — người dùng đã smoke test trước khi chúng tồn tại.

**Hai ô trong checklist P2 mô tả thứ chưa tồn tại**, đã sửa lại cho khớp thực tế và dời phần chờ
xuống đúng phase:

| Ô gốc | Vấn đề | Xử lý |
|---|---|---|
| "chi tiết thú cưng → thấy lịch sử chăm sóc, lịch tiêm" | Hai thứ đó thuộc P4 | Sửa mô tả; phần chờ dời xuống khối P4 |
| "thêm dịch vụ → xuất hiện trong danh sách chọn khi đặt lịch" | Form đặt lịch thuộc P3 | Sửa thành "xuất hiện trong bảng giá"; phần chờ dời xuống khối P3 |

Đây là lần thứ hai gặp kiểu lỗi này (lần đầu là ô `/stats` ở P1). Nguyên nhân chung: checklist
viết một lần ở P0 mô tả hệ thống hoàn chỉnh, trong khi mỗi phase chỉ dựng được một phần.
