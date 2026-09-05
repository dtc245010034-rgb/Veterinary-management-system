"""Bảng care_records — hồ sơ chăm sóc sau mỗi buổi dịch vụ.

Theo docs/erd.md. Phục vụ US-15, US-16, và là nguồn dữ liệu chính cho AI tóm tắt hồ sơ
ở P7 (US-25).

Quan hệ 1–1 với lịch hẹn: một lịch hẹn sinh ra tối đa một hồ sơ.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services import clock


class CareRecord(Base):
    __tablename__ = "care_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # UNIQUE là lớp chặn cuối cho TC-055. Tầng services chặn trước để có thông báo
    # tiếng Việt thay vì IntegrityError bay ra thành lỗi 500.
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"), nullable=False, unique=True
    )

    # Sao chép từ lịch hẹn để truy vấn lịch sử của thú cưng không phải join. Luôn suy ra
    # từ appointment, không bao giờ nhận từ form — hai nguồn lệch nhau thì lịch sử sai
    # mà không ai biết.
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)

    # Người THỰC HIỆN buổi chăm sóc, lấy từ appointment.staff_id — không phải người đang
    # đăng nhập. Quản lý ghi hộ thì lịch sử vẫn phải ghi đúng tên nhân viên đã làm.
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Thời điểm buổi chăm sóc diễn ra (= appointment.start_at), không phải lúc bấm nút.
    performed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    condition_note: Mapped[str] = mapped_column(Text, nullable=False)
    actions_taken: Mapped[str | None] = mapped_column(Text)
    next_advice: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    lich_hen: Mapped["Appointment"] = relationship(lazy="selectin")  # noqa: F821
    pet: Mapped["Pet"] = relationship(lazy="selectin")  # noqa: F821
    staff: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<CareRecord lich={self.appointment_id} {self.performed_at:%d/%m %H:%M}>"
