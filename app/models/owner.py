"""Bảng owners — chủ nuôi.

Theo docs/erd.md, thêm cột `search_name` không có trong ERD gốc (xem chú thích bên dưới).
Phục vụ US-04, US-06, US-23.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db import Base
from app.services import clock
from app.services.text import chuan_hoa


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Cố ý KHÔNG đặt UNIQUE: hai người trong cùng gia đình dùng chung một số là chuyện
    # thường. Trùng số chỉ cảnh báo ở tầng nghiệp vụ, không cấm (US-04, TC-015).
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    email: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    # Bản đã bỏ dấu và thường hóa của full_name, dùng cho tìm kiếm không dấu (TC-022).
    # Lưu sẵn thay vì tính lúc truy vấn: tính lúc truy vấn thì SQLite phải quét toàn bảng
    # và không dùng được index. Cột này không có trong ERD gốc — đã ghi bổ sung ở erd.md.
    search_name: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)

    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")  # noqa: F821

    @validates("full_name")
    def _dong_bo_search_name(self, khoa, gia_tri):
        """Cập nhật search_name mỗi khi tên đổi.

        Đặt ở model thay vì bắt từng chỗ gọi phải nhớ điền — quên một chỗ là tra cứu
        trả kết quả cũ mà không báo lỗi gì.
        """
        self.search_name = chuan_hoa(gia_tri or "")
        return gia_tri

    def __repr__(self) -> str:
        return f"<Owner {self.full_name} ({self.phone})>"
