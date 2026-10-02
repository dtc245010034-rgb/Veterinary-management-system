"""Ranh giới với dịch vụ gửi thư: một interface và một loại lỗi.

Cả hệ thống chỉ gửi thư qua `gui(den, tieu_de, noi_dung)`. Nhờ vậy `FakeMailer` thay được
`SmtpMailer` trong test mà không chạm mạng, và đổi sang nhà cung cấp khác (SendGrid, SES…)
chỉ là thêm một file — cùng mẫu với `app/ai/provider.py`.
"""

from typing import Protocol


class LoiGuiMail(Exception):
    """Không gửi được thư (hoặc cấu hình gửi thư sai). Thông điệp hiển thị được cho người dùng.

    Thông điệp **không bao giờ** chứa mật khẩu SMTP hay nội dung thư: liên kết xác minh trong thư
    là bí mật, và lỗi thường bị ghi vào log.
    """


class GuiMail(Protocol):
    def gui(self, den: str, tieu_de: str, noi_dung: str) -> None:
        """Gửi một thư văn bản thuần. Ném `LoiGuiMail` nếu thất bại; không tự thử lại."""
        ...
