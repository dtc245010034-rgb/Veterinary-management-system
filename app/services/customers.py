"""Tài khoản khách hàng: đăng ký, đăng nhập, quên mật khẩu (P9 chặng 4, đợt 4a).

Ba quyết định thiết kế, đều có test:

1. **Khách đặt mật khẩu SAU khi bấm liên kết trong thư**, không phải lúc đăng ký. Cho đặt mật khẩu
   trước rồi mới xác minh thì kẻ lạ đăng ký trước bằng email của nạn nhân, đợi nạn nhân bấm "xác minh",
   là kẻ đó giữ tài khoản mang email của nạn nhân. Cách này cũng không để lại tài khoản "chưa xác minh".
2. **Đăng ký và quên mật khẩu không bao giờ cho biết email có tồn tại hay không**: cùng không ném lỗi,
   cùng nuốt lỗi gửi thư. Người gọi không đoán được ai là khách từ phản hồi.
3. **Mật khẩu đi qua `users.kiem_mat_khau`** như ba đường đặt mật khẩu của nhân viên (M-04).

Service nhận `mailer` và `goc_duong_dan` từ ngoài; không import `app.mail` hay `app.config`.
Không import fastapi.
"""

import logging
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.mail.provider import GuiMail, LoiGuiMail
from app.models.customer import Customer
from app.security import hash_password, verify_password
from app.services import email_tokens
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.services.users import kiem_mat_khau

logger = logging.getLogger("app.customers")

LOI_DANG_NHAP = "Email hoặc mật khẩu không đúng."
LOI_TAI_KHOAN_KHOA = "Tài khoản đã ngưng hoạt động. Vui lòng liên hệ cửa hàng."

# Đủ để chặn xuống dòng và khoảng trắng (đường chèn `Bcc:` vào tiêu đề thư); không cố đoán địa chỉ hợp lệ.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _chuan_hoa_email(email: str) -> str:
    email = (email or "").strip().lower()
    if len(email) > 255 or not _EMAIL.match(email):
        raise LoiNghiepVu("Email không hợp lệ.")
    return email


def _gui(mailer: GuiMail, den: str, tieu_de: str, noi_dung: str) -> None:
    """Gửi thư và NUỐT lỗi: báo lỗi chỉ ở nhánh email có thật sẽ lộ email đó có tồn tại."""
    try:
        mailer.gui(den, tieu_de, noi_dung)
    except LoiGuiMail:
        logger.warning("Không gửi được thư %r", tieu_de)


def _tim(db: Session, email: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.email == email))


# --- Đăng ký ---------------------------------------------------------------------


def yeu_cau_dang_ky(db: Session, mailer: GuiMail, email: str, goc_duong_dan: str) -> None:
    """Gửi thư đăng ký. Email đã có tài khoản thì gửi thư báo (không kèm liên kết đăng ký)."""
    email = _chuan_hoa_email(email)
    if _tim(db, email) is not None:
        _gui(
            mailer,
            email,
            "Bạn đã có tài khoản Petcare",
            "Có người vừa dùng địa chỉ email này để đăng ký, nhưng email này đã có tài khoản.\n"
            f"Nếu là bạn, hãy đăng nhập tại {goc_duong_dan}/khach/dang-nhap "
            f"hoặc đặt lại mật khẩu tại {goc_duong_dan}/khach/quen-mat-khau.\n"
            "Nếu không phải bạn, bạn có thể bỏ qua thư này.",
        )
        return

    token = email_tokens.cap_token(db, email, "verify_email")
    _gui(
        mailer,
        email,
        "Xác minh email để hoàn tất đăng ký Petcare",
        f"Bấm vào liên kết sau để xác minh email và đặt mật khẩu (hiệu lực 24 giờ):\n"
        f"{goc_duong_dan}/khach/dang-ky/{token}\n"
        "Nếu không phải bạn đăng ký, bạn có thể bỏ qua thư này.",
    )


def hoan_tat_dang_ky(db: Session, token: str, full_name: str, mat_khau: str) -> Customer:
    """Dùng liên kết trong thư để tạo tài khoản. Kiểm họ tên và mật khẩu TRƯỚC khi tiêu thụ token."""
    ten = (full_name or "").strip()
    if not ten:
        raise LoiNghiepVu("Họ tên không được để trống.")
    if len(ten) > 100:
        raise LoiNghiepVu("Họ tên quá dài (tối đa 100 ký tự).")
    kiem_mat_khau(mat_khau)

    email = email_tokens.dung_token(db, token, "verify_email")
    khach = Customer(email=email, full_name=ten, password_hash=hash_password(mat_khau))
    db.add(khach)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise LoiNghiepVu(email_tokens.THONG_BAO_SAI) from None
    db.refresh(khach)
    return khach


# --- Đăng nhập -------------------------------------------------------------------


def xac_thuc(db: Session, email: str, mat_khau: str) -> Customer:
    """Trả khách nếu đúng email và mật khẩu. Sai cái nào cũng cùng một thông báo."""
    khach = _tim(db, (email or "").strip().lower())
    if khach is None or not verify_password(mat_khau, khach.password_hash):
        raise LoiNghiepVu(LOI_DANG_NHAP)
    if not khach.is_active:
        raise LoiNghiepVu(LOI_TAI_KHOAN_KHOA)
    return khach


# --- Quên mật khẩu ---------------------------------------------------------------


def yeu_cau_dat_lai(db: Session, mailer: GuiMail, email: str, goc_duong_dan: str) -> None:
    """Gửi liên kết đặt lại nếu có khách đang hoạt động với email này; nếu không thì im lặng."""
    email = _chuan_hoa_email(email)
    khach = _tim(db, email)
    if khach is None or not khach.is_active:
        return
    token = email_tokens.cap_token(db, email, "reset_password")
    _gui(
        mailer,
        email,
        "Đặt lại mật khẩu Petcare",
        f"Bấm vào liên kết sau để đặt mật khẩu mới (hiệu lực 1 giờ):\n"
        f"{goc_duong_dan}/khach/dat-lai/{token}\n"
        "Nếu không phải bạn yêu cầu, hãy bỏ qua thư này — mật khẩu hiện tại vẫn nguyên.",
    )


def dat_lai_mat_khau(db: Session, token: str, mat_khau_moi: str) -> Customer:
    kiem_mat_khau(mat_khau_moi)
    email = email_tokens.dung_token(db, token, "reset_password")
    khach = _tim(db, email)
    if khach is None:
        raise LoiNghiepVu(email_tokens.THONG_BAO_SAI)
    khach.password_hash = hash_password(mat_khau_moi)
    khach.session_version += 1
    db.commit()
    db.refresh(khach)
    return khach


# --- Đổi mật khẩu, thu hồi phiên ---------------------------------------------------


def doi_mat_khau(db: Session, khach: Customer, mat_khau_cu: str, mat_khau_moi: str) -> Customer:
    if not verify_password(mat_khau_cu, khach.password_hash):
        raise LoiNghiepVu("Mật khẩu hiện tại không đúng.")
    kiem_mat_khau(mat_khau_moi)
    khach.password_hash = hash_password(mat_khau_moi)
    khach.session_version += 1
    db.commit()
    db.refresh(khach)
    return khach


def thu_hoi_phien(db: Session, ma_khach: int) -> Customer:
    khach = db.get(Customer, ma_khach)
    if khach is None:
        raise LoiKhongTimThay("Không tìm thấy tài khoản.")
    khach.session_version += 1
    db.commit()
    db.refresh(khach)
    return khach
