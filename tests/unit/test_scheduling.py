"""Test cho app/services/scheduling.py — đặt lịch và chống trùng lịch.

Phục vụ US-10, US-11 — TC-032 → TC-034, TC-036 → TC-042.

Đây là nhóm test quan trọng nhất của dự án. Đề bài nêu đích danh ở mục 6: "KT2: … debug
trùng lịch."

Quy tắc: lịch chiếm khoảng NỬA MỞ [start_at, end_at). Hai lịch giao nhau khi
    A.start < B.end  AND  B.start < A.end
Từ chối khi giao nhau và trùng nhân viên, hoặc giao nhau và trùng thú cưng.
Lịch đã hủy không tham gia kiểm tra.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.appointment import TEN_TRANG_THAI
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.services import billing, care_records, clock
from app.services import scheduling as nv
from app.services.errors import LoiNghiepVu

# Fixture frozen_clock cố định "bây giờ" ở 2026-03-12 08:00, nên mọi mốc dưới đây đều ở
# tương lai gần và không đổi theo ngày chạy test.
NGAY = datetime(2026, 3, 12)


def gio(h: int, p: int = 0) -> datetime:
    return NGAY.replace(hour=h, minute=p)


@pytest.fixture
def nen(db, frozen_clock):
    """Hai thú cưng của hai chủ, một dịch vụ 60 phút, hai nhân viên chăm sóc."""
    o1 = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    o2 = Owner(full_name="Lý Thu Hà", phone="0905112233")
    db.add_all([o1, o2])
    db.flush()

    p1 = Pet(owner_id=o1.id, name="Mực", species="Chó")
    p2 = Pet(owner_id=o2.id, name="Bông", species="Chó")
    dv60 = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    dv30 = Service(code="CATMONG", name="Cắt móng", duration_min=30, price=Decimal("50000"))
    nv1 = User(username="cs1", password_hash="b", full_name="Lê Văn Chăm", role="caretaker")
    nv2 = User(username="cs2", password_hash="b", full_name="Phạm Thị Sóc", role="caretaker")
    lt = User(username="letan", password_hash="b", full_name="Trần Thị Lễ", role="receptionist")
    db.add_all([p1, p2, dv60, dv30, nv1, nv2, lt])
    db.commit()

    return {
        "pet1": p1, "pet2": p2,
        "dv60": dv60, "dv30": dv30,
        "nv1": nv1, "nv2": nv2, "letan": lt,
    }


def dat(db, nen, bat_dau, pet="pet1", nhan_vien="nv1", dich_vu="dv60"):
    return nv.dat_lich(
        db,
        thu_cung_id=nen[pet].id,
        dich_vu_id=nen[dich_vu].id,
        nhan_vien_id=nen[nhan_vien].id,
        bat_dau=bat_dau,
        nguoi_tao_id=nen["letan"].id,
    )


# --- Đặt lịch cơ bản -------------------------------------------------------------


def test_dat_lich_tinh_gio_ket_thuc_tu_thoi_luong_dich_vu(db, nen):
    """TC-032: dịch vụ 60 phút bắt đầu 09:00 thì kết thúc 10:00."""
    a = dat(db, nen, gio(9))

    assert a.start_at == gio(9)
    assert a.end_at == gio(10)
    assert a.status == "booked"


def test_dich_vu_khac_thoi_luong_cho_gio_ket_thuc_khac(db, nen):
    a = dat(db, nen, gio(9), dich_vu="dv30")

    assert a.end_at == gio(9, 30)


def test_dat_lich_trong_qua_khu_bi_tu_choi(db, nen):
    """TC-033. Dùng clock.now() nên kết quả không đổi theo ngày chạy test."""
    with pytest.raises(LoiNghiepVu) as loi:
        dat(db, nen, gio(7))  # frozen_clock đang ở 08:00

    assert "quá khứ" in str(loi.value).lower()


def test_nhan_vien_khong_phai_caretaker_bi_tu_choi(db, nen):
    """TC-034: lễ tân không phải người trực tiếp chăm sóc."""
    with pytest.raises(LoiNghiepVu) as loi:
        nv.dat_lich(
            db,
            thu_cung_id=nen["pet1"].id,
            dich_vu_id=nen["dv60"].id,
            nhan_vien_id=nen["letan"].id,
            bat_dau=gio(9),
            nguoi_tao_id=nen["letan"].id,
        )

    assert "chăm sóc" in str(loi.value).lower()


def test_dat_lich_dich_vu_da_ngung_ban_bi_tu_choi(db, nen):
    """TC-030, phần còn thiếu từ P2b: dịch vụ ngưng bán không đặt lịch mới được."""
    nen["dv60"].is_active = False
    db.commit()

    with pytest.raises(LoiNghiepVu):
        dat(db, nen, gio(9))


# --- SÁU CA BIÊN TRÙNG LỊCH ------------------------------------------------------
# Mỗi ca bắt một lỗi cài đặt cụ thể. Xem bảng trong docs/plans/2026-09-05-p3-lich-hen.md


def test_trung_nhan_vien_giao_nhau_mot_phan_bi_tu_choi(db, nen):
    """TC-036: 09:30–10:30 khi nhân viên đã có 09:00–10:00. Ca cơ bản nhất."""
    dat(db, nen, gio(9))

    with pytest.raises(nv.TrungLich):
        dat(db, nen, gio(9, 30), pet="pet2")


def test_lich_lien_ke_duoc_chap_nhan(db, nen):
    """TC-038 — CA DỄ SAI NHẤT.

    10:00–11:00 ngay sau 09:00–10:00 KHÔNG phải trùng: khoảng là nửa mở, thời điểm 10:00
    thuộc về lịch sau chứ không thuộc lịch trước.

    Cài đặt dùng `<=` thay vì `<` sẽ chặn đúng tình huống hợp lệ này — mà xếp lịch liên
    tiếp là chuyện bình thường ở cửa hàng, và lễ tân sẽ không hiểu vì sao bị từ chối.
    """
    dat(db, nen, gio(9))

    a = dat(db, nen, gio(10), pet="pet2")

    assert a.start_at == gio(10)


def test_trung_thu_cung_khac_nhan_vien_bi_tu_choi(db, nen):
    """TC-039: một thú cưng không thể ở hai nơi cùng lúc.

    Bắt lỗi cài đặt chỉ kiểm theo nhân viên mà quên kiểm theo thú cưng.
    """
    dat(db, nen, gio(9), nhan_vien="nv1")

    with pytest.raises(nv.TrungLich):
        dat(db, nen, gio(9, 30), nhan_vien="nv2")


def test_lich_da_huy_khong_tinh_la_trung(db, nen):
    """TC-040: hủy lịch xong thì khung giờ đó phải đặt lại được."""
    a = dat(db, nen, gio(9))
    a.status = "cancelled"
    db.commit()

    moi = dat(db, nen, gio(9), pet="pet2")

    assert moi.start_at == gio(9)


def test_lich_moi_bao_tron_lich_cu_bi_tu_choi(db, nen):
    """TC-041: 08:00–11:00 phủ trọn 09:00–10:00.

    Bắt lỗi cài đặt chỉ kiểm `start` mới có nằm trong khoảng cũ hay không — ở đây
    start 08:00 nằm ngoài, nhưng hai khoảng vẫn giao nhau.
    """
    dat(db, nen, gio(9))
    dv180 = Service(code="SPA", name="Spa dài", duration_min=180, price=Decimal("1"))
    db.add(dv180)
    db.commit()

    with pytest.raises(nv.TrungLich):
        nv.dat_lich(
            db,
            thu_cung_id=nen["pet2"].id,
            dich_vu_id=dv180.id,
            nhan_vien_id=nen["nv1"].id,
            bat_dau=gio(8),
            nguoi_tao_id=nen["letan"].id,
        )


def test_lich_moi_nam_gon_trong_lich_cu_bi_tu_choi(db, nen):
    """TC-042: 09:15–09:45 nằm hẳn bên trong 09:00–10:00.

    Bắt lỗi cài đặt chỉ kiểm `end` mới có nằm trong khoảng cũ hay không.
    """
    dat(db, nen, gio(9))
    dv15 = Service(code="TAI", name="Vệ sinh tai", duration_min=15, price=Decimal("1"))
    db.add(dv15)
    db.commit()

    with pytest.raises(nv.TrungLich):
        nv.dat_lich(
            db,
            thu_cung_id=nen["pet2"].id,
            dich_vu_id=dv15.id,
            nhan_vien_id=nen["nv1"].id,
            bat_dau=gio(9, 15),
            nguoi_tao_id=nen["letan"].id,
        )


def test_hai_lich_trung_khop_hoan_toan_bi_tu_choi(db, nen):
    dat(db, nen, gio(9))

    with pytest.raises(nv.TrungLich):
        dat(db, nen, gio(9), pet="pet2")


def test_lich_ngay_truoc_gio_lich_cu_duoc_chap_nhan(db, nen):
    """Mặt đối xứng của TC-038: 08:00–09:00 ngay trước 09:00–10:00."""
    dat(db, nen, gio(9))

    a = dat(db, nen, gio(8), pet="pet2")

    assert a.end_at == gio(9)


def test_hai_nhan_vien_khac_nhau_cung_gio_deu_dat_duoc(db, nen):
    """Không được chặn nhầm: hai nhân viên khác nhau làm cùng giờ là bình thường."""
    dat(db, nen, gio(9), nhan_vien="nv1", pet="pet1")

    a = dat(db, nen, gio(9), nhan_vien="nv2", pet="pet2")

    assert a.staff_id == nen["nv2"].id


# --- Gợi ý khung trống -----------------------------------------------------------


def test_tu_choi_kem_goi_y_khung_trong(db, nen):
    """TC-037: từ chối suông thì lễ tân phải tự dò, rất mất thời gian ở quầy."""
    dat(db, nen, gio(9))

    with pytest.raises(nv.TrungLich) as loi:
        dat(db, nen, gio(9, 30), pet="pet2")

    assert loi.value.khung_trong, "Phải gợi ý ít nhất một khung giờ trống"


def test_goi_y_khong_bao_gom_khung_da_bi_chiem(db, nen):
    dat(db, nen, gio(9))

    with pytest.raises(nv.TrungLich) as loi:
        dat(db, nen, gio(9, 30), pet="pet2")

    assert gio(9) not in loi.value.khung_trong
    assert gio(9, 30) not in loi.value.khung_trong


def test_goi_y_nam_trong_gio_lam_viec(db, nen):
    """Gợi ý 03:00 sáng là vô nghĩa."""
    dat(db, nen, gio(9))

    with pytest.raises(nv.TrungLich) as loi:
        dat(db, nen, gio(9, 30), pet="pet2")

    for khung in loi.value.khung_trong:
        assert nv.GIO_MO_CUA <= khung.hour < nv.GIO_DONG_CUA


def test_goi_y_khong_lay_khung_da_qua_trong_ngay_hom_nay(db, nen):
    """frozen_clock ở 08:00 — không gợi ý khung đã trôi qua."""
    dat(db, nen, gio(9))

    with pytest.raises(nv.TrungLich) as loi:
        dat(db, nen, gio(9, 30), pet="pet2")

    for khung in loi.value.khung_trong:
        assert khung >= gio(8)


# --- Truy vấn lịch ---------------------------------------------------------------


def test_lich_theo_ngay_sap_theo_gio_tang_dan(db, nen):
    dat(db, nen, gio(14), pet="pet2")
    dat(db, nen, gio(9))

    ds = nv.lich_theo_ngay(db, NGAY.date())

    assert [a.start_at for a in ds] == [gio(9), gio(14)]


def test_lich_theo_ngay_khong_lay_lich_ngay_khac(db, nen):
    dat(db, nen, gio(9))

    assert nv.lich_theo_ngay(db, (NGAY + timedelta(days=1)).date()) == []


def test_lich_theo_ngay_van_hien_lich_da_huy(db, nen):
    """Lễ tân cần thấy lịch đã hủy để biết khách nào đã báo bận."""
    a = dat(db, nen, gio(9))
    a.status = "cancelled"
    db.commit()

    assert len(nv.lich_theo_ngay(db, NGAY.date())) == 1


def test_loc_lich_theo_nhan_vien(db, nen):
    dat(db, nen, gio(9), nhan_vien="nv1", pet="pet1")
    dat(db, nen, gio(9), nhan_vien="nv2", pet="pet2")

    ds = nv.lich_theo_ngay(db, NGAY.date(), nhan_vien_id=nen["nv1"].id)

    assert [a.staff_id for a in ds] == [nen["nv1"].id]


# --- Đổi lịch (chặng 2) ------------------------------------------------------------


def test_doi_sang_khung_trong_cap_nhat_gio_va_chuyen_trang_thai(db, nen):
    """TC-044."""
    a = dat(db, nen, gio(9))

    nv.doi_lich(db, a.id, bat_dau=gio(14))

    assert a.start_at == gio(14)
    assert a.end_at == gio(15)
    assert a.status == "rescheduled"


def test_doi_sang_khung_ban_bi_tu_choi_va_giu_nguyen_gio_cu(db, nen):
    """TC-045 — ca quan trọng nhất của đổi lịch.

    Cập nhật trước rồi mới kiểm tra sẽ để lịch rơi vào trạng thái nửa vời: giờ đã đổi
    nhưng thao tác báo lỗi. Phải kiểm xong mới ghi.
    """
    a = dat(db, nen, gio(9))
    dat(db, nen, gio(14), pet="pet2")

    with pytest.raises(nv.TrungLich):
        nv.doi_lich(db, a.id, bat_dau=gio(14))

    assert a.start_at == gio(9)
    assert a.status == "booked"

    # Đọc lại từ CSDL: nếu có bản ghi nào đã lỡ ghi xuống thì phải lộ ra ở đây.
    db.expire_all()
    assert nv.lay_lich(db, a.id).start_at == gio(9)


def test_doi_lich_khong_tu_so_sanh_voi_chinh_no(db, nen):
    """TC-046 — cái bẫy thứ hai.

    Lịch 09:00–10:00 dời sang 09:30–10:30. Lịch duy nhất giao với khung mới chính là
    nó. Không loại ra khỏi tập so sánh thì không lịch nào đổi giờ được.
    """
    a = dat(db, nen, gio(9))

    nv.doi_lich(db, a.id, bat_dau=gio(9, 30))

    assert a.start_at == gio(9, 30)


def test_doi_lich_da_huy_bi_tu_choi(db, nen):
    """TC-047."""
    a = dat(db, nen, gio(9))
    nv.huy_lich(db, a.id, "Khách báo bận")

    with pytest.raises(LoiNghiepVu):
        nv.doi_lich(db, a.id, bat_dau=gio(14))


def test_doi_lich_da_hoan_thanh_bi_tu_choi(db, nen):
    """TC-047 — nửa còn lại."""
    a = dat(db, nen, gio(9))
    a.status = "done"
    db.commit()

    with pytest.raises(LoiNghiepVu):
        nv.doi_lich(db, a.id, bat_dau=gio(14))


def test_doi_sang_nhan_vien_khac(db, nen):
    """US-12 cho phép đổi cả nhân viên, không chỉ giờ."""
    a = dat(db, nen, gio(9), nhan_vien="nv1")

    nv.doi_lich(db, a.id, bat_dau=gio(9), nhan_vien_id=nen["nv2"].id)

    assert a.staff_id == nen["nv2"].id
    assert a.start_at == gio(9)


def test_doi_lich_ve_qua_khu_bi_tu_choi(db, nen):
    """frozen_clock đang ở 08:00 ngày 12/03."""
    a = dat(db, nen, gio(9))

    with pytest.raises(LoiNghiepVu):
        nv.doi_lich(db, a.id, bat_dau=gio(7))


def test_doi_lich_giu_nguyen_gio_van_bao_trung_neu_nhan_vien_moi_ban(db, nen):
    """Đổi nhân viên sang người đã có lịch trùng giờ → từ chối."""
    a = dat(db, nen, gio(9), nhan_vien="nv1")
    dat(db, nen, gio(9), pet="pet2", nhan_vien="nv2")

    with pytest.raises(nv.TrungLich):
        nv.doi_lich(db, a.id, bat_dau=gio(9), nhan_vien_id=nen["nv2"].id)

    assert a.staff_id == nen["nv1"].id


def test_doi_gio_ma_giu_nhan_vien_da_khoa_bi_tu_choi(db, nen):
    """Lỗ hổng S4 (kế hoạch P7 chặng 0).

    Nhân viên bị khóa sau khi đã được phân lịch. Đổi giờ mà giữ nguyên người đó thì trước
    đây lọt qua — phép kiểm nhân viên chỉ chạy khi ĐỔI nhân viên — và lịch mới lại nằm
    trong tay một tài khoản không đăng nhập được, không ai ghi hồ sơ cho nó.
    """
    a = dat(db, nen, gio(9), nhan_vien="nv1")
    nen["nv1"].is_active = False
    db.commit()

    with pytest.raises(LoiNghiepVu, match="ngưng hoạt động"):
        nv.doi_lich(db, a.id, bat_dau=gio(14))

    assert a.start_at == gio(9)


def test_lich_cua_nhan_vien_da_khoa_van_chuyen_duoc_sang_nguoi_khac(db, nen):
    """Biên của ca trên: lối thoát đúng cho lịch kẹt là chuyển người, và nó phải còn mở."""
    a = dat(db, nen, gio(9), nhan_vien="nv1")
    nen["nv1"].is_active = False
    db.commit()

    nv.doi_lich(db, a.id, bat_dau=gio(9), nhan_vien_id=nen["nv2"].id)

    assert a.staff_id == nen["nv2"].id


def test_dem_lich_chua_lam_theo_nhan_vien(db, nen):
    """S4: trang Tài khoản cần biết nhân viên sắp khóa/đã khóa còn giữ bao nhiêu lịch.

    Chỉ đếm lịch còn sửa được (`booked`, `rescheduled`): lịch đã hủy không cần ai làm,
    lịch đã xong thì đã làm rồi.
    """
    dat(db, nen, gio(9), nhan_vien="nv1")
    dat(db, nen, gio(10), nhan_vien="nv1")
    huy = dat(db, nen, gio(11), nhan_vien="nv1")
    nv.huy_lich(db, huy.id, "Khách báo bận")
    dat(db, nen, gio(9), pet="pet2", nhan_vien="nv2")

    assert nv.so_lich_chua_lam_theo_nhan_vien(db) == {nen["nv1"].id: 2, nen["nv2"].id: 1}


def test_dem_lich_chua_lam_khi_chua_co_lich_nao(db, nen):
    assert nv.so_lich_chua_lam_theo_nhan_vien(db) == {}


# --- Hủy lịch (chặng 2) ------------------------------------------------------------


def test_huy_lich_kem_ly_do_doi_trang_thai_va_luu_ly_do(db, nen):
    """TC-048."""
    a = dat(db, nen, gio(9))

    nv.huy_lich(db, a.id, "Khách báo bận")

    assert a.status == "cancelled"
    assert a.cancel_reason == "Khách báo bận"


def test_khung_gio_sau_khi_huy_dat_lai_duoc(db, nen):
    """TC-048 — nửa sau: hủy phải thật sự giải phóng khung giờ."""
    a = dat(db, nen, gio(9))
    nv.huy_lich(db, a.id, "Khách báo bận")

    b = dat(db, nen, gio(9), pet="pet2")

    assert b.start_at == gio(9)


def test_huy_lich_da_hoan_thanh_bi_tu_choi(db, nen):
    """TC-049: buổi chăm sóc đã làm xong thì không hủy được nữa."""
    a = dat(db, nen, gio(9))
    a.status = "done"
    db.commit()

    with pytest.raises(LoiNghiepVu):
        nv.huy_lich(db, a.id, "Đổi ý")

    assert a.status == "done"


def test_huy_lich_khong_co_ly_do_bi_tu_choi(db, nen):
    """Lý do hủy là bắt buộc — ERD ghi rõ, và không có lý do thì không truy nguyên được."""
    a = dat(db, nen, gio(9))

    with pytest.raises(LoiNghiepVu):
        nv.huy_lich(db, a.id, "   ")

    assert a.status == "booked"


def test_huy_lich_da_huy_bi_tu_choi(db, nen):
    a = dat(db, nen, gio(9))
    nv.huy_lich(db, a.id, "Khách báo bận")

    with pytest.raises(LoiNghiepVu):
        nv.huy_lich(db, a.id, "Hủy lần nữa")


# --- Hủy lịch khi đã có hóa đơn (US-21) -------------------------------------------
#
# Hai lớp chặn độc lập chồng lên nhau, và ở P5 lớp nào cũng đủ chặn một mình:
#
#   lớp hóa đơn    — lịch còn hóa đơn chưa hủy thì không hủy lịch được
#   lớp trạng thái — lịch `done` thì không hủy được, có hóa đơn hay không
#
# Lịch có hóa đơn thì luôn `done` (hóa đơn chỉ lập từ lịch `done`, và `done` là cửa một
# chiều), nên riêng ở P5 lớp trạng thái đã chặn sẵn mọi ca của lớp hóa đơn. Cái lớp hóa
# đơn thêm vào là **thông báo**: nêu mã hóa đơn để lễ tân biết phải hủy hóa đơn trước.
# Vì vậy hai test dưới đây kiểm đúng thứ phân biệt được hai lớp — nội dung thông báo —
# chứ không kiểm "có ném lỗi không": kiểm ném lỗi thì bỏ phép kiểm hóa đơn đi vẫn xanh.


def lich_da_lap_hoa_don(db, nen):
    """Một lịch đã xong và đã có hóa đơn, đi qua đúng luồng thật của ứng dụng."""
    a = dat(db, nen, gio(9))
    with clock.freeze(a.end_at):
        care_records.ghi_ho_so(db, a.id, nguoi_ghi_id=nen["nv1"].id, tinh_trang="Da sạch.")
    return a, billing.lap_hoa_don(db, a.id)


def test_huy_lich_con_hoa_don_thi_thong_bao_neu_ma_hoa_don(db, nen):
    """TC-074."""
    a, hd = lich_da_lap_hoa_don(db, nen)

    with pytest.raises(LoiNghiepVu) as loi:
        nv.huy_lich(db, a.id, "Khách báo bận")

    assert f"#{hd.id}" in str(loi.value)
    assert a.status == "done"


def test_huy_hoa_don_roi_thi_ly_do_chan_khong_con_la_hoa_don(db, nen):
    """TC-075: lớp hóa đơn nhả ra, lớp trạng thái vẫn giữ.

    Ca biên của TC-074: chứng minh phép kiểm bám vào TRẠNG THÁI của hóa đơn chứ không
    phải vào việc có tồn tại bản ghi hóa đơn hay không.
    """
    a, hd = lich_da_lap_hoa_don(db, nen)
    billing.huy_hoa_don(db, hd.id)

    with pytest.raises(LoiNghiepVu) as loi:
        nv.huy_lich(db, a.id, "Khách báo bận")

    assert f"#{hd.id}" not in str(loi.value)
    assert TEN_TRANG_THAI["done"] in str(loi.value)


# --- Gọi thẳng hai hàm nền --------------------------------------------------------
#
# tim_lich_trung() và khung_gio_trong() tới giờ chỉ được kiểm gián tiếp qua dat_lich()
# và doi_lich(). Chúng là hàm public nên luật bao phủ ở CLAUDE.md mục 7 đòi test gọi
# thẳng: gián tiếp thì khi đỏ không biết lỗi nằm ở hàm nền hay ở lớp gọi nó.


def test_tim_lich_trung_tra_ve_dung_lich_bi_giao(db, nen):
    a = dat(db, nen, gio(9))

    trung = nv.tim_lich_trung(db, nen["pet1"].id, nen["nv1"].id, gio(9, 30), gio(10, 30))

    assert trung is not None
    assert trung.id == a.id


def test_tim_lich_trung_tra_ve_none_khi_khong_giao(db, nen):
    dat(db, nen, gio(9))

    assert nv.tim_lich_trung(db, nen["pet1"].id, nen["nv1"].id, gio(10), gio(11)) is None


def test_tim_lich_trung_bo_qua_id_loai_dung_ban_ghi_do(db, nen):
    """Ca biên của `bo_qua_id`: loại chính nó ra thì không còn lịch trùng nào."""
    a = dat(db, nen, gio(9))

    assert nv.tim_lich_trung(
        db, nen["pet1"].id, nen["nv1"].id, gio(9, 30), gio(10, 30), bo_qua_id=a.id
    ) is None


def test_khung_gio_trong_bat_dau_tu_gio_mo_cua_khi_lich_con_trong(db, nen):
    ket_qua = nv.khung_gio_trong(db, nen["nv1"].id, nen["pet1"].id, NGAY.date(), 60)

    assert ket_qua[0] == gio(nv.GIO_MO_CUA)
    assert len(ket_qua) == nv.SO_GOI_Y


def test_khung_gio_trong_rong_khi_thoi_luong_dai_hon_gio_lam_viec(db, nen):
    """Ca biên: dịch vụ 11 tiếng không nhét vừa khung 08:00–18:00 nào."""
    ket_qua = nv.khung_gio_trong(db, nen["nv1"].id, nen["pet1"].id, NGAY.date(), 11 * 60)

    assert ket_qua == []


def test_khung_gio_trong_toi_da_none_do_het_ngay_va_van_tinh_ca_khung_cuoi_khit_gio_dong_cua(db, nen):
    """P9 chặng 6: khách xem cả ngày. 08:00 → 17:00 bước 30 phút = 19 khung cho dịch vụ 60 phút; 17:00–18:00 vừa khít."""
    dat(db, nen, gio(9), pet="pet2")  # nv1 bận 09:00–10:00

    ket_qua = nv.khung_gio_trong(db, nen["nv1"].id, nen["pet1"].id, NGAY.date(), 60, toi_da=None)

    assert gio(8) in ket_qua and gio(10) in ket_qua and gio(17) in ket_qua
    assert gio(8, 30) not in ket_qua and gio(9) not in ket_qua and gio(9, 30) not in ket_qua
    assert gio(17, 30) not in ket_qua
    assert len(ket_qua) == 19 - 3
    assert len(ket_qua) > nv.SO_GOI_Y


def test_khung_gio_trong_mac_dinh_van_cat_o_so_goi_y(db, nen):
    """Chỗ gọi cũ (lễ tân bị từ chối rồi nhận gợi ý) không đổi hành vi."""
    assert len(nv.khung_gio_trong(db, nen["nv1"].id, nen["pet1"].id, NGAY.date(), 60)) == nv.SO_GOI_Y


# --- M-06 (= S6): buổi chăm sóc phải nằm trọn trong giờ mở cửa -------------------
#
# Lỗi tìm được khi rà soát 19/09: `dat_lich` không hề kiểm giờ làm việc. Đo trên giao
# diện: đặt được lịch 03:00, đặt được buổi 23:50 → 01:20 hôm sau, và một dịch vụ 2.000
# phút giữ nhân viên hơn 33 giờ. Hằng GIO_MO_CUA/GIO_DONG_CUA có từ P3 nhưng chỉ phần
# gợi ý khung trống dùng tới.
#
# Người dùng chốt 24/09: cả buổi phải nằm trọn trong giờ — bắt đầu >= 08:00 VÀ kết thúc
# <= 18:00, cùng một ngày. Một luật diệt cả ba triệu chứng.
#
# `frozen_clock` đứng ở 2026-03-12 08:00, nên mọi ca giờ sớm phải đặt sang NGÀY HÔM SAU:
# đặt 07:59 hôm nay sẽ vướng phép kiểm "không đặt lịch trong quá khứ" trước, và test sẽ
# xanh vì lý do sai.

MAI = NGAY + timedelta(days=1)


def gio_mai(h: int, p: int = 0) -> datetime:
    return MAI.replace(hour=h, minute=p)


def test_dat_lich_truoc_gio_mo_cua_bi_tu_choi(db, nen):
    """07:59 — sát dưới giờ mở cửa."""
    with pytest.raises(LoiNghiepVu) as e:
        dat(db, nen, gio_mai(7, 59))

    assert "08:00" in str(e.value) and "18:00" in str(e.value)


def test_dat_lich_dung_gio_mo_cua_duoc_nhan(db, nen):
    """Ca biên dưới: 08:00 là hợp lệ, không được chặn nhầm."""
    lich = dat(db, nen, gio_mai(8))

    assert lich.start_at == gio_mai(8)


def test_buoi_ket_thuc_dung_gio_dong_cua_duoc_nhan(db, nen):
    """Ca biên trên: 17:00 + 60 phút = đúng 18:00, phải được nhận.

    Đây là ca dễ hỏng nhất nếu viết `ket_thuc < GIO_DONG_CUA` thay vì `<=`.
    """
    lich = dat(db, nen, gio_mai(17))

    assert lich.end_at == gio_mai(18)


def test_buoi_vuot_gio_dong_cua_bi_tu_choi(db, nen):
    """17:30 + 60 phút = 18:30 — nhân viên phải ở lại sau giờ đóng cửa."""
    with pytest.raises(LoiNghiepVu):
        dat(db, nen, gio_mai(17, 30))


def test_lich_lan_qua_nua_dem_bi_tu_choi(db, nen):
    """23:50 + 60 phút = 00:50 hôm sau — chính ca đo được trên giao diện 19/09."""
    with pytest.raises(LoiNghiepVu):
        dat(db, nen, gio_mai(23, 50))


def test_doi_lich_ra_ngoai_gio_lam_viec_bi_tu_choi(db, nen):
    """Bài học 4 — sửa cả lớp lỗi: `doi_lich` cũng phải chịu đúng luật đó.

    Chặn ở `dat_lich` mà quên `doi_lich` thì đặt đúng giờ rồi dời ra 07:00 vẫn lọt.
    """
    lich = dat(db, nen, gio_mai(9))

    with pytest.raises(LoiNghiepVu):
        nv.doi_lich(db, lich.id, gio_mai(7))


def test_doi_lich_trong_gio_lam_viec_van_duoc(db, nen):
    """Ca đối chứng cho ca trên: đổi sang giờ hợp lệ vẫn phải chạy."""
    lich = dat(db, nen, gio_mai(9))

    sua = nv.doi_lich(db, lich.id, gio_mai(10))

    assert sua.start_at == gio_mai(10)


def test_dich_vu_dai_hon_ngay_lam_viec_khong_dat_duoc(db, nen):
    """Dịch vụ 2.000 phút — ca đo được 19/09, giữ nhân viên hơn 33 giờ.

    Dựng thẳng bằng model chứ không qua `catalog.tao_dich_vu`: từ 24/09 `catalog` chặn
    thời lượng quá một ngày làm việc, nhưng dịch vụ dài có thể đã nằm sẵn trong cơ sở dữ
    liệu từ trước bản vá. Đây đúng là ca mà lớp chặn thứ hai sinh ra để bắt.
    """
    dv_dai = Service(
        code="DAI", name="Dịch vụ rất dài", duration_min=2000, price=Decimal("10000")
    )
    db.add(dv_dai)
    db.commit()

    with pytest.raises(LoiNghiepVu):
        nv.dat_lich(
            db,
            thu_cung_id=nen["pet1"].id,
            dich_vu_id=dv_dai.id,
            nhan_vien_id=nen["nv1"].id,
            bat_dau=gio_mai(8),
            nguoi_tao_id=nen["letan"].id,
        )


# --- L-06: hai thông báo sai hướng ------------------------------------------------
#
# Đo bằng Chrome 24/09:
#  (a) Lập hóa đơn cho lịch **đã hủy** → "Ghi hồ sơ chăm sóc cho buổi này trước đã."
#      Buổi đã hủy thì ghi hồ sơ không giúp được gì; câu này đẩy người dùng đi sai đường.
#  (b) Đổi lịch mà **giữ nguyên giờ và nhân viên** → trạng thái vẫn nhảy sang "Đã đổi
#      lịch". Không có gì đổi cả, mà sổ thì ghi là đã dời.


def test_lap_hoa_don_cho_lich_da_huy_bao_dung_ly_do(db, nen):
    lich = dat(db, nen, gio(9))
    nv.huy_lich(db, lich.id, "Khách bận")

    with pytest.raises(LoiNghiepVu) as e:
        billing.lap_hoa_don(db, lich.id)

    thong_diep = str(e.value)
    assert "hủy" in thong_diep.lower()
    assert "Ghi hồ sơ chăm sóc cho buổi này trước" not in thong_diep


def test_lap_hoa_don_cho_lich_chua_lam_van_bao_ghi_ho_so(db, nen):
    """Ca đối chứng: câu cũ vẫn đúng cho lịch chưa làm — đừng đổi luôn cả ca nó đúng."""
    lich = dat(db, nen, gio(9))

    with pytest.raises(LoiNghiepVu) as e:
        billing.lap_hoa_don(db, lich.id)

    assert "Ghi hồ sơ chăm sóc" in str(e.value)


def test_doi_lich_giu_nguyen_gio_va_nhan_vien_khong_doi_trang_thai(db, nen):
    """(b): không có gì đổi thì trạng thái phải giữ nguyên."""
    lich = dat(db, nen, gio(9))
    trang_thai_cu = lich.status

    sua = nv.doi_lich(db, lich.id, gio(9), nhan_vien_id=nen["nv1"].id)

    assert sua.status == trang_thai_cu
    assert sua.start_at == gio(9)


def test_doi_lich_that_su_doi_gio_van_ghi_da_doi(db, nen):
    """Ca đối chứng: đổi thật thì vẫn phải ghi nhận là đã dời."""
    lich = dat(db, nen, gio(9))

    sua = nv.doi_lich(db, lich.id, gio(10), nhan_vien_id=nen["nv1"].id)

    assert sua.status == "rescheduled"


def test_doi_lich_giu_gio_nhung_doi_nhan_vien_van_ghi_da_doi(db, nen):
    """Ca biên: đổi người mà giữ giờ vẫn là một thay đổi thật."""
    lich = dat(db, nen, gio(9))

    sua = nv.doi_lich(db, lich.id, gio(9), nhan_vien_id=nen["nv2"].id)

    assert sua.status == "rescheduled"
    assert sua.staff_id == nen["nv2"].id


# --- P9 chặng 5: lịch chờ duyệt (`pending`) ------------------------------------------
#
# Khách tự xin lịch; lịch `pending` GIỮ CHỖ tới khi lễ tân duyệt/từ chối hoặc quá hạn
# `HAN_CHO_DUYET_GIO` giờ. Giữ chỗ nằm trong phép chống trùng nên đúng cả khi chưa ai quét.


@pytest.fixture
def dong_ho(frozen_clock):
    """Đồng hồ đã đóng băng, thêm `advance` để trôi thời gian trong một test."""

    class _DongHo:
        @staticmethod
        def advance(**kwargs):
            clock._moc_co_dinh = clock.now() + timedelta(**kwargs)

    return _DongHo()


@pytest.fixture
def khach(db):
    from app.models.customer import Customer

    k = Customer(email="khach1@example.com", full_name="Khach Mot", password_hash="x")
    db.add(k)
    db.commit()
    return k


@pytest.fixture
def khach2(db):
    from app.models.customer import Customer

    k = Customer(email="khach2@example.com", full_name="Khach Hai", password_hash="x")
    db.add(k)
    db.commit()
    return k


def mai(h: int) -> datetime:
    return gio(h) + timedelta(days=1)


def xin(db, nen, k, bat_dau, pet="pet1", nhan_vien="nv1", dich_vu="dv60"):
    return nv.tao_yeu_cau_lich(
        db,
        khach_id=k.id,
        thu_cung_id=nen[pet].id,
        dich_vu_id=nen[dich_vu].id,
        nhan_vien_id=nen[nhan_vien].id,
        bat_dau=bat_dau,
    )


def test_tao_yeu_cau_lich_tao_lich_pending_gan_voi_khach(db, nen, khach):
    lich = xin(db, nen, khach, gio(9))

    assert lich.status == "pending"
    assert lich.customer_id == khach.id
    assert lich.created_by is None
    assert lich.end_at == gio(10)
    assert lich.ten_trang_thai == "Chờ duyệt"


def test_lich_pending_giu_cho_chan_lich_trung_nhan_vien(db, nen, khach):
    xin(db, nen, khach, gio(9))

    with pytest.raises(LoiNghiepVu):
        dat(db, nen, gio(9, 30), pet="pet2")


def test_hai_khach_xin_cung_khung_gio_nguoi_den_sau_bi_chan(db, nen, khach, khach2):
    xin(db, nen, khach, gio(9))

    with pytest.raises(LoiNghiepVu):
        xin(db, nen, khach2, gio(9), pet="pet2")


def test_lich_pending_giu_cho_chan_trung_thu_cung(db, nen, khach):
    xin(db, nen, khach, gio(9), nhan_vien="nv1")

    with pytest.raises(LoiNghiepVu):
        dat(db, nen, gio(9), pet="pet1", nhan_vien="nv2")


def test_lich_pending_het_han_khong_con_giu_cho_du_chua_ai_quet(db, nen, khach, dong_ho):
    """Giữ chỗ do truy vấn quyết định, không phải do hàm quét: quá hạn là khung giờ trống ngay."""
    lich = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO + 1)

    assert nv.tim_lich_trung(db, nen["pet2"].id, nen["nv1"].id, gio(9), gio(10)) is None
    db.refresh(lich)
    assert lich.status == "pending"  # chưa ai quét, trạng thái vẫn cũ mà chỗ đã nhả


def test_lich_pending_dung_moc_han_thi_het_giu_cho(db, nen, khach, dong_ho):
    """Ca biên: đúng HAN_CHO_DUYET_GIO giờ là hết giữ chỗ; thiếu một giây thì còn."""
    xin(db, nen, khach, gio(9))

    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO, seconds=-1)
    assert nv.tim_lich_trung(db, nen["pet2"].id, nen["nv1"].id, gio(9), gio(10)) is not None

    dong_ho.advance(seconds=1)
    assert nv.tim_lich_trung(db, nen["pet2"].id, nen["nv1"].id, gio(9), gio(10)) is None


def test_huy_lich_cho_het_han_chi_huy_lich_qua_han(db, nen, khach, dong_ho):
    cu = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO - 1)
    moi = xin(db, nen, khach, mai(14))
    dong_ho.advance(hours=2)

    so = nv.huy_lich_cho_het_han(db)

    db.refresh(cu)
    db.refresh(moi)
    assert so == 1
    assert cu.status == "cancelled"
    assert cu.cancel_reason == nv.LY_DO_HET_HAN
    assert moi.status == "pending"
    assert nv.huy_lich_cho_het_han(db) == 0  # chạy lại không làm gì


def test_so_lich_cho_cua_khach_dem_dung_khach_va_bo_lich_het_han(db, nen, khach, khach2, dong_ho):
    xin(db, nen, khach, gio(9))
    xin(db, nen, khach, gio(11))
    xin(db, nen, khach2, gio(13), pet="pet2")
    assert nv.so_lich_cho_cua_khach(db, khach.id) == 2
    assert nv.so_lich_cho_cua_khach(db, khach2.id) == 1

    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO + 1)

    assert nv.so_lich_cho_cua_khach(db, khach.id) == 0


def test_khach_xin_qua_tran_lich_cho_bi_chan(db, nen, khach):
    for h in (8, 10, 12):
        xin(db, nen, khach, gio(h))

    with pytest.raises(LoiNghiepVu, match="tối đa"):
        xin(db, nen, khach, gio(14))


def test_tran_lich_cho_tinh_rieng_tung_khach(db, nen, khach, khach2):
    for h in (8, 10, 12):
        xin(db, nen, khach, gio(h))

    xin(db, nen, khach2, gio(14), pet="pet2")  # không ném lỗi


def test_lich_cho_het_han_khong_tinh_vao_tran(db, nen, khach, dong_ho):
    for h in (8, 10, 12):
        xin(db, nen, khach, gio(h))
    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO + 1)
    ngay_sau = clock.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)

    xin(db, nen, khach, ngay_sau)  # 3 lịch cũ đã hết hạn nên không còn chặn


def test_tao_yeu_cau_lich_dung_chung_phep_kiem_voi_dat_lich(db, nen, khach):
    """Khách xin ngoài giờ làm / vào quá khứ bị chặn y như lễ tân đặt."""
    with pytest.raises(LoiNghiepVu):
        xin(db, nen, khach, gio(3))
    with pytest.raises(LoiNghiepVu):
        xin(db, nen, khach, gio(7))


def test_duyet_lich_cho_chuyen_sang_booked_va_ghi_nguoi_duyet(db, nen, khach):
    lich = xin(db, nen, khach, gio(9))

    duyet = nv.duyet_lich_cho(db, lich.id, nen["letan"].id)

    assert duyet.status == "booked"
    assert duyet.decided_by == nen["letan"].id
    assert duyet.customer_id == khach.id


def test_duyet_lich_cho_khong_tu_bao_trung_voi_chinh_no(db, nen, khach):
    """Lịch pending đang giữ chỗ; duyệt không được coi chính nó là đối thủ trùng."""
    lich = xin(db, nen, khach, gio(9))

    assert nv.duyet_lich_cho(db, lich.id, nen["letan"].id).status == "booked"


def test_duyet_lich_cho_da_het_han_bi_tu_choi_va_lich_thanh_cancelled(db, nen, khach, dong_ho):
    lich = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO + 1)

    with pytest.raises(LoiNghiepVu, match="không còn chờ duyệt"):
        nv.duyet_lich_cho(db, lich.id, nen["letan"].id)

    db.refresh(lich)
    assert lich.status == "cancelled"


def test_duyet_lich_cho_khi_gio_hen_da_qua_bi_chan(db, nen, khach, dong_ho):
    lich = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=2)  # 10:00, giờ hẹn 09:00 đã qua, vẫn trong hạn 24h

    with pytest.raises(LoiNghiepVu, match="đã qua"):
        nv.duyet_lich_cho(db, lich.id, nen["letan"].id)

    db.refresh(lich)
    assert lich.status == "pending"


def test_duyet_lich_cho_khi_nhan_vien_bi_khoa_bi_chan(db, nen, khach):
    lich = xin(db, nen, khach, gio(9))
    nen["nv1"].is_active = False
    db.commit()

    with pytest.raises(LoiNghiepVu):
        nv.duyet_lich_cho(db, lich.id, nen["letan"].id)


def test_duyet_lich_khong_phai_pending_bi_chan(db, nen):
    lich = dat(db, nen, gio(9))

    with pytest.raises(LoiNghiepVu, match="không còn chờ duyệt"):
        nv.duyet_lich_cho(db, lich.id, nen["letan"].id)


def test_tu_choi_lich_cho_huy_lich_ghi_ly_do_va_tra_lai_khung_gio(db, nen, khach, khach2):
    lich = xin(db, nen, khach, gio(9))

    tu_choi = nv.tu_choi_lich_cho(db, lich.id, "Kín lịch hôm đó", nen["letan"].id)

    assert tu_choi.status == "cancelled"
    assert tu_choi.cancel_reason == "Kín lịch hôm đó"
    assert tu_choi.decided_by == nen["letan"].id
    xin(db, nen, khach2, gio(9), pet="pet2")  # khung giờ đã trống lại


def test_tu_choi_lich_cho_bat_buoc_co_ly_do(db, nen, khach):
    lich = xin(db, nen, khach, gio(9))

    for ly_do in ("", "   ", None):
        with pytest.raises(LoiNghiepVu, match="lý do"):
            nv.tu_choi_lich_cho(db, lich.id, ly_do, nen["letan"].id)

    db.refresh(lich)
    assert lich.status == "pending"


def test_tu_choi_lich_da_duyet_bi_chan(db, nen, khach):
    lich = xin(db, nen, khach, gio(9))
    nv.duyet_lich_cho(db, lich.id, nen["letan"].id)

    with pytest.raises(LoiNghiepVu, match="không còn chờ duyệt"):
        nv.tu_choi_lich_cho(db, lich.id, "muộn rồi", nen["letan"].id)


def test_danh_sach_cho_duyet_chi_co_pending_con_han_sap_theo_gio(db, nen, khach, dong_ho):
    cu = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO - 1)
    muon = xin(db, nen, khach, mai(15))
    som = xin(db, nen, khach, mai(11))
    dat(db, nen, mai(13), pet="pet2", nhan_vien="nv2")  # lịch booked: không có trong danh sách
    dong_ho.advance(hours=2)  # `cu` hết hạn

    ds = nv.danh_sach_cho_duyet(db)

    assert [x.id for x in ds] == [som.id, muon.id]
    db.refresh(cu)
    assert cu.status == "cancelled"


def test_lich_theo_ngay_khong_hien_lich_cho_het_han_nhu_con_cho(db, nen, khach, dong_ho):
    lich = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=nv.HAN_CHO_DUYET_GIO + 1)

    ds = nv.lich_theo_ngay(db, NGAY.date())

    assert all(x.id != lich.id or x.status == "cancelled" for x in ds)


# --- Trạng thái `pending` trong hóa đơn và hồ sơ chăm sóc ------------------------------


def test_lap_hoa_don_cho_lich_pending_bao_dung_ly_do(db, nen, khach):
    lich = xin(db, nen, khach, gio(9))

    with pytest.raises(LoiNghiepVu) as e:
        billing.lap_hoa_don(db, lich.id)

    thong_diep = str(e.value).lower()
    assert "chờ duyệt" in thong_diep
    assert "ghi hồ sơ chăm sóc cho buổi này trước" not in thong_diep


def test_ghi_ho_so_cho_lich_pending_da_qua_gio_hen_van_bi_chan(db, nen, khach, dong_ho):
    """Lịch chờ còn hạn 24h có thể mang giờ hẹn đã qua — không chặn thì nó nhảy thẳng sang `done`."""
    lich = xin(db, nen, khach, gio(9))
    dong_ho.advance(hours=3)

    with pytest.raises(LoiNghiepVu) as e:
        care_records.ghi_ho_so(db, lich.id, nen["nv1"].id, "Khỏe")

    assert "chờ duyệt" in str(e.value).lower()
