"""Cổng khách qua HTTP: đăng ký bằng email, đăng nhập, quên mật khẩu, tách phiên khỏi nhân viên (P9 chặng 4a).

Dùng `FakeMailer` thay cho bộ gửi thật: thư nằm trong `mailer.da_gui`, test đọc liên kết từ đó như người
dùng đọc từ hộp thư. Không test nào đọc token từ CSDL (CSDL chỉ giữ băm).
"""

import re

import pytest
from sqlalchemy import select

from app.config import settings
from app.mail.fake import FakeMailer
from app.mail.provider import LoiGuiMail
from app.models.customer import Customer
from app.services import customers as kh
from app.services.login_throttle import MIEN_PHI

GOC = "https://shop.example.com"
MAT_KHAU = "matkhau-khach-1"


@pytest.fixture
def mailer(client):
    from app.mail.service import lay_mailer
    from app.main import app

    fake = FakeMailer()
    app.dependency_overrides[lay_mailer] = lambda: fake
    return fake


@pytest.fixture
def goc(monkeypatch):
    monkeypatch.setattr(settings, "app_origin", GOC)
    return GOC


def _duong_dan_trong_thu(thu) -> str:
    khop = re.search(r"https?://[^/\s]+(/khach/(?:dang-ky|dat-lai)/[A-Za-z0-9_-]+)", thu.noi_dung)
    assert khop, f"Thư không có liên kết: {thu.noi_dung!r}"
    return khop.group(1)


