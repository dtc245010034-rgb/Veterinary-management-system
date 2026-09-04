"""Bảng services — dịch vụ chăm sóc và bảng giá.

Theo docs/erd.md. Phục vụ US-07, US-09, US-10, US-22.
"""

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("duration_min > 0", name="ck_services_duration"),
        CheckConstraint("price >= 0", name="ck_services_price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # P3 dùng cột này để tính appointments.end_at = start_at + duration_min.
    # Thời lượng 0 sẽ tạo lịch hẹn có khoảng thời gian rỗng, lọt qua mọi phép kiểm tra
    # trùng lịch — nên CHECK > 0 chứ không phải >= 0.
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)

    # Numeric chứ KHÔNG phải Float: float là nhị phân, không biểu diễn chính xác được số
    # thập phân (0.1 + 0.2 != 0.3). Với tiền, sai số tích lũy qua từng dòng hóa đơn và
    # cuối kỳ sổ sách lệch mà không lần ra được. Numeric ánh xạ sang decimal.Decimal.
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Ngưng bán thay vì xóa, để lịch hẹn và dòng hóa đơn cũ giữ nguyên (US-09).
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Service {self.code} {self.name}>"
