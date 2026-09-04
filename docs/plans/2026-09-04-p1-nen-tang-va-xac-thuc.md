# P1 — Nền tảng, đăng nhập và phân quyền

> **Phase:** P1 · **Mốc:** KT2 · **Bắt đầu:** 2026-09-04
> Theo [`../roadmap.md`](../roadmap.md). Quy ước lưu kế hoạch: [`README.md`](README.md).

## Mục tiêu

Dựng nền tảng chạy được của ứng dụng và hoàn thành nhóm A của đặc tả: đăng nhập, phân quyền 3 vai
trò, quản lý tài khoản nhân viên. Kết thúc phase, hệ thống đăng nhập được bằng 3 vai trò và mỗi vai
trò chỉ thấy phần việc của mình.

**User story:** US-01, US-02, US-03 · **Test case:** TC-001 → TC-012

## Checklist

- [x] 0. Môi trường: `.venv`, `requirements.txt`, `pytest.ini`
- [x] 1. `app/security.py` — băm mật khẩu (TC-005)
- [x] 2. `app/services/clock.py` — điểm lấy thời gian duy nhất
- [x] 3. `app/config.py`, `app/db.py`, `app/models/user.py`
- [x] 4. `tests/conftest.py` — 5 fixture
- [x] 5. Đăng nhập (TC-001 → TC-004)
- [x] 6. Phân quyền theo vai trò (TC-007, TC-008 — TC-006 và TC-009 hoãn, xem cuối file)
- [x] 7. Quản lý tài khoản nhân viên (TC-010 → TC-012)
- [x] 8. Giao diện: layout chung, trang đăng nhập, trang chủ, trang 403
- [x] 9. Cập nhật `codebase-map.md`, `test-cases.md`, log phiên
- [x] 10. Báo cáo `testing/reports/`, smoke checklist P1, commit

## Cách làm: TDD nghiêm ngặt

Theo luật 2 trong [`../../CLAUDE.md`](../../CLAUDE.md) mục 7 — **đỏ trước, xanh sau**. Mỗi vòng:

1. Viết một test cho một hành vi
2. Chạy, **xác nhận đỏ** và đỏ đúng lý do (thiếu tính năng, không phải lỗi gõ)
3. Viết code tối thiểu để xanh
4. Chạy lại, xác nhận xanh và không làm đỏ test cũ

Log phiên ghi lại cả hai trạng thái của từng vòng.

**Ngoại lệ có chủ đích:** `requirements.txt`, `pytest.ini`, `.venv` là cấu hình môi trường, không
phải logic nghiệp vụ — không áp TDD. `app/config.py` chỉ đọc biến môi trường, cũng vậy. Mọi thứ còn
lại đều bắt đầu bằng một test đỏ.

## Thứ tự vòng TDD

Thứ tự này chọn để mỗi vòng chỉ cần thứ đã có ở vòng trước, không phải dựng sẵn hạ tầng rồi mới test.

| Vòng | Hành vi | Test | Sinh ra |
|---|---|---|---|
| 1 | Băm mật khẩu, không lưu bản gốc | TC-005 | `app/security.py` |
| 2 | Thời gian lấy qua một hàm, cố định được khi test | — | `app/services/clock.py` |
| 3 | Tạo `users` với `role` hợp lệ; `username` UNIQUE | TC-011 (phần model) | `app/db.py`, `app/models/user.py` |
| 4 | Đăng nhập đúng / sai / bị khóa / chưa đăng nhập | TC-001→004 | `app/main.py`, `app/config.py`, `app/routers/auth.py` |
| 5 | Chặn theo vai trò, `caretaker` chỉ thấy phần mình | TC-006→009 | `app/security.py` (dependency), `app/routers/` |
| 6 | Tạo / trùng tên / khóa tài khoản | TC-010→012 | `app/routers/users.py` |

Vòng 2 làm sớm dù chưa có test case nào yêu cầu, vì lý do đã ghi trong log phiên P0: để sau thì mọi
chỗ đã gọi `datetime.now()` trực tiếp đều phải sửa lại, và các ca test phụ thuộc ngày ở P3, P4 sẽ
không viết ổn định được.

