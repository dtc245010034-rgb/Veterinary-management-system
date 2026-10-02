"""R-3 (rà soát 02/10): cookie phiên là chuỗi tự đủ, nên trước đây đăng xuất chỉ xóa cookie ở trình
duyệt — ai đã chép cookie cũ vẫn vào được tới khi phiên hết hạn sau 14 ngày.

Giờ mỗi tài khoản có `session_version`, cookie mang số phiên bản lúc đăng nhập; đăng xuất, đổi/đặt lại
mật khẩu và khóa tài khoản đều tăng số đó nên mọi cookie cũ chết ngay.
"""

import base64
import json

import itsdangerous
from sqlalchemy import select

from app.config import settings
from app.models.user import User

MAT_KHAU = "matkhau123"


def dang_nhap(client, username):
    client.cookies.clear()
    r = client.post("/login", data={"username": username, "password": MAT_KHAU}, follow_redirects=False)
    assert r.status_code == 303
    return client.cookies.get("session")


def dung_cookie(client, cookie):
    client.cookies.clear()
    if cookie is not None:
        client.cookies.set("session", cookie)


def vao_trang_chu(client):
    return client.get("/", follow_redirects=False).status_code


def test_cookie_cu_sau_dang_xuat_khong_con_dung_duoc(client, seed_basic):
    cookie_cu = dang_nhap(client, "letan")
    assert vao_trang_chu(client) == 200

    client.post("/logout", follow_redirects=False)

    dung_cookie(client, cookie_cu)
    assert vao_trang_chu(client) == 303


def test_doi_mat_khau_thu_hoi_cookie_o_thiet_bi_khac_nhung_giu_thiet_bi_dang_dung(client, seed_basic):
    cookie_may_khac = dang_nhap(client, "letan")
    cookie_may_nay = dang_nhap(client, "letan")

    r = client.post(
        "/doi-mat-khau",
        data={"mat_khau_cu": MAT_KHAU, "mat_khau_moi": "matkhaumoi456", "nhap_lai": "matkhaumoi456"},
        follow_redirects=False,
    )
    assert r.status_code == 200
    cookie_sau_doi = client.cookies.get("session")

    dung_cookie(client, cookie_may_khac)
    assert vao_trang_chu(client) == 303
    dung_cookie(client, cookie_may_nay)
    assert vao_trang_chu(client) == 303, "cookie trước khi đổi mật khẩu phải chết, kể cả ở máy đang dùng"
    dung_cookie(client, cookie_sau_doi)
    assert vao_trang_chu(client) == 200, "máy vừa đổi mật khẩu không được bị đá ra"


def test_quan_ly_dat_lai_mat_khau_thi_cookie_cu_cua_nhan_vien_chet(client, seed_basic):
    cookie_nhan_vien = dang_nhap(client, "letan")
    dang_nhap(client, "quanly")

    r = client.post(
        f"/users/{seed_basic['receptionist'].id}/dat-lai-mat-khau",
        data={"mat_khau_moi": "matkhaumoi456"},
        follow_redirects=False,
    )
    assert r.status_code in (200, 303)

    dung_cookie(client, cookie_nhan_vien)
    assert vao_trang_chu(client) == 303


def test_khoa_roi_mo_khoa_khong_hoi_sinh_cookie_cu(client, seed_basic):
    cookie_nhan_vien = dang_nhap(client, "letan")
    dang_nhap(client, "quanly")
    ma = seed_basic["receptionist"].id
    client.post(f"/users/{ma}/khoa", follow_redirects=False)
    client.post(f"/users/{ma}/mo-khoa", follow_redirects=False)

    dung_cookie(client, cookie_nhan_vien)
    assert vao_trang_chu(client) == 303


def test_dang_nhap_lai_sau_khi_bi_thu_hoi_van_duoc(client, seed_basic):
    cookie_cu = dang_nhap(client, "letan")
    client.post("/logout", follow_redirects=False)

    dang_nhap(client, "letan")

    assert vao_trang_chu(client) == 200
    dung_cookie(client, cookie_cu)
    assert vao_trang_chu(client) == 303


def test_cookie_dung_truoc_khi_co_session_version_van_hop_le_voi_phien_ban_0(client, db, seed_basic):
    # Cookie của phiên mở trước khi nâng cấp không có khóa `sv`; coi như 0 để người dùng đang
    # đăng nhập không bị đá ra hàng loạt khi cập nhật ứng dụng.
    ma = seed_basic["receptionist"].id
    du_lieu = base64.b64encode(json.dumps({"user_id": ma}).encode("utf-8"))
    cookie = itsdangerous.TimestampSigner(settings.secret_key).sign(du_lieu).decode("utf-8")

    dung_cookie(client, cookie)

    assert vao_trang_chu(client) == 200
    assert db.scalar(select(User.session_version).where(User.id == ma)) == 0
