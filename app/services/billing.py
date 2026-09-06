"""Nghiệp vụ hóa đơn và thanh toán.

Phục vụ US-19, US-20 — TC-065 → TC-073. Không import fastapi.

Phân quyền (quản lý và lễ tân, theo US-02) nằm ở router như mọi mục khác trong dự án,
nên ở đây không có phép kiểm vai trò.

Bốn chuỗi trạng thái hóa đơn chỉ được viết ở file này và app/models/invoice.py, có phép
canh trong tests/unit/test_architecture.py. Cột `invoices.status` trộn hai loại thông
tin: `unpaid`/`partial`/`paid` suy được 100% từ payments, còn `cancelled` là sự kiện độc
lập. Thứ giữ cho nó không mâu thuẫn là ba luật dưới đây, phải giữ cùng nhau:

1. Chỉ `ghi_nhan_thanh_toan()` tạo bản ghi payments, và nó luôn kết thúc bằng
   `_dat_lai_trang_thai()` trong cùng transaction.
2. Chỉ `huy_hoa_don()` ghi `cancelled`, và nó từ chối khi hóa đơn đã có thanh toán —
   nhờ đó `cancelled` và ba trạng thái tiền loại trừ nhau theo cấu trúc.
3. `trang_thai_tinh_lai()` là định nghĩa chuẩn; test so cột lưu với nó ở từng bước.
"""

from decimal import Decimal

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import HINH_THUC, Payment
from app.services.errors import LoiNghiepVu

# Thứ tự hiện trên màn hình: việc chưa làm xong nằm trên. Hóa đơn đã hủy xuống cuối.
_THU_TU_TRANG_THAI = {"unpaid": 0, "partial": 1, "paid": 2, "cancelled": 3}


def lap_hoa_don(db: Session, lich_id: int, ghi_chu: str | None = None) -> Invoice:
    """Lập hóa đơn cho một lịch hẹn đã hoàn thành — TC-065 → TC-068.

    Dòng hóa đơn CHÉP `name` và `price` của dịch vụ tại thời điểm này thay vì tham chiếu
    lại `services`. Đổi giá tháng sau không được làm đổi con số đã in cho khách tháng
    trước — xem quyết định 2 trong docs/plans/2026-09-06-p5-hoa-don-va-thanh-toan.md.

    `total_amount` tính từ các dòng chứ không nhận từ ngoài: hai nguồn cho cùng một con
    số thì sổ sách lệch mà không ai biết. Cùng luật với `appointments.end_at` ở P3.
    """
    lich = db.get(Appointment, lich_id)
    if lich is None:
        raise LoiNghiepVu("Không tìm thấy lịch hẹn.")

    if lich.status != "done":
        raise LoiNghiepVu(
            "Chỉ lập hóa đơn được cho lịch đã hoàn thành. "
            "Ghi hồ sơ chăm sóc cho buổi này trước đã."
        )

    # Ràng buộc UNIQUE trên appointment_id cũng chặn ca này ở tầng CSDL, nhưng phép kiểm
    # ở đây mới nói được cho người dùng biết hóa đơn cũ nằm ở đâu.
    cu = db.scalar(select(Invoice).where(Invoice.appointment_id == lich.id))
    if cu is not None:
        raise LoiNghiepVu(
            f"Lịch này đã có hóa đơn #{cu.id} ({cu.ten_trang_thai.lower()}). "
            "Mỗi lịch hẹn chỉ một hóa đơn."
        )

    dich_vu = lich.service
    dong = InvoiceItem(
        service_id=dich_vu.id,
        description=dich_vu.name,
        qty=1,
        unit_price=dich_vu.price,
        amount=dich_vu.price,
    )

    hd = Invoice(
        owner_id=lich.pet.owner_id,
        appointment_id=lich.id,
        total_amount=dong.amount,
        status="unpaid",
        note=(ghi_chu or "").strip() or None,
    )
    hd.dong.append(dong)
    db.add(hd)
    db.commit()
    db.refresh(hd)
    return hd


