"""Router đăng nhập, đăng xuất, trang chủ.

Chỉ làm việc HTTP: đọc form, gọi kiểm tra mật khẩu, dựng session, render template.
Không chứa logic nghiệp vụ — theo ranh giới trong docs/architecture.md.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import dang_nhap_session, dang_xuat_session, nguoi_dung_hien_tai
from app.db import get_db
from app.models.user import User
from app.security import verify_password
from app.templates import templates

router = APIRouter()

# Một thông báo duy nhất cho cả hai trường hợp "không có tài khoản" và "sai mật khẩu".
# Thông báo khác nhau sẽ để lộ tài khoản nào có thật (TC-002).
LOI_DANG_NHAP = "Tên đăng nhập hoặc mật khẩu không đúng."
LOI_TAI_KHOAN_KHOA = "Tài khoản đã ngưng hoạt động. Vui lòng liên hệ quản lý."


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
    user = db.scalar(select(User).where(User.username == username))

    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "loi": LOI_DANG_NHAP},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "loi": LOI_TAI_KHOAN_KHOA},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    dang_nhap_session(request, user)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def dang_xuat(request: Request):
    dang_xuat_session(request)
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
def trang_chu(request: Request, user: User = Depends(nguoi_dung_hien_tai)):
    return templates.TemplateResponse(request, "home.html", {"user": user})
