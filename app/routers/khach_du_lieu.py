"""Router cổng khách: xem thú cưng, lịch hẹn, hóa đơn của chính mình (P9 chặng 4, đợt 4c).

Chỉ gọi `app.services.khach_du_lieu`: không import `app.models`, không truy vấn `db.*` trực tiếp. Phép canh trong
`tests/unit/test_architecture.py` giữ điều đó, vì một truy vấn lẻ ở đây là một lỗ IDOR không ai kiểm.
`khach` cố ý không khai báo kiểu để router khỏi phải import model.
"""

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import khach_hien_tai
from app.db import get_db
from app.services import khach_du_lieu as dl
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
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


def _trang_dat_lich(request: Request, db: Session, khach, loi: str | None = None, cu: dict | None = None):
    return templates.TemplateResponse(
        request,
        "khach_dat_lich.html",
        {"khach": khach, "lc": dl.lua_chon_dat_lich(db, khach), "loi": loi, "cu": cu or {}},
        status_code=status.HTTP_400_BAD_REQUEST if loi else status.HTTP_200_OK,
    )


def _doc_ngay_gio(ngay: str, gio: str) -> datetime:
    try:
        return datetime.combine(date.fromisoformat(ngay.strip()), time.fromisoformat(gio.strip()))
    except ValueError:
        raise LoiNghiepVu("Ngày hoặc giờ không đúng định dạng.")


def _doc_ngay(ngay: str) -> date:
    try:
        return date.fromisoformat(ngay.strip())
    except ValueError:
        raise LoiNghiepVu("Ngày không đúng định dạng.")


@router.get("/dat-lich", response_class=HTMLResponse)
def form_dat_lich(
    request: Request,
    thu_cung_id: int | None = None,
    dich_vu_id: int | None = None,
    nhan_vien_id: int | None = None,
    ngay: str = "",
    gio: str = "",
    khach=Depends(khach_hien_tai),
    db: Session = Depends(get_db),
):
    """Tham số truy vấn chỉ để điền sẵn ô (link từ trang khung trống); mọi phép kiểm vẫn chạy lúc POST."""
    cu = {"thu_cung_id": thu_cung_id, "dich_vu_id": dich_vu_id, "nhan_vien_id": nhan_vien_id, "ngay": ngay, "gio": gio}
    return _trang_dat_lich(request, db, khach, cu=cu)


@router.get("/khung-trong", response_class=HTMLResponse)
def xem_khung_trong(
    request: Request,
    thu_cung_id: int | None = None,
    dich_vu_id: int | None = None,
    ngay: str = "",
    khach=Depends(khach_hien_tai),
    db: Session = Depends(get_db),
):
    cu = {"thu_cung_id": thu_cung_id, "dich_vu_id": dich_vu_id, "ngay": ngay}
    nhom, loi = None, None
    if thu_cung_id is not None and dich_vu_id is not None and ngay.strip():
        try:
            nhom = dl.khung_trong_cua_khach(db, khach, thu_cung_id, dich_vu_id, _doc_ngay(ngay))
        except LoiKhongTimThay:
            raise
        except LoiNghiepVu as e:
            loi = str(e)
    return templates.TemplateResponse(
        request,
        "khach_khung_trong.html",
        {"khach": khach, "lc": dl.lua_chon_dat_lich(db, khach), "nhom": nhom, "loi": loi, "cu": cu},
        status_code=status.HTTP_400_BAD_REQUEST if loi else status.HTTP_200_OK,
    )


@router.post("/dat-lich", response_class=HTMLResponse)
def gui_dat_lich(
    request: Request,
    thu_cung_id: int = Form(...),
    dich_vu_id: int = Form(...),
    nhan_vien_id: int = Form(...),
    ngay: str = Form(""),
    gio: str = Form(""),
    ghi_chu: str = Form(""),
    khach=Depends(khach_hien_tai),
    db: Session = Depends(get_db),
):
    cu = {"thu_cung_id": thu_cung_id, "dich_vu_id": dich_vu_id, "nhan_vien_id": nhan_vien_id, "ngay": ngay, "gio": gio, "ghi_chu": ghi_chu}
    try:
        dl.gui_yeu_dat_lich(db, khach, thu_cung_id, dich_vu_id, nhan_vien_id, _doc_ngay_gio(ngay, gio), ghi_chu)
    except LoiKhongTimThay:
        raise
    except LoiNghiepVu as loi:
        return _trang_dat_lich(request, db, khach, loi=str(loi), cu=cu)
    return RedirectResponse("/khach/lich-hen", status_code=status.HTTP_303_SEE_OTHER)