def ghi_nhan_thanh_toan(
    db: Session,
    hoa_don_id: int,
    so_tien: Decimal | None,
    hinh_thuc: str = "cash",
) -> Payment:
    """Ghi một lần khách trả tiền — TC-069 → TC-073.

    Đây là đường DUY NHẤT tạo bản ghi payments, và nó luôn cập nhật lại `status` trong
    cùng transaction. Thêm một đường khác mà quên bước đó thì cột trạng thái và số tiền
    thật lệch nhau âm thầm.
    """
    hd = lay_hoa_don(db, hoa_don_id)

    if hd.status == "cancelled":
        raise LoiNghiepVu("Hóa đơn đã hủy nên không ghi nhận thanh toán được.")

    if so_tien is None:
        raise LoiNghiepVu("Phải nhập số tiền khách trả.")
    if so_tien <= 0:
        raise LoiNghiepVu("Số tiền thanh toán phải lớn hơn 0.")

    if hinh_thuc not in HINH_THUC:
        raise LoiNghiepVu("Hình thức thanh toán không hợp lệ.")

    # Ranh giới là "vượt quá", không phải "bằng": trả đúng nốt số còn nợ là ca thường
    # gặp nhất, chặn nhầm nó thì không hóa đơn nào thu đủ được.
    if so_tien > hd.con_no:
        raise LoiNghiepVu(
            f"Số tiền vượt quá số còn nợ của hóa đơn ({_so(hd.con_no)}đ). "
            "P5 chưa làm nghiệp vụ hoàn tiền."
        )

    p = Payment(amount=so_tien, method=hinh_thuc)
    hd.thanh_toan.append(p)
    db.flush()  # để hd.da_tra tính được cả lần trả vừa thêm

    _dat_lai_trang_thai(hd)
    db.commit()
    db.refresh(p)
    return p


def huy_hoa_don(db: Session, hoa_don_id: int) -> Invoice:
    """Hủy hóa đơn lập nhầm. Đây là đường DUY NHẤT ghi trạng thái `cancelled`.

    Từ chối khi đã có thanh toán: cho phép thì sẽ tồn tại hóa đơn vừa `cancelled` vừa có
    tiền, và không ai trả lời được "hóa đơn này thu được bao nhiêu".

    Giới hạn đã biết, không giấu: cửa hàng thật gặp ca "khách trả rồi nhưng hủy dịch vụ".
    Làm hoàn tiền tử tế cần thêm bảng và nằm ngoài đề bài — xem quyết định 4+6 trong kế
    hoạch P5.
    """
    hd = lay_hoa_don(db, hoa_don_id)

    if hd.status == "cancelled":
        raise LoiNghiepVu("Hóa đơn này đã hủy rồi.")

    if hd.thanh_toan:
        raise LoiNghiepVu(
            f"Hóa đơn đã có thanh toán ({_so(hd.da_tra)}đ) nên không hủy được. "
            "Hệ thống chưa làm nghiệp vụ hoàn tiền."
        )

    hd.status = "cancelled"
    db.commit()
    db.refresh(hd)
    return hd


def trang_thai_tinh_lai(hd: Invoice) -> str:
    """Trạng thái suy lại từ payments — định nghĩa chuẩn của cột `invoices.status`.

    `cancelled` không suy được từ đâu nên được trả về nguyên vẹn; nó chỉ tồn tại khi
    hóa đơn chưa có đồng nào, nên không bao giờ tranh chấp với ba giá trị còn lại.
    """
    if hd.status == "cancelled":
        return "cancelled"
    if hd.da_tra >= hd.total_amount:
        return "paid"
    if hd.da_tra > 0:
        return "partial"
    return "unpaid"


def danh_sach(db: Session) -> list[Invoice]:
    """Mọi hóa đơn, hóa đơn chưa thu xong lên đầu, mới lập lên trước."""
    thu_tu = case(_THU_TU_TRANG_THAI, value=Invoice.status, else_=9)
    return list(
        db.scalars(
            select(Invoice).order_by(thu_tu, Invoice.issued_at.desc(), Invoice.id.desc())
        )
    )


def lay_hoa_don(db: Session, hoa_don_id: int) -> Invoice:
    hd = db.get(Invoice, hoa_don_id)
    if hd is None:
        raise LoiNghiepVu("Không tìm thấy hóa đơn.")
    return hd


def hoa_don_theo_lich(db: Session, lich_ids: list[int]) -> dict[int, Invoice]:
    """Tra hóa đơn của nhiều lịch hẹn một lần — để lưới lịch biết hiện nút nào.

    Trả về dict thay vì hàm tra từng lịch, vì template không được gọi xuống tầng services
    và gọi trong vòng lặp thì mỗi dòng lưới là một truy vấn.
    """
    if not lich_ids:
        return {}
    ds = db.scalars(select(Invoice).where(Invoice.appointment_id.in_(lich_ids)))
    return {hd.appointment_id: hd for hd in ds}


def _dat_lai_trang_thai(hd: Invoice) -> None:
    hd.status = trang_thai_tinh_lai(hd)


def _so(tien: Decimal) -> str:
    """150000 -> '150.000'. Chỉ dùng trong thông báo lỗi tiếng Việt."""
    return f"{tien:,.0f}".replace(",", ".")
