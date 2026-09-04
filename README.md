# Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI

Phần mềm quản lý cho cửa hàng dịch vụ thú cưng: chủ nuôi, thú cưng, lịch spa/tắm/grooming, lịch tiêm
nhắc lại, hồ sơ chăm sóc, hóa đơn và thống kê. Tích hợp AI để soạn tin nhắn nhắc lịch, tóm tắt hồ sơ
chăm sóc và trả lời câu hỏi chăm sóc thường ngày ở mức tham khảo.

> **AI trong hệ thống này chỉ đưa thông tin tham khảo, không thay thế chẩn đoán của bác sĩ thú y.**

Đề bài gốc: [`đề-bài.md`](đề-bài.md) · Trạng thái: **P0 — đang dựng đặc tả**, chưa có code ứng dụng.
Lộ trình đầy đủ: [`docs/roadmap.md`](docs/roadmap.md).

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| CSDL | SQLite |
| Frontend | Jinja2 + HTML/JS thuần |
| AI | Gemini API sau lớp adapter, có `FakeProvider` để test offline |
| Test | pytest — 4 tầng: unit, integration, regression, e2e |

## Cách chạy

> Phần này hoàn thiện ở phase P1. Hiện repo chưa có code ứng dụng.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env          # rồi điền GEMINI_API_KEY
uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000`.

Không có khóa Gemini vẫn chạy được toàn bộ phần quản lý: đặt `AI_PROVIDER=fake` trong `.env`, các
tính năng AI sẽ trả lời cố định thay vì gọi API thật.

## Cách chạy test

```bash
pytest tests/unit            # < 5s   — chạy mỗi lần sửa code
pytest tests/integration     # < 30s  — chạy cuối mỗi phiên làm việc
pytest                       # < 1p   — chạy trước mỗi commit (hồi quy)
pytest tests/e2e             # vài phút — chạy cuối mỗi phase
```

Bốn tầng và lý do chia như vậy: [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md).

## Tài liệu

| File | Nội dung |
|---|---|
| [`docs/user-stories.md`](docs/user-stories.md) | 28 user story, 98 tiêu chí chấp nhận Given/When/Then |
| [`docs/erd.md`](docs/erd.md) | 13 bảng, sơ đồ quan hệ, mô tả cột và ràng buộc |
| [`docs/architecture.md`](docs/architecture.md) | Ba lớp, ranh giới, luồng dữ liệu, cách xử lý lỗi |
| [`docs/ai-safety.md`](docs/ai-safety.md) | System prompt, guardrail, 20 ca kiểm thử an toàn AI |
| [`docs/roadmap.md`](docs/roadmap.md) | Lộ trình P0–P8 gắn với mốc KT1/KT2/KT3/cuối kỳ |
| [`docs/codebase-map.md`](docs/codebase-map.md) | Bản đồ file → trách nhiệm |
| [`docs/testing/`](docs/testing/) | Chiến lược, ma trận 102 test case, checklist thủ công, báo cáo |
| [`docs/plans/`](docs/plans/) | Kế hoạch đã duyệt của từng phase |
| [`docs/sessions/`](docs/sessions/) | Nhật ký từng phiên làm việc |

## Quy trình phát triển

Dự án được làm phần lớn bằng AI agent (vibe code). Hai luật giữ cho code, tài liệu và báo cáo không
lệch nhau:

1. **Mỗi phiên làm việc để lại một log** trong `docs/sessions/`, tạo tự động bởi hook trong
   [`.claude/`](.claude/) của repo. Phiên có sửa code thì bắt buộc ghi file đã đổi và kết quả test.
2. **Mọi ngữ cảnh nằm trong repo** — cấu hình agent, hook, kế hoạch đã duyệt, log phiên đều được
   commit. Clone repo về máy khác là có đủ ngữ cảnh làm tiếp.

Chi tiết trong [`CLAUDE.md`](CLAUDE.md) mục 6. Mọi phiên làm việc bắt đầu bằng việc vào thư mục dự án
và đọc `docs/codebase-map.md` cùng log phiên gần nhất.
