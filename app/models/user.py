"""Bảng users — tài khoản nhân viên.

Theo docs/erd.md. Phục vụ US-01 (đăng nhập), US-02 (phân quyền), US-03 (quản lý tài khoản).
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.services import clock

VAI_TRO = ("manager", "receptionist", "caretaker")

TEN_VAI_TRO = {
    "manager": "Quản lý",
    "receptionist": "Lễ tân",
    "caretaker": "Nhân viên chăm sóc",
}


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('manager', 'receptionist', 'caretaker')",
            name="ck_users_role",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Khóa tài khoản thay vì xóa, để hồ sơ chăm sóc và lịch hẹn cũ giữ nguyên (US-03)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    @property
    def ten_vai_tro(self) -> str:
        """Tên vai trò tiếng Việt để hiển thị trên giao diện."""
        return TEN_VAI_TRO.get(self.role, self.role)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
