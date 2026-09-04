"""Test cho app/services/text.py — chuẩn hóa chuỗi tiếng Việt để tìm kiếm.

Phục vụ TC-022 (US-06): gõ "mun" phải ra thú cưng tên "Mun", "MUN"; gõ "muc" phải ra "Mực".

SQLite không có unaccent như PostgreSQL, và LIKE của nó chỉ bỏ phân biệt hoa thường với
ASCII. Nên hệ thống lưu sẵn bản đã chuẩn hóa vào cột search_name và tìm trên cột đó.
"""

import pytest

from app.services.text import chuan_hoa


@pytest.mark.parametrize(
    "goc, mong_doi",
    [
        ("Mực", "muc"),
        ("MỰC", "muc"),
        ("Mun", "mun"),
        ("Trần Thị Lễ", "tran thi le"),
        ("Nguyễn Văn Quản", "nguyen van quan"),
        ("Phạm Thị Sóc", "pham thi soc"),
        ("Lê Văn Chăm", "le van cham"),
    ],
)
def test_bo_dau_va_thuong_hoa(goc, mong_doi):
    assert chuan_hoa(goc) == mong_doi


@pytest.mark.parametrize(
    "goc, mong_doi",
    [
        ("Đen", "den"),
        ("ĐEN", "den"),
        ("Đậu Đỏ", "dau do"),
        ("bánh đúc", "banh duc"),
    ],
)
def test_chu_d_gach_ngang_thanh_d_thuong(goc, mong_doi):
    """Chữ đ/Đ là cái bẫy riêng của tiếng Việt.

    Nó KHÔNG phải nguyên âm mang dấu tổ hợp, mà là một ký tự Latin riêng, nên
    unicodedata.normalize('NFD') không tách được gì và đ sẽ sót lại nguyên. Phải thay tay.

    Bỏ sót chỗ này thì gõ "dau do" sẽ không ra "Đậu Đỏ" — đúng loại lỗi mà người dùng
    gặp hàng ngày còn lập trình viên không bao giờ thấy vì toàn gõ có dấu.
    """
    assert chuan_hoa(goc) == mong_doi


@pytest.mark.parametrize(
    "goc, mong_doi",
    [
        ("  Mun  ", "mun"),
        ("Mun   Đen", "mun den"),
        ("\tMực\n", "muc"),
    ],
)
def test_gom_khoang_trang_thua(goc, mong_doi):
    """Người dùng gõ vội hay để dư khoảng trắng; không được vì thế mà tìm hụt."""
    assert chuan_hoa(goc) == mong_doi


def test_chuoi_rong_tra_ve_rong():
    assert chuan_hoa("") == ""
    assert chuan_hoa("   ") == ""


def test_giu_nguyen_chu_so_va_ky_tu_ascii():
    assert chuan_hoa("Mun 2") == "mun 2"
    assert chuan_hoa("0912345678") == "0912345678"
