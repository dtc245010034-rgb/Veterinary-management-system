"""Khách xin lịch, lễ tân duyệt/từ chối qua HTTP (P9 chặng 5).

Ba bên cùng lúc nên mỗi bên một `TestClient` riêng (khách = cookie `csv`, nhân viên = cookie nhân viên), chung một CSDL
qua override `get_db` của fixture `client`. Đồng hồ đóng băng ở 2026-03-12 08:00.

Điều cần chứng minh:
- Luồng chính: khách xin → lịch hiện "Chờ duyệt" cho cả hai bên → lễ tân duyệt → thành lịch đã đặt.
- Từ chối: bắt buộc lý do, khách đọc được lý do, khung giờ được trả lại.
- Biên quyền: thú cưng của người khác và id không tồn tại cho CÙNG một phản hồi 404; khách chưa nối hồ sơ không xin
  được; nhân viên chăm sóc và khách không vào được màn duyệt.
- Không rò rỉ: lý do hủy NỘI BỘ của lịch do nhân viên đặt không hiện cho khách.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.security import hash_password
from app.services import scheduling
from app.services.errors import LoiNghiepVu

MAT_KHAU = "matkhau-khach-1"
NGAY = "2026-03-13"
KHONG_CO = 99999


@pytest.fixture
def the_gioi(client, db, seed_basic, frozen_clock):
    dv = Service(code="TAM", name="Tam va say", duration_min=60, price=Decimal("150000"))
    chu_a = Owner(full_name="Chu Anh", phone="0911111111")
    chu_b = Owner(full_name="Chu Binh", phone="0922222222")
    db.add_all([dv, chu_a, chu_b])
    db.flush()
    pet_a = Pet(owner_id=chu_a.id, name="Muc", species="Cho")
    pet_b = Pet(owner_id=chu_b.id, name="Lu", species="Cho")
    db.add_all([pet_a, pet_b])
    db.flush()
    db.add_all([
        Customer(email="a@example.com", full_name="Khach A", password_hash=hash_password(MAT_KHAU), owner_id=chu_a.id),
        Customer(email="c@example.com", full_name="Khach C", password_hash=hash_password(MAT_KHAU)),
    ])
    db.commit()
    return {"dv": dv, "pet_a": pet_a, "pet_b": pet_b, "nv": seed_basic["caretaker1"], "seed": seed_basic}


def _khach(email):
    c = TestClient(app)
    r = c.post("/khach/dang-nhap", data={"email": email, "mat_khau": MAT_KHAU}, follow_redirects=False)
    assert r.status_code == 303
    return c


def _nhan_vien(seed, username):
    c = TestClient(app)
    r = c.post("/login", data={"username": username, "password": seed["mat_khau"]}, follow_redirects=False)
    assert r.status_code == 303
    return c


@pytest.fixture
def khach_a(the_gioi):
    return _khach("a@example.com")


@pytest.fixture
def khach_c(the_gioi):
    return _khach("c@example.com")


@pytest.fixture
def le_tan(the_gioi):
    return _nhan_vien(the_gioi["seed"], "letan")


def _form(the_gioi, pet="pet_a", gio="09:00", ngay=NGAY, ghi_chu=""):
    return {
        "thu_cung_id": the_gioi[pet].id,
        "dich_vu_id": the_gioi["dv"].id,
        "nhan_vien_id": the_gioi["nv"].id,
        "ngay": ngay,
        "gio": gio,
        "ghi_chu": ghi_chu,
    }


def _xin(khach, the_gioi, **kw):
    return khach.post("/khach/dat-lich", data=_form(the_gioi, **kw), follow_redirects=False)


def _lich(db):
    db.expire_all()
    return db.query(Appointment).order_by(Appointment.id).all()


# --- Luồng chính -----------------------------------------------------------------------


def test_luong_khach_xin_le_tan_duyet_thanh_lich_da_dat(db, khach_a, le_tan, the_gioi):
    form = khach_a.get("/khach/dat-lich")
    assert form.status_code == 200
    assert "Muc" in form.text and "Tam va say" in form.text

    r = _xin(khach_a, the_gioi, ghi_chu="Ve sinh tai")
    assert r.status_code == 303 and r.headers["location"] == "/khach/lich-hen"
    assert "Chờ duyệt" in khach_a.get("/khach/lich-hen").text

    man = le_tan.get("/lich-cho-duyet")
    assert man.status_code == 200
    assert "Muc" in man.text and "Chu Anh" in man.text and "Ve sinh tai" in man.text
    lich_id = _lich(db)[0].id

    r = le_tan.post(f"/lich-cho-duyet/{lich_id}/duyet", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/lich-cho-duyet"
    assert "Không có yêu cầu nào đang chờ" in le_tan.get("/lich-cho-duyet").text
    assert "Đã đặt" in khach_a.get("/khach/lich-hen").text
    assert _lich(db)[0].status == "booked"

    luoi = le_tan.get(f"/appointments?ngay={NGAY}")
    assert "Muc" in luoi.text and "Đã đặt" in luoi.text


def test_le_tan_tu_choi_khach_doc_duoc_ly_do_va_khung_gio_duoc_tra_lai(db, khach_a, le_tan, the_gioi):
    _xin(khach_a, the_gioi)
    lich_id = _lich(db)[0].id
    # khung giờ đang bị giữ
    with pytest.raises(LoiNghiepVu):
        scheduling.dat_lich(
            db, the_gioi["pet_b"].id, the_gioi["dv"].id, the_gioi["nv"].id, datetime(2026, 3, 13, 9),
            the_gioi["seed"]["receptionist"].id,
        )

    r = le_tan.post(f"/lich-cho-duyet/{lich_id}/tu-choi", data={"ly_do": "Hom do tiem nghi"}, follow_redirects=False)

    assert r.status_code == 303
    trang = khach_a.get("/khach/lich-hen").text
    assert "Đã hủy" in trang and "Hom do tiem nghi" in trang
    scheduling.dat_lich(
        db, the_gioi["pet_b"].id, the_gioi["dv"].id, the_gioi["nv"].id, datetime(2026, 3, 13, 9),
        the_gioi["seed"]["receptionist"].id,
    )


def test_tu_choi_thieu_ly_do_bi_chan_va_lich_van_cho(db, khach_a, le_tan, the_gioi):
    _xin(khach_a, the_gioi)
    lich_id = _lich(db)[0].id

    r = le_tan.post(f"/lich-cho-duyet/{lich_id}/tu-choi", data={"ly_do": "   "})

    assert r.status_code == 400 and "lý do" in r.text
    assert _lich(db)[0].status == "pending"


def test_duyet_lich_da_het_han_bao_loi_khong_500(db, khach_a, le_tan, the_gioi):
    _xin(khach_a, the_gioi)
    lich_id = _lich(db)[0].id
    from app.services import clock

    with clock.freeze(datetime(2026, 3, 14, 12, 0)):
        r = le_tan.post(f"/lich-cho-duyet/{lich_id}/duyet")

    assert r.status_code == 400 and "không còn chờ duyệt" in r.text
    assert _lich(db)[0].status == "cancelled"


def test_duyet_lich_khong_ton_tai_la_404(le_tan):
    assert le_tan.post(f"/lich-cho-duyet/{KHONG_CO}/duyet").status_code == 404
    assert le_tan.post(f"/lich-cho-duyet/{KHONG_CO}/tu-choi", data={"ly_do": "x"}).status_code == 404


# --- Biên quyền -----------------------------------------------------------------------


def test_thu_cung_cua_nguoi_khac_va_id_khong_ton_tai_cho_cung_mot_404(db, khach_a, the_gioi):
    cua_nguoi_khac = _xin(khach_a, the_gioi, pet="pet_b")
    ma_khong_co = khach_a.post("/khach/dat-lich", data={**_form(the_gioi), "thu_cung_id": KHONG_CO})

    assert cua_nguoi_khac.status_code == 404
    assert ma_khong_co.status_code == 404
    assert cua_nguoi_khac.text == ma_khong_co.text
    assert _lich(db) == []


def test_khach_chua_noi_ho_so_khong_xin_duoc(db, khach_c, the_gioi):
    form = khach_c.get("/khach/dat-lich")
    assert form.status_code == 200 and "chưa được liên kết" in form.text

    assert _xin(khach_c, the_gioi).status_code == 404
    assert _lich(db) == []


def test_chua_dang_nhap_khach_bi_day_ve_dang_nhap():
    c = TestClient(app)
    for r in (c.get("/khach/dat-lich", follow_redirects=False), c.post("/khach/dat-lich", data={}, follow_redirects=False)):
        assert r.status_code == 303 and r.headers["location"] == "/khach/dang-nhap"


def test_man_duyet_chi_cho_quan_ly_va_le_tan(the_gioi, khach_a):
    cs = _nhan_vien(the_gioi["seed"], "chamsoc1")
    assert cs.get("/lich-cho-duyet").status_code == 403
    assert cs.post("/lich-cho-duyet/1/duyet").status_code == 403
    assert _nhan_vien(the_gioi["seed"], "quanly").get("/lich-cho-duyet").status_code == 200

    r = khach_a.get("/lich-cho-duyet", follow_redirects=False)  # cookie khách không phải cookie nhân viên
    assert r.status_code == 303 and r.headers["location"] == "/login"


# --- Quy tắc nghiệp vụ qua HTTP -----------------------------------------------------------


def test_khach_xin_qua_tran_bi_chan_voi_thong_bao_tieng_viet(db, khach_a, the_gioi):
    for gio in ("08:00", "10:00", "12:00"):
        assert _xin(khach_a, the_gioi, gio=gio).status_code == 303

    r = _xin(khach_a, the_gioi, gio="14:00")

    assert r.status_code == 400 and "tối đa" in r.text
    assert len(_lich(db)) == 3


def test_khach_xin_trung_gio_lich_da_dat_bi_chan(db, khach_a, the_gioi):
    scheduling.dat_lich(
        db, the_gioi["pet_b"].id, the_gioi["dv"].id, the_gioi["nv"].id, datetime(2026, 3, 13, 9),
        the_gioi["seed"]["receptionist"].id,
    )

    r = _xin(khach_a, the_gioi, gio="09:30")

    assert r.status_code == 400
    assert len(_lich(db)) == 1


def test_ngay_gio_sai_dinh_dang_bao_loi_va_giu_lai_cac_o_da_nhap(khach_a, the_gioi):
    r = _xin(khach_a, the_gioi, ngay="khong-phai-ngay", ghi_chu="Giu lai ghi chu")

    assert r.status_code == 400
    assert "không đúng định dạng" in r.text
    assert "Giu lai ghi chu" in r.text


def test_ly_do_huy_noi_bo_cua_lich_nhan_vien_dat_khong_hien_cho_khach(db, khach_a, the_gioi):
    lich = scheduling.dat_lich(
        db, the_gioi["pet_a"].id, the_gioi["dv"].id, the_gioi["nv"].id, datetime(2026, 3, 13, 9),
        the_gioi["seed"]["receptionist"].id,
    )
    scheduling.huy_lich(db, lich.id, "BIMAT-ly-do-noi-bo")

    trang = khach_a.get("/khach/lich-hen")

    assert "Đã hủy" in trang.text
    assert "BIMAT-ly-do-noi-bo" not in trang.text


def test_luoi_lich_cua_le_tan_hien_lich_cho_voi_nhan_va_lien_ket_duyet(le_tan, khach_a, the_gioi):
    _xin(khach_a, the_gioi)

    luoi = le_tan.get(f"/appointments?ngay={NGAY}")

    assert "nhan-pending" in luoi.text and "Chờ duyệt" in luoi.text
    assert 'href="/lich-cho-duyet"' in luoi.text
    assert "/hoa-don" not in luoi.text.split("Chờ duyệt", 1)[1].split("</tr>", 1)[0]  # không có nút lập hóa đơn
