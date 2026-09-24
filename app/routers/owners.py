"""Router chủ nuôi và thú cưng.

Phục vụ US-04, US-05, US-06. Chỉ làm việc HTTP: đọc form, gọi app/services/owners.py,
render template. Mọi kiểm tra dữ liệu nằm ở tầng services.
"""

import math
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
    bo_qua_id: int | None = None,
    loi: str | None = None,
    loi_nhap: str | None = None,
    ma: int = 200,
    da_nhap: dict | None = None,
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
            "trung_so": (
                nv.tim_theo_so_dien_thoai(db, sdt_kiem_tra, bo_qua_id)
                if sdt_kiem_tra
                else []
            ),
            "sdt_kiem_tra": sdt_kiem_tra,
            # Hai chỗ khác nhau: `loi` là lỗi của cả trang (xóa chủ nuôi không được),
            # `loi_nhap` là lỗi của form thêm và phải hiện ngay trong khung nhập.
            "loi": loi,
            "loi_nhap": loi_nhap,
            # Báo lỗi mà xóa sạch ô nhập thì người dùng phải gõ lại cả form.
            "da_nhap": da_nhap or {},
        },
        status_code=ma,
    )


@router.get("/owners", response_class=HTMLResponse)
def trang_chu_nuoi(
    request: Request,
    q: str = "",
    sdt_kiem_tra: str = "",
    bo_qua_id: int | None = None,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
):
    return _trang_danh_sach(
        request, db, user, tu_khoa=q, sdt_kiem_tra=sdt_kiem_tra, bo_qua_id=bo_qua_id
    )


