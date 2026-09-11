"""Test chủ nuôi, thú cưng và tra cứu qua HTTP.

Phục vụ US-04, US-05, US-06 — TC-013 → TC-023.

Logic nghiệp vụ đã được kiểm kỹ ở tests/unit/test_owners_service.py. Ở đây chỉ kiểm phần
mà tầng HTTP chịu trách nhiệm: phân quyền, mã trạng thái, và thông báo có thật sự hiện ra
trên trang cho người dùng đọc.
"""

import pytest


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


def them_chu_nuoi(client, ho_ten="Trần Thị Lễ", sdt="0912345678", **them):
    return client.post(
        "/owners",
        data={"ho_ten": ho_ten, "so_dien_thoai": sdt, **them},
        follow_redirects=True,
    )


# --- Phân quyền -----------------------------------------------------------------


@pytest.mark.parametrize("username", ["quanly", "letan"])
def test_quan_ly_va_le_tan_vao_duoc_trang_chu_nuoi(client, seed_basic, username):
    dang_nhap(client, username)

    assert client.get("/owners").status_code == 200


def test_nhan_vien_cham_soc_chi_xem_khong_thay_nut_them(client, seed_basic):
    """Bảng phân quyền US-02: caretaker chỉ xem chủ nuôi và thú cưng."""
    dang_nhap(client, "chamsoc1")

    r = client.get("/owners")

    assert r.status_code == 200
    assert "Thêm chủ nuôi" not in r.text


def test_nhan_vien_cham_soc_khong_them_duoc_chu_nuoi(client, seed_basic):
    """Ẩn nút là chưa đủ — gõ thẳng POST cũng phải bị chặn."""
    dang_nhap(client, "chamsoc1")

    r = them_chu_nuoi(client)

    assert r.status_code == 403


# --- Chủ nuôi -------------------------------------------------------------------


def test_them_chu_nuoi_hien_ngay_trong_danh_sach(client, seed_basic):
    """TC-013."""
    dang_nhap(client, "letan")

    r = them_chu_nuoi(client, ho_ten="Trần Thị Lễ", sdt="0912345678")

    assert r.status_code == 200
    assert "Trần Thị Lễ" in r.text
    assert "0912345678" in r.text


@pytest.mark.parametrize(
    "ho_ten, sdt, tu_khoa_loi",
    [("", "0912345678", "Họ tên"), ("Trần Thị Lễ", "", "Số điện thoại")],
)
def test_thieu_truong_bat_buoc_hien_loi_tren_trang(client, seed_basic, ho_ten, sdt, tu_khoa_loi):
    """TC-014: lỗi phải hiện ra cho người dùng đọc, không phải trang 500."""
    dang_nhap(client, "letan")

    r = them_chu_nuoi(client, ho_ten=ho_ten, sdt=sdt)

    assert r.status_code == 400
    assert tu_khoa_loi in r.text


def test_so_dien_thoai_trung_hien_canh_bao_ngay_sau_khi_them(client, seed_basic):
    """TC-015: cảnh báo chứ không cấm — và cảnh báo phải hiện TRONG LUỒNG.

    Bản test cũ gọi thẳng `/owners?sdt_kiem_tra=...`, một URL không nút nào trong giao
    diện sinh ra. Nó xanh suốt từ P2a trong khi người dùng thật thêm chủ nuôi trùng số
    mà không thấy cảnh báo nào. Tìm ra khi rà bằng chuột trên trình duyệt ở P4.
    """
    dang_nhap(client, "letan")
    them_chu_nuoi(client, ho_ten="Người Một", sdt="0912345678")

    r = them_chu_nuoi(client, ho_ten="Người Hai", sdt="0912345678")

    assert "đã dùng số này" in r.text
    assert "Người Một" in r.text
    # Không tự liệt kê chính người vừa tạo — nói "đã có" mà trỏ vào chính nó thì vô nghĩa.
    assert r.text.count("Người Hai") == 1


def test_them_chu_nuoi_so_dien_thoai_moi_khong_hien_canh_bao(client, seed_basic):
    """Ca biên: cảnh báo chỉ được xuất hiện khi thật sự có trùng."""
    dang_nhap(client, "letan")

    r = them_chu_nuoi(client, ho_ten="Người Một", sdt="0988777666")

    assert "đã dùng số này" not in r.text


def test_trang_chi_tiet_chu_nuoi_khong_hua_hen_phase_tuong_lai(client, seed_basic):
    """Ghi chú "sẽ hiển thị từ phase P4" đã lỗi thời — P4 đặt lịch sử ở /pets/{id}."""
    dang_nhap(client, "letan")
    them_chu_nuoi(client, ho_ten="Người Một", sdt="0912345678")

    r = client.get("/owners/1")

    assert "phase P4" not in r.text


