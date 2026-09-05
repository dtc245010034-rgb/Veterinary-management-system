"""Test cho app/services/catalog.py — nghiệp vụ dịch vụ và gói dịch vụ.

Phục vụ US-07, US-08, US-09 — TC-024, TC-025, TC-026, TC-027, TC-028, TC-029, TC-030.
"""

from decimal import Decimal

import pytest

from app.services import catalog as nv
from app.services.errors import LoiNghiepVu


def them_dich_vu(db, ma="TAM", ten="Tắm cho chó", gia="150000", phut=45):
    return nv.tao_dich_vu(db, ma=ma, ten=ten, gia=Decimal(gia), thoi_luong_phut=phut)


# --- Dịch vụ ---------------------------------------------------------------------


def test_tao_dich_vu_thanh_cong(db):
    """TC-024."""
    s = them_dich_vu(db)

    assert s.id is not None
    assert s.is_active is True


def test_dich_vu_moi_nam_trong_danh_sach_dang_ban(db):
    """TC-024: đây chính là danh sách mà form đặt lịch ở P3 sẽ dùng."""
    them_dich_vu(db, ma="TAM")

    assert [s.code for s in nv.danh_sach_dang_ban(db)] == ["TAM"]


@pytest.mark.parametrize("gia, phut", [("-1000", 45), ("150000", 0), ("150000", -30)])
def test_gia_am_hoac_thoi_luong_khong_duong_bi_tu_choi(db, gia, phut):
    """TC-025: báo lỗi nghiệp vụ có thông báo tiếng Việt, không phải IntegrityError."""
    with pytest.raises(LoiNghiepVu):
        them_dich_vu(db, gia=gia, phut=phut)


def test_thieu_ma_hoac_ten_bi_tu_choi(db):
    with pytest.raises(LoiNghiepVu):
        them_dich_vu(db, ma="", ten="Tắm")

    with pytest.raises(LoiNghiepVu):
        them_dich_vu(db, ma="TAM", ten="  ")


def test_ma_dich_vu_trung_bi_tu_choi_kem_thong_bao(db):
    them_dich_vu(db, ma="TAM")

    with pytest.raises(LoiNghiepVu) as loi:
        them_dich_vu(db, ma="TAM", ten="Tắm khác")

    assert "TAM" in str(loi.value)


def test_ma_dich_vu_luon_luu_chu_hoa(db):
    """Mã gõ thường và gõ hoa phải là cùng một mã, nếu không sẽ có hai dịch vụ trùng."""
    s = them_dich_vu(db, ma="tam")

    assert s.code == "TAM"

    with pytest.raises(LoiNghiepVu):
        them_dich_vu(db, ma="TAM", ten="Trùng")


def test_doi_gia_dich_vu(db):
    """TC-026, phần làm được ở P2b.

    Phần "hóa đơn cũ giữ nguyên giá" chỉ kiểm được ở P5, khi có invoice_items chép sẵn
    đơn giá tại thời điểm lập.
    """
    s = them_dich_vu(db, gia="150000")

    nv.sua_dich_vu(db, s.id, gia=Decimal("180000"))

    assert nv.lay_dich_vu(db, s.id).price == Decimal("180000")


def test_doi_gia_thanh_so_am_bi_tu_choi(db):
    s = them_dich_vu(db)

    with pytest.raises(LoiNghiepVu):
        nv.sua_dich_vu(db, s.id, gia=Decimal("-1"))


# --- Ngưng bán --------------------------------------------------------------------


def test_ngung_ban_thi_bien_khoi_danh_sach_dang_ban(db):
    """TC-030: đây là cơ chế P3 dựa vào để không cho đặt lịch dịch vụ đã ngưng."""
    a = them_dich_vu(db, ma="TAM")
    them_dich_vu(db, ma="CATMONG", ten="Cắt móng")

    nv.ngung_ban(db, a.id)

    assert [s.code for s in nv.danh_sach_dang_ban(db)] == ["CATMONG"]


def test_ngung_ban_khong_xoa_du_lieu(db):
    """US-09: bản ghi phải còn nguyên để lịch hẹn và hóa đơn cũ vẫn tham chiếu được."""
    a = them_dich_vu(db, ma="TAM", ten="Tắm cho chó")

    nv.ngung_ban(db, a.id)

    van_con = nv.lay_dich_vu(db, a.id)
    assert van_con.name == "Tắm cho chó"
    assert van_con.is_active is False


def test_ban_lai_dich_vu_da_ngung(db):
    a = them_dich_vu(db, ma="TAM")
    nv.ngung_ban(db, a.id)

    nv.ban_lai(db, a.id)

    assert [s.code for s in nv.danh_sach_dang_ban(db)] == ["TAM"]


def test_danh_sach_tat_ca_van_hien_ca_dich_vu_da_ngung(db):
    """Quản lý phải thấy được dịch vụ đã ngưng để bật lại."""
    a = them_dich_vu(db, ma="TAM")
    them_dich_vu(db, ma="CATMONG", ten="Cắt móng")
    nv.ngung_ban(db, a.id)

    assert len(nv.danh_sach_dich_vu(db)) == 2


