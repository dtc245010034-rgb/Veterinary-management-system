"""Chọn bộ gửi thư theo cấu hình — cửa duy nhất router được dùng (như `app/ai/service.py`)."""

from app.config import settings
from app.mail.console import ConsoleMailer
from app.mail.provider import GuiMail, LoiGuiMail


def lay_mailer() -> GuiMail:
    """Dependency của FastAPI. Test override nó bằng `FakeMailer`, nên bộ test không gửi thư thật.

    Tên lạ là lỗi cấu hình chứ không rơi về `console`: gõ nhầm `smpt` mà âm thầm in thư ra log
    thì khách không bao giờ nhận được thư xác minh.
    """
    if settings.mail_provider == "console":
        return ConsoleMailer()
    if settings.mail_provider == "smtp":
        from app.mail.smtp import SmtpMailer

        if not settings.smtp_host:
            raise LoiGuiMail("MAIL_PROVIDER=smtp nhưng thiếu SMTP_HOST trong .env.")
        return SmtpMailer(
            host=settings.smtp_host,
            port=settings.smtp_port,
            nguoi_gui=settings.mail_from,
            tai_khoan=settings.smtp_user,
            mat_khau=settings.smtp_password,
            starttls=settings.smtp_starttls,
            timeout=settings.mail_timeout_giay,
        )
    raise LoiGuiMail(f"MAIL_PROVIDER không hợp lệ: {settings.mail_provider!r} (chỉ nhận console hoặc smtp).")
