"""Router lịch hẹn: xem, đặt, đổi, hủy.

Phục vụ US-10 → US-14. Chỉ làm việc HTTP; quy tắc trùng lịch nằm ở
app/services/scheduling.py.
"""

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.user import User
from app.services import catalog, clock
from app.services import scheduling as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/appointments")

duoc_dat_lich = Depends(yeu_cau_vai_tro("manager", "receptionist"))


def _render(
    request: Request,
    db: Session,
    user: User,
    ngay: date,
    nhan_vien_id: int | None = None,
    loi: str | None = None,
    khung_trong: list[datetime] | None = None,
    ma: int = 200,
    chi_cua_toi: bool = False,
):
    return templates.TemplateResponse(
        request,
        "appointments.html",
        {
            "user": user,
            "ngay": ngay,
            "nhan_vien_id": nhan_vien_id,
            "danh_sach": nv.lich_theo_ngay(db, ngay, nhan_vien_id),
            "thu_cung": _danh_sach_thu_cung(db),
            "dich_vu": catalog.danh_sach_dang_ban(db),
            "nhan_vien": _danh_sach_nhan_vien(db),
            "loi": loi,
            "khung_trong": khung_trong or [],
            "chi_cua_toi": chi_cua_toi,
            "duong_dan": "/appointments/cua-toi" if chi_cua_toi else "/appointments",
        },
        status_code=ma,
    )


def _danh_sach_thu_cung(db: Session) -> list[Pet]:
    return list(db.scalars(select(Pet).join(Owner).order_by(Owner.full_name, Pet.name)))


def _danh_sach_nhan_vien(db: Session) -> list[User]:
    """Chỉ nhân viên chăm sóc còn hoạt động mới được phân lịch."""
    return list(
        db.scalars(
            select(User)
            .where(User.role == "caretaker", User.is_active)
            .order_by(User.full_name)
        )
    )


@router.get("", response_class=HTMLResponse)
def trang_lich(
    request: Request,
    ngay: str = "",
    nhan_vien_id: int | None = None,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    ngay_chon = _doc_ngay(ngay)

    # Chặn đường vòng chứ không chỉ ẩn link trong menu: gõ thẳng /appointments cũng
    # chỉ thấy lịch của chính mình (TC-009, TC-050).
    if user.role == "caretaker":
        return RedirectResponse(
            f"/appointments/cua-toi?ngay={ngay_chon.isoformat()}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return _render(request, db, user, ngay_chon, nhan_vien_id)


@router.get("/cua-toi", response_class=HTMLResponse)
def lich_cua_toi(
    request: Request,
    ngay: str = "",
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    """Lịch được phân cho chính người đang đăng nhập — US-14."""
    return _render(request, db, user, _doc_ngay(ngay), nhan_vien_id=user.id, chi_cua_toi=True)


@router.post("", response_class=HTMLResponse)
def dat_lich(
    request: Request,
    thu_cung_id: int = Form(...),
    dich_vu_id: int = Form(...),
    nhan_vien_id: int = Form(...),
    ngay: str = Form(""),
    gio: str = Form(""),
    ghi_chu: str = Form(""),
    user: User = duoc_dat_lich,
    db: Session = Depends(get_db),
):
    ngay_chon = _doc_ngay(ngay)

    try:
        nv.dat_lich(
            db,
            thu_cung_id=thu_cung_id,
            dich_vu_id=dich_vu_id,
            nhan_vien_id=nhan_vien_id,
            bat_dau=datetime.combine(ngay_chon, _doc_gio(gio)),
            nguoi_tao_id=user.id,
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        return _bao_loi(request, db, user, ngay_chon, loi)

    return _ve_lich(ngay_chon)


@router.post("/{lich_id}/doi", response_class=HTMLResponse)
def doi_lich(
    request: Request,
    lich_id: int,
    ngay: str = Form(""),
    gio: str = Form(""),
    nhan_vien_id: int | None = Form(None),
    user: User = duoc_dat_lich,
    db: Session = Depends(get_db),
):
    ngay_chon = _doc_ngay(ngay)

    try:
        nv.doi_lich(
            db,
            lich_id,
            bat_dau=datetime.combine(ngay_chon, _doc_gio(gio)),
            nhan_vien_id=nhan_vien_id,
        )
    except LoiNghiepVu as loi:
        return _bao_loi(request, db, user, ngay_chon, loi)

    return _ve_lich(ngay_chon)


@router.post("/{lich_id}/huy", response_class=HTMLResponse)
def huy_lich(
    request: Request,
    lich_id: int,
    ngay: str = Form(""),
    ly_do: str = Form(""),
    user: User = duoc_dat_lich,
    db: Session = Depends(get_db),
):
    ngay_chon = _doc_ngay(ngay)

    try:
        nv.huy_lich(db, lich_id, ly_do)
    except LoiNghiepVu as loi:
        return _bao_loi(request, db, user, ngay_chon, loi)

    return _ve_lich(ngay_chon)


def _bao_loi(request: Request, db: Session, user: User, ngay: date, loi: LoiNghiepVu):
    """TrungLich mang theo khung trống để lễ tân chọn ngay, không phải tự dò từng khung."""
    return _render(
        request, db, user, ngay,
        loi=str(loi),
        khung_trong=getattr(loi, "khung_trong", None),
        ma=status.HTTP_400_BAD_REQUEST,
    )


def _ve_lich(ngay: date) -> RedirectResponse:
    return RedirectResponse(
        f"/appointments?ngay={ngay.isoformat()}", status_code=status.HTTP_303_SEE_OTHER
    )


def _doc_ngay(chuoi: str) -> date:
    """Không truyền ngày thì mở lịch hôm nay, không phải trang trống."""
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return clock.now().date()
    try:
        return date.fromisoformat(chuoi)
    except ValueError:
        return clock.now().date()


def _doc_gio(chuoi: str) -> time:
    chuoi = (chuoi or "").strip()
    if not chuoi:
        raise LoiNghiepVu("Giờ bắt đầu không được để trống.")
    try:
        return time.fromisoformat(chuoi)
    except ValueError:
        raise LoiNghiepVu("Giờ bắt đầu không đúng định dạng.")
