"""Phiên đăng nhập và phân quyền theo vai trò.

Dùng session cookie của Starlette, không dùng JWT: ứng dụng server-rendered, không có
client tách rời, nên JWT chỉ thêm phức tạp mà không giải quyết vấn đề nào.

Phân quyền viết dưới dạng dependency của FastAPI thay vì decorator, để test được độc lập
và hiện trong OpenAPI schema.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User

KHOA_SESSION = "user_id"


class ChuaDangNhap(Exception):
    """Chưa đăng nhập — trình xử lý sẽ chuyển hướng về trang đăng nhập."""


def dang_nhap_session(request: Request, user: User) -> None:
    request.session[KHOA_SESSION] = user.id


def dang_xuat_session(request: Request) -> None:
    request.session.pop(KHOA_SESSION, None)


def nguoi_dung_hien_tai_hoac_none(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Người đang đăng nhập, hoặc None. Dùng cho trang công khai như trang đăng nhập."""
    user_id = request.session.get(KHOA_SESSION)
    if user_id is None:
        return None

    user = db.get(User, user_id)
    # Tài khoản bị khóa giữa chừng thì phiên cũ phải hết hiệu lực ngay, không đợi
    # người dùng đăng xuất.
    if user is None or not user.is_active:
        return None

    return user


def nguoi_dung_hien_tai(user: User | None = Depends(nguoi_dung_hien_tai_hoac_none)) -> User:
    """Bắt buộc đã đăng nhập."""
    if user is None:
        raise ChuaDangNhap()
    return user


def yeu_cau_vai_tro(*vai_tro: str):
    """Dependency chặn theo vai trò.

    Ví dụ: Depends(yeu_cau_vai_tro("manager")) cho trang chỉ quản lý mới vào được.
    """

    def kiem_tra(user: User = Depends(nguoi_dung_hien_tai)) -> User:
        if user.role not in vai_tro:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập chức năng này.",
            )
        return user

    return kiem_tra
