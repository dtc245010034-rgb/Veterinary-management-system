"""Cổng khách xem dữ liệu của chính mình qua HTTP, và không xem được của ai khác (P9 chặng 4, đợt 4c).

Ba khách: A và B đã nối hồ sơ chủ nuôi khác nhau, C chưa nối. Mỗi chủ nuôi có thú cưng, mũi tiêm, lịch hẹn,
hồ sơ chăm sóc, hóa đơn; các trường nội bộ (ghi chú, lý do hủy, tên nhân viên, hồ sơ chăm sóc) mang chuỗi
"BIMAT-..." để kiểm chúng không bao giờ lọt ra trang khách.

Quét IDOR theo kiểu `test_khong_tim_thay.py`: id của người khác và id không tồn tại phải cho **cùng một**
phản hồi 404, chứ không phải 403 (403 xác nhận cho kẻ dò rằng id đó có thật) và càng không phải 200 hay 500.
"""

import re
from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.appointment import Appointment
from app.models.care_record import CareRecord
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.owner import Owner
from app.models.payment import Payment
from app.models.pet import Pet
from app.models.service import Service
from app.models.vaccination import Vaccination
from app.security import hash_password

MAT_KHAU = "matkhau-khach-1"
KHONG_CO = 99999
BI_MAT = "BIMAT"


def _dung_chu(db, nv, dv, ten, sdt, ten_pet, email):
    chu = Owner(full_name=ten, phone=sdt, address=f"{BI_MAT}-dia-chi-{ten_pet}")
    db.add(chu)
    db.flush()
    pet = Pet(owner_id=chu.id, name=ten_pet, species="Cho", breed="Poodle", note=f"{BI_MAT}-ghi-chu-pet-{ten_pet}")
    db.add(pet)
    db.flush()
    lich = Appointment(
        pet_id=pet.id, service_id=dv.id, staff_id=nv.id, created_by=nv.id,
        start_at=datetime(2026, 3, 12, 9), end_at=datetime(2026, 3, 12, 10),
        note=f"{BI_MAT}-ghi-chu-lich-{ten_pet}", cancel_reason=f"{BI_MAT}-ly-do-huy-{ten_pet}",
    )
    tiem = Vaccination(
        pet_id=pet.id, vaccine_name=f"Dai-{ten_pet}", given_at=date(2026, 1, 5), note=f"{BI_MAT}-ghi-chu-tiem-{ten_pet}"
    )
    hd = Invoice(owner_id=chu.id, total_amount=Decimal("150000"), note=f"{BI_MAT}-ghi-chu-hd-{ten_pet}")
    hd.dong.append(InvoiceItem(description=f"Tam va say {ten_pet}", qty=1, unit_price=Decimal("150000"), amount=Decimal("150000")))
    hd.thanh_toan.append(Payment(amount=Decimal("50000")))
    khach = Customer(email=email, full_name=f"Khach {ten}", password_hash=hash_password(MAT_KHAU), owner_id=chu.id)
    db.add_all([lich, tiem, hd, khach])
    db.flush()
    db.add(CareRecord(
        appointment_id=lich.id, pet_id=pet.id, staff_id=nv.id, performed_at=lich.start_at,
        condition_note=f"{BI_MAT}-hoso-{ten_pet}",
    ))
    db.flush()
    return {"chu": chu, "pet": pet, "lich": lich, "tiem": tiem, "hd": hd, "email": email}


@pytest.fixture
def the_gioi(client, db, seed_basic):
    nv = seed_basic["caretaker1"]
    dv = Service(code="TAM", name="Tam va say", duration_min=60, price=Decimal("150000"))
    db.add(dv)
    db.flush()
    a = _dung_chu(db, nv, dv, "Chu Anh", "0911111111", "Muc", "a@example.com")
    b = _dung_chu(db, nv, dv, "Chu Binh", "0922222222", "Lu", "b@example.com")
    db.add(Customer(email="c@example.com", full_name="Khach C", password_hash=hash_password(MAT_KHAU)))
    db.commit()
    return {"a": a, "b": b}


def _dang_nhap(email):
    c = TestClient(app)
    r = c.post("/khach/dang-nhap", data={"email": email, "mat_khau": MAT_KHAU}, follow_redirects=False)
    assert r.status_code == 303
    return c


