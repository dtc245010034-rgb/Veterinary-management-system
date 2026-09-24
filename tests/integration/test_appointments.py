"""Test lịch hẹn qua HTTP — chặng 1 của P3.

Phục vụ US-10, US-11 — TC-035, TC-043, và phần còn thiếu của TC-024, TC-030 từ P2b.

Quy tắc trùng lịch đã kiểm kỹ ở tests/unit/test_scheduling.py, gồm cả ba thử nghiệm đột
biến chứng minh test bắt được lỗi. Ở đây chỉ kiểm phần thuộc tầng HTTP.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.appointment import Appointment
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


# --- Đổi lịch và hủy lịch qua HTTP (chặng 2) ---------------------------------------


def id_lich(db):
    """Lấy id lịch sớm nhất — test qua HTTP nhưng vẫn cần id để dựng URL."""
    return db.scalars(select(Appointment).order_by(Appointment.start_at)).first().id


def test_doi_lich_qua_api_cap_nhat_gio_moi(client, db, nen):
    """TC-044 qua HTTP."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")
    ma = id_lich(db)

    r = client.post(
        f"/appointments/{ma}/doi",
        data={"ngay": NGAY, "gio": "14:00", "nhan_vien_id": str(nen["nv1"].id)},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "14:00" in r.text
    assert "Đã đổi lịch" in r.text


def test_doi_lich_trung_qua_api_giu_nguyen_gio_cu(client, db, nen):
    """TC-045 qua HTTP: từ chối và lịch cũ vẫn nguyên giờ ban đầu."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")
    dat(client, nen, gio="14:00", pet="pet2")
    ma = id_lich(db)

    r = client.post(
        f"/appointments/{ma}/doi",
        data={"ngay": NGAY, "gio": "14:00", "nhan_vien_id": str(nen["nv1"].id)},
        follow_redirects=True,
    )

    assert r.status_code == 400
    db.expire_all()
    assert db.get(Appointment, ma).start_at.strftime("%H:%M") == "09:00"


@pytest.mark.parametrize("ngay_sai", ["abc", "2026-13-45", ""])
def test_doi_lich_ngay_sai_dinh_dang_bao_loi_khong_doi_ve_hom_nay(client, db, nen, ngay_sai):
    """Lỗi H-02 (S7) tìm được khi rà 19/09: ngày hỏng từng bị quy thành hôm nay, và lịch
    thật đã bị dời sang 23:30 hôm đó mà không một dòng cảnh báo."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")
    ma = id_lich(db)

    r = client.post(
        f"/appointments/{ma}/doi",
        data={"ngay": ngay_sai, "gio": "23:30", "nhan_vien_id": str(nen["nv1"].id)},
    )

    assert r.status_code == 400
    assert "Ngày không đúng định dạng" in r.text
    db.expire_all()
    assert db.get(Appointment, ma).start_at == datetime(2026, 3, 12, 9, 0)


@pytest.mark.parametrize("ngay_sai", ["2026-13-45", ""])
def test_dat_lich_ngay_sai_dinh_dang_bao_loi_khong_dat_vao_hom_nay(client, db, nen, ngay_sai):
    dang_nhap(client, "letan")

    r = client.post(
        "/appointments",
        data={
            "thu_cung_id": str(nen["pet1"].id),
            "dich_vu_id": str(nen["dv"].id),
            "nhan_vien_id": str(nen["nv1"].id),
            "ngay": ngay_sai,
            "gio": "15:00",
        },
    )

    assert r.status_code == 400
    assert "Ngày không đúng định dạng" in r.text
    assert db.scalars(select(Appointment)).first() is None


