"""Chuẩn hóa chuỗi tiếng Việt để tìm kiếm không dấu.

SQLite không có unaccent như PostgreSQL, và LIKE của nó chỉ bỏ phân biệt hoa thường với
ASCII. Nên hệ thống lưu sẵn bản đã chuẩn hóa vào cột `search_name` và tìm trên cột đó.

Lưu sẵn thay vì tính lúc truy vấn: tính lúc truy vấn thì SQLite phải quét toàn bảng và
không dùng được index, mà tra cứu tại quầy thì phải nhanh.
"""

import re
import unicodedata

# Chữ đ/Đ là ký tự Latin riêng, không phải nguyên âm mang dấu tổ hợp, nên
# unicodedata.normalize("NFD") không tách được gì và nó sẽ sót lại nguyên.
# Đây là ngoại lệ duy nhất của tiếng Việt cần thay tay.
CHU_D = str.maketrans({"đ": "d", "Đ": "d"})


def chuan_hoa(chuoi: str) -> str:
    """Bỏ dấu, thường hóa, gom khoảng trắng thừa.

    "Đậu Đỏ" -> "dau do"   ·   "  Mực \n" -> "muc"
    """
    if not chuoi:
        return ""

    chuoi = chuoi.translate(CHU_D)

    # NFD tách nguyên âm thành ký tự gốc + dấu tổ hợp; lọc bỏ nhóm dấu (Mn).
    chuoi = unicodedata.normalize("NFD", chuoi)
    chuoi = "".join(c for c in chuoi if unicodedata.category(c) != "Mn")

    return re.sub(r"\s+", " ", chuoi).strip().lower()
