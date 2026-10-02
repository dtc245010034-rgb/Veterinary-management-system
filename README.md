# Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI

[![Kiểm thử](https://github.com/dtc245010034-rgb/Veterinary-management-system/actions/workflows/ci.yml/badge.svg)](https://github.com/dtc245010034-rgb/Veterinary-management-system/actions/workflows/ci.yml)

Phần mềm quản lý cho cửa hàng dịch vụ thú cưng: chủ nuôi, thú cưng, lịch spa/tắm/grooming, lịch tiêm
nhắc lại, hồ sơ chăm sóc, hóa đơn và thống kê. Tích hợp AI để soạn tin nhắn nhắc lịch, tóm tắt hồ sơ
chăm sóc và trả lời câu hỏi chăm sóc thường ngày ở mức tham khảo.

> **AI trong hệ thống này chỉ đưa thông tin tham khảo, không thay thế chẩn đoán của bác sĩ thú y.**

Đề bài gốc: [`đề-bài.md`](đề-bài.md) · Trạng thái: **P0→P7 xong, đang làm P8 (hoàn thiện và nộp) và P9 (cổng khách hàng — chặng 0→2 xong: fixture test, tách đặc tả, bảo mật, Docker)** — quản lý chủ nuôi, thú
cưng, dịch vụ, đặt/đổi/hủy lịch có chống trùng **trong giờ mở cửa**, hồ sơ chăm sóc, nhắc tiêm, hóa đơn,
thanh toán và thống kê đều chạy được. **Ba tính năng AI đã dùng được trên giao diện** và đã kiểm chứng
với Gemini thật (13/13 ca guardrail đạt). Lượt rà soát toàn hệ thống 19/09 tìm 18 lỗi: **đã sửa 3 lỗi
cao, 4 lỗi ưu tiên** (thiếu chức năng sửa, chuyển hướng mở, mật khẩu yếu, khuyến cáo lặp) **và M-06**
(đặt lịch ngoài giờ mở cửa) **và toàn bộ 11 lỗi trung bình/thấp còn lại**; smoke bấm tay P1→P7 đã
tick đủ. **Không còn lỗi nào tồn từ lượt rà soát.** Còn lại là **P8 hoàn thiện** — xem tiến độ từng
phase trong [`docs/roadmap.md`](docs/roadmap.md).

Chạy lần đầu: `python run.py` tự tạo `.env` với `SECRET_KEY` ngẫu nhiên (chạy tay thì phải sao chép
`.env.example` thành `.env` và tự đặt `SECRET_KEY` — ứng dụng từ chối khởi động với khóa mặc định).
Muốn gọi AI thật thì đặt thêm `GEMINI_API_KEY` và `AI_PROVIDER=gemini`;
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
python run.py
```

Một lệnh làm hết: tạo `.venv`, cài thư viện, tạo `.env` (khóa `SECRET_KEY` ngẫu nhiên; `.env` có sẵn thì **không bao giờ bị ghi đè**), nạp dữ liệu mẫu nếu CSDL chưa có, chạy web và mở trình duyệt. Dừng bằng Ctrl+C.

| Lệnh | Việc |
|---|---|
| `python run.py --port 9000 --no-open --reload` | chọn cổng, không mở trình duyệt, tự nạp lại khi sửa code |
| `python run.py status` | xem tình trạng môi trường |
| `python run.py reset` | xóa CSDL SQLite (hỏi xác nhận); lần chạy sau seed lại |
| `python run.py test` hoặc `python test.py` | chạy pytest, truyền nguyên tham số (`python test.py -k dang_nhap`) |
| `python tools/kiem_tra_song.py` | dựng **CSDL mới** trong thư mục tạm, chạy server thật, đi qua mọi chức năng theo từng vai trò (150 kiểm tra) — xem mục "Kiểm tra trên CSDL mới" bên dưới |
| `python run.py docker` | dựng image và chạy trong Docker (`docker logs`/`down`/`reset` để xem log, tắt giữ dữ liệu, xóa cả dữ liệu) |
| `python run.py --public-url https://abc.ngrok.app` | chế độ công khai qua tunnel HTTPS: cookie `Secure`, mật khẩu seed ngẫu nhiên; xem [`docs/trien-khai.md`](docs/trien-khai.md) |

<details><summary>Chạy tay từng bước (không dùng run.py)</summary>

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

copy .env.example .env            # bắt buộc; sửa SECRET_KEY thành chuỗi ngẫu nhiên của riêng bạn
python -m app.seed                # dữ liệu mẫu: tài khoản, chủ nuôi, thú cưng, lịch, hóa đơn…
uvicorn app.main:app --reload
```

</details>

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
pytest tests/unit            # 704 ca — chạy mỗi lần sửa code
pytest tests/integration     # 348 ca — chạy cuối mỗi phiên làm việc
pytest tests/e2e             #   1 ca — kịch bản xuyên suốt 11 bước, chạy cuối mỗi phase
pytest                       # 1053 ca (1052 đạt + 1 bỏ qua trên Linux) — chạy trước mỗi commit
```

Số ca đếm lại ngày 02/10 bằng `pytest --co`; lượt chạy toàn bộ cùng ngày: **44s tới 116s** tùy tải máy
(không đo riêng từng tầng). Số đo ngày 25/09 qua bảy lượt chạy. **Dao động rất rộng theo tải máy — 101s tới 148s cho cùng một
bộ test, cùng một ngày**, nên đừng coi một lượt đo là kết luận. Chạy riêng từng tầng rồi cộng lại
(~127s) cũng lớn hơn một lượt chạy chung; chưa truy nguyên nhân chỗ chênh đó.

Ngân sách trong `test-strategy.md` (toàn bộ **< 100s**) là **mốc xem lại, không phải mốc chặn**:
vượt thì đo và tìm nguyên nhân, không cắt test để lấy màu xanh. Lượt đo 25/09 cho thấy **không
test nào đáng cắt** — 20 ca chậm nhất cộng lại chỉ ~24s, phần còn lại là chi phí fixture rải đều.

Bốn tầng và lý do chia như vậy: [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md).
Kết quả từng phase: [`docs/testing/reports/`](docs/testing/reports/).

## Kiểm tra trên CSDL mới

Muốn thử **toàn bộ chức năng trên một CSDL sạch** mà không đụng dữ liệu đang dùng (`petcare.db`):

```bash
python tools/kiem_tra_song.py              # dựng CSDL tạm + server thật, chạy 150 kiểm tra, tự dọn
python tools/kiem_tra_song.py --giu-lai    # như trên nhưng giữ lại thư mục tạm để mở xem
```

Công cụ này (không phải pytest) dùng **một file SQLite thật trong thư mục tạm, một tiến trình
uvicorn thật và các yêu cầu HTTP thật**; `AI_PROVIDER=fake` nên không tốn lượt Gemini. Nó đăng nhập
bằng bốn tài khoản mẫu và đi qua: đăng nhập/phân quyền (ma trận 3 vai trò × 12 trang), chủ nuôi,
thú cưng, dịch vụ và gói, đặt/đổi/hủy lịch (trùng giờ, ngoài giờ mở cửa, ngày quá khứ), hồ sơ chăm
sóc, hóa đơn và thu tiền, tiêm phòng, quản lý tài khoản, đổi mật khẩu/đăng xuất, xóa có ràng buộc,
thống kê, ba tính năng AI kèm câu xin thuốc bị chặn, và chống dò mật khẩu. Thoát `0` khi mọi kiểm
tra đạt, `1` khi còn lỗi hoặc server trả 500.

Nó **không thay** smoke bấm tay trên trình duyệt (layout, nút bấm, thông báo hiện đúng chỗ) — xem
[`docs/testing/smoke-checklist.md`](docs/testing/smoke-checklist.md).

Muốn tự bấm trên một CSDL mới, có hai cách:

```bash
# Cách 1: làm mới CSDL đang dùng (MẤT dữ liệu trong petcare.db — hỏi xác nhận)
python run.py reset
python run.py                       # seed lại dữ liệu mẫu, chạy, mở trình duyệt

# Cách 2: một file CSDL riêng, giữ nguyên petcare.db  (bash; Windows PowerShell: $env:DATABASE_URL="...")
DATABASE_URL=sqlite:///thu-nghiem.db python -m app.seed
DATABASE_URL=sqlite:///thu-nghiem.db uvicorn app.main:app --port 8001
```

Ngày giờ của dữ liệu mẫu tính lùi/tiến từ **lúc chạy seed** (xem `app/seed.py`), nên dữ liệu "ngày
mai", "hôm qua" luôn khớp với hôm nay — CSDL càng cũ thì các lịch mẫu càng lệch.

## Tài liệu

| File | Nội dung |
|---|---|
| [`docs/user-stories/README.md`](docs/user-stories/README.md) | 28 user story tách thành 9 file theo nhóm A–I, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên; 118 tiêu chí Given/When/Then |
| [`docs/erd.md`](docs/erd.md) | 15 bảng, sơ đồ quan hệ, mô tả cột và ràng buộc — tất cả đã dựng |
| [`docs/architecture.md`](docs/architecture.md) | Ba lớp, ranh giới, luồng dữ liệu, cách xử lý lỗi |
| [`docs/trien-khai.md`](docs/trien-khai.md) | Chạy bằng venv, Docker, công khai qua tunnel; đường chuyển PostgreSQL; giới hạn đã biết |
| [`docs/ai-safety.md`](docs/ai-safety.md) | System prompt, ba lớp guardrail trong code, 20 ca kiểm thử an toàn AI |
| [`docs/roadmap.md`](docs/roadmap.md) | Lộ trình P0–P8 gắn với mốc KT1/KT2/KT3/cuối kỳ |
| [`docs/codebase-map.md`](docs/codebase-map.md) | Bản đồ file → trách nhiệm |
| [`docs/testing/`](docs/testing/) | Chiến lược, ma trận 145 test case, checklist thủ công, báo cáo |
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
