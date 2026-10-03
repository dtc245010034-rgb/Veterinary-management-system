"""Router màn hình lễ tân: duyệt hoặc từ chối lịch khách tự xin (P9 chặng 5).

Chỉ làm việc HTTP. Quy tắc nằm ở `app/services/scheduling.py`. Quản lý và lễ tân dùng được; nhân viên chăm sóc
không (họ không tiếp khách tại quầy). Đặt route riêng `/lich-cho-duyet` thay vì dưới `/appointments` để khỏi
vướng `/appointments/{lich_id}/...`.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services import scheduling as nv
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/lich-cho-duyet")

duoc_duyet = Depends(yeu_cau_vai_tro("manager", "receptionist"))


def _trang(request: Request, db: Session, user: User, loi: str | None = None):
    return templates.TemplateResponse(
        request,
        "lich_cho_duyet.html",
        {"user": user, "cho_duyet": nv.danh_sach_cho_duyet(db), "loi": loi},
        status_code=status.HTTP_400_BAD_REQUEST if loi else status.HTTP_200_OK,
    )


def _ve_danh_sach():
    return RedirectResponse("/lich-cho-duyet", status_code=status.HTTP_303_SEE_OTHER)


@router.get("", response_class=HTMLResponse)
def danh_sach(request: Request, user: User = duoc_duyet, db: Session = Depends(get_db)):
    return _trang(request, db, user)


@router.post("/{lich_id}/duyet", response_class=HTMLResponse)
def duyet(request: Request, lich_id: int, user: User = duoc_duyet, db: Session = Depends(get_db)):
    try:
        nv.duyet_lich_cho(db, lich_id, user.id)
    except LoiKhongTimThay:
        raise
    except LoiNghiepVu as loi:
        return _trang(request, db, user, loi=str(loi))
    return _ve_danh_sach()


@router.post("/{lich_id}/tu-choi", response_class=HTMLResponse)
def tu_choi(
    request: Request,
    lich_id: int,
    ly_do: str = Form(""),
    user: User = duoc_duyet,
    db: Session = Depends(get_db),
):
    try:
        nv.tu_choi_lich_cho(db, lich_id, ly_do, user.id)
    except LoiKhongTimThay:
        raise
    except LoiNghiepVu as loi:
        return _trang(request, db, user, loi=str(loi))
    return _ve_danh_sach()
