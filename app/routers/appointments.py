"""Router lịch hẹn — chặng 1 của P3: xem lịch và đặt lịch.

Phục vụ US-10, US-11, US-14. Chỉ làm việc HTTP; quy tắc trùng lịch nằm ở
app/services/scheduling.py.

Đổi lịch, hủy lịch và trang riêng của nhân viên chăm sóc thuộc chặng 2.
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
    return _render(request, db, user, _doc_ngay(ngay), nhan_vien_id)


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
    except nv.TrungLich as loi:
        # Kèm khung trống để lễ tân chọn ngay, không phải tự dò từng khung.
        return _render(
            request, db, user, ngay_chon, loi=str(loi),
            khung_trong=loi.khung_trong, ma=status.HTTP_400_BAD_REQUEST,
        )
    except LoiNghiepVu as loi:
        return _render(request, db, user, ngay_chon, loi=str(loi), ma=status.HTTP_400_BAD_REQUEST)

    return RedirectResponse(
        f"/appointments?ngay={ngay_chon.isoformat()}", status_code=status.HTTP_303_SEE_OTHER
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