@pytest.fixture
def khach_a(the_gioi):
    return _dang_nhap("a@example.com")


@pytest.fixture
def khach_c(the_gioi):
    return _dang_nhap("c@example.com")


TRANG_DANH_SACH = ["/khach/thu-cung", "/khach/lich-hen", "/khach/hoa-don"]


# --- Khách thấy đúng dữ liệu của mình ----------------------------------------------------


def test_khach_thay_thu_cung_lich_hen_hoa_don_cua_minh_va_khong_thay_cua_nguoi_khac(khach_a, the_gioi):
    thu_cung = khach_a.get("/khach/thu-cung")
    lich = khach_a.get("/khach/lich-hen")
    hoa_don = khach_a.get("/khach/hoa-don")

    assert (thu_cung.status_code, lich.status_code, hoa_don.status_code) == (200, 200, 200)
    assert "Muc" in thu_cung.text and "Lu" not in re.findall(r">([^<]+)<", thu_cung.text)
    assert "Muc" in lich.text and "12/03/2026 09:00" in lich.text
    assert "Lu" not in re.findall(r">([^<]+)<", lich.text)
    assert f"#{the_gioi['a']['hd'].id}" in hoa_don.text
    assert f"/khach/hoa-don/{the_gioi['b']['hd'].id}\"" not in hoa_don.text
    assert f"/khach/thu-cung/{the_gioi['b']['pet'].id}\"" not in thu_cung.text


def test_chi_tiet_thu_cung_va_hoa_don_cua_minh_hien_du_truong_can_xem(khach_a, the_gioi):
    pet = khach_a.get(f"/khach/thu-cung/{the_gioi['a']['pet'].id}")
    hd = khach_a.get(f"/khach/hoa-don/{the_gioi['a']['hd'].id}")

    assert pet.status_code == 200 and "Dai-Muc" in pet.text and "05/01/2026" in pet.text
    assert hd.status_code == 200 and "Tam va say Muc" in hd.text
    assert "150.000đ" in hd.text and "50.000đ" in hd.text and "100.000đ" in hd.text  # tổng, đã trả, còn nợ


def test_khong_trang_nao_lo_truong_noi_bo_hay_thong_tin_chu_khac(khach_a, the_gioi):
    """Ghi chú, lý do hủy, hồ sơ chăm sóc, tên nhân viên, địa chỉ: không có đường nào ra trang khách."""
    a, b = the_gioi["a"], the_gioi["b"]
    duong_dan = TRANG_DANH_SACH + [
        "/khach",
        f"/khach/thu-cung/{a['pet'].id}",
        f"/khach/hoa-don/{a['hd'].id}",
    ]

    for url in duong_dan:
        r = khach_a.get(url)
        assert r.status_code == 200, url
        assert BI_MAT not in r.text, f"{url} lộ trường nội bộ"
        assert "Le Van Cham" not in r.text, f"{url} lộ tên nhân viên"
        assert "Chu Binh" not in r.text and "0922222222" not in r.text and b["email"] not in r.text, url


def test_thanh_dieu_huong_khach_da_noi_co_link_du_lieu_chua_noi_chi_co_link_lien_ket(khach_a, khach_c):
    da_noi = khach_a.get("/khach").text
    chua_noi = khach_c.get("/khach").text

    for link in ("/khach/thu-cung", "/khach/lich-hen", "/khach/hoa-don"):
        assert f'href="{link}"' in da_noi
        assert f'href="{link}"' not in chua_noi
    assert 'href="/khach/lien-ket"' in chua_noi


# --- Khách chưa nối ------------------------------------------------------------------------


@pytest.mark.parametrize("url", TRANG_DANH_SACH)
def test_khach_chua_noi_thay_danh_sach_rong_va_loi_moi_lien_ket(khach_c, the_gioi, url):
    r = khach_c.get(url)

    assert r.status_code == 200
    assert "chưa được liên kết" in r.text
    assert BI_MAT not in r.text and "Muc" not in r.text and "Lu" not in re.findall(r">([^<]+)<", r.text)


