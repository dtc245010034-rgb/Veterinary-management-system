"""R-2 qua HTTP: POST đổi trạng thái kèm `Origin` lạ phải bị 403 và KHÔNG được thực thi."""

from sqlalchemy import select

from app.models.user import User


def dang_nhap(client, username="quanly", password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert r.status_code == 303


def test_post_khoa_tai_khoan_voi_origin_la_bi_403_va_khong_khoa(client, db, seed_basic):
    dang_nhap(client)
    muc_tieu = seed_basic["receptionist"]

    r = client.post(
        f"/users/{muc_tieu.id}/khoa", headers={"Origin": "https://evil.com"}, follow_redirects=False
    )

    assert r.status_code == 403
    assert "Cache-Control" in r.headers and "no-store" in r.headers["Cache-Control"]
    db.expire_all()
    assert db.scalar(select(User.is_active).where(User.id == muc_tieu.id)) is True


def test_cung_post_do_voi_origin_cung_host_van_chay(client, db, seed_basic):
    dang_nhap(client)
    muc_tieu = seed_basic["receptionist"]

    r = client.post(
        f"/users/{muc_tieu.id}/khoa", headers={"Origin": "http://testserver"}, follow_redirects=False
    )

    assert r.status_code == 303
    db.expire_all()
    assert db.scalar(select(User.is_active).where(User.id == muc_tieu.id)) is False


def test_post_khong_co_header_nguon_goc_van_chay_nhu_cu(client, seed_basic):
    r = client.post("/login", data={"username": "letan", "password": "sai"})

    assert r.status_code == 401


def test_dang_nhap_tu_trang_la_cung_bi_chan(client, seed_basic):
    # Login CSRF: kẻ tấn công ép nạn nhân đăng nhập vào tài khoản của kẻ đó.
    r = client.post(
        "/login",
        data={"username": "letan", "password": "matkhau123"},
        headers={"Sec-Fetch-Site": "cross-site"},
    )

    assert r.status_code == 403
    assert "set-cookie" not in r.headers


def test_get_voi_origin_la_khong_bi_chan(client, seed_basic):
    r = client.get("/login", headers={"Origin": "https://evil.com", "Sec-Fetch-Site": "cross-site"})

    assert r.status_code == 200


def test_app_origin_cho_phep_post_tu_dia_chi_cong_khai_dang_sau_proxy(client, seed_basic, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "app_origin", "https://abc.ngrok.app")

    r = client.post(
        "/login",
        data={"username": "letan", "password": "sai"},
        headers={"Origin": "https://abc.ngrok.app"},
    )

    assert r.status_code == 401
