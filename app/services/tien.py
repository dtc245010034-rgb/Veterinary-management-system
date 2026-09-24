"""Đọc số tiền người dùng gõ vào form.

Tách riêng vì luật này từng nằm **trùng nhau** ở `routers/services.py` (ô Giá) và
`routers/invoices.py` (ô Số tiền). Hai bản chép tay của cùng một luật là cách chắc chắn
để sửa một chỗ quên chỗ kia — và L-03 đúng là lỗi có ở cả hai chỗ.

Hiển thị tiền đi đường khác: filter `tien` trong `app/templates.py`. Ở đây chỉ có chiều
đọc vào.

LUẬT (người dùng chốt 24/09): **chỉ nhận số nguyên đồng.** Dấu chấm, phẩy và khoảng
trắng được coi là phân cách nghìn khi chúng chia chuỗi thành các nhóm đúng 3 chữ số.
Chuỗi có phần lẻ thì **từ chối**, không đoán.

Vì sao không nhận phần lẻ: tiền Việt không dùng phần lẻ, mà `150.000` — cách lễ tân gõ
hằng ngày — thì không có cách nào phân biệt được với "150 phẩy 000". Nhận phần lẻ nghĩa
là chọn hiểu `150.000` thành 150đ. Đổi một ca mơ hồ hiếm gặp lấy một ca mơ hồ phổ biến.
"""

import re
from decimal import Decimal, InvalidOperation

from app.services.errors import LoiNghiepVu

# Số nguyên, có thể âm, các nhóm nghìn cách nhau bởi `.`, `,` hoặc khoảng trắng.
# Nhóm đầu 1–3 chữ số, mọi nhóm sau đúng 3 chữ số. Không phân cách cũng hợp lệ.
_MAU = re.compile(r"^-?(\d{1,3}([.,\s]\d{3})*|\d+)$")

# Chỉ gồm chữ số và ký tự phân cách. Dùng để tách "gõ nhầm chữ" khỏi "số có phần lẻ":
# `abc`, `NaN`, `Infinity` rơi vào loại thứ nhất, `1234.56` rơi vào loại thứ hai.
_MAU_KY_TU_SO = re.compile(r"^-?[\d.,\s]+$")


def doc_tien(chuoi: str | None, ten_truong: str) -> Decimal | None:
    """Trả về `Decimal`, hoặc `None` khi ô để trống.

    `None` chứ không phải 0: tầng nghiệp vụ cần phân biệt "không nhập" với "nhập số 0" —
    hai thông báo lỗi khác nhau, và luật "phải nhập" là nghiệp vụ nên nó ở tầng trên.

    Không đi qua `float`: `Decimal(float)` kéo theo sai số nhị phân ngay từ bước đầu —
    `Decimal(0.1)` cho 0.1000000000000000055511151231257827.
    """
    tho = (chuoi or "").strip()
    if not tho:
        return None

    # Hai loại hỏng khác nhau, hai câu khác nhau. Gộp làm một thì người gõ `1234.56`
    # nhận câu "phải là một số" trong khi họ vừa gõ đúng một con số — và đó chính là
    # kiểu thông báo sai hướng mà L-06 đang phải sửa ở chỗ khác.
    if not _MAU_KY_TU_SO.match(tho):
        raise LoiNghiepVu(f"{ten_truong} phải là một số.")

    if not _MAU.match(tho):
        raise LoiNghiepVu(
            f"{ten_truong} phải là số nguyên bằng đồng, ví dụ 150000 hoặc 150.000. "
            "Không nhận phần lẻ."
        )

    sach = re.sub(r"[.,\s]", "", tho)
    try:
        so = Decimal(sach)
    except InvalidOperation:
        raise LoiNghiepVu(f"{ten_truong} phải là một số.")

    # `Decimal` nhận cả "NaN" và "Infinity"; NaN làm phép so ở tầng nghiệp vụ ném
    # InvalidOperation thành lỗi 500 (rà bằng trình duyệt 11/09). Mẫu ở trên đã loại
    # chúng rồi, nhưng giữ lớp chặn này vì mẫu có thể được nới về sau.
    if not so.is_finite():
        raise LoiNghiepVu(f"{ten_truong} phải là một số.")
    return so
