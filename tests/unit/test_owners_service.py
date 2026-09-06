"""Test cho app/services/owners.py — nghiệp vụ chủ nuôi và thú cưng.

Phục vụ US-04, US-05, US-06. Đây là tầng chứa mọi kiểm tra dữ liệu và quy tắc; router chỉ
gọi xuống đây. Nhờ vậy test gọi hàm trực tiếp, không cần dựng HTTP.
"""

from datetime import date, timedelta

import pytest

from app.models.pet import Pet
from app.services import owners as nv
from app.services.errors import LoiNghiepVu

# fixture frozen_clock cố định "bây giờ" ở 2026-03-12 08:00
HOM_NAY = date(2026, 3, 12)


# --- Tạo chủ nuôi ---------------------------------------------------------------


def test_tao_chu_nuoi_thanh_cong(db):
    """TC-013."""
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")

    assert o.id is not None
    assert o.search_name == "tran thi le"


@pytest.mark.parametrize("ho_ten, sdt", [("", "0912345678"), ("   ", "0912345678"), ("Tên", "")])
def test_thieu_ho_ten_hoac_so_dien_thoai_bi_tu_choi(db, ho_ten, sdt):
    """TC-014: báo lỗi nghiệp vụ có thông báo tiếng Việt, không phải IntegrityError.

    IntegrityError sẽ đi thẳng ra người dùng thành lỗi 500. Chặn ở đây để router trả
    được thông báo đọc hiểu được.
    """
    with pytest.raises(LoiNghiepVu):
        nv.tao_chu_nuoi(db, ho_ten=ho_ten, so_dien_thoai=sdt)


def test_ho_ten_duoc_cat_khoang_trang_thua(db):
    o = nv.tao_chu_nuoi(db, ho_ten="  Trần Thị Lễ  ", so_dien_thoai="0912345678")

    assert o.full_name == "Trần Thị Lễ"


# --- Cảnh báo trùng số điện thoại -----------------------------------------------


def test_so_dien_thoai_trung_tra_ve_danh_sach_de_canh_bao(db):
    """TC-015: cảnh báo chứ không cấm — người dùng tự quyết có phải khách cũ không."""
    nv.tao_chu_nuoi(db, ho_ten="Người Một", so_dien_thoai="0912345678")

    trung = nv.tim_theo_so_dien_thoai(db, "0912345678")

    assert len(trung) == 1
    assert trung[0].full_name == "Người Một"


def test_so_dien_thoai_chua_ai_dung_tra_ve_rong(db):
    assert nv.tim_theo_so_dien_thoai(db, "0900000000") == []


# --- Xóa chủ nuôi ---------------------------------------------------------------


def test_xoa_chu_nuoi_khong_co_thu_cung_thanh_cong(db):
    o = nv.tao_chu_nuoi(db, ho_ten="Không Thú", so_dien_thoai="0912345678")

    nv.xoa_chu_nuoi(db, o.id)

    assert nv.tim_theo_so_dien_thoai(db, "0912345678") == []


def test_xoa_chu_nuoi_con_thu_cung_bi_chan_kem_thong_bao(db, frozen_clock):
    """TC-016: chặn ở tầng nghiệp vụ để có thông báo tiếng Việt.

    Khóa ngoại của SQLite cũng chặn, nhưng nó ném IntegrityError và người dùng nhận
    về lỗi 500 — đúng về dữ liệu, vô dụng với người đang đứng ở quầy.
    """
    o = nv.tao_chu_nuoi(db, ho_ten="Có Thú", so_dien_thoai="0912345678")
    nv.tao_thu_cung(db, chu_nuoi_id=o.id, ten="Mực", loai="Chó")

    with pytest.raises(LoiNghiepVu) as loi:
        nv.xoa_chu_nuoi(db, o.id)

    assert "thú cưng" in str(loi.value).lower()


# --- Tạo thú cưng ---------------------------------------------------------------


def test_tao_thu_cung_thanh_cong(db, frozen_clock):
    """TC-017."""
    o = nv.tao_chu_nuoi(db, ho_ten="Chủ", so_dien_thoai="0912345678")

    p = nv.tao_thu_cung(db, chu_nuoi_id=o.id, ten="Mực", loai="Chó", giong="Poodle")

    assert p.owner_id == o.id
    assert p.search_name == "muc"


