"""Router cổng khách: xin nối tài khoản với hồ sơ tại cửa hàng (P9 chặng 4, đợt 4b).

Khách chỉ gửi số điện thoại và ghi chú làm gợi ý. Phản hồi không cho biết số đó có phải chủ nuôi hay không.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import khach_hien_tai
from app.db import get_db
from app.models.customer import Customer
from app.services import link_requests as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/khach")


@router.get("/lien-ket", response_class=HTMLResponse)
def trang_lien_ket(request: Request, khach: Customer = Depends(khach_hien_tai), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "khach_lien_ket.html", {"khach": khach, "yeu_cau": nv.yeu_cau_cua_khach(db, khach)}
    )


@router.post("/lien-ket", response_class=HTMLResponse)
def gui_yeu_cau(
    request: Request,
    so_dien_thoai: str = Form(""),
    ghi_chu: str = Form(""),
    khach: Customer = Depends(khach_hien_tai),
    db: Session = Depends(get_db),
):
    try:
        nv.gui_yeu_cau(db, khach, so_dien_thoai, ghi_chu)
    except LoiNghiepVu as loi:
        return templates.TemplateResponse(
            request,
            "khach_lien_ket.html",
            {
                "khach": khach,
                "yeu_cau": nv.yeu_cau_cua_khach(db, khach),
                "loi": str(loi),
                "so_dien_thoai": so_dien_thoai,
                "ghi_chu": ghi_chu,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return templates.TemplateResponse(
        request, "khach_lien_ket.html", {"khach": khach, "yeu_cau": nv.yeu_cau_cua_khach(db, khach), "vua_gui": True}
    )
