"""Bảng vaccinations — mũi tiêm đã tiêm và hạn nhắc lại.

Theo docs/erd.md. Phục vụ US-17, US-18, và là nguồn dữ liệu cho AI sinh tin nhắn nhắc
tiêm ở P7 (US-24).

Bảng ghi nhận **thông tin**, không phải chỉ định y tế. Lịch tiêm cụ thể do bác sĩ thú y
quyết định — màn hình hiển thị phải ghi rõ điều đó (docs/ai-safety.md).

Ràng buộc "ngày tiêm không được ở tương lai" (US-17, TC-061) cố ý KHÔNG đặt làm CHECK:
CHECK của SQLite sẽ phải gọi date('now'), tức lấy ngày thật của hệ thống và bỏ qua
app/services/clock.py, khiến test không cố định được thời gian. Nó nằm ở tầng services,
cùng lý do với pets.birth_date.
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services import clock


class Vaccination(Base):
    __tablename__ = "vaccinations"
    __table_args__ = (
        CheckConstraint("dose_no IS NULL OR dose_no > 0", name="ck_vaccinations_dose"),
        # Hạn nhắc trước ngày tiêm là dữ liệu vô nghĩa và sẽ làm danh sách đến hạn ở
        # US-18 báo quá hạn ngay từ lúc vừa nhập.
        CheckConstraint(
            "next_due_at IS NULL OR next_due_at >= given_at", name="ck_vaccinations_han_nhac"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False, index=True)

    vaccine_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Mũi thứ mấy — có thể không biết, để trống chứ không điền bừa số 0.
    dose_no: Mapped[int | None] = mapped_column(Integer)

    given_at: Mapped[date] = mapped_column(Date, nullable=False)

    # Nguồn duy nhất của danh sách đến hạn (US-18). Để trống khi mũi này không cần
    # nhắc lại — đó là thông tin thật, không phải dữ liệu thiếu.
    next_due_at: Mapped[date | None] = mapped_column(Date, index=True)

    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    pet: Mapped["Pet"] = relationship(lazy="selectin")  # noqa: F821

    @property
    def qua_han(self) -> bool:
        """Đã qua hạn nhắc tính tới hôm nay — US-18 đòi đánh dấu rõ (TC-063)."""
        return self.next_due_at is not None and self.next_due_at < clock.now().date()

    def __repr__(self) -> str:
        return f"<Vaccination {self.vaccine_name} {self.given_at:%d/%m/%Y}>"
