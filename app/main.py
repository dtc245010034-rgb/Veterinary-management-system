"""Khởi tạo ứng dụng FastAPI.

Đăng ký middleware session, router, và hai trình xử lý lỗi để người dùng thấy trang
tiếng Việt thay vì JSON thô.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth import ChuaDangNhap
from app.config import settings
import app.models  # noqa: F401 — đăng ký mọi bảng trước create_all
from app.db import Base, engine
from app.routers import auth as auth_router
from app.routers import owners as owners_router
from app.routers import users as users_router
from app.templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Tạo bảng nếu chưa có. Đủ dùng cho dự án môn học, không cần Alembic."""
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Quản lý thú cưng và lịch chăm sóc", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(owners_router.router)


@app.exception_handler(ChuaDangNhap)
async def xu_ly_chua_dang_nhap(request: Request, exc: ChuaDangNhap):
    """TC-004: chưa đăng nhập thì đưa về trang đăng nhập, không trả lỗi thô."""
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@app.exception_handler(HTTPException)
async def xu_ly_loi_http(request: Request, exc: HTTPException):
    """403 và 404 hiển thị thành trang có bố cục, không phải JSON.

    TC-007 yêu cầu người dùng gõ thẳng URL bị chặn phải thấy trang báo lỗi tử tế.
    """
    if exc.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND):
        return templates.TemplateResponse(
            request,
            "error.html",
            {"ma_loi": exc.status_code, "thong_diep": exc.detail},
            status_code=exc.status_code,
        )

    return HTMLResponse(str(exc.detail), status_code=exc.status_code)
