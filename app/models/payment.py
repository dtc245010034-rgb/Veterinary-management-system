"""Bảng payments — từng lần khách trả tiền.

Theo docs/erd.md. Phục vụ US-20, US-22.

Một hóa đơn có nhiều lần trả (trả góp từng phần), nên đây là bảng con chứ không phải một
cột `paid_amount` trên invoices: chỉ có lưu từng lần trả mới nói được khách trả bao nhiêu
lần, ngày nào, bằng hình thức gì — và doanh thu ở P6 tính trên bảng này.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services import clock

HINH_THUC = ("cash", "transfer", "card")

TEN_HINH_THUC = {
    "cash": "Tiền mặt",
    "transfer": "Chuyển khoản",
    "card": "Thẻ",
}


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        # CHECK > 0 chứ không phải >= 0: bản ghi 0 đồng không nói lên điều gì, còn số âm
        # là cách vô tình dựng nên nghiệp vụ hoàn tiền mà P5 chưa làm (TC-073).
        CheckConstraint("amount > 0", name="ck_payments_amount"),
        CheckConstraint(
            "method IN ('cash', 'transfer', 'card')", name="ck_payments_method"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")

    invoice: Mapped["Invoice"] = relationship(back_populates="thanh_toan")  # noqa: F821

    @property
    def ten_hinh_thuc(self) -> str:
        return TEN_HINH_THUC.get(self.method, self.method)

    def __repr__(self) -> str:
        return f"<Payment {self.amount} {self.method}>"
