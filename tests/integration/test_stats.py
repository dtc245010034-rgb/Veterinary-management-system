"""Test trang thống kê qua HTTP — P6 chặng 2.

Phục vụ US-02 (TC-006) và US-22, US-23 ở mức integration. Cách tính số liệu đã kiểm kỹ ở
tests/unit/test_stats_service.py; ở đây chỉ kiểm phần thuộc tầng HTTP: phân quyền, đọc
ngày từ query string, kỳ mặc định, và việc trang giữ lại ngày đã nhập khi báo lỗi.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.services import billing, care_records, clock, scheduling


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


@pytest.fixture
def nen(db, seed_basic, frozen_clock):
    """Một buổi 12/03 09:00 đã làm xong, lập hóa đơn 150.000đ, khách trả trước 50.000đ.

    "Bây giờ" là 12/03/2026 08:00 nên buổi này nằm trong kỳ mặc định (11/02 → 12/03).
    """
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()
    pet = Pet(owner_id=o.id, name="Mực", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    db.add_all([pet, dv])
    db.commit()

    lich = scheduling.dat_lich(
        db,
        thu_cung_id=pet.id,
        dich_vu_id=dv.id,
        nhan_vien_id=seed_basic["caretaker1"].id,
        bat_dau=datetime(2026, 3, 12, 9, 0),
        nguoi_tao_id=seed_basic["receptionist"].id,
    )
    with clock.freeze(lich.end_at):
        care_records.ghi_ho_so(
            db, lich.id, nguoi_ghi_id=seed_basic["caretaker1"].id, tinh_trang="Ổn."
        )
        hd = billing.lap_hoa_don(db, lich.id)
        billing.ghi_nhan_thanh_toan(db, hd.id, Decimal("50000"))
    return seed_basic


# --- Phân quyền (US-02) -----------------------------------------------------------


def test_caretaker_mo_trang_thong_ke_bi_chan_403(client, nen):
    """TC-006 — hoãn từ P1 vì khi đó chưa có trang này."""
    dang_nhap(client, "chamsoc1")

    r = client.get("/stats")

    assert r.status_code == 403
    assert "150.000đ" not in r.text and "50.000đ" not in r.text


def test_le_tan_mo_trang_thong_ke_bi_chan_403(client, nen):
    """Bảng phân quyền US-02: thống kê chỉ dành cho quản lý."""
    dang_nhap(client, "letan")

    assert client.get("/stats").status_code == 403


# --- Trang của quản lý ------------------------------------------------------------


def test_quan_ly_mo_thong_ke_thay_so_lieu_ky_mac_dinh(client, nen):
    """Không truyền ngày → 30 ngày gần nhất, và hai ô ngày điền sẵn đúng kỳ đó."""
    dang_nhap(client, "quanly")

    r = client.get("/stats")

    assert r.status_code == 200
    assert 'value="2026-02-11"' in r.text and 'value="2026-03-12"' in r.text
    assert "50.000đ" in r.text  # doanh thu: tiền thực nhận
    assert "100.000đ" in r.text  # chưa thu: phần còn nợ, hiện riêng
    assert "Tắm và sấy" in r.text


def test_ky_khong_co_du_lieu_hien_so_0_va_trang_thai_rong(client, nen):
    """TC-078 ở tầng HTTP: kỳ trống là trang bình thường, không phải trang lỗi."""
    dang_nhap(client, "quanly")

    r = client.get("/stats", params={"tu_ngay": "2025-01-01", "den_ngay": "2025-01-31"})

    assert r.status_code == 200
    assert "0đ" in r.text
    # Cùng một chữ số lẻ như kỳ có khách mà không ai quay lại ("0,0%") — rà trên app thật
    # 11/09 thấy kỳ trống hiện "0%", hai cách viết cho cùng một con số.
    assert "0,0%" in r.text
    assert "Không có lượt dịch vụ hay khoản thu nào" in r.text
    assert "Tắm và sấy" not in r.text


def test_ngay_bat_dau_sau_ngay_ket_thuc_bao_loi_va_giu_ngay_da_nhap(client, nen):
    """TC-079 ở tầng HTTP: báo lỗi mà xóa ngày đã chọn thì người dùng phải chọn lại."""
    dang_nhap(client, "quanly")

    r = client.get("/stats", params={"tu_ngay": "2026-03-12", "den_ngay": "2026-03-01"})

    assert r.status_code == 400
    assert "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc" in r.text
    assert 'value="2026-03-12"' in r.text and 'value="2026-03-01"' in r.text


def test_bo_trong_tu_ngay_lay_30_ngay_ket_thuc_o_den_ngay(client, nen):
    """Lỗi thật, rà bằng trình duyệt 11/09: xóa trống "Từ ngày", chọn "Đến ngày" năm ngoái.

    Hệ thống lấy "Từ ngày" = 30 ngày trước HÔM NAY, tức sau "Đến ngày", rồi báo "Ngày bắt
    đầu phải trước…" — trách người dùng về một ngày họ không hề chọn. Kỳ mặc định phải là
    30 ngày KẾT THÚC Ở "Đến ngày" đã chọn.
    """
    dang_nhap(client, "quanly")

    r = client.get("/stats", params={"tu_ngay": "", "den_ngay": "2025-06-30"})

    assert r.status_code == 200
    assert 'value="2025-06-01"' in r.text and 'value="2025-06-30"' in r.text


def test_ngay_sai_dinh_dang_bao_loi_tieng_viet(client, nen):
    """Gõ tay vào URL, hoặc trình duyệt cũ không có ô chọn ngày — không được ra lỗi 422 thô."""
    dang_nhap(client, "quanly")

    r = client.get("/stats", params={"tu_ngay": "12/03/2026", "den_ngay": ""})

    assert r.status_code == 400
    assert "Ngày không hợp lệ" in r.text


def test_trang_thong_ke_canh_bao_lich_qua_gio_chua_ghi_ho_so(client, db, nen):
    """S5 (kế hoạch P7 chặng 0): quản lý phải đọc được bao nhiêu lượt chưa có hồ sơ.

    Buổi 10:00 ngày 11/03 đã qua mà không ai ghi hồ sơ — nó vẫn nằm trong "Lượt dịch vụ".
    """
    thu_cung = db.query(Pet).one()
    dich_vu = db.query(Service).one()
    with clock.freeze(datetime(2026, 3, 10, 8, 0)):
        scheduling.dat_lich(
            db,
            thu_cung_id=thu_cung.id,
            dich_vu_id=dich_vu.id,
            nhan_vien_id=nen["caretaker1"].id,
            bat_dau=datetime(2026, 3, 11, 10, 0),
            nguoi_tao_id=nen["receptionist"].id,
        )
    dang_nhap(client, "quanly")

    r = client.get("/stats")

    assert "1 lịch đã qua giờ nhưng chưa ghi hồ sơ" in r.text


def test_trang_thong_ke_khong_canh_bao_khi_moi_lich_qua_gio_deu_co_ho_so(client, nen):
    """Biên của ca trên: fixture chỉ có một buổi và buổi đó đã ghi hồ sơ."""
    dang_nhap(client, "quanly")

    r = client.get("/stats")

    assert "chưa ghi hồ sơ" not in r.text
