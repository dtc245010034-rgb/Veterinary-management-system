"""Băm mật khẩu và kiểm tra mật khẩu.

Dùng bcrypt trực tiếp, không qua passlib: passlib 1.7.4 lỗi tương thích với bcrypt 4.x
trở lên và đã lâu không cập nhật. Hệ thống chỉ cần băm và kiểm tra, nên gọi thẳng bcrypt
là đủ và ít phụ thuộc hơn.
"""

from urllib.parse import urlsplit

import bcrypt

from app.config import settings


def hash_password(mat_khau: str) -> str:
    """Băm mật khẩu kèm salt ngẫu nhiên.

    Salt khiến hai người dùng đặt cùng mật khẩu vẫn có hai chuỗi băm khác nhau.
    """
    if not mat_khau:
        raise ValueError("Mật khẩu không được để trống")

    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(mat_khau.encode("utf-8"), salt).decode("utf-8")


def verify_password(mat_khau: str, chuoi_bam: str) -> bool:
    """Kiểm tra mật khẩu có khớp chuỗi băm không."""
    return bcrypt.checkpw(mat_khau.encode("utf-8"), chuoi_bam.encode("utf-8"))


PHUONG_THUC_GHI = {"POST", "PUT", "PATCH", "DELETE"}


def la_post_cheo_nguon(
    phuong_thuc: str,
    origin: str | None,
    sec_fetch_site: str | None,
    host: str | None,
    origin_tin_cay: str = "",
) -> bool:
    """Yêu cầu ghi này có do trình duyệt gửi từ một trang web KHÁC không (R-2, CSRF)?

    Không có token CSRF; `SameSite=Lax` của cookie chưa đủ khi ứng dụng công khai. Trình duyệt luôn tự
    gắn `Origin` hoặc `Sec-Fetch-Site` vào yêu cầu ghi và trang web không sửa được hai header này.
    Không có cả hai (curl, script, TestClient) thì không phải tấn công bằng trình duyệt nên cho qua.
    `origin_tin_cay` (APP_ORIGIN) là địa chỉ công khai được tin thêm khi proxy đổi `Host`.
    """
    if phuong_thuc.upper() not in PHUONG_THUC_GHI:
        return False
    if sec_fetch_site is not None and sec_fetch_site not in ("same-origin", "none"):
        return True
    if origin is not None:
        if origin_tin_cay and origin.rstrip("/") == origin_tin_cay.rstrip("/"):
            return False
        return urlsplit(origin).netloc != (host or "")
    return False
