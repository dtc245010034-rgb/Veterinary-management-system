"""Test đăng nhập qua HTTP.

Phục vụ US-01: TC-001 (đăng nhập đúng), TC-002 (sai mật khẩu không lộ thông tin),
TC-003 (tài khoản bị khóa), TC-004 (chưa đăng nhập bị chuyển về trang đăng nhập).
"""

from app.models.user import User
from app.security import hash_password


def test_dang_nhap_dung_mat_khau_vao_duoc_he_thong(client, seed_basic):
    """TC-001."""
    r = client.post(
        "/login",
        data={"username": "letan", "password": "matkhau123"},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "Tran Thi Le" in r.text


def test_sai_mat_khau_bi_tu_choi(client, seed_basic):
    """TC-002, phần một: sai mật khẩu thì không vào được."""
    r = client.post("/login", data={"username": "letan", "password": "sai-mat-khau"})

    assert r.status_code == 401
    assert "Tên đăng nhập hoặc mật khẩu không đúng" in r.text


def test_bao_loi_giong_het_nhau_du_tai_khoan_co_ton_tai_hay_khong(client, seed_basic):
    """TC-002, phần hai: không được tiết lộ tài khoản có tồn tại hay không.

    Nếu hai trường hợp trả về thông báo khác nhau, kẻ tấn công dò được danh sách tên
    đăng nhập hợp lệ chỉ bằng cách thử và so sánh phản hồi.
    """
    r_co_that = client.post("/login", data={"username": "letan", "password": "sai"})
    r_khong_co = client.post("/login", data={"username": "khong-ton-tai", "password": "sai"})

    assert r_co_that.status_code == r_khong_co.status_code
    assert r_co_that.text == r_khong_co.text


def test_tai_khoan_bi_khoa_khong_dang_nhap_duoc(client, db):
    """TC-003: đúng mật khẩu nhưng tài khoản đã ngưng hoạt động thì vẫn bị từ chối."""
    db.add(
        User(
            username="danghi",
            password_hash=hash_password("matkhau123"),
            full_name="Nguoi Da Nghi",
            role="caretaker",
            is_active=False,
        )
    )
    db.commit()

    r = client.post("/login", data={"username": "danghi", "password": "matkhau123"})

    assert r.status_code == 401
    assert "ngưng hoạt động" in r.text


def test_chua_dang_nhap_bi_chuyen_ve_trang_dang_nhap(client):
    """TC-004."""
    r = client.get("/", follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_dang_xuat_thi_mat_quyen_truy_cap(client, seed_basic):
    client.post("/login", data={"username": "letan", "password": "matkhau123"})

    client.post("/logout")
    r = client.get("/", follow_redirects=False)

    assert r.status_code == 303
