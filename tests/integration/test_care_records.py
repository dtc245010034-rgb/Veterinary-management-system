"""Test hồ sơ chăm sóc qua HTTP — chặng 1 của P4.

Phục vụ US-15, US-16 — TC-053, TC-054, TC-057, TC-058.

Quy tắc nghiệp vụ đã kiểm kỹ ở tests/unit/test_care_records_service.py. Ở đây chỉ kiểm
phần thuộc tầng HTTP: phân quyền, nút có hiện đúng lúc không, trang lịch sử.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.services import clock

NGAY = "2026-03-12"
BAY_GIO = datetime(2026, 3, 12, 8, 0)
SAU_BUOI = datetime(2026, 3, 12, 10, 30)


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


@pytest.fixture
def nen(db, seed_basic, frozen_clock):
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    p = Pet(owner_id=o.id, name="Mực", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    db.add_all([p, dv])
    db.commit()

    return {
        "pet": p, "dv": dv,
        "nv1": seed_basic["caretaker1"], "nv2": seed_basic["caretaker2"],
        "ten_nv1": seed_basic["caretaker1"].full_name,
    }


def dat(client, nen, gio="09:00", nhan_vien="nv1"):
    """Lễ tân đặt lịch. Phải đăng nhập lại sau vì hàm này đăng xuất."""
    dang_nhap(client, "letan")
    r = client.post(
        "/appointments",
        data={
            "thu_cung_id": str(nen["pet"].id),
            "dich_vu_id": str(nen["dv"].id),
            "nhan_vien_id": str(nen[nhan_vien].id),
            "ngay": NGAY,
            "gio": gio,
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    client.post("/logout")


def ma_lich(db):
    from sqlalchemy import select

    from app.models.appointment import Appointment

    return db.scalars(select(Appointment).order_by(Appointment.start_at)).first().id


def ghi(client, ma, tinh_trang="Da khô nhẹ, tai sạch.", luc=SAU_BUOI, **them):
    """Buổi chăm sóc đã kết thúc thì mới ghi được, nên phải dịch đồng hồ."""
    du_lieu = {"tinh_trang": tinh_trang, **them}
    with clock.freeze(luc):
        return client.post(f"/appointments/{ma}/ho-so", data=du_lieu, follow_redirects=True)


# --- Ghi hồ sơ -------------------------------------------------------------------


def test_nhan_vien_ghi_ho_so_cho_lich_cua_minh(client, db, nen):
    """TC-053 qua HTTP."""
    dat(client, nen)
    ma = ma_lich(db)
    dang_nhap(client, "chamsoc1")

    r = ghi(client, ma, viec_da_lam="Tắm, sấy, cắt móng")

    assert r.status_code == 200
    assert "Hoàn thành" in r.text


def test_nhan_vien_khac_khong_ghi_duoc_ho_so(client, db, nen):
    """TC-054 qua HTTP."""
    dat(client, nen, nhan_vien="nv1")
    ma = ma_lich(db)
    dang_nhap(client, "chamsoc2")

    r = ghi(client, ma)

    assert r.status_code == 400


def test_le_tan_khong_ghi_duoc_ho_so(client, db, nen):
    dat(client, nen)
    ma = ma_lich(db)
    dang_nhap(client, "letan")

    r = ghi(client, ma)

    assert r.status_code == 403


def test_bo_trong_tinh_trang_hien_loi(client, db, nen):
    """TC-056 qua HTTP."""
    dat(client, nen)
    ma = ma_lich(db)
    dang_nhap(client, "chamsoc1")

    r = ghi(client, ma, tinh_trang="  ")

    assert r.status_code == 400
    assert "tình trạng" in r.text.lower()


def test_ghi_ho_so_cho_buoi_chua_dien_ra_hien_loi(client, db, nen):
    """Quyết định 5 của P4, qua HTTP."""
    dat(client, nen)
    ma = ma_lich(db)
    dang_nhap(client, "chamsoc1")

    r = ghi(client, ma, luc=BAY_GIO)

    assert r.status_code == 400
    assert "chưa diễn ra" in r.text


# --- Nút và form -----------------------------------------------------------------


def test_nut_ghi_ho_so_khong_hien_khi_buoi_chua_dien_ra(client, db, nen):
    dat(client, nen)
    dang_nhap(client, "chamsoc1")

    with clock.freeze(BAY_GIO):
        r = client.get(f"/appointments/cua-toi?ngay={NGAY}")

    assert "Ghi hồ sơ" not in r.text


def test_nut_ghi_ho_so_hien_sau_khi_buoi_ket_thuc(client, db, nen):
    dat(client, nen)
    dang_nhap(client, "chamsoc1")

    with clock.freeze(SAU_BUOI):
        r = client.get(f"/appointments/cua-toi?ngay={NGAY}")

    assert "Ghi hồ sơ" in r.text


def test_sau_khi_ghi_ho_so_lich_khong_con_doi_hay_huy_duoc(client, db, nen):
    """Đóng vòng với P3 — đây là ô smoke chuyển từ khối P3 sang."""
    dat(client, nen)
    ma = ma_lich(db)
    dang_nhap(client, "chamsoc1")
    ghi(client, ma)
    client.post("/logout")
    dang_nhap(client, "letan")

    with clock.freeze(SAU_BUOI):
        r_xem = client.get(f"/appointments?ngay={NGAY}")
        r_huy = client.post(
            f"/appointments/{ma}/huy",
            data={"ngay": NGAY, "ly_do": "Đổi ý"},
            follow_redirects=True,
        )

    assert "Hủy" not in r_xem.text
    assert r_huy.status_code == 400


# --- Lịch sử chăm sóc ------------------------------------------------------------


def test_trang_thu_cung_hien_lich_su_cham_soc(client, db, nen):
    """TC-057 qua HTTP."""
    dat(client, nen)
    ma = ma_lich(db)
    dang_nhap(client, "chamsoc1")
    ghi(client, ma, tinh_trang="Da khô nhẹ ở lưng")
    client.post("/logout")
    dang_nhap(client, "letan")

    r = client.get(f"/pets/{nen['pet'].id}")

    assert r.status_code == 200
    assert "Da khô nhẹ ở lưng" in r.text
    assert "Tắm và sấy" in r.text
    assert nen["ten_nv1"] in r.text


def test_thu_cung_chua_dung_dich_vu_hien_trang_thai_rong(client, db, nen):
    """TC-058 qua HTTP."""
    dang_nhap(client, "letan")

    r = client.get(f"/pets/{nen['pet'].id}")

    assert r.status_code == 200
    assert "Chưa có hồ sơ chăm sóc nào" in r.text


def test_trang_thu_cung_khong_ton_tai_tra_ve_404(client, nen):
    dang_nhap(client, "letan")

    assert client.get("/pets/9999").status_code == 404
