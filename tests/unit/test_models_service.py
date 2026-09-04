"""Test cho app/models/service.py, service_package.py — dịch vụ, bảng giá, gói.

Phục vụ US-07, US-08, US-09.

Nhóm test về kiểu tiền là quan trọng nhất ở đây: SQLite không có kiểu số thập phân thật,
SQLAlchemy lưu Numeric dưới dạng chuỗi rồi tự chuyển đổi. Nếu chỗ nào đó lỡ dùng float,
sai số sẽ tích lũy qua từng dòng hóa đơn ở P5 và sổ sách lệch mà không lần ra được.
"""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.service import Service
from app.models.service_package import PackageItem, ServicePackage


def tao_dich_vu(db, ma="TAM", ten="Tắm cho chó", gia="150000", phut=45) -> Service:
    s = Service(code=ma, name=ten, price=Decimal(gia), duration_min=phut)
    db.add(s)
    db.commit()
    return s


# --- Kiểu tiền ------------------------------------------------------------------


def test_gia_doc_ra_dung_bang_gia_ghi_vao(db):
    """Không được có sai số làm tròn ở bất kỳ đâu trong đường đi của tiền."""
    s = tao_dich_vu(db, gia="150000.50")
    db.expire_all()

    doc_lai = db.get(Service, s.id)

    assert doc_lai.price == Decimal("150000.50")


def test_gia_la_decimal_khong_phai_float(db):
    """float không biểu diễn chính xác số thập phân — 0.1 + 0.2 != 0.3.

    Test này là chốt chặn: nếu ai đó đổi cột sang Float, nó đỏ ngay thay vì để sai số
    âm thầm tích lũy tới P5.
    """
    s = tao_dich_vu(db, gia="150000.50")

    assert isinstance(s.price, Decimal)


def test_cong_nhieu_gia_khong_sinh_sai_so(db):
    """Ba lần 0,10 phải bằng đúng 0,30 — phép cộng float sẽ ra 0,30000000000000004."""
    tao_dich_vu(db, ma="A", gia="0.10")
    tao_dich_vu(db, ma="B", gia="0.10")
    tao_dich_vu(db, ma="C", gia="0.10")

    tong = sum(s.price for s in db.query(Service).all())

    assert tong == Decimal("0.30")


# --- Ràng buộc services ----------------------------------------------------------


def test_dich_vu_moi_mac_dinh_dang_ban(db):
    s = tao_dich_vu(db)

    assert s.is_active is True


def test_ma_dich_vu_trung_bi_tu_choi(db):
    tao_dich_vu(db, ma="TAM")

    db.add(Service(code="TAM", name="Tắm khác", price=Decimal("100000"), duration_min=30))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("phut", [0, -30])
def test_thoi_luong_khong_duong_bi_tu_choi(db, phut):
    """TC-025. duration_min là thứ P3 dùng để tính giờ kết thúc lịch hẹn.

    Thời lượng 0 sẽ tạo ra lịch hẹn có start_at bằng end_at — một khoảng rỗng lọt qua
    mọi phép kiểm tra trùng lịch.
    """
    db.add(Service(code="X", name="Sai", price=Decimal("100000"), duration_min=phut))

    with pytest.raises(IntegrityError):
        db.commit()


def test_gia_am_bi_tu_choi(db):
    """TC-025."""
    db.add(Service(code="X", name="Sai", price=Decimal("-1000"), duration_min=30))

    with pytest.raises(IntegrityError):
        db.commit()


def test_gia_bang_khong_duoc_chap_nhan(db):
    """Dịch vụ miễn phí là hợp lệ — chỉ số âm mới vô lý."""
    s = tao_dich_vu(db, gia="0")

    assert s.price == Decimal("0")


# --- Gói dịch vụ ------------------------------------------------------------------


def test_tao_goi_voi_cac_dich_vu_thanh_phan(db):
    """TC-027."""
    a = tao_dich_vu(db, ma="TAM", gia="150000")
    b = tao_dich_vu(db, ma="CATMONG", ten="Cắt móng", gia="50000")

    goi = ServicePackage(name="Combo cơ bản", price=Decimal("180000"))
    goi.items = [
        PackageItem(service_id=a.id, quantity=1),
        PackageItem(service_id=b.id, quantity=2),
    ]
    db.add(goi)
    db.commit()

    assert len(goi.items) == 2


def test_mot_dich_vu_chi_xuat_hien_mot_dong_trong_goi(db):
    """Cùng dịch vụ hai dòng thì số lượng thành mơ hồ — dùng cột quantity thay vì lặp dòng."""
    a = tao_dich_vu(db, ma="TAM")
    goi = ServicePackage(name="Gói lỗi", price=Decimal("100000"))
    goi.items = [PackageItem(service_id=a.id, quantity=1), PackageItem(service_id=a.id, quantity=1)]
    db.add(goi)

    with pytest.raises(IntegrityError):
        db.commit()


def test_so_luong_khong_duong_bi_tu_choi(db):
    a = tao_dich_vu(db, ma="TAM")
    goi = ServicePackage(name="Gói lỗi", price=Decimal("100000"))
    goi.items = [PackageItem(service_id=a.id, quantity=0)]
    db.add(goi)

    with pytest.raises(IntegrityError):
        db.commit()


def test_tong_gia_le_tinh_dung_theo_so_luong(db):
    """TC-028: quản lý cần thấy giá lẻ để biết gói giảm bao nhiêu."""
    a = tao_dich_vu(db, ma="TAM", gia="150000")
    b = tao_dich_vu(db, ma="CATMONG", ten="Cắt móng", gia="50000")

    goi = ServicePackage(name="Combo", price=Decimal("180000"))
    goi.items = [
        PackageItem(service_id=a.id, quantity=1),
        PackageItem(service_id=b.id, quantity=2),
    ]
    db.add(goi)
    db.commit()

    # 150000 x 1 + 50000 x 2
    assert goi.tong_gia_le == Decimal("250000")
    assert goi.tiet_kiem == Decimal("70000")
