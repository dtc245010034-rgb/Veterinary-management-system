"""Test cho app/services/link_requests.py — nối tài khoản khách với hồ sơ chủ nuôi (P9 chặng 4, đợt 4b).

Ba điều cần chứng minh: khách không tự nối được; gửi yêu cầu không lộ số nào là chủ nuôi; duyệt nhầm
thì gỡ được.
"""

import pytest
from sqlalchemy import select

from app.models.customer import Customer
from app.models.link_request import LinkRequest
from app.services import link_requests as lk
from app.services import owners
from app.services.errors import LoiKhongTimThay, LoiNghiepVu


def _khach(db, email="khach@example.com") -> Customer:
    k = Customer(email=email, full_name="Nguyen Khach", password_hash="x")
    db.add(k)
    db.commit()
    return k


def _chu_nuoi(db, ten="Chu Nuoi", sdt="0912345678"):
    return owners.tao_chu_nuoi(db, ho_ten=ten, so_dien_thoai=sdt)


# --- Khách gửi yêu cầu ---------------------------------------------------------------


def test_gui_yeu_cau_tao_yeu_cau_cho_duyet_va_chuan_hoa_so_dien_thoai(db):
    k = _khach(db)

    yc = lk.gui_yeu_cau(db, k, "+84 912 345 678", "  Con chó tên Mực  ")

    assert (yc.status, yc.phone, yc.note) == ("pending", "0912345678", "Con chó tên Mực")
    assert yc.customer_id == k.id


def test_gui_yeu_cau_khong_tu_noi_du_so_khop_voi_mot_chu_nuoi(db):
    _chu_nuoi(db, sdt="0912345678")
    k = _khach(db)

    lk.gui_yeu_cau(db, k, "0912345678")

    db.refresh(k)
    assert k.owner_id is None


def test_gui_yeu_cau_cho_so_la_va_so_cua_chu_nuoi_that_cho_ket_qua_giong_nhau(db):
    """Không tra `owners`: khách không dò được số nào là chủ nuôi của cửa hàng."""
    _chu_nuoi(db, sdt="0912345678")
    a, b = _khach(db, "a@example.com"), _khach(db, "b@example.com")

    co = lk.gui_yeu_cau(db, a, "0912345678")
    khong = lk.gui_yeu_cau(db, b, "0999999999")

    assert (co.status, khong.status) == ("pending", "pending")


def test_gui_yeu_cau_so_dien_thoai_sai_dinh_dang_bi_tu_choi(db):
    k = _khach(db)

    with pytest.raises(LoiNghiepVu, match="Số điện thoại"):
        lk.gui_yeu_cau(db, k, "12345")

    assert db.scalars(select(LinkRequest)).all() == []


def test_gui_yeu_cau_ghi_chu_qua_dai_bi_tu_choi(db):
    k = _khach(db)

    with pytest.raises(LoiNghiepVu, match="Ghi chú"):
        lk.gui_yeu_cau(db, k, "0912345678", "x" * 501)


def test_gui_yeu_cau_lan_hai_khi_con_yeu_cau_cho_bi_tu_choi(db):
    k = _khach(db)
    lk.gui_yeu_cau(db, k, "0912345678")

    with pytest.raises(LoiNghiepVu, match="đang chờ"):
        lk.gui_yeu_cau(db, k, "0987654321")

    assert len(db.scalars(select(LinkRequest)).all()) == 1


def test_gui_yeu_cau_khi_da_noi_bi_tu_choi(db):
    o = _chu_nuoi(db)
    k = _khach(db)
    k.owner_id = o.id
    db.commit()

    with pytest.raises(LoiNghiepVu, match="đã được liên kết"):
        lk.gui_yeu_cau(db, k, "0912345678")


def test_gui_lai_duoc_sau_khi_yeu_cau_truoc_bi_tu_choi(db, seed_basic):
    k = _khach(db)
    cu = lk.gui_yeu_cau(db, k, "0912345678")
    lk.tu_choi(db, cu.id, "Sai số", seed_basic["receptionist"])

    moi = lk.gui_yeu_cau(db, k, "0987654321")

    assert moi.id != cu.id and moi.status == "pending"


def test_yeu_cau_cua_khach_tra_yeu_cau_moi_nhat_hoac_none(db, seed_basic):
    k = _khach(db)
    assert lk.yeu_cau_cua_khach(db, k) is None

    cu = lk.gui_yeu_cau(db, k, "0912345678")
    lk.tu_choi(db, cu.id, "Sai số", seed_basic["receptionist"])
    moi = lk.gui_yeu_cau(db, k, "0987654321")

    assert lk.yeu_cau_cua_khach(db, k).id == moi.id


