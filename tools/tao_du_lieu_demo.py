"""Dựng CSDL DEMO đầy đủ dữ liệu, tách hẳn khỏi CSDL chính.

Chạy:  .venv/bin/python tools/tao_du_lieu_demo.py            (tạo ./demo.db, xóa bản demo cũ nếu có)
       .venv/bin/python tools/tao_du_lieu_demo.py --out /duong/dan/khac.db

Rồi chạy ứng dụng trên CSDL demo (AI giả, không gọi Gemini, không tốn hạn mức):
       DATABASE_URL=sqlite:///./demo.db AI_PROVIDER=fake .venv/bin/python run.py

Công cụ này KHÔNG bao giờ mở `petcare.db`: nó từ chối nếu đường dẫn đích trùng file đó, và chỉ xóa
đúng file đích. Dữ liệu sinh ngẫu nhiên nhưng cố định hạt giống, nên mỗi lần chạy ra cùng một bộ
(ngày giờ tính lùi/tiến từ lúc chạy). Mọi tài khoản dùng mật khẩu chung `matkhau123`
(hoặc SEED_MAT_KHAU nếu bạn đặt).
"""

import argparse
import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))


def _doc_tham_so() -> Path:
    p = argparse.ArgumentParser(description="Dựng CSDL demo riêng, không đụng petcare.db.")
    p.add_argument("--out", default=str(GOC / "demo.db"), help="file CSDL đích (mặc định ./demo.db)")
    dich = Path(p.parse_args().out).expanduser().resolve()
    if dich.name == "petcare.db" or dich == (GOC / "petcare.db").resolve():
        sys.exit("Từ chối: đây là CSDL chính. Chọn tên file khác (mặc định demo.db).")
    return dich


DICH = _doc_tham_so() if __name__ == "__main__" else GOC / "demo.db"

# Phải đặt trước khi import app: app.db dựng engine ngay lúc import.
os.environ["DATABASE_URL"] = f"sqlite:///{DICH.as_posix()}"
os.environ.setdefault("AI_PROVIDER", "fake")

from sqlalchemy import select  # noqa: E402

import app.models  # noqa: E402,F401
from app.config import MAT_KHAU_MAC_DINH, settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models.ai_log import AiLog  # noqa: E402
from app.models.appointment import Appointment  # noqa: E402
from app.models.care_record import CareRecord  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.link_request import LinkRequest  # noqa: E402
from app.models.owner import Owner  # noqa: E402
from app.models.pet import Pet  # noqa: E402
from app.models.service import Service  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.vaccination import Vaccination  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services import billing, clock, scheduling  # noqa: E402

CHU_NUOI_THEM = [
    ("Nguyễn Minh Anh", "0901000001", [("Lu", "Chó", "Husky", "Đực"), ("Kem", "Mèo", "Ba tư", "Cái")]),
    ("Phạm Gia Bảo", "0901000002", [("Xoài", "Chó", "Phốc sóc", "Cái")]),
    ("Võ Thanh Tâm", "0901000003", [("Mít", "Mèo", "Mèo ta", "Đực"), ("Khoai", "Chó", "Golden", "Đực")]),
    ("Đặng Thu Trang", "0901000004", [("Bơ", "Chó", "Shiba", "Cái")]),
    ("Bùi Quang Huy", "0901000005", [("Sóc Nâu", "Hamster", None, "Đực")]),
    ("Hoàng Mai Linh", "0901000006", [("Tuyết", "Mèo", "Anh lông dài", "Cái"), ("Gấu", "Chó", "Alaska", "Đực")]),
    ("Ngô Đức Long", "0901000007", [("Lucky", "Chó", "Becgie", "Đực")]),
    ("Trương Bích Ngọc", "0901000008", [("Nutella", "Mèo", "Munchkin", "Cái"), ("Mochi", "Mèo", "Mèo ta", "Cái")]),
    ("Lương Văn Phúc", "0901000009", [("Đen", "Chó", "Chó cỏ", "Đực")]),
    ("Đinh Hải Yến", "0901000010", [("Pug", "Chó", "Pug", "Đực"), ("Mimi", "Mèo", "Mèo ta", "Cái")]),
    ("Cao Tuấn Kiệt", "0901000011", [("Sushi", "Mèo", "Scottish Fold", "Đực")]),
    ("Mai Phương Thảo", "0901000012", [("Cún", "Chó", "Poodle", "Cái")]),
]

