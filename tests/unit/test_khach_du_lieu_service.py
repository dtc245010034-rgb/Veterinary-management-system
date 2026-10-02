"""Test cho app/services/khach_du_lieu.py — dữ liệu khách được xem (P9 chặng 4, đợt 4c).

Ba người trong mọi ca: khách A nối chủ nuôi A, khách B nối chủ nuôi B, khách C chưa nối. Điều phải đúng:
mỗi khách chỉ thấy của mình, id của người khác và id không tồn tại cho cùng một kết quả, khách chưa nối
không thấy gì.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.models.appointment import Appointment
from app.models.care_record import CareRecord
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.models.vaccination import Vaccination
from app.services import khach_du_lieu as kd
from app.services.errors import LoiKhongTimThay


@pytest.fixture
def the_gioi(db):
    nv = User(username="cs1", password_hash="b", full_name="Le Van Cham", role="caretaker")
    dv = Service(code="TAM", name="Tam va say", duration_min=60, price=Decimal("150000"))
    db.add_all([nv, dv])
    db.flush()

    def dung(ten_chu, sdt, ten_pet, email):
        chu = Owner(full_name=ten_chu, phone=sdt)
        db.add(chu)
        db.flush()
        pet = Pet(owner_id=chu.id, name=ten_pet, species="Cho")
        db.add(pet)
        db.flush()
        lich = Appointment(
            pet_id=pet.id, service_id=dv.id, staff_id=nv.id, created_by=nv.id,
            start_at=datetime(2026, 3, 12, 9), end_at=datetime(2026, 3, 12, 10),
        )
        tiem = Vaccination(pet_id=pet.id, vaccine_name="Dai", given_at=date(2026, 1, 5))
        hd = Invoice(owner_id=chu.id, total_amount=Decimal("150000"))
        khach = Customer(email=email, full_name="Khach " + ten_chu, password_hash="x", owner_id=chu.id)
        db.add_all([lich, tiem, hd, khach])
        db.flush()
        ho_so = CareRecord(
            appointment_id=lich.id, pet_id=pet.id, staff_id=nv.id,
            performed_at=lich.start_at, condition_note="ghi chu noi bo",
        )
        db.add(ho_so)
        db.flush()
        return {"chu": chu, "pet": pet, "lich": lich, "tiem": tiem, "hd": hd, "khach": khach, "ho_so": ho_so}

    a = dung("Chu A", "0911111111", "Muc", "a@example.com")
    b = dung("Chu B", "0922222222", "Lu", "b@example.com")
    c = Customer(email="c@example.com", full_name="Khach C", password_hash="x")
    db.add(c)
    db.commit()
    return {"a": a, "b": b, "c": c}


# --- yeu_cau_so_huu, ma_chu_nuoi -------------------------------------------------------


def test_ma_chu_nuoi_la_ho_so_da_noi_hoac_none_khi_chua_noi(the_gioi):
    assert kd.ma_chu_nuoi(the_gioi["a"]["khach"]) == the_gioi["a"]["chu"].id
    assert kd.ma_chu_nuoi(the_gioi["c"]) is None


LOAI_BAN_GHI = ["pet", "hd", "lich", "tiem", "ho_so"]


@pytest.mark.parametrize("loai", LOAI_BAN_GHI)
def test_yeu_cau_so_huu_cho_qua_ban_ghi_cua_chinh_chu(the_gioi, loai):
    kd.yeu_cau_so_huu(the_gioi["a"]["khach"], the_gioi["a"][loai])


@pytest.mark.parametrize("loai", LOAI_BAN_GHI)
def test_yeu_cau_so_huu_chan_ban_ghi_cua_chu_khac(the_gioi, loai):
    with pytest.raises(LoiKhongTimThay):
        kd.yeu_cau_so_huu(the_gioi["a"]["khach"], the_gioi["b"][loai])


@pytest.mark.parametrize("loai", LOAI_BAN_GHI)
def test_yeu_cau_so_huu_chan_moi_ban_ghi_khi_khach_chua_noi(the_gioi, loai):
    with pytest.raises(LoiKhongTimThay):
        kd.yeu_cau_so_huu(the_gioi["c"], the_gioi["a"][loai])


def test_thong_diep_chan_khong_nhac_den_chu_so_huu_that(the_gioi):
    with pytest.raises(LoiKhongTimThay) as loi:
        kd.yeu_cau_so_huu(the_gioi["a"]["khach"], the_gioi["b"]["pet"])

    assert str(loi.value) == kd.LOI_KHONG_THAY


# --- Danh sách ---------------------------------------------------------------------------


def test_danh_sach_thu_cung_chi_co_thu_cung_cua_minh(db, the_gioi):
    ds = kd.danh_sach_thu_cung(db, the_gioi["a"]["khach"])

    assert [p.id for p in ds] == [the_gioi["a"]["pet"].id]


def test_danh_sach_cua_khach_chua_noi_rong_o_ca_ba_loai(db, the_gioi):
    c = the_gioi["c"]

    assert kd.danh_sach_thu_cung(db, c) == []
    assert kd.danh_sach_lich_hen(db, c) == []
    assert kd.danh_sach_hoa_don(db, c) == []


def test_danh_sach_lich_hen_chi_co_lich_cua_thu_cung_minh_moi_nhat_truoc(db, the_gioi):
    a = the_gioi["a"]
    cu_hon = Appointment(
        pet_id=a["pet"].id, service_id=a["lich"].service_id, staff_id=a["lich"].staff_id, created_by=a["lich"].staff_id,
        start_at=datetime(2026, 2, 1, 9), end_at=datetime(2026, 2, 1, 10),
    )
    db.add(cu_hon)
    db.commit()

    ds = kd.danh_sach_lich_hen(db, a["khach"])

    assert [x.id for x in ds] == [a["lich"].id, cu_hon.id]
    assert the_gioi["b"]["lich"].id not in [x.id for x in ds]


def test_danh_sach_hoa_don_chi_co_hoa_don_cua_minh(db, the_gioi):
    ds = kd.danh_sach_hoa_don(db, the_gioi["b"]["khach"])

    assert [h.id for h in ds] == [the_gioi["b"]["hd"].id]


def test_danh_sach_van_dung_sau_khi_go_lien_ket(db, the_gioi):
    khach = the_gioi["a"]["khach"]
    khach.owner_id = None
    db.commit()

    assert kd.danh_sach_thu_cung(db, khach) == []
    assert kd.danh_sach_hoa_don(db, khach) == []


# --- Chi tiết theo id ----------------------------------------------------------------------


def test_chi_tiet_thu_cung_cua_minh_kem_lich_su_tiem_moi_nhat_truoc(db, the_gioi):
    a = the_gioi["a"]
    moi = Vaccination(pet_id=a["pet"].id, vaccine_name="Dai", given_at=date(2026, 2, 5))
    db.add(moi)
    db.commit()

    ct = kd.chi_tiet_thu_cung(db, a["khach"], a["pet"].id)

    assert ct.thu_cung.id == a["pet"].id
    assert [t.id for t in ct.tiem_phong] == [moi.id, a["tiem"].id]


def test_chi_tiet_thu_cung_cua_nguoi_khac_va_id_khong_ton_tai_cung_mot_ket_qua(db, the_gioi):
    khach = the_gioi["a"]["khach"]

    with pytest.raises(LoiKhongTimThay) as cua_nguoi_khac:
        kd.chi_tiet_thu_cung(db, khach, the_gioi["b"]["pet"].id)
    with pytest.raises(LoiKhongTimThay) as khong_ton_tai:
        kd.chi_tiet_thu_cung(db, khach, 99999)

    assert str(cua_nguoi_khac.value) == str(khong_ton_tai.value)


def test_chi_tiet_thu_cung_khach_chua_noi_bi_chan_du_id_dung(db, the_gioi):
    with pytest.raises(LoiKhongTimThay):
        kd.chi_tiet_thu_cung(db, the_gioi["c"], the_gioi["a"]["pet"].id)


def test_chi_tiet_hoa_don_cua_minh(db, the_gioi):
    a = the_gioi["a"]

    assert kd.chi_tiet_hoa_don(db, a["khach"], a["hd"].id).id == a["hd"].id


def test_chi_tiet_hoa_don_cua_nguoi_khac_va_id_khong_ton_tai_cung_mot_ket_qua(db, the_gioi):
    khach = the_gioi["a"]["khach"]

    with pytest.raises(LoiKhongTimThay) as cua_nguoi_khac:
        kd.chi_tiet_hoa_don(db, khach, the_gioi["b"]["hd"].id)
    with pytest.raises(LoiKhongTimThay) as khong_ton_tai:
        kd.chi_tiet_hoa_don(db, khach, 99999)

    assert str(cua_nguoi_khac.value) == str(khong_ton_tai.value)


def test_chi_tiet_hoa_don_khach_chua_noi_bi_chan(db, the_gioi):
    with pytest.raises(LoiKhongTimThay):
        kd.chi_tiet_hoa_don(db, the_gioi["c"], the_gioi["a"]["hd"].id)
