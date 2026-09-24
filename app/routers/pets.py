"""Router trang chi tiết thú cưng.

Phục vụ US-05 — TC-020, hoãn từ P2a và đóng lại ở P4 chặng 2.

Trang này gộp hai miền nghiệp vụ: lịch sử chăm sóc (app/services/care_records.py) và hồ
sơ tiêm (app/services/vaccinations.py). Vì vậy nó có router riêng thay vì nằm nhờ trong
care_records.py như ở chặng 1 — đúng như cây thư mục trong docs/architecture.md.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.routers.owners import doc_ngay_form, doc_so_form
from app.services import care_records, clock, owners
from app.services import vaccinations as tiem
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter()

duoc_sua = Depends(yeu_cau_vai_tro("manager", "receptionist"))


@router.get("/pets/{thu_cung_id}", response_class=HTMLResponse)
def trang_thu_cung(
    request: Request,
    thu_cung_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    loi: str | None = None,
    ma: int = 200,
    da_nhap: dict | None = None,
):
    try:
        thu_cung = owners.lay_thu_cung(db, thu_cung_id)
    except LoiNghiepVu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thú cưng.")

    ho_so_tiem = tiem.ho_so_tiem(db, thu_cung_id)

    return templates.TemplateResponse(
        request,
        "pet_detail.html",
        {
            "user": user,
            "thu_cung": thu_cung,
            "lich_su": care_records.lich_su(db, thu_cung_id),
            "ho_so_tiem": ho_so_tiem,
            # L-04: chỉ mũi mới nhất của mỗi loại mới được gắn nhãn "Quá hạn". Mũi cũ đã
            # có mũi sau thay thế thì lời nhắc của nó đã hoàn thành — cùng luật mà
            # `vaccinations.den_han()` dùng cho danh sách đến hạn.
            "mui_moi_nhat": tiem.mui_moi_nhat_moi_loai(ho_so_tiem),
            # Chặn chọn ngày tương lai ngay ở trình duyệt; tầng services vẫn kiểm lại.
            "hom_nay": clock.now().date(),
            "loi": loi,
            # Báo lỗi mà xóa sạch ô nhập thì người dùng phải gõ lại cả form.
            "da_nhap": da_nhap or {},
        },
        status_code=ma,
    )


@router.post("/pets/{thu_cung_id}/sua", response_class=HTMLResponse)
def sua_thu_cung(
    request: Request,
    thu_cung_id: int,
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
    """US-05 "thêm, **sửa**, xem" — `owners.sua_thu_cung` có unit test từ P2 nhưng chưa
    có đường vào từ giao diện (M-02).

    Route nằm ở đây chứ không ở `owners.py` để lỗi render lại được đúng trang người dùng
    đang đứng, không phải đẩy họ về trang chủ nuôi và mất cả form vừa gõ.
    """
    try:
        owners.sua_thu_cung(
            db,
            thu_cung_id,
            ten=ten,
            loai=loai,
            giong=giong,
            gioi_tinh=gioi_tinh,
            ngay_sinh=doc_ngay_form(ngay_sinh),
            can_nang=doc_so_form(can_nang),
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        return trang_thu_cung(
            request, thu_cung_id, user, db,
            loi=str(loi),
            ma=status.HTTP_400_BAD_REQUEST,
            da_nhap={
                "ten": ten, "loai": loai, "giong": giong, "gioi_tinh": gioi_tinh,
                "ngay_sinh": ngay_sinh, "can_nang": can_nang, "ghi_chu": ghi_chu,
            },
        )

    return RedirectResponse(f"/pets/{thu_cung_id}", status_code=status.HTTP_303_SEE_OTHER)
