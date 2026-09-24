"""Bảng pets — thú cưng.

Theo docs/erd.md, thêm cột `search_name`. Phục vụ US-05, US-06.

Ràng buộc "ngày sinh không được ở tương lai" (TC-018) cố ý KHÔNG đặt làm CHECK của
SQLite. CHECK sẽ phải dùng date('now') — lấy ngày thật của hệ thống, bỏ qua
app/services/clock.py, khiến test không cố định được thời gian. Ràng buộc đó nằm ở
tầng services, nơi dùng clock.now() và test kiểm được ổn định.
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db import Base
from app.services import clock
from app.services.text import chuan_hoa

# Giới tính nhận được. Đặt ở model cùng chỗ với cột `sex`, theo đúng tiền lệ `VAI_TRO`
# của `models/user.py`: template dựng ô chọn từ hằng này, `services/owners.py` kiểm theo
# đúng hằng này. Viết cứng ở ba chỗ là cách chắc chắn để ba chỗ lệch nhau — rà 19/09 cho
# thấy giá trị `hack` lưu được vì không chỗ nào kiểm (L-03).
GIOI_TINH = ("Đực", "Cái")


class Pet(Base):
    __tablename__ = "pets"
    __table_args__ = (
        CheckConstraint("weight_kg IS NULL OR weight_kg > 0", name="ck_pets_weight"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    species: Mapped[str] = mapped_column(String(30), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(50))
    sex: Mapped[str | None] = mapped_column(String(10))
    birth_date: Mapped[date | None] = mapped_column(Date)

    # Để trống khi chưa cân, không phải điền bừa số 0.
    weight_kg: Mapped[float | None] = mapped_column(Float)

    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    search_name: Mapped[str] = mapped_column(String(50), nullable=False, default="", index=True)

    owner: Mapped["Owner"] = relationship(back_populates="pets")  # noqa: F821

    @validates("name")
    def _dong_bo_search_name(self, khoa, gia_tri):
        self.search_name = chuan_hoa(gia_tri or "")
        return gia_tri

    def __repr__(self) -> str:
        return f"<Pet {self.name} ({self.species})>"
