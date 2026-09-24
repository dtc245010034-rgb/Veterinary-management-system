"""Test tiêm phòng qua HTTP — chặng 2 của P4.

Phục vụ US-17, US-18 — TC-059, TC-063, TC-064, và TC-020 hoãn từ P2a.

Quy tắc nghiệp vụ đã kiểm kỹ ở tests/unit/test_vaccinations_service.py. Ở đây chỉ kiểm
phần thuộc tầng HTTP: form ghi mũi tiêm, danh sách đến hạn, link menu, khuyến cáo bác sĩ.
"""

from datetime import date, timedelta

import pytest

from app.models.owner import Owner
from app.models.pet import Pet

HOM_NAY = date(2026, 3, 12)  # = MOC_THOI_GIAN trong conftest


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
    p2 = Pet(owner_id=o.id, name="Mun", species="Mèo")
    db.add_all([p, p2])
    db.commit()

    return {"muc": p, "mun": p2}


def ghi_mui(client, thu_cung, **ghi_de):
    truong = {
        "ten_vac_xin": "Dại",
        "so_mui": "1",
        "ngay_tiem": (HOM_NAY - timedelta(days=10)).isoformat(),
        "han_nhac": (HOM_NAY + timedelta(days=10)).isoformat(),
        "ghi_chu": "",
    }
    truong.update(ghi_de)
    return client.post(
        f"/pets/{thu_cung.id}/vaccinations", data=truong, follow_redirects=True
    )


# --- Ghi mũi tiêm trên trang thú cưng — TC-059 -----------------------------------


def test_ghi_mui_tiem_hien_ngay_trong_ho_so_tiem(client, nen):
    """TC-059."""
    dang_nhap(client, "letan")

    r = ghi_mui(client, nen["muc"])

    assert r.status_code == 200
    assert "Dại" in r.text
    assert "02/03/2026" in r.text  # ngày tiêm, định dạng Việt


def test_ho_so_tiem_khong_lan_sang_thu_cung_khac(client, nen):
    # Tên vắc-xin cố ý không trùng gợi ý trong ô nhập ("Dại, Care, FVRCP…"): dùng tên có
    # sẵn trong placeholder thì phép kiểm "không xuất hiện" đỏ vì lý do sai.
    dang_nhap(client, "letan")
    ghi_mui(client, nen["muc"], ten_vac_xin="Cúm mèo bốn bệnh")

    r = client.get(f"/pets/{nen['mun'].id}")

    assert "Cúm mèo bốn bệnh" not in r.text
    assert "Chưa có mũi tiêm nào" in r.text


def test_han_nhac_som_hon_ngay_tiem_hien_loi_khong_vo_trang(client, nen):
    """TC-060 ở tầng HTTP: người dùng phải thấy lý do, không phải trang 500."""
    dang_nhap(client, "letan")

    r = ghi_mui(client, nen["muc"], han_nhac=(HOM_NAY - timedelta(days=20)).isoformat())

    assert r.status_code == 400
    assert "sớm hơn ngày tiêm" in r.text
    assert nen["muc"].name in r.text  # trang thú cưng vẫn dựng đủ, không phải trang lỗi


def test_ngay_tiem_o_tuong_lai_hien_loi(client, nen):
    """TC-061 ở tầng HTTP."""
    dang_nhap(client, "letan")

    r = ghi_mui(client, nen["muc"], ngay_tiem=(HOM_NAY + timedelta(days=1)).isoformat())

    assert r.status_code == 400
    assert "tương lai" in r.text


def test_nhan_vien_cham_soc_cung_ghi_duoc_mui_tiem(client, nen):
    """Bảng phân quyền US-02 cho cả ba vai trò toàn quyền ở mục tiêm phòng."""
    dang_nhap(client, "chamsoc1")

    r = ghi_mui(client, nen["muc"])

    assert r.status_code == 200
    assert "Dại" in r.text


# --- Danh sách đến hạn — TC-062 → TC-064 -----------------------------------------


def test_danh_sach_den_han_hien_thu_cung_va_chu_nuoi(client, nen):
    dang_nhap(client, "letan")
    ghi_mui(client, nen["muc"])

    r = client.get("/vaccinations")

    assert r.status_code == 200
    assert nen["muc"].name in r.text
    assert "Đỗ Thị Hằng" in r.text


def test_ban_ghi_qua_han_duoc_danh_dau(client, nen):
    """TC-063."""
    dang_nhap(client, "letan")
    ghi_mui(client, nen["muc"], han_nhac=(HOM_NAY - timedelta(days=3)).isoformat())

    r = client.get("/vaccinations")

    assert "Quá hạn" in r.text


def test_han_con_xa_khong_hien_trong_danh_sach(client, nen):
    dang_nhap(client, "letan")
    ghi_mui(client, nen["mun"], han_nhac=(HOM_NAY + timedelta(days=60)).isoformat())

    r = client.get("/vaccinations")

    # Không có mã 200 thì phép kiểm "tên không xuất hiện" xanh cả khi trang trả về 404 —
    # đúng loại test xanh vì lý do sai mà dự án đang cố loại bỏ.
    assert r.status_code == 200
    assert nen["mun"].name not in r.text


def test_khong_ai_den_han_hien_trang_thai_rong(client, nen):
    """TC-064: trạng thái rỗng có chữ, không phải bảng trống."""
    dang_nhap(client, "letan")

    r = client.get("/vaccinations")

    assert r.status_code == 200
    assert "Không có thú cưng nào đến hạn" in r.text


