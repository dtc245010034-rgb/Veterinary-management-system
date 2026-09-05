# Bản đồ mã nguồn

> **File này bắt buộc cập nhật mỗi khi thêm, xóa hoặc đổi vai trò một file.** Đây là thứ đầu tiên
> agent đọc ở mỗi phiên làm việc (xem [`../CLAUDE.md`](../CLAUDE.md) mục 6). Bản đồ lệch thực tế thì
> phiên sau sẽ làm việc dựa trên thông tin sai.

**Cập nhật lần cuối:** 2026-09-05 (phase P3 chặng 1) · **Trạng thái:** đặt lịch và chống trùng lịch chạy được; đổi/hủy lịch ở chặng 2

---

## Hiện có

### Gốc dự án

| File | Vai trò |
|---|---|
| `CLAUDE.md` | Nguyên tắc làm việc + ngữ cảnh dự án + quy trình mỗi phiên + luật kiểm thử |
| `đề-bài.md` | Đề bài gốc của môn học. **Không sửa** |
| `README.md` | Giới thiệu, cách chạy, cách chạy test |
| `.gitignore` | Bỏ qua `.venv`, `__pycache__`, `*.db`, `.env`, `.claude/settings.local.json` |
| `.env.example` | Mẫu biến môi trường. `.env` thật không vào repo |

### `.claude/` — cấu hình agent, nằm trong repo

| File | Vai trò |
|---|---|
| `settings.json` | Đăng ký hook `SessionStart` và `Stop`. **Được commit** |
| `hooks/session-start.ps1` | Tạo `docs/sessions/YYYY-MM-DD-NN.md`, in nhắc nhở, cảnh báo nếu sai thư mục làm việc |
| `hooks/session-stop.ps1` | Xóa file log rỗng, nhắc cập nhật codebase-map và checklist plan |

### `docs/`

| File | Vai trò |
|---|---|
| `user-stories.md` | 28 user story, 98 tiêu chí Given/When/Then, bảng đối chiếu với đề bài |
| `erd.md` | 13 bảng, sơ đồ Mermaid, mô tả cột và ràng buộc |
| `architecture.md` | Cây thư mục, ranh giới ba lớp, 3 sequence diagram, cách xử lý lỗi |
| `ai-safety.md` | System prompt 3 tính năng, `DISCLAIMER`, 20 ca guardrail G-01→G-20 |
| `codebase-map.md` | File này |
| `roadmap.md` | Lộ trình P0→P8 gắn với mốc KT1/KT2/KT3/cuối kỳ, kèm Definition of Done |
| `plans/README.md` | Quy ước lưu kế hoạch đã duyệt |
| `plans/YYYY-MM-DD-<slug>.md` | Một file mỗi kế hoạch đã duyệt, kèm checklist tick trong lúc làm. Hiện có 5: P0, P1, P2a, P2b, P3 |
| `sessions/README.md` | Quy ước log phiên làm việc |
| `sessions/YYYY-MM-DD-NN.md` | Một file mỗi phiên chat, hook tạo khung sẵn. Hiện có 5 |
| `testing/test-strategy.md` | 4 tầng test, 3 luật chống test giả, fixture, kịch bản e2e |
| `testing/test-cases.md` | Ma trận truy vết US → TC → file test, 102 test case |
| `testing/smoke-checklist.md` | Checklist bấm tay theo từng phase |
| `testing/reports/README.md` | Mẫu báo cáo kiểm thử cuối phase |
| `testing/reports/YYYY-MM-DD-Pn.md` | Một file mỗi phase, chứa output pytest thật. Hiện có 5: P1, P2a, P2b, P3 chặng 1, P3 chặng 2 |

### Ứng dụng (`app/`) — từ P1

