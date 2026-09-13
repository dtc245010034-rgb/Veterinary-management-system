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
    user: User = duoc_sua,
    db: Session = Depends(get_db),
):
    try:
        moi = nv.tao_chu_nuoi(
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
            da_nhap={
                "ho_ten": ho_ten, "so_dien_thoai": so_dien_thoai,
                "email": email, "dia_chi": dia_chi, "ghi_chu": ghi_chu,
            },
        )

    # US-04: trùng số thì cảnh báo chứ không cấm. Khối cảnh báo có sẵn trong template từ
    # P2a nhưng chỉ hiện khi tự gõ `?sdt_kiem_tra=` — không nút nào sinh ra URL đó, nên
    # trên thực tế người dùng thêm chủ nuôi trùng số mà chưa từng thấy cảnh báo nào.
    if nv.tim_theo_so_dien_thoai(db, moi.phone, bo_qua_id=moi.id):
        return RedirectResponse(
            f"/owners?sdt_kiem_tra={moi.phone}&bo_qua_id={moi.id}",
            status_code=status.HTTP_303_SEE_OTHER,
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
            ngay_sinh=_doc_ngay(ngay_sinh),
            can_nang=_doc_so(can_nang),
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
        so = float(chuoi)
    except ValueError:
        raise LoiNghiepVu("Cân nặng phải là một số.")
    # float() nhận cả "nan" và "inf": nan lọt qua phép so "> 0" rồi bị lưu thành trống,
    # inf hiện ra "inf kg" (rà bằng trình duyệt 11/09).
    if not math.isfinite(so):
        raise LoiNghiepVu("Cân nặng phải là một số.")
    return so
