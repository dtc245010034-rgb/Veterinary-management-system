"""Router hóa đơn: danh sách, chi tiết, thu tiền, hủy hóa đơn.

Phục vụ US-19, US-20. Chỉ làm việc HTTP; nghiệp vụ nằm ở app/services/billing.py.

Cả router yêu cầu vai trò `manager` hoặc `receptionist` — bảng phân quyền US-02 không cho
`caretaker` quyền nào ở mục hóa đơn, kể cả quyền xem.

Việc LẬP hóa đơn không nằm ở đây mà ở `routers/appointments.py`: nó xuất phát từ một dòng
trong lưới lịch hẹn, và khi bị từ chối thì phải quay về đúng lưới đó kèm thông báo.
"""

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.payment import TEN_HINH_THUC
from app.models.user import User
from app.services import billing as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

# Phép kiểm vai trò đặt ở cấp router thay vì từng route: thiếu một route là thủng cả
# trang, và mục hóa đơn không có ngoại lệ nào cho `caretaker`.
router = APIRouter(
    prefix="/invoices",
    dependencies=[Depends(yeu_cau_vai_tro("manager", "receptionist"))],
)


@router.get("", response_class=HTMLResponse)
def trang_danh_sach(
    request: Request,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request,
        "invoices.html",
        {"user": user, "danh_sach": nv.danh_sach(db)},
    )


@router.get("/{hoa_don_id}", response_class=HTMLResponse)
def trang_chi_tiet(
    request: Request,
    hoa_don_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    loi: str | None = None,
    ma: int = 200,
    da_nhap: dict | None = None,
):
    try:
        hoa_don = nv.lay_hoa_don(db, hoa_don_id)
    except LoiNghiepVu as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))

    return templates.TemplateResponse(
        request,
        "invoice_detail.html",
        {
            "user": user,
            "hoa_don": hoa_don,
            "hinh_thuc": TEN_HINH_THUC,
            "loi": loi,
            # Báo lỗi mà xóa sạch ô nhập thì người dùng phải gõ lại cả form.
            "da_nhap": da_nhap or {},
        },
        status_code=ma,
    )


@router.post("/{hoa_don_id}/thanh-toan", response_class=HTMLResponse)
def thu_tien(
    request: Request,
    hoa_don_id: int,
    so_tien: str = Form(""),
    hinh_thuc: str = Form("cash"),
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    try:
        nv.ghi_nhan_thanh_toan(db, hoa_don_id, _doc_tien(so_tien), hinh_thuc)
    except LoiNghiepVu as e:
        return trang_chi_tiet(
            request,
            hoa_don_id,
            user,
            db,
            loi=str(e),
            ma=status.HTTP_400_BAD_REQUEST,
            da_nhap={"so_tien": so_tien, "hinh_thuc": hinh_thuc},
        )

    return _ve_chi_tiet(hoa_don_id)


@router.post("/{hoa_don_id}/huy", response_class=HTMLResponse)
def huy(
    request: Request,
    hoa_don_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    try:
        nv.huy_hoa_don(db, hoa_don_id)
    except LoiNghiepVu as e:
        return trang_chi_tiet(
            request, hoa_don_id, user, db, loi=str(e), ma=status.HTTP_400_BAD_REQUEST
        )

    return _ve_chi_tiet(hoa_don_id)


def _ve_chi_tiet(hoa_don_id: int) -> RedirectResponse:
    """POST xong thì chuyển hướng — F5 sau đó không gửi lại form (PRG)."""
    return RedirectResponse(
        f"/invoices/{hoa_don_id}", status_code=status.HTTP_303_SEE_OTHER
    )


def _doc_tien(chuoi: str) -> Decimal | None:
    """Đọc tiền thành Decimal, không qua float, và chấp nhận cả '150.000'.

    Ô trống trả về None để tầng services phân biệt "không nhập" với "nhập số 0" — hai
    thông báo lỗi khác nhau, và luật "phải nhập" là nghiệp vụ nên nó ở services.
    """
    chuoi = (chuoi or "").strip().replace(".", "").replace(",", "").replace(" ", "")
    if not chuoi:
        return None
    try:
        return Decimal(chuoi)
    except InvalidOperation:
        raise LoiNghiepVu("Số tiền phải là một số.")
