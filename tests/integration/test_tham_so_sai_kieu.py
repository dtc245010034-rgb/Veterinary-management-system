"""Tham số truy vấn rỗng hoặc sai kiểu không được lộ JSON 422 thô (lỗi demo 28/10).

Form HTML gửi `nhan_vien_id=` (rỗng) khi người dùng chọn "Tất cả"/"Chưa chọn"; FastAPI không ép
được chuỗi rỗng thành int nên trả `{"detail":[{"type":"int_parsing",...}]}`. Tiền lệ: `/stats`
nhận ngày dạng str rồi tự đọc.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.customer import Customer
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.security import hash_password
from app.services import scheduling

MAT_KHAU = "matkhau-khach-1"


@pytest.fixture
def the_gioi(client, db, seed_basic, frozen_clock):
    dv = Service(code="TAM", name="Tam va say", duration_min=60, price=Decimal("150000"))
    chu = Owner(full_name="Chu Anh", phone="0911111111")
    db.add_all([dv, chu])
    db.flush()
    pet = Pet(owner_id=chu.id, name="Muc", species="Cho")
    db.add(pet)
    db.add(Customer(email="a@example.com", full_name="Khach A", password_hash=hash_password(MAT_KHAU), owner_id=chu.id))
    db.commit()
    nv1, nv2 = seed_basic["caretaker1"], seed_basic["caretaker2"]
    for nv, gio in ((nv1, 9), (nv2, 14)):
        scheduling.dat_lich(db, thu_cung_id=pet.id, dich_vu_id=dv.id, nhan_vien_id=nv.id, bat_dau=datetime(2026, 3, 12, gio), nguoi_tao_id=seed_basic["receptionist"].id)
    return {"pet": pet, "dv": dv, "nv1": nv1, "nv2": nv2}


def _nhan_vien(client, username="letan"):
    r = client.post("/login", data={"username": username, "password": "matkhau123"})
    assert r.status_code in (200, 303)
    return client


def _khach():
    c = TestClient(app)
    r = c.post("/khach/dang-nhap", data={"email": "a@example.com", "mat_khau": MAT_KHAU}, follow_redirects=False)
    assert r.status_code == 303
    return c


def _la_html_tieng_viet(r):
    assert r.headers["content-type"].startswith("text/html")
    assert '"detail"' not in r.text
    assert "int_parsing" not in r.text


# --- Lỗi 1 ---------------------------------------------------------------------------------

@pytest.mark.parametrize("tai_khoan", ["letan", "quanly"])
def test_loc_lich_nhan_vien_tat_ca_hien_lich_moi_nhan_vien(client, the_gioi, tai_khoan):
    _nhan_vien(client, tai_khoan)

    r = client.get("/appointments", params={"ngay": "2026-03-12", "nhan_vien_id": ""})

    assert r.status_code == 200
    assert "09:00" in r.text and "14:00" in r.text
    assert "Le Van Cham" in r.text and "Pham Thi Soc" in r.text


def test_loc_lich_nhan_vien_khoang_trang_cung_la_tat_ca(client, the_gioi):
    _nhan_vien(client)

    r = client.get("/appointments", params={"ngay": "2026-03-12", "nhan_vien_id": "  "})

    assert r.status_code == 200
    assert "09:00" in r.text and "14:00" in r.text


def test_loc_lich_nhan_vien_cu_the_van_loc_dung(client, the_gioi):
    _nhan_vien(client)

    r = client.get("/appointments", params={"ngay": "2026-03-12", "nhan_vien_id": str(the_gioi["nv1"].id)})

    assert r.status_code == 200
    assert "09:00" in r.text and "14:00" not in r.text


def test_loc_lich_nhan_vien_khong_phai_so_bao_loi_tieng_viet(client, the_gioi):
    _nhan_vien(client)

    r = client.get("/appointments", params={"ngay": "2026-03-12", "nhan_vien_id": "abc"})

    assert r.status_code == 400
    _la_html_tieng_viet(r)
    assert "Nhân viên không hợp lệ" in r.text


# --- Lỗi 2: lưới an toàn RequestValidationError ----------------------------------------------

def test_duong_dan_sai_kieu_ra_404_trang_co_bo_cuc(client, the_gioi):
    _nhan_vien(client)

    r = client.get("/pets/abc")

    assert r.status_code == 404
    _la_html_tieng_viet(r)
    assert "Không tìm thấy" in r.text


def test_query_sai_kieu_ra_400_trang_co_bo_cuc(client, the_gioi):
    _nhan_vien(client)

    r = client.get("/owners", params={"bo_qua_id": "abc"})

    assert r.status_code == 400
    _la_html_tieng_viet(r)
    assert "Dữ liệu gửi lên không hợp lệ." in r.text


def test_form_sai_kieu_ra_400_tieng_viet_khong_lo_ten_truong(client, the_gioi):
    _nhan_vien(client)

    r = client.post("/appointments", data={"thu_cung_id": "abc", "dich_vu_id": "", "nhan_vien_id": ""})

    assert r.status_code == 400
    _la_html_tieng_viet(r)
    assert "Dữ liệu gửi lên không hợp lệ." in r.text
    assert "thu_cung_id" not in r.text


# --- Lỗi 2: hai route khách --------------------------------------------------------------------

def test_khung_trong_tham_so_rong_la_chua_chon(client, the_gioi):
    khach = _khach()

    r = khach.get("/khach/khung-trong", params={"thu_cung_id": "", "dich_vu_id": "", "ngay": ""})

    assert r.status_code == 200
    _la_html_tieng_viet(r)


def test_dat_lich_tham_so_rong_la_chua_chon(client, the_gioi):
    khach = _khach()

    r = khach.get("/khach/dat-lich", params={"thu_cung_id": "", "dich_vu_id": "", "nhan_vien_id": ""})

    assert r.status_code == 200
    _la_html_tieng_viet(r)


def test_khung_trong_tham_so_khong_phai_so_ra_html_khong_phai_422(client, the_gioi):
    khach = _khach()

    r = khach.get("/khach/khung-trong", params={"thu_cung_id": "abc", "dich_vu_id": "", "ngay": "2026-03-13"})

    assert r.status_code != 422
    _la_html_tieng_viet(r)
