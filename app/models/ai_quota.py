"""Bảng ai_quota — lượt đã dùng và trạng thái của từng model Gemini trong một ngày quota.

Gói miễn phí giới hạn số lượt mỗi ngày cho từng model, và quota reset theo **giờ Pacific**
chứ không theo nửa đêm giờ Việt Nam. Mỗi dòng là một cặp (model, ngày quota).

VÌ SAO LƯU XUỐNG CSDL chứ không giữ trong bộ nhớ: lệnh `python -m app.ai.quota` và tiến
trình uvicorn là hai tiến trình khác nhau, phải thấy cùng một con số. Giữ trong bộ nhớ thì
bảng quota in ra ở CLI luôn bằng 0, và khởi động lại server là quên mất model đang bị chặn.
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AiQuota(Base):
    __tablename__ = "ai_quota"
    __table_args__ = (
        UniqueConstraint("model", "quota_day", name="uq_ai_quota_model_ngay"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model: Mapped[str] = mapped_column(String(60), nullable=False)

    # Ngày theo múi giờ Pacific — xem app/ai/quota.py.
    quota_day: Mapped[date] = mapped_column(Date, nullable=False)

    # Số lần đã gọi tới model này trong ngày. Chỉ là ƯỚC TÍNH của hệ thống: nó không thấy
    # được lượt gọi từ ứng dụng khác dùng chung khóa API.
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Hạn mức THẬT, học được từ `quotaValue` trong lỗi 429. NULL nghĩa là chưa biết, khi đó
    # màn hình hiện số ước tính kèm dấu ~.
    daily_limit: Mapped[int | None] = mapped_column(Integer)

    # Đã hết lượt ngày: Google đã từ chối bằng 429 loại theo ngày.
    exhausted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Nghỉ tới thời điểm này vì quá tải (503) hoặc hết lượt theo phút.
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime)

    # Lý do model bị loại hẳn (404 — Google đã tắt model). Khác `exhausted`: hết lượt thì
    # mai lại dùng được, model bị tắt thì không.
    disabled_reason: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<AiQuota {self.model} {self.quota_day} {self.request_count}>"
