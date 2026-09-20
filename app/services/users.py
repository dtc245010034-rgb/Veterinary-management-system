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
from app.security import hash_password, verify_password
from app.services.errors import LoiKhongTimThay, LoiNghiepVu


# Một luật duy nhất, cố ý không thêm điều kiện chữ/số. Mật khẩu 1 ký tự từng đăng nhập
# được (M-04, đo bằng Chrome 20/09). Hằng nằm ở tầng services vì cả ba đường đặt mật khẩu
# — tạo tài khoản, quản lý đặt lại, người dùng tự đổi — đều phải đi qua cùng một phép kiểm.
DO_DAI_MAT_KHAU_TOI_THIEU = 8


def kiem_mat_khau(password: str) -> None:
    """Ném `LoiNghiepVu` nếu mật khẩu không đạt. Không trả về gì khi đạt."""
    if len(password) < DO_DAI_MAT_KHAU_TOI_THIEU:
        raise LoiNghiepVu(
            f"Mật khẩu phải dài ít nhất {DO_DAI_MAT_KHAU_TOI_THIEU} ký tự."
        )


def danh_sach_tai_khoan(db: Session) -> list[User]:
    """Cả tài khoản đã khóa. Khóa không phải xóa — quản lý phải thấy để mở lại được."""
    return list(db.scalars(select(User).order_by(User.role, User.username)))


def tao_tai_khoan(
    db: Session, username: str, full_name: str, role: str, password: str
) -> User:
    """TC-010, TC-012."""
    if role not in VAI_TRO:
        raise LoiNghiepVu("Vai trò không hợp lệ.")

    kiem_mat_khau(password)

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


def sua_tai_khoan(
    db: Session,
    ma_tai_khoan: int,
    full_name: str,
    role: str,
    nguoi_thao_tac_id: int | None = None,
) -> User:
    """Sửa họ tên và vai trò. US-03 nói "tạo, **sửa**, khóa" — phần sửa thiếu từ P1 (M-02).

    Không cho đổi `username`: đó là thứ nhân viên nhớ để đăng nhập, và là khóa tra cứu
    trong log phiên. Đổi tên đăng nhập là tạo tài khoản khác chứ không phải sửa.
    """
    tai_khoan = db.get(User, ma_tai_khoan)
    if tai_khoan is None:
        raise LoiKhongTimThay("Không tìm thấy tài khoản.")

    if role not in VAI_TRO:
        raise LoiNghiepVu("Vai trò không hợp lệ.")

    ten = (full_name or "").strip()
    if not ten:
        raise LoiNghiepVu("Họ tên không được để trống.")

    # Cùng lớp với "không tự khóa mình" (TC-011): quản lý tự hạ vai trò là mất quyền vào
    # trang tài khoản, và không còn ai nâng lại được.
    if (
        nguoi_thao_tac_id is not None
        and ma_tai_khoan == nguoi_thao_tac_id
        and tai_khoan.role == "manager"
        and role != "manager"
    ):
        raise LoiNghiepVu("Bạn không thể tự bỏ vai trò quản lý của mình.")

    tai_khoan.full_name = ten
    tai_khoan.role = role
    db.commit()
    db.refresh(tai_khoan)
    return tai_khoan


def dat_lai_mat_khau(db: Session, ma_tai_khoan: int, mat_khau_moi: str) -> User:
    """Quản lý đặt lại cho nhân viên quên mật khẩu — **không** hỏi mật khẩu cũ.

    Trước khi có hàm này, quên mật khẩu là mất hẳn tài khoản (M-02).
    """
    tai_khoan = db.get(User, ma_tai_khoan)
    if tai_khoan is None:
        raise LoiKhongTimThay("Không tìm thấy tài khoản.")

    kiem_mat_khau(mat_khau_moi)
    tai_khoan.password_hash = hash_password(mat_khau_moi)
    db.commit()
    db.refresh(tai_khoan)
    return tai_khoan


def doi_mat_khau(
    db: Session, ma_tai_khoan: int, mat_khau_cu: str, mat_khau_moi: str
) -> User:
    """Người dùng tự đổi mật khẩu của chính mình — **phải** nhập đúng mật khẩu cũ.

    Khác `dat_lai_mat_khau` ở đúng điểm đó: ai ngồi vào máy quầy đang mở phiên cũng đổi
    được mật khẩu nếu không hỏi lại.
    """
    tai_khoan = db.get(User, ma_tai_khoan)
    if tai_khoan is None:
        raise LoiKhongTimThay("Không tìm thấy tài khoản.")

    if not verify_password(mat_khau_cu, tai_khoan.password_hash):
        raise LoiNghiepVu("Mật khẩu hiện tại không đúng.")

    kiem_mat_khau(mat_khau_moi)
    tai_khoan.password_hash = hash_password(mat_khau_moi)
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
        raise LoiKhongTimThay("Không tìm thấy tài khoản.")

    tai_khoan.is_active = dang_hoat_dong
    db.commit()
    db.refresh(tai_khoan)
    return tai_khoan