VAC_XIN = ["Dại", "Care 5 bệnh", "FVRCP", "Lepto", "Bordetella"]
TINH_TRANG = [
    "Lông mượt, da sạch, không có ký sinh.",
    "Lông rối vùng bụng, hơi sợ máy sấy.",
    "Móng dài, tai có ít ráy.",
    "Da hơi khô, nên bổ sung dưỡng lông.",
    "Có cao răng nhẹ, hợp tác tốt.",
    "Rụng lông theo mùa, cần chải thường xuyên.",
]
VIEC_LAM = ["Tắm, sấy", "Tắm, cắt móng", "Cắt tỉa lông, vệ sinh tai", "Spa toàn diện", "Cắt móng, vệ sinh tai"]
LOI_DAN = ["Chải lông mỗi ngày.", "Quay lại sau 4 tuần.", "Theo dõi vùng da khô, báo lại nếu đỏ.", None]

# (email, họ tên, kiểu): kiểu quyết định trạng thái liên kết để demo đủ các nhánh của cổng khách.
KHACH_MAU = [
    ("khach1@demo.test", "Đỗ Thị Hằng", "da_noi:0912345678"),
    ("khach2@demo.test", "Trần Quốc Đạt", "da_noi:0987654321"),
    ("khach3@demo.test", "Nguyễn Minh Anh", "da_noi:0901000001"),
    ("khach4@demo.test", "Lý Thu Hà", "dang_cho:0905112233"),
    ("khach5@demo.test", "Phạm Gia Bảo", "bi_tu_choi:0901000002"),
    ("khach6@demo.test", "Võ Thanh Tâm", "chua_gui:"),
    ("khach7@demo.test", "Đặng Thu Trang", "het_luot_ai:0901000004"),
]

CAU_HOI_AI = [
    ("Mèo nhà em hay liếm lông nhiều, có bình thường không?",
     "Mèo liếm lông để vệ sinh là bình thường. Nếu bé liếm quá nhiều đến rụng lông hoặc đỏ da, bạn nên cho bé gặp bác sĩ thú y để được khám."),
    ("Bao lâu thì nên tắm cho chó một lần?",
     "Thông thường khoảng 2–4 tuần một lần tùy giống và môi trường sống. Nếu da có dấu hiệu bất thường, hãy liên hệ bác sĩ thú y."),
    ("Chó con mấy tháng thì cắt móng được?",
     "Có thể làm quen việc cắt móng từ khi còn nhỏ, nhẹ nhàng và thưởng cho bé. Hãy hỏi nhân viên chăm sóc để được hướng dẫn cụ thể."),
]


def _gio(ngay, gio: int, phut: int = 0) -> datetime:
    return datetime.combine(ngay, datetime.min.time()).replace(hour=gio, minute=phut)


def _them_chu_nuoi_va_thu_cung(db) -> None:
    for ho_ten, sdt, thu in CHU_NUOI_THEM:
        chu = db.scalar(select(Owner).where(Owner.phone == sdt))
        if chu is None:
            chu = Owner(full_name=ho_ten, phone=sdt, address="Hà Nội (dữ liệu demo)")
            db.add(chu)
            db.flush()
        for ten, loai, giong, gioi in thu:
            if db.scalar(select(Pet).where(Pet.owner_id == chu.id, Pet.name == ten)) is None:
                db.add(Pet(owner_id=chu.id, name=ten, species=loai, breed=giong, sex=gioi))
    db.commit()


