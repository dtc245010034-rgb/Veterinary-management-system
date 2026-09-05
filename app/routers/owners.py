"""Router chủ nuôi và thú cưng.

Phục vụ US-04, US-05, US-06. Chỉ làm việc HTTP: đọc form, gọi app/services/owners.py,
render template. Mọi kiểm tra dữ liệu nằm ở tầng services.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services import owners as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter()

# Quản lý và lễ tân được sửa; nhân viên chăm sóc chỉ xem (bảng phân quyền US-02).
duoc_sua = Depends(yeu_cau_vai_tro("manager", "receptionist"))


def _trang_danh_sach(
    request: Request,
    db: Session,
    user: User,
    tu_khoa: str = "",
    sdt_kiem_tra: str = "",
    loi: str | None = None,
    ma: int = 200,
):
    ket_qua = nv.tra_cuu(db, tu_khoa) if tu_khoa else None
    tat_ca = None if tu_khoa else nv.danh_sach_chu_nuoi(db)

    return templates.TemplateResponse(
        request,
        "owners.html",
        {
            "user": user,
            "tu_khoa": tu_khoa,
            "ket_qua": ket_qua,
            "tat_ca": tat_ca,
            "trung_so": nv.tim_theo_so_dien_thoai(db, sdt_kiem_tra) if sdt_kiem_tra else [],
            "sdt_kiem_tra": sdt_kiem_tra,
            "loi": loi,
        },
        status_code=ma,
    )


@router.get("/owners", response_class=HTMLResponse)
def trang_chu_nuoi(
    request: Request,
    q: str = "",
    sdt_kiem_tra: str = "",
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    return _trang_danh_sach(request, db, user, tu_khoa=q, sdt_kiem_tra=sdt_kiem_tra)


@router.post("/owners", response_class=HTMLResponse)
def them_chu_nuoi(
    request: Request,
    ho_ten: str = Form(""),
    so_dien_thoai: str = Form(""),
    email: str = Form(""),
    dia_chi: str = Form(""),
    ghi_chu: str = Form(""),
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    try:
        nv.tao_chu_nuoi(
            db,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            email=email,
            dia_chi=dia_chi,
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        return _trang_danh_sach(request, db, user, loi=str(loi), ma=status.HTTP_400_BAD_REQUEST)

    return RedirectResponse("/owners", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/owners/{chu_nuoi_id}", response_class=HTMLResponse)
def trang_chi_tiet(
    request: Request,
    chu_nuoi_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    loi: str | None = None,
):
    chu_nuoi = nv.lay_chu_nuoi(db, chu_nuoi_id)
    return templates.TemplateResponse(
        request,
        "owner_detail.html",
        {"user": user, "chu_nuoi": chu_nuoi, "loi": loi},
        status_code=status.HTTP_400_BAD_REQUEST if loi else 200,
    )


@router.post("/owners/{chu_nuoi_id}/xoa", response_class=HTMLResponse)
def xoa_chu_nuoi(
    request: Request,
    chu_nuoi_id: int,
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    try:
        nv.xoa_chu_nuoi(db, chu_nuoi_id)
    except LoiNghiepVu as loi:
        return _trang_danh_sach(request, db, user, loi=str(loi), ma=status.HTTP_400_BAD_REQUEST)

    return RedirectResponse("/owners", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/owners/{chu_nuoi_id}/pets", response_class=HTMLResponse)
def them_thu_cung(
    request: Request,
    chu_nuoi_id: int,
    ten: str = Form(""),
    loai: str = Form(""),
    giong: str = Form(""),
    gioi_tinh: str = Form(""),
    ngay_sinh: str = Form(""),
    can_nang: str = Form(""),
    ghi_chu: str = Form(""),
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    try:
        nv.tao_thu_cung(
            db,
            chu_nuoi_id=chu_nuoi_id,
            ten=ten,
            loai=loai,
            giong=giong,
            gioi_tinh=gioi_tinh,
            ngay_sinh=_doc_ngay(ngay_sinh),
            can_nang=_doc_so(can_nang),
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        return trang_chi_tiet(request, chu_nuoi_id, user, db, loi=str(loi))

    return RedirectResponse(f"/owners/{chu_nuoi_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/pets/{thu_cung_id}/xoa")
def xoa_thu_cung(
    thu_cung_id: int,
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    chu_nuoi_id = nv.lay_thu_cung(db, thu_cung_id).owner_id
    nv.xoa_thu_cung(db, thu_cung_id)
    return RedirectResponse(f"/owners/{chu_nuoi_id}", status_code=status.HTTP_303_SEE_OTHER)


def _doc_ngay(chuoi: str) -> date | None:
    """Form HTML gửi chuỗi rỗng khi người dùng bỏ trống ô ngày."""
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None
    try:
        return date.fromisoformat(chuoi)
    except ValueError:
        raise LoiNghiepVu("Ngày sinh không đúng định dạng.")


def _doc_so(chuoi: str) -> float | None:
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None
    try:
        return float(chuoi)
    except ValueError:
        raise LoiNghiepVu("Cân nặng phải là một số.")
