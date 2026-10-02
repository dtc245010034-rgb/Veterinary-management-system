"""Test cho app/services/customers.py — tài khoản khách hàng (P9 chặng 4, đợt 4a).

Khách chỉ có dòng trong `customers` SAU KHI đã xác minh email và tự đặt mật khẩu: không có
tài khoản "chưa xác minh" để kẻ khác đăng ký trước bằng email của nạn nhân rồi đợi họ bấm link.
"""

import re

import pytest
from sqlalchemy import select

from app.mail.fake import FakeMailer
from app.mail.provider import LoiGuiMail
from app.models.customer import Customer
from app.security import verify_password
from app.services import customers as kh
from app.services import email_tokens
from app.services.errors import LoiNghiepVu

GOC = "https://shop.example.com"
MAT_KHAU = "matkhau-khach-1"


def _token_trong_thu(thu) -> str:
    khop = re.search(r"/(?:dang-ky|dat-lai)/([A-Za-z0-9_-]+)", thu.noi_dung)
    assert khop, f"Thư không có liên kết: {thu.noi_dung!r}"
    return khop.group(1)


def _dang_ky_xong(db, email="khach@example.com", ten="Nguyen Khach", mat_khau=MAT_KHAU) -> Customer:
    mailer = FakeMailer()
    kh.yeu_cau_dang_ky(db, mailer, email, GOC)
    return kh.hoan_tat_dang_ky(db, _token_trong_thu(mailer.da_gui[0]), ten, mat_khau)


# --- Đăng ký ---------------------------------------------------------------------


def test_yeu_cau_dang_ky_gui_dung_mot_thu_co_lien_ket_goc_cau_hinh_va_khong_tao_tai_khoan(db, frozen_clock):
    mailer = FakeMailer()

    kh.yeu_cau_dang_ky(db, mailer, "  Khach@Example.COM ", GOC)

    assert len(mailer.da_gui) == 1
    thu = mailer.da_gui[0]
    assert thu.den == "khach@example.com"
    assert f"{GOC}/khach/dang-ky/" in thu.noi_dung
    assert db.scalars(select(Customer)).all() == []


def test_hoan_tat_dang_ky_tao_khach_voi_email_trong_token_va_mat_khau_da_bam(db, frozen_clock):
    khach = _dang_ky_xong(db, email="Khach@Example.com", ten="  Nguyen Khach ")

    assert khach.email == "khach@example.com"
    assert khach.full_name == "Nguyen Khach"
    assert khach.password_hash != MAT_KHAU
    assert verify_password(MAT_KHAU, khach.password_hash)
    assert khach.is_active and khach.owner_id is None


def test_email_khong_hop_le_bi_tu_choi_va_khong_gui_thu(db, frozen_clock):
    mailer = FakeMailer()

    for xau in ("", "khong-co-a-cong", "a@b", "a b@example.com", "a@example.com\r\nBcc: x@y.com"):
        with pytest.raises(LoiNghiepVu, match="Email"):
            kh.yeu_cau_dang_ky(db, mailer, xau, GOC)

    assert mailer.da_gui == []


def test_dang_ky_voi_email_da_co_tai_khoan_gui_thu_bao_chu_khong_cap_token_va_khong_ten_loi(db, frozen_clock):
    _dang_ky_xong(db)
    mailer = FakeMailer()

    kh.yeu_cau_dang_ky(db, mailer, "khach@example.com", GOC)  # không ném

    assert len(mailer.da_gui) == 1
    assert "/khach/dang-ky/" not in mailer.da_gui[0].noi_dung  # không có liên kết đăng ký mới
    assert "đã có tài khoản" in mailer.da_gui[0].noi_dung
    assert len(db.scalars(select(Customer)).all()) == 1


def test_loi_gui_thu_khong_lo_ra_ngoai_de_khong_phan_biet_email_co_hay_chua_co(db, frozen_clock):
    """Cả hai nhánh (email mới / email đã có) cùng nuốt lỗi gửi thư: người gọi không đoán được gì từ lỗi."""
    _dang_ky_xong(db)
    hong = FakeMailer(loi=LoiGuiMail("Máy chủ thư không phản hồi."))

    kh.yeu_cau_dang_ky(db, hong, "khach@example.com", GOC)
    kh.yeu_cau_dang_ky(db, hong, "moi@example.com", GOC)

    assert hong.da_gui == []


