"""Test cho app/services/stats.py — thống kê lượt dịch vụ, doanh thu, khách quay lại.

Phục vụ US-22, US-23 — TC-076 → TC-081. Định nghĩa số liệu do người dùng chốt ngày 11/09,
xem docs/plans/2026-09-11-p6-thong-ke.md:

- Lượt dịch vụ: mọi lịch CHƯA HỦY có ngày hẹn trong kỳ.
- Doanh thu: tiền thực nhận, lọc theo NGÀY THU. Số chưa thu: phần còn nợ của hóa đơn LẬP
  trong kỳ.
- Khách quay lại: chủ nuôi có lịch chưa hủy vào ≥ 2 NGÀY khác nhau trong kỳ.

Mọi sai ở đây đều là loại sai âm thầm — không exception, chỉ có con số lệch. Nên dữ liệu
đi qua đúng luồng thật (đặt lịch, ghi hồ sơ, lập hóa đơn, thu tiền) chứ không dựng model
bằng tay: trạng thái và ngày tháng phải giống hệt thứ người dùng tạo ra.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.services import billing, care_records, catalog, clock, scheduling
from app.services import stats as nv
from app.services.errors import LoiNghiepVu

THANG_3 = (date(2026, 3, 1), date(2026, 3, 31))


def gio(ngay: int, h: int = 9, p: int = 0, thang: int = 3) -> datetime:
    return datetime(2026, thang, ngay, h, p)


@pytest.fixture
def nen(db, frozen_clock):
    """Ba chủ nuôi, bốn thú cưng, hai dịch vụ. "Bây giờ" là 12/03/2026 08:00."""
    hang = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    dat = Owner(full_name="Trần Quốc Đạt", phone="0987654321")
    ha = Owner(full_name="Lý Thu Hà", phone="0905112233")
    db.add_all([hang, dat, ha])
    db.flush()

    muc = Pet(owner_id=hang.id, name="Mực", species="Chó")
    mun = Pet(owner_id=hang.id, name="Mun", species="Mèo")
    dau_do = Pet(owner_id=dat.id, name="Đậu Đỏ", species="Mèo")
    bong = Pet(owner_id=ha.id, name="Bông", species="Chó")
    tam = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    cat_mong = Service(code="CATMONG", name="Cắt móng", duration_min=30, price=Decimal("50000"))
    cs = User(username="cs1", password_hash="b", full_name="Lê Văn Chăm", role="caretaker")
    lt = User(username="letan", password_hash="b", full_name="Trần Thị Lễ", role="receptionist")
    db.add_all([muc, mun, dau_do, bong, tam, cat_mong, cs, lt])
    db.commit()
    return {
        "muc": muc, "mun": mun, "dau_do": dau_do, "bong": bong,
        "tam": tam, "cat_mong": cat_mong, "cs": cs, "letan": lt,
    }


def dat(db, nen, thu_cung, bat_dau, dich_vu=None):
    """Đặt lịch như lễ tân đặt — một ngày trước giờ hẹn, để lọt luật "không đặt quá khứ"."""
    with clock.freeze(bat_dau - timedelta(days=1)):
        return scheduling.dat_lich(
            db,
            thu_cung_id=nen[thu_cung].id,
            dich_vu_id=(dich_vu or nen["tam"]).id,
            nhan_vien_id=nen["cs"].id,
            bat_dau=bat_dau,
            nguoi_tao_id=nen["letan"].id,
        )


def xong(db, nen, lich):
    """Nhân viên ghi hồ sơ ngay khi buổi kết thúc — lịch chuyển `done`."""
    with clock.freeze(lich.end_at):
        care_records.ghi_ho_so(db, lich.id, nguoi_ghi_id=nen["cs"].id, tinh_trang="Ổn.")
    return lich


def lap(db, lich, luc: datetime):
    with clock.freeze(luc):
        return billing.lap_hoa_don(db, lich.id)


def thu(db, hoa_don, so_tien: str, luc: datetime):
    with clock.freeze(luc):
        billing.ghi_nhan_thanh_toan(db, hoa_don.id, Decimal(so_tien))


def buoi_da_thu_du(db, nen, thu_cung, bat_dau, dich_vu=None):
    """Một buổi trọn vòng: đặt, làm xong, lập hóa đơn và thu đủ ngay trong ngày."""
    lich = xong(db, nen, dat(db, nen, thu_cung, bat_dau, dich_vu))
    hd = lap(db, lich, lich.end_at)
    thu(db, hd, str(hd.total_amount), lich.end_at)
    return lich


# --- Lượt và doanh thu (US-22) ----------------------------------------------------


def test_thong_ke_tong_luot_doanh_thu_va_chia_theo_dich_vu(db, nen):
    """TC-076."""
    buoi_da_thu_du(db, nen, "muc", gio(3))
    buoi_da_thu_du(db, nen, "mun", gio(5), nen["cat_mong"])
    buoi_da_thu_du(db, nen, "dau_do", gio(10))

    tk = nv.thong_ke(db, *THANG_3)

    assert tk.so_luot == 3
    assert tk.doanh_thu == Decimal("350000")
    assert tk.chua_thu == Decimal("0")
    # Doanh thu giảm dần: tắm (2 lượt, 300.000) đứng trên cắt móng.
    assert [(d.ten, d.so_luot, d.doanh_thu) for d in tk.theo_dich_vu] == [
        ("Tắm và sấy", 2, Decimal("300000")),
        ("Cắt móng", 1, Decimal("50000")),
    ]


def test_bang_theo_dich_vu_cong_lai_bang_dung_hai_con_so_tong(db, nen):
    """Bất biến của bảng chia: không dòng nào bị rơi hay đếm hai lần."""
    buoi_da_thu_du(db, nen, "muc", gio(3))
    buoi_da_thu_du(db, nen, "mun", gio(5), nen["cat_mong"])
    dat(db, nen, "bong", gio(20))  # lượt chưa có đồng nào

    tk = nv.thong_ke(db, *THANG_3)

    assert sum(d.so_luot for d in tk.theo_dich_vu) == tk.so_luot == 3
    assert sum(d.doanh_thu for d in tk.theo_dich_vu) == tk.doanh_thu


def test_doanh_thu_chi_tinh_tien_da_thu_so_chua_thu_hien_rieng(db, nen):
    """TC-077: hóa đơn chưa thu và thu một phần không được cộng vào doanh thu."""
    lap(db, xong(db, nen, dat(db, nen, "muc", gio(3))), gio(3, 11))
    hd = lap(db, xong(db, nen, dat(db, nen, "mun", gio(4))), gio(4, 11))
    thu(db, hd, "60000", gio(4, 11))

    tk = nv.thong_ke(db, *THANG_3)

    assert tk.doanh_thu == Decimal("60000")
    assert tk.chua_thu == Decimal("150000") + Decimal("90000")


def test_hoa_don_da_huy_khong_cong_vao_so_chua_thu(db, nen):
    """TC-077 biên: `total_amount` của hóa đơn đã hủy vẫn còn nguyên — đừng cộng nhầm nó."""
    lich = xong(db, nen, dat(db, nen, "muc", gio(3)))
    hd = lap(db, lich, gio(3, 11))
    billing.huy_hoa_don(db, hd.id)

    tk = nv.thong_ke(db, *THANG_3)

    assert tk.chua_thu == Decimal("0")
    assert tk.doanh_thu == Decimal("0")
    # Buổi chăm sóc vẫn đã diễn ra — hủy hóa đơn không xóa lượt dịch vụ.
    assert tk.so_luot == 1


def test_hoa_don_lap_ky_truoc_thu_ky_nay_vao_doanh_thu_ky_nay(db, nen):
    """Doanh thu theo NGÀY THU: tiền nhận tháng 3 là doanh thu tháng 3, dù hóa đơn lập tháng 2.

    Và doanh thu tháng 2 không tự tăng khi khách trả nợ vào tháng 3 — lý do chọn mốc này.
    """
    lich = xong(db, nen, dat(db, nen, "muc", gio(25, thang=2)))
    hd = lap(db, lich, gio(25, 11, thang=2))
    thu(db, hd, "150000", gio(2, 10))

    thang_3 = nv.thong_ke(db, *THANG_3)
    thang_2 = nv.thong_ke(db, date(2026, 2, 1), date(2026, 2, 28))

    assert thang_3.doanh_thu == Decimal("150000")
    assert thang_3.chua_thu == Decimal("0")  # hóa đơn không lập trong tháng 3
    assert thang_3.so_luot == 0  # buổi chăm sóc ở tháng 2
    assert thang_2.doanh_thu == Decimal("0")
    assert thang_2.so_luot == 1


def test_ky_tinh_ca_hai_ngay_dau_va_cuoi(db, nen):
    """Kỳ là [từ ngày, đến ngày] tính cả hai đầu — ca biên của cả lượt lẫn doanh thu."""
    lich = xong(db, nen, dat(db, nen, "muc", gio(10)))
    hd = lap(db, lich, gio(10, 11))
    thu(db, hd, "50000", gio(10, 23, 59))
    thu(db, hd, "100000", gio(11, 0, 0))

    ngay_10 = nv.thong_ke(db, date(2026, 3, 10), date(2026, 3, 10))
    truoc_do = nv.thong_ke(db, date(2026, 3, 1), date(2026, 3, 9))
    ngay_11 = nv.thong_ke(db, date(2026, 3, 11), date(2026, 3, 11))

    assert (ngay_10.so_luot, ngay_10.doanh_thu) == (1, Decimal("50000"))
    assert (truoc_do.so_luot, truoc_do.doanh_thu) == (0, Decimal("0"))
    assert (ngay_11.so_luot, ngay_11.doanh_thu) == (0, Decimal("100000"))


def test_luot_gom_moi_lich_chua_huy_va_bo_lich_da_huy(db, nen):
    """Lượt = lịch chưa hủy: đã đặt, đã đổi lịch, đã hoàn thành đều tính."""
    xong(db, nen, dat(db, nen, "dau_do", gio(10)))
    dat(db, nen, "muc", gio(15))
    doi = dat(db, nen, "mun", gio(16))
    scheduling.doi_lich(db, doi.id, gio(17))
    huy = dat(db, nen, "bong", gio(18))
    scheduling.huy_lich(db, huy.id, "Khách báo bận")

    tk = nv.thong_ke(db, *THANG_3)

    assert tk.so_luot == 3
    assert tk.so_luot_hoan_thanh == 1


def test_dem_lich_da_qua_gio_ma_chua_ghi_ho_so(db, nen):
    """Lỗ hổng S5 (kế hoạch P7 chặng 0).

    Lượt dịch vụ đếm mọi lịch chưa hủy (định nghĩa đã chốt 11/09), nên buổi khách không đến
    hoặc nhân viên quên ghi hồ sơ vẫn được tính. `services/care_records.py` từng hứa P6 sẽ
    hiện chỉ báo cho đúng nhóm này — lời hứa chưa làm. Con số phải tách ra được.
    """
    dat(db, nen, "muc", gio(3))                     # qua giờ, chưa ghi → tính
    doi = dat(db, nen, "bong", gio(4))
    with clock.freeze(gio(3)):
        scheduling.doi_lich(db, doi.id, gio(6))     # đã đổi lịch, qua giờ → tính
    xong(db, nen, dat(db, nen, "mun", gio(5)))      # đã ghi → không tính
    dat(db, nen, "dau_do", gio(20))                 # chưa tới giờ → không tính

    tk = nv.thong_ke(db, *THANG_3)

    assert tk.so_luot == 4
    assert tk.so_lich_qua_gio_chua_ghi == 2


def test_lich_vua_ket_thuc_dung_bay_gio_da_tinh_la_qua_gio(db, nen):
    """Biên: buổi kết thúc ĐÚNG lúc "bây giờ" đã xong, chưa ghi thì là thiếu.

    Bản cũ dựng buổi 07:00–08:00 để chạm mốc 08:00 của `frozen_clock`. Từ 24/09 lịch phải
    nằm trọn trong giờ mở cửa (M-06) nên 07:00 không đặt được nữa, và mọi buổi kết thúc
    đúng 08:00 đều phải bắt đầu trước giờ mở cửa. Dời cả cảnh vào trong giờ và cố định
    "bây giờ" ở 10:00 ngay lúc gọi thống kê — vẫn đúng ca biên cũ, chỉ khác con số.
    """
    dat(db, nen, "muc", gio(12, 9))   # 09:00–10:00, kết thúc đúng "bây giờ"
    dat(db, nen, "mun", gio(12, 10))  # 10:00–11:00 vừa bắt đầu → không tính

    with clock.freeze(gio(12, 10)):
        tk = nv.thong_ke(db, *THANG_3)

    assert tk.so_lich_qua_gio_chua_ghi == 1


def test_dich_vu_da_ngung_ban_van_co_dong_trong_bang(db, nen):
    """Việc 5 của roadmap P6: lọc `is_active` là làm hóa đơn cũ biến khỏi sổ, âm thầm."""
    buoi_da_thu_du(db, nen, "mun", gio(5), nen["cat_mong"])
    catalog.ngung_ban(db, nen["cat_mong"].id)

    tk = nv.thong_ke(db, *THANG_3)

    assert [(d.ten, d.dang_ban, d.doanh_thu) for d in tk.theo_dich_vu] == [
        ("Cắt móng", False, Decimal("50000"))
    ]
    assert tk.doanh_thu == Decimal("50000")


def test_ky_khong_co_du_lieu_ra_so_0_khong_loi(db, nen):
    """TC-078: không chia cho 0 khi không có khách nào."""
    tk = nv.thong_ke(db, *THANG_3)

    assert (tk.so_luot, tk.so_luot_hoan_thanh) == (0, 0)
    assert (tk.doanh_thu, tk.chua_thu) == (Decimal("0"), Decimal("0"))
    assert tk.theo_dich_vu == []
    assert (tk.so_khach, tk.so_khach_quay_lai, tk.ti_le_quay_lai) == (0, 0, Decimal("0"))


def test_ngay_bat_dau_sau_ngay_ket_thuc_bi_tu_choi(db, nen):
    """TC-079."""
    with pytest.raises(LoiNghiepVu, match="Ngày bắt đầu"):
        nv.thong_ke(db, date(2026, 3, 10), date(2026, 3, 9))


def test_ky_mot_ngay_hop_le(db, nen):
    """TC-079 biên: từ ngày = đến ngày là kỳ một ngày, không phải kỳ ngược."""
    tk = nv.thong_ke(db, date(2026, 3, 10), date(2026, 3, 10))

    assert tk.tu_ngay == tk.den_ngay == date(2026, 3, 10)


# --- Khách quay lại (US-23) --------------------------------------------------------


def test_khach_quay_lai_tinh_theo_so_ngay_den_khong_theo_so_luot(db, nen):
    """TC-080.

    Đạt đến hai ngày khác nhau → quay lại. Hằng mang HAI con đi trong CÙNG một ngày → một
    lần đến, chưa phải quay lại. Hà một lần, cộng một lịch đã hủy không được tính.
    """
    dat(db, nen, "dau_do", gio(3))
    dat(db, nen, "dau_do", gio(5))
    dat(db, nen, "muc", gio(4, 9))
    dat(db, nen, "mun", gio(4, 11))
    dat(db, nen, "bong", gio(6))
    huy = dat(db, nen, "bong", gio(8))
    scheduling.huy_lich(db, huy.id, "Khách báo bận")

    tk = nv.thong_ke(db, *THANG_3)

    assert (tk.so_khach, tk.so_khach_quay_lai) == (3, 1)
    assert tk.ti_le_quay_lai == Decimal("33.3")


def test_moi_khach_chi_den_mot_lan_ti_le_quay_lai_bang_0(db, nen):
    """TC-081."""
    dat(db, nen, "muc", gio(3))
    dat(db, nen, "dau_do", gio(4))
    dat(db, nen, "bong", gio(5))

    tk = nv.thong_ke(db, *THANG_3)

    assert (tk.so_khach, tk.so_khach_quay_lai, tk.ti_le_quay_lai) == (3, 0, Decimal("0"))


# --- Kỳ mặc định ----------------------------------------------------------------


def test_ky_mac_dinh_la_30_ngay_gan_nhat_tinh_ca_hom_nay(frozen_clock):
    assert nv.ky_mac_dinh() == (date(2026, 2, 11), date(2026, 3, 12))


def test_ky_mac_dinh_ket_thuc_o_ngay_duoc_chon(frozen_clock):
    """Biên: người dùng chỉ chọn "Đến ngày" — 30 ngày tính lùi từ ngày đó, không từ hôm nay."""
    assert nv.ky_mac_dinh(date(2025, 6, 30)) == (date(2025, 6, 1), date(2025, 6, 30))
