"""Test cho app/models/owner.py và app/models/pet.py.

Phục vụ US-04, US-05. Chỉ kiểm những ràng buộc thuộc về tầng CSDL: NOT NULL, CHECK tĩnh,
khóa ngoại, và cột search_name tự sinh.

Ràng buộc phụ thuộc thời gian (ngày sinh không được ở tương lai) nằm ở tầng services chứ
không phải CHECK của SQLite — xem test_owners_service.py và ghi chú trong kế hoạch P2a.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.owner import Owner
from app.models.pet import Pet


def tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", sdt="0912345678") -> Owner:
    o = Owner(full_name=ho_ten, phone=sdt)
    db.add(o)
    db.commit()
    return o


# --- owners ---------------------------------------------------------------------


def test_tao_chu_nuoi_luu_duoc(db):
    o = tao_chu_nuoi(db)

    assert o.id is not None
    assert o.created_at is not None


def test_search_name_tu_sinh_khi_tao(db):
    """TC-022: cột tìm kiếm phải tự có, không để lập trình viên nhớ điền tay."""
    o = tao_chu_nuoi(db, ho_ten="Nguyễn Văn Quản")

    assert o.search_name == "nguyen van quan"


def test_search_name_cap_nhat_khi_doi_ten(db):
    """Đổi tên mà quên cập nhật cột tìm kiếm thì tra cứu sẽ ra kết quả cũ."""
    o = tao_chu_nuoi(db, ho_ten="Trần Thị Lễ")

    o.full_name = "Trần Thị Lệ"
    db.commit()

    assert o.search_name == "tran thi le"


def test_thieu_ho_ten_bi_tu_choi(db):
    db.add(Owner(full_name=None, phone="0912345678"))

    with pytest.raises(IntegrityError):
        db.commit()


def test_thieu_so_dien_thoai_bi_tu_choi(db):
    db.add(Owner(full_name="Không Số", phone=None))

    with pytest.raises(IntegrityError):
        db.commit()


def test_hai_chu_nuoi_dung_chung_so_dien_thoai_van_luu_duoc(db):
    """TC-015: số trùng chỉ cảnh báo, không cấm.

    Hai người trong cùng gia đình dùng chung một số là chuyện thường. Đặt UNIQUE ở đây
    sẽ chặn đúng tình huống hợp lệ đó.
    """
    tao_chu_nuoi(db, ho_ten="Người Một", sdt="0912345678")
    tao_chu_nuoi(db, ho_ten="Người Hai", sdt="0912345678")

    assert db.query(Owner).count() == 2


# --- pets -----------------------------------------------------------------------


def test_tao_thu_cung_gan_chu_nuoi(db):
    o = tao_chu_nuoi(db)

    p = Pet(owner_id=o.id, name="Mực", species="Chó")
    db.add(p)
    db.commit()

    assert p.owner_id == o.id
    assert p.search_name == "muc"


def test_thu_cung_phai_thuoc_mot_chu_nuoi_co_that(db):
    """Khóa ngoại phải thật sự hoạt động — SQLite mặc định KHÔNG kiểm tra.

    app/db.py bật PRAGMA foreign_keys cho từng kết nối. Test này là thứ phát hiện nếu
    ai đó gỡ dòng đó ra: không có nó, bản ghi mồ côi sẽ lưu được và mọi ràng buộc trong
    ERD trở thành chú thích.
    """
    db.add(Pet(owner_id=9999, name="Mồ Côi", species="Chó"))

    with pytest.raises(IntegrityError):
        db.commit()


def test_xoa_chu_nuoi_con_thu_cung_bi_khoa_ngoai_chan(db):
    """TC-016, lớp chặn cuối. Tầng services chặn trước với thông báo tiếng Việt."""
    o = tao_chu_nuoi(db)
    db.add(Pet(owner_id=o.id, name="Mực", species="Chó"))
    db.commit()

    db.delete(o)
    with pytest.raises(IntegrityError):
        db.commit()


def test_can_nang_am_bi_tu_choi(db):
    """TC-019."""
    o = tao_chu_nuoi(db)
    db.add(Pet(owner_id=o.id, name="Mực", species="Chó", weight_kg=-1))

    with pytest.raises(IntegrityError):
        db.commit()


def test_can_nang_bang_khong_bi_tu_choi(db):
    """TC-019: 0 kg cũng vô lý như số âm."""
    o = tao_chu_nuoi(db)
    db.add(Pet(owner_id=o.id, name="Mực", species="Chó", weight_kg=0))

    with pytest.raises(IntegrityError):
        db.commit()


def test_can_nang_de_trong_van_luu_duoc(db):
    """Chưa cân thì để trống, không phải điền bừa số 0."""
    o = tao_chu_nuoi(db)
    p = Pet(owner_id=o.id, name="Mực", species="Chó", weight_kg=None)
    db.add(p)
    db.commit()

    assert p.weight_kg is None


def test_thieu_ten_hoac_loai_bi_tu_choi(db):
    o = tao_chu_nuoi(db)
    db.add(Pet(owner_id=o.id, name=None, species="Chó"))

    with pytest.raises(IntegrityError):
        db.commit()


def test_thu_cung_luu_duoc_ngay_sinh(db):
    o = tao_chu_nuoi(db)
    p = Pet(owner_id=o.id, name="Mực", species="Chó", birth_date=date(2024, 5, 1))
    db.add(p)
    db.commit()

    assert p.birth_date == date(2024, 5, 1)
