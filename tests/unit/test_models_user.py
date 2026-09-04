"""Test cho app/models/user.py — bảng users.

Phục vụ US-01, US-03. Ràng buộc ở đây là nền cho TC-003 (tài khoản bị khóa),
TC-011 (tên đăng nhập trùng) và TC-012 (khóa tài khoản, dữ liệu cũ còn nguyên).

Test chạy trên SQLite thật (in-memory), không mock, nên bắt được cả ràng buộc
UNIQUE và CHECK ở tầng CSDL chứ không chỉ ở tầng Python.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User


def test_tao_user_mac_dinh_dang_hoat_dong(db):
    """Tài khoản mới tạo phải dùng được ngay, không cần bật thủ công."""
    u = User(
        username="letan",
        password_hash="bam",
        full_name="Tran Thi Le",
        role="receptionist",
    )
    db.add(u)
    db.commit()

    assert u.is_active is True


def test_created_at_tu_dong_dien(db):
    u = User(username="letan", password_hash="bam", full_name="Le", role="receptionist")
    db.add(u)
    db.commit()

    assert u.created_at is not None


def test_username_trung_bi_tu_choi(db):
    """TC-011: hai tài khoản không được cùng tên đăng nhập."""
    db.add(User(username="letan", password_hash="a", full_name="Le 1", role="receptionist"))
    db.commit()

    db.add(User(username="letan", password_hash="b", full_name="Le 2", role="caretaker"))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("role", ["manager", "receptionist", "caretaker"])
def test_ba_vai_tro_hop_le_deu_luu_duoc(db, role):
    u = User(username=f"nv-{role}", password_hash="bam", full_name="Nhan vien", role=role)
    db.add(u)
    db.commit()

    assert u.role == role


def test_vai_tro_ngoai_ba_gia_tri_bi_tu_choi(db):
    """Vai trò sai chính tả phải bị chặn ở tầng CSDL.

    Nếu không, một lỗi gõ như 'reception' sẽ tạo ra tài khoản không khớp bất kỳ
    luật phân quyền nào — người dùng đăng nhập được nhưng không thấy gì, và lỗi
    này rất khó lần ra.
    """
    db.add(User(username="sai", password_hash="bam", full_name="Sai", role="reception"))

    with pytest.raises(IntegrityError):
        db.commit()