def test_hoan_tat_dang_ky_mat_khau_yeu_bi_tu_choi_va_khong_dot_token(db, frozen_clock):
    """Gõ mật khẩu ngắn rồi sửa lại không được mất liên kết."""
    mailer = FakeMailer()
    kh.yeu_cau_dang_ky(db, mailer, "khach@example.com", GOC)
    token = _token_trong_thu(mailer.da_gui[0])

    with pytest.raises(LoiNghiepVu, match="ít nhất 8 ký tự"):
        kh.hoan_tat_dang_ky(db, token, "Nguyen Khach", "ngan")
    with pytest.raises(LoiNghiepVu, match="Họ tên"):
        kh.hoan_tat_dang_ky(db, token, "   ", MAT_KHAU)

    assert kh.hoan_tat_dang_ky(db, token, "Nguyen Khach", MAT_KHAU).email == "khach@example.com"


def test_hoan_tat_dang_ky_dung_lai_lien_ket_bi_tu_choi(db, frozen_clock):
    mailer = FakeMailer()
    kh.yeu_cau_dang_ky(db, mailer, "khach@example.com", GOC)
    token = _token_trong_thu(mailer.da_gui[0])
    kh.hoan_tat_dang_ky(db, token, "Nguyen Khach", MAT_KHAU)

    with pytest.raises(LoiNghiepVu, match="không hợp lệ hoặc đã hết hạn"):
        kh.hoan_tat_dang_ky(db, token, "Nguoi Khac", "mat-khau-khac-1")

    assert len(db.scalars(select(Customer)).all()) == 1


def test_token_dat_lai_mat_khau_khong_dung_duoc_de_dang_ky(db, frozen_clock):
    token = email_tokens.cap_token(db, "khach@example.com", "reset_password")

    with pytest.raises(LoiNghiepVu):
        kh.hoan_tat_dang_ky(db, token, "Nguyen Khach", MAT_KHAU)


def test_lien_ket_dang_ky_cua_email_da_co_tai_khoan_bi_tu_choi_khong_ghi_de(db, frozen_clock):
    """Đua: hai thư đăng ký cùng email, bấm cả hai. Lần thứ hai không được ghi đè mật khẩu lần đầu."""
    mailer = FakeMailer()
    kh.yeu_cau_dang_ky(db, mailer, "khach@example.com", GOC)
    token = _token_trong_thu(mailer.da_gui[0])
    # Dựng tình huống: tài khoản đã được tạo bằng đường khác trong lúc token còn hạn.
    db.add(Customer(email="khach@example.com", full_name="Chủ thật", password_hash="x"))
    db.commit()

    with pytest.raises(LoiNghiepVu):
        kh.hoan_tat_dang_ky(db, token, "Kẻ đến sau", MAT_KHAU)

    assert db.scalars(select(Customer)).one().full_name == "Chủ thật"


# --- Đăng nhập -------------------------------------------------------------------


def test_xac_thuc_dung_email_va_mat_khau_tra_ve_khach(db, frozen_clock):
    khach = _dang_ky_xong(db)

    assert kh.xac_thuc(db, "  KHACH@example.com ", MAT_KHAU).id == khach.id


def test_xac_thuc_sai_mat_khau_va_email_la_cung_mot_thong_bao(db, frozen_clock):
    _dang_ky_xong(db)

    with pytest.raises(LoiNghiepVu) as sai_mk:
        kh.xac_thuc(db, "khach@example.com", "sai-mat-khau")
    with pytest.raises(LoiNghiepVu) as sai_email:
        kh.xac_thuc(db, "ai-do@example.com", MAT_KHAU)

    assert str(sai_mk.value) == str(sai_email.value) == kh.LOI_DANG_NHAP


def test_xac_thuc_tai_khoan_bi_khoa_bi_tu_choi_du_dung_mat_khau(db, frozen_clock):
    khach = _dang_ky_xong(db)
    khach.is_active = False
    db.commit()

    with pytest.raises(LoiNghiepVu, match="ngưng hoạt động"):
        kh.xac_thuc(db, "khach@example.com", MAT_KHAU)


# --- Quên mật khẩu ---------------------------------------------------------------