## Fixture cần có (`tests/conftest.py`)

Theo [`../testing/test-strategy.md`](../testing/test-strategy.md) mục 5:

| Fixture | Nội dung |
|---|---|
| `db` | `Session` trên SQLite in-memory, tạo bảng mới mỗi test |
| `client` | `TestClient` với `get_db` override sang `db` |
| `fake_ai` | `FakeProvider` ghi lại `(system, user)` — **dựng khung ở P1, dùng thật ở P7** |
| `frozen_clock` | Cố định "bây giờ" |
| `seed_basic` | 1 manager, 1 receptionist, 2 caretaker |

`seed_basic` ở P1 chỉ tạo tài khoản; owner/pet/service thêm vào ở P2 khi các model đó tồn tại.

## Quyết định kỹ thuật

**Băm mật khẩu: dùng `bcrypt` trực tiếp, không qua `passlib`.** `passlib` 1.7.4 lỗi tương thích với
`bcrypt` 4.x và đã lâu không cập nhật. Gọi thẳng `bcrypt` ít phụ thuộc hơn và đủ dùng — hệ thống chỉ
cần băm và kiểm tra mật khẩu.

**Phiên đăng nhập: session cookie qua `SessionMiddleware` của Starlette**, không dùng JWT. Ứng dụng
server-rendered, không có client tách rời, nên JWT chỉ thêm phức tạp mà không giải quyết vấn đề nào.

**Phân quyền: FastAPI dependency, không phải decorator.** `require_role("manager")` trả về dependency
kiểm tra vai trò trong session; router khai báo qua `Depends`. Cách này test được độc lập và hiện
trong OpenAPI schema.

## Definition of Done

- [x] TC-001→005, TC-007, TC-008, TC-010→012 chuyển ✅ (10/12; TC-006 và TC-009 hoãn) trong [`../testing/test-cases.md`](../testing/test-cases.md)
- [x] `pytest tests/unit` và `pytest tests/integration` xanh, output sạch
- [x] Đăng nhập được bằng cả 3 vai trò trên trình duyệt thật
- [x] Khối smoke P1 trong [`../testing/smoke-checklist.md`](../testing/smoke-checklist.md) tick đủ 8/8
- [x] `codebase-map.md` cập nhật đúng file thực tế
- [x] Báo cáo trong [`../testing/reports/`](../testing/reports/) có output pytest thật

## Ngoài phạm vi

Chủ nuôi, thú cưng, dịch vụ (P2). Lịch hẹn (P3). Mọi thứ liên quan AI trừ khung `FakeProvider` trong
conftest (P7).

## Điều chỉnh so với kế hoạch gốc

**TC-006 và TC-009 hoãn sang P6 và P3.** Kế hoạch gốc xếp cả 12 test case của nhóm A vào P1, nhưng
TC-006 cần trang thống kê và TC-009 cần bảng lịch hẹn — cả hai đều thuộc phase sau. Làm bây giờ sẽ
phải tạo route rỗng chỉ để có chỗ gắn test. Cơ chế phân quyền dùng chung đã được kiểm qua `/users`.

**Không tạo `app/schemas/`.** Form của P1 chỉ có 4 trường, đọc thẳng qua `Form()` là đủ; thêm một
tầng Pydantic lúc này là trừu tượng cho code dùng một lần. Cân nhắc lại ở P2 khi chủ nuôi và thú
cưng có nhiều trường cần kiểm tra hơn.

**Thêm `app/seed.py` và `app/templates.py`** — không có trong kế hoạch gốc. `seed.py` cần để chạy
thử được ứng dụng; `templates.py` để cấu hình Jinja2 ở một chỗ thay vì lặp trong từng router.

**Smoke test bằng mắt do người dùng chạy tay**, vì Chrome extension chưa kết nối. Đã tick đủ 8/8.
Một ô phải sửa mô tả cho khớp thực tế: `/stats` chưa có ở P1 nên ô đó chuyển sang `/users`, và ô
`/stats` dời xuống khối P6 cùng TC-006.
