"""Nghiệp vụ quản lý tài khoản nhân viên.

Phục vụ US-03 — TC-010 → TC-012.

Bốn thao tác này trước nằm thẳng trong `app/routers/users.py`, vi phạm ranh giới ở
docs/architecture.md. Chuyển ra đây để kiểm được mà không cần khởi động app: quy tắc
"quản lý không tự khóa chính mình" là nghiệp vụ thuần, không dính gì tới HTTP.

Không import fastapi.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import VAI_TRO, User
from app.security import hash_password
from app.services.errors import LoiNghiepVu


def danh_sach_tai_khoan(db: Session) -> list[User]:
    """Cả tài khoản đã khóa. Khóa không phải xóa — quản lý phải thấy để mở lại được."""
    return list(db.scalars(select(User).order_by(User.role, User.username)))


def tao_tai_khoan(
    db: Session, username: str, full_name: str, role: str, password: str
) -> User:
    """TC-010, TC-012."""
    if role not in VAI_TRO:
        raise LoiNghiepVu("Vai trò không hợp lệ.")

    # Ràng buộc UNIQUE ở CSDL cũng chặn được, nhưng chặn ở đây mới có thông báo đọc được
    # thay vì một IntegrityError.
    if db.scalar(select(User).where(User.username == username)):
        raise LoiNghiepVu(f"Tên đăng nhập “{username}” đã tồn tại.")

    tai_khoan = User(
        username=username,
        full_name=full_name,
        role=role,
        password_hash=hash_password(password),
    )
    db.add(tai_khoan)
    db.commit()
    db.refresh(tai_khoan)
    return tai_khoan


def khoa_tai_khoan(db: Session, ma_tai_khoan: int, nguoi_thao_tac_id: int) -> User:
    """TC-011.

    Tự khóa mình sẽ đẩy quản lý ra khỏi hệ thống và không còn ai mở lại được — hệ thống
    khóa cứng, chỉ sửa được bằng cách vào thẳng CSDL.
    """
    if ma_tai_khoan == nguoi_thao_tac_id:
        raise LoiNghiepVu("Bạn không thể khóa chính tài khoản của mình.")

    return _dat_trang_thai(db, ma_tai_khoan, False)


def mo_khoa_tai_khoan(db: Session, ma_tai_khoan: int) -> User:
    return _dat_trang_thai(db, ma_tai_khoan, True)


def _dat_trang_thai(db: Session, ma_tai_khoan: int, dang_hoat_dong: bool) -> User:
    tai_khoan = db.get(User, ma_tai_khoan)
    if tai_khoan is None:
        raise LoiNghiepVu("Không tìm thấy tài khoản.")

    tai_khoan.is_active = dang_hoat_dong
    db.commit()
    db.refresh(tai_khoan)
    return tai_khoan