def test_xoa_chu_nuoi_con_thu_cung_bi_chan_kem_thong_bao(client, seed_basic):
    """TC-016."""
    dang_nhap(client, "letan")
    them_chu_nuoi(client)
    ma = _ma_chu_nuoi_dau_tien(client)
    client.post(f"/owners/{ma}/pets", data={"ten": "Mực", "loai": "Chó"})

    r = client.post(f"/owners/{ma}/xoa", follow_redirects=True)

    assert r.status_code == 400
    assert "thú cưng" in r.text.lower()


def test_xoa_chu_nuoi_khong_co_thu_cung_thanh_cong(client, seed_basic):
    dang_nhap(client, "letan")
    them_chu_nuoi(client, ho_ten="Không Thú", sdt="0900000001")
    ma = _ma_chu_nuoi_dau_tien(client)

    r = client.post(f"/owners/{ma}/xoa", follow_redirects=True)

    assert r.status_code == 200
    assert "Không Thú" not in r.text


# --- Thú cưng -------------------------------------------------------------------


def test_them_thu_cung_hien_trong_danh_sach_cua_chu(client, seed_basic):
    """TC-017."""
    dang_nhap(client, "letan")
    them_chu_nuoi(client)
    ma = _ma_chu_nuoi_dau_tien(client)

    r = client.post(
        f"/owners/{ma}/pets",
        data={"ten": "Mực", "loai": "Chó", "giong": "Poodle"},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "Mực" in r.text
    assert "Poodle" in r.text


def test_ngay_sinh_tuong_lai_bi_chan_kem_thong_bao(client, seed_basic, frozen_clock):
    """TC-018."""
    dang_nhap(client, "letan")
    them_chu_nuoi(client)
    ma = _ma_chu_nuoi_dau_tien(client)

    r = client.post(
        f"/owners/{ma}/pets",
        data={"ten": "Mực", "loai": "Chó", "ngay_sinh": "2030-01-01"},
        follow_redirects=True,
    )

    assert r.status_code == 400
    assert "tương lai" in r.text


def test_can_nang_am_bi_chan_kem_thong_bao(client, seed_basic):
    """TC-019."""
    dang_nhap(client, "letan")
    them_chu_nuoi(client)
    ma = _ma_chu_nuoi_dau_tien(client)

    r = client.post(
        f"/owners/{ma}/pets",
        data={"ten": "Mực", "loai": "Chó", "can_nang": "-2"},
        follow_redirects=True,
    )

    assert r.status_code == 400
    assert "Cân nặng" in r.text


@pytest.mark.parametrize("can_nang", ["nan", "inf", "-inf", "Infinity"])
def test_can_nang_nan_hay_vo_cuc_bi_chan_kem_thong_bao(client, seed_basic, can_nang):
    """Lỗi thật, rà bằng trình duyệt 11/09: `float()` nhận cả "nan" và "inf".

    "nan" lọt qua phép so `<= 0` rồi bị SQLite lưu thành NULL — cân nặng người dùng gõ biến
    mất không một lời báo. "inf" được lưu thật và trang hiện "inf kg".
    """
    dang_nhap(client, "letan")
    them_chu_nuoi(client)
    ma = _ma_chu_nuoi_dau_tien(client)

    r = client.post(
        f"/owners/{ma}/pets",
        data={"ten": "Mực", "loai": "Chó", "can_nang": can_nang},
        follow_redirects=True,
    )

    assert r.status_code == 400
    assert "Cân nặng phải là một số" in r.text


def test_trang_chi_tiet_thu_cung_hien_thong_tin_chu_nuoi(client, seed_basic):
    """TC-020, phần làm được ở P2a.

    Lịch sử chăm sóc và lịch tiêm cũng thuộc TC-020 nhưng cần bảng care_records và
    vaccinations của P4 — chưa kiểm được ở đây.
    """
    dang_nhap(client, "letan")
    them_chu_nuoi(client, ho_ten="Trần Thị Lễ", sdt="0912345678")
    ma = _ma_chu_nuoi_dau_tien(client)
    client.post(f"/owners/{ma}/pets", data={"ten": "Mực", "loai": "Chó"})

    r = client.get(f"/owners/{ma}")

    assert "Mực" in r.text
    assert "Trần Thị Lễ" in r.text
    assert "0912345678" in r.text


# --- Tra cứu --------------------------------------------------------------------


@pytest.fixture
def du_lieu_tra_cuu(client, seed_basic):
    dang_nhap(client, "letan")
    them_chu_nuoi(client, ho_ten="Trần Thị Lễ", sdt="0912345678")
    ma = _ma_chu_nuoi_dau_tien(client)
    client.post(f"/owners/{ma}/pets", data={"ten": "Mực", "loai": "Chó"})
    client.post(f"/owners/{ma}/pets", data={"ten": "Đậu Đỏ", "loai": "Mèo"})
    return client


def test_tim_theo_so_dien_thoai(client, du_lieu_tra_cuu):
    """TC-021."""
    r = client.get("/owners?q=0912345678")

    assert "Trần Thị Lễ" in r.text


@pytest.mark.parametrize("tu_khoa", ["muc", "MUC", "Mực"])
def test_tim_khong_dau_va_khong_phan_biet_hoa_thuong(client, du_lieu_tra_cuu, tu_khoa):
    """TC-022."""
    r = client.get(f"/owners?q={tu_khoa}")

    assert "Mực" in r.text


def test_tim_ten_co_chu_d_gach_ngang(client, du_lieu_tra_cuu):
    r = client.get("/owners?q=dau do")

    assert "Đậu Đỏ" in r.text


def test_tim_khong_khop_hien_trang_thai_rong_co_huong_dan(client, du_lieu_tra_cuu):
    """TC-023: không phải trang trắng, không phải lỗi."""
    r = client.get("/owners?q=khong-co-gi-khop")

    assert r.status_code == 200
    assert "Không tìm thấy" in r.text


# --- Tiện ích -------------------------------------------------------------------


def _ma_chu_nuoi_dau_tien(client) -> int:
    """Lấy id chủ nuôi mới nhất từ trang danh sách.

    Đọc qua HTML thay vì truy vấn thẳng CSDL: test integration nên chỉ dùng những gì
    người dùng thật sự thấy, nếu không nó sẽ vẫn xanh cả khi trang hỏng.
    """
    import re

    html = client.get("/owners").text
    ma = re.findall(r'/owners/(\d+)"', html)
    assert ma, "Không tìm thấy liên kết tới chủ nuôi nào trên trang danh sách"
    return int(ma[-1])


@pytest.mark.parametrize("username", ["quanly", "letan", "chamsoc1"])
def test_moi_vai_tro_deu_co_link_menu_toi_trang_chu_nuoi(client, seed_basic, username):
    """Bảng phân quyền US-02 cho `caretaker` quyền **xem** chủ nuôi và thú cưng.

    Lỗi thật, lần thứ hai cùng một dạng: trang mở được, phân quyền đúng, nhưng thanh điều
    hướng không có link nên nhân viên chăm sóc phải tự gõ URL. Lần trước là link "Dịch vụ";
    sửa xong chỉ sửa đúng dòng đó chứ không soát lại cả bảng phân quyền.

    Lấy trang không phải trang chủ để chỉ thanh điều hướng dùng chung được tính.
    """
    r = client.post(
        "/login", data={"username": username, "password": "matkhau123"}
    )
    assert r.status_code in (200, 303)

    r = client.get("/services")

    assert 'href="/owners"' in r.text


def test_form_chu_nuoi_giu_lai_du_lieu_da_nhap_khi_bao_loi(client, seed_basic):
    """Cùng lỗi đã sửa cho form mũi tiêm ngày 06/09, còn sót ở hai form của P2a.

    Bỏ trống họ tên thì mất luôn số điện thoại, email, địa chỉ vừa gõ.
    """
    client.post("/login", data={"username": "letan", "password": "matkhau123"})

    r = client.post(
        "/owners",
        data={
            "ho_ten": "",
            "so_dien_thoai": "0906111222",
            "email": "hoa@example.com",
            "dia_chi": "12 Lê Lợi",
            "ghi_chu": "Khách quen",
        },
        follow_redirects=True,
    )

    assert r.status_code == 400
    assert 'value="0906111222"' in r.text
    assert 'value="hoa@example.com"' in r.text
    assert 'value="12 Lê Lợi"' in r.text
    assert 'value="Khách quen"' in r.text


def test_loi_form_chu_nuoi_hien_ngay_trong_khung_nhap(client, seed_basic):
    """Ô smoke P2 đòi lỗi hiện "ngay cạnh ô nhập".

    Trước đây thông báo nằm phía trên danh sách ở cột trái, còn form ở cột phải — người
    dùng gõ ở một chỗ, lỗi hiện ở chỗ khác.
    """
    client.post("/login", data={"username": "letan", "password": "matkhau123"})

    r = client.post("/owners", data={"ho_ten": "", "so_dien_thoai": "0906111222"})

    truoc_form = r.text.split('action="/owners"')[-1]
    assert "Họ tên không được để trống." in truoc_form


def test_form_thu_cung_giu_lai_du_lieu_da_nhap_khi_bao_loi(client, db, seed_basic, frozen_clock):
    from app.models.owner import Owner

    o = Owner(full_name="Lý Thu Hà", phone="0905112233")
    db.add(o)
    db.commit()

    client.post("/login", data={"username": "letan", "password": "matkhau123"})

    r = client.post(
        f"/owners/{o.id}/pets",
        data={
            "ten": "",
            "loai": "Mèo",
            "giong": "Anh lông ngắn",
            "gioi_tinh": "Cái",
            "ngay_sinh": "2025-01-15",
            "can_nang": "3.2",
            "ghi_chu": "Sợ máy sấy",
        },
    )

    assert r.status_code == 400
    assert 'value="Mèo"' in r.text
    assert 'value="Anh lông ngắn"' in r.text
    assert 'value="2025-01-15"' in r.text
    assert 'value="Sợ máy sấy"' in r.text
