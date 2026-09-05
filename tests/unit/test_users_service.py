"""Test cho app/services/users.py — nghiệp vụ quản lý tài khoản nhân viên.

Phục vụ US-03 — TC-010 → TC-012.

Bốn quy tắc ở đây trước nằm trong router nên chỉ kiểm được qua HTTP. Chuyển ra tầng
services để kiểm thẳng, không cần khởi động app: quy tắc "quản lý không tự khóa chính
mình" là nghiệp vụ thuần, không dính gì tới HTTP.
"""

import pytest

from app.models.user import User
from app.security import verify_password
from app.services import users as nv
from app.services.errors import LoiNghiepVu


# --- Tạo tài khoản ---------------------------------------------------------------


def test_tao_tai_khoan_luu_dung_vai_tro_va_ten(db, seed_basic):
    u = nv.tao_tai_khoan(db, "letan2", "Nguyen Thi Hai", "receptionist", "matkhau456")

    assert u.id is not None
    assert u.username == "letan2"
    assert u.role == "receptionist"
    assert u.is_active is True


def test_tao_tai_khoan_bam_mat_khau_khong_luu_ban_goc(db, seed_basic):
    """TC-005 ở tầng nghiệp vụ: không đâu trong bản ghi còn mật khẩu gốc."""
    u = nv.tao_tai_khoan(db, "letan2", "Nguyen Thi Hai", "receptionist", "matkhau456")

    assert u.password_hash != "matkhau456"
    assert verify_password("matkhau456", u.password_hash)


def test_tao_tai_khoan_trung_username_bi_tu_choi(db, seed_basic):
    """TC-012. Ràng buộc UNIQUE ở CSDL cũng chặn, nhưng chặn ở đây mới có thông báo đọc được."""
    with pytest.raises(LoiNghiepVu) as loi:
        nv.tao_tai_khoan(db, "letan", "Trung ten dang nhap", "receptionist", "matkhau456")

    assert "letan" in str(loi.value)


def test_tao_tai_khoan_vai_tro_khong_hop_le_bi_tu_choi(db, seed_basic):
    """Ba vai trò là cố định. Vai trò lạ lọt vào sẽ làm mọi phép kiểm quyền sau đó vô nghĩa."""
    with pytest.raises(LoiNghiepVu):
        nv.tao_tai_khoan(db, "aidong", "Vai tro la", "admin", "matkhau456")

    assert db.query(User).filter_by(username="aidong").first() is None


# --- Khóa và mở khóa -------------------------------------------------------------


def test_khoa_tai_khoan_chuyen_is_active_ve_false(db, seed_basic):
    """TC-011."""
    letan = seed_basic["receptionist"]
    quan_ly = seed_basic["manager"]

    nv.khoa_tai_khoan(db, letan.id, nguoi_thao_tac_id=quan_ly.id)

    assert letan.is_active is False


def test_quan_ly_khong_tu_khoa_chinh_minh(db, seed_basic):
    """Ca biên quan trọng nhất của nhóm này.

    Tự khóa mình sẽ đẩy quản lý ra khỏi hệ thống, và không còn ai mở lại được — hệ thống
    khóa cứng, chỉ sửa được bằng cách vào thẳng CSDL.
    """
    quan_ly = seed_basic["manager"]

    with pytest.raises(LoiNghiepVu):
        nv.khoa_tai_khoan(db, quan_ly.id, nguoi_thao_tac_id=quan_ly.id)

    assert quan_ly.is_active is True


def test_khoa_tai_khoan_khong_ton_tai_bi_tu_choi(db, seed_basic):
    with pytest.raises(LoiNghiepVu):
        nv.khoa_tai_khoan(db, 9999, nguoi_thao_tac_id=seed_basic["manager"].id)


def test_mo_khoa_tai_khoan_chuyen_is_active_ve_true(db, seed_basic):
    letan = seed_basic["receptionist"]
    nv.khoa_tai_khoan(db, letan.id, nguoi_thao_tac_id=seed_basic["manager"].id)

    nv.mo_khoa_tai_khoan(db, letan.id)

    assert letan.is_active is True


def test_mo_khoa_tai_khoan_khong_ton_tai_bi_tu_choi(db, seed_basic):
    with pytest.raises(LoiNghiepVu):
        nv.mo_khoa_tai_khoan(db, 9999)


# --- Danh sách -------------------------------------------------------------------


def test_danh_sach_tai_khoan_sap_theo_vai_tro_roi_ten(db, seed_basic):
    ds = nv.danh_sach_tai_khoan(db)

    assert [u.username for u in ds] == ["chamsoc1", "chamsoc2", "quanly", "letan"]


def test_danh_sach_tai_khoan_van_hien_tai_khoan_da_khoa(db, seed_basic):
    """Khóa không phải xóa — quản lý phải thấy để mở lại được."""
    letan = seed_basic["receptionist"]
    nv.khoa_tai_khoan(db, letan.id, nguoi_thao_tac_id=seed_basic["manager"].id)

    assert letan.id in [u.id for u in nv.danh_sach_tai_khoan(db)]
