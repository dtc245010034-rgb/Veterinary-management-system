"""Router tiêm phòng: ghi mũi tiêm, danh sách đến hạn nhắc.

Phục vụ US-17, US-18. Chỉ làm việc HTTP; quy tắc nghiệp vụ nằm ở
app/services/vaccinations.py.

Không có phép kiểm vai trò nào ở đây: bảng phân quyền US-02 cho cả ba vai trò toàn quyền
ở mục tiêm phòng.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai
from app.db import get_db
from app.models.user import User
from app.routers import pets as trang_pets
from app.services import clock
from app.services import vaccinations as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter()


@router.get("/vaccinations", response_class=HTMLResponse)
def trang_den_han(
    request: Request,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request,
        "vaccinations.html",
        {
            "user": user,
            "danh_sach": nv.den_han(db),
            "so_ngay": nv.SO_NGAY_NHAC,
            "hom_nay": clock.now().date(),
        },
    )


@router.post("/pets/{thu_cung_id}/vaccinations", response_class=HTMLResponse)
def them_mui_tiem(
    request: Request,
    thu_cung_id: int,
    ten_vac_xin: str = Form(""),
    so_mui: str = Form(""),
    ngay_tiem: str = Form(""),
    han_nhac: str = Form(""),
    ghi_chu: str = Form(""),
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    try:
        nv.ghi_mui_tiem(
            db,
            thu_cung_id,
            ten_vac_xin=ten_vac_xin,
            ngay_tiem=_doc_ngay(ngay_tiem, "Ngày tiêm"),
            han_nhac=_doc_ngay(han_nhac, "Ngày hạn nhắc lại", bat_buoc=False),
            so_mui=_doc_so_mui(so_mui),
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        # Dựng lại đúng trang thú cưng kèm thông báo, không đẩy sang trang lỗi: người
        # dùng cần thấy lại form và những gì đã có để sửa.
        return trang_pets.trang_thu_cung(
            request, thu_cung_id, user, db, loi=str(loi), ma=status.HTTP_400_BAD_REQUEST
        )

    return RedirectResponse(f"/pets/{thu_cung_id}", status_code=status.HTTP_303_SEE_OTHER)


def _doc_ngay(chuoi: str, ten_truong: str, bat_buoc: bool = True) -> date | None:
    chuoi = (chuoi or "").strip()
    if not chuoi:
        if bat_buoc:
            raise LoiNghiepVu(f"{ten_truong} không được để trống.")
        return None
    try:
        return date.fromisoformat(chuoi)
    except ValueError:
        raise LoiNghiepVu(f"{ten_truong} không đúng định dạng.")


def _doc_so_mui(chuoi: str) -> int | None:
    """Để trống là hợp lệ — không phải ai cũng biết đây là mũi thứ mấy."""
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None
    try:
        return int(chuoi)
    except ValueError:
        raise LoiNghiepVu("Mũi thứ mấy phải là số.")
