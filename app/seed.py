"""Tạo dữ liệu mẫu để chạy thử và demo.

Chạy: python -m app.seed

Chỉ thêm tài khoản còn thiếu, chạy nhiều lần không sinh trùng. Ở các phase sau, chủ nuôi,
thú cưng và dịch vụ mẫu sẽ thêm vào đây.
"""

import sys

from sqlalchemy import select

import app.models  # noqa: F401 — đăng ký mọi bảng trước create_all
from app.db import Base, SessionLocal, engine
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.user import User
from app.security import hash_password

MAT_KHAU_MAC_DINH = "matkhau123"

TAI_KHOAN_MAU = [
    ("quanly", "Nguyễn Văn Quản", "manager"),
    ("letan", "Trần Thị Lễ", "receptionist"),
    ("chamsoc1", "Lê Văn Chăm", "caretaker"),
    ("chamsoc2", "Phạm Thị Sóc", "caretaker"),
]

# (họ tên, số điện thoại, [(tên thú cưng, loài, giống)])
# Tên có dấu và có chữ đ để thử ngay được tính năng tìm không dấu.
CHU_NUOI_MAU = [
    ("Đỗ Thị Hằng", "0912345678", [("Mực", "Chó", "Poodle"), ("Mun", "Mèo", "Mèo ta")]),
    ("Trần Quốc Đạt", "0987654321", [("Đậu Đỏ", "Mèo", "Anh lông ngắn")]),
    ("Lý Thu Hà", "0905112233", [("Bông", "Chó", "Corgi"), ("Sữa", "Mèo", None)]),
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

        chu_nuoi_moi = 0
        thu_cung_moi = 0
        for ho_ten, sdt, danh_sach_thu in CHU_NUOI_MAU:
            chu_nuoi = db.scalar(select(Owner).where(Owner.phone == sdt))
            if chu_nuoi is None:
                chu_nuoi = Owner(full_name=ho_ten, phone=sdt)
                db.add(chu_nuoi)
                db.flush()
                chu_nuoi_moi += 1

            for ten, loai, giong in danh_sach_thu:
                da_co = db.scalar(
                    select(Pet).where(Pet.owner_id == chu_nuoi.id, Pet.name == ten)
                )
                if da_co is None:
                    db.add(Pet(owner_id=chu_nuoi.id, name=ten, species=loai, breed=giong))
                    thu_cung_moi += 1

        db.commit()

    print(f"Đã thêm {them_moi} tài khoản, {chu_nuoi_moi} chủ nuôi, {thu_cung_moi} thú cưng.")
    print(f"Mật khẩu chung của mọi tài khoản: {MAT_KHAU_MAC_DINH}\n")
    for username, full_name, role in TAI_KHOAN_MAU:
        print(f"  {username:10} {role:14} {full_name}")
    print('\nThử tìm kiếm không dấu: gõ "dau do" phải ra "Đậu Đỏ".')


if __name__ == "__main__":
    main()
