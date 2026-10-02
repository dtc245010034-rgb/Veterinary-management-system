"""Nối tài khoản khách với hồ sơ chủ nuôi qua HTTP (P9 chặng 4, đợt 4b).

Hai người dùng cùng lúc: khách (cookie `csv`) và lễ tân (cookie nhân viên) nên mỗi người một `TestClient`
riêng, cùng dùng một CSDL qua override `get_db` của fixture `client`.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.customer import Customer
from app.models.link_request import LinkRequest
from app.security import hash_password
from app.services import owners

MAT_KHAU_KHACH = "matkhau-khach-1"


@pytest.fixture
def khach_client(client, db):
    """Khách đã có tài khoản và đã đăng nhập, chưa được nối với hồ sơ nào."""
    db.add(Customer(email="khach@example.com", full_name="Nguyen Khach", password_hash=hash_password(MAT_KHAU_KHACH)))
    db.commit()
    c = TestClient(app)
    r = c.post("/khach/dang-nhap", data={"email": "khach@example.com", "mat_khau": MAT_KHAU_KHACH}, follow_redirects=False)
    assert r.status_code == 303
    return c


def _nhan_vien(client, seed_basic, username="letan"):
    c = TestClient(app)
    r = c.post("/login", data={"username": username, "password": seed_basic["mat_khau"]}, follow_redirects=False)
    assert r.status_code == 303
    return c


def _khach_trong_db(db) -> Customer:
    db.expire_all()
    return db.query(Customer).filter_by(email="khach@example.com").one()


# --- Luồng chính -----------------------------------------------------------------------


def test_luong_khach_gui_yeu_cau_le_tan_duyet_roi_go(client, db, seed_basic, khach_client):
    chu = owners.tao_chu_nuoi(db, ho_ten="Chu Cua Muc", so_dien_thoai="0912345678")
    letan = _nhan_vien(client, seed_basic)

    trang_chu = khach_client.get("/khach").text
    assert "chưa được liên kết" in trang_chu
    assert 'href="/khach/lien-ket"' in trang_chu  # đường vào form xin liên kết

    r = khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678", "ghi_chu": "Con chó tên Mực"})
    assert r.status_code == 200
    assert "đang chờ" in khach_client.get("/khach/lien-ket").text

    man_hinh = letan.get("/lien-ket-khach")
    assert man_hinh.status_code == 200
    assert "khach@example.com" in man_hinh.text
    assert "Con chó tên Mực" in man_hinh.text
    assert "Chu Cua Muc" in man_hinh.text  # hồ sơ gợi ý theo số điện thoại

    yeu_cau_id = db.query(LinkRequest).one().id
    r = letan.post(f"/lien-ket-khach/{yeu_cau_id}/duyet", data={"ung_vien": str(chu.id)}, follow_redirects=False)
    assert r.status_code == 303
    assert _khach_trong_db(db).owner_id == chu.id
    assert "đã được liên kết" in khach_client.get("/khach").text

    r = letan.post(f"/lien-ket-khach/tai-khoan/{_khach_trong_db(db).id}/go", follow_redirects=False)
    assert r.status_code == 303
    assert _khach_trong_db(db).owner_id is None
    assert "chưa được liên kết" in khach_client.get("/khach").text


def test_le_tan_tu_choi_khach_thay_ly_do_va_gui_lai_duoc(client, db, seed_basic, khach_client):
    letan = _nhan_vien(client, seed_basic)
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    r = letan.post("/lien-ket-khach/1/tu-choi", data={"ly_do": "Số không khớp hồ sơ nào"}, follow_redirects=False)
    assert r.status_code == 303

    trang = khach_client.get("/khach/lien-ket")
    assert "Số không khớp hồ sơ nào" in trang.text
    assert 'name="so_dien_thoai"' in trang.text  # form hiện lại để gửi yêu cầu mới
    assert khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0987654321"}).status_code == 200
    assert _khach_trong_db(db).owner_id is None


def test_tu_choi_khong_ly_do_bi_tra_400_va_yeu_cau_van_cho(client, db, seed_basic, khach_client):
    letan = _nhan_vien(client, seed_basic)
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    r = letan.post("/lien-ket-khach/1/tu-choi", data={"ly_do": " "})

    assert r.status_code == 400
    assert "lý do" in r.text
    assert "khach@example.com" in letan.get("/lien-ket-khach").text


def test_duyet_khong_chon_ho_so_nao_bi_tra_400(client, db, seed_basic, khach_client):
    letan = _nhan_vien(client, seed_basic)
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    r = letan.post("/lien-ket-khach/1/duyet", data={})

    assert r.status_code == 400
    assert _khach_trong_db(db).owner_id is None


def test_duyet_bang_ma_ho_so_khac_so_khach_nhap(client, db, seed_basic, khach_client):
    chu = owners.tao_chu_nuoi(db, ho_ten="Doi So", so_dien_thoai="0900000000")
    letan = _nhan_vien(client, seed_basic)
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    r = letan.post("/lien-ket-khach/1/duyet", data={"owner_id_khac": str(chu.id)}, follow_redirects=False)

    assert r.status_code == 303
    assert _khach_trong_db(db).owner_id == chu.id


def test_duyet_ma_ho_so_khong_ton_tai_bao_loi_ngay_tren_man_hinh_chu_khong_500(client, db, seed_basic, khach_client):
    letan = _nhan_vien(client, seed_basic)
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    r = letan.post("/lien-ket-khach/1/duyet", data={"owner_id_khac": "99999"})

    assert r.status_code == 400
    assert "Không tìm thấy hồ sơ chủ nuôi" in r.text
    assert _khach_trong_db(db).owner_id is None


# --- Phía khách: không lộ gì, không tự nối ---------------------------------------------


def test_phan_hoi_gui_yeu_cau_giong_nhau_du_so_co_hay_khong_la_chu_nuoi(client, db, seed_basic):
    owners.tao_chu_nuoi(db, ho_ten="Chu That", so_dien_thoai="0912345678")
    phan_hoi = []
    for i, so in enumerate(("0912345678", "0999999999")):
        db.add(Customer(email=f"k{i}@example.com", full_name="Khach", password_hash=hash_password(MAT_KHAU_KHACH)))
        db.commit()
        c = TestClient(app)
        c.post("/khach/dang-nhap", data={"email": f"k{i}@example.com", "mat_khau": MAT_KHAU_KHACH})
        r = c.post("/khach/lien-ket", data={"so_dien_thoai": so})
        phan_hoi.append((r.status_code, r.text.replace(so, "SO")))

    assert phan_hoi[0] == phan_hoi[1]
    assert "Chu That" not in phan_hoi[0][1]


def test_khach_gui_so_khop_chu_nuoi_van_khong_tu_duoc_noi(client, db, seed_basic, khach_client):
    owners.tao_chu_nuoi(db, ho_ten="Chu That", so_dien_thoai="0912345678")

    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    assert _khach_trong_db(db).owner_id is None


def test_khach_gui_so_sai_dinh_dang_bi_tra_400_va_giu_lai_gia_tri_da_nhap(client, db, khach_client):
    r = khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "123", "ghi_chu": "ghi chu cua toi"})

    assert r.status_code == 400
    assert "ghi chu cua toi" in r.text


def test_khach_gui_hai_lan_lan_hai_bi_tu_choi(client, db, khach_client):
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})

    r = khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0987654321"})

    assert r.status_code == 400
    assert "đang chờ" in r.text
    assert db.query(LinkRequest).count() == 1


# --- Phân quyền ------------------------------------------------------------------------


@pytest.mark.parametrize("vai_tro", ["quanly", "letan"])
def test_quan_ly_va_le_tan_vao_duoc_man_hinh_duyet(client, seed_basic, vai_tro):
    assert _nhan_vien(client, seed_basic, vai_tro).get("/lien-ket-khach").status_code == 200


def test_nhan_vien_cham_soc_bi_chan_o_moi_duong_cua_man_hinh_duyet(client, seed_basic, khach_client):
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})
    cs = _nhan_vien(client, seed_basic, "chamsoc1")

    assert cs.get("/lien-ket-khach").status_code == 403
    assert cs.post("/lien-ket-khach/1/duyet", data={"owner_id_khac": "1"}).status_code == 403
    assert cs.post("/lien-ket-khach/1/tu-choi", data={"ly_do": "x"}).status_code == 403
    assert cs.post("/lien-ket-khach/tai-khoan/1/go").status_code == 403


def test_khach_khong_vao_duoc_man_hinh_duyet_va_khong_tu_duyet_cho_minh(client, db, seed_basic, khach_client):
    khach_client.post("/khach/lien-ket", data={"so_dien_thoai": "0912345678"})
    chu = owners.tao_chu_nuoi(db, ho_ten="Chu Nguoi Khac", so_dien_thoai="0900000000")

    r1 = khach_client.get("/lien-ket-khach", follow_redirects=False)
    r2 = khach_client.post("/lien-ket-khach/1/duyet", data={"ung_vien": str(chu.id)}, follow_redirects=False)

    assert (r1.status_code, r1.headers["location"]) == (303, "/login")
    assert (r2.status_code, r2.headers["location"]) == (303, "/login")
    assert _khach_trong_db(db).owner_id is None


def test_chua_dang_nhap_khach_duoc_dua_ve_trang_dang_nhap_khach(client):
    for phuong_thuc, url in (("get", "/khach/lien-ket"), ("post", "/khach/lien-ket")):
        r = getattr(TestClient(app), phuong_thuc)(url, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/khach/dang-nhap", (phuong_thuc, url)


def test_menu_nhan_vien_chi_hien_muc_lien_ket_khach_cho_quan_ly_va_le_tan(client, seed_basic):
    assert "/lien-ket-khach" in _nhan_vien(client, seed_basic, "letan").get("/owners").text
    assert "/lien-ket-khach" not in _nhan_vien(client, seed_basic, "chamsoc1").get("/owners").text
