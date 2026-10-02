"""Router cổng khách: đăng ký bằng email, đăng nhập, quên mật khẩu, đổi mật khẩu (P9 chặng 4, đợt 4a).

Chỉ làm việc HTTP. Mọi quy tắc nằm ở `app/services/customers.py`.

Bốn điểm cần giữ khi sửa file này:
- Phản hồi của đăng ký và quên mật khẩu **không phụ thuộc email có tồn tại hay không**.
- Liên kết trong thư dựng từ `APP_ORIGIN`, KHÔNG từ header `Host` (kẻ gửi `Host` giả sẽ khiến thư đặt lại
  mật khẩu chứa liên kết về trang của kẻ đó). Chỉ máy phát triển, nơi không có `APP_ORIGIN`, mới rơi về địa chỉ
  request; chế độ công khai không có `APP_ORIGIN` thì ứng dụng không khởi động (xem `lifespan`).
- `GET` trên liên kết trong thư chỉ đọc; chỉ `POST` mới tiêu thụ token (trình quét liên kết của hộp thư
  `GET` mọi link trước người nhận).
- Đăng ký, quên mật khẩu giới hạn theo IP bằng cùng bộ đếm với đăng nhập nhân viên.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import (
    dang_nhap_khach_session,
    dang_xuat_khach_session,
    khach_hien_tai,
    khach_hien_tai_hoac_none,
)
from app.config import settings
from app.db import get_db
from app.mail.provider import GuiMail
from app.mail.service import lay_mailer
from app.models.customer import Customer
from app.services import customers as nv
from app.services import email_tokens
from app.services.errors import LoiNghiepVu
from app.services.login_throttle import gioi_han_dang_nhap, tao_khoa
from app.templates import templates

router = APIRouter(prefix="/khach")

LOI_KHONG_KHOP = "Hai ô mật khẩu không khớp nhau."


def _goc_duong_dan(request: Request) -> str:
    return (settings.app_origin or str(request.base_url)).rstrip("/")


def _ip(request: Request) -> str:
    return request.client.host if request.client else "?"


def _thong_diep_cho(giay: int) -> str:
    cho = f"{giay} giây" if giay < 60 else f"{-(-giay // 60)} phút"
    return f"Bạn thao tác quá nhiều lần. Vui lòng thử lại sau {cho}."


def _qua_nhieu(request: Request, mau: str, giay: int, **ngu_canh):
    return templates.TemplateResponse(
        request,
        mau,
        {"loi": _thong_diep_cho(giay), **ngu_canh},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(giay)},
    )


def _trang(request: Request, mau: str, ma: int = status.HTTP_200_OK, **ngu_canh):
    return templates.TemplateResponse(request, mau, ngu_canh, status_code=ma)


def _lien_ket_hong(request: Request):
    return _trang(request, "khach_lien_ket_hong.html", status.HTTP_400_BAD_REQUEST)


# --- Đăng ký ------------------------------------------------------------------------


@router.get("/dang-ky", response_class=HTMLResponse)
def trang_dang_ky(request: Request):
    return _trang(request, "khach_dang_ky.html")


@router.post("/dang-ky", response_class=HTMLResponse)
def xu_ly_dang_ky(
    request: Request,
    email: str = Form(""),
    db: Session = Depends(get_db),
    mailer: GuiMail = Depends(lay_mailer),
):
    khoa = tao_khoa(_ip(request), "khach:dang-ky")
    giay_cho = gioi_han_dang_nhap.con_phai_cho(khoa)
    if giay_cho > 0:
        return _qua_nhieu(request, "khach_dang_ky.html", giay_cho, email=email)
    # Mỗi lượt đều tính: lượt đúng cũng tốn một thư gửi đi, và bộ đếm là thứ chặn kẻ dùng form này để làm
    # loa phát thư rác tới địa chỉ người khác.
    gioi_han_dang_nhap.ghi_that_bai(khoa)

    try:
        nv.yeu_cau_dang_ky(db, mailer, email, _goc_duong_dan(request))
    except LoiNghiepVu as loi:
        return _trang(request, "khach_dang_ky.html", status.HTTP_400_BAD_REQUEST, loi=str(loi), email=email)
    return _trang(request, "khach_da_gui_thu.html", hanh_dong="đăng ký")


@router.get("/dang-ky/{token}", response_class=HTMLResponse)
def trang_dat_mat_khau(request: Request, token: str, db: Session = Depends(get_db)):
    if not email_tokens.con_hieu_luc(db, token, "verify_email"):
        return _lien_ket_hong(request)
    return _trang(request, "khach_dat_mat_khau.html", token=token)


@router.post("/dang-ky/{token}", response_class=HTMLResponse)
def xu_ly_dat_mat_khau(
    request: Request,
    token: str,
    full_name: str = Form(""),
    mat_khau: str = Form(""),
    nhap_lai: str = Form(""),
    db: Session = Depends(get_db),
):
    def bao(thong_diep: str):
        if not email_tokens.con_hieu_luc(db, token, "verify_email"):
            return _lien_ket_hong(request)
        return _trang(
            request,
            "khach_dat_mat_khau.html",
            status.HTTP_400_BAD_REQUEST,
            token=token,
            loi=thong_diep,
            full_name=full_name,
        )

    if mat_khau != nhap_lai:
        return bao(LOI_KHONG_KHOP)
    try:
        khach = nv.hoan_tat_dang_ky(db, token, full_name, mat_khau)
    except LoiNghiepVu as loi:
        return bao(str(loi))

    dang_nhap_khach_session(request, khach)
    return RedirectResponse("/khach", status_code=status.HTTP_303_SEE_OTHER)


# --- Đăng nhập, đăng xuất ------------------------------------------------------------


@router.get("/dang-nhap", response_class=HTMLResponse)
def trang_dang_nhap(request: Request, da_dat_lai: int = 0):
    return _trang(request, "khach_dang_nhap.html", da_dat_lai=bool(da_dat_lai))


@router.post("/dang-nhap", response_class=HTMLResponse)
def xu_ly_dang_nhap(
    request: Request,
    email: str = Form(""),
    mat_khau: str = Form(""),
    db: Session = Depends(get_db),
):
    # Khóa theo (IP, email) như đăng nhập nhân viên; tiền tố tách khỏi tên đăng nhập của nhân viên.
    khoa = tao_khoa(_ip(request), "khach:" + email)
    giay_cho = gioi_han_dang_nhap.con_phai_cho(khoa)
    if giay_cho > 0:
        return _qua_nhieu(request, "khach_dang_nhap.html", giay_cho, email=email)

    try:
        khach = nv.xac_thuc(db, email, mat_khau)
    except LoiNghiepVu as loi:
        if str(loi) == nv.LOI_DANG_NHAP:
            gioi_han_dang_nhap.ghi_that_bai(khoa)
        # Giữ email đã gõ, KHÔNG giữ mật khẩu (xem L-07 ở đăng nhập nhân viên).
        return _trang(request, "khach_dang_nhap.html", status.HTTP_401_UNAUTHORIZED, loi=str(loi), email=email)

    gioi_han_dang_nhap.xoa(khoa)
    dang_nhap_khach_session(request, khach)
    return RedirectResponse("/khach", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dang-xuat")
def dang_xuat(
    request: Request,
    khach: Customer | None = Depends(khach_hien_tai_hoac_none),
    db: Session = Depends(get_db),
):
    if khach is not None:
        nv.thu_hoi_phien(db, khach.id)
    dang_xuat_khach_session(request)
    return RedirectResponse("/khach/dang-nhap", status_code=status.HTTP_303_SEE_OTHER)


# --- Quên mật khẩu ---------------------------------------------------------------------


@router.get("/quen-mat-khau", response_class=HTMLResponse)
def trang_quen_mat_khau(request: Request):
    return _trang(request, "khach_quen_mat_khau.html")


@router.post("/quen-mat-khau", response_class=HTMLResponse)
def xu_ly_quen_mat_khau(
    request: Request,
    email: str = Form(""),
    db: Session = Depends(get_db),
    mailer: GuiMail = Depends(lay_mailer),
):
    khoa = tao_khoa(_ip(request), "khach:quen-mat-khau")
    giay_cho = gioi_han_dang_nhap.con_phai_cho(khoa)
    if giay_cho > 0:
        return _qua_nhieu(request, "khach_quen_mat_khau.html", giay_cho, email=email)
    gioi_han_dang_nhap.ghi_that_bai(khoa)

    try:
        nv.yeu_cau_dat_lai(db, mailer, email, _goc_duong_dan(request))
    except LoiNghiepVu as loi:
        return _trang(request, "khach_quen_mat_khau.html", status.HTTP_400_BAD_REQUEST, loi=str(loi), email=email)
    return _trang(request, "khach_da_gui_thu.html", hanh_dong="đặt lại mật khẩu")


@router.get("/dat-lai/{token}", response_class=HTMLResponse)
def trang_dat_lai(request: Request, token: str, db: Session = Depends(get_db)):
    if not email_tokens.con_hieu_luc(db, token, "reset_password"):
        return _lien_ket_hong(request)
    return _trang(request, "khach_dat_lai.html", token=token)


@router.post("/dat-lai/{token}", response_class=HTMLResponse)
def xu_ly_dat_lai(
    request: Request,
    token: str,
    mat_khau: str = Form(""),
    nhap_lai: str = Form(""),
    db: Session = Depends(get_db),
):
    def bao(thong_diep: str):
        if not email_tokens.con_hieu_luc(db, token, "reset_password"):
            return _lien_ket_hong(request)
        return _trang(request, "khach_dat_lai.html", status.HTTP_400_BAD_REQUEST, token=token, loi=thong_diep)

    if mat_khau != nhap_lai:
        return bao(LOI_KHONG_KHOP)
    try:
        nv.dat_lai_mat_khau(db, token, mat_khau)
    except LoiNghiepVu as loi:
        return bao(str(loi))
    # Không tự đăng nhập: thư đặt lại là bằng chứng sở hữu hộp thư, không phải bằng chứng người đang ngồi máy này.
    return RedirectResponse("/khach/dang-nhap?da_dat_lai=1", status_code=status.HTTP_303_SEE_OTHER)


# --- Sau khi đăng nhập ---------------------------------------------------------------------


@router.get("", response_class=HTMLResponse)
def trang_chu_khach(request: Request, khach: Customer = Depends(khach_hien_tai)):
    return _trang(request, "khach_trang_chu.html", khach=khach)


@router.get("/doi-mat-khau", response_class=HTMLResponse)
def trang_doi_mat_khau(request: Request, khach: Customer = Depends(khach_hien_tai)):
    return _trang(request, "khach_doi_mat_khau.html", khach=khach)


@router.post("/doi-mat-khau", response_class=HTMLResponse)
def xu_ly_doi_mat_khau(
    request: Request,
    mat_khau_cu: str = Form(""),
    mat_khau_moi: str = Form(""),
    nhap_lai: str = Form(""),
    khach: Customer = Depends(khach_hien_tai),
    db: Session = Depends(get_db),
):
    def bao(thong_diep: str):
        return _trang(request, "khach_doi_mat_khau.html", status.HTTP_400_BAD_REQUEST, khach=khach, loi=thong_diep)

    if mat_khau_moi != nhap_lai:
        return bao(LOI_KHONG_KHOP)
    try:
        nv.doi_mat_khau(db, khach, mat_khau_cu, mat_khau_moi)
    except LoiNghiepVu as loi:
        return bao(str(loi))

    # Số phiên bản vừa tăng: cookie của máy này cũng chết trừ khi cấp lại ngay.
    dang_nhap_khach_session(request, khach)
    return _trang(request, "khach_doi_mat_khau.html", khach=khach, xong=True)
