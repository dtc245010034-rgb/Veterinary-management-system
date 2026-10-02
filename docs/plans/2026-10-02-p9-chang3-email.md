# Kế hoạch — P9 chặng 3: Hạ tầng gửi email

**Trạng thái: XONG 02/10/2026 về code và tài liệu** ("bắt đầu chặng 3 đi, nếu còn gì chưa ổn thì phản biện luôn"). Thay thế ba ô 3.1–3.3 của
[kế hoạch P9](2026-09-25-p9-cong-khach-hang.md); chặng này **chưa có màn hình nào** — đăng ký, xác minh, quên mật khẩu là chặng 4.

## Phản biện kế hoạch gốc (đã đối chiếu với code)

| # | Kế hoạch gốc nói | Vấn đề | Quyết định |
|---|---|---|---|
| 1 | Quyết định #5: "Thêm **thư viện** gửi email" | Không cần. `smtplib` + `email.message.EmailMessage` có sẵn trong thư viện chuẩn; thêm gói ngoài là thêm bề mặt tấn công cho đúng phần xử lý bí mật SMTP | **Không thêm dependency** |
| 2 | Hai bộ gửi: `SmtpMailer`, `FakeMailer` | Máy dev **không có SMTP** (Gmail cần bật xác minh hai bước + mật khẩu ứng dụng). Chạy `python run.py` xong đăng ký khách thì link xác minh đi đâu? Không có đường thứ ba thì chặng 4 không demo được cục bộ | Thêm `ConsoleMailer` (in thư ra log). Mặc định `MAIL_PROVIDER=console` |
| 3 | Token "hết hạn và dùng một lần" | Gắn vào `user_id`? **Lúc đăng ký chưa có user.** Lưu token thô trong CSDL? Lộ CSDL là lộ mọi link còn hạn | Token gắn với **email + mục đích**, CSDL chỉ lưu **băm SHA-256**; token thô chỉ có trong thư |
| 4 | "Dùng một lần" | Kiểm `used_at is None` rồi mới ghi là **đua** (hai request cùng lúc đều qua) | Đánh dấu bằng **một lệnh `UPDATE … WHERE used_at IS NULL`** và đọc `rowcount` |
| 5 | "Token của người khác" (ca biên 3.2) | Mơ hồ vì chưa có "người". Hai thứ kiểm được ở chặng này: token **đúng chuỗi nhưng sai mục đích** (token xác minh mang đi đặt lại mật khẩu), và chuỗi bịa | Cả hai trả cùng một lỗi, không phân biệt "không tồn tại" với "sai mục đích" |
| 6 | "Không một lượt gửi thật nào trong suite" | Chỉ là lời hứa nếu không có gì canh | Fixture tự động trong `conftest.py`: `smtplib.SMTP`/`SMTP_SSL` ném lỗi nếu host không phải `127.0.0.1`. Test `SmtpMailer` dùng **máy chủ SMTP thật trong tiến trình** (luồng, cổng ngẫu nhiên) nên kiểm cả giao thức chứ không mock `smtplib` |
| 7 | Chống lạm dụng gửi mail (bảng rủi ro) | Thuộc chặng 4 vì cần biết "ai gửi" | Chặng này chỉ **vô hiệu token cũ** khi cấp token mới cùng (email, mục đích), để không tích lũy link còn hạn |
| 8 | (không nói) | `ConsoleMailer` in link xác minh vào log: **không được dùng ở bản công khai** | Ghi rõ ở đây; luật "công khai mà `MAIL_PROVIDER=console` thì từ chối khởi động" làm ở chặng 4 cùng lúc có luồng đăng ký (chưa có người dùng thì luật vô nghĩa) |

## Thiết kế