def test_ngay_sinh_tuong_lai_bi_tu_choi(db, frozen_clock):
    """TC-018. Dùng clock cố định nên kết quả không đổi theo ngày chạy test."""
    o = nv.tao_chu_nuoi(db, ho_ten="Chủ", so_dien_thoai="0912345678")

    with pytest.raises(LoiNghiepVu):
        nv.tao_thu_cung(
            db, chu_nuoi_id=o.id, ten="Mực", loai="Chó", ngay_sinh=HOM_NAY + timedelta(days=1)
        )


def test_ngay_sinh_hom_nay_duoc_chap_nhan(db, frozen_clock):
    """Thú cưng mới sinh hôm nay là hợp lệ — ranh giới phải là "sau hôm nay" mới bị chặn."""
    o = nv.tao_chu_nuoi(db, ho_ten="Chủ", so_dien_thoai="0912345678")

    p = nv.tao_thu_cung(db, chu_nuoi_id=o.id, ten="Mực", loai="Chó", ngay_sinh=HOM_NAY)

    assert p.birth_date == HOM_NAY


@pytest.mark.parametrize("can_nang", [-1.0, 0.0])
def test_can_nang_khong_duong_bi_tu_choi(db, frozen_clock, can_nang):
    """TC-019."""
    o = nv.tao_chu_nuoi(db, ho_ten="Chủ", so_dien_thoai="0912345678")

    with pytest.raises(LoiNghiepVu):
        nv.tao_thu_cung(db, chu_nuoi_id=o.id, ten="Mực", loai="Chó", can_nang=can_nang)


def test_thieu_ten_hoac_loai_bi_tu_choi(db, frozen_clock):
    o = nv.tao_chu_nuoi(db, ho_ten="Chủ", so_dien_thoai="0912345678")

    with pytest.raises(LoiNghiepVu):
        nv.tao_thu_cung(db, chu_nuoi_id=o.id, ten="", loai="Chó")


def test_gan_thu_cung_cho_chu_nuoi_khong_ton_tai_bi_tu_choi(db, frozen_clock):
    with pytest.raises(LoiNghiepVu):
        nv.tao_thu_cung(db, chu_nuoi_id=9999, ten="Mồ Côi", loai="Chó")


# --- Tra cứu --------------------------------------------------------------------


@pytest.fixture
def du_lieu_tra_cuu(db, frozen_clock):
    o1 = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    o2 = nv.tao_chu_nuoi(db, ho_ten="Nguyễn Văn Quản", so_dien_thoai="0987654321")
    nv.tao_thu_cung(db, chu_nuoi_id=o1.id, ten="Mực", loai="Chó")
    nv.tao_thu_cung(db, chu_nuoi_id=o1.id, ten="Mun", loai="Mèo")
    nv.tao_thu_cung(db, chu_nuoi_id=o2.id, ten="Đậu Đỏ", loai="Mèo")
    return {"o1": o1, "o2": o2}


def test_tim_theo_so_dien_thoai(db, du_lieu_tra_cuu):
    """TC-021."""
    kq = nv.tra_cuu(db, "0912345678")

    assert [o.full_name for o in kq.chu_nuoi] == ["Trần Thị Lễ"]


def test_tim_theo_mot_phan_so_dien_thoai(db, du_lieu_tra_cuu):
    """Khách đọc bốn số cuối là chuyện thường ở quầy."""
    kq = nv.tra_cuu(db, "5678")

    assert len(kq.chu_nuoi) == 1


@pytest.mark.parametrize("tu_khoa", ["mun", "MUN", "Mun"])
def test_tim_ten_thu_cung_khong_phan_biet_hoa_thuong(db, du_lieu_tra_cuu, tu_khoa):
    """TC-022."""
    kq = nv.tra_cuu(db, tu_khoa)

    assert [p.name for p in kq.thu_cung] == ["Mun"]


@pytest.mark.parametrize("tu_khoa", ["muc", "Mực", "MỰC"])
def test_tim_ten_thu_cung_khong_dau(db, du_lieu_tra_cuu, tu_khoa):
    """TC-022: gõ "muc" phải ra "Mực"."""
    kq = nv.tra_cuu(db, tu_khoa)

    assert [p.name for p in kq.thu_cung] == ["Mực"]


def test_tim_ten_co_chu_d_gach_ngang(db, du_lieu_tra_cuu):
    """Gõ "dau do" phải ra "Đậu Đỏ" — chỗ dễ sót nhất của tiếng Việt."""
    kq = nv.tra_cuu(db, "dau do")

    assert [p.name for p in kq.thu_cung] == ["Đậu Đỏ"]


