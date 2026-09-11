"""Router trang thống kê.

Phục vụ US-22, US-23 và TC-006. Chỉ làm việc HTTP; số liệu tính ở app/services/stats.py.

Cả router chỉ cho vai trò `manager` — bảng phân quyền US-02 không cho lễ tân hay nhân viên
chăm sóc xem thống kê. Kiểm ở cấp router như `routers/invoices.py`: thiếu một route là thủng.
"""

from datetime import date

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services import stats as nv
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/stats", dependencies=[Depends(yeu_cau_vai_tro("manager"))])


@router.get("", response_class=HTMLResponse)
def trang_thong_ke(
    request: Request,
    tu_ngay: str = "",
    den_ngay: str = "",
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    # Nhận chuỗi chứ không khai báo `date` cho FastAPI tự đọc: sai định dạng thì FastAPI
    # trả 422 dạng JSON thô, còn ở đây người dùng cần một câu tiếng Việt ngay trên trang.
    try:
        # Ô nào trống thì lấy theo kỳ mặc định — tính lùi từ "Đến ngày" nếu nó đã được chọn.
        mac_dinh_tu, den = nv.ky_mac_dinh(_doc_ngay(den_ngay))
        tu = _doc_ngay(tu_ngay) or mac_dinh_tu
        thong_ke = nv.thong_ke(db, tu, den)
    except LoiNghiepVu as e:
        # Giữ nguyên thứ người dùng đã chọn — báo lỗi mà xóa ngày thì phải chọn lại cả hai.
        return templates.TemplateResponse(
            request,
            "stats.html",
            {"user": user, "tk": None, "loi": str(e), "tu_ngay": tu_ngay, "den_ngay": den_ngay},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request,
        "stats.html",
        {
            "user": user,
            "tk": thong_ke,
            "loi": None,
            "tu_ngay": tu.isoformat(),
            "den_ngay": den.isoformat(),
        },
    )


def _doc_ngay(chuoi: str) -> date | None:
    """'2026-03-12' -> date. Ô trống trả None để dùng kỳ mặc định.

    Ô `type=date` của trình duyệt luôn gửi dạng năm-tháng-ngày; dạng khác chỉ tới từ URL
    gõ tay hoặc trình duyệt không có ô chọn ngày.
    """
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None
    try:
        return date.fromisoformat(chuoi)
    except ValueError:
        raise LoiNghiepVu(
            "Ngày không hợp lệ. Chọn ngày bằng ô lịch, hoặc nhập theo dạng năm-tháng-ngày."
        )
