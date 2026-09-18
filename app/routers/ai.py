"""Router ba tính năng AI và trang quota.

Phục vụ US-24 → US-28. Chỉ làm việc HTTP: kiểm quyền, gọi `app/ai/service.py`, render.
Không import file nào khác trong `app/ai/` — có phép canh trong test_architecture.py.

**Post/Redirect/Get.** Mọi lời gọi AI đi bằng POST rồi chuyển hướng sang trang kết quả đọc
theo mã `ai_logs`. Nhờ vậy bấm F5 chỉ đọc lại bản ghi cũ chứ không gọi AI thêm lần nữa —
mỗi lần gọi thừa là một lượt quota miễn phí bị đốt (xem app/ai/quota.py).

Phân quyền (người dùng chốt 18/09): tóm tắt và hỏi đáp cho cả ba vai trò; nhắc lịch là việc
của quầy nên chỉ `manager` và `receptionist`; trang quota chỉ `manager`.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.ai import service as nv
from app.auth import nguoi_dung_hien_tai, yeu_cau_vai_tro
from app.db import get_db
from app.models.user import User
from app.services.errors import LoiNghiepVu
from app.templates import templates

router = APIRouter(prefix="/ai")

# Lấy qua `service` chứ không import thẳng `app.ai.provider`: router chỉ được biết một cửa
# duy nhất của tầng AI (CLAUDE.md mục 8). Phép canh trong test_architecture.py bắt được ngay.
AIProvider = nv.AIProvider
LoiAI = nv.LoiAI

soan_nhac_lich = Depends(yeu_cau_vai_tro("manager", "receptionist"))
chi_quan_ly = Depends(yeu_cau_vai_tro("manager"))


def _quay_lai(tu: str) -> str:
    """Đường dẫn cho nút "Quay lại", lấy từ query string.

    Chỉ nhận đường dẫn nội bộ bắt đầu bằng đúng MỘT dấu `/`. `//evil.com` cũng là một URL
    hợp lệ với trình duyệt và sẽ đưa người dùng ra khỏi hệ thống.
    """
    if tu.startswith("/") and not tu.startswith("//"):
        return tu
    return "/"


def _ve_ket_qua(log_id: int, tu: str) -> RedirectResponse:
    return RedirectResponse(
        f"/ai/ket-qua/{log_id}?tu={_quay_lai(tu)}", status_code=status.HTTP_303_SEE_OTHER
    )


def _bao_loi(request: Request, user: User, thong_diep: str, tu: str, ma: int = 400):
    """Lỗi AI không được làm vỡ trang — US-24. Khuyến cáo vẫn hiện (ca G-19)."""
    return templates.TemplateResponse(
        request,
        "ai_ket_qua.html",
        {"user": user, "log": None, "loi": thong_diep, "quay_lai": _quay_lai(tu)},
        status_code=ma,
    )


# --- Nhắc lịch (US-24) -------------------------------------------------------------


@router.post("/nhac-lich/lich-hen/{lich_id}", response_class=HTMLResponse)
def nhac_lich_hen(
    request: Request,
    lich_id: int,
    tu: str = Form("/appointments"),
    user: User = soan_nhac_lich,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(nv.lay_provider),
):
    try:
        ket_qua = nv.nhac_lich_hen(db, provider, user.id, lich_id)
    except (LoiNghiepVu, LoiAI) as loi:
        return _bao_loi(request, user, str(loi), tu)

    return _ve_ket_qua(ket_qua.log_id, tu)


@router.post("/nhac-lich/tiem/{mui_id}", response_class=HTMLResponse)
def nhac_lich_tiem(
    request: Request,
    mui_id: int,
    tu: str = Form("/vaccinations"),
    user: User = soan_nhac_lich,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(nv.lay_provider),
):
    try:
        ket_qua = nv.nhac_lich_tiem(db, provider, user.id, mui_id)
    except (LoiNghiepVu, LoiAI) as loi:
        return _bao_loi(request, user, str(loi), tu)

    return _ve_ket_qua(ket_qua.log_id, tu)


# --- Tóm tắt hồ sơ (US-25) ----------------------------------------------------------


@router.post("/tom-tat/{thu_cung_id}", response_class=HTMLResponse)
def tom_tat(
    request: Request,
    thu_cung_id: int,
    tu: str = Form(""),
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(nv.lay_provider),
):
    tu = tu or f"/pets/{thu_cung_id}"
    try:
        ket_qua = nv.tom_tat_ho_so(db, provider, user.id, thu_cung_id)
    except (LoiNghiepVu, LoiAI) as loi:
        return _bao_loi(request, user, str(loi), tu)

    return _ve_ket_qua(ket_qua.log_id, tu)


# --- Hỏi đáp (US-26, US-27) ----------------------------------------------------------


@router.get("/hoi-dap", response_class=HTMLResponse)
def trang_hoi_dap(
    request: Request,
    user: User = Depends(nguoi_dung_hien_tai),
    cau_hoi: str = "",
    loi: str | None = None,
    ma: int = 200,
):
    return templates.TemplateResponse(
        request,
        "ai_hoi_dap.html",
        {"user": user, "cau_hoi": cau_hoi, "loi": loi},
        status_code=ma,
    )


@router.post("/hoi-dap", response_class=HTMLResponse)
def hoi_dap(
    request: Request,
    cau_hoi: str = Form(""),
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(nv.lay_provider),
):
    try:
        ket_qua = nv.hoi_dap(db, provider, user.id, cau_hoi)
    except (LoiNghiepVu, LoiAI) as loi:
        # Giữ lại câu đã gõ: bắt người dùng gõ lại cả câu hỏi chỉ vì AI bận là vô lý.
        return trang_hoi_dap(
            request, user, cau_hoi=cau_hoi, loi=str(loi), ma=status.HTTP_400_BAD_REQUEST
        )

    return _ve_ket_qua(ket_qua.log_id, "/ai/hoi-dap")


# --- Trang kết quả dùng chung ---------------------------------------------------------


@router.get("/ket-qua/{log_id}", response_class=HTMLResponse)
def trang_ket_qua(
    request: Request,
    log_id: int,
    tu: str = "/",
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    """Đọc lại một kết quả đã lưu. Không gọi AI — đó là điểm của Post/Redirect/Get."""
    try:
        log = nv.lay_log(db, log_id)
    except LoiNghiepVu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy kết quả AI này.")

    if log.feature == "reminder" and user.role not in ("manager", "receptionist"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Bạn không có quyền truy cập chức năng này."
        )

    return templates.TemplateResponse(
        request,
        "ai_ket_qua.html",
        {"user": user, "log": log, "loi": None, "quay_lai": _quay_lai(tu)},
    )


@router.post("/ket-qua/{log_id}/chot", response_class=HTMLResponse)
def chot_tin_nhan(
    request: Request,
    log_id: int,
    noi_dung: str = Form(""),
    tu: str = Form("/appointments"),
    user: User = soan_nhac_lich,
    db: Session = Depends(get_db),
):
    """Bản lễ tân đã sửa mới là bản được dùng — US-24.

    Không ghi đè `ai_logs.response`: cột đó là bằng chứng AI đã trả về gì, sửa nó đi thì
    báo cáo cuối kỳ không còn đối chiếu được. Bản chốt chỉ hiện ra để sao chép và gửi.
    """
    try:
        log = nv.lay_log(db, log_id)
    except LoiNghiepVu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy kết quả AI này.")

    return templates.TemplateResponse(
        request,
        "ai_ket_qua.html",
        {
            "user": user,
            "log": log,
            "loi": None,
            "quay_lai": _quay_lai(tu),
            "ban_chot": noi_dung.strip(),
        },
    )


# --- Quota (chỉ quản lý) ---------------------------------------------------------------


@router.get("/quota", response_class=HTMLResponse)
def trang_quota(
    request: Request,
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
    da_dat_lai: int | None = None,
):
    return templates.TemplateResponse(
        request,
        "ai_quota.html",
        {
            "user": user,
            "bang": nv.bang_quota(db),
            "moc_reset": nv.moc_reset_ke_tiep(),
            "da_dat_lai": da_dat_lai,
        },
    )


@router.post("/quota/dat-lai", response_class=HTMLResponse)
def dat_lai_quota(
    user: User = chi_quan_ly,
    db: Session = Depends(get_db),
):
    """Xóa trạng thái chặn khi hệ thống đoán sai, giữ nguyên số lượt đã đếm."""
    so_model = nv.dat_lai_quota(db)
    return RedirectResponse(
        f"/ai/quota?da_dat_lai={so_model}", status_code=status.HTTP_303_SEE_OTHER
    )
