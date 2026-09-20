"""Router quản lý tài khoản nhân viên. Chỉ vai trò manager.

Phục vụ US-03. Chỉ làm việc HTTP — theo ranh giới trong docs/architecture.md.
Quy tắc nghiệp vụ nằm ở app/services/users.py.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import yeu_cau_vai_tro
from app.db import get_db
from app.models.user import TEN_VAI_TRO, VAI_TRO, User
from app.services import scheduling
from app.services import users as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/users")

chi_quan_ly = Depends(yeu_cau_vai_tro("manager"))


def _render(request: Request, db: Session, user: User, loi: str | None = None, ma: int = 200):
    return templates.TemplateResponse(
        request,
        "users.html",
        {
            "user": user,
            "danh_sach": nv.danh_sach_tai_khoan(db),
            # Nhân viên đã khóa mà còn giữ lịch thì phải chuyển người (S4).
            "lich_chua_lam": scheduling.so_lich_chua_lam_theo_nhan_vien(db),
            "vai_tro": VAI_TRO,
            "ten_vai_tro": TEN_VAI_TRO,
            "loi": loi,
        },
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
    # Mặc định "" chứ không phải `Form(...)`: ô trống làm FastAPI trả JSON thô 422 kèm tên
    # trường nội bộ (N-02). Để chuỗi rỗng đi tiếp tới `kiem_mat_khau` thì người dùng nhận
    # được câu tiếng Việt như mọi lỗi nhập liệu khác.
    password: str = Form(""),
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.tao_tai_khoan(db, username, full_name, role, password)
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return _ve_danh_sach()


@router.post("/{ma_tai_khoan}/sua", response_class=HTMLResponse)
def sua_tai_khoan(
    request: Request,
    ma_tai_khoan: int,
    full_name: str = Form(""),
    role: str = Form(""),
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.sua_tai_khoan(db, ma_tai_khoan, full_name, role, nguoi_thao_tac_id=user.id)
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return _ve_danh_sach()


@router.post("/{ma_tai_khoan}/dat-lai-mat-khau", response_class=HTMLResponse)
def dat_lai_mat_khau(
    request: Request,
    ma_tai_khoan: int,
    mat_khau_moi: str = Form(""),
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.dat_lai_mat_khau(db, ma_tai_khoan, mat_khau_moi)
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return _ve_danh_sach()


@router.post("/{ma_tai_khoan}/khoa", response_class=HTMLResponse)
def khoa_tai_khoan(
    request: Request,
    ma_tai_khoan: int,
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.khoa_tai_khoan(db, ma_tai_khoan, nguoi_thao_tac_id=user.id)
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return _ve_danh_sach()


@router.post("/{ma_tai_khoan}/mo-khoa", response_class=HTMLResponse)
def mo_khoa_tai_khoan(
    request: Request,
    ma_tai_khoan: int,
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.mo_khoa_tai_khoan(db, ma_tai_khoan)
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return _ve_danh_sach()


def _ve_danh_sach() -> RedirectResponse:
    return RedirectResponse("/users", status_code=status.HTTP_303_SEE_OTHER)