def test_tim_ten_chu_nuoi_khong_dau(db, du_lieu_tra_cuu):
    kq = nv.tra_cuu(db, "tran thi le")

    assert [o.full_name for o in kq.chu_nuoi] == ["Trần Thị Lễ"]


def test_tim_khong_khop_tra_ve_rong(db, du_lieu_tra_cuu):
    """TC-023."""
    kq = nv.tra_cuu(db, "khong-co-gi-khop")

    assert kq.chu_nuoi == []
    assert kq.thu_cung == []


def test_tu_khoa_rong_tra_ve_rong(db, du_lieu_tra_cuu):
    """Bấm tìm với ô trống không được trả về toàn bộ CSDL."""
    kq = nv.tra_cuu(db, "   ")

    assert kq.chu_nuoi == []
    assert kq.thu_cung == []


# --- Sửa, lấy, xóa: bù bao phủ cho các hàm public còn thiếu -----------------------
#
# Sáu hàm dưới đây đã có sẵn từ P2a và chạy đúng, nhưng chỉ được kiểm gián tiếp qua
# integration test. Luật bao phủ trong CLAUDE.md mục 7 đòi mỗi hàm public trong
# app/services/ có tối thiểu 1 happy path + 1 ca biên gọi thẳng.


def test_sua_chu_nuoi_doi_dung_truong_va_dong_bo_search_name(db):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")

    nv.sua_chu_nuoi(db, o.id, ho_ten="Trần Thị Lệ Hằng", dia_chi="12 Lê Lợi")

    assert o.full_name == "Trần Thị Lệ Hằng"
    assert o.address == "12 Lê Lợi"
    assert o.search_name == "tran thi le hang"
    assert o.phone == "0912345678"  # trường không truyền thì giữ nguyên


def test_sua_chu_nuoi_bo_trong_ho_ten_bi_tu_choi(db):
    """Sửa phải chặt như tạo, nếu không có thể xóa trắng tên bằng đường sửa."""
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")

    with pytest.raises(LoiNghiepVu):
        nv.sua_chu_nuoi(db, o.id, ho_ten="   ")

    db.expire_all()
    assert nv.lay_chu_nuoi(db, o.id).full_name == "Trần Thị Lễ"


def test_sua_chu_nuoi_khong_ton_tai_bi_tu_choi(db):
    with pytest.raises(LoiNghiepVu):
        nv.sua_chu_nuoi(db, 9999, ho_ten="Ai đó")


def test_danh_sach_chu_nuoi_sap_theo_ho_ten(db):
    for ten in ("Trần Thị Lễ", "Đỗ Thị Hằng", "Lý Thu Hà"):
        nv.tao_chu_nuoi(db, ho_ten=ten, so_dien_thoai="0912345678")

    assert [o.full_name for o in nv.danh_sach_chu_nuoi(db)] == [
        "Lý Thu Hà", "Trần Thị Lễ", "Đỗ Thị Hằng"
    ]


def test_danh_sach_chu_nuoi_rong_khi_chua_co_ai(db):
    assert nv.danh_sach_chu_nuoi(db) == []


def test_lay_chu_nuoi_tra_ve_dung_ban_ghi(db):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")

    assert nv.lay_chu_nuoi(db, o.id).id == o.id


def test_lay_chu_nuoi_khong_ton_tai_nem_loi_nghiep_vu(db):
    """Trả None sẽ đẩy lỗi xuống chỗ khác thành AttributeError khó lần."""
    with pytest.raises(LoiNghiepVu):
        nv.lay_chu_nuoi(db, 9999)


def test_sua_thu_cung_doi_can_nang_va_ghi_chu(db, frozen_clock):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    p = nv.tao_thu_cung(db, o.id, ten="Mực", loai="Chó", can_nang=8.0)

    nv.sua_thu_cung(db, p.id, can_nang=9.5, ghi_chu="Sợ máy sấy")

    assert p.weight_kg == 9.5
    assert p.note == "Sợ máy sấy"
    assert p.name == "Mực"


def test_sua_thu_cung_can_nang_khong_duong_bi_tu_choi(db, frozen_clock):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    p = nv.tao_thu_cung(db, o.id, ten="Mực", loai="Chó", can_nang=8.0)

    with pytest.raises(LoiNghiepVu):
        nv.sua_thu_cung(db, p.id, can_nang=0)

    db.expire_all()
    assert nv.lay_thu_cung(db, p.id).weight_kg == 8.0


