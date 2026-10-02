"""Token xác minh email và đặt lại mật khẩu: hết hạn, dùng một lần, chỉ lưu băm.

Chưa có màn hình nào dùng — đăng ký, xác minh và quên mật khẩu là chặng 4 của P9.
"""

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.email_token import MUC_DICH, EmailToken
from app.services import clock
from app.services.errors import LoiNghiepVu

# Link đặt lại mật khẩu là chìa khóa vào tài khoản nên sống ngắn; link xác minh cho người ta thời
# gian ra hộp thư.
HAN_DUNG = {
    "verify_email": timedelta(hours=24),
    "reset_password": timedelta(hours=1),
}

# Một thông điệp cho mọi cách thất bại (không có, sai mục đích, hết hạn, đã dùng): nói rõ cái nào
# thì kẻ đoán token biết được token nào từng tồn tại.
THONG_BAO_SAI = "Liên kết không hợp lệ hoặc đã hết hạn. Hãy yêu cầu gửi lại."


def _bam(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _chuan_hoa_email(email: str) -> str:
    return email.strip().lower()


def cap_token(db: Session, email: str, muc_dich: str) -> str:
    """Tạo token mới cho (email, mục đích) và trả **chuỗi thô** để đưa vào thư.

    Token còn lại chưa dùng của cùng (email, mục đích) bị vô hiệu: bấm "gửi lại" nhiều lần không
    tích lũy các liên kết còn hạn.
    """
    if muc_dich not in MUC_DICH:
        raise ValueError(f"Mục đích token không hợp lệ: {muc_dich!r}")
    email = _chuan_hoa_email(email)
    bay_gio = clock.now()

    db.execute(
        update(EmailToken)
        .where(
            EmailToken.email == email,
            EmailToken.purpose == muc_dich,
            EmailToken.used_at.is_(None),
        )
        .values(used_at=bay_gio)
    )
    token = secrets.token_urlsafe(32)
    db.add(
        EmailToken(
            email=email,
            purpose=muc_dich,
            token_hash=_bam(token),
            expires_at=bay_gio + HAN_DUNG[muc_dich],
        )
    )
    db.commit()
    return token


def dung_token(db: Session, token: str, muc_dich: str) -> str:
    """Tiêu thụ token và trả email của nó. Ném `LoiNghiepVu` nếu sai, sai mục đích, hết hạn hoặc đã dùng.

    Đánh dấu đã dùng bằng **một lệnh** `UPDATE … WHERE used_at IS NULL AND expires_at > now`
    rồi đọc `rowcount`. Đọc dòng, kiểm `used_at`, rồi mới ghi là đua: hai request cùng lúc đều qua.
    """
    bay_gio = clock.now()
    ket_qua = db.execute(
        update(EmailToken)
        .where(
            EmailToken.token_hash == _bam(token),
            EmailToken.purpose == muc_dich,
            EmailToken.used_at.is_(None),
            EmailToken.expires_at > bay_gio,
        )
        .values(used_at=bay_gio)
    )
    if ket_qua.rowcount != 1:
        db.rollback()
        raise LoiNghiepVu(THONG_BAO_SAI)
    email = db.scalars(select(EmailToken.email).where(EmailToken.token_hash == _bam(token))).one()
    db.commit()
    return email


def con_hieu_luc(db: Session, token: str, muc_dich: str) -> bool:
    """Token còn dùng được không — **chỉ đọc**, không tiêu thụ.

    Để trang `GET` biết nên hiện form hay báo liên kết hỏng. Tuyệt đối không dùng `dung_token` ở `GET`:
    trình quét liên kết của hộp thư mở mọi link trong thư trước người nhận và sẽ đốt token.
    """
    return (
        db.scalar(
            select(EmailToken.id).where(
                EmailToken.token_hash == _bam(token),
                EmailToken.purpose == muc_dich,
                EmailToken.used_at.is_(None),
                EmailToken.expires_at > clock.now(),
            )
        )
        is not None
    )