def test_yeu_cau_cua_khach_khong_tra_yeu_cau_cua_nguoi_khac(db):
    a, b = _khach(db, "a@example.com"), _khach(db, "b@example.com")
    lk.gui_yeu_cau(db, a, "0912345678")

    assert lk.yeu_cau_cua_khach(db, b) is None


# --- Danh sách chờ duyệt -------------------------------------------------------------


def test_danh_sach_cho_duyet_cu_nhat_truoc_kem_ung_vien_cung_so(db):
    trung1 = _chu_nuoi(db, "Gia Dinh A", "0912345678")
    trung2 = _chu_nuoi(db, "Gia Dinh B", "0912345678")
    _chu_nuoi(db, "Nguoi Khac", "0900000000")
    a, b = _khach(db, "a@example.com"), _khach(db, "b@example.com")
    lk.gui_yeu_cau(db, a, "0912345678")
    lk.gui_yeu_cau(db, b, "0777777777")

    ds = lk.danh_sach_cho_duyet(db)

    assert [d.khach.email for d in ds] == ["a@example.com", "b@example.com"]
    assert {o.id for o in ds[0].ung_vien} == {trung1.id, trung2.id}
    assert ds[1].ung_vien == []


def test_danh_sach_cho_duyet_bo_ung_vien_da_thuoc_khach_khac_va_yeu_cau_da_xu_ly(db, seed_basic):
    da_co_chu, con_trong = _chu_nuoi(db, "Da Co Chu", "0912345678"), _chu_nuoi(db, "Con Trong", "0912345678")
    chu_khach = _khach(db, "chu@example.com")
    chu_khach.owner_id = da_co_chu.id
    xong = _khach(db, "xong@example.com")
    cho = _khach(db, "cho@example.com")
    db.commit()
    yc_xong = lk.gui_yeu_cau(db, xong, "0912345678")
    lk.tu_choi(db, yc_xong.id, "Sai", seed_basic["receptionist"])
    lk.gui_yeu_cau(db, cho, "0912345678")

    ds = lk.danh_sach_cho_duyet(db)

    assert [d.khach.email for d in ds] == ["cho@example.com"]
    assert [o.id for o in ds[0].ung_vien] == [con_trong.id]


def test_danh_sach_cho_duyet_rong_khi_khong_co_yeu_cau(db):
    assert lk.danh_sach_cho_duyet(db) == []


# --- Duyệt ---------------------------------------------------------------------------


def test_duyet_noi_khach_voi_ho_so_va_ghi_nguoi_duyet_thoi_diem(db, seed_basic, frozen_clock):
    o = _chu_nuoi(db)
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")

    lk.duyet(db, yc.id, o.id, seed_basic["receptionist"])

    db.refresh(k)
    db.refresh(yc)
    assert k.owner_id == o.id
    assert (yc.status, yc.owner_id, yc.decided_by) == ("approved", o.id, seed_basic["receptionist"].id)
    assert yc.decided_at is not None


def test_duyet_duoc_ho_so_khac_so_khach_nhap_vi_so_chi_la_goi_y(db, seed_basic):
    o = _chu_nuoi(db, sdt="0900000000")
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")

    lk.duyet(db, yc.id, o.id, seed_basic["receptionist"])

    db.refresh(k)
    assert k.owner_id == o.id


def test_duyet_ho_so_da_thuoc_khach_khac_bi_tu_choi_va_khong_doi_gi(db, seed_basic):
    o = _chu_nuoi(db)
    a, b = _khach(db, "a@example.com"), _khach(db, "b@example.com")
    lk.duyet(db, lk.gui_yeu_cau(db, a, "0912345678").id, o.id, seed_basic["receptionist"])
    yc_b = lk.gui_yeu_cau(db, b, "0912345678")

    with pytest.raises(LoiNghiepVu, match="khách khác"):
        lk.duyet(db, yc_b.id, o.id, seed_basic["receptionist"])

    db.refresh(b)
    db.refresh(yc_b)
    assert b.owner_id is None and yc_b.status == "pending"


def test_duyet_hai_lan_bi_tu_choi(db, seed_basic):
    o = _chu_nuoi(db)
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")
    lk.duyet(db, yc.id, o.id, seed_basic["receptionist"])

    with pytest.raises(LoiNghiepVu, match="đã được xử lý"):
        lk.duyet(db, yc.id, o.id, seed_basic["receptionist"])


def test_duyet_yeu_cau_da_bi_tu_choi_bi_chan(db, seed_basic):
    o = _chu_nuoi(db)
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")
    lk.tu_choi(db, yc.id, "Sai", seed_basic["receptionist"])

    with pytest.raises(LoiNghiepVu, match="đã được xử lý"):
        lk.duyet(db, yc.id, o.id, seed_basic["receptionist"])

    db.refresh(k)
    assert k.owner_id is None