def test_man_hinh_tiem_phong_ghi_ro_lich_tiem_do_bac_si_quyet_dinh(client, nen):
    """Bắt buộc theo docs/ai-safety.md, dù màn hình này chưa dính AI.

    Hệ thống chỉ nhắc lại đúng ngày người dùng đã ghi; nó không sinh lịch tiêm, không gợi
    ý loại vắc-xin. Thiếu dòng này thì màn hình trông như một chỉ định y tế.
    """
    dang_nhap(client, "letan")

    r = client.get("/vaccinations")

    assert "bác sĩ thú y" in r.text


@pytest.mark.parametrize("username", ["quanly", "letan", "chamsoc1"])
def test_moi_vai_tro_deu_co_link_menu_toi_danh_sach_den_han(client, nen, username):
    """US-02 cho cả ba vai trò toàn quyền ở mục tiêm phòng.

    Lỗi thật ở P4 chặng 1: lễ tân và nhân viên có quyền xem bảng giá nhưng không có link
    menu nào, phải tự gõ URL. Kiểm ngay từ đầu ở chặng này thay vì đợi rà luồng.
    """
    dang_nhap(client, username)

    # Lấy một trang KHÔNG phải trang chủ: link phải nằm trong thanh điều hướng dùng chung
    # nên bấm tới được từ bất kỳ đâu. Kiểm trên "/" thì thẻ ở trang chủ cũng khớp, và xóa
    # link trong thanh điều hướng vẫn xanh.
    r = client.get("/services")

    assert 'href="/vaccinations"' in r.text


# --- Trang thú cưng gộp đủ hai khối — TC-020 hoãn từ P2a -------------------------


def test_trang_thu_cung_hien_ca_lich_su_cham_soc_lan_ho_so_tiem(client, nen):
    """TC-020: trang chi tiết thú cưng hiện chủ nuôi, lịch sử chăm sóc, hồ sơ tiêm."""
    dang_nhap(client, "letan")
    ghi_mui(client, nen["muc"])

    r = client.get(f"/pets/{nen['muc'].id}")

    assert "Đỗ Thị Hằng" in r.text
    assert "Lịch sử chăm sóc" in r.text
    assert "Hồ sơ tiêm" in r.text
    assert "Dại" in r.text


def test_xoa_thu_cung_chi_co_ho_so_tiem_ra_400_khong_phai_500(client, nen):
    """Lỗi tìm ra khi rà luồng bằng trình duyệt: trang đen "Internal Server Error".

    Router chỉ bắt `LoiNghiepVu`, nên khi tầng services để `IntegrityError` bay ra thì
    người dùng nhận về trang 500 thô. Đây là ca đi qua đúng luồng bình thường: bấm "Xóa"
    trên một thú cưng chỉ mới có hồ sơ tiêm.
    """
    dang_nhap(client, "letan")
    ghi_mui(client, nen["mun"])

    r = client.post(f"/pets/{nen['mun'].id}/xoa", follow_redirects=True)

    assert r.status_code == 400
    assert "không xóa được" in r.text


def test_form_mui_tiem_giu_lai_du_lieu_da_nhap_khi_bao_loi(client, nen):
    """Bắt lỗi rồi xóa sạch ô nhập thì người dùng phải gõ lại cả năm ô, gồm hai ô ngày.

    Tìm ra khi rà luồng bằng trình duyệt: sai một ô ngày là mất toàn bộ phần đã nhập.
    """
    dang_nhap(client, "letan")

    r = ghi_mui(
        client,
        nen["muc"],
        ten_vac_xin="Cúm mèo bốn bệnh",
        so_mui="3",
        ngay_tiem=(HOM_NAY - timedelta(days=5)).isoformat(),
        han_nhac=(HOM_NAY - timedelta(days=20)).isoformat(),
        ghi_chu="Tiêm ở phòng khám An Khang",
    )

    assert r.status_code == 400
    assert 'value="Cúm mèo bốn bệnh"' in r.text
    assert 'value="3"' in r.text
    assert f'value="{(HOM_NAY - timedelta(days=5)).isoformat()}"' in r.text
    assert "Tiêm ở phòng khám An Khang" in r.text


# --- L-04: trang thú cưng không gắn "Quá hạn" cho mũi đã có mũi sau thay thế ------
#
# Đo bằng Chrome 24/09 trên CSDL thật: "Mực" có mũi Dại số 2 hạn 04/08/2027 mà mũi số 1
# vẫn mang nhãn Quá hạn. Danh sách `/vaccinations` thì đúng — hai màn hình nói khác nhau
# về cùng một con vật.


def test_trang_thu_cung_khong_gan_qua_han_cho_mui_da_co_mui_sau(client, nen):
    dang_nhap(client, "letan")
    ghi_mui(client, nen["muc"], so_mui="1",
            ngay_tiem=(HOM_NAY - timedelta(days=400)).isoformat(),
            han_nhac=(HOM_NAY - timedelta(days=35)).isoformat())
    ghi_mui(client, nen["muc"], so_mui="2",
            ngay_tiem=(HOM_NAY - timedelta(days=5)).isoformat(),
            han_nhac=(HOM_NAY + timedelta(days=360)).isoformat())

    r = client.get(f"/pets/{nen['muc'].id}")

    assert r.status_code == 200
    assert "Quá hạn" not in r.text


def test_trang_thu_cung_van_gan_qua_han_khi_mui_moi_nhat_that_su_qua_han(client, nen):
    """Ca đối chứng: đừng lọc mất luôn cảnh báo thật — đó mới là mục đích của màn hình."""
    dang_nhap(client, "letan")
    ghi_mui(client, nen["muc"], so_mui="1",
            ngay_tiem=(HOM_NAY - timedelta(days=400)).isoformat(),
            han_nhac=(HOM_NAY - timedelta(days=35)).isoformat())

    r = client.get(f"/pets/{nen['muc'].id}")

    assert "Quá hạn" in r.text
