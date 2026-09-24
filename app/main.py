"""Khởi tạo ứng dụng FastAPI.

Đăng ký middleware session, router, và hai trình xử lý lỗi để người dùng thấy trang
tiếng Việt thay vì JSON thô.
"""

from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as LoiHTTPStarlette
from starlette.middleware.sessions import SessionMiddleware

from app.auth import ChuaDangNhap
from app.config import SECRET_KEY_MAC_DINH, settings
import app.models  # noqa: F401 — đăng ký mọi bảng trước create_all
from app.db import Base, engine
from app.routers import ai as ai_router
from app.routers import appointments as appointments_router
from app.routers import auth as auth_router
from app.routers import care_records as care_records_router
from app.routers import invoices as invoices_router
from app.routers import owners as owners_router
from app.routers import pets as pets_router
from app.routers import services as services_router
from app.routers import stats as stats_router
from app.routers import users as users_router
from app.routers import vaccinations as vaccinations_router
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Tạo bảng nếu chưa có. Đủ dùng cho dự án môn học, không cần Alembic.

    Kiểm SECRET_KEY trước tiên: khóa mặc định nằm công khai trong repo, chạy với nó thì
    ai cũng tự ký được cookie phiên quản lý. Dừng hẳn còn hơn chạy âm thầm không an toàn.
    """
    if settings.secret_key == SECRET_KEY_MAC_DINH:
        raise RuntimeError(
            "SECRET_KEY vẫn là chuỗi mặc định trong app/config.py. Sao chép .env.example "
            "thành .env và đặt SECRET_KEY là một chuỗi ngẫu nhiên riêng trước khi chạy."
        )
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Quản lý thú cưng và lịch chăm sóc", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def khong_luu_dem(request: Request, call_next):
    """Mọi trang của ứng dụng đều `no-store` — L-02.

    Rà 19/09: đăng xuất rồi bấm Back vẫn thấy tên nhân viên và danh sách khách kèm số
    điện thoại, vì trình duyệt dựng lại trang từ bộ nhớ đệm mà không hỏi máy chủ. Máy ở
    quầy lễ tân là máy dùng chung, và phiên sống 14 ngày.

    Chừa `/static`: file CSS không chứa dữ liệu của ai, tắt bộ nhớ đệm của nó chỉ tốn
    băng thông. Đây cũng là lý do phép canh có một ca đối chứng riêng cho `/static`.
    """
    phan_hoi = await call_next(request)
    if not request.url.path.startswith("/static"):
        phan_hoi.headers["Cache-Control"] = "no-store, must-revalidate"
    return phan_hoi

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(owners_router.router)
app.include_router(services_router.router)
app.include_router(appointments_router.router)
app.include_router(care_records_router.router)
app.include_router(pets_router.router)
app.include_router(vaccinations_router.router)
app.include_router(invoices_router.router)
app.include_router(stats_router.router)
app.include_router(ai_router.router)


@app.exception_handler(ChuaDangNhap)
async def xu_ly_chua_dang_nhap(request: Request, exc: ChuaDangNhap):
    """TC-004: chưa đăng nhập thì đưa về trang đăng nhập, không trả lỗi thô."""
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


# Starlette điền `detail` bằng cụm tiếng Anh mặc định của mã lỗi ("Not Found") khi URL
# không khớp route nào — và người dùng từng gặp đúng câu đó qua link Thống kê trong menu
# quản lý, trước khi P6 dựng trang. CLAUDE.md mục 5: chữ hiển thị cho người dùng phải là tiếng Việt. Chỉ thay khi
# `detail` đúng bằng cụm mặc định; thông điệp do dự án tự viết thì giữ nguyên.
MO_TA_LOI_MAC_DINH = {
    status.HTTP_403_FORBIDDEN: "Bạn không có quyền truy cập chức năng này.",
    status.HTTP_404_NOT_FOUND: "Đường dẫn này không tồn tại, hoặc mục bạn tìm đã bị xóa.",
}


# Đăng ký trên lớp của Starlette chứ KHÔNG phải fastapi.HTTPException: URL không khớp
# route nào ném lớp cha, mà handler đăng ký ở lớp con không bắt được lớp cha. Vì vậy
# `/stats` — một link có sẵn trong menu quản lý — từng trả `{"detail":"Not Found"}` thô.
# fastapi.HTTPException kế thừa lớp này nên một handler bắt được cả hai.
@app.exception_handler(LoiHTTPStarlette)
async def xu_ly_loi_http(request: Request, exc: LoiHTTPStarlette):
    """403 và 404 hiển thị thành trang có bố cục, không phải JSON.

    TC-007 yêu cầu người dùng gõ thẳng URL bị chặn phải thấy trang báo lỗi tử tế.
    """
    if exc.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND):
        thong_diep = exc.detail
        if thong_diep == HTTPStatus(exc.status_code).phrase:
            thong_diep = MO_TA_LOI_MAC_DINH[exc.status_code]

        return templates.TemplateResponse(
            request,
            "error.html",
            {"ma_loi": exc.status_code, "thong_diep": thong_diep},
            status_code=exc.status_code,
        )

    return HTMLResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(LoiNghiepVu)
async def xu_ly_loi_nghiep_vu_lot_khoi_router(request: Request, exc: LoiNghiepVu):
    """Lưới an toàn cho router quên `try/except`: trang lỗi tiếng Việt thay vì 500.

    Lỗi H-03 (rà 19/09): chín đường dẫn trả "Internal Server Error" khi bản ghi đã bị xóa.
    Vá từng route thì route viết sau lại quên — bắt một lần ở đây cho cả lớp lỗi.
    """
    ma = status.HTTP_404_NOT_FOUND if isinstance(exc, LoiKhongTimThay) else status.HTTP_400_BAD_REQUEST
    return templates.TemplateResponse(
        request, "error.html", {"ma_loi": ma, "thong_diep": str(exc)}, status_code=ma
    )
