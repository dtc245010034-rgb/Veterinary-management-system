"""Bộ gửi thư qua SMTP, chỉ dùng thư viện chuẩn (`smtplib`, `email`).

Mỗi lần gửi mở một kết nối rồi đóng: thư xác minh/đặt lại mật khẩu là việc hiếm, giữ kết nối
chỉ thêm trạng thái để hỏng.
"""

import smtplib
from email.message import EmailMessage

from app.mail.provider import LoiGuiMail


class SmtpMailer:
    def __init__(
        self,
        host: str,
        port: int,
        nguoi_gui: str,
        tai_khoan: str = "",
        mat_khau: str = "",
        starttls: bool = True,
        timeout: float = 10,
    ):
        self.host = host
        self.port = port
        self.nguoi_gui = nguoi_gui
        self.tai_khoan = tai_khoan
        self.mat_khau = mat_khau
        self.starttls = starttls
        self.timeout = timeout

    def gui(self, den: str, tieu_de: str, noi_dung: str) -> None:
        thu = EmailMessage()
        try:
            thu["From"] = self.nguoi_gui
            thu["To"] = den
            thu["Subject"] = tieu_de
        except ValueError:
            # `email` từ chối giá trị có xuống dòng: chặn chèn thêm đầu thư (Bcc:…).
            raise LoiGuiMail("Địa chỉ nhận hoặc tiêu đề thư không hợp lệ.") from None
        thu.set_content(noi_dung)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as may_chu:
                if self.starttls:
                    may_chu.starttls()
                if self.tai_khoan:
                    may_chu.login(self.tai_khoan, self.mat_khau)
                may_chu.send_message(thu)
        except OSError:
            # `smtplib.SMTPException` cũng là con của OSError nên một nhánh phủ cả lỗi mạng lẫn mã 4xx/5xx.
            # Cố ý bỏ nguyên nhân gốc: thông điệp của smtplib có thể kèm địa chỉ và phản hồi máy chủ,
            # và `from None` giữ cho log không in lại chuỗi đó cùng traceback.
            raise LoiGuiMail("Không gửi được thư. Vui lòng thử lại sau.") from None
