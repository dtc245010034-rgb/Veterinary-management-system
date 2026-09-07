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
from app.models.care_record import CareRecord
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.service_package import PackageItem, ServicePackage
from app.models.invoice import Invoice
from app.models.user import User
from app.models.vaccination import Vaccination
from app.security import hash_password
from app.services import billing, clock

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


# (chỉ số thú cưng, số ngày trước hôm nay, tình trạng, việc đã làm)
# Mực (chỉ số 0) cố ý có HAI buổi cách nhau gần một tháng: ô smoke "lịch sử mới nhất lên
# đầu" không kiểm được bằng mắt nếu mỗi thú cưng chỉ có đúng một hồ sơ.
HO_SO_MAU = [
    (0, 1, "Da hơi khô ở lưng, tai sạch, răng có cao răng nhẹ.", "Tắm, sấy, vệ sinh tai, cắt móng"),
    (1, 1, "Lông rối vùng bụng, tâm lý hơi sợ máy sấy.", "Tắm, gỡ rối, sấy ở chế độ gió mát"),
    (0, 28, "Móng dài, tai có ít ráy. Cân nặng ổn định.", "Cắt móng, vệ sinh tai"),
]

# Thú cưng có buổi đã qua nhưng CHƯA ghi hồ sơ, để bấm thử được nút "Ghi hồ sơ".
CHUA_GHI_HO_SO = 2

# (chỉ số thú cưng, tên vắc-xin, mũi thứ mấy, ngày tiêm cách hôm nay, hạn nhắc cách hôm nay)
# Bộ này cố ý dựng sẵn đủ bốn trạng thái mà smoke checklist P4 chặng 2 cần nhìn thấy:
# quá hạn, sắp đến hạn, còn xa (không được hiện), và một cặp hai mũi cùng loại vắc-xin để
# thấy luật "chỉ tính mũi mới nhất" — mũi 1 của Mực quá hạn nhưng mũi 2 đã nối tiếp nên
# nó KHÔNG được xuất hiện trong danh sách đến hạn.
MUI_TIEM_MAU = [
    (0, "Dại", 1, -400, -20),
    (0, "Dại", 2, -35, 330),
    (1, "Care 5 bệnh", 2, -180, -5),
    (2, "FVRCP", 1, -60, 12),
    (3, "Dại", 1, -10, 355),
]


