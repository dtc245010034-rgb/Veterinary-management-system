"""Test cho app/services/email_tokens.py — token xác minh email và đặt lại mật khẩu (P9 chặng 3).

Token gắn với (email, mục đích), không gắn với tài khoản: lúc đăng ký chưa có tài khoản nào.
CSDL chỉ giữ băm SHA-256; chuỗi thô chỉ tồn tại trong thư gửi đi.
"""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.email_token import EmailToken
from app.services import clock
from app.services import email_tokens as nv
from app.services.errors import LoiNghiepVu

XAC_MINH = "verify_email"
DAT_LAI = "reset_password"


# --- Cấp và dùng token ----------------------------------------------------------


def test_cap_token_roi_dung_token_tra_ve_dung_email(db, frozen_clock):
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    assert nv.dung_token(db, token, XAC_MINH) == "khach@example.com"


def test_email_duoc_chuan_hoa_chu_thuong_va_cat_khoang_trang(db, frozen_clock):
    token = nv.cap_token(db, "  Khach@Example.COM ", XAC_MINH)

    assert nv.dung_token(db, token, XAC_MINH) == "khach@example.com"


def test_token_ngau_nhien_khong_trung_nhau_va_du_dai(db, frozen_clock):
    a = nv.cap_token(db, "a@example.com", XAC_MINH)
    b = nv.cap_token(db, "b@example.com", XAC_MINH)

    assert a != b
    assert len(a) >= 32


def test_csdl_khong_chua_token_tho_chi_chua_ban_bam(db, frozen_clock):
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    dong = db.scalars(select(EmailToken)).one()
    assert token not in dong.token_hash
    assert token not in str(dong.__dict__)
    assert len(dong.token_hash) == 64  # SHA-256 dạng hex


# --- Dùng một lần ---------------------------------------------------------------


def test_dung_lai_token_da_dung_bi_tu_choi(db, frozen_clock):
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)
    nv.dung_token(db, token, XAC_MINH)

    with pytest.raises(LoiNghiepVu, match="không hợp lệ hoặc đã hết hạn"):
        nv.dung_token(db, token, XAC_MINH)


def test_dung_that_bai_khong_danh_dau_da_dung(db, frozen_clock):
    """Dùng sai mục đích rồi dùng đúng mục đích: lần đúng vẫn phải được."""
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    with pytest.raises(LoiNghiepVu):
        nv.dung_token(db, token, DAT_LAI)

    assert nv.dung_token(db, token, XAC_MINH) == "khach@example.com"


def test_danh_dau_da_dung_la_mot_lenh_nguyen_tu_nen_doi_tuong_cu_trong_bo_nho_khong_danh_lua_duoc(db, frozen_clock):
    """Đua: request A và B cùng đọc dòng khi `used_at` còn trống; A dùng xong, B vẫn thấy `None` trong bộ nhớ.

    Dựng đúng tình huống đó: nạp dòng vào session, rồi đánh dấu đã dùng bằng lệnh SQL bỏ qua ORM — đối
    tượng trong bộ nhớ vẫn nói `used_at is None`. Mã kiểm bằng thuộc tính đối tượng sẽ cho lượt hai lọt qua;
    chỉ `UPDATE … WHERE used_at IS NULL` rồi đọc `rowcount` mới từ chối đúng.
    """
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)
    dong = db.scalars(select(EmailToken)).one()
    db.execute(EmailToken.__table__.update().values(used_at=clock.now()))
    assert dong.used_at is None  # xác nhận tình huống đã dựng đúng: bộ nhớ lạc hậu

    with pytest.raises(LoiNghiepVu):
        nv.dung_token(db, token, XAC_MINH)


# --- Hết hạn ---------------------------------------------------------------------


def test_token_xac_minh_con_dung_duoc_truoc_han_24_gio(db):
    with clock.freeze(datetime(2026, 3, 12, 8, 0)):
        token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    with clock.freeze(datetime(2026, 3, 13, 7, 59, 59)):
        assert nv.dung_token(db, token, XAC_MINH) == "khach@example.com"


def test_token_xac_minh_het_han_dung_luc_24_gio(db):
    with clock.freeze(datetime(2026, 3, 12, 8, 0)):
        token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    with clock.freeze(datetime(2026, 3, 13, 8, 0)):
        with pytest.raises(LoiNghiepVu, match="không hợp lệ hoặc đã hết hạn"):
            nv.dung_token(db, token, XAC_MINH)


def test_token_dat_lai_mat_khau_chi_song_1_gio(db):
    with clock.freeze(datetime(2026, 3, 12, 8, 0)):
        token = nv.cap_token(db, "khach@example.com", DAT_LAI)

    with clock.freeze(datetime(2026, 3, 12, 8, 59, 59)):
        assert nv.dung_token(db, token, DAT_LAI) == "khach@example.com"


