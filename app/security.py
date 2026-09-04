"""Băm mật khẩu và kiểm tra mật khẩu.

Dùng bcrypt trực tiếp, không qua passlib: passlib 1.7.4 lỗi tương thích với bcrypt 4.x
trở lên và đã lâu không cập nhật. Hệ thống chỉ cần băm và kiểm tra, nên gọi thẳng bcrypt
là đủ và ít phụ thuộc hơn.
"""

import bcrypt


def hash_password(mat_khau: str) -> str:
    """Băm mật khẩu kèm salt ngẫu nhiên.

    Salt khiến hai người dùng đặt cùng mật khẩu vẫn có hai chuỗi băm khác nhau.
    """
    if not mat_khau:
        raise ValueError("Mật khẩu không được để trống")

    return bcrypt.hashpw(mat_khau.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(mat_khau: str, chuoi_bam: str) -> bool:
    """Kiểm tra mật khẩu có khớp chuỗi băm không."""
    return bcrypt.checkpw(mat_khau.encode("utf-8"), chuoi_bam.encode("utf-8"))