| File | Vai trò |
|---|---|
| `main.py` | Khởi tạo FastAPI, session middleware, đăng ký router, 2 trình xử lý lỗi (403/404 ra trang có bố cục, chưa đăng nhập thì chuyển về `/login`) |
| `config.py` | Đọc `.env` qua pydantic-settings: `DATABASE_URL`, `SECRET_KEY`, `AI_PROVIDER`, `GEMINI_API_KEY` |
| `db.py` | `Base`, `engine`, `SessionLocal`, `get_db()`. Bật `PRAGMA foreign_keys` cho từng kết nối SQLite |
| `security.py` | `hash_password()`, `verify_password()` — bcrypt trực tiếp, không qua passlib |
| `auth.py` | Session cookie, `nguoi_dung_hien_tai`, `yeu_cau_vai_tro()`, ngoại lệ `ChuaDangNhap` |
| `templates.py` | Cấu hình Jinja2 dùng chung |
| `seed.py` | 4 tài khoản, 3 chủ nuôi, 5 thú cưng, 5 dịch vụ, 2 gói, 4 lịch hẹn ngày mai. Chạy `python -m app.seed`, không sinh trùng |
| `models/__init__.py` | Gom mọi model — `create_all` chỉ tạo bảng đã được import |
| `models/user.py` | Bảng `users` + hằng `VAI_TRO`, `TEN_VAI_TRO` |
| `models/owner.py` | Bảng `owners`. `search_name` tự đồng bộ qua `@validates` |
| `models/pet.py` | Bảng `pets`. CHECK `weight_kg > 0`; ngày sinh kiểm ở tầng services |
| `models/service.py` | Bảng `services`. `price` kiểu `Numeric(12,2)`, **không** `Float` |
| `models/service_package.py` | `service_packages` + `package_items`, property `tong_gia_le`, `tiet_kiem` |
| `models/appointment.py` | Bảng `appointments`, hằng `TRANG_THAI`, 2 index phục vụ kiểm trùng |
| `services/clock.py` | `now()` và `freeze()` — điểm lấy thời gian duy nhất của hệ thống |
| `services/text.py` | `chuan_hoa()` — bỏ dấu tiếng Việt cho tìm kiếm, xử lý riêng chữ `đ` |
| `services/errors.py` | `LoiNghiepVu` — lỗi nghiệp vụ, thông điệp hiển thị thẳng cho người dùng |
| `services/owners.py` | Nghiệp vụ chủ nuôi và thú cưng: tạo, sửa, xóa, tra cứu |
| `services/catalog.py` | Nghiệp vụ dịch vụ và gói. `danh_sach_dang_ban()` là danh sách P3 và P5 sẽ dùng |
| `services/scheduling.py` | **Quy tắc chống trùng lịch**, đặt/đổi/hủy lịch, gợi ý khung trống. Khoảng nửa mở `[start, end)` |
| `routers/auth.py` | `/login`, `/logout`, `/` |
| `routers/users.py` | `/users` — quản lý tài khoản, chỉ vai trò `manager` |
| `routers/owners.py` | `/owners`, `/owners/{id}`, `/owners/{id}/pets`, `/pets/{id}/xoa` |
| `routers/services.py` | `/services` và `/services/goi` — chỉ `manager` sửa |
| `routers/appointments.py` | `/appointments` lưới lịch + đặt/đổi/hủy; `/appointments/cua-toi` lịch riêng của nhân viên chăm sóc |
| `templates/base.html` | Bố cục chung, menu hiện theo vai trò |
| `templates/login.html` · `home.html` · `users.html` · `error.html` | Các trang từ P1 |
| `templates/owners.html` | Danh sách, tra cứu, form thêm chủ nuôi |
| `templates/owner_detail.html` | Chi tiết chủ nuôi, danh sách thú cưng, form thêm thú cưng |
| `templates/services.html` | Bảng giá, gói dịch vụ, form thêm dịch vụ và tạo gói |
| `templates/appointments.html` | Lưới lịch, form đặt lịch, cột thao tác đổi/hủy, khung trống khi bị từ chối. Dùng chung cho `/appointments` và `/appointments/cua-toi` |
| `static/style.css` | Toàn bộ CSS, một file, không build tool |

