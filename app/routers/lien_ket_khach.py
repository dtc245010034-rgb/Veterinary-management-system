"""Router màn hình lễ tân: duyệt yêu cầu nối tài khoản khách với hồ sơ chủ nuôi (P9 chặng 4, đợt 4b).

Chỉ làm việc HTTP. Quy tắc nằm ở `app/services/link_requests.py`. Quản lý và lễ tân dùng được;
nhân viên chăm sóc không (họ không tiếp khách tại quầy).
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services import link_requests as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/lien-ket-khach")

duoc_duyet = Depends(yeu_cau_vai_tro("manager", "receptionist"))


def _trang(request: Request, db: Session, user: User, loi: str | None = None):
    return templates.TemplateResponse(
        request,
        "lien_ket_khach.html",
        {
            "user": user,
            "cho_duyet": nv.danh_sach_cho_duyet(db),
            "da_lien_ket": nv.danh_sach_da_lien_ket(db),
            "loi": loi,
        },
        status_code=status.HTTP_400_BAD_REQUEST if loi else status.HTTP_200_OK,
    )


def _ve_danh_sach():
    return RedirectResponse("/lien-ket-khach", status_code=status.HTTP_303_SEE_OTHER)


@router.get("", response_class=HTMLResponse)
def danh_sach(request: Request, user: User = duoc_duyet, db: Session = Depends(get_db)):
    return _trang(request, db, user)


@router.post("/{yeu_cau_id}/duyet", response_class=HTMLResponse)
def duyet(
    request: Request,
    yeu_cau_id: int,
    ung_vien: str = Form(""),
    owner_id_khac: str = Form(""),
    user: User = duoc_duyet,
    db: Session = Depends(get_db),
):
    # Ô số khác chỉ dùng khi lễ tân không chọn ứng viên nào: số khách nhập chỉ là gợi ý, hồ sơ đúng
    # có thể mang số khác (đổi số, số người nhà).
    chon = (ung_vien or owner_id_khac).strip()
    if not chon.isdigit():
        return _trang(request, db, user, loi="Hãy chọn một hồ sơ chủ nuôi, hoặc nhập mã hồ sơ.")
    try:
        nv.duyet(db, yeu_cau_id, int(chon), user)
    except LoiNghiepVu as loi:
        return _trang(request, db, user, loi=str(loi))
    return _ve_danh_sach()


@router.post("/{yeu_cau_id}/tu-choi", response_class=HTMLResponse)
def tu_choi(
    request: Request,
    yeu_cau_id: int,
    ly_do: str = Form(""),
    user: User = duoc_duyet,
    db: Session = Depends(get_db),
):
    try:
        nv.tu_choi(db, yeu_cau_id, ly_do, user)
    except LoiNghiepVu as loi:
        return _trang(request, db, user, loi=str(loi))
    return _ve_danh_sach()


@router.post("/tai-khoan/{khach_id}/go", response_class=HTMLResponse)
def go_lien_ket(
    request: Request,
    khach_id: int,
    user: User = duoc_duyet,
    db: Session = Depends(get_db),
):
    try:
        nv.go_lien_ket(db, khach_id)
    except LoiNghiepVu as loi:
        return _trang(request, db, user, loi=str(loi))
    return _ve_danh_sach()
