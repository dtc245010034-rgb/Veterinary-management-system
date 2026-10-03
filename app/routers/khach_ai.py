"""Router hỏi đáp AI của khách (P9 chặng 7): GET/POST `/khach/hoi-dap`, GET `/khach/hoi-dap/{log_id}`.

Khách chỉ có hỏi đáp (US-26); nhắc lịch và tóm tắt hồ sơ đọc dữ liệu chủ nuôi nên không mở cho khách. Chỉ làm việc
HTTP: không import `app.models`, không truy vấn `db.*`, và chỉ biết một cửa của tầng AI là `app.ai.service`.

Post/Redirect/Get như màn nhân viên: bấm F5 trang kết quả chỉ đọc lại dòng log, không đốt thêm một lượt.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.ai import service as nv
from app.auth import khach_hien_tai
from app.db import get_db
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/khach")

AIProvider = nv.AIProvider
LoiAI = nv.LoiAI
LoiHetHanMuc = nv.LoiHetHanMuc


def _trang_hoi(request: Request, khach, db: Session, cau_hoi: str = "", loi: str | None = None, ma: int = 200):
    return templates.TemplateResponse(
        request,
        "khach_hoi_dap.html",
        {
            "khach": khach,
            "cau_hoi": cau_hoi,
            "loi": loi,
            "con_lai": nv.so_luot_con_lai_khach(db, khach.id),
            "toi_da": nv.so_luot_toi_da_khach(),
        },
        status_code=ma,
    )


@router.get("/hoi-dap", response_class=HTMLResponse)
def trang_hoi_dap(request: Request, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)):
    return _trang_hoi(request, khach, db)


@router.post("/hoi-dap", response_class=HTMLResponse)
def hoi_dap(
    request: Request,
    cau_hoi: str = Form(""),
    khach=Depends(khach_hien_tai),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(nv.lay_provider),
):
    try:
        ket_qua = nv.hoi_dap_khach(db, provider, khach.id, cau_hoi)
    except LoiHetHanMuc as loi:
        return _trang_hoi(request, khach, db, cau_hoi, str(loi), status.HTTP_429_TOO_MANY_REQUESTS)
    except (LoiNghiepVu, LoiAI) as loi:
        # Giữ lại câu đã gõ: bắt khách gõ lại chỉ vì AI bận là vô lý.
        return _trang_hoi(request, khach, db, cau_hoi, str(loi), status.HTTP_400_BAD_REQUEST)

    return RedirectResponse(f"/khach/hoi-dap/{ket_qua.log_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/hoi-dap/{log_id}", response_class=HTMLResponse)
def ket_qua_hoi_dap(
    request: Request, log_id: int, khach=Depends(khach_hien_tai), db: Session = Depends(get_db)
):
    """Chỉ chủ của dòng log mới đọc được; id của người khác trả 404 y hệt id không tồn tại."""
    try:
        log = nv.lay_log_khach(db, khach.id, log_id)
    except LoiKhongTimThay as loi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(loi))

    return templates.TemplateResponse(request, "khach_ket_qua_hoi_dap.html", {"khach": khach, "log": log})
