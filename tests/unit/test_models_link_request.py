"""Test cho app/models/link_request.py — bảng link_requests (P9 chặng 4, đợt 4b).

Chạy trên SQLite thật: ràng buộc UNIQUE bán phần và CHECK là của CSDL, mock sẽ không thấy.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.customer import Customer
from app.models.link_request import LinkRequest


def _khach(db, email="khach@example.com") -> Customer:
    k = Customer(email=email, full_name="Nguyen Khach", password_hash="bam")
    db.add(k)
    db.commit()
    return k


def test_yeu_cau_moi_mac_dinh_dang_cho_duyet_va_dien_san_thoi_gian(db):
    k = _khach(db)
    db.add(LinkRequest(customer_id=k.id, phone="0912345678"))
    db.commit()

    yc = db.query(LinkRequest).one()
    assert yc.status == "pending"
    assert yc.created_at is not None
    assert yc.owner_id is None


def test_hai_yeu_cau_dang_cho_cua_mot_khach_bi_csdl_chan(db):
    k = _khach(db)
    db.add(LinkRequest(customer_id=k.id, phone="0912345678"))
    db.commit()

    db.add(LinkRequest(customer_id=k.id, phone="0987654321"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_yeu_cau_da_xu_ly_khong_chan_yeu_cau_moi_va_khach_khac_khong_bi_anh_huong(db):
    k = _khach(db)
    khac = _khach(db, "khac@example.com")
    db.add(LinkRequest(customer_id=k.id, phone="0912345678", status="rejected"))
    db.add(LinkRequest(customer_id=k.id, phone="0912345678", status="rejected"))
    db.add(LinkRequest(customer_id=k.id, phone="0912345678"))
    db.add(LinkRequest(customer_id=khac.id, phone="0912345678"))
    db.commit()

    assert db.query(LinkRequest).count() == 4


def test_trang_thai_la_bi_csdl_chan(db):
    k = _khach(db)
    db.add(LinkRequest(customer_id=k.id, phone="0912345678", status="xong"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_xoa_chu_nuoi_da_gap_lich_su_yeu_cau_thi_yeu_cau_giu_lai_va_mat_ma_ho_so(db):
    from app.models.owner import Owner

    k = _khach(db)
    o = Owner(full_name="Chu Nuoi", phone="0912345678")
    db.add(o)
    db.commit()
    db.add(LinkRequest(customer_id=k.id, phone="0912345678", status="approved", owner_id=o.id))
    db.commit()

    db.delete(o)
    db.commit()

    yc = db.query(LinkRequest).one()
    assert yc.status == "approved"
    assert yc.owner_id is None
