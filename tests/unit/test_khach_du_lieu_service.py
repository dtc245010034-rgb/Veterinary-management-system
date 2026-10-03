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
from app.services.errors import LoiKhongTimThay, LoiNghiepVu


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


# --- Xin đặt lịch (P9 chặng 5) ---------------------------------------------------------


def _xin(db, khach, pet, nv, dv, gio=9):
    return kd.gui_yeu_dat_lich(db, khach, pet.id, dv.id, nv.id, datetime(2026, 3, 13, gio), "ghi chu khach")


def test_lua_chon_dat_lich_chi_gom_thu_cung_cua_khach_va_dem_lich_cho(db, frozen_clock, the_gioi):
    a, b = the_gioi["a"], the_gioi["b"]
    nv = db.query(User).filter_by(username="cs1").one()
    dv = db.query(Service).one()
    _xin(db, a["khach"], a["pet"], nv, dv)

    lc = kd.lua_chon_dat_lich(db, a["khach"])

    assert [p.id for p in lc.thu_cung] == [a["pet"].id]
    assert [d.id for d in lc.dich_vu] == [dv.id]
    assert [n.id for n in lc.nhan_vien] == [nv.id]
    assert lc.so_lich_cho == 1
    assert lc.tran_lich_cho >= 1
    assert b["pet"].id not in [p.id for p in lc.thu_cung]


def test_lua_chon_dat_lich_khach_chua_noi_khong_co_thu_cung_nao(db, the_gioi):
    lc = kd.lua_chon_dat_lich(db, the_gioi["c"])

    assert lc.thu_cung == []
    assert lc.so_lich_cho == 0


def test_gui_yeu_dat_lich_tao_lich_pending_gan_dung_khach(db, frozen_clock, the_gioi):
    a = the_gioi["a"]
    nv = db.query(User).filter_by(username="cs1").one()
    dv = db.query(Service).one()

    lich = _xin(db, a["khach"], a["pet"], nv, dv)

    assert lich.status == "pending"
    assert lich.customer_id == a["khach"].id
    assert lich.pet_id == a["pet"].id
    assert lich.note == "ghi chu khach"


@pytest.mark.parametrize("ai_xin,pet_cua", [("a", "b"), ("c", "a")])
def test_gui_yeu_dat_lich_cho_thu_cung_khong_phai_cua_minh_la_404_nhu_id_khong_co(db, frozen_clock, the_gioi, ai_xin, pet_cua):
    """Khách C chưa nối hồ sơ cũng vào cùng nhánh: không có chủ nuôi nào để so."""
    khach = the_gioi[ai_xin]["khach"] if ai_xin != "c" else the_gioi["c"]
    nv = db.query(User).filter_by(username="cs1").one()
    dv = db.query(Service).one()

    with pytest.raises(LoiKhongTimThay) as that:
        kd.gui_yeu_dat_lich(db, khach, the_gioi[pet_cua]["pet"].id, dv.id, nv.id, datetime(2026, 3, 13, 9))
    with pytest.raises(LoiKhongTimThay) as khong_co:
        kd.gui_yeu_dat_lich(db, khach, 99999, dv.id, nv.id, datetime(2026, 3, 13, 9))

    assert str(that.value) == str(khong_co.value)
    assert db.query(Appointment).filter(Appointment.status == "pending").count() == 0


# --- Khung giờ trống theo nhân viên (P9 chặng 6) ---------------------------------------
# frozen_clock = 2026-03-12 08:00. Fixture: cs1 và cả hai thú cưng cùng có lịch 09:00–10:00 ngày 12/03.

NGAY_XEM = date(2026, 3, 12)


def _them_nhan_vien(db, username, ten, role="caretaker", dang_hoat_dong=True):
    nv = User(username=username, password_hash="b", full_name=ten, role=role, is_active=dang_hoat_dong)
    db.add(nv)
    db.commit()
    return nv


def _gio_cua(nhom, nhan_vien_id):
    return next(g.gio for g in nhom if g.nhan_vien.id == nhan_vien_id)


