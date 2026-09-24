"""Test cho app/services/tien.py — đọc số tiền người dùng gõ vào form.

Sinh ra từ L-03 (rà 19/09, đo lại bằng Chrome 24/09): gõ `1234.56` vào ô giá thì hệ
thống lưu **123.456đ** — dấu chấm bị bỏ đi như phân cách nghìn. Thu tiền `0,5` thành 5đ
và được ghi nhận. Cả hai đều là sai số tiền, âm thầm, không thông báo gì.

Người dùng chốt 24/09: **chỉ nhận số nguyên đồng**. Phân cách nghìn vẫn gõ được, nhưng
chuỗi có phần lẻ thì **từ chối** thay vì đoán.

Luật cũ nằm trùng nhau ở hai router (`services.py` và `invoices.py`) — sửa một chỗ quên
chỗ kia là chuyện chắc chắn xảy ra, nên gom về một hàm.
"""

from decimal import Decimal

import pytest

from app.services.errors import LoiNghiepVu
from app.services.tien import doc_tien


@pytest.mark.parametrize(
    "go_vao, mong_doi",
    [
        ("150000", "150000"),
        ("150.000", "150000"),
        ("150 000", "150000"),
        ("150,000", "150000"),
        ("1.234.567", "1234567"),
        ("0", "0"),
        ("  150000  ", "150000"),
    ],
)
def test_cac_cach_go_phan_cach_nghin_deu_ra_dung_so(go_vao, mong_doi):
    assert doc_tien(go_vao, "Giá") == Decimal(mong_doi)


@pytest.mark.parametrize("go_vao", ["1234.56", "0,5", "150.5", "1.234,56", "12,25"])
def test_chuoi_co_phan_le_bi_tu_choi(go_vao):
    """Hai ca đầu là ca đo được thật trên trình duyệt."""
    with pytest.raises(LoiNghiepVu) as e:
        doc_tien(go_vao, "Giá")

    assert "nguyên" in str(e.value)


@pytest.mark.parametrize("go_vao", ["abc", "12abc", "NaN", "Infinity", "-", "1..2"])
def test_chuoi_khong_phai_so_bi_tu_choi(go_vao):
    """`NaN` và `Infinity` từng thành lỗi 500 (rà 11/09) — giữ nguyên phép chặn đó."""
    with pytest.raises(LoiNghiepVu):
        doc_tien(go_vao, "Giá")


def test_o_trong_tra_ve_None_de_tang_tren_phan_biet():
    """Không nhập gì khác với nhập số 0 — hai thông báo khác nhau ở tầng nghiệp vụ."""
    assert doc_tien("", "Giá") is None
    assert doc_tien("   ", "Giá") is None


def test_so_am_van_doc_duoc_de_tang_nghiep_vu_tu_tu_choi():
    """Ranh giới trách nhiệm: hàm này đọc, `catalog._kiem_gia` mới quyết âm hay dương.

    Trả lỗi ngay tại đây sẽ làm mất câu "Giá không được là số âm." đang có.
    """
    assert doc_tien("-1000", "Giá") == Decimal("-1000")


def test_ten_truong_di_vao_thong_bao():
    """Cùng một hàm phục vụ ô Giá và ô Số tiền — thông báo phải gọi đúng tên ô."""
    with pytest.raises(LoiNghiepVu) as e:
        doc_tien("1234.56", "Số tiền")

    assert "Số tiền" in str(e.value)
