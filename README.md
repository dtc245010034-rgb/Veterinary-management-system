# Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI

Phần mềm quản lý cho cửa hàng dịch vụ thú cưng: chủ nuôi, thú cưng, lịch spa/tắm/grooming, lịch tiêm
nhắc lại, hồ sơ chăm sóc, hóa đơn và thống kê. Tích hợp AI để soạn tin nhắn nhắc lịch, tóm tắt hồ sơ
chăm sóc và trả lời câu hỏi chăm sóc thường ngày ở mức tham khảo.

> **AI trong hệ thống này chỉ đưa thông tin tham khảo, không thay thế chẩn đoán của bác sĩ thú y.**

Đề bài gốc: [`đề-bài.md`](đề-bài.md) · Trạng thái: **P0→P7 xong, đang làm P8 (hoàn thiện và nộp)** — quản lý chủ nuôi, thú
cưng, dịch vụ, đặt/đổi/hủy lịch có chống trùng **trong giờ mở cửa**, hồ sơ chăm sóc, nhắc tiêm, hóa đơn,
thanh toán và thống kê đều chạy được. **Ba tính năng AI đã dùng được trên giao diện** và đã kiểm chứng
với Gemini thật (13/13 ca guardrail đạt). Lượt rà soát toàn hệ thống 19/09 tìm 18 lỗi: **đã sửa 3 lỗi
cao, 4 lỗi ưu tiên** (thiếu chức năng sửa, chuyển hướng mở, mật khẩu yếu, khuyến cáo lặp) **và M-06**
(đặt lịch ngoài giờ mở cửa); smoke bấm tay P1→P7 đã tick đủ. Còn **10 lỗi trung bình/thấp** và **P8
hoàn thiện** — xem tiến độ từng phase trong [`docs/roadmap.md`](docs/roadmap.md).

Chạy lần đầu phải sao chép `.env.example` thành `.env` và đặt `SECRET_KEY` riêng — ứng dụng từ chối
khởi động với khóa mặc định. Muốn gọi AI thật thì đặt thêm `GEMINI_API_KEY` và `AI_PROVIDER=gemini`;
để `fake` thì hệ thống trả lời cố định, không cần mạng và không tốn lượt gọi.

Xem lượt gọi AI còn lại trong ngày: `python -m app.ai.quota`.

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| CSDL | SQLite |
| Frontend | Jinja2 + HTML/JS thuần |
| AI | Gemini API sau lớp adapter, có `FakeProvider` để test offline |
| Test | pytest — 4 tầng: unit, integration, regression, e2e |

## Cách chạy

Cần Python 3.11 trở lên (đã kiểm trên 3.14.6).

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

