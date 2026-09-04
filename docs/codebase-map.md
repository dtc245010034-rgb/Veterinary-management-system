# Bản đồ mã nguồn

> **File này bắt buộc cập nhật mỗi khi thêm, xóa hoặc đổi vai trò một file.** Đây là thứ đầu tiên
> agent đọc ở mỗi phiên làm việc (xem [`../CLAUDE.md`](../CLAUDE.md) mục 6). Bản đồ lệch thực tế thì
> phiên sau sẽ làm việc dựa trên thông tin sai.

**Cập nhật lần cuối:** 2026-09-04 (phase P0) · **Trạng thái:** chưa có code ứng dụng

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

---

## Chưa có — sẽ thêm theo phase

Cấu trúc dưới đây theo [`architecture.md`](architecture.md). Khi một file được tạo, chuyển dòng
tương ứng lên mục "Hiện có" và ghi rõ vai trò thật.

| Đường dẫn | Vai trò dự kiến | Phase |
|---|---|---|
| `requirements.txt` | Danh sách package | P1 |
| `app/main.py` | Khởi tạo FastAPI, đăng ký router | P1 |
| `app/config.py` | Đọc `.env` | P1 |
| `app/db.py` | Engine, `SessionLocal`, `get_db()` | P1 |
| `app/security.py` | Băm mật khẩu, session cookie, dependency kiểm tra vai trò | P1 |
| `app/models/` | 13 model SQLAlchemy | P1–P5 |
| `app/schemas/` | Pydantic request/response | P1–P6 |
| `app/services/clock.py` | Hàm lấy thời gian hiện tại — điểm mock duy nhất cho thời gian | P1 |
| `app/services/scheduling.py` | Đặt/đổi/hủy lịch, kiểm tra trùng lịch | P3 |
| `app/services/billing.py` | Lập hóa đơn, ghi nhận thanh toán | P5 |
| `app/services/stats.py` | Lượt dịch vụ, doanh thu, khách quay lại | P6 |
| `app/ai/provider.py` | Interface `AIProvider` | P7 |
| `app/ai/gemini.py` | `GeminiProvider` | P7 |
| `app/ai/fake.py` | `FakeProvider` — ghi lại prompt nhận được | P7 |
| `app/ai/prompts.py` | System prompt + `DISCLAIMER` | P7 |
| `app/ai/service.py` | 3 use case AI, lọc dữ liệu cá nhân, ghi `ai_logs` | P7 |
| `app/routers/` | auth, owners, pets, services, appointments, care_records, vaccinations, invoices, stats, ai | P1–P7 |
| `app/templates/` | Jinja2 | P1–P7 |
| `app/static/` | CSS, JS | P1 |
| `tests/conftest.py` | Fixture: `db`, `client`, `fake_ai`, `frozen_clock`, `seed_basic` | P1 |
| `tests/unit/` | Test `services/` và `ai/prompts.py` | P1–P7 |
| `tests/integration/` | Test qua `TestClient` | P1–P7 |
| `tests/e2e/test_full_flow.py` | Kịch bản xuyên suốt 11 bước | P5 |
