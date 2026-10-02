"""Bộ gửi thư cho máy phát triển: in thư ra log thay vì gửi.

Chạy `python run.py` trên máy mình thường không có SMTP, mà đăng ký khách (chặng 4) cần một
liên kết xác minh — bộ này cho người dùng copy liên kết từ terminal.

**Không dùng cho bản công khai:** liên kết xác minh và đặt lại mật khẩu sẽ nằm trong log.
"""

import logging

log = logging.getLogger("app.mail")


class ConsoleMailer:
    def gui(self, den: str, tieu_de: str, noi_dung: str) -> None:
        log.info("[THƯ GIẢ — không gửi đi] Tới: %s | Tiêu đề: %s\n%s", den, tieu_de, noi_dung)
