"""Bảng appointments — lịch hẹn chăm sóc.

Theo docs/erd.md. Bảng trung tâm của nghiệp vụ, phục vụ US-10 → US-14, US-21.

Quy tắc chống trùng lịch KHÔNG nằm ở đây — nó không diễn đạt được bằng ràng buộc CSDL vì
phải so sánh khoảng thời gian giữa các bản ghi. Xem app/services/scheduling.py.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services import clock

TRANG_THAI = ("booked", "rescheduled", "cancelled", "done")

TEN_TRANG_THAI = {
    "booked": "Đã đặt",
    "rescheduled": "Đã đổi lịch",
    "cancelled": "Đã hủy",
    "done": "Hoàn thành",
}

# Trạng thái còn chiếm chỗ trong lịch. Lịch đã hủy không tham gia kiểm tra trùng.
TRANG_THAI_CON_HIEU_LUC = ("booked", "rescheduled", "done")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        # Khoảng rỗng hoặc âm sẽ lọt qua mọi phép kiểm tra trùng lịch vì không giao với gì cả.
        CheckConstraint("end_at > start_at", name="ck_appointments_thoi_gian"),
        CheckConstraint(
            "status IN ('booked', 'rescheduled', 'cancelled', 'done')",
            name="ck_appointments_status",
        ),
        # Hai index này phục vụ truy vấn kiểm tra trùng lịch trong scheduling.py.
        Index("ix_appointments_staff_start", "staff_id", "start_at"),
        Index("ix_appointments_pet_start", "pet_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Luôn tính từ start_at + services.duration_min, không cho người dùng nhập tay:
    # thời lượng không khớp dịch vụ sẽ làm sai thống kê ở P6.
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="booked")
    note: Mapped[str | None] = mapped_column(Text)
    cancel_reason: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    pet: Mapped["Pet"] = relationship(lazy="selectin")  # noqa: F821
    service: Mapped["Service"] = relationship(lazy="selectin")  # noqa: F821

    # Hai quan hệ cùng trỏ tới users nên phải nói rõ dùng khóa ngoại nào,
    # nếu không SQLAlchemy không biết chọn cột nào.
    staff: Mapped["User"] = relationship(foreign_keys=[staff_id], lazy="selectin")  # noqa: F821
    nguoi_tao: Mapped["User"] = relationship(foreign_keys=[created_by])  # noqa: F821

    @property
    def ten_trang_thai(self) -> str:
        return TEN_TRANG_THAI.get(self.status, self.status)

    @property
    def con_hieu_luc(self) -> bool:
        return self.status in TRANG_THAI_CON_HIEU_LUC

    def __repr__(self) -> str:
        return f"<Appointment {self.start_at:%d/%m %H:%M}-{self.end_at:%H:%M} {self.status}>"
