"""Test dịch vụ, bảng giá và gói qua HTTP.

Phục vụ US-07, US-08, US-09 — TC-024 → TC-031.

Logic đã kiểm kỹ ở tests/unit/test_catalog_service.py. Ở đây chỉ kiểm phần thuộc tầng HTTP:
phân quyền, mã trạng thái, và thông báo có thật sự hiện ra cho người dùng đọc.
"""

import re
from decimal import Decimal

import pytest

from app.models.service import Service


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


def them_dich_vu(client, ma="TAM", ten="Tắm cho chó", gia="150000", phut="45", mo_ta=""):
    return client.post(
        "/services",
        data={"ma": ma, "ten": ten, "gia": gia, "thoi_luong_phut": phut, "mo_ta": mo_ta},
        follow_redirects=True,
    )


# --- Phân quyền -----------------------------------------------------------------


def test_quan_ly_vao_duoc_trang_dich_vu(client, seed_basic):
    dang_nhap(client, "quanly")

    assert client.get("/services").status_code == 200


@pytest.mark.parametrize("username", ["letan", "chamsoc1"])
def test_le_tan_va_nhan_vien_cham_soc_chi_xem(client, seed_basic, username):
    """Bảng phân quyền US-02: dịch vụ và bảng giá — hai vai trò này chỉ xem."""
    dang_nhap(client, username)

    r = client.get("/services")

    assert r.status_code == 200
    assert "Thêm dịch vụ" not in r.text


@pytest.mark.parametrize("username", ["letan", "chamsoc1"])
def test_chi_xem_thi_khong_them_duoc_du_goi_thang_post(client, seed_basic, username):
    """Ẩn nút là chưa đủ — máy chủ phải chặn thật."""
    dang_nhap(client, username)

    assert them_dich_vu(client).status_code == 403


def test_chi_xem_thi_khong_ngung_ban_duoc(client, seed_basic):
    dang_nhap(client, "quanly")
    them_dich_vu(client)
    ma = _ma_dich_vu_dau_tien(client)

    client.post("/logout")
    dang_nhap(client, "letan")

    assert client.post(f"/services/{ma}/ngung-ban").status_code == 403


# --- Dịch vụ ---------------------------------------------------------------------


def test_them_dich_vu_hien_trong_danh_sach(client, seed_basic):
    """TC-024."""
    dang_nhap(client, "quanly")

    r = them_dich_vu(client, ten="Tắm cho chó", gia="150000")

    assert r.status_code == 200
    assert "Tắm cho chó" in r.text
    assert "150.000" in r.text or "150000" in r.text


@pytest.mark.parametrize(
    "gia, phut, tu_khoa",
    [("-1000", "45", "âm"), ("150000", "0", "lớn hơn 0"), ("150000", "-30", "lớn hơn 0")],
)
def test_gia_am_hoac_thoi_luong_sai_hien_loi_tren_trang(client, seed_basic, gia, phut, tu_khoa):
    """TC-025: lỗi phải hiện cho người dùng đọc, không phải trang 500."""
    dang_nhap(client, "quanly")

    r = them_dich_vu(client, gia=gia, phut=phut)

    assert r.status_code == 400
    assert tu_khoa in r.text


def test_ma_trung_hien_loi_neu_ro_ma_nao(client, seed_basic):
    dang_nhap(client, "quanly")
    them_dich_vu(client, ma="TAM")

    r = them_dich_vu(client, ma="TAM", ten="Tắm khác")

    assert r.status_code == 400
    assert "TAM" in r.text


def test_trang_dich_vu_co_form_sua_gia(client, seed_basic):
    """Route `/services/{id}/sua` có từ P2b nhưng KHÔNG có form nào trỏ tới nó.

    Hậu quả: quản lý không đổi được giá bằng chuột, dù US-07 nói "cập nhật giá". Ô smoke
    quan trọng nhất của P5 — "đổi giá rồi mở lại hóa đơn cũ" — cũng không bấm được.
    Cùng lớp lỗi với "route có nhưng thiếu link menu" đã gặp ở P4: test cũ gọi thẳng POST
    nên không ai phát hiện giao diện thiếu.
    """
    dang_nhap(client, "quanly")
    them_dich_vu(client, gia="150000")
    ma = _ma_dich_vu_dau_tien(client)

    r = client.get("/services")

    assert f'action="/services/{ma}/sua"' in r.text


def _truong_cua_form(html: str, action: str) -> dict[str, str]:
    """Đọc mọi ô input của đúng một form — gửi y như trình duyệt gửi.

    Tự gõ tay danh sách trường trong test sẽ bỏ qua đúng thứ cần kiểm: trường nào form
    QUÊN gửi thì route /sua ghi đè bằng rỗng.
    """
    khoi = html[html.index(f'action="{action}"') :]
    khoi = khoi[: khoi.index("</form>")]
    return dict(re.findall(r'name="([^"]+)"[^>]*value="([^"]*)"', khoi))


