# P2a — Chủ nuôi và thú cưng

> **Phase:** P2a · **Mốc:** KT2 · **Duyệt ngày:** 2026-09-04 · **Trạng thái:** hoàn thành
>
> P2 được tách đôi theo yêu cầu: **P2a** chủ nuôi + thú cưng + tra cứu (TC-013→023),
> **P2b** dịch vụ + bảng giá + gói (TC-024→031). Lý do tách: 19 test case và 5 bảng trong một
> phiên là quá lớn để nắn hướng kịp nếu hiểu sai ở phần đầu.
> Theo [`../roadmap.md`](../roadmap.md). Quy ước: [`README.md`](README.md).

## Mục tiêu

Lễ tân thêm, sửa và tra cứu được chủ nuôi cùng thú cưng của họ — kể cả tìm không dấu.

**User story:** US-04, US-05, US-06 · **Test case:** TC-013 → TC-023 (11 ca)

## Checklist

- [x] 1. `app/services/text.py` — chuẩn hóa chuỗi tiếng Việt (nền cho TC-022)
- [x] 2. Model `owners`, `pets` + ràng buộc CSDL
- [x] 3. `app/services/owners.py` — nghiệp vụ chủ nuôi và thú cưng
- [x] 4. CRUD chủ nuôi qua HTTP — TC-013 → TC-016
- [x] 5. CRUD thú cưng qua HTTP — TC-017 → TC-020
- [x] 6. Tra cứu — TC-021 → TC-023
- [x] 7. Bổ sung `seed_basic` và `app/seed.py` dữ liệu mẫu mới
- [x] 8. Cập nhật `codebase-map.md`, `erd.md`, `test-cases.md`, log phiên
- [x] 9. Báo cáo `testing/reports/`, smoke P1+P2a, commit

## Cách làm

TDD nghiêm ngặt như P1 — đỏ trước, xanh sau, log phiên ghi cả hai trạng thái. Sáu vòng, thứ tự theo
checklist: mỗi vòng chỉ cần thứ đã có ở vòng trước.

Ngoại lệ không áp TDD: template và CSS (kiểm bằng smoke checklist), `app/seed.py` (tiện ích dev).

## Quyết định kỹ thuật

### 1. Tìm kiếm không dấu — tự viết hàm chuẩn hóa

TC-022 yêu cầu gõ "mun" ra được thú cưng tên "Mun", "MUN", và gõ "muc" ra "Mực". SQLite không có
`unaccent` như PostgreSQL, và `LIKE` của nó chỉ bỏ phân biệt hoa thường với ASCII.

Cách làm: thêm cột `search_name` lưu sẵn bản đã chuẩn hóa (bỏ dấu, thường hóa), cập nhật mỗi khi
tên đổi, rồi tìm bằng `LIKE` trên cột đó.

```python
# app/services/text.py
def chuan_hoa(s: str) -> str:
    """'Mực' -> 'muc', 'Trần Thị Lễ' -> 'tran thi le'"""
```

Không dùng cách tính lúc truy vấn: SQLite sẽ phải quét toàn bảng và không dùng được index. Lưu sẵn
tốn một cột nhưng tra cứu tại quầy phải nhanh.

Hàm `chuan_hoa` được test riêng ở tầng unit — nó là logic thuần, dễ sai với `đ`/`Đ` (không phải dấu
tổ hợp Unicode nên `unicodedata.normalize` không xử lý được, phải thay tay).

### 2. Chưa tạo `app/schemas/`

Form chủ nuôi có 5 trường, thú cưng có 8 — vẫn đọc thẳng qua `Form()` được. Kiểm tra dữ liệu đặt ở
`app/services/`, nơi test unit gọi trực tiếp được mà không cần HTTP. Thêm tầng Pydantic lúc này chỉ
làm cùng một việc ở hai chỗ.

Xem lại ở P3 nếu form lịch hẹn phức tạp hơn dự kiến.

