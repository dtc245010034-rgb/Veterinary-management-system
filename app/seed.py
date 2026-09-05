"""Tạo dữ liệu mẫu để chạy thử và demo.

Chạy: python -m app.seed

Chỉ thêm tài khoản còn thiếu, chạy nhiều lần không sinh trùng. Ở các phase sau, chủ nuôi,
thú cưng và dịch vụ mẫu sẽ thêm vào đây.
"""

import sys
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

import app.models  # noqa: F401 — đăng ký mọi bảng trước create_all
from app.db import Base, SessionLocal, engine
from app.models.appointment import Appointment
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.service_package import PackageItem, ServicePackage
from app.models.user import User
from app.security import hash_password
from app.services import clock

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

# (mã, tên, thời lượng phút, giá)
DICH_VU_MAU = [
    ("TAM", "Tắm và sấy", 45, "150000"),
    ("CATMONG", "Cắt móng", 15, "50000"),
    ("CATTIA", "Cắt tỉa lông", 60, "250000"),
    ("VESINHTAI", "Vệ sinh tai", 15, "60000"),
    ("SPA", "Spa toàn diện", 90, "450000"),
]

# (tên gói, giá gói, {mã dịch vụ: số lượt})
GOI_MAU = [
    ("Combo vệ sinh cơ bản", "220000", {"TAM": 1, "CATMONG": 1, "VESINHTAI": 1}),
    ("Combo làm đẹp", "400000", {"TAM": 1, "CATTIA": 1, "CATMONG": 1}),
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

        dich_vu_moi = 0
        for ma, ten, phut, gia in DICH_VU_MAU:
            if db.scalar(select(Service).where(Service.code == ma)):
                continue
            db.add(
                Service(code=ma, name=ten, duration_min=phut, price=Decimal(gia))
            )
            dich_vu_moi += 1
        db.flush()

        goi_moi = 0
        for ten_goi, gia_goi, thanh_phan in GOI_MAU:
            if db.scalar(select(ServicePackage).where(ServicePackage.name == ten_goi)):
                continue
            goi = ServicePackage(name=ten_goi, price=Decimal(gia_goi))
            for ma, so_luot in thanh_phan.items():
                dv = db.scalar(select(Service).where(Service.code == ma))
                goi.items.append(PackageItem(service_id=dv.id, quantity=so_luot))
            db.add(goi)
            goi_moi += 1

        db.flush()

        # Lịch mẫu cho ngày mai, trong giờ làm việc, không trùng nhau.
        # Đặt ở tương lai để không vi phạm quy tắc "không đặt lịch trong quá khứ".
        mai = (clock.now() + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        lich_moi = 0
        if db.scalar(select(Appointment)) is None:
            le_tan = db.scalar(select(User).where(User.username == "letan"))
            cham_soc = list(db.scalars(select(User).where(User.role == "caretaker")))
            thu_cung = list(db.scalars(select(Pet).order_by(Pet.id)))
            dich_vu = db.scalar(select(Service).where(Service.code == "TAM"))

            # Hai nhân viên, mỗi người hai lịch liên tiếp — chính là tình huống mà quy
            # tắc nửa mở [start, end) cho phép và cách cài đặt sai sẽ chặn nhầm.
            for i, nhan_su in enumerate(cham_soc[:2]):
                for j in range(2):
                    if len(thu_cung) <= i * 2 + j:
                        break
                    bat_dau = mai + timedelta(hours=j)
                    db.add(
                        Appointment(
                            pet_id=thu_cung[i * 2 + j].id,
                            service_id=dich_vu.id,
                            staff_id=nhan_su.id,
                            start_at=bat_dau,
                            end_at=bat_dau + timedelta(minutes=dich_vu.duration_min),
                            created_by=le_tan.id,
                        )
                    )
                    lich_moi += 1

        db.commit()

    print(f"Đã thêm {them_moi} tài khoản, {chu_nuoi_moi} chủ nuôi, {thu_cung_moi} thú cưng, "
          f"{dich_vu_moi} dịch vụ, {goi_moi} gói, {lich_moi} lịch hẹn.")
    print(f"Mật khẩu chung của mọi tài khoản: {MAT_KHAU_MAC_DINH}\n")
    for username, full_name, role in TAI_KHOAN_MAU:
        print(f"  {username:10} {role:14} {full_name}")
    print('\nThử tìm kiếm không dấu: gõ "dau do" phải ra "Đậu Đỏ".')


if __name__ == "__main__":
    main()
