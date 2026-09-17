"""Bảng ai_logs — nhật ký gọi AI.

Theo docs/erd.md. Phục vụ US-26, US-28 và phần báo cáo cuối kỳ: đây là chỗ chứng minh hệ
thống đã gửi gì sang AI và nhận về gì.

`prompt` lưu ĐÚNG chuỗi đã gửi đi, sau khi lọc dữ liệu cá nhân. Nhờ vậy kiểm US-28 chỉ cần
đọc bảng này, không phải tin vào lời hứa trong tài liệu.
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.services import clock

TINH_NANG = ("reminder", "summary", "qa")

TEN_TINH_NANG = {
    "reminder": "Nhắc lịch",
    "summary": "Tóm tắt hồ sơ",
    "qa": "Hỏi đáp chăm sóc",
}


class AiLog(Base):
    __tablename__ = "ai_logs"
    __table_args__ = (
        CheckConstraint(
            "feature IN ('reminder', 'summary', 'qa')", name="ck_ai_logs_feature"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    feature: Mapped[str] = mapped_column(String(20), nullable=False)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # NULL khi lời gọi lỗi — không có phản hồi nào để lưu.
    response: Mapped[str | None] = mapped_column(Text)
    is_error: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Model đã trả lời. NULL nghĩa là KHÔNG có lời gọi nào đi ra: câu hỏi bị guardrail chặn
    # trước, hoặc thiếu dữ liệu nên hệ thống tự trả lời. Báo cáo guardrail cần biết ca nào
    # do model nào trả lời, vì mỗi model tuân thủ prompt một kiểu.
    model: Mapped[str | None] = mapped_column(String(60))

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=clock.now)

    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821

    @property
    def ten_tinh_nang(self) -> str:
        return TEN_TINH_NANG.get(self.feature, self.feature)

    def __repr__(self) -> str:
        return f"<AiLog #{self.id} {self.feature} {'loi' if self.is_error else 'ok'}>"
