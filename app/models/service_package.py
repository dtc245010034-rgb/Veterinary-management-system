"""Bảng service_packages và package_items — gói dịch vụ.

Theo docs/erd.md. Phục vụ US-08.
"""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.service import Service


class ServicePackage(Base):
    __tablename__ = "service_packages"
    __table_args__ = (CheckConstraint("price >= 0", name="ck_packages_price"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Giá gói là con số do quản lý đặt, thường thấp hơn tổng giá lẻ — đó chính là lý do
    # bán gói. Không tính lại từ thành phần, làm vậy sẽ mất phần chiết khấu.
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    items: Mapped[list["PackageItem"]] = relationship(
        back_populates="package", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def tong_gia_le(self) -> Decimal:
        """Tổng tiền nếu mua lẻ từng dịch vụ. Dùng để so sánh với giá gói (TC-028)."""
        return sum((it.service.price * it.quantity for it in self.items), Decimal("0"))

    @property
    def tiet_kiem(self) -> Decimal:
        """Số tiền khách tiết kiệm được khi mua gói."""
        return self.tong_gia_le - self.price

    def __repr__(self) -> str:
        return f"<ServicePackage {self.name}>"


class PackageItem(Base):
    __tablename__ = "package_items"
    __table_args__ = (
        # Cùng một dịch vụ xuất hiện hai dòng thì số lượng thành mơ hồ — dùng cột
        # quantity để ghi số lượt, không lặp dòng.
        UniqueConstraint("package_id", "service_id", name="uq_package_service"),
        CheckConstraint("quantity > 0", name="ck_package_items_quantity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("service_packages.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    package: Mapped["ServicePackage"] = relationship(back_populates="items")
    service: Mapped["Service"] = relationship(lazy="selectin")