def test_token_dat_lai_mat_khau_het_han_sau_1_gio(db):
    with clock.freeze(datetime(2026, 3, 12, 8, 0)):
        token = nv.cap_token(db, "khach@example.com", DAT_LAI)

    with clock.freeze(datetime(2026, 3, 12, 9, 0)):
        with pytest.raises(LoiNghiepVu):
            nv.dung_token(db, token, DAT_LAI)


def test_dung_token_het_han_khong_danh_dau_da_dung(db):
    with clock.freeze(datetime(2026, 3, 12, 8, 0)):
        token = nv.cap_token(db, "khach@example.com", DAT_LAI)

    with clock.freeze(datetime(2026, 3, 12, 10, 0)):
        with pytest.raises(LoiNghiepVu):
            nv.dung_token(db, token, DAT_LAI)

    assert db.scalars(select(EmailToken)).one().used_at is None


# --- Sai mục đích, chuỗi bịa -----------------------------------------------------


def test_token_xac_minh_khong_dung_duoc_de_dat_lai_mat_khau(db, frozen_clock):
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    with pytest.raises(LoiNghiepVu, match="không hợp lệ hoặc đã hết hạn"):
        nv.dung_token(db, token, DAT_LAI)


def test_chuoi_bia_va_chuoi_rong_bi_tu_choi_cung_mot_thong_bao(db, frozen_clock):
    nv.cap_token(db, "khach@example.com", XAC_MINH)

    thong_bao = set()
    for token in ("", "abc", "x" * 200, "khach@example.com"):
        with pytest.raises(LoiNghiepVu) as loi:
            nv.dung_token(db, token, XAC_MINH)
        thong_bao.add(str(loi.value))

    assert len(thong_bao) == 1


def test_sai_muc_dich_va_chuoi_bia_cung_thong_bao_de_khong_lo_token_co_ton_tai(db, frozen_clock):
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    with pytest.raises(LoiNghiepVu) as sai_muc_dich:
        nv.dung_token(db, token, DAT_LAI)
    with pytest.raises(LoiNghiepVu) as bia:
        nv.dung_token(db, "chuoi-bia", DAT_LAI)

    assert str(sai_muc_dich.value) == str(bia.value)


def test_cap_token_voi_muc_dich_la_bi_tu_choi(db, frozen_clock):
    with pytest.raises(ValueError):
        nv.cap_token(db, "khach@example.com", "xoa_tai_khoan")


# --- Cấp token mới vô hiệu token cũ ---------------------------------------------


def test_cap_token_moi_vo_hieu_token_cu_cung_email_va_muc_dich(db, frozen_clock):
    cu = nv.cap_token(db, "khach@example.com", XAC_MINH)
    moi = nv.cap_token(db, "khach@example.com", XAC_MINH)

    with pytest.raises(LoiNghiepVu):
        nv.dung_token(db, cu, XAC_MINH)
    assert nv.dung_token(db, moi, XAC_MINH) == "khach@example.com"


def test_cap_token_moi_khong_dung_den_token_cua_email_khac_hoac_muc_dich_khac(db, frozen_clock):
    cua_khac = nv.cap_token(db, "khac@example.com", XAC_MINH)
    cung_email_khac_muc_dich = nv.cap_token(db, "khach@example.com", DAT_LAI)
    nv.cap_token(db, "khach@example.com", XAC_MINH)

    assert nv.dung_token(db, cua_khac, XAC_MINH) == "khac@example.com"
    assert nv.dung_token(db, cung_email_khac_muc_dich, DAT_LAI) == "khach@example.com"


# --- Xem token mà không tiêu thụ ------------------------------------------------


def test_con_hieu_luc_chi_doc_khong_dot_token(db, frozen_clock):
    token = nv.cap_token(db, "khach@example.com", XAC_MINH)

    assert nv.con_hieu_luc(db, token, XAC_MINH) is True
    assert nv.con_hieu_luc(db, token, XAC_MINH) is True  # đọc hai lần vẫn còn
    assert nv.dung_token(db, token, XAC_MINH) == "khach@example.com"


def test_con_hieu_luc_sai_voi_chuoi_bia_sai_muc_dich_da_dung_va_het_han(db):
    with clock.freeze(datetime(2026, 3, 12, 8, 0)):
        token = nv.cap_token(db, "khach@example.com", DAT_LAI)
        da_dung = nv.cap_token(db, "khac@example.com", DAT_LAI)
        nv.dung_token(db, da_dung, DAT_LAI)

        assert nv.con_hieu_luc(db, "chuoi-bia", DAT_LAI) is False
        assert nv.con_hieu_luc(db, token, XAC_MINH) is False
        assert nv.con_hieu_luc(db, da_dung, DAT_LAI) is False

    with clock.freeze(datetime(2026, 3, 12, 9, 0)):
        assert nv.con_hieu_luc(db, token, DAT_LAI) is False
