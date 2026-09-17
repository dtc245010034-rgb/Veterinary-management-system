"""Test cho app/services/vaccinations.py.

Phục vụ US-17, US-18 — TC-059 → TC-062. Gọi thẳng tầng services, không qua HTTP.

Mọi test dùng fixture `frozen_clock` nên "hôm nay" luôn là 12/03/2026: danh sách đến hạn
phụ thuộc ngày chạy, không cố định thời gian thì test đổi kết quả theo lịch treo tường.
"""

from datetime import date, timedelta

import pytest

from app.models.owner import Owner
from app.models.pet import Pet
from app.services import vaccinations as nv
from app.services.errors import LoiNghiepVu

HOM_NAY = date(2026, 3, 12)  # = MOC_THOI_GIAN trong conftest


@pytest.fixture
def thu_cung(db, frozen_clock):
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p = Pet(owner_id=o.id, name="Mực", species="Chó")
    p2 = Pet(owner_id=o.id, name="Mun", species="Mèo")
    db.add_all([p, p2])
    db.commit()
    return {"muc": p, "mun": p2}


def ghi(db, thu_cung, **ghi_de):
    truong = dict(
        thu_cung_id=thu_cung.id,
        ten_vac_xin="Dại",
        ngay_tiem=HOM_NAY - timedelta(days=30),
        han_nhac=HOM_NAY + timedelta(days=10),
    )
    truong.update(ghi_de)
    return nv.ghi_mui_tiem(db, **truong)


# --- Ghi mũi tiêm — TC-059, TC-060, TC-061 ---------------------------------------


def test_ghi_mui_tiem_hop_le(db, thu_cung):
    v = ghi(db, thu_cung["muc"], so_mui=2, ghi_chu="Tiêm ở phòng khám Thú Y An Khang")

    assert v.id is not None
    assert v.vaccine_name == "Dại"
    assert v.dose_no == 2
    assert v.pet_id == thu_cung["muc"].id


def test_mui_vua_ghi_hien_trong_ho_so_tiem(db, thu_cung):
    """TC-059: ghi xong phải thấy ngay trong hồ sơ tiêm của đúng con vật đó."""
    ghi(db, thu_cung["muc"])

    assert [v.vaccine_name for v in nv.ho_so_tiem(db, thu_cung["muc"].id)] == ["Dại"]
    assert nv.ho_so_tiem(db, thu_cung["mun"].id) == []


def test_thu_cung_khong_ton_tai_thi_bao_loi(db, thu_cung):
    with pytest.raises(LoiNghiepVu, match="thú cưng"):
        nv.ghi_mui_tiem(db, 9999, "Dại", HOM_NAY)


def test_ten_vac_xin_de_trong_thi_bi_tu_choi(db, thu_cung):
    with pytest.raises(LoiNghiepVu, match="Tên vắc-xin"):
        ghi(db, thu_cung["muc"], ten_vac_xin="   ")


def test_thieu_ngay_tiem_thi_bi_tu_choi(db, thu_cung):
    with pytest.raises(LoiNghiepVu, match="Ngày tiêm"):
        ghi(db, thu_cung["muc"], ngay_tiem=None)


def test_ngay_tiem_o_tuong_lai_thi_bi_tu_choi(db, thu_cung):
    """TC-061."""
    with pytest.raises(LoiNghiepVu, match="tương lai"):
        ghi(db, thu_cung["muc"], ngay_tiem=HOM_NAY + timedelta(days=1))


def test_tiem_dung_hom_nay_thi_chap_nhan(db, thu_cung):
    """Ranh giới của TC-061: chặn "sau hôm nay", không chặn "hôm nay"."""
    v = ghi(db, thu_cung["muc"], ngay_tiem=HOM_NAY, han_nhac=None)

    assert v.given_at == HOM_NAY


def test_han_nhac_som_hon_ngay_tiem_thi_bi_tu_choi(db, thu_cung):
    """TC-060."""
    with pytest.raises(LoiNghiepVu, match="hạn nhắc"):
        ghi(db, thu_cung["muc"], ngay_tiem=HOM_NAY, han_nhac=HOM_NAY - timedelta(days=1))


def test_han_nhac_dung_bang_ngay_tiem_thi_chap_nhan(db, thu_cung):
    """Ranh giới của TC-060."""
    v = ghi(db, thu_cung["muc"], ngay_tiem=HOM_NAY, han_nhac=HOM_NAY)

    assert v.next_due_at == HOM_NAY


def test_so_mui_khong_duong_thi_bi_tu_choi(db, thu_cung):
    with pytest.raises(LoiNghiepVu, match="Mũi thứ"):
        ghi(db, thu_cung["muc"], so_mui=0)


def test_ho_so_tiem_moi_nhat_len_dau(db, thu_cung):
    ghi(db, thu_cung["muc"], ten_vac_xin="Mũi cũ", ngay_tiem=HOM_NAY - timedelta(days=365))
    ghi(db, thu_cung["muc"], ten_vac_xin="Mũi mới", ngay_tiem=HOM_NAY)

    assert [v.vaccine_name for v in nv.ho_so_tiem(db, thu_cung["muc"].id)] == [
        "Mũi mới",
        "Mũi cũ",
    ]


# --- Danh sách đến hạn — TC-062 --------------------------------------------------


