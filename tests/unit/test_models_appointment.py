"""Test cho app/models/appointment.py — bảng appointments.

Phục vụ US-10 → US-14. Chỉ kiểm ràng buộc thuộc tầng CSDL; quy tắc trùng lịch nằm ở
tests/unit/test_scheduling.py vì nó không diễn đạt được bằng ràng buộc CSDL.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.appointment import TRANG_THAI, Appointment
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User

MOC = datetime(2026, 3, 12, 9, 0)


@pytest.fixture
def du_lieu(db):
    """Một chủ nuôi, một thú cưng, một dịch vụ 60 phút, một nhân viên chăm sóc."""
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p = Pet(owner_id=o.id, name="Mực", species="Chó")
    s = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    nv = User(username="chamsoc1", password_hash="bam", full_name="Lê Văn Chăm", role="caretaker")
    lt = User(username="letan", password_hash="bam", full_name="Trần Thị Lễ", role="receptionist")
    db.add_all([p, s, nv, lt])
    db.commit()

    return {"pet": p, "service": s, "staff": nv, "letan": lt}


def tao_lich(db, du_lieu, bat_dau=MOC, phut=60, **ghi_de) -> Appointment:
    a = Appointment(
        pet_id=du_lieu["pet"].id,
        service_id=du_lieu["service"].id,
        staff_id=du_lieu["staff"].id,
        start_at=bat_dau,
        end_at=bat_dau + timedelta(minutes=phut),
        created_by=du_lieu["letan"].id,
        **ghi_de,
    )
    db.add(a)
    db.commit()
    return a


def test_tao_lich_mac_dinh_trang_thai_booked(db, du_lieu):
    a = tao_lich(db, du_lieu)

    assert a.status == "booked"
    assert a.created_at is not None


def test_gio_ket_thuc_phai_sau_gio_bat_dau(db, du_lieu):
    """Khoảng thời gian rỗng hoặc âm sẽ lọt qua mọi phép kiểm tra trùng lịch."""
    db.add(
        Appointment(
            pet_id=du_lieu["pet"].id,
            service_id=du_lieu["service"].id,
            staff_id=du_lieu["staff"].id,
            start_at=MOC,
            end_at=MOC,
            created_by=du_lieu["letan"].id,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("trang_thai", TRANG_THAI)
def test_bon_trang_thai_hop_le_deu_luu_duoc(db, du_lieu, trang_thai):
    a = tao_lich(db, du_lieu, status=trang_thai)

    assert a.status == trang_thai


def test_trang_thai_ngoai_danh_sach_bi_tu_choi(db, du_lieu):
    """Trạng thái sai chính tả sẽ tạo ra lịch không lọt vào bất kỳ bộ lọc nào."""
    with pytest.raises(IntegrityError):
        tao_lich(db, du_lieu, status="dat-roi")


def test_lich_phai_gan_thu_cung_dich_vu_nhan_vien_co_that(db, du_lieu):
    """Khóa ngoại phải hoạt động — SQLite mặc định không kiểm tra."""
    db.add(
        Appointment(
            pet_id=9999,
            service_id=du_lieu["service"].id,
            staff_id=du_lieu["staff"].id,
            start_at=MOC,
            end_at=MOC + timedelta(minutes=60),
            created_by=du_lieu["letan"].id,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_quan_he_doc_duoc_thu_cung_dich_vu_nhan_vien(db, du_lieu):
    a = tao_lich(db, du_lieu)
    db.expire_all()

    doc_lai = db.get(Appointment, a.id)

    assert doc_lai.pet.name == "Mực"
    assert doc_lai.service.name == "Tắm và sấy"
    assert doc_lai.staff.full_name == "Lê Văn Chăm"
