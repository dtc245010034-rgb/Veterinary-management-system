"""Lỗi giao diện phát hiện khi demo thử 28/10: đường sang cổng khách, đường dẫn hay gõ nhầm, script meme.

Phục vụ buổi demo 31/10 trước giảng viên; xem `docs/plans/2026-10-28-sua-loi-demo-28-10.md`.
"""

import pytest


def _dang_nhap(client, username):
    r = client.post("/login", data={"username": username, "password": "matkhau123"})
    assert r.status_code in (200, 303)


# --- Lỗi 3: đường đi giữa cổng nhân viên và cổng khách -----------------------------------------

def test_trang_dang_nhap_nhan_vien_co_link_sang_cong_khach(client):
    r = client.get("/login")

    assert r.status_code == 200
    assert 'href="/khach/dang-nhap"' in r.text
    assert "Bạn là khách hàng?" in r.text


def test_trang_dang_nhap_khach_co_link_dang_ky_va_sang_cong_nhan_vien(client):
    r = client.get("/khach/dang-nhap")

    assert r.status_code == 200
    assert 'href="/khach/dang-ky"' in r.text
    assert 'href="/login"' in r.text
    assert "Bạn là nhân viên cửa hàng?" in r.text


@pytest.mark.parametrize(
    ("nguon", "dich"),
    [
        ("/login/khach", "/khach/dang-nhap"),
        ("/login/khach/dang-nhap", "/khach/dang-nhap"),
        ("/dang-ky", "/khach/dang-ky"),
        ("/register", "/khach/dang-ky"),
    ],
)
def test_url_hay_go_nham_chuyen_303_ve_dung_dich(client, nguon, dich):
    r = client.get(nguon, follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == dich


# --- Lỗi 5: pet-meme.js được nạp lại, mặc định BẬT và có nút bật/tắt ----------------------
# Hành vi của script (mặc định bật, nút bật/tắt, không chèn vào trang `giua-man-hinh`) chạy trên trình duyệt nên
# pytest không kiểm được; nó được kiểm bằng Playwright (ghi ở log phiên 2026-10-28-02). Pytest chỉ giữ việc cả
# hai template nền vẫn nạp script, để nút bật/tắt không âm thầm biến mất.

def test_trang_nhan_vien_nap_pet_meme(client, seed_basic, frozen_clock):
    _dang_nhap(client, "letan")

    r = client.get("/appointments")

    assert r.status_code == 200
    assert "/static/pet-meme.js" in r.text


def test_trang_khach_nap_pet_meme(client, db, seed_basic):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.models.customer import Customer
    from app.security import hash_password

    db.add(Customer(email="a@example.com", full_name="Khach A", password_hash=hash_password("matkhau-khach-1")))
    db.commit()
    khach = TestClient(app)
    assert khach.post("/khach/dang-nhap", data={"email": "a@example.com", "mat_khau": "matkhau-khach-1"}, follow_redirects=False).status_code == 303

    r = khach.get("/khach")

    assert r.status_code == 200
    assert "/static/pet-meme.js" in r.text


def test_trang_404_nap_pet_meme(client, seed_basic):
    _dang_nhap(client, "letan")

    r = client.get("/khong-co-trang-nay")

    assert r.status_code == 404
    assert "/static/pet-meme.js" in r.text
