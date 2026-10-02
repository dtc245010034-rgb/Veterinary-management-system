"""Bộ gửi thư giả: ghi lại mọi thư thay vì gửi, và giả lập được lỗi.

Dùng cho toàn bộ test tự động. Cùng vai với `app/ai/fake.py`: ranh giới ngoài được phép thay
khi test (CLAUDE.md mục 7). Không có thư nào ra khỏi tiến trình.
"""

from dataclasses import dataclass, field

from app.mail.provider import LoiGuiMail


@dataclass(frozen=True)
class ThuDaGui:
    den: str
    tieu_de: str
    noi_dung: str


@dataclass
class FakeMailer:
    loi: LoiGuiMail | None = None
    da_gui: list[ThuDaGui] = field(default_factory=list)

    def gui(self, den: str, tieu_de: str, noi_dung: str) -> None:
        if self.loi is not None:
            raise self.loi
        self.da_gui.append(ThuDaGui(den, tieu_de, noi_dung))