def _them_lich_su(db, rng: random.Random) -> tuple[int, int, int]:
    """30 ngày lịch đã xong (kèm hồ sơ, hóa đơn đủ mọi trạng thái) + vài lịch đã hủy."""
    thu_cung = list(db.scalars(select(Pet).order_by(Pet.id)))
    dich_vu = list(db.scalars(select(Service).order_by(Service.id)))
    cham_soc = list(db.scalars(select(User).where(User.role == "caretaker").order_by(User.id)))
    le_tan = db.scalar(select(User).where(User.username == "letan"))
    hom_nay = clock.now().date()
    so_lich = so_ho_so = so_hoa_don = 0
    gio_bat_dau = [(8, 30), (10, 30), (13, 0), (15, 0)]  # cách nhau ≥ 2 giờ: không bao giờ trùng

    for lui in range(2, 31):
        ngay = hom_nay - timedelta(days=lui)
        for nv in cham_soc:
            for gio, phut in rng.sample(gio_bat_dau, k=rng.choice([1, 2, 2, 3])):
                dv = rng.choice(dich_vu)
                bd = _gio(ngay, gio, phut)
                lich = Appointment(
                    pet_id=rng.choice(thu_cung).id,
                    service_id=dv.id,
                    staff_id=nv.id,
                    start_at=bd,
                    end_at=bd + timedelta(minutes=dv.duration_min),
                    status="done",
                    created_by=le_tan.id,
                )
                if rng.random() < 0.08:
                    lich.status = "cancelled"
                    lich.cancel_reason = rng.choice(["Chủ nuôi bận đột xuất.", "Thú cưng không khỏe."])
                db.add(lich)
                db.flush()
                so_lich += 1
                if lich.status != "done":
                    continue
                # Lịch `done` chỉ sinh ra qua ghi hồ sơ, nên mỗi lịch đã xong đều có đúng một hồ sơ.
                db.add(
                    CareRecord(
                        appointment_id=lich.id,
                        pet_id=lich.pet_id,
                        staff_id=lich.staff_id,
                        performed_at=lich.start_at,
                        condition_note=rng.choice(TINH_TRANG),
                        actions_taken=rng.choice(VIEC_LAM),
                        next_advice=rng.choice(LOI_DAN),
                    )
                )
                so_ho_so += 1

    db.commit()

    # Hóa đơn đi qua billing để trạng thái do đúng một chỗ quyết. Ngày hóa đơn = ngày buổi chăm sóc.
    da_xong = list(db.scalars(select(Appointment).where(Appointment.status == "done").order_by(Appointment.id)))
    da_co_hd = billing.hoa_don_theo_lich(db, [l.id for l in da_xong])
    for lich in da_xong:
        if lich.id in da_co_hd:
            continue
        if lich.start_at.date() >= hom_nay - timedelta(days=1) or rng.random() < 0.15:
            continue  # chừa buổi gần đây và vài buổi cũ chưa lập hóa đơn để bấm thử "Lập hóa đơn"
        with clock.freeze(lich.end_at):
            hd = billing.lap_hoa_don(db, lich.id)
            kieu = rng.random()
            if kieu < 0.55:
                billing.ghi_nhan_thanh_toan(db, hd.id, hd.total_amount, rng.choice(["cash", "transfer", "card"]))
            elif kieu < 0.75:
                billing.ghi_nhan_thanh_toan(db, hd.id, (hd.total_amount * Decimal("0.5")).quantize(Decimal("1")), "cash")
            elif kieu < 0.80:
                billing.huy_hoa_don(db, hd.id)
        so_hoa_don += 1
    return so_lich, so_ho_so, so_hoa_don


def _them_mui_tiem(db, rng: random.Random) -> int:
    hom_nay = clock.now().date()
    n = 0
    for thu in db.scalars(select(Pet).order_by(Pet.id)):
        if db.scalar(select(Vaccination).where(Vaccination.pet_id == thu.id)) is not None:
            continue
        for ten in rng.sample(VAC_XIN, k=rng.choice([1, 2])):
            tiem = hom_nay - timedelta(days=rng.randint(5, 380))
            db.add(
                Vaccination(
                    pet_id=thu.id,
                    vaccine_name=ten,
                    dose_no=1,
                    given_at=tiem,
                    next_due_at=tiem + timedelta(days=365) if rng.random() < 0.9 else None,
                )
            )
            n += 1
    db.commit()
    return n