def test_sua_thu_cung_ngay_sinh_tuong_lai_bi_tu_choi(db, frozen_clock):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    p = nv.tao_thu_cung(db, o.id, ten="Mực", loai="Chó")

    with pytest.raises(LoiNghiepVu):
        nv.sua_thu_cung(db, p.id, ngay_sinh=HOM_NAY + timedelta(days=1))


def test_lay_thu_cung_tra_ve_dung_ban_ghi(db, frozen_clock):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    p = nv.tao_thu_cung(db, o.id, ten="Mực", loai="Chó")

    assert nv.lay_thu_cung(db, p.id).name == "Mực"


def test_lay_thu_cung_khong_ton_tai_nem_loi_nghiep_vu(db):
    with pytest.raises(LoiNghiepVu):
        nv.lay_thu_cung(db, 9999)


def test_xoa_thu_cung_thanh_cong_va_chu_nuoi_van_con(db, frozen_clock):
    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    p = nv.tao_thu_cung(db, o.id, ten="Mực", loai="Chó")

    nv.xoa_thu_cung(db, p.id)

    assert db.get(Pet, p.id) is None
    assert nv.lay_chu_nuoi(db, o.id) is not None


def test_xoa_thu_cung_khong_ton_tai_bi_tu_choi(db):
    with pytest.raises(LoiNghiepVu):
        nv.xoa_thu_cung(db, 9999)


def test_xoa_thu_cung_con_lich_hen_bi_chan_kem_thong_bao(db, frozen_clock):
    """Lỗi tồn tại từ P3: khóa ngoại ném IntegrityError thành lỗi 500.

    Cùng luật với `xoa_chu_nuoi` — chặn ở đây để trả thông báo đọc hiểu được, khóa ngoại
    giữ vai trò lớp chặn cuối.
    """
    from datetime import datetime
    from decimal import Decimal

    from app.models.appointment import Appointment
    from app.models.service import Service
    from app.models.user import User

    o = nv.tao_chu_nuoi(db, ho_ten="Trần Thị Lễ", so_dien_thoai="0912345678")
    p = nv.tao_thu_cung(db, o.id, ten="Mực", loai="Chó")
    dv = Service(code="TAM", name="Tắm", duration_min=60, price=Decimal("1"))
    u = User(username="cs", password_hash="b", full_name="Chăm", role="caretaker")
    db.add_all([dv, u])
    db.commit()
    db.add(
        Appointment(
            pet_id=p.id, service_id=dv.id, staff_id=u.id,
            start_at=datetime(2026, 3, 12, 9), end_at=datetime(2026, 3, 12, 10),
            created_by=u.id,
        )
    )
    db.commit()

    with pytest.raises(LoiNghiepVu) as loi:
        nv.xoa_thu_cung(db, p.id)

    assert "lịch hẹn" in str(loi.value).lower()
    assert nv.lay_thu_cung(db, p.id) is not None


def test_xoa_thu_cung_chi_co_ho_so_tiem_bi_chan_khong_phai_loi_500(db, frozen_clock):
    """Lỗi mở lại ở P4 chặng 2, tìm ra khi rà luồng bằng trình duyệt.

    Phép chặn cũ hỏi đúng một câu: "thú cưng này còn lịch hẹn không?". Bảng `vaccinations`
    cũng trỏ vào `pets`, nên thú cưng chỉ có hồ sơ tiêm lọt qua phép chặn, rơi xuống khóa
    ngoại, và người dùng nhận về trang đen "Internal Server Error".

    Sửa bằng cách hỏi CSDL thay vì liệt kê bảng: bảng nào trỏ vào `pets` ở phase sau cũng
    được chặn sẵn, không phải nhớ sửa lại hàm này.
    """
    from datetime import date

    from app.models.vaccination import Vaccination

    o = nv.tao_chu_nuoi(db, ho_ten="Lý Thu Hà", so_dien_thoai="0905112233")
    p = nv.tao_thu_cung(db, o.id, ten="Sữa", loai="Mèo")
    db.add(Vaccination(pet_id=p.id, vaccine_name="FVRCP", given_at=date(2026, 1, 1)))
    db.commit()

    with pytest.raises(LoiNghiepVu):
        nv.xoa_thu_cung(db, p.id)

    assert db.get(Pet, p.id) is not None