@router.post("/owners", response_class=HTMLResponse)
def them_chu_nuoi(
    request: Request,
    ho_ten: str = Form(""),
    so_dien_thoai: str = Form(""),
    email: str = Form(""),
    dia_chi: str = Form(""),
    ghi_chu: str = Form(""),
    xac_nhan: str = Form(""),
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    da_nhap = {
        "ho_ten": ho_ten, "so_dien_thoai": so_dien_thoai,
        "email": email, "dia_chi": dia_chi, "ghi_chu": ghi_chu,
    }

    # US-04: "cảnh báo trùng và HỎI có phải khách cũ không". Hỏi phải diễn ra TRƯỚC khi
    # tạo — bản cũ tạo xong mới cảnh báo, và câu cảnh báo bảo "hãy mở hồ sơ đó thay vì
    # tạo mới" trong khi bản ghi mới đã nằm trong cơ sở dữ liệu (M-07).
    if not xac_nhan:
        trung = nv.tim_theo_so_dien_thoai(db, so_dien_thoai)
        if trung:
            ten_cu = ", ".join(o.full_name for o in trung)
            return _trang_xac_nhan(
                request, user,
                tieu_de="Số điện thoại này đã có trong hệ thống",
                thong_tin=[
                    ("Khách đã có", ten_cu),
                    ("Số điện thoại", nv.chuan_hoa_so_dien_thoai(so_dien_thoai)),
                    ("Tên vừa nhập", ho_ten),
                ],
                canh_bao=(
                    f"Nếu đây chính là {ten_cu} thì hãy quay lại và mở hồ sơ sẵn có "
                    "thay vì tạo mới. Chỉ tạo khách mới khi đúng là hai người khác nhau "
                    "dùng chung một số."
                ),
                hanh_dong="/owners",
                quay_lai="/owners",
                nut="Vẫn tạo khách mới",
                kieu_nut="chinh",
                truong_an={**da_nhap, "xac_nhan": "1"},
            )

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
        return _trang_danh_sach(
            request, db, user,
            loi_nhap=str(loi),
            ma=status.HTTP_400_BAD_REQUEST,
            da_nhap=da_nhap,
        )

    return RedirectResponse("/owners", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/owners/{chu_nuoi_id}", response_class=HTMLResponse)
def trang_chi_tiet(
    request: Request,
    chu_nuoi_id: int,
    user: User = Depends(nguoi_dung_hien_tai),
    db: Session = Depends(get_db),
    loi: str | None = None,
    da_nhap: dict | None = None,
):
    chu_nuoi = nv.lay_chu_nuoi(db, chu_nuoi_id)
    return templates.TemplateResponse(
        request,
        "owner_detail.html",
        {"user": user, "chu_nuoi": chu_nuoi, "loi": loi, "da_nhap": da_nhap or {}},
        status_code=status.HTTP_400_BAD_REQUEST if loi else 200,
    )


@router.post("/owners/{chu_nuoi_id}/sua", response_class=HTMLResponse)
def sua_chu_nuoi(
    request: Request,
    chu_nuoi_id: int,
    ho_ten: str = Form(""),
    so_dien_thoai: str = Form(""),
    email: str = Form(""),
    dia_chi: str = Form(""),
    ghi_chu: str = Form(""),
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    """US-04 nói "thêm, **sửa**, xem" — `nv.sua_chu_nuoi` có từ P2 mà không router nào gọi (M-02)."""
    try:
        nv.sua_chu_nuoi(
            db,
            chu_nuoi_id,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            email=email,
            dia_chi=dia_chi,
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        return trang_chi_tiet(request, chu_nuoi_id, user, db, loi=str(loi))

    return RedirectResponse(f"/owners/{chu_nuoi_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/owners/{chu_nuoi_id}/xoa", response_class=HTMLResponse)
def trang_xac_nhan_xoa_chu_nuoi(
    request: Request,
    chu_nuoi_id: int,
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    """Hỏi lại trước khi xóa. GET không đổi gì — việc thật nằm ở route POST bên dưới."""
    chu_nuoi = nv.lay_chu_nuoi(db, chu_nuoi_id)
    return _trang_xac_nhan(
        request,
        user,
        tieu_de=f"Xác nhận xóa chủ nuôi {chu_nuoi.full_name}",
        thong_tin=[
            ("Họ tên", chu_nuoi.full_name),
            ("Số điện thoại", chu_nuoi.phone),
            ("Thú cưng", len(chu_nuoi.pets)),
        ],
        canh_bao=(
            "Xóa rồi thì hồ sơ chủ nuôi này không lấy lại được. Chủ nuôi còn thú cưng "
            "thì hệ thống sẽ từ chối — xóa thú cưng trước."
        ),
        hanh_dong=f"/owners/{chu_nuoi.id}/xoa",
        quay_lai=f"/owners/{chu_nuoi.id}",
        nut="Xóa chủ nuôi",
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
            ngay_sinh=doc_ngay_form(ngay_sinh),
            can_nang=doc_so_form(can_nang),
            ghi_chu=ghi_chu,
        )
    except LoiNghiepVu as loi:
        return trang_chi_tiet(
            request, chu_nuoi_id, user, db,
            loi=str(loi),
            da_nhap={
                "ten": ten, "loai": loai, "giong": giong, "gioi_tinh": gioi_tinh,
                "ngay_sinh": ngay_sinh, "can_nang": can_nang, "ghi_chu": ghi_chu,
            },
        )

    return RedirectResponse(f"/owners/{chu_nuoi_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/pets/{thu_cung_id}/xoa", response_class=HTMLResponse)
def trang_xac_nhan_xoa_thu_cung(
    request: Request,
    thu_cung_id: int,
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    thu_cung = nv.lay_thu_cung(db, thu_cung_id)
    return _trang_xac_nhan(
        request,
        user,
        tieu_de=f"Xác nhận xóa thú cưng {thu_cung.name}",
        thong_tin=[
            ("Tên", thu_cung.name),
            ("Loài", thu_cung.species),
            ("Chủ nuôi", thu_cung.owner.full_name),
        ],
        canh_bao=(
            "Xóa rồi thì hồ sơ con vật này không lấy lại được. Thú cưng đã có lịch hẹn "
            "hoặc mũi tiêm thì hệ thống sẽ từ chối."
        ),
        hanh_dong=f"/pets/{thu_cung.id}/xoa",
        quay_lai=f"/owners/{thu_cung.owner_id}",
        nut="Xóa thú cưng",
    )


@router.post("/pets/{thu_cung_id}/xoa", response_class=HTMLResponse)
def xoa_thu_cung(
    request: Request,
    thu_cung_id: int,
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    chu_nuoi_id = nv.lay_thu_cung(db, thu_cung_id).owner_id

    try:
        nv.xoa_thu_cung(db, thu_cung_id)
    except LoiNghiepVu as loi:
        # Thiếu nhánh này thì LoiNghiepVu bay ra thành 500 — đúng lỗi mà việc chặn ở
        # tầng services vừa sửa xong lại tái diễn ở tầng HTTP.
        return trang_chi_tiet(request, chu_nuoi_id, user, db, loi=str(loi))

    return RedirectResponse(f"/owners/{chu_nuoi_id}", status_code=status.HTTP_303_SEE_OTHER)


def _trang_xac_nhan(request: Request, user: User, **noi_dung):
    """Render trang hỏi lại dùng chung — xem `templates/xac_nhan.html`."""
    return templates.TemplateResponse(
        request, "xac_nhan.html", {"user": user, **noi_dung}
    )


def doc_ngay_form(chuoi: str) -> date | None:
    """Form HTML gửi chuỗi rỗng khi người dùng bỏ trống ô ngày.

    Tên công khai (không gạch dưới) vì `routers/pets.py` dùng chung khi sửa thú cưng —
    nhập một hàm riêng tư từ module khác là nói dối về phạm vi của nó.
    """
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None
    try:
        return date.fromisoformat(chuoi)
    except ValueError:
        raise LoiNghiepVu("Ngày sinh không đúng định dạng.")


def doc_so_form(chuoi: str) -> float | None:
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None
    try:
        so = float(chuoi)
    except ValueError:
        raise LoiNghiepVu("Cân nặng phải là một số.")
    # float() nhận cả "nan" và "inf": nan lọt qua phép so "> 0" rồi bị lưu thành trống,
    # inf hiện ra "inf kg" (rà bằng trình duyệt 11/09).
    if not math.isfinite(so):
        raise LoiNghiepVu("Cân nặng phải là một số.")
    return so