# Phần đã trả của hóa đơn lập cho từng buổi đã hoàn thành, theo thứ tự lịch hẹn.
# `None` nghĩa là KHÔNG lập hóa đơn — cố ý chừa lại một buổi để bấm thử được nút
# "Lập hóa đơn", giống cách CHUA_GHI_HO_SO chừa chỗ cho nút "Ghi hồ sơ".
# Buổi được chừa phải là buổi HÔM QUA chứ không phải buổi cách đây một tháng: lưới lịch
# mở theo ngày, để nút ở ngày xa thì người kiểm thử không tìm thấy nó.
# Tỷ lệ chứ không phải số tiền, để đổi bảng giá mẫu không làm hỏng dữ liệu seed.
PHAN_DA_TRA = [Decimal("1"), None, Decimal("0.4")]


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

        # Hai buổi đã xong hôm qua, kèm hồ sơ — để trang chi tiết thú cưng có lịch sử
        # thật ngay sau khi seed, thay vì phải chờ một buổi chăm sóc diễn ra.
        ho_so_moi = 0
        if db.scalar(select(CareRecord)) is None:
            hom_qua = mai - timedelta(days=2)
            le_tan = db.scalar(select(User).where(User.username == "letan"))
            cham_soc = list(db.scalars(select(User).where(User.role == "caretaker")))
            thu_cung = list(db.scalars(select(Pet).order_by(Pet.id)))
            dich_vu = db.scalar(select(Service).where(Service.code == "TAM"))

            for j, (chi_so, cach_ngay, tinh_trang, viec) in enumerate(HO_SO_MAU):
                if len(thu_cung) <= chi_so:
                    break
                bat_dau = hom_qua - timedelta(days=cach_ngay - 1) + timedelta(hours=j)
                lich = Appointment(
                    pet_id=thu_cung[chi_so].id,
                    service_id=dich_vu.id,
                    staff_id=cham_soc[0].id,
                    start_at=bat_dau,
                    end_at=bat_dau + timedelta(minutes=dich_vu.duration_min),
                    status="done",
                    created_by=le_tan.id,
                )
                db.add(lich)
                db.flush()
                db.add(
                    CareRecord(
                        appointment_id=lich.id,
                        pet_id=lich.pet_id,
                        staff_id=lich.staff_id,
                        performed_at=lich.start_at,
                        condition_note=tinh_trang,
                        actions_taken=viec,
                    )
                )
                ho_so_moi += 1

            # Một buổi đã qua nhưng CHƯA ghi hồ sơ. Không có bản ghi kiểu này thì không ai
            # bấm thử được nút "Ghi hồ sơ" — phải đợi một lịch hẹn trôi qua trong thực tế.
            if len(thu_cung) > CHUA_GHI_HO_SO:
                bat_dau = hom_qua + timedelta(hours=len(HO_SO_MAU))
                db.add(
                    Appointment(
                        pet_id=thu_cung[CHUA_GHI_HO_SO].id,
                        service_id=dich_vu.id,
                        staff_id=cham_soc[0].id,
                        start_at=bat_dau,
                        end_at=bat_dau + timedelta(minutes=dich_vu.duration_min),
                        created_by=le_tan.id,
                    )
                )
                lich_moi += 1

        mui_tiem_moi = 0
        if db.scalar(select(Vaccination)) is None:
            hom_nay = clock.now().date()
            thu_cung = list(db.scalars(select(Pet).order_by(Pet.id)))

            for chi_so, ten_vac_xin, mui, cach_tiem, cach_nhac in MUI_TIEM_MAU:
                if len(thu_cung) <= chi_so:
                    break
                db.add(
                    Vaccination(
                        pet_id=thu_cung[chi_so].id,
                        vaccine_name=ten_vac_xin,
                        dose_no=mui,
                        given_at=hom_nay + timedelta(days=cach_tiem),
                        next_due_at=hom_nay + timedelta(days=cach_nhac),
                    )
                )
                mui_tiem_moi += 1

        # Hóa đơn mẫu đi qua đúng app/services/billing.py chứ không dựng model bằng tay:
        # trạng thái hóa đơn chỉ được quyết ở một chỗ, và seed cũng không phải ngoại lệ.
        hoa_don_moi = 0
        if db.scalar(select(Invoice)) is None:
            da_xong = list(
                db.scalars(
                    select(Appointment)
                    .where(Appointment.status == "done")
                    .order_by(Appointment.id)
                )
            )
            for lich, phan in zip(da_xong, PHAN_DA_TRA):
                if phan is None:
                    continue
                hd = billing.lap_hoa_don(db, lich.id)
                billing.ghi_nhan_thanh_toan(db, hd.id, hd.total_amount * phan, "cash")
                hoa_don_moi += 1

        db.commit()

    print(f"Đã thêm {them_moi} tài khoản, {chu_nuoi_moi} chủ nuôi, {thu_cung_moi} thú cưng, "
          f"{dich_vu_moi} dịch vụ, {goi_moi} gói, {lich_moi} lịch hẹn, "
          f"{ho_so_moi} hồ sơ chăm sóc, {mui_tiem_moi} mũi tiêm, {hoa_don_moi} hóa đơn.")
    print(f"Mật khẩu chung của mọi tài khoản: {MAT_KHAU_MAC_DINH}\n")
    for username, full_name, role in TAI_KHOAN_MAU:
        print(f"  {username:10} {role:14} {full_name}")
    print('\nThử tìm kiếm không dấu: gõ "dau do" phải ra "Đậu Đỏ".')


if __name__ == "__main__":
    main()