def test_duyet_voi_ho_so_khong_ton_tai_hoac_yeu_cau_khong_ton_tai(db, seed_basic):
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")

    with pytest.raises(LoiKhongTimThay):
        lk.duyet(db, yc.id, 99999, seed_basic["receptionist"])
    with pytest.raises(LoiKhongTimThay):
        lk.duyet(db, 99999, 1, seed_basic["receptionist"])

    db.refresh(yc)
    assert yc.status == "pending"


def test_duyet_khi_khach_da_duoc_noi_bang_duong_khac_bi_chan(db, seed_basic):
    o1, o2 = _chu_nuoi(db, "Mot", "0912345678"), _chu_nuoi(db, "Hai", "0987654321")
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")
    k.owner_id = o1.id
    db.commit()

    with pytest.raises(LoiNghiepVu, match="đã được liên kết"):
        lk.duyet(db, yc.id, o2.id, seed_basic["receptionist"])

    db.refresh(k)
    assert k.owner_id == o1.id


# --- Từ chối -------------------------------------------------------------------------


def test_tu_choi_ghi_ly_do_nguoi_xu_ly_va_khong_noi_gi(db, seed_basic, frozen_clock):
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")

    lk.tu_choi(db, yc.id, "  Số không khớp hồ sơ nào  ", seed_basic["receptionist"])

    db.refresh(k)
    db.refresh(yc)
    assert k.owner_id is None
    assert (yc.status, yc.reject_reason, yc.decided_by) == (
        "rejected",
        "Số không khớp hồ sơ nào",
        seed_basic["receptionist"].id,
    )
    assert yc.decided_at is not None


@pytest.mark.parametrize("ly_do", ["", "   ", None])
def test_tu_choi_bat_buoc_co_ly_do_va_yeu_cau_van_dang_cho(db, seed_basic, ly_do):
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")

    with pytest.raises(LoiNghiepVu, match="lý do"):
        lk.tu_choi(db, yc.id, ly_do, seed_basic["receptionist"])

    db.refresh(yc)
    assert yc.status == "pending"


def test_tu_choi_ly_do_qua_dai_va_yeu_cau_da_xu_ly_va_khong_ton_tai(db, seed_basic):
    k = _khach(db)
    yc = lk.gui_yeu_cau(db, k, "0912345678")

    with pytest.raises(LoiNghiepVu, match="dài quá"):
        lk.tu_choi(db, yc.id, "x" * 501, seed_basic["receptionist"])
    lk.tu_choi(db, yc.id, "Sai", seed_basic["receptionist"])
    with pytest.raises(LoiNghiepVu, match="đã được xử lý"):
        lk.tu_choi(db, yc.id, "Sai nữa", seed_basic["receptionist"])
    with pytest.raises(LoiKhongTimThay):
        lk.tu_choi(db, 99999, "Sai", seed_basic["receptionist"])


# --- Gỡ liên kết ---------------------------------------------------------------------


def test_go_lien_ket_dua_khach_ve_chua_noi_va_ho_so_noi_duoc_cho_khach_khac(db, seed_basic):
    o = _chu_nuoi(db)
    a, b = _khach(db, "a@example.com"), _khach(db, "b@example.com")
    lk.duyet(db, lk.gui_yeu_cau(db, a, "0912345678").id, o.id, seed_basic["receptionist"])

    lk.go_lien_ket(db, a.id)
    db.refresh(a)
    assert a.owner_id is None

    lk.duyet(db, lk.gui_yeu_cau(db, b, "0912345678").id, o.id, seed_basic["receptionist"])
    db.refresh(b)
    assert b.owner_id == o.id


def test_go_lien_ket_chua_noi_hoac_khong_ton_tai_bi_tu_choi(db):
    k = _khach(db)

    with pytest.raises(LoiNghiepVu, match="chưa được liên kết"):
        lk.go_lien_ket(db, k.id)
    with pytest.raises(LoiKhongTimThay):
        lk.go_lien_ket(db, 99999)


def test_danh_sach_da_lien_ket_chi_co_khach_da_noi_xep_theo_email(db):
    o1, o2 = _chu_nuoi(db, "Mot", "0912345678"), _chu_nuoi(db, "Hai", "0987654321")
    b, a, _chua_noi = _khach(db, "b@example.com"), _khach(db, "a@example.com"), _khach(db, "c@example.com")
    a.owner_id, b.owner_id = o1.id, o2.id
    db.commit()

    ds = lk.danh_sach_da_lien_ket(db)

    assert [(k.email, o.full_name) for k, o in ds] == [("a@example.com", "Mot"), ("b@example.com", "Hai")]


def test_danh_sach_da_lien_ket_rong_khi_chua_ai_duoc_noi(db):
    _khach(db)
    assert lk.danh_sach_da_lien_ket(db) == []
