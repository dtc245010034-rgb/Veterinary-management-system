"""Hạ tầng gửi email (P9 chặng 3): FakeMailer, ConsoleMailer, chọn bộ gửi theo cấu hình.

`SmtpMailer` có file test riêng (test_smtp_mailer.py) vì cần một máy chủ SMTP cục bộ.
"""

import logging

import pytest

from app.config import settings
from app.mail.console import ConsoleMailer
from app.mail.fake import FakeMailer
from app.mail.provider import LoiGuiMail
from app.mail.service import lay_mailer


def test_fake_mailer_ghi_lai_dung_thu_da_gui():
    fake = FakeMailer()

    fake.gui("khach@example.com", "Xác minh email", "Bấm vào liên kết để xác minh.")

    assert len(fake.da_gui) == 1
    thu = fake.da_gui[0]
    assert (thu.den, thu.tieu_de, thu.noi_dung) == (
        "khach@example.com",
        "Xác minh email",
        "Bấm vào liên kết để xác minh.",
    )


def test_fake_mailer_ghi_nhieu_thu_theo_thu_tu():
    fake = FakeMailer()

    fake.gui("a@example.com", "Một", "x")
    fake.gui("b@example.com", "Hai", "y")

    assert [t.den for t in fake.da_gui] == ["a@example.com", "b@example.com"]


def test_fake_mailer_nem_loi_da_cai_va_khong_ghi_thu_that_bai():
    fake = FakeMailer(loi=LoiGuiMail("Máy chủ thư không phản hồi."))

    with pytest.raises(LoiGuiMail, match="không phản hồi"):
        fake.gui("khach@example.com", "Tiêu đề", "Nội dung")

    assert fake.da_gui == []


def test_console_mailer_in_thu_ra_log_de_chay_cuc_bo_khong_can_smtp(caplog):
    with caplog.at_level(logging.INFO, logger="app.mail"):
        ConsoleMailer().gui("khach@example.com", "Xác minh email", "Liên kết: http://127.0.0.1:8000/x")

    log = caplog.text
    assert "khach@example.com" in log
    assert "Xác minh email" in log
    assert "http://127.0.0.1:8000/x" in log


def test_lay_mailer_console_la_bo_gui_mac_dinh_khi_chay_cuc_bo(monkeypatch):
    monkeypatch.setattr(settings, "mail_provider", "console")

    assert type(lay_mailer()) is ConsoleMailer


def test_lay_mailer_smtp_doc_host_va_nguoi_gui_tu_cau_hinh(monkeypatch):
    from app.mail.smtp import SmtpMailer

    monkeypatch.setattr(settings, "mail_provider", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", 2525)
    monkeypatch.setattr(settings, "mail_from", "Petcare <noreply@example.com>")

    mailer = lay_mailer()

    assert isinstance(mailer, SmtpMailer)
    assert (mailer.host, mailer.port, mailer.nguoi_gui) == ("127.0.0.1", 2525, "Petcare <noreply@example.com>")


def test_lay_mailer_smtp_thieu_host_bao_loi_cau_hinh_ro_rang(monkeypatch):
    monkeypatch.setattr(settings, "mail_provider", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "")

    with pytest.raises(LoiGuiMail, match="SMTP_HOST"):
        lay_mailer()


def test_lay_mailer_ten_la_bao_loi_thay_vi_im_lang_roi_ve_console(monkeypatch):
    """Gõ nhầm `MAIL_PROVIDER=smpt` mà âm thầm in thư ra log thì khách không bao giờ nhận được mail."""
    monkeypatch.setattr(settings, "mail_provider", "smpt")

    with pytest.raises(LoiGuiMail, match="MAIL_PROVIDER"):
        lay_mailer()