def _them_lich_tuong_lai(db, rng: random.Random) -> int:
    """Lịch sắp tới đặt qua đúng scheduling.dat_lich (có kiểm trùng lịch, giờ làm việc)."""
    thu_cung = list(db.scalars(select(Pet).order_by(Pet.id)))
    dich_vu = list(db.scalars(select(Service).order_by(Service.id)))
    cham_soc = list(db.scalars(select(User).where(User.role == "caretaker").order_by(User.id)))
    le_tan = db.scalar(select(User).where(User.username == "letan"))
    hom_nay = clock.now().date()
    n = 0
    for tien in range(1, 8):
        ngay = hom_nay + timedelta(days=tien)
        for nv in cham_soc:
            for gio, phut in rng.sample([(8, 30), (10, 30), (13, 0), (15, 0)], k=rng.choice([1, 2])):
                try:
                    scheduling.dat_lich(
                        db, rng.choice(thu_cung).id, rng.choice(dich_vu).id, nv.id,
                        _gio(ngay, gio, phut), le_tan.id, "Lịch demo",
                    )
                    n += 1
                except Exception:
                    db.rollback()  # trùng với lịch mẫu đã có: bỏ qua, không phải lỗi
    return n


def _them_khach(db, mat_khau: str, rng: random.Random) -> dict[str, int]:
    le_tan = db.scalar(select(User).where(User.username == "letan"))
    bam = hash_password(mat_khau)
    dem = {"khach": 0, "yeu_cau_lien_ket": 0, "lich_cho": 0, "log_ai": 0}
    hom_nay = clock.now().date()
    dich_vu = list(db.scalars(select(Service).order_by(Service.id)))
    cham_soc = list(db.scalars(select(User).where(User.role == "caretaker").order_by(User.id)))

    for email, ten, kieu in KHACH_MAU:
        trang_thai, _, sdt = kieu.partition(":")
        khach = Customer(email=email, full_name=ten, password_hash=bam)
        chu = db.scalar(select(Owner).where(Owner.phone == sdt)) if sdt else None
        if trang_thai in ("da_noi", "het_luot_ai") and chu is not None:
            khach.owner_id = chu.id
        db.add(khach)
        db.flush()
        dem["khach"] += 1

        if trang_thai in ("da_noi", "het_luot_ai") and chu is not None:
            db.add(LinkRequest(customer_id=khach.id, phone=sdt, status="approved", owner_id=chu.id,
                               decided_by=le_tan.id, decided_at=clock.now() - timedelta(days=3)))
            dem["yeu_cau_lien_ket"] += 1
        elif trang_thai == "dang_cho":
            db.add(LinkRequest(customer_id=khach.id, phone=sdt, note="Mình là chủ của bé Bông và bé Sữa ạ."))
            dem["yeu_cau_lien_ket"] += 1
        elif trang_thai == "bi_tu_choi":
            db.add(LinkRequest(customer_id=khach.id, phone=sdt, status="rejected", decided_by=le_tan.id,
                               decided_at=clock.now() - timedelta(days=1),
                               reject_reason="Số điện thoại chưa khớp hồ sơ nào. Vui lòng gửi lại kèm tên thú cưng."))
            dem["yeu_cau_lien_ket"] += 1
    db.commit()

    # Lịch chờ duyệt do khách xin (đi qua đúng đường của cổng khách).
    for email, so_lich in (("khach1@demo.test", 2), ("khach2@demo.test", 1), ("khach3@demo.test", 1)):
        khach = db.scalar(select(Customer).where(Customer.email == email))
        thu_cua_khach = list(db.scalars(select(Pet).where(Pet.owner_id == khach.owner_id).order_by(Pet.id)))
        for i in range(so_lich):
            ngay = hom_nay + timedelta(days=2 + i)
            try:
                scheduling.tao_yeu_cau_lich(
                    db, khach.id, thu_cua_khach[i % len(thu_cua_khach)].id, rng.choice(dich_vu).id,
                    rng.choice(cham_soc).id, _gio(ngay, 9 + i * 2), "Xin lịch từ cổng khách (demo)",
                )
                dem["lich_cho"] += 1
            except Exception:
                db.rollback()

    # Log AI: khách 1 đã hỏi 3 câu; khách 7 đã dùng hết hạn mức trong ngày (để thấy cảnh báo 429).
    khach1 = db.scalar(select(Customer).where(Customer.email == "khach1@demo.test"))
    for hoi, dap in CAU_HOI_AI:
        db.add(AiLog(customer_id=khach1.id, feature="qa", prompt=hoi, response=dap, model="fake"))
        dem["log_ai"] += 1
    khach7 = db.scalar(select(Customer).where(Customer.email == "khach7@demo.test"))
    for i in range(settings.ai_khach_toi_da_moi_ngay):
        hoi, dap = CAU_HOI_AI[i % len(CAU_HOI_AI)]
        db.add(AiLog(customer_id=khach7.id, feature="qa", prompt=f"{hoi} ({i + 1})", response=dap, model="fake"))
        dem["log_ai"] += 1

    # Log AI của nhân viên (xem ở "Trợ lý AI" / Hạn mức AI).
    quan_ly = db.scalar(select(User).where(User.username == "quanly"))
    db.add(AiLog(user_id=quan_ly.id, feature="reminder",
                 prompt="Soạn tin nhắc lịch tắm cho bé Mực vào 09:00 ngày mai.",
                 response="Chào bạn, nhắc bạn bé Mực có lịch tắm lúc 09:00 ngày mai. Hẹn gặp bạn!", model="fake"))
    db.add(AiLog(user_id=quan_ly.id, feature="summary",
                 prompt="Tóm tắt hồ sơ chăm sóc của bé Mực.",
                 response="Mực da hơi khô, đã tắm và cắt móng định kỳ. Nếu da đỏ hoặc ngứa, hãy hỏi bác sĩ thú y.",
                 model="fake"))
    dem["log_ai"] += 2
    db.commit()
    return dem


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if DICH.exists():
        DICH.unlink()
    for hau_to in ("-wal", "-shm"):
        phu = Path(str(DICH) + hau_to)
        if phu.exists():
            phu.unlink()

    # Nền: tài khoản nhân viên, dịch vụ, gói, 3 chủ nuôi mẫu, lịch/hồ sơ/hóa đơn mẫu của seed chuẩn.
    from app import seed

    seed.main()

    rng = random.Random(20261003)
    mat_khau = settings.seed_mat_khau or MAT_KHAU_MAC_DINH
    with SessionLocal() as db:
        _them_chu_nuoi_va_thu_cung(db)
        so_lich, so_ho_so, so_hoa_don = _them_lich_su(db, rng)
        so_mui = _them_mui_tiem(db, rng)
        so_tuong_lai = _them_lich_tuong_lai(db, rng)
        khach = _them_khach(db, mat_khau, rng)

        tong = {b.__tablename__: db.query(b).count() for b in Base.__subclasses__()}

    print("\n=== DEMO ===")
    print(f"CSDL demo: {DICH}")
    print(f"Thêm: {so_lich} lịch đã qua, {so_ho_so} hồ sơ chăm sóc, {so_hoa_don} hóa đơn, {so_mui} mũi tiêm, "
          f"{so_tuong_lai} lịch sắp tới, {khach['khach']} khách, {khach['yeu_cau_lien_ket']} yêu cầu liên kết, "
          f"{khach['lich_cho']} lịch chờ duyệt, {khach['log_ai']} log AI.")
    print("Số dòng mỗi bảng:", ", ".join(f"{k}={v}" for k, v in sorted(tong.items())))
    print(f"\nMật khẩu chung: {mat_khau}")
    print("Nhân viên: quanly | letan | chamsoc1 | chamsoc2")
    print("Khách (cổng /khach/dang-nhap):")
    for email, ten, kieu in KHACH_MAU:
        print(f"  {email:20} {ten:18} {kieu.split(':')[0]}")
    print(f"\nChạy:  DATABASE_URL=sqlite:///{os.path.relpath(DICH, GOC) if DICH.is_relative_to(GOC) else DICH}"
          " AI_PROVIDER=fake .venv/bin/python run.py")
    engine.dispose()


if __name__ == "__main__":
    main()
