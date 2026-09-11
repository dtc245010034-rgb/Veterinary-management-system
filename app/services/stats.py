"""Thống kê lượt dịch vụ, doanh thu, khách quay lại.

Phục vụ US-22, US-23 — TC-076 → TC-081. Không import fastapi. Phân quyền (chỉ quản lý,
theo US-02) nằm ở router như mọi mục khác.

Định nghĩa số liệu do người dùng chốt ngày 11/09 — docs/plans/2026-09-11-p6-thong-ke.md.
Ba con số dùng ba mốc ngày khác nhau, và đó là chủ ý:

- Lượt dịch vụ, khách: theo NGÀY HẸN (`appointments.start_at`), mọi lịch chưa hủy.
- Doanh thu: theo NGÀY THU (`payments.paid_at`) — tiền thực nhận. Nhờ vậy doanh thu kỳ
  đã qua không tự tăng khi khách trả nợ vào kỳ sau.
- Số chưa thu: theo NGÀY LẬP (`invoices.issued_at`), phần còn nợ của hóa đơn lập trong kỳ.

Tính trong Python trên các dòng thuộc kỳ, không gộp nhóm bằng SQL: số còn nợ đã có định
nghĩa chuẩn ở `Invoice.con_no` (hóa đơn đã hủy thì nợ 0). Viết lại luật đó thành SQL là
nguồn sự thật thứ hai, đúng loại lệch âm thầm dự án đang chống. Quy mô một cửa hàng không
cần tốc độ của SQL.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import TRANG_THAI_CON_HIEU_LUC, Appointment
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.service import Service
from app.services import clock
from app.services.errors import LoiNghiepVu

SO_NGAY_KY_MAC_DINH = 30


@dataclass(frozen=True)
class DongDichVu:
    ten: str
    dang_ban: bool
    so_luot: int
    doanh_thu: Decimal


@dataclass(frozen=True)
class ThongKe:
    tu_ngay: date
    den_ngay: date
    so_luot: int
    so_luot_hoan_thanh: int
    doanh_thu: Decimal
    chua_thu: Decimal
    theo_dich_vu: list[DongDichVu]
    so_khach: int
    so_khach_quay_lai: int
    ti_le_quay_lai: Decimal  # phần trăm, một chữ số lẻ


def ky_mac_dinh() -> tuple[date, date]:
    """30 ngày gần nhất, tính cả hôm nay — mở vào mùng 1 vẫn có dữ liệu để xem."""
    hom_nay = clock.now().date()
    return hom_nay - timedelta(days=SO_NGAY_KY_MAC_DINH - 1), hom_nay


def thong_ke(db: Session, tu_ngay: date, den_ngay: date) -> ThongKe:
    """Số liệu của kỳ `[tu_ngay, den_ngay]`, tính cả hai đầu — TC-076 → TC-081."""
    if tu_ngay > den_ngay:
        raise LoiNghiepVu("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")

    # So bằng khoảng nửa mở [đầu ngày đầu, đầu ngày SAU ngày cuối) — cùng quy ước với lịch
    # hẹn. So `<= den_ngay 00:00` sẽ đánh rơi mọi thứ xảy ra trong chính ngày cuối kỳ.
    tu = datetime.combine(tu_ngay, time.min)
    den = datetime.combine(den_ngay + timedelta(days=1), time.min)

    lich = list(
        db.scalars(
            select(Appointment).where(
                Appointment.status.in_(TRANG_THAI_CON_HIEU_LUC),
                Appointment.start_at >= tu,
                Appointment.start_at < den,
            )
        )
    )
    thanh_toan = list(
        db.scalars(select(Payment).where(Payment.paid_at >= tu, Payment.paid_at < den))
    )
    hoa_don = list(
        db.scalars(select(Invoice).where(Invoice.issued_at >= tu, Invoice.issued_at < den))
    )

    luot_theo_dv: dict[int, int] = defaultdict(int)
    for l in lich:
        luot_theo_dv[l.service_id] += 1

    tien_theo_dv: dict[int, Decimal] = defaultdict(Decimal)
    for p in thanh_toan:
        # Mỗi hóa đơn đúng một dòng (quyết định 8 của kế hoạch P5), nên lần trả quy trọn về
        # dịch vụ của dòng đó. Có hóa đơn nhiều dòng thì phải chia tỉ lệ ở đây.
        tien_theo_dv[p.invoice.dong[0].service_id] += p.amount

    # KHÔNG lọc `is_active`: dịch vụ đã ngưng bán vẫn có lượt và tiền trong kỳ cũ, lọc đi
    # là số liệu biến mất khỏi sổ mà không ai biết (việc 5 của roadmap P6).
    ma_dich_vu = set(luot_theo_dv) | set(tien_theo_dv)
    dich_vu = db.scalars(select(Service).where(Service.id.in_(ma_dich_vu)))
    theo_dich_vu = sorted(
        (
            DongDichVu(
                ten=dv.name,
                dang_ban=dv.is_active,
                so_luot=luot_theo_dv.get(dv.id, 0),
                doanh_thu=tien_theo_dv.get(dv.id, Decimal("0")),
            )
            for dv in dich_vu
        ),
        key=lambda d: (-d.doanh_thu, -d.so_luot, d.ten),
    )

    # Khách quay lại tính theo số NGÀY đến, không theo số lượt: chủ mang hai con đi tắm
    # cùng một buổi là một lần đến, không phải khách quen.
    ngay_den: dict[int, set[date]] = defaultdict(set)
    for l in lich:
        ngay_den[l.pet.owner_id].add(l.start_at.date())
    so_khach = len(ngay_den)
    so_khach_quay_lai = sum(1 for ngay in ngay_den.values() if len(ngay) >= 2)
    ti_le = (
        (Decimal(so_khach_quay_lai * 100) / so_khach).quantize(Decimal("0.1"))
        if so_khach
        else Decimal("0.0")  # cùng một chữ số lẻ với nhánh trên: trang hiện "0,0%", không lẫn "0%"
    )

    return ThongKe(
        tu_ngay=tu_ngay,
        den_ngay=den_ngay,
        so_luot=len(lich),
        so_luot_hoan_thanh=sum(1 for l in lich if l.status == "done"),
        doanh_thu=sum((p.amount for p in thanh_toan), Decimal("0")),
        chua_thu=sum((hd.con_no for hd in hoa_don), Decimal("0")),
        theo_dich_vu=theo_dich_vu,
        so_khach=so_khach,
        so_khach_quay_lai=so_khach_quay_lai,
        ti_le_quay_lai=ti_le,
    )