def test_khung_trong_nhom_theo_nhan_vien_va_tinh_theo_ca_nhan_vien_lan_thu_cung(db, frozen_clock, the_gioi):
    a = the_gioi["a"]
    cs1 = db.query(User).filter_by(username="cs1").one()
    cs2 = _them_nhan_vien(db, "cs2", "Pham Thi Soc")
    dv = db.query(Service).one()

    nhom = kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, dv.id, NGAY_XEM)

    assert [g.nhan_vien.id for g in nhom] == [cs1.id, cs2.id]
    gio_cs1, gio_cs2 = _gio_cua(nhom, cs1.id), _gio_cua(nhom, cs2.id)
    # cs1 bận 09:00–10:00: mọi khung chạm vào đó đều mất
    assert datetime(2026, 3, 12, 8) in gio_cs1 and datetime(2026, 3, 12, 10) in gio_cs1
    assert not {datetime(2026, 3, 12, 8, 30), datetime(2026, 3, 12, 9), datetime(2026, 3, 12, 9, 30)} & set(gio_cs1)
    # cs2 rảnh cả ngày, nhưng thú cưng của khách đang có lịch 09:00–10:00 với cs1 nên cũng không thể ở hai nơi
    assert datetime(2026, 3, 12, 9) not in gio_cs2 and datetime(2026, 3, 12, 8, 30) not in gio_cs2
    assert datetime(2026, 3, 12, 10) in gio_cs2
    assert len(gio_cs2) > 5


def test_khung_trong_chi_co_nhan_vien_cham_soc_dang_hoat_dong(db, frozen_clock, the_gioi):
    a = the_gioi["a"]
    _them_nhan_vien(db, "cs_khoa", "Bi Khoa", dang_hoat_dong=False)
    _them_nhan_vien(db, "lt", "Le Tan", role="receptionist")
    dv = db.query(Service).one()

    nhom = kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, dv.id, NGAY_XEM)

    assert [g.nhan_vien.username for g in nhom] == ["cs1"]


def test_khung_trong_ngay_da_qua_van_liet_ke_nhan_vien_voi_danh_sach_rong(db, frozen_clock, the_gioi):
    a = the_gioi["a"]
    dv = db.query(Service).one()

    nhom = kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, dv.id, date(2026, 3, 11))

    assert len(nhom) == 1 and nhom[0].gio == []


def test_khung_trong_lich_pending_cua_khach_khac_dang_giu_cho(db, frozen_clock, the_gioi):
    a, b = the_gioi["a"], the_gioi["b"]
    cs1 = db.query(User).filter_by(username="cs1").one()
    dv = db.query(Service).one()
    kd.gui_yeu_dat_lich(db, b["khach"], b["pet"].id, dv.id, cs1.id, datetime(2026, 3, 12, 11))

    gio = _gio_cua(kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, dv.id, NGAY_XEM), cs1.id)

    assert not {datetime(2026, 3, 12, 10, 30), datetime(2026, 3, 12, 11), datetime(2026, 3, 12, 11, 30)} & set(gio)
    assert datetime(2026, 3, 12, 10) in gio and datetime(2026, 3, 12, 12) in gio


def test_khung_trong_ket_qua_chi_gom_nhan_vien_va_gio_khong_dau_vet_cua_khach_khac(db, frozen_clock, the_gioi):
    a = the_gioi["a"]
    dv = db.query(Service).one()

    nhom = kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, dv.id, NGAY_XEM)

    assert set(vars(nhom[0])) == {"nhan_vien", "gio"}


def test_khung_trong_thu_cung_cua_nguoi_khac_va_id_khong_co_cung_mot_404(db, frozen_clock, the_gioi):
    a, b, c = the_gioi["a"], the_gioi["b"], the_gioi["c"]
    dv = db.query(Service).one()

    with pytest.raises(LoiKhongTimThay) as cua_nguoi_khac:
        kd.khung_trong_cua_khach(db, a["khach"], b["pet"].id, dv.id, NGAY_XEM)
    with pytest.raises(LoiKhongTimThay) as khong_co:
        kd.khung_trong_cua_khach(db, a["khach"], 99999, dv.id, NGAY_XEM)
    with pytest.raises(LoiKhongTimThay) as chua_noi:
        kd.khung_trong_cua_khach(db, c, a["pet"].id, dv.id, NGAY_XEM)

    assert str(cua_nguoi_khac.value) == str(khong_co.value) == str(chua_noi.value)


def test_khung_trong_dich_vu_khong_co_la_404_va_dich_vu_ngung_ban_bi_chan(db, frozen_clock, the_gioi):
    a = the_gioi["a"]
    dv = db.query(Service).one()

    with pytest.raises(LoiKhongTimThay):
        kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, 99999, NGAY_XEM)

    dv.is_active = False
    db.commit()
    with pytest.raises(LoiNghiepVu, match="ngưng bán"):
        kd.khung_trong_cua_khach(db, a["khach"], a["pet"].id, dv.id, NGAY_XEM)
