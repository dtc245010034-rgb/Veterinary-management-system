"""Bộ gửi thư cho máy phát triển: in thư ra log thay vì gửi.

Chạy `python run.py` trên máy mình thường không có SMTP, mà đăng ký khách (chặng 4) cần một
liên kết xác minh — bộ này cho người dùng copy liên kết từ terminal.

**Không dùng cho bản công khai:** liên kết xác minh và đặt lại mật khẩu sẽ nằm trong log.
"""

import logging
import sys

log = logging.getLogger("app.mail")


class _InRaStderrHienTai(logging.StreamHandler):
    """Ghi ra `sys.stderr` tại lúc in, không chốt luồng lúc tạo — để chạy đúng cả khi test đổi `sys.stderr`."""

    def __init__(self):
        logging.Handler.__init__(self)

    @property
    def stream(self):
        return sys.stderr


def cau_hinh_log_thu() -> None:
    """Cho logger `app.mail` tự in mức INFO ra stderr (lỗi B-2).

    Uvicorn chỉ cấu hình logger của nó; `app.mail` không ai cấu hình nên bản ghi INFO rơi về handler
    mặc định của Python (chỉ in từ WARNING) và thư giả biến mất. Gọi nhiều lần vẫn chỉ một handler.
    """
    if any(isinstance(h, _InRaStderrHienTai) for h in log.handlers):
        return
    handler = _InRaStderrHienTai()
    handler.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


class ConsoleMailer:
    def gui(self, den: str, tieu_de: str, noi_dung: str) -> None:
        log.info("[THƯ GIẢ — không gửi đi] Tới: %s | Tiêu đề: %s\n%s", den, tieu_de, noi_dung)
