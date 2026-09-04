"""Tạo dữ liệu mẫu để chạy thử và demo.

Chạy: python -m app.seed

Chỉ thêm tài khoản còn thiếu, chạy nhiều lần không sinh trùng. Ở các phase sau, chủ nuôi,
thú cưng và dịch vụ mẫu sẽ thêm vào đây.
"""

import sys

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models.user import User
from app.security import hash_password

MAT_KHAU_MAC_DINH = "matkhau123"

TAI_KHOAN_MAU = [
    ("quanly", "Nguyễn Văn Quản", "manager"),
    ("letan", "Trần Thị Lễ", "receptionist"),
    ("chamsoc1", "Lê Văn Chăm", "caretaker"),
    ("chamsoc2", "Phạm Thị Sóc", "caretaker"),
]


def main() -> None:
    # Console Windows mặc định dùng cp1252, không in được tiếng Việt và sẽ ném
    # UnicodeEncodeError. Ép stdout sang UTF-8 để script chạy được trên máy sạch.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        them_moi = 0
        for username, full_name, role in TAI_KHOAN_MAU:
            if db.scalar(select(User).where(User.username == username)):
                continue

            db.add(
                User(
                    username=username,
                    full_name=full_name,
                    role=role,
                    password_hash=hash_password(MAT_KHAU_MAC_DINH),
                )
            )
            them_moi += 1

        db.commit()

    print(f"Đã thêm {them_moi} tài khoản. Mật khẩu chung: {MAT_KHAU_MAC_DINH}")
    for username, full_name, role in TAI_KHOAN_MAU:
        print(f"  {username:10} {role:14} {full_name}")


if __name__ == "__main__":
    main()
