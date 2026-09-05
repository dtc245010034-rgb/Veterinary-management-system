"""Test cho app/models/care_record.py — bảng care_records.

Phục vụ US-15, US-16. Chỉ kiểm ràng buộc thuộc tầng CSDL; quy tắc nghiệp vụ nằm ở
tests/unit/test_care_records_service.py.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.appointment import Appointment
from app.models.care_record import CareRecord
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User

MOC = datetime(2026, 3, 12, 9, 0)


@pytest.fixture
def du_lieu(db):
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p = Pet(owner_id=o.id, name="Mực", species="Chó")
    s = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    nv = User(username="chamsoc1", password_hash="bam", full_name="Lê Văn Chăm", role="caretaker")
    db.add_all([p, s, nv])
    db.commit()

    a = Appointment(
        pet_id=p.id, service_id=s.id, staff_id=nv.id,
        start_at=MOC, end_at=MOC.replace(hour=10), status="booked", created_by=nv.id,
    )
    db.add(a)
    db.commit()

    return {"pet": p, "staff": nv, "lich": a}


def tao_ho_so(db, du_lieu, **ghi_de) -> CareRecord:
    truong = dict(
        appointment_id=du_lieu["lich"].id,
        pet_id=du_lieu["pet"].id,
        staff_id=du_lieu["staff"].id,
        performed_at=MOC,
        condition_note="Da khô nhẹ ở lưng, tai sạch.",
    )
    truong.update(ghi_de)
    hs = CareRecord(**truong)
    db.add(hs)
    db.commit()
    return hs


def test_tao_ho_so_hop_le(db, du_lieu):
    hs = tao_ho_so(db, du_lieu)

    assert hs.id is not None
    assert hs.created_at is not None


def test_moi_lich_hen_chi_mot_ho_so(db, du_lieu):
    """TC-055 ở tầng CSDL: `appointment_id` UNIQUE.

    Tầng services chặn lại lần nữa để có thông báo tiếng Việt; ràng buộc này là lớp chặn
    cuối nếu có đường ghi nào khác quên gọi hàm nghiệp vụ.
    """
    tao_ho_so(db, du_lieu)

    with pytest.raises(IntegrityError):
        tao_ho_so(db, du_lieu)


def test_thieu_ghi_chu_tinh_trang_bi_tu_choi(db, du_lieu):
    """TC-056 ở tầng CSDL: `condition_note` NOT NULL."""
    with pytest.raises(IntegrityError):
        tao_ho_so(db, du_lieu, condition_note=None)


def test_ho_so_phai_gan_voi_lich_hen_co_that(db, du_lieu):
    """Khóa ngoại phải được bật — bài học từ P1."""
    with pytest.raises(IntegrityError):
        tao_ho_so(db, du_lieu, appointment_id=9999)


def test_quan_he_toi_lich_hen_thu_cung_va_nhan_vien(db, du_lieu):
    hs = tao_ho_so(db, du_lieu)

    assert hs.lich_hen.id == du_lieu["lich"].id
    assert hs.pet.name == "Mực"
    assert hs.staff.full_name == "Lê Văn Chăm"
