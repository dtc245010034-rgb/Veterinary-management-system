"""Điểm lấy thời gian duy nhất của hệ thống.

Mọi nơi cần "bây giờ" phải gọi clock.now() thay vì datetime.now(). Nhờ vậy test cố định
được thời gian, và các ca phụ thuộc ngày ở P3 (đặt lịch trong quá khứ) cùng P4 (đến hạn
tiêm trong 30 ngày) viết được ổn định thay vì đổi kết quả theo ngày chạy test.

Theo CLAUDE.md mục 7, thời gian hệ thống là một trong hai ranh giới ngoài duy nhất được
phép thay thế khi test — ranh giới còn lại là API AI.
"""

from contextlib import contextmanager
from datetime import datetime

_moc_co_dinh: datetime | None = None


def now() -> datetime:
    """Thời điểm hiện tại, hoặc mốc đã cố định nếu đang trong freeze()."""
    return _moc_co_dinh if _moc_co_dinh is not None else datetime.now()


@contextmanager
def freeze(moc: datetime):
    """Cố định thời gian trong phạm vi khối with. Chỉ dùng khi test.

    Khôi phục giá trị trước đó khi thoát, kể cả khi có exception, để một test hỏng
    không làm sai lệch những test chạy sau.
    """
    global _moc_co_dinh
    truoc_do = _moc_co_dinh
    _moc_co_dinh = moc
    try:
        yield moc
    finally:
        _moc_co_dinh = truoc_do
