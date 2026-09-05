"""Test cho app/models/vaccination.py — bảng vaccinations.

Phục vụ US-17, US-18. Chỉ kiểm ràng buộc thuộc tầng CSDL; quy tắc nghiệp vụ nằm ở
tests/unit/test_vaccinations_service.py.

Ràng buộc "ngày tiêm không ở tương lai" cố ý KHÔNG có ở đây: CHECK của SQLite phải gọi
date('now'), tức bỏ qua app/services/clock.py và test không cố định được thời gian. Nó
nằm ở tầng services, cùng lý do với pets.birth_date.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.owner import Owner
from app.models.pet import Pet
from app.models.vaccination import Vaccination

NGAY_TIEM = date(2026, 3, 1)


@pytest.fixture
def thu_cung(db):
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p = Pet(owner_id=o.id, name="Mực", species="Chó")
    db.add(p)
    db.commit()
    return p


def tao_mui(db, thu_cung, **ghi_de) -> Vaccination:
    truong = dict(
        pet_id=thu_cung.id,
        vaccine_name="Dại",
        dose_no=1,
        given_at=NGAY_TIEM,
        next_due_at=date(2027, 3, 1),
    )
    truong.update(ghi_de)
    v = Vaccination(**truong)
    db.add(v)
    db.commit()
    return v


def test_mui_tiem_hop_le_luu_duoc(db, thu_cung):
    v = tao_mui(db, thu_cung)

    assert v.id is not None
    assert v.given_at == NGAY_TIEM


def test_thieu_ten_vac_xin_thi_bi_chan(db, thu_cung):
    with pytest.raises(IntegrityError):
        tao_mui(db, thu_cung, vaccine_name=None)


def test_thieu_ngay_tiem_thi_bi_chan(db, thu_cung):
    with pytest.raises(IntegrityError):
        tao_mui(db, thu_cung, given_at=None)


def test_pet_id_khong_co_that_thi_bi_khoa_ngoai_chan(db, thu_cung):
    with pytest.raises(IntegrityError):
        tao_mui(db, thu_cung, pet_id=9999)


def test_so_mui_phai_lon_hon_khong(db, thu_cung):
    with pytest.raises(IntegrityError):
        tao_mui(db, thu_cung, dose_no=0)


def test_khong_ghi_so_mui_thi_van_luu_duoc(db, thu_cung):
    """Mũi thứ mấy là thông tin có thể không biết — để trống, không điền bừa số 0."""
    v = tao_mui(db, thu_cung, dose_no=None)

    assert v.dose_no is None


def test_han_nhac_som_hon_ngay_tiem_thi_bi_chan(db, thu_cung):
    """TC-060 ở tầng CSDL. Tầng services chặn trước để có thông báo tiếng Việt."""
    with pytest.raises(IntegrityError):
        tao_mui(db, thu_cung, next_due_at=date(2026, 2, 28))


def test_han_nhac_dung_bang_ngay_tiem_thi_chap_nhan(db, thu_cung):
    """Ranh giới của TC-060 là "sớm hơn", không phải "bằng"."""
    v = tao_mui(db, thu_cung, next_due_at=NGAY_TIEM)

    assert v.next_due_at == NGAY_TIEM


def test_khong_co_han_nhac_thi_van_luu_duoc(db, thu_cung):
    """Mũi tiêm không cần nhắc lại là chuyện có thật, không phải dữ liệu thiếu."""
    v = tao_mui(db, thu_cung, next_due_at=None)

    assert v.next_due_at is None