def test_den_han_lay_dung_khoang_va_sap_theo_han_tang_dan(db, thu_cung):
    """TC-062: từ quá khứ tới hôm nay + 30 ngày, hạn gần lên trước."""
    ghi(db, thu_cung["muc"], ten_vac_xin="Sắp tới", han_nhac=HOM_NAY + timedelta(days=5))
    ghi(db, thu_cung["muc"], ten_vac_xin="Quá hạn", han_nhac=HOM_NAY - timedelta(days=3))
    ghi(db, thu_cung["mun"], ten_vac_xin="Còn xa", han_nhac=HOM_NAY + timedelta(days=60))

    assert [v.vaccine_name for v in nv.den_han(db)] == ["Quá hạn", "Sắp tới"]


def test_han_dung_ngay_thu_30_van_nam_trong_danh_sach(db, thu_cung):
    """Ranh giới trên: ngày thứ 30 còn lấy, ngày thứ 31 thì không."""
    ghi(db, thu_cung["muc"], ten_vac_xin="Vừa đủ 30", han_nhac=HOM_NAY + timedelta(days=30))
    ghi(db, thu_cung["mun"], ten_vac_xin="Quá 1 ngày", han_nhac=HOM_NAY + timedelta(days=31))

    assert [v.vaccine_name for v in nv.den_han(db)] == ["Vừa đủ 30"]


def test_mui_khong_co_han_nhac_thi_khong_vao_danh_sach(db, thu_cung):
    ghi(db, thu_cung["muc"], han_nhac=None)

    assert nv.den_han(db) == []


def test_chi_tinh_mui_moi_nhat_cua_moi_loai_vac_xin(db, thu_cung):
    """TC-062, phần sửa spec lần hai của US-18.

    Mũi 1 có hạn nhắc đã qua, nhưng mũi 2 của **cùng loại vắc-xin** đã tiêm rồi. Lời nhắc
    ấy đã hoàn thành. Tính cả nó thì nó nằm lì trong danh sách quá hạn vĩnh viễn và cả
    màn hình mất tác dụng.
    """
    ghi(
        db, thu_cung["muc"], ten_vac_xin="Dại",
        ngay_tiem=HOM_NAY - timedelta(days=400), han_nhac=HOM_NAY - timedelta(days=35),
    )
    ghi(
        db, thu_cung["muc"], ten_vac_xin="Dại",
        ngay_tiem=HOM_NAY - timedelta(days=35), han_nhac=HOM_NAY + timedelta(days=330),
    )

    assert nv.den_han(db) == []


def test_loai_vac_xin_khac_thi_van_tinh_rieng(db, thu_cung):
    """Ranh giới của luật trên: "mới nhất" tính theo từng loại vắc-xin, không theo thú cưng."""
    ghi(
        db, thu_cung["muc"], ten_vac_xin="Dại",
        ngay_tiem=HOM_NAY - timedelta(days=5), han_nhac=HOM_NAY + timedelta(days=360),
    )
    ghi(
        db, thu_cung["muc"], ten_vac_xin="Cúm",
        ngay_tiem=HOM_NAY - timedelta(days=400), han_nhac=HOM_NAY - timedelta(days=35),
    )

    assert [v.vaccine_name for v in nv.den_han(db)] == ["Cúm"]


def test_ten_vac_xin_go_khac_hoa_thuong_va_dau_van_tinh_la_cung_loai(db, thu_cung):
    """Lỗ hổng S2 (kế hoạch P7 chặng 0).

    Lần đầu ghi "Dại", lần sau lễ tân gõ "dai " không dấu. So tên tuyệt đối thì đó là hai
    loại vắc-xin, và mũi 1 nằm lì trong danh sách quá hạn — đúng lỗi luật "mũi mới nhất"
    sinh ra để chặn. Ghi mũi mới phải dùng lại đúng tên đã có của thú cưng đó.
    """
    ghi(
        db, thu_cung["muc"], ten_vac_xin="Dại",
        ngay_tiem=HOM_NAY - timedelta(days=400), han_nhac=HOM_NAY - timedelta(days=35),
    )
    moi = ghi(
        db, thu_cung["muc"], ten_vac_xin="  dai ",
        ngay_tiem=HOM_NAY - timedelta(days=35), han_nhac=HOM_NAY + timedelta(days=330),
    )

    assert moi.vaccine_name == "Dại"
    assert nv.den_han(db) == []


def test_ten_vac_xin_trung_o_thu_cung_khac_thi_khong_bi_doi(db, thu_cung):
    """Biên của luật trên: chỉ dùng lại tên đã có của CHÍNH thú cưng đó."""
    ghi(db, thu_cung["mun"], ten_vac_xin="Dại")

    assert ghi(db, thu_cung["muc"], ten_vac_xin="dai").vaccine_name == "dai"


def test_khong_ai_den_han_thi_tra_ve_danh_sach_rong(db, thu_cung):
    """TC-064 ở tầng nghiệp vụ."""
    assert nv.den_han(db) == []


def test_qua_han_danh_dau_dung_theo_hom_nay(db, thu_cung):
    """TC-063 ở tầng model: hôm nay chưa phải quá hạn, hôm qua thì phải."""
    hom_nay = ghi(db, thu_cung["muc"], ten_vac_xin="Đúng hôm nay", han_nhac=HOM_NAY)
    hom_qua = ghi(
        db, thu_cung["mun"], ten_vac_xin="Hôm qua", han_nhac=HOM_NAY - timedelta(days=1)
    )

    assert hom_nay.qua_han is False
    assert hom_qua.qua_han is True
