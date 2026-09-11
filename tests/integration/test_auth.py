"""Test đăng nhập qua HTTP.

Phục vụ US-01: TC-001 (đăng nhập đúng), TC-002 (sai mật khẩu không lộ thông tin),
TC-003 (tài khoản bị khóa), TC-004 (chưa đăng nhập bị chuyển về trang đăng nhập).
"""

import pytest

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



# --- Lỗi tìm được khi rà bằng chuột trên trình duyệt (P4) ------------------------


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


def test_url_khong_khop_route_nao_van_hien_trang_loi_co_bo_cuc(client, seed_basic):
    """TC-007 mở rộng: 404 do không khớp route cũng phải là trang, không phải JSON.

    Handler đăng ký trên `fastapi.HTTPException`, còn route không khớp ném
    `starlette.HTTPException` — lớp cha. Đăng ký ở lớp con không bắt được lớp cha, nên
    `/stats` (link có sẵn trong menu quản lý) trả `{"detail":"Not Found"}` trên nền đen.
    """
    dang_nhap(client, "quanly")

    r = client.get("/khong-co-trang-nay")

    assert r.status_code == 404
    assert "Không tìm thấy trang" in r.text
    assert "detail" not in r.text


def test_trang_loi_404_khong_hien_chu_tieng_anh_cua_framework(client, seed_basic):
    """Trang 404 có bố cục rồi, nhưng dòng mô tả vẫn là "Not Found" của Starlette.

    Người dùng từng gặp trang này qua link **Thống kê** trong menu quản lý, trước khi P6
    dựng trang đó. CLAUDE.md mục 5: thông báo hiển thị cho người dùng viết bằng tiếng Việt.
    Ca 403 không dính vì thông điệp do chính dự án viết.
    """
    dang_nhap(client, "quanly")

    r = client.get("/khong-co-trang-nay")

    assert "Not Found" not in r.text
    assert "Đường dẫn này không tồn tại" in r.text


def test_trang_loi_403_van_giu_nguyen_thong_diep_cua_du_an(client, seed_basic):
    """Ca biên: chỉ thay chữ mặc định của framework, không nuốt thông điệp mình viết."""
    dang_nhap(client, "letan")

    r = client.get("/users")

    assert r.status_code == 403
    assert "Bạn không có quyền" in r.text


@pytest.mark.parametrize("username", ["quanly", "letan", "chamsoc1"])
def test_moi_vai_tro_deu_co_link_menu_toi_bang_gia_dich_vu(client, seed_basic, username):
    """Bảng phân quyền US-02 cho cả ba vai trò quyền xem dịch vụ.

    Trước đây chỉ `manager` có link; lễ tân và nhân viên mở được trang nhưng phải gõ URL.
    """
    dang_nhap(client, username)

    r = client.get("/")

    assert 'href="/services"' in r.text
