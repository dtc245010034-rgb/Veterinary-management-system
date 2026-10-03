# Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI

[![Kiểm thử](https://github.com/dtc245010034-rgb/Veterinary-management-system/actions/workflows/ci.yml/badge.svg)](https://github.com/dtc245010034-rgb/Veterinary-management-system/actions/workflows/ci.yml)

Phần mềm quản lý cho cửa hàng dịch vụ thú cưng: chủ nuôi, thú cưng, lịch spa/tắm/grooming, lịch tiêm
nhắc lại, hồ sơ chăm sóc, hóa đơn và thống kê. Có **cổng khách hàng** để chủ nuôi tự đăng ký, xem
thú cưng, xin đặt lịch và hỏi đáp AI. AI soạn tin nhắn nhắc lịch, tóm tắt hồ sơ chăm sóc và trả lời
câu hỏi chăm sóc thường ngày ở mức tham khảo.

> **AI trong hệ thống này chỉ đưa thông tin tham khảo, không thay thế chẩn đoán của bác sĩ thú y.**

Đề bài gốc: [`đề-bài.md`](đề-bài.md) · Trạng thái: **P0→P7 xong; P8 (hoàn thiện và nộp) đang làm; P9 (cổng khách hàng) đã code xong, 1381 test xanh ngày 03/10, còn chờ người dùng tự tick checklist bấm tay và duyệt phase** — xem [`docs/roadmap.md`](docs/roadmap.md) và [báo cáo P9](docs/testing/reports/2026-10-03-P9.md).

## Mục lục

1. [Tính năng](#1-tính-năng) · 2. [Công nghệ](#2-công-nghệ) · 3. [Cài đặt và chạy](#3-cài-đặt-và-chạy) ·
4. [Tài khoản mẫu và phân quyền](#4-tài-khoản-mẫu-và-phân-quyền) · 5. [Hướng dẫn cho nhân viên](#5-hướng-dẫn-sử-dụng-cho-nhân-viên) ·
6. [Hướng dẫn cho khách hàng](#6-hướng-dẫn-sử-dụng-cổng-khách-hàng) · 7. [AI](#7-ai) · 8. [Gửi email](#8-gửi-email) ·
9. [Biến môi trường](#9-biến-môi-trường) · 10. [Kiểm thử](#10-kiểm-thử) · 11. [Cấu trúc thư mục](#11-cấu-trúc-thư-mục) ·
12. [Lỗi thường gặp](#12-lỗi-thường-gặp) · 13. [Tài liệu](#13-tài-liệu) · 14. [Quy trình phát triển](#14-quy-trình-phát-triển)

## 1. Tính năng

**Nhân viên (giao diện quản trị)**

- Chủ nuôi và thú cưng: thêm, sửa, xóa có ràng buộc, tìm kiếm không phân biệt dấu.
- Dịch vụ và gói dịch vụ: bảng giá, ngừng bán/bán lại (quản lý sửa giá).
- Lịch hẹn: đặt, đổi, hủy; **chống trùng giờ** theo nhân viên và theo thú cưng, chỉ trong giờ mở cửa 08:00–18:00.
- Hồ sơ chăm sóc: nhân viên ghi sau buổi làm; ghi hồ sơ là cách duy nhất đưa lịch sang "Hoàn thành".
- Tiêm phòng: sổ tiêm từng thú cưng, danh sách mũi sắp đến hạn.
- Hóa đơn và thanh toán: lập từ lịch đã hoàn thành, thu nhiều lần (tiền mặt/chuyển khoản/thẻ), hủy hóa đơn chưa thu.
- Thống kê doanh thu và hoạt động (quản lý), quản lý tài khoản nhân viên.
- Duyệt yêu cầu liên kết hồ sơ của khách và duyệt/từ chối lịch khách xin đặt.
- Ba tính năng AI: soạn tin nhắc lịch, tóm tắt hồ sơ chăm sóc, trợ lý hỏi đáp.

**Khách hàng (cổng `/khach`)**

- Đăng ký bằng email có xác minh, đăng nhập, quên và đặt lại mật khẩu, đổi mật khẩu.
- Liên kết tài khoản với hồ sơ chủ nuôi bằng số điện thoại, **chờ lễ tân duyệt**.
- Xem thú cưng, lịch hẹn, hóa đơn của chính mình; không thấy dữ liệu của người khác.
- Xem khung giờ trống theo nhân viên và dịch vụ, gửi yêu cầu đặt lịch (trạng thái "Chờ duyệt").
- Hỏi đáp AI về chăm sóc thú cưng, tối đa 10 lượt mỗi ngày.

## 2. Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| CSDL | SQLite (`petcare.db`) |
| Frontend | Jinja2 render phía server + HTML/JS thuần, không có bước build |
| AI | Gemini API sau lớp adapter `AIProvider`; `FakeProvider` để chạy offline và để test |
| Test | pytest — 4 tầng: unit, integration, regression, e2e |

## 3. Cài đặt và chạy

Cần **Python 3.11 trở lên** (đã chạy trên 3.12 và 3.14). Không cần cài gì khác, kể cả khi chưa có `.venv`.

### 3.1. Cách nhanh nhất — một lệnh

```bash
python run.py
```

Lệnh này làm hết: tạo `.venv`, cài thư viện, tạo `.env` (với `SECRET_KEY` ngẫu nhiên), nạp dữ liệu
mẫu nếu CSDL chưa có, chạy web và mở trình duyệt tại `http://127.0.0.1:8000`. Dừng bằng **Ctrl+C**.
`.env` đã có thì **không bao giờ bị ghi đè** (chỉ dòng `SECRET_KEY` được thay khi còn giá trị mặc định).
Đăng nhập bằng một [tài khoản mẫu](#4-tài-khoản-mẫu-và-phân-quyền).

| Lệnh | Việc |
|---|---|
| `python run.py --port 9000` | chọn cổng (mặc định 8000; cổng bạn tự chọn mà bận thì báo lỗi) |
| `python run.py --no-open` | không tự mở trình duyệt |
| `python run.py --reload` | tự nạp lại khi sửa code (dùng khi phát triển) |
| `python run.py --check` | chạy thử: đợi `/login` trả 200 rồi tắt (dùng trong CI) |
| `python run.py status` | xem tình trạng môi trường (venv, `.env`, CSDL…) |
| `python run.py reset` | **xóa CSDL SQLite** (hỏi xác nhận, thêm `--yes` để bỏ qua); lần chạy sau seed lại dữ liệu mẫu |
| `python run.py test [tham số]` | chạy pytest, chuyển nguyên tham số: `python run.py test -k dang_nhap`. `python test.py` làm y hệt |
| `python run.py docker [up\|down\|logs\|reset]` | chạy trong Docker (xem 3.3) |
| `python run.py --public-url https://abc.ngrok.app` | chế độ công khai qua tunnel HTTPS (xem 3.4) |

### 3.2. Chạy tay từng bước

```bash
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# BẮT BUỘC: sửa SECRET_KEY trong .env thành chuỗi ngẫu nhiên của riêng bạn,
# ứng dụng từ chối khởi động với khóa mặc định.
python -m app.seed                 # dữ liệu mẫu: tài khoản, chủ nuôi, thú cưng, lịch, hóa đơn…
uvicorn app.main:app --reload      # mở http://127.0.0.1:8000
```

Ngày giờ của dữ liệu mẫu tính lùi/tiến từ **lúc chạy seed**, nên "ngày mai", "hôm qua" luôn khớp với
hôm nay; CSDL càng cũ thì các lịch mẫu càng lệch. Muốn dữ liệu mới: `python run.py reset` rồi `python run.py`.

### 3.3. Chạy bằng Docker

```bash
python run.py docker           # dựng image, chạy nền, đợi /login rồi mở trình duyệt
python run.py docker logs      # xem log của ứng dụng
python run.py docker down      # tắt, GIỮ dữ liệu
python run.py docker reset     # tắt và XÓA cả dữ liệu
```

Dữ liệu SQLite nằm trong volume Docker nên dựng lại image không mất dữ liệu. Chi tiết:
[`docs/trien-khai.md`](docs/trien-khai.md).

### 3.4. Cho người khác thử qua Internet (công khai tạm)

```bash
python run.py --public-url https://abc.ngrok.app
```

Chế độ này bật cookie `Secure`, sinh **mật khẩu ngẫu nhiên** cho tài khoản mẫu và **đòi cấu hình
SMTP thật** (`MAIL_PROVIDER=smtp`, `APP_ORIGIN`); ứng dụng từ chối khởi động nếu còn tài khoản dùng
mật khẩu `matkhau123`. Đọc [`docs/trien-khai.md`](docs/trien-khai.md) trước khi mở cổng ra ngoài.

## 4. Tài khoản mẫu và phân quyền

Mật khẩu chung khi chạy cục bộ: **`matkhau123`** (đổi bằng biến `SEED_MAT_KHAU` trước khi seed).

| Tên đăng nhập | Họ tên | Vai trò |
|---|---|---|
| `quanly` | Nguyễn Văn Quản | Quản lý (`manager`) |
| `letan` | Trần Thị Lễ | Lễ tân (`receptionist`) |
| `chamsoc1` | Lê Văn Chăm | Nhân viên chăm sóc (`caretaker`) |
| `chamsoc2` | Phạm Thị Sóc | Nhân viên chăm sóc (`caretaker`) |

**Dữ liệu mẫu:** 3 chủ nuôi (Đỗ Thị Hằng `0912345678` với Mực và Mun; Trần Quốc Đạt `0987654321` với
Đậu Đỏ; Lý Thu Hà `0905112233` với Bông và Sữa), 5 dịch vụ (`TAM`, `CATMONG`, `CATTIA`, `VESINHTAI`,
`SPA`), 2 gói dịch vụ, cùng lịch hẹn, hồ sơ chăm sóc, mũi tiêm và hóa đơn mẫu. Ba số điện thoại trên
dùng được khi thử liên kết hồ sơ ở cổng khách.

**Menu và quyền theo vai trò**

| Mục | Quản lý | Lễ tân | Chăm sóc |
|---|:-:|:-:|:-:|
| Chủ nuôi, Dịch vụ (xem), Tiêm phòng, Trợ lý AI | ✓ | ✓ | ✓ |
| Lịch hẹn (`/appointments`) | ✓ | ✓ | — |
| Lịch của tôi (`/appointments/cua-toi`) | — | — | ✓ |
| Hóa đơn (`/invoices`) | ✓ | ✓ | — |
| Lịch chờ duyệt (`/lich-cho-duyet`), Liên kết khách (`/lien-ket-khach`) | ✓ | ✓ | — |
| Ghi hồ sơ chăm sóc | ✓ | — | ✓ |
| Soạn tin nhắc lịch bằng AI | ✓ | ✓ | — |
| Sửa bảng giá, Thống kê (`/stats`), Tài khoản (`/users`), bảng lượt AI (`/ai/quota`) | ✓ | — | — |

Truy cập trang không đủ quyền trả về 403; chưa đăng nhập thì chuyển về trang đăng nhập.
**Một trình duyệt chỉ giữ một danh tính:** đăng nhập nhân viên sẽ đẩy phiên khách ra và ngược lại —
muốn thử cả hai cùng lúc, dùng hai trình duyệt (hoặc cửa sổ ẩn danh).

## 5. Hướng dẫn sử dụng cho nhân viên

Đăng nhập tại `/login`. Mật khẩu sai nhiều lần liên tiếp bị làm chậm (5 lần miễn phí, sau đó khóa
30 giây, gấp đôi mỗi lần, tối đa 900 giây). Đổi mật khẩu ở liên kết **Đổi mật khẩu** trên menu
(tối thiểu 8 ký tự).

### 5.1. Chủ nuôi và thú cưng (`/owners`)

- **Thêm chủ nuôi:** điền họ tên và số điện thoại (bắt buộc; số Việt Nam 10 chữ số, bắt đầu bằng 0), email và địa chỉ (không bắt buộc) → *Lưu*.
- **Tìm kiếm:** gõ tên hoặc số điện thoại vào ô tìm; **không cần gõ dấu** (`do thi hang` tìm ra "Đỗ Thị Hằng").
- Bấm tên chủ nuôi để xem hồ sơ, **sửa** thông tin và **thêm thú cưng** (tên, loài, giống, ngày sinh, cân nặng…).
- Trang thú cưng (`/pets/{id}`) có lịch sử chăm sóc, sổ tiêm và nút **Tóm tắt bằng AI**.
- **Xóa** chủ nuôi bị chặn khi còn thú cưng hoặc còn tài khoản khách đang liên kết. Xóa thú cưng bị chặn khi đã có lịch hẹn hoặc mũi tiêm. Hệ thống báo rõ lý do bằng tiếng Việt.

### 5.2. Dịch vụ và gói (`/services`)

Mọi vai trò xem được bảng giá. **Quản lý** sửa giá, thêm gói, **ngừng bán** hoặc **bán lại** một dịch
vụ/gói (dịch vụ ngừng bán không còn chọn được khi đặt lịch mới nhưng hóa đơn cũ giữ nguyên giá đã lập).

### 5.3. Lịch hẹn (`/appointments`)

1. Chọn thú cưng, dịch vụ, nhân viên phụ trách, ngày và giờ → *Đặt lịch*.
2. Hệ thống **từ chối** nếu giờ nằm ngoài **08:00–18:00**, ở quá khứ, hoặc **trùng** với lịch khác của
   cùng nhân viên hoặc cùng thú cưng. Lỗi hiện ngay trên form.
3. Mỗi lịch có nút **Đổi** (chọn giờ mới, vẫn kiểm trùng) và **Hủy**.
4. **Soạn tin nhắc (AI)** tạo tin nhắn nháp để gửi khách; sửa được trước khi gửi.

Trạng thái lịch: *Chờ duyệt* (khách xin) → *Đã đặt* → *Đã đổi lịch* / *Đã hủy* / *Hoàn thành*.
Nhân viên chăm sóc xem lịch của mình ở **Lịch của tôi**.

### 5.4. Hồ sơ chăm sóc → Hoàn thành

Mở lịch của buổi vừa làm → **Hồ sơ** (`/appointments/{id}/ho-so`) → ghi tình trạng, việc đã làm, ghi
chú → *Lưu*. **Lưu hồ sơ là cách duy nhất đưa lịch sang "Hoàn thành"**, và chỉ quản lý hoặc nhân viên
chăm sóc ghi được.

### 5.5. Tiêm phòng (`/vaccinations`)

Danh sách mũi tiêm sắp đến hạn của mọi thú cưng, kèm nút **Soạn tin nhắc (AI)**. Thêm mũi tiêm mới ở
trang thú cưng (tên vắc-xin, ngày tiêm, ngày nhắc lại).

### 5.6. Hóa đơn và thanh toán (`/invoices`)

1. **Chỉ lập được hóa đơn từ lịch đã "Hoàn thành"** — nút *Lập hóa đơn* nằm ở lịch hẹn đó.
2. Trên hóa đơn: **Thu tiền** (số tiền, hình thức *Tiền mặt / Chuyển khoản / Thẻ*). Có thể thu nhiều
   lần; trạng thái đi từ *Chưa thanh toán* → *Thanh toán một phần* → *Đã thanh toán*. Không thu quá số còn nợ.
3. **Hủy hóa đơn** chỉ được khi **chưa có khoản thu nào** (hệ thống không có hoàn tiền).

### 5.7. Duyệt khách hàng đăng ký

- **Liên kết khách** (`/lien-ket-khach`): khách gửi yêu cầu nối tài khoản với hồ sơ chủ nuôi (theo số
  điện thoại). Xem thông tin, đối chiếu với chủ nuôi, bấm **Duyệt** hoặc **Từ chối**. Có thể **gỡ liên
  kết** của một tài khoản đã duyệt.
- **Lịch chờ duyệt** (`/lich-cho-duyet`): các lịch khách xin đặt. **Duyệt** để chuyển sang "Đã đặt";
  **Từ chối** thì **bắt buộc nhập lý do** — khách sẽ thấy lý do này ở "Ghi chú của cửa hàng". Lịch
  chờ quá **24 giờ** mà chưa duyệt thì **tự chuyển sang "Đã hủy"** và khung giờ đó mở lại cho người khác
  (hệ thống dọn khi có người mở danh sách lịch hoặc thao tác với lịch, không chạy ngầm theo đồng hồ).

### 5.8. Thống kê và tài khoản (chỉ quản lý)

- `/stats`: chọn khoảng ngày (mặc định theo kỳ gần nhất) → lượt dịch vụ, số khách, doanh thu và bảng theo từng dịch vụ.
- `/users`: thêm tài khoản nhân viên, sửa họ tên và vai trò, **khóa/mở khóa**, **đặt lại mật khẩu**.

## 6. Hướng dẫn sử dụng cổng khách hàng

Địa chỉ: `http://127.0.0.1:8000/khach` (khi chưa đăng nhập sẽ chuyển tới `/khach/dang-nhap`).

1. **Đăng ký** (`/khach/dang-ky`): nhập họ tên, email, mật khẩu (tối thiểu 8 ký tự).
2. **Xác minh email:** hệ thống gửi thư chứa liên kết có hiệu lực **24 giờ**, dùng **một lần**.
   **Lỗi đã biết (B-2, chưa sửa):** với `MAIL_PROVIDER=console` (mặc định) lẽ ra thư giả hiện trong terminal,
   nhưng thực tế **không hiện gì** vì mức log của `app.mail` chưa được cấu hình. Trên máy mình, muốn thử luồng
   đăng ký đầy đủ hãy dựng CSDL demo (mục 10, có sẵn 7 tài khoản khách) hoặc đặt `MAIL_PROVIDER=smtp`.
3. **Đăng nhập** (`/khach/dang-nhap`). Quên mật khẩu: `/khach/quen-mat-khau` → liên kết đặt lại hiệu
   lực **1 giờ**, một lần. Đổi mật khẩu ở `/khach/doi-mat-khau`.
4. **Liên kết hồ sơ** (`/khach/lien-ket`): nhập số điện thoại đã đăng ký với cửa hàng (thử `0912345678`)
   và ghi chú nếu cần. Yêu cầu ở trạng thái *chờ* cho tới khi **lễ tân duyệt** (mục 5.7). Chưa liên kết
   thì chưa xem được dữ liệu thú cưng.
5. Sau khi được duyệt, khách xem:
   - **Thú cưng** (`/khach/thu-cung`) và chi tiết từng con;
   - **Lịch hẹn** (`/khach/lich-hen`) và **Hóa đơn** (`/khach/hoa-don`).
   Chỉ thấy của **chủ nuôi mình đã liên kết**; mở id của người khác cho kết quả 404 giống hệt id không tồn tại.
6. **Giờ trống** (`/khach/khung-trong`): chọn thú cưng, dịch vụ, ngày → xem các khung còn trống trong 08:00–18:00 theo từng nhân viên.
7. **Xin đặt lịch** (`/khach/dat-lich`): chọn thú cưng, dịch vụ, nhân viên, ngày, giờ, ghi chú. Lịch vào
   trạng thái **Chờ duyệt**; mỗi khách có tối đa **3 lịch chờ** cùng lúc. Cửa hàng duyệt hoặc từ chối (kèm lý do).
8. **Hỏi đáp AI** (`/khach/hoi-dap`): gõ câu hỏi chăm sóc thường ngày. **Tối đa 10 lượt mỗi ngày**
   (`AI_KHACH_TOI_DA_MOI_NGAY`); hết lượt thì hiện thông báo và nút bị vô hiệu. Câu xin thuốc hoặc liều
   bị từ chối nhưng **vẫn tính một lượt**. Mỗi câu trả lời kèm lời khuyên liên hệ bác sĩ thú y.

## 7. AI

| Ở đâu | Ai dùng | Làm gì |
|---|---|---|
| Lưới lịch hẹn, trang Tiêm phòng | Quản lý, lễ tân | **Soạn tin nhắc (AI)** — tin nhắn nháp gửi khách |
| Trang thú cưng | Nhân viên | **Tóm tắt bằng AI** lịch sử chăm sóc |
| Menu **Trợ lý AI** (`/ai/hoi-dap`) | Nhân viên | Hỏi đáp chăm sóc thường ngày |
| `/khach/hoi-dap` | Khách hàng | Hỏi đáp, 10 lượt/ngày/tài khoản |

- **Không có khóa Gemini vẫn chạy được:** `AI_PROVIDER=fake` (mặc định trong `.env.example`) trả lời cố
  định, không cần mạng. Muốn gọi thật: lấy khóa tại <https://aistudio.google.com/apikey>, đặt
  `GEMINI_API_KEY=...` và `AI_PROVIDER=gemini` trong `.env`, khởi động lại.
- **Xoay model:** gói miễn phí giới hạn lượt theo từng model, nên hệ thống thử lần lượt các model trong
  `GEMINI_MODELS` và chuyển sang model kế khi model đầu hết lượt hoặc quá tải. Quản lý xem bảng lượt ở
  `/ai/quota`; trên terminal: `python -m app.ai.quota`.
- **An toàn (nằm trong code, không phụ thuộc mô hình có nghe lời hay không):** câu xin thuốc/liều bị chặn
  **trước khi gọi API**; phản hồi có liều lượng bị thay; mọi phản hồi sức khỏe kèm khuyến cáo bác sĩ thú y.
- **Dữ liệu gửi sang AI:** chỉ dữ liệu chăm sóc thú cưng. **Không** gửi số điện thoại, email, địa chỉ chủ
  nuôi; với khách, **chỉ riêng câu hỏi** được gửi đi, không kèm tên, email hay thú cưng.
- Giới hạn đã biết: nhân viên đọc được câu hỏi/đáp của khách qua `/ai/ket-qua/{id}` (**chấp nhận có chủ ý**) — xem
  [`docs/ai-safety.md`](docs/ai-safety.md) mục 10.

Chi tiết: [`docs/ai-safety.md`](docs/ai-safety.md).

## 8. Gửi email

Dùng cho xác minh email và đặt lại mật khẩu của khách.

- **`MAIL_PROVIDER=console` (mặc định):** không gửi thật. Thiết kế là in thư ra log, nhưng hiện chưa hiện được
  (lỗi B-2, xem mục 6). **Không dùng cho bản công khai** (liên kết nằm trong log).
- **`MAIL_PROVIDER=smtp`:** gửi thật. Điền `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`,
  `MAIL_FROM`. Gmail cần **mật khẩu ứng dụng** (bật xác minh hai bước). `SMTP_PASSWORD` là bí mật, chỉ điền
  trong `.env` thật.

## 9. Biến môi trường

Sao chép từ [`.env.example`](.env.example); `python run.py` tự tạo `.env` nếu chưa có.

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `SECRET_KEY` | (phải đổi) | Khóa ký cookie phiên; `run.py` tự sinh ngẫu nhiên |
| `DATABASE_URL` | `sqlite:///./petcare.db` | Đường dẫn CSDL |
| `SESSION_HTTPS_ONLY` | `false` | `true` khi công khai qua HTTPS (cookie `Secure`) |
| `APP_ORIGIN` | trống | Địa chỉ công khai khi đi qua tunnel/proxy |
| `SEED_MAT_KHAU` | trống = `matkhau123` | Mật khẩu của tài khoản mẫu |
| `BCRYPT_ROUNDS` | `12` | Độ nặng băm mật khẩu (test tự hạ xuống 4) |
| `AI_PROVIDER` | `fake` | `gemini` hoặc `fake` |
| `GEMINI_API_KEY` | trống | Khóa API Gemini |
| `GEMINI_MODELS` | 4 model, cách nhau dấu phẩy | Thứ tự ưu tiên khi xoay model |
| `GEMINI_RPD_UOC_TINH` | `20` | Ước tính lượt/ngày **mỗi model** (học lại khi Google trả 429) |
| `GEMINI_RPM_UOC_TINH` | `5` | Ước tính lượt/phút |
| `GEMINI_THINKING_BUDGET` | `0` | Token "suy nghĩ" mỗi lời gọi; `-1` = mặc định của model |
| `AI_TONG_GIAY` / `AI_MOI_LAN_GIAY` | `45` / `25` | Ngân sách thời gian một lần bấm / một lần thử |
| `AI_NGHI_GIAY` | `120` | Nghỉ bao lâu với model vừa quá tải |
| `AI_KHACH_TOI_DA_MOI_NGAY` | `10` | Lượt hỏi AI/ngày của mỗi khách |
| `MAIL_PROVIDER` | `console` | `console` hoặc `smtp` |
| `MAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `MAIL_TIMEOUT_GIAY` | xem file | Cấu hình SMTP |

## 10. Kiểm thử

```bash
pytest tests/unit            # 923 ca — chạy mỗi lần sửa code
pytest tests/integration     # 458 ca — chạy cuối mỗi phiên làm việc
pytest tests/e2e             #   1 ca — kịch bản xuyên suốt, chạy cuối mỗi phase
pytest                       # 1382 ca — chạy trước mỗi commit
```

Dùng `python run.py test` nếu chưa kích hoạt `.venv`. Số ca đếm bằng `pytest --co` ngày 03/10; một lượt
chạy toàn bộ mất khoảng **một phút** (dao động theo tải máy). Trên Linux có **một ca bị bỏ qua** (kiểm hook PowerShell, máy không có PowerShell) — xem kết quả
thật trong [báo cáo P9](docs/testing/reports/2026-10-03-P9.md).
Phép canh kiến trúc (`tests/unit/test_architecture.py`) giữ cho code, tài liệu và số liệu không lệch nhau.

**Dựng CSDL demo nhiều dữ liệu, không đụng `petcare.db`:**

```bash
python tools/tao_du_lieu_demo.py           # tạo demo.db: 15 chủ nuôi, hơn 130 lịch, 80+ hóa đơn, 7 khách mẫu
DATABASE_URL=sqlite:///demo.db AI_PROVIDER=fake python run.py
```

(Windows PowerShell: `$env:DATABASE_URL="sqlite:///demo.db"; $env:AI_PROVIDER="fake"; python run.py`.)

Mật khẩu chung `matkhau123`; khách thử đăng nhập tại `/khach/dang-nhap` với `khach1@demo.test` … `khach7@demo.test`.
Chạy lại script thì `demo.db` được dựng lại từ đầu (dữ liệu cố định theo hạt giống).

**Kiểm tra trên CSDL mới, không đụng dữ liệu đang dùng:**

```bash
python tools/kiem_tra_song.py              # CSDL tạm + server thật, 150 kiểm tra, tự dọn
python tools/kiem_tra_song.py --giu-lai    # giữ lại thư mục tạm để mở xem
```

Công cụ đi qua đăng nhập/phân quyền, chủ nuôi, thú cưng, dịch vụ, lịch hẹn, hồ sơ chăm sóc, hóa đơn,
tiêm phòng, tài khoản, thống kê, ba tính năng AI và chống dò mật khẩu (`AI_PROVIDER=fake`). Thoát `0` khi
mọi kiểm tra đạt (đã chạy 03/10: 150/150, 0 phản hồi 500). **Nó chưa đi qua cổng khách `/khach`** — phần
đó được phủ bằng integration test và lượt kiểm tra trên Chrome ghi trong báo cáo P9. Nó cũng không thay
thế [checklist bấm tay](docs/testing/smoke-checklist.md) (layout, nút bấm, thông báo hiện đúng chỗ).

Muốn tự bấm trên CSDL riêng, giữ nguyên `petcare.db`:

```bash
DATABASE_URL=sqlite:///thu-nghiem.db python -m app.seed
DATABASE_URL=sqlite:///thu-nghiem.db uvicorn app.main:app --port 8001
```

Chiến lược và lý do chia bốn tầng: [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md) ·
ma trận 182 test case: [`docs/testing/test-cases.md`](docs/testing/test-cases.md) ·
báo cáo từng phase: [`docs/testing/reports/`](docs/testing/reports/).

## 11. Cấu trúc thư mục

```
app/
  main.py            khởi tạo FastAPI, gắn router, middleware, nâng cấp schema lúc khởi động
  routers/           CHỈ làm HTTP: parse request, kiểm tra quyền, render (không có logic nghiệp vụ)
  services/          toàn bộ logic nghiệp vụ, test được mà không cần chạy app
  ai/                adapter AIProvider, guardrail, quota; chỉ được gọi qua app/ai/service.py
  models/            các bảng SQLAlchemy (17 bảng)
  templates/         Jinja2 — giao diện nhân viên và cổng khách (khach_*.html)
  static/            style.css
  seed.py            nạp dữ liệu mẫu
tests/               unit/ · integration/ · e2e/
tools/               kiem_tra_song.py · tao_du_lieu_demo.py
docs/                đặc tả, kiến trúc, kế hoạch, nhật ký, báo cáo kiểm thử
run.py · test.py     chạy một lệnh / chạy pytest
Dockerfile · docker-compose.yml
```

Bản đồ từng file → trách nhiệm: [`docs/codebase-map.md`](docs/codebase-map.md).

## 12. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Ứng dụng từ chối khởi động, nhắc `SECRET_KEY` | Đang dùng khóa mặc định. Chạy bằng `python run.py` (tự sinh) hoặc tự đặt chuỗi ngẫu nhiên trong `.env` |
| Cổng 8000 bận | `python run.py --port 9000` |
| Đăng nhập xong nhưng bị đẩy ra lại | Đang bật `SESSION_HTTPS_ONLY=true` mà truy cập bằng `http://`; đặt lại `false` khi chạy cục bộ |
| POST bị chặn (403) khi chạy sau tunnel/proxy | Đặt `APP_ORIGIN=https://địa-chỉ-công-khai` |
| Không thấy thư xác minh của khách | Với `MAIL_PROVIDER=console` thư **không** hiện ở terminal (lỗi B-2, chưa sửa); dùng tài khoản khách mẫu hoặc `MAIL_PROVIDER=smtp` |
| Đăng nhập báo bị làm chậm (429) | Sai mật khẩu nhiều lần; đợi hết thời gian khóa (tối đa 15 phút) |
| Lịch mẫu bị lệch ngày | Dữ liệu mẫu tính từ lúc seed; `python run.py reset` rồi chạy lại |
| AI báo lỗi hoặc trả lời cố định | `AI_PROVIDER=fake` trả lời cố định; với `gemini` kiểm tra `GEMINI_API_KEY` và `python -m app.ai.quota` |
| Công khai nhưng không khởi động được | Cần `MAIL_PROVIDER=smtp`, `APP_ORIGIN`, và không còn tài khoản `matkhau123` — xem [`docs/trien-khai.md`](docs/trien-khai.md) |
| Muốn làm lại từ đầu | `python run.py reset` (xóa CSDL, hỏi xác nhận) |

## 13. Tài liệu

| File | Nội dung |
|---|---|
| [`docs/user-stories/README.md`](docs/user-stories/README.md) | 36 user story chia 10 nhóm A–J (nhóm J là cổng khách hàng), 185 tiêu chí Given/When/Then |
| [`docs/erd.md`](docs/erd.md) | 17 bảng, sơ đồ quan hệ, mô tả cột và ràng buộc |
| [`docs/architecture.md`](docs/architecture.md) | Ba lớp, ranh giới, luồng dữ liệu, cách xử lý lỗi |
| [`docs/trien-khai.md`](docs/trien-khai.md) | Venv, Docker, công khai qua tunnel; đường chuyển PostgreSQL; giới hạn đã biết |
| [`docs/ai-safety.md`](docs/ai-safety.md) | System prompt, guardrail trong code, ca kiểm thử an toàn AI, AI cho khách |
| [`docs/roadmap.md`](docs/roadmap.md) | Lộ trình P0–P9 gắn với các mốc KT1/KT2/KT3/cuối kỳ |
| [`docs/codebase-map.md`](docs/codebase-map.md) | Bản đồ file → trách nhiệm |
| [`docs/testing/`](docs/testing/) | Chiến lược, ma trận 182 test case, checklist bấm tay, báo cáo |
| [`docs/plans/`](docs/plans/) | Kế hoạch đã duyệt của từng phase |
| [`docs/sessions/`](docs/sessions/) | Nhật ký từng phiên làm việc |

## 14. Quy trình phát triển

Dự án được làm phần lớn bằng AI agent (vibe code). Hai luật giữ cho code, tài liệu và báo cáo không lệch nhau:

1. **Mỗi phiên làm việc để lại một log** trong `docs/sessions/`, tạo tự động bởi hook trong
   [`.claude/`](.claude/). Phiên có sửa code thì bắt buộc ghi file đã đổi và kết quả test.
2. **Mọi ngữ cảnh nằm trong repo** — cấu hình agent, hook, kế hoạch đã duyệt, log phiên đều được commit.
   Clone repo về máy khác là có đủ ngữ cảnh làm tiếp:

   ```bash
   git clone https://github.com/dtc245010034-rgb/Veterinary-management-system.git
   ```

   Hai thứ **không** theo repo vì là bí mật hoặc dữ liệu máy: `.env` và `petcare.db`.

Chi tiết trong [`CLAUDE.md`](CLAUDE.md) mục 6. Quy ước: tài liệu và thông báo tiếng Việt; tên trong code
tiếng Anh không dấu; commit tiếng Việt không dấu dạng `<loại>: <mô tả>`.
