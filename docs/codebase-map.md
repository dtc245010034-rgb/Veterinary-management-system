# Bản đồ mã nguồn

> **File này bắt buộc cập nhật mỗi khi thêm, xóa hoặc đổi vai trò một file.** Đây là thứ đầu tiên
> agent đọc ở mỗi phiên làm việc (xem [`../CLAUDE.md`](../CLAUDE.md) mục 6). Bản đồ lệch thực tế thì
> phiên sau sẽ làm việc dựa trên thông tin sai.

**Cập nhật lần cuối:** 2026-09-04 (phase P1) · **Trạng thái:** đăng nhập và phân quyền chạy được

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
| `plans/2026-09-04-kt1-bo-context-va-dac-ta.md` | Kế hoạch phase P0 kèm checklist |
| `sessions/README.md` | Quy ước log phiên làm việc |
| `sessions/2026-09-04-01.md` | Log phiên đầu tiên |
| `testing/test-strategy.md` | 4 tầng test, 3 luật chống test giả, fixture, kịch bản e2e |
| `testing/test-cases.md` | Ma trận truy vết US → TC → file test, 102 test case |
| `testing/smoke-checklist.md` | Checklist bấm tay theo từng phase |
| `testing/reports/README.md` | Mẫu báo cáo kiểm thử cuối phase |

### Ứng dụng (`app/`) — từ P1

| File | Vai trò |
|---|---|
| `main.py` | Khởi tạo FastAPI, session middleware, đăng ký router, 2 trình xử lý lỗi (403/404 ra trang có bố cục, chưa đăng nhập thì chuyển về `/login`) |
| `config.py` | Đọc `.env` qua pydantic-settings: `DATABASE_URL`, `SECRET_KEY`, `AI_PROVIDER`, `GEMINI_API_KEY` |
| `db.py` | `Base`, `engine`, `SessionLocal`, `get_db()`. Bật `PRAGMA foreign_keys` cho từng kết nối SQLite |
| `security.py` | `hash_password()`, `verify_password()` — bcrypt trực tiếp, không qua passlib |
| `auth.py` | Session cookie, `nguoi_dung_hien_tai`, `yeu_cau_vai_tro()`, ngoại lệ `ChuaDangNhap` |
| `templates.py` | Cấu hình Jinja2 dùng chung |
| `seed.py` | Tạo 4 tài khoản mẫu. Chạy `python -m app.seed` |
| `models/user.py` | Bảng `users` + hằng `VAI_TRO`, `TEN_VAI_TRO` |
| `services/clock.py` | `now()` và `freeze()` — điểm lấy thời gian duy nhất của hệ thống |
| `routers/auth.py` | `/login`, `/logout`, `/` |
| `routers/users.py` | `/users` — quản lý tài khoản, chỉ vai trò `manager` |
| `templates/base.html` | Bố cục chung, menu hiện theo vai trò |
| `templates/login.html` · `home.html` · `users.html` · `error.html` | Các trang |
| `static/style.css` | Toàn bộ CSS, một file, không build tool |

### Kiểm thử (`tests/`) — từ P1

| File | Vai trò |
|---|---|
| `conftest.py` | 5 fixture: `db`, `client`, `frozen_clock`, `fake_ai` (khung, dùng từ P7), `seed_basic` |
| `unit/test_security.py` | Băm mật khẩu (TC-005) |
| `unit/test_clock.py` | Cố định thời gian |
| `unit/test_models_user.py` | Ràng buộc bảng `users`: UNIQUE username, CHECK role |
| `integration/test_auth.py` | Đăng nhập (TC-001→004) |
| `integration/test_users.py` | Phân quyền và quản lý tài khoản (TC-007, 008, 010→012) |

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
| `app/models/` — 12 model còn lại | owner, pet, service, package, package_item, appointment, care_record, vaccination, invoice, invoice_item, payment, ai_log | P2–P7 |
| `app/schemas/` | Pydantic request/response. Chưa cần ở P1 vì form đơn giản đọc thẳng qua `Form()` | P2+ |
| `app/services/scheduling.py` | Đặt/đổi/hủy lịch, kiểm tra trùng lịch | P3 |
| `app/services/billing.py` | Lập hóa đơn, ghi nhận thanh toán | P5 |
| `app/services/stats.py` | Lượt dịch vụ, doanh thu, khách quay lại | P6 |
| `app/ai/provider.py` | Interface `AIProvider` | P7 |
| `app/ai/gemini.py` | `GeminiProvider` | P7 |
| `app/ai/fake.py` | `FakeProvider` — ghi lại prompt nhận được | P7 |
| `app/ai/prompts.py` | System prompt + `DISCLAIMER` | P7 |
| `app/ai/service.py` | 3 use case AI, lọc dữ liệu cá nhân, ghi `ai_logs` | P7 |
| `app/routers/` — còn lại | owners, pets, services, appointments, care_records, vaccinations, invoices, stats, ai | P2–P7 |
| `tests/e2e/test_full_flow.py` | Kịch bản xuyên suốt 11 bước | P5 |
