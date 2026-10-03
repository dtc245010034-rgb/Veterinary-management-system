"""Khách xem khung giờ trống theo nhân viên rồi bấm vào một khung để xin lịch (P9 chặng 6).

Đồng hồ đóng băng ở 2026-03-12 08:00. Điều cần chứng minh:
- Trang nhóm khung trống theo từng nhân viên, mỗi khung là link sang form xin lịch đã điền sẵn.
- Không rò rỉ: tên thú cưng, tên và số điện thoại chủ nuôi KHÁC không xuất hiện; lịch người khác chỉ làm khung biến mất.
- Biên quyền: thú cưng của người khác và id không tồn tại cho CÙNG một phản hồi 404.
"""

import html
import re
from datetime import datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

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
NGAY = "2026-03-13"
KHONG_CO = 99999
TEN_THU_CUNG_NGUOI_KHAC = "Lulu-Rieng-Tu"
TEN_CHU_NGUOI_KHAC = "Chu Binh Bi Mat"
SDT_NGUOI_KHAC = "0922222222"


@pytest.fixture
def the_gioi(client, db, seed_basic, frozen_clock):
    dv = Service(code="TAM", name="Tam va say", duration_min=60, price=Decimal("150000"))
    chu_a = Owner(full_name="Chu Anh", phone="0911111111")
    chu_b = Owner(full_name=TEN_CHU_NGUOI_KHAC, phone=SDT_NGUOI_KHAC)
    db.add_all([dv, chu_a, chu_b])
    db.flush()
    pet_a = Pet(owner_id=chu_a.id, name="Muc", species="Cho")
    pet_b = Pet(owner_id=chu_b.id, name=TEN_THU_CUNG_NGUOI_KHAC, species="Cho")
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


@pytest.fixture
def khach_a(the_gioi):
    return _khach("a@example.com")


@pytest.fixture
def khach_c(the_gioi):
    return _khach("c@example.com")


def _xem(khach, the_gioi, pet="pet_a", ngay=NGAY):
    return khach.get(
        "/khach/khung-trong",
        params={"thu_cung_id": the_gioi[pet].id, "dich_vu_id": the_gioi["dv"].id, "ngay": ngay},
    )


def _link_dat_lich(trang):
    """Mọi href trỏ tới form xin lịch, đã giải mã `&amp;`, tách thành dict tham số."""
    ket_qua = []
    for href in re.findall(r'href="(/khach/dat-lich\?[^"]*)"', trang):
        ket_qua.append({k: v[0] for k, v in parse_qs(urlsplit(html.unescape(href)).query).items()})
    return ket_qua


def test_trang_nhom_khung_trong_theo_nhan_vien_voi_link_toi_form_da_dien_san(khach_a, the_gioi):
    r = _xem(khach_a, the_gioi)

    assert r.status_code == 200
    assert "Le Van Cham" in r.text and "Pham Thi Soc" in r.text
    link = _link_dat_lich(r.text)
    assert {"thu_cung_id": str(the_gioi["pet_a"].id), "dich_vu_id": str(the_gioi["dv"].id),
            "nhan_vien_id": str(the_gioi["nv"].id), "ngay": NGAY, "gio": "08:00"} in link
    assert any(l["nhan_vien_id"] != str(the_gioi["nv"].id) for l in link)  # nhân viên thứ hai cũng có khung


def test_trang_khung_trong_khong_ro_ri_du_lieu_nguoi_khac(db, khach_a, the_gioi):
    scheduling.dat_lich(
        db, the_gioi["pet_b"].id, the_gioi["dv"].id, the_gioi["nv"].id, datetime(2026, 3, 13, 9),
        the_gioi["seed"]["receptionist"].id,
    )

    r = _xem(khach_a, the_gioi)

    for bi_mat in (TEN_THU_CUNG_NGUOI_KHAC, TEN_CHU_NGUOI_KHAC, SDT_NGUOI_KHAC, "/owners/", "/pets/"):
        assert bi_mat not in r.text
    # lịch của người khác chỉ làm khung của nhân viên đó biến mất, không để lại dấu vết nào khác
    link_cua_nv = [l["gio"] for l in _link_dat_lich(r.text) if l["nhan_vien_id"] == str(the_gioi["nv"].id)]
    assert "09:00" not in link_cua_nv and "08:30" not in link_cua_nv and "10:00" in link_cua_nv


