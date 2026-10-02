"""Router đăng nhập, đăng xuất, trang chủ.

Chỉ làm việc HTTP: đọc form, gọi kiểm tra mật khẩu, dựng session, render template.
Không chứa logic nghiệp vụ — theo ranh giới trong docs/architecture.md.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import dang_nhap_session, dang_xuat_session, nguoi_dung_hien_tai, nguoi_dung_hien_tai_hoac_none
from app.db import get_db
from app.models.user import User
from app.security import verify_password
from app.services import users as nv
from app.services.errors import LoiNghiepVu
from app.services.login_throttle import gioi_han_dang_nhap, tao_khoa
from app.templates import templates

router = APIRouter()

# Một thông báo duy nhất cho cả hai trường hợp "không có tài khoản" và "sai mật khẩu".
# Thông báo khác nhau sẽ để lộ tài khoản nào có thật (TC-002).
LOI_DANG_NHAP = "Tên đăng nhập hoặc mật khẩu không đúng."
LOI_TAI_KHOAN_KHOA = "Tài khoản đã ngưng hoạt động. Vui lòng liên hệ quản lý."


def _thong_diep_cho(giay: int) -> str:
    cho = f"{giay} giây" if giay < 60 else f"{-(-giay // 60)} phút"
    return f"Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {cho}."


@router.get("/login", response_class=HTMLResponse)
def trang_dang_nhap(request: Request):
    return templates.TemplateResponse(request, "login.html", {"user": None})


@router.post("/login", response_class=HTMLResponse)
def xu_ly_dang_nhap(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Kiểm giới hạn TRƯỚC khi đụng CSDL hay băm mật khẩu: lượt thử trong lúc bị khóa không được
    # tốn tài nguyên, và mật khẩu đúng cũng không được qua (R-1).
    khoa = tao_khoa(request.client.host if request.client else "?", username)
    giay_cho = gioi_han_dang_nhap.con_phai_cho(khoa)
    if giay_cho > 0:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "loi": _thong_diep_cho(giay_cho), "username": username},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(giay_cho)},
        )

    user = db.scalar(select(User).where(User.username == username))

    if user is None or not verify_password(password, user.password_hash):
        gioi_han_dang_nhap.ghi_that_bai(khoa)
        return templates.TemplateResponse(
            request,
            "login.html",
            # Giữ lại tên đã gõ, KHÔNG giữ mật khẩu: máy quầy dùng chung và HTML
            # còn nằm trong bộ nhớ đệm của trình duyệt (L-07).
            {"user": None, "loi": LOI_DANG_NHAP, "username": username},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "loi": LOI_TAI_KHOAN_KHOA, "username": username},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    gioi_han_dang_nhap.xoa(khoa)
    dang_nhap_session(request, user)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def dang_xuat(
    request: Request,
    user: User | None = Depends(nguoi_dung_hien_tai_hoac_none),
    db: Session = Depends(get_db),
):
    if user is not None:
        nv.thu_hoi_phien(db, user.id)
    dang_xuat_session(request)
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
def trang_chu(request: Request, user: User = Depends(nguoi_dung_hien_tai)):
    return templates.TemplateResponse(request, "home.html", {"user": user})


# --- Tự đổi mật khẩu (M-02) --------------------------------------------------------
# Nằm ở router này chứ không ở `/users`: cả ba vai trò đều dùng được, trong khi cả router
# `/users` chặn ai không phải quản lý.


@router.get("/doi-mat-khau", response_class=HTMLResponse)
def trang_doi_mat_khau(request: Request, user: User = Depends(nguoi_dung_hien_tai)):
    return templates.TemplateResponse(request, "doi_mat_khau.html", {"user": user})


@router.post("/doi-mat-khau", response_class=HTMLResponse)
def xu_ly_doi_mat_khau(
    request: Request,
    mat_khau_cu: str = Form(""),
    mat_khau_moi: str = Form(""),
    nhap_lai: str = Form(""),
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    def bao(thong_diep: str, ma: int = status.HTTP_400_BAD_REQUEST):
        return templates.TemplateResponse(
            request, "doi_mat_khau.html", {"user": user, "loi": thong_diep}, status_code=ma
        )

    # Kiểm "nhập lại" ở router vì nó thuần là chuyện của form — service không biết gì về
    # ô nhập lại, và một mật khẩu gõ nhầm hai lần giống nhau vẫn là mật khẩu hợp lệ.
    if mat_khau_moi != nhap_lai:
        return bao("Hai ô mật khẩu mới không khớp nhau.")

    try:
        nv.doi_mat_khau(db, user.id, mat_khau_cu=mat_khau_cu, mat_khau_moi=mat_khau_moi)
    except LoiNghiepVu as loi:
        return bao(str(loi))

    # Số phiên bản vừa tăng: cookie của máy này cũng chết trừ khi cấp lại ngay.
    dang_nhap_session(request, user)
    return templates.TemplateResponse(
        request, "doi_mat_khau.html", {"user": user, "xong": True}
    )
