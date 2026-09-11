"""Router dịch vụ, bảng giá và gói dịch vụ.

Phục vụ US-07, US-08, US-09. Chỉ làm việc HTTP; nghiệp vụ nằm ở app/services/catalog.py.

Phân quyền theo bảng US-02: quản lý toàn quyền, lễ tân và nhân viên chăm sóc chỉ xem.
"""

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services import catalog as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/services")

chi_quan_ly = Depends(yeu_cau_vai_tro("manager"))


def _render(request: Request, db: Session, user: User, loi: str | None = None, ma: int = 200):
    return templates.TemplateResponse(
        request,
        "services.html",
        {
            "user": user,
            "dich_vu": nv.danh_sach_dich_vu(db),
            "dang_ban": nv.danh_sach_dang_ban(db),
            "goi": nv.danh_sach_goi(db),
            "loi": loi,
        },
        status_code=ma,
    )


@router.get("", response_class=HTMLResponse)
def trang_dich_vu(
    request: Request,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    return _render(request, db, user)


@router.post("", response_class=HTMLResponse)
def them_dich_vu(
    request: Request,
    ma: str = Form(""),
    ten: str = Form(""),
    gia: str = Form(""),
    thoi_luong_phut: str = Form(""),
    mo_ta: str = Form(""),
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.tao_dich_vu(
            db,
            ma=ma,
            ten=ten,
            gia=_doc_tien(gia),
            thoi_luong_phut=_doc_nguyen(thoi_luong_phut, "Thời lượng"),
            mo_ta=mo_ta,
        )
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{dich_vu_id}/sua", response_class=HTMLResponse)
def sua_dich_vu(
    request: Request,
    dich_vu_id: int,
    ten: str = Form(""),
    gia: str = Form(""),
    thoi_luong_phut: str = Form(""),
    mo_ta: str = Form(""),
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    try:
        nv.sua_dich_vu(
            db,
            dich_vu_id,
            ten=ten,
            gia=_doc_tien(gia),
            thoi_luong_phut=_doc_nguyen(thoi_luong_phut, "Thời lượng"),
            mo_ta=mo_ta,
        )
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{dich_vu_id}/ngung-ban")
def ngung_ban(dich_vu_id: int, user: User = chi_quan_ly, db: Session = Depends(get_db)):
    nv.ngung_ban(db, dich_vu_id)
    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{dich_vu_id}/ban-lai")
def ban_lai(dich_vu_id: int, user: User = chi_quan_ly, db: Session = Depends(get_db)):
    nv.ban_lai(db, dich_vu_id)
    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/goi", response_class=HTMLResponse)
async def tao_goi(
    request: Request,
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    """Đọc form thủ công vì số dòng thành phần thay đổi theo số dịch vụ đang bán.

    Form gửi hai danh sách song song `dich_vu_id[]` và `so_luong[]`; chỉ dòng nào có số
    lượt lớn hơn 0 mới được tính là đã chọn.
    """
    form = await request.form()
    danh_sach_ma = form.getlist("dich_vu_id")
    danh_sach_so = form.getlist("so_luong")

    thanh_phan: dict[int, int] = {}
    for ma_chuoi, so_chuoi in zip(danh_sach_ma, danh_sach_so):
        so = (so_chuoi or "").strip()
        # isdecimal() chứ không phải isdigit(): "²".isdigit() là True mà int("²") ném
        # ValueError — từng thành lỗi 500 (rà 11/09). isdecimal() khớp đúng thứ int() đọc được.
        if so and so.isdecimal() and int(so) > 0:
            thanh_phan[int(ma_chuoi)] = int(so)

    try:
        nv.tao_goi(
            db,
            ten=form.get("ten", ""),
            gia=_doc_tien(form.get("gia", "")),
            thanh_phan=thanh_phan,
            mo_ta=form.get("mo_ta", ""),
        )
    except LoiNghiepVu as loi:
        return _render(request, db, user, str(loi), status.HTTP_400_BAD_REQUEST)

    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/goi/{goi_id}/ngung-ban")
def ngung_ban_goi(goi_id: int, user: User = chi_quan_ly, db: Session = Depends(get_db)):
    nv.ngung_ban_goi(db, goi_id)
    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/goi/{goi_id}/ban-lai")
def ban_lai_goi(goi_id: int, user: User = chi_quan_ly, db: Session = Depends(get_db)):
    nv.ban_lai_goi(db, goi_id)
    return RedirectResponse("/services", status_code=status.HTTP_303_SEE_OTHER)


def _doc_tien(chuoi: str) -> Decimal:
    """Đọc tiền thành Decimal, không qua float.

    float(chuoi) rồi Decimal(float) sẽ kéo theo sai số nhị phân ngay từ bước đầu —
    Decimal(0.1) cho 0.1000000000000000055511151231257827.
    """
    chuoi = (chuoi or "").strip().replace(",", "").replace(".", "")
    if not chuoi:
        raise LoiNghiepVu("Giá không được để trống.")
    try:
        gia = Decimal(chuoi)
    except InvalidOperation:
        raise LoiNghiepVu("Giá phải là một số.")
    # Decimal nhận cả "NaN" và "Infinity" — cả hai từng thành lỗi 500 (rà 11/09).
    if not gia.is_finite():
        raise LoiNghiepVu("Giá phải là một số.")
    return gia


def _doc_nguyen(chuoi: str, ten_truong: str) -> int:
    chuoi = (chuoi or "").strip()
    if not chuoi:
        raise LoiNghiepVu(f"{ten_truong} không được để trống.")
    try:
        return int(chuoi)
    except ValueError:
        raise LoiNghiepVu(f"{ten_truong} phải là một số nguyên.")
