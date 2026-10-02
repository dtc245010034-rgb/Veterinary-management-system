"""Dữ liệu mà khách được xem sau khi đã nối hồ sơ (P9 chặng 4, đợt 4c).

Đây là **cổng duy nhất** từ cổng khách tới dữ liệu chủ nuôi, thú cưng, lịch hẹn, hóa đơn. Hai luật, đều có
phép canh trong `tests/unit/test_architecture.py`:

1. Mọi hàm public nhận `khach` và đi qua `ma_chu_nuoi` (danh sách) hoặc `yeu_cau_so_huu` (theo id).
2. Id của người khác và id không tồn tại cho **cùng một kết quả** (`LoiKhongTimThay`, tức 404): trả 403 cho
   id của người khác là xác nhận cho kẻ dò rằng id đó có thật.

Chỉ mở: thú cưng (kèm lịch sử tiêm), lịch hẹn, hóa đơn. KHÔNG mở hồ sơ chăm sóc: đó là ghi chú nội bộ của nhân
viên. Template chỉ đọc đúng các trường nêu trong từng trang; `note`, `cancel_reason`, tên nhân viên không hiện.

Không import fastapi.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.pet import Pet
from app.models.vaccination import Vaccination
from app.services.errors import LoiKhongTimThay

LOI_KHONG_THAY = "Không tìm thấy mục này trong hồ sơ của bạn."


@dataclass
class ChiTietThuCung:
    thu_cung: Pet
    tiem_phong: list[Vaccination]


def ma_chu_nuoi(khach: Customer) -> int | None:
    """Hồ sơ chủ nuôi của khách, hoặc None nếu chưa được lễ tân nối (khi đó khách không thấy gì)."""
    return khach.owner_id


def yeu_cau_so_huu(khach: Customer, ban_ghi) -> None:
    """Điểm chặn duy nhất: ném `LoiKhongTimThay` nếu `ban_ghi` không thuộc chủ nuôi mà khách được nối.

    `ban_ghi` có `owner_id` (thú cưng, hóa đơn) hoặc đi qua `pet` (lịch hẹn, tiêm phòng, hồ sơ chăm sóc).
    """
    chu = ban_ghi.owner_id if hasattr(ban_ghi, "owner_id") else ban_ghi.pet.owner_id
    da_noi = ma_chu_nuoi(khach)
    if da_noi is None or chu != da_noi:
        raise LoiKhongTimThay(LOI_KHONG_THAY)


def danh_sach_thu_cung(db: Session, khach: Customer) -> list[Pet]:
    chu = ma_chu_nuoi(khach)
    if chu is None:
        return []
    return list(db.scalars(select(Pet).where(Pet.owner_id == chu).order_by(Pet.name, Pet.id)))


def chi_tiet_thu_cung(db: Session, khach: Customer, thu_cung_id: int) -> ChiTietThuCung:
    thu_cung = db.get(Pet, thu_cung_id)
    if thu_cung is None:
        raise LoiKhongTimThay(LOI_KHONG_THAY)
    yeu_cau_so_huu(khach, thu_cung)
    tiem = db.scalars(
        select(Vaccination).where(Vaccination.pet_id == thu_cung.id).order_by(Vaccination.given_at.desc(), Vaccination.id.desc())
    )
    return ChiTietThuCung(thu_cung, list(tiem))


def danh_sach_lich_hen(db: Session, khach: Customer) -> list[Appointment]:
    chu = ma_chu_nuoi(khach)
    if chu is None:
        return []
    return list(
        db.scalars(
            select(Appointment)
            .join(Pet, Pet.id == Appointment.pet_id)
            .where(Pet.owner_id == chu)
            .order_by(Appointment.start_at.desc(), Appointment.id.desc())
        )
    )


def danh_sach_hoa_don(db: Session, khach: Customer) -> list[Invoice]:
    chu = ma_chu_nuoi(khach)
    if chu is None:
        return []
    return list(
        db.scalars(select(Invoice).where(Invoice.owner_id == chu).order_by(Invoice.issued_at.desc(), Invoice.id.desc()))
    )


def chi_tiet_hoa_don(db: Session, khach: Customer, hoa_don_id: int) -> Invoice:
    hoa_don = db.get(Invoice, hoa_don_id)
    if hoa_don is None:
        raise LoiKhongTimThay(LOI_KHONG_THAY)
    yeu_cau_so_huu(khach, hoa_don)
    return hoa_don