copy .env.example .env            # bắt buộc; sửa SECRET_KEY thành chuỗi ngẫu nhiên của riêng bạn
python -m app.seed                # dữ liệu mẫu: tài khoản, chủ nuôi, thú cưng, lịch, hóa đơn…
uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000`.

### Tài khoản mẫu

Mật khẩu chung: `matkhau123`

| Tên đăng nhập | Vai trò | Thấy được gì |
|---|---|---|
| `quanly` | Quản lý | Toàn bộ hệ thống, gồm tài khoản nhân viên và sửa bảng giá |
| `letan` | Lễ tân | Chủ nuôi, thú cưng, lịch hẹn, tiêm phòng, hóa đơn; xem bảng giá |
| `chamsoc1`, `chamsoc2` | Nhân viên chăm sóc | Lịch của mình, ghi hồ sơ chăm sóc, tiêm phòng; xem chủ nuôi và bảng giá |

### Ba tính năng AI

| Ở đâu | Làm gì |
|---|---|
| Lưới lịch hẹn, trang Tiêm phòng | **Soạn tin nhắc (AI)** — tin nhắn nháp gửi khách, sửa được trước khi gửi |
| Trang thú cưng | **Tóm tắt bằng AI** lịch sử chăm sóc |
| Menu **Trợ lý AI** | Hỏi đáp chăm sóc thường ngày |

Không có khóa Gemini vẫn chạy được: để `AI_PROVIDER=fake` thì các tính năng AI trả lời cố định thay
vì gọi API thật. Gói Gemini miễn phí giới hạn lượt mỗi ngày cho từng model, nên hệ thống **tự xoay
sang model kế** khi model đầu hết lượt hoặc quá tải; quản lý xem được bảng lượt ở `/ai/quota`.

Ba lớp an toàn nằm trong code, không phụ thuộc mô hình có nghe lời hay không: câu xin thuốc/liều bị
chặn **trước khi gọi API**, phản hồi có liều lượng bị thay, số điện thoại và email bị lọc khỏi mọi
prompt. Chi tiết: [`docs/ai-safety.md`](docs/ai-safety.md).

## Cách chạy test

```bash
pytest tests/unit            # 489 ca, ~35–45s — chạy mỗi lần sửa code
pytest tests/integration     # 286 ca, ~55–65s — chạy cuối mỗi phiên làm việc
pytest tests/e2e             #   1 ca,  ~6s    — kịch bản xuyên suốt 11 bước, chạy cuối mỗi phase
pytest                       # 797 ca, ~102s   — chạy trước mỗi commit (hồi quy)
```

Bốn tầng và lý do chia như vậy: [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md).
Kết quả từng phase: [`docs/testing/reports/`](docs/testing/reports/).

## Tài liệu

| File | Nội dung |
|---|---|
| [`docs/user-stories.md`](docs/user-stories.md) | 28 user story, 104 tiêu chí chấp nhận Given/When/Then |
| [`docs/erd.md`](docs/erd.md) | 14 bảng, sơ đồ quan hệ, mô tả cột và ràng buộc — tất cả đã dựng |
| [`docs/architecture.md`](docs/architecture.md) | Ba lớp, ranh giới, luồng dữ liệu, cách xử lý lỗi |
| [`docs/ai-safety.md`](docs/ai-safety.md) | System prompt, ba lớp guardrail trong code, 20 ca kiểm thử an toàn AI |
| [`docs/roadmap.md`](docs/roadmap.md) | Lộ trình P0–P8 gắn với mốc KT1/KT2/KT3/cuối kỳ |
| [`docs/codebase-map.md`](docs/codebase-map.md) | Bản đồ file → trách nhiệm |
| [`docs/testing/`](docs/testing/) | Chiến lược, ma trận 122 test case, checklist thủ công, báo cáo |
| [`docs/plans/`](docs/plans/) | Kế hoạch đã duyệt của từng phase |
| [`docs/sessions/`](docs/sessions/) | Nhật ký từng phiên làm việc |

## Quy trình phát triển

Dự án được làm phần lớn bằng AI agent (vibe code). Hai luật giữ cho code, tài liệu và báo cáo không
lệch nhau:

1. **Mỗi phiên làm việc để lại một log** trong `docs/sessions/`, tạo tự động bởi hook trong
   [`.claude/`](.claude/) của repo. Phiên có sửa code thì bắt buộc ghi file đã đổi và kết quả test.
2. **Mọi ngữ cảnh nằm trong repo** — cấu hình agent, hook, kế hoạch đã duyệt, log phiên đều được
   commit. Clone repo về máy khác là có đủ ngữ cảnh làm tiếp:

   ```bash
   git clone https://github.com/dtc245010034-rgb/Veterinary-management-system.git
   ```

   Hai thứ **không** theo repo vì là bí mật hoặc dữ liệu máy: `.env` và `petcare.db`.

Chi tiết trong [`CLAUDE.md`](CLAUDE.md) mục 6. Mọi phiên làm việc bắt đầu bằng việc vào thư mục dự án
và đọc `docs/codebase-map.md` cùng log phiên gần nhất.
