"""Bảng customers — tài khoản khách hàng của cổng khách (P9 chặng 4).

Theo docs/erd.md. **Bảng riêng, không phải vai trò thứ tư của `users`**: `users.role` có CHECK
trong CSDL mà SQLite không sửa được, và mọi dependency của nhân viên chỉ đọc khóa phiên `user_id`
nên cookie của khách không thể trở thành người dùng nhân viên.

Một dòng chỉ xuất hiện SAU KHI khách xác minh email và tự đặt mật khẩu, nên không có cột
"đã xác minh": có dòng nghĩa là đã xác minh.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.services import clock


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Cùng cơ chế với users.session_version: tăng số này thì mọi cookie cũ của khách hết hiệu lực.
    session_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    # Hồ sơ chủ nuôi đã được lễ tân duyệt nối cho khách này (đợt 4b). NULL = chưa nối, khách chưa thấy dữ liệu nào.
    # UNIQUE: một hồ sơ chủ nuôi chỉ thuộc một tài khoản khách.
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id"), unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    def __repr__(self) -> str:
        return f"<Customer {self.email}>"
