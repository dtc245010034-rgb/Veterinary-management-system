"""Router trang chi tiết thú cưng.

Phục vụ US-05 — TC-020, hoãn từ P2a và đóng lại ở P4 chặng 2.

Trang này gộp hai miền nghiệp vụ: lịch sử chăm sóc (app/services/care_records.py) và hồ
sơ tiêm (app/services/vaccinations.py). Vì vậy nó có router riêng thay vì nằm nhờ trong
care_records.py như ở chặng 1 — đúng như cây thư mục trong docs/architecture.md.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai
from app.db import get_db
from app.models.user import User
from app.services import care_records, clock, owners
from app.services import vaccinations as tiem
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter()


@router.get("/pets/{thu_cung_id}", response_class=HTMLResponse)
def trang_thu_cung(
    request: Request,
    thu_cung_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    loi: str | None = None,
    ma: int = 200,
):
    try:
        thu_cung = owners.lay_thu_cung(db, thu_cung_id)
    except LoiNghiepVu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thú cưng.")

    return templates.TemplateResponse(
        request,
        "pet_detail.html",
        {
            "user": user,
            "thu_cung": thu_cung,
            "lich_su": care_records.lich_su(db, thu_cung_id),
            "ho_so_tiem": tiem.ho_so_tiem(db, thu_cung_id),
            # Chặn chọn ngày tương lai ngay ở trình duyệt; tầng services vẫn kiểm lại.
            "hom_nay": clock.now().date(),
            "loi": loi,
        },
        status_code=ma,
    )
