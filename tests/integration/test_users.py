"""Test phân quyền và quản lý tài khoản nhân viên.

Phục vụ US-02 (TC-007, TC-008) và US-03 (TC-010, TC-011, TC-012).

TC-006 (caretaker mở trang thống kê) và TC-009 (caretaker chỉ thấy lịch của mình) không
kiểm được ở phase này vì trang thống kê thuộc P6 và lịch hẹn thuộc P3. Cơ chế phân quyền
dùng chung được kiểm ở đây qua trang /users; hai TC kia sẽ tick khi trang tương ứng ra đời.
"""

import pytest

from app.models.user import User


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303), f"Đăng nhập {username} thất bại"
    return client


# --- Phân quyền -----------------------------------------------------------------


def test_quan_ly_vao_duoc_trang_tai_khoan(client, seed_basic):
    """TC-008."""
    dang_nhap(client, "quanly")

    r = client.get("/users")

    assert r.status_code == 200


@pytest.mark.parametrize("username", ["letan", "chamsoc1"])
def test_le_tan_va_nhan_vien_cham_soc_bi_chan_khoi_trang_tai_khoan(client, seed_basic, username):
    """TC-007: gõ thẳng URL cũng phải bị chặn, không chỉ ẩn menu."""
    dang_nhap(client, username)

    r = client.get("/users")

    assert r.status_code == 403


def test_trang_bi_chan_hien_thi_trang_loi_co_bo_cuc_khong_phai_json(client, seed_basic):
    """TC-007: người dùng phải thấy trang báo lỗi tử tế, không phải JSON thô."""
    dang_nhap(client, "letan")

    r = client.get("/users")

    assert "Không có quyền truy cập" in r.text
    assert "Về trang chủ" in r.text


def test_chua_dang_nhap_vao_trang_tai_khoan_bi_chuyen_ve_dang_nhap(client, seed_basic):
    r = client.get("/users", follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_menu_chi_hien_muc_thuoc_quyen_cua_vai_tro(client, seed_basic):
    """Lễ tân không được thấy lối vào trang thống kê và trang tài khoản."""
    dang_nhap(client, "letan")

    r = client.get("/")

    assert "/owners" in r.text
    assert "/users" not in r.text
    assert "/stats" not in r.text


# --- Quản lý tài khoản ----------------------------------------------------------


def test_tao_tai_khoan_moi_thi_dang_nhap_duoc_ngay(client, seed_basic):
    """TC-010."""
    dang_nhap(client, "quanly")
    client.post(
        "/users",
        data={
            "username": "letan2",
            "full_name": "Nguyen Thi Hai",
            "role": "receptionist",
            "password": "matkhau456",
        },
    )

    client.post("/logout")
    r = client.post(
        "/login",
        data={"username": "letan2", "password": "matkhau456"},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "Nguyen Thi Hai" in r.text


def test_tao_tai_khoan_trung_ten_dang_nhap_bi_tu_choi(client, seed_basic):
    """TC-011."""
    dang_nhap(client, "quanly")

    r = client.post(
        "/users",
        data={
            "username": "letan",
            "full_name": "Nguoi Khac",
            "role": "caretaker",
            "password": "matkhau456",
        },
    )

    assert r.status_code == 400
    assert "đã tồn tại" in r.text


def test_tao_tai_khoan_voi_vai_tro_khong_hop_le_bi_tu_choi(client, seed_basic):
    dang_nhap(client, "quanly")

    r = client.post(
        "/users",
        data={
            "username": "moi",
            "full_name": "Nguoi Moi",
            "role": "giam-doc",
            "password": "matkhau456",
        },
    )

    assert r.status_code == 400


def test_khoa_tai_khoan_thi_khong_dang_nhap_duoc_nua(client, seed_basic):
    """TC-012, phần một."""
    dang_nhap(client, "quanly")
    ma_le_tan = seed_basic["receptionist"].id

    client.post(f"/users/{ma_le_tan}/khoa")

    client.post("/logout")
    r = client.post("/login", data={"username": "letan", "password": "matkhau123"})

    assert r.status_code == 401
    assert "ngưng hoạt động" in r.text


def test_khoa_tai_khoan_khong_lam_mat_du_lieu_cu(client, db, seed_basic):
    """TC-012, phần hai: khóa chứ không xóa, để lịch sử còn nguyên.

    Xóa tài khoản sẽ kéo theo mất hồ sơ chăm sóc và lịch hẹn do người đó tạo — đó là
    lý do hệ thống dùng cờ is_active thay vì DELETE.
    """
    dang_nhap(client, "quanly")
    ma_le_tan = seed_basic["receptionist"].id

    client.post(f"/users/{ma_le_tan}/khoa")

    con_trong_db = db.get(User, ma_le_tan)
    assert con_trong_db is not None
    assert con_trong_db.is_active is False
    assert con_trong_db.full_name == "Tran Thi Le"


def test_mo_khoa_tai_khoan_thi_dang_nhap_lai_duoc(client, seed_basic):
    dang_nhap(client, "quanly")
    ma_le_tan = seed_basic["receptionist"].id
    client.post(f"/users/{ma_le_tan}/khoa")

    client.post(f"/users/{ma_le_tan}/mo-khoa")

    client.post("/logout")
    r = client.post(
        "/login", data={"username": "letan", "password": "matkhau123"}, follow_redirects=True
    )
    assert r.status_code == 200


def test_quan_ly_khong_the_tu_khoa_chinh_minh(client, seed_basic):
    """Tự khóa mình sẽ đẩy quản lý ra khỏi hệ thống và không ai mở lại được."""
    dang_nhap(client, "quanly")
    ma_quan_ly = seed_basic["manager"].id

    r = client.post(f"/users/{ma_quan_ly}/khoa")

    assert r.status_code == 400


def test_phien_dang_nhap_het_hieu_luc_ngay_khi_tai_khoan_bi_khoa(client, db, seed_basic):
    """Người đang đăng nhập mà bị khóa thì mất quyền ngay, không đợi đăng xuất."""
    dang_nhap(client, "letan")
    assert client.get("/").status_code == 200

    seed_basic["receptionist"].is_active = False
    db.commit()

    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303