def test_huy_lich_qua_api_luu_ly_do(client, db, nen):
    """TC-048 qua HTTP."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")
    ma = id_lich(db)

    r = client.post(
        f"/appointments/{ma}/huy",
        data={"ngay": NGAY, "ly_do": "Khách báo bận"},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "Đã hủy" in r.text
    db.expire_all()
    assert db.get(Appointment, ma).cancel_reason == "Khách báo bận"


def test_huy_lich_khong_ly_do_bi_tu_choi_qua_api(client, db, nen):
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")
    ma = id_lich(db)

    r = client.post(
        f"/appointments/{ma}/huy", data={"ngay": NGAY, "ly_do": " "}, follow_redirects=True
    )

    assert r.status_code == 400
    assert "lý do" in r.text.lower()


def test_nhan_vien_cham_soc_khong_doi_duoc_lich(client, db, nen):
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00")
    ma = id_lich(db)
    client.post("/logout")
    dang_nhap(client, "chamsoc1")

    r = client.post(
        f"/appointments/{ma}/doi", data={"ngay": NGAY, "gio": "14:00"}, follow_redirects=True
    )

    assert r.status_code == 403


# --- Xem lịch theo vai trò (chặng 2) -----------------------------------------------


@pytest.fixture
def hai_lich(client, nen):
    """Nhân viên 1 chăm Mực lúc 09:00, nhân viên 2 chăm Bông lúc 10:00."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00", pet="pet1", nhan_vien="nv1")
    dat(client, nen, gio="10:00", pet="pet2", nhan_vien="nv2")
    client.post("/logout")
    return nen


def test_caretaker_chi_thay_lich_cua_minh(client, hai_lich):
    """TC-050 và TC-009 hoãn từ P1."""
    dang_nhap(client, "chamsoc1")

    r = client.get(f"/appointments/cua-toi?ngay={NGAY}")

    assert r.status_code == 200
    assert "Mực" in r.text
    assert "Bông" not in r.text


def test_caretaker_go_thang_trang_lich_chung_van_chi_thay_lich_minh(client, hai_lich):
    """TC-009: chặn đường vòng, không chỉ ẩn link trong menu."""
    dang_nhap(client, "chamsoc1")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert r.status_code == 200
    assert "Mực" in r.text
    assert "Bông" not in r.text


def test_caretaker_khong_thay_form_dat_lich(client, hai_lich):
    dang_nhap(client, "chamsoc1")

    r = client.get(f"/appointments/cua-toi?ngay={NGAY}")

    assert r.status_code == 200
    assert "Đặt lịch" not in r.text
    assert "Hủy" not in r.text


def test_le_tan_thay_lich_cua_moi_nhan_vien(client, hai_lich):
    """TC-051."""
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Mực" in r.text
    assert "Bông" in r.text


def test_caretaker_ngay_khong_co_lich_hien_trang_thai_rong(client, hai_lich):
    """TC-052 cho trang riêng của nhân viên chăm sóc."""
    dang_nhap(client, "chamsoc1")

    r = client.get("/appointments/cua-toi?ngay=2026-03-20")

    assert r.status_code == 200
    assert "Chưa có lịch hẹn nào" in r.text


# --- Lỗi tìm được khi rà bằng chuột trên trình duyệt (P4) ------------------------


def test_form_doi_lich_van_giu_nhan_vien_da_khoa_lam_lua_chon_hien_tai(client, db, nen):
    """Lỗi nặng nhất tìm được khi smoke bằng chuột.

    Ô chọn nhân viên trong nút "Đổi" chỉ liệt kê nhân viên đang hoạt động. Khi lịch
    thuộc về nhân viên đã bị khóa, không option nào được chọn nên trình duyệt gửi
    option ĐẦU TIÊN — bấm "Đổi" mà không sửa gì sẽ âm thầm chuyển lịch sang người khác.

    Chỉ lộ ra khi dựng đúng trạng thái "nhân viên bị khóa nhưng còn lịch cũ", nên không
    test nào trước đó bắt được.
    """
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00", nhan_vien="nv2")
    nen["nv2"].is_active = False
    db.commit()

    r = client.get(f"/appointments?ngay={NGAY}")

    assert f'value="{nen["nv2"].id}" selected' in r.text


def test_doi_lich_sang_nhan_vien_da_khoa_bi_tu_choi(client, db, nen):
    """Lớp chặn thứ hai: kể cả gõ thẳng id cũng không phân được cho người đã khóa."""
    dang_nhap(client, "letan")
    dat(client, nen, gio="09:00", nhan_vien="nv1")
    ma = id_lich(db)
    nen["nv2"].is_active = False
    db.commit()

    r = client.post(
        f"/appointments/{ma}/doi",
        data={"ngay": NGAY, "gio": "14:00", "nhan_vien_id": str(nen["nv2"].id)},
        follow_redirects=True,
    )

    assert r.status_code == 400
    db.expire_all()
    assert db.get(Appointment, ma).staff_id == nen["nv1"].id