def test_khach_chua_noi_khong_xem_duoc_ca_id_dung_cua_nguoi_khac(khach_c, the_gioi):
    assert khach_c.get(f"/khach/thu-cung/{the_gioi['a']['pet'].id}").status_code == 404
    assert khach_c.get(f"/khach/hoa-don/{the_gioi['a']['hd'].id}").status_code == 404


# --- IDOR ------------------------------------------------------------------------------------


def _duong_dan_theo_id(the_gioi, loai_chu):
    return [
        ("/khach/thu-cung/{id}", the_gioi[loai_chu]["pet"].id),
        ("/khach/hoa-don/{id}", the_gioi[loai_chu]["hd"].id),
    ]


@pytest.mark.parametrize("mau", ["/khach/thu-cung/{id}", "/khach/hoa-don/{id}"])
def test_id_cua_nguoi_khac_va_id_khong_ton_tai_cho_cung_mot_phan_hoi_404(khach_a, the_gioi, mau):
    id_cua_b = dict(_duong_dan_theo_id(the_gioi, "b"))[mau]

    cua_nguoi_khac = khach_a.get(mau.format(id=id_cua_b))
    khong_ton_tai = khach_a.get(mau.format(id=KHONG_CO))

    assert cua_nguoi_khac.status_code == 404
    assert khong_ton_tai.status_code == 404
    assert cua_nguoi_khac.text == khong_ton_tai.text
    assert BI_MAT not in cua_nguoi_khac.text and "Lu" not in re.findall(r">([^<]+)<", cua_nguoi_khac.text)


@pytest.mark.parametrize("mau", ["/khach/thu-cung/{id}", "/khach/hoa-don/{id}"])
def test_trang_loi_cua_khach_dua_ve_cong_khach_khong_ve_trang_nhan_vien(khach_a, mau):
    r = khach_a.get(mau.format(id=KHONG_CO))

    assert 'href="/khach"' in r.text
    assert 'class="chinh" href="/"' not in r.text


def test_quet_moi_route_khach_co_tham_so_id_deu_nam_trong_phep_thu_idor():
    """Thêm route `/khach/.../{..._id}` mà chưa có ca IDOR ở trên thì phép canh này đỏ."""
    da_thu = {"/khach/thu-cung/{thu_cung_id}", "/khach/hoa-don/{hoa_don_id}"}
    co = {
        duong_dan
        for duong_dan, cac_phuong_thuc in app.openapi()["paths"].items()
        if duong_dan.startswith("/khach") and re.search(r"\{\w*id\}", duong_dan) and "get" in cac_phuong_thuc
    }

    assert co == da_thu, f"Route khách có id chưa được thử IDOR: {sorted(co - da_thu)}"


def test_go_lien_ket_co_hieu_luc_ngay_o_yeu_cau_ke_tiep(db, khach_a, the_gioi):
    """`owner_id` đọc lại từ CSDL ở mỗi yêu cầu: lễ tân gỡ liên kết thì khách mất quyền xem ngay."""
    url = f"/khach/thu-cung/{the_gioi['a']['pet'].id}"
    assert khach_a.get(url).status_code == 200

    db.query(Customer).filter_by(email="a@example.com").one().owner_id = None
    db.commit()

    assert khach_a.get(url).status_code == 404
    assert "chưa được liên kết" in khach_a.get("/khach/thu-cung").text


# --- Chưa đăng nhập / sai loại tài khoản -------------------------------------------------------


@pytest.mark.parametrize("url", TRANG_DANH_SACH + ["/khach/thu-cung/1", "/khach/hoa-don/1"])
def test_chua_dang_nhap_bi_dua_ve_trang_dang_nhap_khach(client, the_gioi, url):
    r = TestClient(app).get(url, follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"


@pytest.mark.parametrize("url", TRANG_DANH_SACH + ["/khach/thu-cung/1", "/khach/hoa-don/1"])
def test_nhan_vien_dang_nhap_khong_vao_duoc_trang_du_lieu_cua_khach(client, seed_basic, the_gioi, url):
    nv = TestClient(app)
    nv.post("/login", data={"username": "quanly", "password": seed_basic["mat_khau"]}, follow_redirects=False)

    r = nv.get(url, follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"