# --- Gói dịch vụ ------------------------------------------------------------------


def test_tao_goi_voi_thanh_phan(db):
    """TC-027."""
    a = them_dich_vu(db, ma="TAM", gia="150000")
    b = them_dich_vu(db, ma="CATMONG", ten="Cắt móng", gia="50000")

    goi = nv.tao_goi(db, ten="Combo cơ bản", gia=Decimal("180000"), thanh_phan={a.id: 1, b.id: 2})

    assert goi.tong_gia_le == Decimal("250000")
    assert goi.tiet_kiem == Decimal("70000")


def test_goi_khong_co_thanh_phan_bi_tu_choi(db):
    """TC-029."""
    with pytest.raises(LoiNghiepVu):
        nv.tao_goi(db, ten="Gói rỗng", gia=Decimal("100000"), thanh_phan={})


def test_goi_chua_dich_vu_khong_ton_tai_bi_tu_choi(db):
    with pytest.raises(LoiNghiepVu):
        nv.tao_goi(db, ten="Gói lỗi", gia=Decimal("100000"), thanh_phan={9999: 1})


def test_goi_gia_am_bi_tu_choi(db):
    a = them_dich_vu(db, ma="TAM")

    with pytest.raises(LoiNghiepVu):
        nv.tao_goi(db, ten="Gói lỗi", gia=Decimal("-1"), thanh_phan={a.id: 1})


def test_goi_so_luong_khong_duong_bi_tu_choi(db):
    a = them_dich_vu(db, ma="TAM")

    with pytest.raises(LoiNghiepVu):
        nv.tao_goi(db, ten="Gói lỗi", gia=Decimal("100000"), thanh_phan={a.id: 0})


def test_goi_chua_dich_vu_da_ngung_ban_bi_tu_choi(db):
    """Bán một gói chứa dịch vụ không còn cung cấp là hứa với khách thứ không giao được."""
    a = them_dich_vu(db, ma="TAM")
    nv.ngung_ban(db, a.id)

    with pytest.raises(LoiNghiepVu):
        nv.tao_goi(db, ten="Gói lỗi", gia=Decimal("100000"), thanh_phan={a.id: 1})


def test_goi_dat_hon_tong_gia_le_van_luu_duoc_nhung_tiet_kiem_am(db):
    """Không cấm — quản lý có thể gộp gói vì lý do khác giá. Nhưng số liệu phải trung thực."""
    a = them_dich_vu(db, ma="TAM", gia="100000")

    goi = nv.tao_goi(db, ten="Gói đắt", gia=Decimal("120000"), thanh_phan={a.id: 1})

    assert goi.tiet_kiem == Decimal("-20000")


def test_ngung_ban_goi(db):
    a = them_dich_vu(db, ma="TAM")
    goi = nv.tao_goi(db, ten="Combo", gia=Decimal("100000"), thanh_phan={a.id: 1})

    nv.ngung_ban_goi(db, goi.id)

    assert nv.danh_sach_goi_dang_ban(db) == []
    assert len(nv.danh_sach_goi(db)) == 1


# --- Bù bao phủ: lay_goi và ban_lai_goi -------------------------------------------
#
# Hai hàm này có từ P2b nhưng chỉ chạy qua router. Luật bao phủ ở CLAUDE.md mục 7 đòi
# gọi thẳng, tối thiểu 1 happy path + 1 ca biên.


def test_lay_goi_tra_ve_dung_ban_ghi_kem_thanh_phan(db):
    a = them_dich_vu(db, ma="TAM")
    goi = nv.tao_goi(db, ten="Combo cơ bản", gia=Decimal("180000"), thanh_phan={a.id: 2})

    lay_ra = nv.lay_goi(db, goi.id)

    assert lay_ra.name == "Combo cơ bản"
    assert [(m.service_id, m.quantity) for m in lay_ra.items] == [(a.id, 2)]


def test_lay_goi_khong_ton_tai_nem_loi_nghiep_vu(db):
    with pytest.raises(LoiNghiepVu):
        nv.lay_goi(db, 9999)


def test_ban_lai_goi_da_ngung_thi_hien_lai_trong_danh_sach_dang_ban(db):
    a = them_dich_vu(db, ma="TAM")
    goi = nv.tao_goi(db, ten="Combo cơ bản", gia=Decimal("180000"), thanh_phan={a.id: 1})
    nv.ngung_ban_goi(db, goi.id)
    assert goi.id not in [g.id for g in nv.danh_sach_goi_dang_ban(db)]

    nv.ban_lai_goi(db, goi.id)

    assert goi.is_active is True
    assert goi.id in [g.id for g in nv.danh_sach_goi_dang_ban(db)]


def test_ban_lai_goi_khong_ton_tai_bi_tu_choi(db):
    with pytest.raises(LoiNghiepVu):
        nv.ban_lai_goi(db, 9999)