# --- Việc P6 để lại, đóng ở P8: form đặt lịch trên cơ sở dữ liệu chưa có dữ liệu nền ---
#
# Phát hiện khi rà luồng 11/09: mở /appointments trên CSDL trống thì ba ô chọn bắt buộc
# đều rỗng và không có câu nào nói vì sao. Người dùng chỉ gặp thông báo của chính trình
# duyệt khi bấm Đặt lịch. Đo lại 24/09 trên CSDL tạm: thu_cung_id 0 lựa chọn,
# dich_vu_id 0 lựa chọn, nhan_vien_id (ô trong form) 0 lựa chọn, không câu hướng dẫn nào.


def test_csdl_chua_co_du_lieu_nen_thi_form_dat_lich_hien_cau_huong_dan(
    client, db, seed_basic, frozen_clock
):
    """Chỉ có tài khoản, chưa có thú cưng và dịch vụ → nói rõ còn thiếu gì.

    Không dùng fixture `nen` vì chính trạng thái "chưa có gì" mới là thứ cần dựng.
    """
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert r.status_code == 200
    assert "Chưa có thú cưng nào" in r.text
    assert "Chưa có dịch vụ nào đang bán" in r.text
    # Ô chọn rỗng bắt buộc không được hiện nữa — đó chính là thứ gây khó hiểu.
    assert 'name="thu_cung_id"' not in r.text
    assert 'name="dich_vu_id"' not in r.text


def test_thieu_moi_dich_vu_thi_chi_bao_thieu_dich_vu(client, db, seed_basic, frozen_clock):
    """Ca biên: có thú cưng nhưng chưa có dịch vụ → chỉ nêu đúng thứ còn thiếu."""
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()
    db.add(Pet(owner_id=o.id, name="Mực", species="Chó"))
    db.commit()
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Chưa có dịch vụ nào đang bán" in r.text
    assert "Chưa có thú cưng nào" not in r.text


def test_dich_vu_ngung_ban_khong_tinh_la_da_co_dich_vu(client, db, seed_basic, frozen_clock):
    """Ca biên: dịch vụ đã ngưng bán không đặt lịch được, nên vẫn phải báo thiếu."""
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()
    db.add(Pet(owner_id=o.id, name="Mực", species="Chó"))
    db.add(
        Service(
            code="CU", name="Dịch vụ cũ", duration_min=30,
            price=Decimal("10000"), is_active=False,
        )
    )
    db.commit()
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Chưa có dịch vụ nào đang bán" in r.text


def test_du_du_lieu_nen_thi_form_hien_binh_thuong(client, db, nen):
    """Ca đối chứng: đủ dữ liệu thì form phải trở lại, không còn câu hướng dẫn."""
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert 'name="thu_cung_id"' in r.text
    assert 'name="dich_vu_id"' in r.text
    assert "Chưa có thú cưng nào" not in r.text
    assert "Chưa có dịch vụ nào đang bán" not in r.text


def test_khoa_het_nhan_vien_cham_soc_thi_bao_thieu_nhan_vien(client, db, nen, seed_basic):
    """Ca biên thứ ba: đủ thú cưng và dịch vụ nhưng không còn ai nhận lịch.

    Dựng bằng cách khóa cả hai nhân viên chăm sóc — `_danh_sach_nhan_vien` chỉ lấy người
    còn hoạt động, nên đây là đường thật dẫn tới danh sách rỗng, không phải dựng tay.
    """
    seed_basic["caretaker1"].is_active = False
    seed_basic["caretaker2"].is_active = False
    db.commit()
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Chưa có nhân viên chăm sóc nào" in r.text
    assert "Chưa có thú cưng nào" not in r.text
    assert "Chưa có dịch vụ nào đang bán" not in r.text