def test_bam_vao_khung_dien_san_form_roi_gui_duoc_yeu_cau(db, khach_a, the_gioi):
    link = next(l for l in _link_dat_lich(_xem(khach_a, the_gioi).text) if l["gio"] == "10:00" and l["nhan_vien_id"] == str(the_gioi["nv"].id))

    form = khach_a.get("/khach/dat-lich", params=link)

    assert form.status_code == 200
    assert re.search(rf'<option value="{the_gioi["pet_a"].id}"\s+selected', form.text)
    assert re.search(rf'<option value="{the_gioi["nv"].id}"\s+selected', form.text)
    assert f'value="{NGAY}"' in form.text and 'value="10:00"' in form.text

    r = khach_a.post("/khach/dat-lich", data={**link, "ghi_chu": ""}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/khach/lich-hen"
    # khung vừa xin đã bị giữ chỗ nên không còn hiện là trống
    sau = [l["gio"] for l in _link_dat_lich(_xem(khach_a, the_gioi).text) if l["nhan_vien_id"] == str(the_gioi["nv"].id)]
    assert "10:00" not in sau


def test_form_dien_san_thoat_ky_tu_dac_biet_khong_chen_html(khach_a):
    r = khach_a.get("/khach/dat-lich", params={"gio": '"><script>alert(1)</script>', "ngay": "<b>x</b>"})

    assert r.status_code == 200
    assert "<script>alert(1)</script>" not in r.text and "<b>x</b>" not in r.text


def test_thu_cung_cua_nguoi_khac_va_id_khong_ton_tai_cho_cung_mot_404(khach_a, the_gioi):
    cua_nguoi_khac = _xem(khach_a, the_gioi, pet="pet_b")
    ma_khong_co = khach_a.get(
        "/khach/khung-trong", params={"thu_cung_id": KHONG_CO, "dich_vu_id": the_gioi["dv"].id, "ngay": NGAY}
    )

    assert cua_nguoi_khac.status_code == 404 and ma_khong_co.status_code == 404
    assert cua_nguoi_khac.text == ma_khong_co.text


def test_khach_chua_noi_ho_so_thay_loi_giai_thich_va_khong_xem_duoc_khung(khach_c, the_gioi):
    trang = khach_c.get("/khach/khung-trong")
    assert trang.status_code == 200 and "chưa được liên kết" in trang.text

    assert _xem(khach_c, the_gioi).status_code == 404


def test_chua_dang_nhap_bi_day_ve_dang_nhap():
    r = TestClient(app).get("/khach/khung-trong", follow_redirects=False)

    assert r.status_code == 303 and r.headers["location"] == "/khach/dang-nhap"


def test_khong_co_tham_so_chi_hien_form_chon_khong_co_ket_qua(khach_a):
    r = khach_a.get("/khach/khung-trong")

    assert r.status_code == 200 and "Xem giờ trống" in r.text
    assert _link_dat_lich(r.text) == []


def test_ngay_sai_dinh_dang_bao_loi_400_khong_500(khach_a, the_gioi):
    r = _xem(khach_a, the_gioi, ngay="khong-phai-ngay")

    assert r.status_code == 400 and "không đúng định dạng" in r.text


def test_ngay_da_qua_hien_thong_bao_het_gio_trong_chu_khong_loi(khach_a, the_gioi):
    r = _xem(khach_a, the_gioi, ngay="2026-03-11")

    assert r.status_code == 200
    assert _link_dat_lich(r.text) == []
    assert "Le Van Cham" in r.text and "Không còn giờ trống" in r.text