### 3. Xóa chủ nuôi bị chặn ở tầng nghiệp vụ, không chỉ dựa vào khóa ngoại

TC-016 yêu cầu chặn xóa chủ nuôi còn thú cưng kèm **thông báo dễ hiểu**. Khóa ngoại của SQLite sẽ
ném `IntegrityError` — đúng nhưng người dùng nhận về lỗi 500. Kiểm tra ở `services/` để trả thông
báo tiếng Việt, và giữ khóa ngoại làm lớp chặn cuối.

### 4. Số điện thoại trùng chỉ cảnh báo, không cấm

TC-015 nói "cảnh báo trùng và hỏi có phải khách cũ không". Hai người trong cùng gia đình dùng chung
một số là chuyện thường. Nên `phone` **không** đặt UNIQUE; luồng thêm chủ nuôi hiện cảnh báo kèm
link tới hồ sơ đã có, người dùng tự quyết.

### 5. Giá và tiền: dùng `Numeric`, không dùng `float` — áp dụng từ P2b

`float` làm tròn sai với tiền: `0.1 + 0.2 != 0.3`. SQLAlchemy `Numeric(12, 2)` ánh xạ sang
`decimal.Decimal`. Ghi lại ở đây để không quên; `services.price` ở P2b là nơi đầu tiên có tiền.

## Mô hình dữ liệu thêm mới

Theo [`../erd.md`](../erd.md). Hai bảng, thêm một cột ngoài ERD:

| Bảng | Ghi chú |
|---|---|
| `owners` | Thêm `search_name` — không có trong ERD gốc, cần cho TC-022. Sẽ cập nhật ERD |
| `pets` | Thêm `search_name`. `birth_date` CHECK ≤ hôm nay, `weight_kg` CHECK > 0 |

`services`, `service_packages`, `package_items` thuộc P2b.

## Definition of Done

- [x] TC-013→019, TC-021→023 chuyển ✅; TC-020 🟡 một phần (chờ P4) trong [`../testing/test-cases.md`](../testing/test-cases.md)
- [x] `pytest` toàn bộ xanh (114 passed in 8.93s), output sạch, không test nào bị skip
- [x] Phần chủ nuôi / thú cưng của khối smoke P2 tick đủ, cùng toàn bộ khối P1 (hồi quy thủ công)
- [x] `codebase-map.md` và `erd.md` (cột `search_name`) cập nhật đúng thực tế
- [x] Báo cáo trong [`../testing/reports/`](../testing/reports/) có output pytest thật

## Ngoài phạm vi

Dịch vụ, bảng giá, gói dịch vụ (P2b). Lịch hẹn (P3). Hồ sơ chăm sóc và tiêm phòng (P4).

Sau P2a, menu `/services`, `/stats`, `/appointments` vẫn trả 404.

## Điều chỉnh so với kế hoạch gốc

**Thêm `app/models/__init__.py` và `app/services/errors.py`** — không có trong kế hoạch. Cái đầu
cần vì `create_all` chỉ tạo bảng đã được import; cái sau để router phân biệt lỗi nghiệp vụ với lỗi
CSDL và trả thông báo tiếng Việt thay vì lỗi 500.

**Bỏ CHECK `birth_date ≤ hôm nay` khỏi CSDL**, chuyển lên tầng services. CHECK của SQLite phải gọi
`date('now')` là ngày thật của hệ thống, bỏ qua `app/services/clock.py` và làm test không cố định
được thời gian. Đã ghi lý do vào `erd.md`.

**Thêm tham số cấu hình `BCRYPT_ROUNDS`** — không có trong kế hoạch. Tầng integration chạm 43,71s,
vượt ngân sách 30s, vì mỗi test đăng nhập tốn một lần bcrypt. Xem báo cáo P2a mục 4.

**TC-020 chỉ đạt một phần**, phần lịch sử chăm sóc và lịch tiêm chờ P4.
