"""Router cổng khách: xem thú cưng, lịch hẹn, hóa đơn của chính mình (P9 chặng 4, đợt 4c).

Chỉ gọi `app.services.khach_du_lieu`: không import `app.models`, không truy vấn `db.*` trực tiếp. Phép canh trong
`tests/unit/test_architecture.py` giữ điều đó, vì một truy vấn lẻ ở đây là một lỗ IDOR không ai kiểm.
`khach` cố ý không khai báo kiểu để router khỏi phải import model.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import khach_hien_tai
from app.db import get_db
from app.services import khach_du_lieu as dl
from app.templates import templates

router = APIRouter(prefix="/khach")


@router.get("/thu-cung", response_class=HTMLResponse)
def danh_sach_thu_cung(request: Request, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "khach_thu_cung.html", {"khach": khach, "thu_cung": dl.danh_sach_thu_cung(db, khach)}
    )


@router.get("/thu-cung/{thu_cung_id}", response_class=HTMLResponse)
def chi_tiet_thu_cung(
    request: Request, thu_cung_id: int, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        request, "khach_chi_tiet_thu_cung.html", {"khach": khach, "ct": dl.chi_tiet_thu_cung(db, khach, thu_cung_id)}
    )


@router.get("/lich-hen", response_class=HTMLResponse)
def danh_sach_lich_hen(request: Request, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "khach_lich_hen.html", {"khach": khach, "lich_hen": dl.danh_sach_lich_hen(db, khach)}
    )


@router.get("/hoa-don", response_class=HTMLResponse)
def danh_sach_hoa_don(request: Request, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "khach_hoa_don.html", {"khach": khach, "hoa_don": dl.danh_sach_hoa_don(db, khach)}
    )


@router.get("/hoa-don/{hoa_don_id}", response_class=HTMLResponse)
def chi_tiet_hoa_don(
    request: Request, hoa_don_id: int, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        request, "khach_chi_tiet_hoa_don.html", {"khach": khach, "hd": dl.chi_tiet_hoa_don(db, khach, hoa_don_id)}
    )
