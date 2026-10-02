"""Bảng email_tokens — token xác minh email và đặt lại mật khẩu (P9 chặng 3).

Theo docs/erd.md. Token gắn với **(email, mục đích)** chứ không với tài khoản, vì lúc đăng ký
chưa có tài khoản nào. CSDL chỉ giữ **băm SHA-256**: lộ file `petcare.db` không làm lộ liên kết
còn hạn. Chuỗi thô chỉ tồn tại trong thư gửi đi.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.services import clock

MUC_DICH = ("verify_email", "reset_password")


class EmailToken(Base):
    __tablename__ = "email_tokens"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('verify_email', 'reset_password')", name="ck_email_tokens_purpose"
        ),
        Index("ix_email_tokens_email_purpose", "email", "purpose"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)

    # SHA-256 dạng hex (64 ký tự). UNIQUE để tra bằng chỉ mục.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # NULL = chưa dùng. Đặt bằng một lệnh UPDATE có điều kiện (app/services/email_tokens.py).
    used_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)