### Kiểm thử (`tests/`) — từ P1

| File | Vai trò |
|---|---|
| `conftest.py` | 5 fixture: `db`, `client`, `frozen_clock`, `fake_ai` (khung, dùng từ P7), `seed_basic` |
| `unit/test_security.py` | Băm mật khẩu (TC-005) |
| `unit/test_clock.py` | Cố định thời gian |
| `unit/test_models_user.py` | Ràng buộc bảng `users`: UNIQUE username, CHECK role |
| `unit/test_text.py` | Chuẩn hóa chuỗi tiếng Việt, gồm bẫy chữ `đ` |
| `unit/test_models_owner_pet.py` | Ràng buộc `owners`, `pets`, khóa ngoại, `search_name` |
| `unit/test_owners_service.py` | Nghiệp vụ chủ nuôi, thú cưng, tra cứu |
| `unit/test_models_service.py` | Ràng buộc `services`, gói, và **kiểu tiền `Decimal`** |
| `unit/test_catalog_service.py` | Nghiệp vụ dịch vụ, ngưng bán, gói |
| `unit/test_models_appointment.py` | Ràng buộc `appointments`: `end_at > start_at`, CHECK trạng thái |
| `unit/test_scheduling.py` | **6 ca biên trùng lịch**, gợi ý khung trống, đổi lịch (TC-044→047), hủy lịch (TC-048, TC-049) |
| `integration/test_auth.py` | Đăng nhập (TC-001→004) |
| `integration/test_users.py` | Phân quyền và quản lý tài khoản (TC-007, 008, 010→012) |
| `integration/test_owners.py` | Chủ nuôi, thú cưng, tra cứu qua HTTP (TC-013→023) |
| `integration/test_services.py` | Dịch vụ, bảng giá, gói qua HTTP (TC-024→031) |
| `integration/test_appointments.py` | Đặt/đổi/hủy lịch qua HTTP, lịch theo vai trò (TC-035, TC-043, TC-050→052, TC-009) |

### Cấu hình

| File | Vai trò |
|---|---|
| `requirements.txt` | Phụ thuộc, đã pin phiên bản |
| `pytest.ini` | `pythonpath`, `testpaths`, `filterwarnings = error` |

---

## Chưa có — sẽ thêm theo phase

Cấu trúc dưới đây theo [`architecture.md`](architecture.md). Khi một file được tạo, chuyển nó lên
mục "Hiện có" và ghi rõ vai trò thật, rồi xóa dòng ở đây.

| Đường dẫn | Vai trò dự kiến | Phase |
|---|---|---|
| `app/models/` — 10 model còn lại | owner, pet, service, package, package_item, appointment, care_record, vaccination, invoice, invoice_item, payment, ai_log | P2–P7 |
| ~~`app/schemas/`~~ | **Bỏ.** Qua P1→P3 form đọc thẳng bằng `Form()` và kiểm ở `services/` là đủ; thêm một tầng Pydantic nữa chỉ để lặp lại phép kiểm đã có | — |
| `app/services/scheduling.py` | Đặt/đổi/hủy lịch, kiểm tra trùng lịch | P3 |
| `app/services/billing.py` | Lập hóa đơn, ghi nhận thanh toán | P5 |
| `app/services/stats.py` | Lượt dịch vụ, doanh thu, khách quay lại | P6 |
| `app/ai/provider.py` | Interface `AIProvider` | P7 |
| `app/ai/gemini.py` | `GeminiProvider` | P7 |
| `app/ai/fake.py` | `FakeProvider` — ghi lại prompt nhận được | P7 |
| `app/ai/prompts.py` | System prompt + `DISCLAIMER` | P7 |
| `app/ai/service.py` | 3 use case AI, lọc dữ liệu cá nhân, ghi `ai_logs` | P7 |
| `app/routers/` — còn lại | appointments, care_records, vaccinations, invoices, stats, ai | P3–P7 |
| `tests/e2e/test_full_flow.py` | Kịch bản xuyên suốt 11 bước | P5 |