def _dang_ky(client, mailer=None, email="khach@example.com", ten_dang_nhap="nguyenkhach", mat_khau=MAT_KHAU):
    """Đăng ký trực tiếp 3 trường; client được chuyển hướng và đăng nhập khi xong."""
    r = client.post(
        "/khach/dang-ky",
        data={"email": email, "ten_dang_nhap": ten_dang_nhap, "mat_khau": mat_khau},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    return r


def _dang_nhap(client, email="khach@example.com", mat_khau=MAT_KHAU):
    return client.post("/khach/dang-nhap", data={"email": email, "mat_khau": mat_khau}, follow_redirects=False)


# --- Đăng ký (trực tiếp 3 trường) --------------------------------------------------


def test_dang_ky_thanh_cong_vao_thang_cong_khach(client, db):
    r = client.post(
        "/khach/dang-ky",
        data={"email": "  KhachMoi@Example.Com ", "ten_dang_nhap": "  khach_moi.1 ", "mat_khau": MAT_KHAU},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/khach"

    # Lưu db dưới dạng lower() + strip()
    khach = db.scalars(select(Customer).where(Customer.email == "khachmoi@example.com")).first()
    assert khach is not None
    assert khach.ten_dang_nhap == "khach_moi.1"

    # Phiên đăng nhập hoạt động
    cong = client.get("/khach")
    assert cong.status_code == 200


def test_dang_ky_trung_email_khac_hoa_thuong_bi_tu_choi(client):
    _dang_ky(client, email="trung@example.com", ten_dang_nhap="user1")
    client.post("/khach/dang-xuat")

    r = client.post(
        "/khach/dang-ky",
        data={"email": "  TRUNG@EXAMPLE.COM  ", "ten_dang_nhap": "user2", "mat_khau": MAT_KHAU},
    )
    assert r.status_code == 400
    assert "Email này đã được sử dụng" in r.text
    assert 'value="  TRUNG@EXAMPLE.COM  "' in r.text or 'value="TRUNG@EXAMPLE.COM"' in r.text or "TRUNG" in r.text
    assert MAT_KHAU not in r.text  # Không giữ mật khẩu


def test_dang_ky_trung_ten_dang_nhap_khac_hoa_thuong_bi_tu_choi(client):
    _dang_ky(client, email="user1@example.com", ten_dang_nhap="ten_trung")
    client.post("/khach/dang-xuat")

    r = client.post(
        "/khach/dang-ky",
        data={"email": "user2@example.com", "ten_dang_nhap": "  TEN_TRUNG  ", "mat_khau": MAT_KHAU},
    )
    assert r.status_code == 400
    assert "Tên đăng nhập này đã được sử dụng" in r.text


def test_dang_ky_du_lieu_khong_hop_le_bi_tu_choi(client):
    # Email không hợp lệ
    r1 = client.post("/khach/dang-ky", data={"email": "khong-phai-email", "ten_dang_nhap": "validuser", "mat_khau": MAT_KHAU})
    assert r1.status_code == 400
    assert "Email không hợp lệ" in r1.text

    # Tên đăng nhập quá ngắn (<3)
    r2 = client.post("/khach/dang-ky", data={"email": "ok@example.com", "ten_dang_nhap": "ab", "mat_khau": MAT_KHAU})
    assert r2.status_code == 400
    assert "Tên đăng nhập" in r2.text

    # Tên đăng nhập ký tự đặc biệt không hợp lệ
    r3 = client.post("/khach/dang-ky", data={"email": "ok@example.com", "ten_dang_nhap": "user@name!", "mat_khau": MAT_KHAU})
    assert r3.status_code == 400

    # Mật khẩu < 8 ký tự
    r4 = client.post("/khach/dang-ky", data={"email": "ok@example.com", "ten_dang_nhap": "validuser", "mat_khau": "short"})
    assert r4.status_code == 400
    assert "Mật khẩu" in r4.text


def test_dang_ky_lien_tuc_qua_nguong_bi_429(client):
    for i in range(MIEN_PHI):
        assert client.post(
            "/khach/dang-ky",
            data={"email": f"k{i}@example.com", "ten_dang_nhap": f"user_{i}", "mat_khau": MAT_KHAU},
            follow_redirects=False,
        ).status_code == 303
        client.post("/khach/dang-xuat")

    r = client.post(
        "/khach/dang-ky",
        data={"email": "k-ke-tiep@example.com", "ten_dang_nhap": "user_next", "mat_khau": MAT_KHAU},
    )
    assert r.status_code == 429
    assert "retry-after" in r.headers


def test_quen_mat_khau_lien_tuc_qua_nguong_bi_429(client, mailer, goc):
    for i in range(MIEN_PHI):
        assert client.post("/khach/quen-mat-khau", data={"email": f"k{i}@example.com"}).status_code == 200

    r = client.post("/khach/quen-mat-khau", data={"email": "k-ke-tiep@example.com"})

    assert r.status_code == 429
    assert "retry-after" in r.headers


def test_dang_ky_va_quen_mat_khau_dem_rieng_khong_khoa_lan_nhau(client, mailer, goc):
    for i in range(MIEN_PHI):
        client.post(
            "/khach/dang-ky",
            data={"email": f"k{i}@example.com", "ten_dang_nhap": f"user_{i}", "mat_khau": MAT_KHAU},
            follow_redirects=False,
        )
        client.post("/khach/dang-xuat")

    assert client.post("/khach/quen-mat-khau", data={"email": "k@example.com"}).status_code == 200


# --- Đăng nhập --------------------------------------------------------------------


def test_dang_nhap_sai_email_va_sai_mat_khau_cung_mot_thong_bao(client, mailer, goc):
    _dang_ky(client, mailer)
    client.post("/khach/dang-xuat")

    khong_co = _dang_nhap(client, "khong-co@example.com")
    sai_mk = _dang_nhap(client, mat_khau="sai-mat-khau-1")

    assert khong_co.status_code == sai_mk.status_code == 401
    assert "Email hoặc mật khẩu không đúng" in khong_co.text
    assert "Email hoặc mật khẩu không đúng" in sai_mk.text


def test_dang_nhap_dung_vao_cong_khach(client, mailer, goc):
    _dang_ky(client, mailer)
    client.post("/khach/dang-xuat")

    r = _dang_nhap(client, "  KHACH@example.com ")

    assert r.status_code == 303
    assert r.headers["location"] == "/khach"


def test_dang_nhap_sai_lien_tuc_qua_nguong_bi_429_ke_ca_mat_khau_dung(client, mailer, goc):
    _dang_ky(client, mailer)
    client.post("/khach/dang-xuat")
    for _ in range(MIEN_PHI):
        assert _dang_nhap(client, mat_khau="sai-mat-khau-1").status_code == 401

    r = _dang_nhap(client)

    assert r.status_code == 429
    assert "set-cookie" not in r.headers


def test_khach_bi_khoa_thi_phien_dang_mo_chet_ngay(client, mailer, goc, db):
    _dang_ky(client, mailer)
    assert client.get("/khach", follow_redirects=False).status_code == 200

    khach = db.scalars(select(Customer)).one()
    khach.is_active = False
    db.commit()

    r = client.get("/khach", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"


def test_chua_dang_nhap_vao_cong_khach_bi_chuyen_ve_dang_nhap_khach_khong_phai_cua_nhan_vien(client):
    r = client.get("/khach", follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"


def test_dang_xuat_thu_hoi_phien_nen_cookie_cu_phat_lai_khong_con_hieu_luc(client, mailer, goc):
    _dang_ky(client, mailer)
    cookie_cu = client.cookies.get("session")
    assert cookie_cu

    client.post("/khach/dang-xuat")
    client.cookies.set("session", cookie_cu)

    r = client.get("/khach", follow_redirects=False)
    assert r.status_code == 303


# --- Tách khỏi nhân viên -----------------------------------------------------------


def test_cookie_khach_khong_mo_duoc_trang_nhan_vien(client, mailer, goc, seed_basic):
    _dang_ky(client, mailer)

    for url in ("/owners", "/services", "/vaccinations", "/appointments", "/invoices", "/users", "/"):
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 303, url
        assert r.headers["location"] == "/login", url


def test_cookie_nhan_vien_khong_mo_duoc_cong_khach(client, seed_basic):
    client.post("/login", data={"username": "quanly", "password": seed_basic["mat_khau"]})
    assert client.get("/owners", follow_redirects=False).status_code == 200

    r = client.get("/khach", follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"


def test_dang_nhap_nhan_vien_tren_may_dang_giu_phien_khach_thi_xoa_phien_khach(client, mailer, goc, seed_basic):
    _dang_ky(client, mailer)

    client.post("/login", data={"username": "quanly", "password": seed_basic["mat_khau"]})

    assert client.get("/khach", follow_redirects=False).status_code == 303
    assert client.get("/owners", follow_redirects=False).status_code == 200


def test_dang_nhap_khach_tren_may_dang_giu_phien_nhan_vien_thi_xoa_phien_nhan_vien(client, mailer, goc, seed_basic):
    _dang_ky(client, mailer)
    client.post("/khach/dang-xuat")
    client.post("/login", data={"username": "quanly", "password": seed_basic["mat_khau"]})

    _dang_nhap(client)

    assert client.get("/khach", follow_redirects=False).status_code == 200
    r = client.get("/owners", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


# --- Quên mật khẩu, đổi mật khẩu ------------------------------------------------------


def test_quen_mat_khau_email_co_va_khong_co_nhan_cung_mot_phan_hoi(client, mailer, goc):
    _dang_ky(client, mailer)
    client.post("/khach/dang-xuat")
    mailer.da_gui.clear()

    co = client.post("/khach/quen-mat-khau", data={"email": "khach@example.com"})
    khong = client.post("/khach/quen-mat-khau", data={"email": "khong-co@example.com"})

    assert (co.status_code, co.text) == (khong.status_code, khong.text)
    assert [t.den for t in mailer.da_gui] == ["khach@example.com"]


def test_dat_lai_mat_khau_qua_thu_doi_mat_khau_va_giet_phien_cu(client, mailer, goc):
    _dang_ky(client, mailer)
    cookie_cu = client.cookies.get("session")
    mailer.da_gui.clear()

    client.post("/khach/quen-mat-khau", data={"email": "khach@example.com"})
    duong_dan = _duong_dan_trong_thu(mailer.da_gui[0])
    assert client.get(duong_dan).status_code == 200
    moi = "mat-khau-moi-xyz"
    r = client.post(duong_dan, data={"mat_khau": moi, "nhap_lai": moi}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/khach/dang-nhap")

    client.cookies.set("session", cookie_cu)
    assert client.get("/khach", follow_redirects=False).status_code == 303
    assert _dang_nhap(client, mat_khau=MAT_KHAU).status_code == 401
    assert _dang_nhap(client, mat_khau=moi).status_code == 303

    # Liên kết dùng một lần.
    assert client.get(duong_dan).status_code == 400


def test_doi_mat_khau_khi_dang_dang_nhap(client, mailer, goc):
    _dang_ky(client, mailer)

    sai = client.post(
        "/khach/doi-mat-khau", data={"mat_khau_cu": "sai-mat-khau-1", "mat_khau_moi": "mat-khau-moi-xyz", "nhap_lai": "mat-khau-moi-xyz"}
    )
    assert sai.status_code == 400 and "không đúng" in sai.text

    ok = client.post(
        "/khach/doi-mat-khau", data={"mat_khau_cu": MAT_KHAU, "mat_khau_moi": "mat-khau-moi-xyz", "nhap_lai": "mat-khau-moi-xyz"}
    )
    assert ok.status_code == 200 and "Đã đổi mật khẩu" in ok.text
    # Phiên của chính máy này được cấp lại, không bị văng.
    assert client.get("/khach", follow_redirects=False).status_code == 200
    client.post("/khach/dang-xuat")
    assert _dang_nhap(client, mat_khau="mat-khau-moi-xyz").status_code == 303


def test_chua_dang_nhap_thi_khong_doi_duoc_mat_khau(client):
    r = client.post("/khach/doi-mat-khau", data={"mat_khau_cu": "x", "mat_khau_moi": "y", "nhap_lai": "y"}, follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"


def test_thu_hoi_phien_bang_service_giet_cookie_dang_mo(client, mailer, goc, db):
    _dang_ky(client, mailer)
    khach = db.scalars(select(Customer)).one()
    kh.thu_hoi_phien(db, khach.id)

    assert client.get("/khach", follow_redirects=False).status_code == 303
