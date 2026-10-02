"""SmtpMailer nói chuyện SMTP thật với một máy chủ cục bộ chạy trong tiến trình test.

Không mock `smtplib`: mock thì chỉ chứng minh mình gọi đúng tên hàm, không chứng minh
thư ra khỏi máy với đúng người nhận, tiêu đề và nội dung tiếng Việt. Máy chủ giả dưới đây
là ranh giới ngoài duy nhất (CLAUDE.md mục 7, luật 1) và nằm hoàn toàn ở 127.0.0.1.
"""

import email
import email.policy
import smtplib
import socket
import socketserver
import threading

import pytest

from app.mail.provider import LoiGuiMail
from app.mail.smtp import SmtpMailer


class _MayChuSmtp(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _XuLy)
        self.thu_nhan: list[bytes] = []
        self.lenh_nhan: list[str] = []

    @property
    def cong(self) -> int:
        return self.server_address[1]


class _XuLy(socketserver.StreamRequestHandler):
    """Vừa đủ SMTP để nhận một thư: EHLO, MAIL, RCPT, DATA, QUIT. Không có STARTTLS/AUTH."""

    def _tra(self, dong: str) -> None:
        self.wfile.write((dong + "\r\n").encode())

    def handle(self):
        self._tra("220 test ESMTP")
        while True:
            dong = self.rfile.readline().decode(errors="replace").strip()
            if not dong:
                return
            self.server.lenh_nhan.append(dong)
            lenh = dong.split()[0].upper()
            if lenh in ("EHLO", "HELO"):
                self._tra("250 test")
            elif lenh in ("MAIL", "RCPT", "RSET", "NOOP"):
                self._tra("250 OK")
            elif lenh == "DATA":
                self._tra("354 gui di")
                khung = []
                while True:
                    d = self.rfile.readline()
                    if d in (b".\r\n", b""):
                        break
                    khung.append(d[1:] if d.startswith(b"..") else d)
                self.server.thu_nhan.append(b"".join(khung))
                self._tra("250 da nhan")
            elif lenh == "QUIT":
                self._tra("221 bye")
                return
            else:
                self._tra("502 khong ho tro")


@pytest.fixture
def may_chu_smtp():
    may_chu = _MayChuSmtp()
    luong = threading.Thread(target=may_chu.serve_forever, daemon=True)
    luong.start()
    yield may_chu
    may_chu.shutdown()
    may_chu.server_close()
    luong.join(timeout=5)


def _mailer(may_chu, **kw) -> SmtpMailer:
    tham_so = dict(
        host="127.0.0.1",
        port=may_chu.cong,
        nguoi_gui="Petcare <noreply@example.com>",
        tai_khoan="",
        mat_khau="",
        starttls=False,
        timeout=5,
    )
    tham_so.update(kw)
    return SmtpMailer(**tham_so)


def test_gui_thu_that_toi_may_chu_smtp_dung_nguoi_nhan_tieu_de_va_tieng_viet(may_chu_smtp):
    _mailer(may_chu_smtp).gui(
        "khach@example.com", "Xác minh email của bạn", "Chào bạn,\nBấm vào liên kết sau: http://127.0.0.1:8000/xac-minh/abc"
    )

    assert len(may_chu_smtp.thu_nhan) == 1
    thu = email.message_from_bytes(may_chu_smtp.thu_nhan[0], policy=email.policy.default)
    assert thu["To"] == "khach@example.com"
    assert thu["From"] == "Petcare <noreply@example.com>"
    assert thu["Subject"] == "Xác minh email của bạn"
    noi_dung = thu.get_content()
    assert "http://127.0.0.1:8000/xac-minh/abc" in noi_dung
    assert "Chào bạn" in noi_dung
    assert any(l.upper().startswith("RCPT TO:<KHACH@EXAMPLE.COM>") for l in may_chu_smtp.lenh_nhan)


def test_khong_chen_duoc_dau_thu_qua_tieu_de_hoac_dia_chi_nguoi_nhan(may_chu_smtp):
    """Tiêu đề/người nhận có xuống dòng là đường chèn thêm `Bcc:` — gửi thư rác bằng tài khoản của shop."""
    mailer = _mailer(may_chu_smtp)

    with pytest.raises(LoiGuiMail):
        mailer.gui("khach@example.com\r\nBcc: ke-xau@example.com", "Tiêu đề", "x")
    with pytest.raises(LoiGuiMail):
        mailer.gui("khach@example.com", "Tiêu đề\r\nBcc: ke-xau@example.com", "x")

    assert may_chu_smtp.thu_nhan == []


def test_khong_ket_noi_duoc_thi_bao_loi_gui_mail_khong_lo_mat_khau():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        cong_dong = s.getsockname()[1]  # đóng ngay sau with: cổng này không ai nghe

    mailer = SmtpMailer(
        host="127.0.0.1",
        port=cong_dong,
        nguoi_gui="noreply@example.com",
        tai_khoan="shop",
        mat_khau="BI-MAT-KHONG-DUOC-LO",
        starttls=False,
        timeout=2,
    )

    with pytest.raises(LoiGuiMail) as loi:
        mailer.gui("khach@example.com", "Tiêu đề", "Nội dung bí mật của thư")

    assert "BI-MAT-KHONG-DUOC-LO" not in str(loi.value)
    assert "Nội dung bí mật của thư" not in str(loi.value)


def test_may_chu_tu_choi_nguoi_nhan_thi_bao_loi_gui_mail(may_chu_smtp):
    """Mã 5xx từ máy chủ (SMTPException, không phải OSError) cũng phải thành LoiGuiMail."""
    may_chu_smtp.RequestHandlerClass = type(
        "TuChoi",
        (_XuLy,),
        {"handle": lambda self: (self._tra("554 tu choi het"), None)[1]},
    )

    with pytest.raises(LoiGuiMail):
        _mailer(may_chu_smtp).gui("khach@example.com", "Tiêu đề", "x")


def test_fixture_chan_gui_that_nem_loi_khi_host_la_may_chu_ngoai():
    """Bảo đảm của "không lượt gửi thật nào trong suite": tự canh, không dựa vào lời hứa."""
    with pytest.raises(AssertionError, match="gửi mail thật"):
        smtplib.SMTP("smtp.gmail.com", 587)
    with pytest.raises(AssertionError, match="gửi mail thật"):
        smtplib.SMTP_SSL("smtp.gmail.com", 465)
