"""Ranh giới với nhà cung cấp AI: một interface và bộ lỗi đã phân loại.

Cả hệ thống chỉ gọi AI qua `tra_loi(model, system, user, timeout)`. Nhờ vậy `FakeProvider`
thay được `GeminiProvider` trong test mà không cần mạng, và đổi nhà cung cấp chỉ là thêm
một file — xem docs/architecture.md.

VÌ SAO LỖI PHẢI PHÂN LOẠI: cơ chế xoay ca model (app/ai/quota.py) phản ứng khác nhau với
từng loại. Gộp hết vào một `Exception` thì hoặc bỏ oan model cả ngày vì một lỗi nhất thời,
hoặc thử lại vô ích một model đã hết lượt.
"""

from typing import Protocol


class LoiAI(Exception):
    """Gốc của mọi lỗi khi gọi AI. Thông điệp hiển thị thẳng cho người dùng."""


class LoiQuaTai(LoiAI):
    """Model đang quá tải hoặc lời gọi quá hạn chờ (HTTP 5xx, timeout). Thử model khác."""


class LoiKetNoi(LoiQuaTai):
    """Không kết nối được tới máy chủ AI: mất mạng, lỗi DNS, bị từ chối kết nối.

    Khác 503 và timeout ở một điểm: lời gọi **chưa tới server**, nên không được tính lượt
    (luật đếm của app/ai/quota.py). Vẫn là `LoiQuaTai` để luật xoay ca giữ nguyên.
    """


class LoiHetQuota(LoiAI):
    """Hết lượt (HTTP 429).

    `theo_ngay` phân biệt hai loại hạn mức hoàn toàn khác nhau: hết lượt/phút thì nghỉ một
    lát là dùng lại được, hết lượt/ngày thì phải đợi tới khi quota reset. Coi mọi 429 là
    theo ngày sẽ bỏ oan model cho tới nửa đêm giờ Pacific.

    `gioi_han` là con số thật Google trả về trong `quotaValue`, nếu có — hệ thống lưu lại
    để thay cho số ước tính.
    """

    def __init__(
        self,
        thong_diep: str,
        theo_ngay: bool,
        gioi_han: int | None = None,
        thu_lai_sau: int | None = None,
    ):
        super().__init__(thong_diep)
        self.theo_ngay = theo_ngay
        self.gioi_han = gioi_han
        self.thu_lai_sau = thu_lai_sau


class LoiModelKhongCo(LoiAI):
    """Tên model không còn tồn tại (HTTP 404). Google tắt model cũ mà không báo trước."""


class LoiCauHinh(LoiAI):
    """Khóa API sai, thiếu quyền, hoặc request sai định dạng (400, 401, 403).

    Đổi model không cứu được lỗi này, nên gặp nó là dừng xoay ngay.
    """


class AIProvider(Protocol):
    """Một lần gọi tới một model. Không tự thử lại, không tự đổi model.

    Việc chọn model và xử lý hết lượt nằm ở app/ai/quota.py — provider chỉ biết gọi.
    """

    def tra_loi(self, model: str, system: str, user: str, timeout: float) -> str:
        ...