def test_luu_gia_khong_lam_mat_mo_ta_dich_vu(client, db, seed_basic):
    """Route /sua ghi đè cả bốn trường, nên form chỉ gửi giá là xóa trắng mô tả."""
    dang_nhap(client, "quanly")
    them_dich_vu(client, gia="150000", mo_ta="Tắm nước ấm, sấy khô.")
    ma = _ma_dich_vu_dau_tien(client)

    truong = _truong_cua_form(client.get("/services").text, f"/services/{ma}/sua")
    truong["gia"] = "180000"
    client.post(f"/services/{ma}/sua", data=truong, follow_redirects=True)

    s = db.get(Service, ma)
    assert s.price == Decimal("180000")
    assert s.description == "Tắm nước ấm, sấy khô."


def test_le_tan_khong_thay_form_sua_gia(client, seed_basic):
    """Ca biên: US-02 cho lễ tân quyền XEM bảng giá, không có quyền sửa."""
    dang_nhap(client, "quanly")
    them_dich_vu(client, gia="150000")
    ma = _ma_dich_vu_dau_tien(client)
    dang_nhap(client, "letan")

    r = client.get("/services")

    assert f'action="/services/{ma}/sua"' not in r.text


def test_doi_gia_dich_vu(client, seed_basic):
    """TC-026, phần làm được ở P2b. Phần hóa đơn cũ giữ giá chờ P5."""
    dang_nhap(client, "quanly")
    them_dich_vu(client, gia="150000")
    ma = _ma_dich_vu_dau_tien(client)

    r = client.post(
        f"/services/{ma}/sua",
        data={"ten": "Tắm cho chó", "gia": "180000", "thoi_luong_phut": "45"},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "180.000" in r.text or "180000" in r.text


# --- Ngưng bán --------------------------------------------------------------------


def test_ngung_ban_thi_danh_dau_tren_trang_nhung_khong_mat_du_lieu(client, seed_basic):
    """TC-030 phần giao diện, US-09."""
    dang_nhap(client, "quanly")
    them_dich_vu(client, ten="Tắm cho chó")
    ma = _ma_dich_vu_dau_tien(client)

    r = client.post(f"/services/{ma}/ngung-ban", follow_redirects=True)

    assert r.status_code == 200
    assert "Tắm cho chó" in r.text
    assert "Đã ngưng bán" in r.text


def test_ban_lai_dich_vu_da_ngung(client, seed_basic):
    dang_nhap(client, "quanly")
    them_dich_vu(client)
    ma = _ma_dich_vu_dau_tien(client)
    client.post(f"/services/{ma}/ngung-ban")

    r = client.post(f"/services/{ma}/ban-lai", follow_redirects=True)

    assert r.status_code == 200
    assert "Đã ngưng bán" not in r.text


# --- Gói dịch vụ ------------------------------------------------------------------


def test_tao_goi_hien_thanh_phan_va_tien_tiet_kiem(client, seed_basic):
    """TC-027, TC-028."""
    dang_nhap(client, "quanly")
    them_dich_vu(client, ma="TAM", ten="Tắm cho chó", gia="150000")
    them_dich_vu(client, ma="CATMONG", ten="Cắt móng", gia="50000")
    ma = _ma_theo_ten(client)

    r = client.post(
        "/services/goi",
        data={
            "ten": "Combo cơ bản",
            "gia": "180000",
            "dich_vu_id": [str(ma["Tắm cho chó"]), str(ma["Cắt móng"])],
            "so_luong": ["1", "2"],
        },
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "Combo cơ bản" in r.text
    # tổng lẻ 150.000 x1 + 50.000 x2 = 250.000, tiết kiệm 70.000
    assert "250.000" in r.text
    assert "70.000" in r.text


def test_goi_khong_chon_dich_vu_nao_bi_tu_choi(client, seed_basic):
    """TC-029."""
    dang_nhap(client, "quanly")

    r = client.post(
        "/services/goi",
        data={"ten": "Gói rỗng", "gia": "100000"},
        follow_redirects=True,
    )

    assert r.status_code == 400
    assert "ít nhất một dịch vụ" in r.text


def test_trang_dich_vu_trong_hien_trang_thai_rong(client, seed_basic):
    dang_nhap(client, "quanly")

    r = client.get("/services")

    assert "Chưa có dịch vụ nào" in r.text


# --- Tiện ích -------------------------------------------------------------------


def _tat_ca_ma_dich_vu(client) -> list[int]:
    import re

    html = client.get("/services").text
    return [int(m) for m in re.findall(r'name="dich_vu_id" value="(\d+)"', html)]


def _ma_theo_ten(client) -> dict[str, int]:
    """Ánh xạ tên dịch vụ sang id, đọc từ form tạo gói.

    Dùng thay cho việc lấy theo chỉ số: danh sách sắp theo tên, nên "Cắt móng" đứng
    trước "Tắm cho chó" và chỉ số dễ gán nhầm — chính chỗ này đã làm test đỏ một lần.
    """
    import re

    html = client.get("/services").text
    cap = re.findall(
        r'<span>([^<]+?)\s*<span class="phu">[^<]*</span></span>\s*'
        r'<input type="hidden" name="dich_vu_id" value="(\d+)">',
        html,
    )
    assert cap, "Không đọc được dịch vụ nào từ form tạo gói"
    return {ten.strip(): int(ma) for ten, ma in cap}


def _ma_dich_vu_dau_tien(client) -> int:
    ma = _tat_ca_ma_dich_vu(client)
    assert ma, "Không tìm thấy dịch vụ nào trên trang"
    return ma[0]
