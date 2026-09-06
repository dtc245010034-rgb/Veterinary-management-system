"""Bảng invoices và invoice_items — hóa đơn và các dòng của nó.

Theo docs/erd.md. Phục vụ US-19 → US-22.

Bốn chuỗi trạng thái hóa đơn chỉ được viết ở file này và app/services/billing.py — có
phép canh trong tests/unit/test_architecture.py giữ luật đó. Lý do: `status` vừa cache
lại thứ suy được từ payments (`unpaid`/`partial`/`paid`) vừa ghi một sự kiện độc lập
(`cancelled`); rải chuỗi ra router hay template thì mỗi chỗ tự quyết một kiểu.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services import clock

TRANG_THAI = ("unpaid", "partial", "paid", "cancelled")

TEN_TRANG_THAI = {
    "unpaid": "Chưa thu",
    "partial": "Thu một phần",
    "paid": "Đã thu đủ",
    "cancelled": "Đã hủy",
}


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_invoices_total"),
        CheckConstraint(
            "status IN ('unpaid', 'partial', 'paid', 'cancelled')",
            name="ck_invoices_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)

    # UNIQUE chặn hóa đơn thứ hai cho cùng lịch ở tầng CSDL (US-19, TC-068): phép kiểm
    # trong billing.py có thể thua cuộc đua hai request cùng lúc, ràng buộc thì không.
    # Nullable theo ERD (chỗ cho hóa đơn bán gói ở tương lai), nhưng P5 không có đường
    # nào tạo ra hóa đơn không gắn lịch.
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id"), unique=True
    )

    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    # Numeric chứ không phải Float — cùng lý do đã ghi ở services.price.
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unpaid")
    note: Mapped[str | None] = mapped_column(Text)

    owner: Mapped["Owner"] = relationship(lazy="selectin")  # noqa: F821
    appointment: Mapped["Appointment | None"] = relationship(lazy="selectin")  # noqa: F821

    dong: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )
    thanh_toan: Mapped[list["Payment"]] = relationship(  # noqa: F821
        back_populates="invoice", cascade="all, delete-orphan", lazy="selectin",
        order_by="Payment.paid_at, Payment.id",
    )

    @property
    def da_tra(self) -> Decimal:
        """Tổng tiền khách đã trả. Tính từ payments, KHÔNG lưu thành cột.

        Suy được thì đừng lưu: một cột `paid_amount` sẽ là nguồn sự thật thứ hai, và chỉ
        cần một đường ghi payments quên cập nhật là sổ sách lệch âm thầm.
        """
        return sum((p.amount for p in self.thanh_toan), Decimal("0"))

    @property
    def con_no(self) -> Decimal:
        return self.total_amount - self.da_tra

    @property
    def ten_trang_thai(self) -> str:
        return TEN_TRANG_THAI.get(self.status, self.status)

    def __repr__(self) -> str:
        return f"<Invoice #{self.id} {self.total_amount} {self.status}>"


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_invoice_items_qty"),
        CheckConstraint("unit_price >= 0", name="ck_invoice_items_unit_price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)

    # NULL được, để dòng hóa đơn sống sót khi dịch vụ bị xóa khỏi bảng giá.
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"))

    # description và unit_price được CHÉP vào đây lúc lập hóa đơn, không tham chiếu lại
    # services. Tháng sau quản lý tăng giá thì hóa đơn cũ vẫn giữ nguyên con số đã in
    # cho khách. Đây là quyết định quan trọng nhất của P5 — xem docs/plans/
    # 2026-09-06-p5-hoa-don-va-thanh-toan.md quyết định 2.
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    invoice: Mapped["Invoice"] = relationship(back_populates="dong")

    def __repr__(self) -> str:
        return f"<InvoiceItem {self.description} x{self.qty}>"
