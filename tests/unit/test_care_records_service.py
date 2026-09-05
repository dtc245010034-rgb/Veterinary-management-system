"""Test cho app/services/care_records.py — nghiệp vụ hồ sơ chăm sóc.

Phục vụ US-15, US-16 — TC-053 → TC-058.

Ghi hồ sơ là thao tác duy nhất đưa lịch hẹn về trạng thái `done`. Không có nút "đánh dấu
hoàn thành" riêng: trạng thái phản ánh việc đã làm thật, không phải một nhãn bấm tay.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.appointment import Appointment
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.services import care_records as nv
from app.services import clock, scheduling
from app.services.errors import LoiNghiepVu

# frozen_clock cố định "bây giờ" ở 2026-03-12 08:00.
BAY_GIO = datetime(2026, 3, 12, 8, 0)


def gio(h: int, p: int = 0, ngay: int = 12) -> datetime:
    return datetime(2026, 3, ngay, h, p)


@pytest.fixture
def nen(db, frozen_clock):
    """Hai thú cưng, một dịch vụ 60 phút, hai nhân viên chăm sóc, một quản lý."""
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p1 = Pet(owner_id=o.id, name="Mực", species="Chó")
    p2 = Pet(owner_id=o.id, name="Bông", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    nv1 = User(username="cs1", password_hash="b", full_name="Lê Văn Chăm", role="caretaker")
    nv2 = User(username="cs2", password_hash="b", full_name="Phạm Thị Sóc", role="caretaker")
    ql = User(username="quanly", password_hash="b", full_name="Nguyễn Văn Quản", role="manager")
    lt = User(username="letan", password_hash="b", full_name="Trần Thị Lễ", role="receptionist")
    db.add_all([p1, p2, dv, nv1, nv2, ql, lt])
    db.commit()

    return {"pet1": p1, "pet2": p2, "dv": dv, "nv1": nv1, "nv2": nv2, "ql": ql, "letan": lt}


def dat(db, nen, bat_dau=None, pet="pet1", nhan_vien="nv1", luc=None) -> Appointment:
    """Đặt lịch tại thời điểm `luc` (mặc định: mốc đông cứng của fixture)."""
    bat_dau = bat_dau or gio(9)
    with clock.freeze(luc or BAY_GIO):
        return scheduling.dat_lich(
            db,
            thu_cung_id=nen[pet].id,
            dich_vu_id=nen["dv"].id,
            nhan_vien_id=nen[nhan_vien].id,
            bat_dau=bat_dau,
            nguoi_tao_id=nen["letan"].id,
        )


def ghi(db, lich, nguoi_ghi, luc=None, **ghi_de):
    """Ghi hồ sơ tại thời điểm `luc` — mặc định ngay sau khi buổi chăm sóc kết thúc.

    Dùng clock.freeze lồng nhau thay vì sửa fixture frozen_clock dùng chung: một test
    hồ sơ cần hai mốc thời gian khác nhau (lúc đặt lịch và lúc ghi hồ sơ), còn mọi test
    khác trong dự án chỉ cần một.
    """
    truong = dict(tinh_trang="Da khô nhẹ ở lưng, tai sạch.")
    truong.update(ghi_de)
    with clock.freeze(luc or lich.end_at):
        return nv.ghi_ho_so(db, lich.id, nguoi_ghi_id=nguoi_ghi.id, **truong)


# --- Ghi hồ sơ -------------------------------------------------------------------


def test_ghi_ho_so_luu_duoc_va_lich_chuyen_hoan_thanh(db, nen, frozen_clock):
    """TC-053 — thao tác duy nhất đưa lịch về `done`."""
    lich = dat(db, nen)

    hs = ghi(db, lich, nen["nv1"], viec_da_lam="Tắm, sấy, cắt móng")

    assert hs.id is not None
    assert hs.condition_note == "Da khô nhẹ ở lưng, tai sạch."
    assert hs.actions_taken == "Tắm, sấy, cắt móng"
    assert lich.status == "done"


def test_performed_at_lay_tu_gio_lich_hen_khong_phai_luc_bam_nut(db, nen, frozen_clock):
    """Quyết định 2 của P4.

    Nhân viên ghi hồ sơ sáng hôm sau thì buổi chăm sóc vẫn phải nằm đúng chỗ trong lịch
    sử. Lấy clock.now() sẽ đẩy nó sang ngày 13 và làm sai thứ tự ở TC-057.
    """
    lich = dat(db, nen, bat_dau=gio(9))

    hs = ghi(db, lich, nen["nv1"], luc=gio(8, ngay=13))

    assert hs.performed_at == gio(9)


def test_staff_id_lay_tu_lich_hen_khong_phai_nguoi_dang_nhap(db, nen, frozen_clock):
    """Quyết định 4 của P4 — cái bẫy dễ mắc nhất của chặng này.

    Quản lý ghi hộ một buổi. Nếu lưu `current_user.id` thì lịch sử sẽ ghi quản lý là
    người tắm chó, trong khi US-16 đòi mỗi dòng có tên người THỰC HIỆN.
    """
    lich = dat(db, nen, nhan_vien="nv1")

    hs = ghi(db, lich, nen["ql"])

    assert hs.staff_id == nen["nv1"].id
    assert hs.staff.full_name == "Lê Văn Chăm"


def test_pet_id_lay_tu_lich_hen(db, nen, frozen_clock):
    """Quyết định 3: suy ra từ lịch hẹn, không nhận từ form."""
    lich = dat(db, nen, pet="pet2")

    hs = ghi(db, lich, nen["nv1"])

    assert hs.pet_id == nen["pet2"].id


def test_nhan_vien_khac_khong_ghi_duoc_ho_so(db, nen, frozen_clock):
    """TC-054."""
    lich = dat(db, nen, nhan_vien="nv1")

    with pytest.raises(LoiNghiepVu):
        ghi(db, lich, nen["nv2"])

    assert lich.status == "booked"


def test_le_tan_khong_ghi_duoc_ho_so(db, nen, frozen_clock):
    """Bảng phân quyền US-02: lễ tân chỉ xem hồ sơ chăm sóc."""
    lich = dat(db, nen)

    with pytest.raises(LoiNghiepVu):
        ghi(db, lich, nen["letan"])


def test_ghi_ho_so_lan_hai_cho_cung_lich_bi_tu_choi(db, nen, frozen_clock):
    """TC-055 ở tầng nghiệp vụ — thông báo đọc được, không phải IntegrityError."""
    lich = dat(db, nen)
    ghi(db, lich, nen["nv1"])

    with pytest.raises(LoiNghiepVu):
        ghi(db, lich, nen["nv1"], tinh_trang="Ghi đè")


@pytest.mark.parametrize("tinh_trang", ["", "   ", None])
def test_bo_trong_ghi_chu_tinh_trang_bi_tu_choi(db, nen, frozen_clock, tinh_trang):
    """TC-056. Hồ sơ không có tình trạng thì lần sau không có căn cứ gì."""
    lich = dat(db, nen)

    with pytest.raises(LoiNghiepVu):
        ghi(db, lich, nen["nv1"], tinh_trang=tinh_trang)

    assert lich.status == "booked"


def test_khong_ghi_ho_so_cho_lich_chua_dien_ra(db, nen, frozen_clock):
    """Quyết định 5 của P4 — lỗ đi qua đúng luồng bình thường.

    Nút "Ghi hồ sơ" hiện ngay trên lịch tuần sau trong danh sách của nhân viên. Bấm vào
    là có hồ sơ cho buổi chưa xảy ra, đồng thời khóa luôn khả năng đổi và hủy lịch.
    """
    lich = dat(db, nen, bat_dau=gio(9, ngay=20))

    with pytest.raises(LoiNghiepVu):
        ghi(db, lich, nen["nv1"], luc=BAY_GIO)

    assert lich.status == "booked"


def test_khong_ghi_ho_so_cho_lich_da_huy(db, nen, frozen_clock):
    """Buổi chăm sóc đã hủy thì không diễn ra."""
    lich = dat(db, nen)
    scheduling.huy_lich(db, lich.id, "Khách báo bận")

    with pytest.raises(LoiNghiepVu):
        ghi(db, lich, nen["nv1"])


def test_ho_so_khoa_luon_kha_nang_doi_va_huy_lich(db, nen, frozen_clock):
    """Đóng vòng với P3: `TRANG_THAI_SUA_DUOC` chặn sửa lịch đã `done`.

    Đây cũng là ràng buộc mà quyết định 2 dựa vào — lịch `done` không đổi giờ được nữa
    nên bản sao `performed_at` không thể lệch.
    """
    lich = dat(db, nen)
    ghi(db, lich, nen["nv1"])

    with pytest.raises(LoiNghiepVu):
        scheduling.doi_lich(db, lich.id, bat_dau=gio(14, ngay=20))
    with pytest.raises(LoiNghiepVu):
        scheduling.huy_lich(db, lich.id, "Đổi ý")


# --- Lịch sử chăm sóc ------------------------------------------------------------


def test_lich_su_sap_theo_thoi_gian_giam_dan(db, nen, frozen_clock):
    """TC-057: mới nhất lên đầu."""
    for ngay in (10, 12, 11):
        lich = dat(db, nen, bat_dau=gio(9, ngay=ngay), luc=datetime(2026, 3, ngay, 8, 0))
        ghi(db, lich, nen["nv1"], tinh_trang=f"Buổi ngày {ngay}")

    ds = nv.lich_su(db, nen["pet1"].id)

    assert [h.performed_at.day for h in ds] == [12, 11, 10]


def test_moi_dong_lich_su_du_ngay_dich_vu_nhan_vien_va_tinh_trang(db, nen, frozen_clock):
    """TC-057: US-16 đòi mỗi dòng có đủ bốn thông tin này."""
    lich = dat(db, nen)
    ghi(db, lich, nen["nv1"])

    hs = nv.lich_su(db, nen["pet1"].id)[0]

    assert hs.performed_at == gio(9)
    assert hs.lich_hen.service.name == "Tắm và sấy"
    assert hs.staff.full_name == "Lê Văn Chăm"
    assert hs.condition_note


def test_lich_su_chi_lay_ho_so_cua_thu_cung_do(db, nen, frozen_clock):
    lich1 = dat(db, nen, pet="pet1")
    lich2 = dat(db, nen, pet="pet2", nhan_vien="nv2")
    ghi(db, lich1, nen["nv1"], tinh_trang="Của Mực")
    ghi(db, lich2, nen["nv2"], tinh_trang="Của Bông")

    ds = nv.lich_su(db, nen["pet1"].id)

    assert [h.condition_note for h in ds] == ["Của Mực"]


def test_thu_cung_chua_dung_dich_vu_tra_ve_rong(db, nen):
    """TC-058."""
    assert nv.lich_su(db, nen["pet1"].id) == []


# --- Truy vấn hồ sơ ---------------------------------------------------------------


def test_lay_ho_so_tra_ve_dung_ban_ghi(db, nen, frozen_clock):
    lich = dat(db, nen)
    hs = ghi(db, lich, nen["nv1"])

    assert nv.lay_ho_so(db, hs.id).condition_note == hs.condition_note


def test_lay_ho_so_khong_ton_tai_nem_loi_nghiep_vu(db, nen):
    with pytest.raises(LoiNghiepVu):
        nv.lay_ho_so(db, 9999)


def test_ho_so_cua_lich_tra_ve_none_khi_chua_ghi(db, nen, frozen_clock):
    """Giao diện dựa vào None để quyết định hiện form hay hiện nội dung."""
    lich = dat(db, nen)

    assert nv.ho_so_cua_lich(db, lich.id) is None


def test_ho_so_cua_lich_tra_ve_ban_ghi_sau_khi_ghi(db, nen, frozen_clock):
    lich = dat(db, nen)
    hs = ghi(db, lich, nen["nv1"])

    assert nv.ho_so_cua_lich(db, lich.id).id == hs.id
