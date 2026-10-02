"""Nối tài khoản khách với hồ sơ chủ nuôi (P9 chặng 4, đợt 4b).

Ba quyết định, đều có test:

1. **Khách không tự nhận hồ sơ.** Khách chỉ gửi số điện thoại làm gợi ý; lễ tân đối chiếu rồi chọn hồ sơ.
   Tự nối khi số khớp nghĩa là ai biết số của người khác là xem được hồ sơ và hóa đơn của họ.
2. **Gửi yêu cầu không tra bảng `owners`**: khách không dò được số nào là chủ nuôi của cửa hàng.
3. **Có đường gỡ.** Duyệt nhầm thì phải rút lại được ngay; `owner_id` đọc mới từ CSDL ở mỗi request nên
   gỡ có hiệu lực tức thì.

Không import fastapi.
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.link_request import LinkRequest
from app.models.owner import Owner
from app.models.user import User
from app.services import clock
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.services.owners import _kiem_so_dien_thoai, tim_theo_so_dien_thoai

DAI_TOI_DA_GHI_CHU = 500

LOI_DA_NOI = "Tài khoản của bạn đã được liên kết với hồ sơ tại cửa hàng."
LOI_DA_CO_YEU_CAU = "Bạn đã có một yêu cầu đang chờ cửa hàng xử lý."
LOI_DA_XU_LY = "Yêu cầu này đã được xử lý rồi."
LOI_HO_SO_DA_CO_CHU = (
    "Hồ sơ chủ nuôi này đã được liên kết với một tài khoản khách khác. "
    "Nếu liên kết đó sai, hãy gỡ nó trước rồi duyệt lại."
)


@dataclass
class YeuCauCho:
    yeu_cau: LinkRequest
    khach: Customer
    # Hồ sơ chủ nuôi cùng số điện thoại và chưa thuộc tài khoản khách nào: chỉ là gợi ý cho lễ tân.
    ung_vien: list[Owner] = field(default_factory=list)


# --- Phía khách ----------------------------------------------------------------------


def gui_yeu_cau(db: Session, khach: Customer, so_dien_thoai: str, ghi_chu: str | None = None) -> LinkRequest:
    """Khách xin được nối. KHÔNG tra `owners`: kết quả không phụ thuộc số này có là chủ nuôi hay không."""
    if khach.owner_id is not None:
        raise LoiNghiepVu(LOI_DA_NOI)
    so = _kiem_so_dien_thoai(so_dien_thoai)
    ghi_chu = (ghi_chu or "").strip() or None
    if ghi_chu is not None and len(ghi_chu) > DAI_TOI_DA_GHI_CHU:
        raise LoiNghiepVu(f"Ghi chú không được dài quá {DAI_TOI_DA_GHI_CHU} ký tự.")
    if _dang_cho(db, khach.id) is not None:
        raise LoiNghiepVu(LOI_DA_CO_YEU_CAU)

    yeu_cau = LinkRequest(customer_id=khach.id, phone=so, note=ghi_chu)
    db.add(yeu_cau)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise LoiNghiepVu(LOI_DA_CO_YEU_CAU) from None
    db.refresh(yeu_cau)
    return yeu_cau


def yeu_cau_cua_khach(db: Session, khach: Customer) -> LinkRequest | None:
    """Yêu cầu mới nhất của khách (để hiện trạng thái: đang chờ, bị từ chối kèm lý do)."""
    return db.scalar(
        select(LinkRequest).where(LinkRequest.customer_id == khach.id).order_by(LinkRequest.id.desc()).limit(1)
    )


# --- Phía nhân viên ------------------------------------------------------------------


def danh_sach_cho_duyet(db: Session) -> list[YeuCauCho]:
    """Yêu cầu đang chờ, cũ nhất trước, kèm hồ sơ chủ nuôi gợi ý theo số điện thoại."""
    da_co_chu = set(db.scalars(select(Customer.owner_id).where(Customer.owner_id.is_not(None))))
    ket_qua = []
    hang = db.execute(
        select(LinkRequest, Customer)
        .join(Customer, Customer.id == LinkRequest.customer_id)
        .where(LinkRequest.status == "pending")
        .order_by(LinkRequest.id)
    )
    for yeu_cau, khach in hang:
        ung_vien = [o for o in tim_theo_so_dien_thoai(db, yeu_cau.phone) if o.id not in da_co_chu]
        ket_qua.append(YeuCauCho(yeu_cau, khach, ung_vien))
    return ket_qua


def duyet(db: Session, yeu_cau_id: int, owner_id: int, nguoi_duyet: User) -> LinkRequest:
    yeu_cau = _lay_dang_cho(db, yeu_cau_id)
    khach = db.get(Customer, yeu_cau.customer_id)
    if khach.owner_id is not None:
        raise LoiNghiepVu(LOI_DA_NOI)
    if db.get(Owner, owner_id) is None:
        raise LoiKhongTimThay("Không tìm thấy hồ sơ chủ nuôi.")
    if db.scalar(select(Customer.id).where(Customer.owner_id == owner_id)) is not None:
        raise LoiNghiepVu(LOI_HO_SO_DA_CO_CHU)

    khach.owner_id = owner_id
    yeu_cau.status = "approved"
    yeu_cau.owner_id = owner_id
    yeu_cau.decided_by = nguoi_duyet.id
    yeu_cau.decided_at = clock.now()
    try:
        db.commit()
    except IntegrityError:
        # `customers.owner_id` UNIQUE: hai lễ tân cùng duyệt một hồ sơ cho hai khách.
        db.rollback()
        raise LoiNghiepVu(LOI_HO_SO_DA_CO_CHU) from None
    return yeu_cau


def tu_choi(db: Session, yeu_cau_id: int, ly_do: str, nguoi_duyet: User) -> LinkRequest:
    ly_do = (ly_do or "").strip()
    if not ly_do:
        raise LoiNghiepVu("Phải ghi lý do từ chối để khách biết cần bổ sung gì.")
    if len(ly_do) > DAI_TOI_DA_GHI_CHU:
        raise LoiNghiepVu(f"Lý do không được dài quá {DAI_TOI_DA_GHI_CHU} ký tự.")
    yeu_cau = _lay_dang_cho(db, yeu_cau_id)

    yeu_cau.status = "rejected"
    yeu_cau.reject_reason = ly_do
    yeu_cau.decided_by = nguoi_duyet.id
    yeu_cau.decided_at = clock.now()
    db.commit()
    return yeu_cau


def go_lien_ket(db: Session, khach_id: int) -> Customer:
    khach = db.get(Customer, khach_id)
    if khach is None:
        raise LoiKhongTimThay("Không tìm thấy tài khoản khách.")
    if khach.owner_id is None:
        raise LoiNghiepVu("Tài khoản này chưa được liên kết với hồ sơ nào.")
    khach.owner_id = None
    db.commit()
    return khach


def danh_sach_da_lien_ket(db: Session) -> list[tuple[Customer, Owner]]:
    hang = db.execute(
        select(Customer, Owner).join(Owner, Owner.id == Customer.owner_id).order_by(Customer.email)
    )
    return [(khach, chu) for khach, chu in hang]


# --- Nội bộ --------------------------------------------------------------------------


def _dang_cho(db: Session, khach_id: int) -> LinkRequest | None:
    return db.scalar(
        select(LinkRequest).where(LinkRequest.customer_id == khach_id, LinkRequest.status == "pending")
    )


def _lay_dang_cho(db: Session, yeu_cau_id: int) -> LinkRequest:
    yeu_cau = db.get(LinkRequest, yeu_cau_id)
    if yeu_cau is None:
        raise LoiKhongTimThay("Không tìm thấy yêu cầu liên kết.")
    if yeu_cau.status != "pending":
        raise LoiNghiepVu(LOI_DA_XU_LY)
    return yeu_cau
