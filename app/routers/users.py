"""Router quản lý tài khoản nhân viên. Chỉ vai trò manager.

Phục vụ US-03. Chỉ làm việc HTTP — theo ranh giới trong docs/architecture.md.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import yeu_cau_vai_tro
from app.db import get_db
from app.models.user import VAI_TRO, User
from app.security import hash_password
from app.templates import templates

router = APIRouter(prefix="/users")

chi_quan_ly = Depends(yeu_cau_vai_tro("manager"))


def _danh_sach(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.role, User.username)))


def _render(request: Request, db: Session, user: User, loi: str | None = None, ma: int = 200):
    return templates.TemplateResponse(
        request,
        "users.html",
        {"user": user, "danh_sach": _danh_sach(db), "vai_tro": VAI_TRO, "loi": loi},
        status_code=ma,
    )


@router.get("", response_class=HTMLResponse)
def trang_tai_khoan(request: Request, user: User = chi_quan_ly, db: Session = Depends(get_db)):
    return _render(request, db, user)


@router.post("", response_class=HTMLResponse)
def tao_tai_khoan(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    if role not in VAI_TRO:
        return _render(request, db, user, "Vai trò không hợp lệ.", status.HTTP_400_BAD_REQUEST)

    if db.scalar(select(User).where(User.username == username)):
        return _render(
            request,
            db,
            user,
            f"Tên đăng nhập “{username}” đã tồn tại.",
            status.HTTP_400_BAD_REQUEST,
        )

    db.add(
        User(
            username=username,
            full_name=full_name,
            role=role,
            password_hash=hash_password(password),
        )
    )
    db.commit()
    return RedirectResponse("/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{ma_tai_khoan}/khoa", response_class=HTMLResponse)
def khoa_tai_khoan(
    request: Request,
    ma_tai_khoan: int,
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    if ma_tai_khoan == user.id:
        # Tự khóa mình sẽ đẩy quản lý ra khỏi hệ thống và không còn ai mở lại được.
        return _render(
            request, db, user, "Bạn không thể khóa chính tài khoản của mình.", status.HTTP_400_BAD_REQUEST
        )

    tai_khoan = db.get(User, ma_tai_khoan)
    if tai_khoan is None:
        return _render(request, db, user, "Không tìm thấy tài khoản.", status.HTTP_400_BAD_REQUEST)

    tai_khoan.is_active = False
    db.commit()
    return RedirectResponse("/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{ma_tai_khoan}/mo-khoa", response_class=HTMLResponse)
def mo_khoa_tai_khoan(
    request: Request,
    ma_tai_khoan: int,
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    tai_khoan = db.get(User, ma_tai_khoan)
    if tai_khoan is None:
        return _render(request, db, user, "Không tìm thấy tài khoản.", status.HTTP_400_BAD_REQUEST)

    tai_khoan.is_active = True
    db.commit()
    return RedirectResponse("/users", status_code=status.HTTP_303_SEE_OTHER)