def test_yeu_cau_dat_lai_gui_thu_cho_khach_co_that(db, frozen_clock):
    _dang_ky_xong(db)
    mailer = FakeMailer()

    kh.yeu_cau_dat_lai(db, mailer, "KHACH@example.com", GOC)

    assert len(mailer.da_gui) == 1
    assert f"{GOC}/khach/dat-lai/" in mailer.da_gui[0].noi_dung


def test_yeu_cau_dat_lai_voi_email_la_khong_gui_gi_va_khong_ten_loi(db, frozen_clock):
    mailer = FakeMailer()

    kh.yeu_cau_dat_lai(db, mailer, "khong-ai@example.com", GOC)

    assert mailer.da_gui == []
    assert db.scalars(select(Customer)).all() == []


def test_yeu_cau_dat_lai_voi_tai_khoan_bi_khoa_khong_gui_thu(db, frozen_clock):
    khach = _dang_ky_xong(db)
    khach.is_active = False
    db.commit()
    mailer = FakeMailer()

    kh.yeu_cau_dat_lai(db, mailer, "khach@example.com", GOC)

    assert mailer.da_gui == []


def test_dat_lai_mat_khau_doi_mat_khau_thu_hoi_phien_va_lien_ket_chi_dung_mot_lan(db, frozen_clock):
    khach = _dang_ky_xong(db)
    phien_cu = khach.session_version
    mailer = FakeMailer()
    kh.yeu_cau_dat_lai(db, mailer, "khach@example.com", GOC)
    token = _token_trong_thu(mailer.da_gui[0])

    kh.dat_lai_mat_khau(db, token, "mat-khau-moi-123")

    assert kh.xac_thuc(db, "khach@example.com", "mat-khau-moi-123").id == khach.id
    with pytest.raises(LoiNghiepVu):
        kh.xac_thuc(db, "khach@example.com", MAT_KHAU)
    db.refresh(khach)
    assert khach.session_version == phien_cu + 1
    with pytest.raises(LoiNghiepVu, match="không hợp lệ hoặc đã hết hạn"):
        kh.dat_lai_mat_khau(db, token, "mat-khau-khac-456")


def test_dat_lai_mat_khau_yeu_bi_tu_choi_va_khong_dot_token(db, frozen_clock):
    _dang_ky_xong(db)
    mailer = FakeMailer()
    kh.yeu_cau_dat_lai(db, mailer, "khach@example.com", GOC)
    token = _token_trong_thu(mailer.da_gui[0])

    with pytest.raises(LoiNghiepVu, match="ít nhất 8 ký tự"):
        kh.dat_lai_mat_khau(db, token, "ngan")

    kh.dat_lai_mat_khau(db, token, "mat-khau-moi-123")  # liên kết vẫn dùng được


def test_token_dang_ky_khong_dung_duoc_de_dat_lai_mat_khau(db, frozen_clock):
    _dang_ky_xong(db)
    token = email_tokens.cap_token(db, "khach@example.com", "verify_email")

    with pytest.raises(LoiNghiepVu):
        kh.dat_lai_mat_khau(db, token, "mat-khau-moi-123")


# --- Đổi mật khẩu, thu hồi phiên ---------------------------------------------------


def test_doi_mat_khau_can_mat_khau_cu_dung_va_thu_hoi_phien(db, frozen_clock):
    khach = _dang_ky_xong(db)
    phien_cu = khach.session_version

    with pytest.raises(LoiNghiepVu, match="không đúng"):
        kh.doi_mat_khau(db, khach, "sai-mat-khau", "mat-khau-moi-123")
    with pytest.raises(LoiNghiepVu, match="ít nhất 8 ký tự"):
        kh.doi_mat_khau(db, khach, MAT_KHAU, "ngan")

    kh.doi_mat_khau(db, khach, MAT_KHAU, "mat-khau-moi-123")

    assert kh.xac_thuc(db, "khach@example.com", "mat-khau-moi-123").id == khach.id
    assert khach.session_version == phien_cu + 1


def test_thu_hoi_phien_tang_so_phien_ban(db, frozen_clock):
    khach = _dang_ky_xong(db)

    kh.thu_hoi_phien(db, khach.id)

    db.refresh(khach)
    assert khach.session_version == 1


def test_thu_hoi_phien_khach_khong_ton_tai_bao_loi_khong_tim_thay(db):
    from app.services.errors import LoiKhongTimThay

    with pytest.raises(LoiKhongTimThay):
        kh.thu_hoi_phien(db, 999)
