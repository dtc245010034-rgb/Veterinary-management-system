"""Tài khoản khách hàng: đăng ký, đăng nhập, quên mật khẩu (P9 chặng 4, đợt 4a).

Ba quyết định thiết kế, đều có test:

1. Đăng ký khách gồm 3 trường: Email, Tên đăng nhập, Mật khẩu. Tạo tài khoản dùng được ngay, không gửi mã/token.
2. Đăng ký và quên mật khẩu không bao giờ cho biết email có tồn tại hay không trong luồng quên mật khẩu.
   Đăng ký báo lỗi rõ ràng nếu email hoặc tên đăng nhập đã được sử dụng.
3. Mật khẩu đi qua `users.kiem_mat_khau` (tối thiểu 8 ký tự).

Service nhận `mailer` và `goc_duong_dan` từ ngoài; không import `app.mail` hay `app.config`.
Không import fastapi.
"""

import logging
import re

from sqlalchemy import or_, select
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
_TEN_DANG_NHAP = re.compile(r"^[a-z0-9_.]+$")


def _chuan_hoa_email(email: str) -> str:
    email = (email or "").strip().lower()
    if len(email) > 255 or not _EMAIL.match(email):
        raise LoiNghiepVu("Email không hợp lệ.")
    return email


def _chuan_hoa_ten_dang_nhap(ten_dang_nhap: str) -> str:
    tdn = (ten_dang_nhap or "").strip().lower()
    if not (3 <= len(tdn) <= 30) or not _TEN_DANG_NHAP.match(tdn):
        raise LoiNghiepVu("Tên đăng nhập phải từ 3–30 ký tự, chỉ gồm chữ thường, số, dấu gạch dưới hoặc dấu chấm.")
    return tdn


def _gui(mailer: GuiMail, den: str, tieu_de: str, noi_dung: str) -> None:
    """Gửi thư và NUỐT lỗi: báo lỗi chỉ ở nhánh email có thật sẽ lộ email đó có tồn tại."""
    try:
        mailer.gui(den, tieu_de, noi_dung)
    except LoiGuiMail:
        logger.warning("Không gửi được thư %r", tieu_de)


def _tim(db: Session, email: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.email == email))


def _tim_theo_ten_dang_nhap(db: Session, ten_dang_nhap: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.ten_dang_nhap == ten_dang_nhap))


def _tim_theo_dinh_danh(db: Session, dinh_danh: str) -> Customer | None:
    dinh_danh = (dinh_danh or "").strip().lower()
    if not dinh_danh:
        return None
    if "@" in dinh_danh:
        return _tim(db, dinh_danh)
    return _tim_theo_ten_dang_nhap(db, dinh_danh)


# --- Đăng ký ---------------------------------------------------------------------


def dang_ky_truc_tiep(db: Session, email: str, ten_dang_nhap: str, mat_khau: str) -> Customer:
    """Tạo tài khoản khách trực tiếp (3 trường: email, tên đăng nhập, mật khẩu)."""
    email_chuan = _chuan_hoa_email(email)
    tdn_chuan = _chuan_hoa_ten_dang_nhap(ten_dang_nhap)
    kiem_mat_khau(mat_khau)

    if _tim(db, email_chuan) is not None:
        raise LoiNghiepVu("Email này đã được sử dụng.")
    if _tim_theo_ten_dang_nhap(db, tdn_chuan) is not None:
        raise LoiNghiepVu("Tên đăng nhập này đã được sử dụng.")

    # Lấy họ tên mặc định từ phần trước @ nếu không có
    ho_ten = tdn_chuan
    khach = Customer(
        email=email_chuan,
        ten_dang_nhap=tdn_chuan,
        full_name=ho_ten,
        password_hash=hash_password(mat_khau),
    )
    db.add(khach)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise LoiNghiepVu("Email hoặc tên đăng nhập đã được sử dụng.") from None
    db.refresh(khach)
    return khach


def yeu_cau_dang_ky(db: Session, mailer: GuiMail, email: str, goc_duong_dan: str) -> None:
    """Gửi thư đăng ký (giữ tương thích route cũ nếu còn dùng)."""
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
    """Dùng liên kết trong thư để tạo tài khoản cũ. Kiểm họ tên và mật khẩu TRƯỚC khi tiêu thụ token."""
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


def xac_thuc(db: Session, email_hoac_ten: str, mat_khau: str) -> Customer:
    """Trả khách nếu đúng email/tên đăng nhập và mật khẩu. Sai cái nào cũng cùng một thông báo."""
    khach = _tim_theo_dinh_danh(db, email_hoac_ten)
    if khach is None or not verify_password(mat_khau, khach.password_hash):
        raise LoiNghiepVu(LOI_DANG_NHAP)
    if not khach.is_active:
        raise LoiNghiepVu(LOI_TAI_KHOAN_KHOA)
    return khach


# --- Quên mật khẩu ---------------------------------------------------------------


def yeu_cau_dat_lai(db: Session, mailer: GuiMail, email: str, goc_duong_dan: str) -> None:
    """Gửi liên kết đặt lại nếu có khách đang hoạt động với email này; nếu không thì im lặng."""
    try:
        email = _chuan_hoa_email(email)
    except LoiNghiepVu:
        return
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
