"""Bảng link_requests — yêu cầu nối tài khoản khách với hồ sơ chủ nuôi (P9 chặng 4, đợt 4b).

Theo docs/erd.md. Khách KHÔNG tự nhận hồ sơ: khách gửi số điện thoại và ghi chú, lễ tân đối chiếu rồi
chọn hồ sơ nào được nối. `phone` chỉ là gợi ý cho lễ tân, không phải khóa tra cứu tự động.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.services import clock

TRANG_THAI = ("pending", "approved", "rejected")


class LinkRequest(Base):
    __tablename__ = "link_requests"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_link_requests_status"),
        # Mỗi khách tối đa một yêu cầu đang chờ. Kiểm ở service là chưa đủ: hai lượt gửi đồng thời đều thấy "chưa có".
        Index(
            "uq_link_requests_mot_cho_duyet",
            "customer_id",
            unique=True,
            sqlite_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)

    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Chỉ có khi đã duyệt: hồ sơ chủ nuôi mà lễ tân chọn. SET NULL: lịch sử yêu cầu không được chặn việc xóa
    # một hồ sơ chủ nuôi đã gỡ liên kết (còn liên kết thì `customers.owner_id` chặn).
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id", ondelete="SET NULL"))
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    reject_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    def __repr__(self) -> str:
        return f"<LinkRequest #{self.id} khach={self.customer_id} {self.status}>"