- `app/mail/provider.py`: `Protocol GuiMail { gui(den, tieu_de, noi_dung) }` + `LoiGuiMail` (gốc lỗi, thông điệp tiếng Việt hiển thị được).
- `app/mail/fake.py`: `FakeMailer` ghi lại mọi thư (`da_gui`), cài được lỗi.
- `app/mail/console.py`: `ConsoleMailer` in ra logger `app.mail`.
- `app/mail/smtp.py`: `SmtpMailer` — STARTTLS mặc định, `timeout`, đóng kết nối, mọi `smtplib.SMTPException`/`OSError` đổi thành `LoiGuiMail`. **Không bao giờ ghi mật khẩu hay nội dung thư vào thông báo lỗi.**
- `app/mail/service.py`: `lay_mailer()` (dependency như `ai.service.lay_provider`) — router không import `smtp.py` trực tiếp.
- `app/models/email_token.py` → bảng `email_tokens(id, email, purpose, token_hash UNIQUE, expires_at, used_at NULL, created_at)`; `purpose` CHECK `verify_email | reset_password`.
- `app/services/email_tokens.py`: `cap_token(db, email, purpose) -> str` (token thô), `dung_token(db, token, purpose) -> str` (trả email, ném `LoiNghiepVu` nếu sai/hết hạn/đã dùng). Hạn: 24 giờ cho xác minh, 1 giờ cho đặt lại mật khẩu. Thời gian lấy từ `clock.now()`.
- Cấu hình: `MAIL_PROVIDER`, `MAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `MAIL_TIMEOUT_GIAY`.

## Danh sách ô

Mỗi ô có code: test đỏ-trước → xanh → một lượt đột biến (CLAUDE.md mục 7).

- [x] 3.1a `app/mail/`: Protocol, `FakeMailer`, `ConsoleMailer`, `lay_mailer`, cấu hình + `.env.example`.
      → verify: test `FakeMailer` ghi đúng thư; `lay_mailer` trả đúng loại theo `MAIL_PROVIDER`; phép canh `.env.example` xanh.
- [x] 3.1b `SmtpMailer` + fixture chặn gửi thật.
      → verify: test với máy chủ SMTP cục bộ nhận đúng `From/To/Subject/body` (có tiếng Việt); lỗi kết nối → `LoiGuiMail` không lộ mật khẩu; fixture đỏ khi thử gửi tới host ngoài.
- [x] 3.2 Bảng `email_tokens` + `app/services/email_tokens.py`.
      → verify: ca biên — hết hạn (đúng ranh giới) · dùng lại · sai mục đích · chuỗi bịa · cấp token mới vô hiệu token cũ · CSDL không chứa token thô.
- [x] 3.3 Cập nhật `erd.md`, `architecture.md`, `ai-safety.md` (không đổi), `codebase-map.md`, `test-cases.md`, log phiên, `plans/README.md`.
      → verify: `test_architecture.py` xanh; chạy lại toàn bộ test.

## Điều chỉnh so với thiết kế ban đầu

- `SmtpMailer` bắt một `OSError` thay vì `(smtplib.SMTPException, OSError)`: `SMTPException` là lớp con của `OSError`, đột biến "bỏ `SMTPException`" sống sót vì tương đương. Có test riêng cho mã 5xx từ máy chủ.
- Thêm kiểm tra ký tự xuống dòng ở người nhận/tiêu đề (đường chèn `Bcc:`): ý này không có trong kế hoạch gốc, phát sinh khi viết `SmtpMailer`.

## Giới hạn đã biết

- `SmtpMailer` **chưa từng nói chuyện với nhà cung cấp thật**: test chỉ dùng máy chủ SMTP cục bộ không TLS/AUTH, nên STARTTLS và `login()` chưa được chứng minh bằng test. Cần một lần thử tay với Gmail (mật khẩu ứng dụng) trước khi chặng 4 dựa vào nó.
- Luật "công khai mà `MAIL_PROVIDER=console` thì từ chối khởi động" chưa có (chặng 4).

## Ngoài phạm vi chặng này

Màn hình đăng ký/xác minh/quên mật khẩu, vai trò `customer`, giới hạn lượt gửi, luật chặn `console` ở bản công khai — chặng 4.
