"""Nghiệp vụ dịch vụ, bảng giá và gói dịch vụ.

Phục vụ US-07, US-08, US-09. Không import fastapi — gọi trực tiếp được trong test.

`danh_sach_dang_ban()` và `danh_sach_goi_dang_ban()` là hai hàm P3 và P5 sẽ dùng khi dựng
danh sách chọn. Tách sẵn ở đây để cơ chế ngưng bán được kiểm ngay tại P2b thay vì phải đợi
tới lúc có form đặt lịch.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import Service
from app.models.service_package import PackageItem, ServicePackage
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.services.scheduling import PHUT_LAM_VIEC_MOI_NGAY

# Trần số tiền. Rà 19/09: giá 99.999.999.999.999 lưu được — vượt cả `Numeric(12,2)`
# mà SQLite không ép kiểu nên không chặn (L-03). Một tỷ đồng cho một dịch vụ chăm sóc
# thú cưng đã rộng hơn mọi mức có thật.
GIA_TOI_DA = Decimal("1000000000")


def _bat_buoc(gia_tri: str | None, ten_truong: str) -> str:
    da_cat = (gia_tri or "").strip()
    if not da_cat:
        raise LoiNghiepVu(f"{ten_truong} không được để trống.")
    return da_cat


def _kiem_gia(gia: Decimal | None) -> Decimal:
    """Giá 0 là hợp lệ — dịch vụ miễn phí có thật. Chỉ số âm mới vô lý."""
    if gia is None:
        raise LoiNghiepVu("Giá không được để trống.")
    if gia < 0:
        raise LoiNghiepVu("Giá không được là số âm.")
    if gia > GIA_TOI_DA:
        raise LoiNghiepVu(
            "Giá không được quá 1 tỷ đồng — kiểm lại xem có gõ thừa số 0 không."
        )
    return gia


def _kiem_thoi_luong(phut: int | None) -> int:
    """Phải lớn hơn 0, không phải lớn hơn hoặc bằng.

    P3 tính end_at = start_at + duration_min. Thời lượng 0 tạo ra lịch hẹn có khoảng thời
    gian rỗng, lọt qua mọi phép kiểm tra trùng lịch.

    Cận trên thêm 24/09 (M-06): dịch vụ dài hơn một ngày làm việc thì không buổi nào của
    nó đặt được, vì `scheduling` buộc cả buổi nằm trong giờ mở cửa. Chặn ngay tại đây để
    quản lý biết lúc tạo, thay vì tạo xong mới phát hiện dịch vụ vô dụng. `scheduling`
    vẫn kiểm lại một lần nữa cho dịch vụ dài đã nằm sẵn trong CSDL từ trước bản vá.
    """
    if phut is None or phut <= 0:
        raise LoiNghiepVu("Thời lượng phải lớn hơn 0 phút.")
    if phut > PHUT_LAM_VIEC_MOI_NGAY:
        raise LoiNghiepVu(
            f"Thời lượng không được dài hơn một ngày làm việc "
            f"({PHUT_LAM_VIEC_MOI_NGAY} phút) — buổi dài hơn thế không xếp vừa giờ mở cửa."
        )
    return phut


# --- Dịch vụ ---------------------------------------------------------------------


def tao_dich_vu(
    db: Session,
    ma: str,
    ten: str,
    gia: Decimal,
    thoi_luong_phut: int,
    mo_ta: str | None = None,
) -> Service:
    # Chuẩn hóa mã về chữ hoa: gõ "tam" và "TAM" phải là cùng một mã, nếu không sẽ có
    # hai dịch vụ trùng nhau mà ràng buộc UNIQUE không phát hiện được.
    ma = _bat_buoc(ma, "Mã dịch vụ").upper()
    ten = _bat_buoc(ten, "Tên dịch vụ")

    if db.scalar(select(Service).where(Service.code == ma)):
        raise LoiNghiepVu(f"Mã dịch vụ “{ma}” đã tồn tại.")

    s = Service(
        code=ma,
        name=ten,
        price=_kiem_gia(gia),
        duration_min=_kiem_thoi_luong(thoi_luong_phut),
        description=(mo_ta or "").strip() or None,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def sua_dich_vu(db: Session, dich_vu_id: int, **truong) -> Service:
    s = lay_dich_vu(db, dich_vu_id)

    if "ten" in truong:
        s.name = _bat_buoc(truong["ten"], "Tên dịch vụ")
    if "gia" in truong:
        s.price = _kiem_gia(truong["gia"])
    if "thoi_luong_phut" in truong:
        s.duration_min = _kiem_thoi_luong(truong["thoi_luong_phut"])
    if "mo_ta" in truong:
        s.description = (truong["mo_ta"] or "").strip() or None

    db.commit()
    db.refresh(s)
    return s


def lay_dich_vu(db: Session, dich_vu_id: int) -> Service:
    s = db.get(Service, dich_vu_id)
    if s is None:
        raise LoiKhongTimThay("Không tìm thấy dịch vụ.")
    return s


def danh_sach_dich_vu(db: Session) -> list[Service]:
    """Toàn bộ, kể cả đã ngưng bán — quản lý cần thấy để bật lại."""
    return list(db.scalars(select(Service).order_by(Service.name)))


def danh_sach_dang_ban(db: Session) -> list[Service]:
    """Chỉ dịch vụ còn cung cấp. Đây là danh sách form đặt lịch ở P3 sẽ dùng."""
    return list(db.scalars(select(Service).where(Service.is_active).order_by(Service.name)))


def ngung_ban(db: Session, dich_vu_id: int) -> Service:
    """US-09: ngưng bán thay vì xóa, để lịch hẹn và dòng hóa đơn cũ giữ nguyên."""
    s = lay_dich_vu(db, dich_vu_id)
    s.is_active = False
    db.commit()
    db.refresh(s)
    return s


def ban_lai(db: Session, dich_vu_id: int) -> Service:
    s = lay_dich_vu(db, dich_vu_id)
    s.is_active = True
    db.commit()
    db.refresh(s)
    return s


# --- Gói dịch vụ ------------------------------------------------------------------


def tao_goi(
    db: Session,
    ten: str,
    gia: Decimal,
    thanh_phan: dict[int, int],
    mo_ta: str | None = None,
) -> ServicePackage:
    """`thanh_phan` là {mã dịch vụ: số lượt}."""
    ten = _bat_buoc(ten, "Tên gói")
    gia = _kiem_gia(gia)

    if not thanh_phan:
        raise LoiNghiepVu("Gói phải có ít nhất một dịch vụ.")

    goi = ServicePackage(name=ten, price=gia, description=(mo_ta or "").strip() or None)

    for dich_vu_id, so_luong in thanh_phan.items():
        dich_vu = lay_dich_vu(db, dich_vu_id)

        if not dich_vu.is_active:
            # Bán gói chứa dịch vụ không còn cung cấp là hứa với khách thứ không giao được.
            raise LoiNghiepVu(f"Dịch vụ “{dich_vu.name}” đã ngưng bán, không thể đưa vào gói.")

        if so_luong is None or so_luong <= 0:
            raise LoiNghiepVu("Số lượt của mỗi dịch vụ trong gói phải lớn hơn 0.")

        goi.items.append(PackageItem(service_id=dich_vu.id, quantity=so_luong))

    db.add(goi)
    db.commit()
    db.refresh(goi)
    return goi


def lay_goi(db: Session, goi_id: int) -> ServicePackage:
    g = db.get(ServicePackage, goi_id)
    if g is None:
        raise LoiKhongTimThay("Không tìm thấy gói dịch vụ.")
    return g


def danh_sach_goi(db: Session) -> list[ServicePackage]:
    return list(db.scalars(select(ServicePackage).order_by(ServicePackage.name)))


def danh_sach_goi_dang_ban(db: Session) -> list[ServicePackage]:
    return list(
        db.scalars(
            select(ServicePackage).where(ServicePackage.is_active).order_by(ServicePackage.name)
        )
    )


def ngung_ban_goi(db: Session, goi_id: int) -> ServicePackage:
    g = lay_goi(db, goi_id)
    g.is_active = False
    db.commit()
    db.refresh(g)
    return g


def ban_lai_goi(db: Session, goi_id: int) -> ServicePackage:
    g = lay_goi(db, goi_id)
    g.is_active = True
    db.commit()
    db.refresh(g)
    return g
