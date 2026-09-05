"""Test lịch hẹn qua HTTP — chặng 1 của P3.

Phục vụ US-10, US-11 — TC-035, TC-043, và phần còn thiếu của TC-024, TC-030 từ P2b.

Quy tắc trùng lịch đã kiểm kỹ ở tests/unit/test_scheduling.py, gồm cả ba thử nghiệm đột
biến chứng minh test bắt được lỗi. Ở đây chỉ kiểm phần thuộc tầng HTTP.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service

NGAY = "2026-03-12"


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


@pytest.fixture
def nen(db, seed_basic, frozen_clock):
    """Chủ nuôi, hai thú cưng, hai dịch vụ — một trong đó đã ngưng bán."""
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p1 = Pet(owner_id=o.id, name="Mực", species="Chó")
    p2 = Pet(owner_id=o.id, name="Bông", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    dv_ngung = Service(
        code="CU", name="Dịch vụ cũ", duration_min=30, price=Decimal("10000"), is_active=False
    )
    db.add_all([p1, p2, dv, dv_ngung])
    db.commit()

    return {
        "pet1": p1, "pet2": p2, "dv": dv, "dv_ngung": dv_ngung,
        "nv1": seed_basic["caretaker1"], "nv2": seed_basic["caretaker2"],
        # Lấy tên từ fixture thay vì viết cứng: seed_basic dùng tên không dấu,
        # viết cứng tên có dấu ở đây đã làm ba test đỏ một lần.
        "ten_nv1": seed_basic["caretaker1"].full_name,
        "ten_nv2": seed_basic["caretaker2"].full_name,
    }


def dat(client, nen, gio="09:00", pet="pet1", nhan_vien="nv1"):
    return client.post(
        "/appointments",
        data={
            "thu_cung_id": str(nen[pet].id),
            "dich_vu_id": str(nen["dv"].id),
            "nhan_vien_id": str(nen[nhan_vien].id),
            "ngay": NGAY,
            "gio": gio,
        },
        follow_redirects=True,
    )


# --- Phân quyền -----------------------------------------------------------------


@pytest.mark.parametrize("username", ["quanly", "letan"])
def test_quan_ly_va_le_tan_vao_duoc_trang_lich(client, nen, username):
    dang_nhap(client, username)

    assert client.get(f"/appointments?ngay={NGAY}").status_code == 200


def test_nhan_vien_cham_soc_khong_dat_duoc_lich(client, nen):
    """Nhân viên chăm sóc thực hiện lịch, không phải người đặt lịch."""
    dang_nhap(client, "chamsoc1")

    assert dat(client, nen).status_code == 403


# --- Đặt lịch --------------------------------------------------------------------


def test_lich_vua_tao_hien_dung_khung_gio_va_nhan_vien(client, nen):
    """TC-035."""
    dang_nhap(client, "letan")

    r = dat(client, nen, gio="09:00")

    assert r.status_code == 200
    assert "09:00" in r.text
    assert "10:00" in r.text  # giờ kết thúc tự tính từ thời lượng 60 phút
    assert nen["ten_nv1"] in r.text
    assert "Mực" in r.text


def test_form_dat_lich_chi_hien_dich_vu_dang_ban(client, nen):
    """TC-024 và TC-030, phần còn thiếu từ P2b."""
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Tắm và sấy" in r.text
    assert "Dịch vụ cũ" not in r.text


def test_dat_lich_gio_qua_khu_hien_loi(client, nen):
    """TC-033 qua HTTP. frozen_clock đang ở 08:00 ngày 12/03."""
    dang_nhap(client, "letan")

    r = dat(client, nen, gio="07:00")

    assert r.status_code == 400
    assert "quá khứ" in r.text.lower()


# --- Chặn trùng lịch qua API ------------------------------------------------------


def test_dat_lich_trung_bi_chan_qua_api(client, nen):
    """TC-043: chặn ở tầng service là chưa đủ, phải chặn cả qua HTTP."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")

    r = dat(client, nen, gio="09:30", pet="pet2")

    assert r.status_code == 400
    assert nen["ten_nv1"] in r.text


def test_thong_bao_tu_choi_hien_goi_y_khung_trong(client, nen):
    """TC-037 qua HTTP: lễ tân phải thấy khung trống ngay trên trang."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")

    r = dat(client, nen, gio="09:30", pet="pet2")

    assert "Khung giờ còn trống" in r.text
    assert "10:00" in r.text


def test_lich_lien_ke_dat_duoc_qua_api(client, nen):
    """TC-038 qua HTTP — ca dễ sai nhất."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")

    r = dat(client, nen, gio="10:00", pet="pet2")

    assert r.status_code == 200
    assert "10:00" in r.text
    assert "11:00" in r.text


def test_dat_lich_dich_vu_da_ngung_ban_bi_chan(client, nen):
    """Gõ thẳng id dịch vụ đã ngưng cũng phải bị chặn, không chỉ ẩn khỏi danh sách."""
    dang_nhap(client, "letan")

    r = client.post(
        "/appointments",
        data={
            "thu_cung_id": str(nen["pet1"].id),
            "dich_vu_id": str(nen["dv_ngung"].id),
            "nhan_vien_id": str(nen["nv1"].id),
            "ngay": NGAY,
            "gio": "09:00",
        },
        follow_redirects=True,
    )

    assert r.status_code == 400
    assert "ngưng bán" in r.text


# --- Lưới lịch --------------------------------------------------------------------


def test_loc_lich_theo_nhan_vien(client, nen):
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00", pet="pet1", nhan_vien="nv1")
    dat(client, nen, gio="09:00", pet="pet2", nhan_vien="nv2")

    r = client.get(f"/appointments?ngay={NGAY}&nhan_vien_id={nen['nv1'].id}")

    assert nen["ten_nv1"] in r.text
    assert nen["ten_nv2"] not in r.text.split("<select")[0]


def test_ngay_khong_co_lich_hien_trang_thai_rong(client, nen):
    """TC-052, phần làm được ở chặng 1."""
    dang_nhap(client, "letan")

    r = client.get("/appointments?ngay=2026-03-20")

    assert r.status_code == 200
    assert "Chưa có lịch hẹn nào" in r.text


def test_mac_dinh_mo_lich_hom_nay(client, nen):
    """Không truyền tham số ngày thì mở ngày hôm nay, không phải trang trống."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")

    r = client.get("/appointments")

    assert datetime.fromisoformat(NGAY).strftime("%d/%m/%Y") in r.text
