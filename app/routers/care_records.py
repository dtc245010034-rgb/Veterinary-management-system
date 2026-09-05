"""Router hồ sơ chăm sóc: ghi hồ sơ sau buổi dịch vụ, xem lịch sử của thú cưng.

Phục vụ US-15, US-16. Chỉ làm việc HTTP; quy tắc nghiệp vụ nằm ở
app/services/care_records.py.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services import care_records as nv
from app.services import owners, scheduling
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter()

duoc_ghi_ho_so = Depends(yeu_cau_vai_tro(*nv.VAI_TRO_GHI_DUOC))


@router.get("/appointments/{lich_id}/ho-so", response_class=HTMLResponse)
def trang_ho_so(
    request: Request,
    lich_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    loi: str | None = None,
    ma: int = 200,
):
    try:
        lich = scheduling.lay_lich(db, lich_id)
    except LoiNghiepVu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lịch hẹn.")

    return templates.TemplateResponse(
        request,
        "care_record_form.html",
        {"user": user, "lich": lich, "ho_so": nv.ho_so_cua_lich(db, lich_id), "loi": loi},
        status_code=ma,
    )


@router.post("/appointments/{lich_id}/ho-so", response_class=HTMLResponse)
def luu_ho_so(
    request: Request,
    lich_id: int,
    tinh_trang: str = Form(""),
    viec_da_lam: str = Form(""),
    dan_do: str = Form(""),
    user: User = duoc_ghi_ho_so,
    db: Session = Depends(get_db),
):
    try:
        nv.ghi_ho_so(
            db,
            lich_id,
            nguoi_ghi_id=user.id,
            tinh_trang=tinh_trang,
            viec_da_lam=viec_da_lam,
            dan_do=dan_do,
        )
    except LoiNghiepVu as loi:
        return trang_ho_so(
            request, lich_id, user, db, loi=str(loi), ma=status.HTTP_400_BAD_REQUEST
        )

    return RedirectResponse(_ve_lich_sau_khi_ghi(db, user, lich_id), status.HTTP_303_SEE_OTHER)


@router.get("/pets/{thu_cung_id}", response_class=HTMLResponse)
def trang_thu_cung(
    request: Request,
    thu_cung_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    """Trang chi tiết thú cưng — TC-020 hoãn từ P2a.

    Chặng 1 hiện lịch sử chăm sóc; chặng 2 thêm khối hồ sơ tiêm vào chính trang này.
    """
    try:
        thu_cung = owners.lay_thu_cung(db, thu_cung_id)
    except LoiNghiepVu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thú cưng.")

    return templates.TemplateResponse(
        request,
        "pet_detail.html",
        {"user": user, "thu_cung": thu_cung, "lich_su": nv.lich_su(db, thu_cung_id)},
    )


def _ve_lich_sau_khi_ghi(db: Session, user: User, lich_id: int) -> str:
    """Về đúng trang mà người vừa ghi nhìn thấy được lịch đó.

    Quản lý không được phân lịch nào nên `/appointments/cua-toi` với họ luôn rỗng: vừa
    làm xong một việc thì nhận về màn hình trắng, không dấu hiệu nào cho biết đã lưu.
    """
    ngay = scheduling.lay_lich(db, lich_id).start_at.date().isoformat()
    trang = "/appointments/cua-toi" if user.role == "caretaker" else "/appointments"
    return f"{trang}?ngay={ngay}"
