"""Khách hỏi đáp AI qua HTTP (P9 chặng 7). TC-181, TC-182.

Đồng hồ đóng băng ở 2026-03-12 08:00; `client` đã thay `lay_provider` bằng `fake_ai` nên không test nào chạm mạng.
Điều cần chứng minh:
- Luồng đủ: gõ câu hỏi → 303 → trang kết quả có câu hỏi, câu trả lời và câu khuyến cáo; F5 không gọi AI thêm.
- Riêng tư: dòng log của khách khác = id không tồn tại (cùng 404 từng chữ); cookie nhân viên không dùng được;
  prompt gửi đi và trang kết quả không có tên khách, tên chủ nuôi, thú cưng.
- Hết hạn mức: 429, provider không bị gọi, câu đã gõ và câu khuyến cáo vẫn hiện.
"""

import pytest
from fastapi.testclient import TestClient

from app.ai import prompts
from app.ai.fake import FakeProvider
from app.ai.provider import LoiQuaTai
from app.config import settings
from app.main import app
from app.models.ai_log import AiLog
from app.models.customer import Customer
from app.models.owner import Owner
from app.models.pet import Pet
from app.security import hash_password

MAT_KHAU = "matkhau-khach-1"
TEN_THU_CUNG = "Muc-Rieng-Tu"
TEN_CHU = "Chu Rieng Tu"
KHONG_CO = 99999


@pytest.fixture
def the_gioi(client, db, seed_basic, frozen_clock):
    chu = Owner(full_name=TEN_CHU, phone="0911111111", email="chu@example.com")
    db.add(chu)
    db.flush()
    db.add(Pet(owner_id=chu.id, name=TEN_THU_CUNG, species="Cho"))
    db.add_all([
        Customer(email="a@example.com", full_name="Khach An Rieng", password_hash=hash_password(MAT_KHAU), owner_id=chu.id),
        Customer(email="b@example.com", full_name="Khach B", password_hash=hash_password(MAT_KHAU)),
    ])
    db.commit()
    return seed_basic


def _khach(email):
    c = TestClient(app)
    r = c.post("/khach/dang-nhap", data={"email": email, "mat_khau": MAT_KHAU}, follow_redirects=False)
    assert r.status_code == 303
    return c


@pytest.fixture
def khach_a(the_gioi):
    return _khach("a@example.com")


@pytest.fixture
def khach_b(the_gioi):
    return _khach("b@example.com")


def _hoi(khach, cau="Bao lau nen tam cho cho mot lan?"):
    return khach.post("/khach/hoi-dap", data={"cau_hoi": cau}, follow_redirects=False)


def test_luong_hoi_dap_day_du_den_trang_ket_qua_co_khuyen_cao(khach_a, fake_ai):
    r = _hoi(khach_a)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/khach/hoi-dap/")

    trang = khach_a.get(r.headers["location"])
    assert trang.status_code == 200
    assert "Bao lau nen tam cho cho mot lan?" in trang.text
    assert fake_ai.phan_hoi in trang.text
    assert prompts.DISCLAIMER in trang.text
    assert "AI không thay thế chẩn đoán của bác sĩ thú y" in trang.text


def test_tai_lai_trang_ket_qua_khong_goi_ai_them_lan_nua(khach_a, fake_ai):
    vi_tri = _hoi(khach_a).headers["location"]
    so_lan = len(fake_ai.da_goi)
    for _ in range(3):
        assert khach_a.get(vi_tri).status_code == 200
    assert len(fake_ai.da_goi) == so_lan == 1


def test_trang_hoi_hien_khuyen_cao_va_so_luot_con_lai(khach_a):
    trang = khach_a.get("/khach/hoi-dap")
    assert trang.status_code == 200
    assert "AI không chẩn đoán bệnh, không tư vấn thuốc" in trang.text
    assert f"<strong>{settings.ai_khach_toi_da_moi_ngay}</strong>/{settings.ai_khach_toi_da_moi_ngay}" in trang.text


def test_so_luot_con_lai_giam_sau_moi_cau_hoi(khach_a):
    _hoi(khach_a)
    _hoi(khach_a)
    con = settings.ai_khach_toi_da_moi_ngay - 2
    assert f"<strong>{con}</strong>/" in khach_a.get("/khach/hoi-dap").text


def test_chi_cau_hoi_di_sang_ai_khong_co_ten_khach_chu_nuoi_hay_thu_cung(khach_a, fake_ai):
    _hoi(khach_a)
    gui_di = fake_ai.lan_cuoi.system + fake_ai.lan_cuoi.user
    for rieng_tu in ("Khach An Rieng", "a@example.com", TEN_CHU, "0911111111", "chu@example.com", TEN_THU_CUNG):
        assert rieng_tu not in gui_di


def test_trang_khach_khong_hien_ten_chu_nuoi_hay_thu_cung(khach_a):
    vi_tri = _hoi(khach_a).headers["location"]
    for url in ("/khach/hoi-dap", vi_tri):
        trang = khach_a.get(url).text
        assert TEN_CHU not in trang
        assert TEN_THU_CUNG not in trang


def test_khach_chua_noi_ho_so_van_hoi_duoc(khach_b, fake_ai):
    r = _hoi(khach_b)
    assert r.status_code == 303
    assert khach_b.get(r.headers["location"]).status_code == 200


def test_xin_thuoc_bi_tu_choi_truoc_khi_goi_api_nhung_van_co_trang_ket_qua(khach_a, fake_ai):
    r = _hoi(khach_a, "Cho uong thuoc gi va lieu bao nhieu?")
    assert r.status_code == 303
    trang = khach_a.get(r.headers["location"]).text
    assert "không tư vấn thuốc" in trang
    assert fake_ai.da_goi == []


def test_mo_hinh_lo_tra_ve_lieu_thi_trang_ket_qua_khong_co_lieu(khach_a, fake_ai):
    fake_ai.phan_hoi = "Cho uong 5 mg paracetamol moi ngay."
    trang = khach_a.get(_hoi(khach_a).headers["location"]).text
    assert "paracetamol" not in trang
    assert "5 mg" not in trang
    assert prompts.DISCLAIMER in trang


def test_ai_loi_thi_trang_van_hien_khuyen_cao_giu_cau_da_go_va_khong_tru_luot(khach_a, fake_ai):
    fake_ai.loi_chung = LoiQuaTai("qua tai")
    r = _hoi(khach_a, "Cau hoi can giu lai")
    assert r.status_code == 400
    assert "Cau hoi can giu lai" in r.text
    assert "AI không chẩn đoán bệnh" in r.text
    assert f"<strong>{settings.ai_khach_toi_da_moi_ngay}</strong>/" in r.text


def test_cau_rong_bi_tu_choi_400_khong_goi_api(khach_a, fake_ai):
    r = _hoi(khach_a, "   ")
    assert r.status_code == 400
    assert fake_ai.da_goi == []


def test_het_han_muc_tra_429_khong_goi_api_va_van_hien_khuyen_cao(khach_a, fake_ai, monkeypatch):
    monkeypatch.setattr(settings, "ai_khach_toi_da_moi_ngay", 2)
    assert _hoi(khach_a).status_code == 303
    assert _hoi(khach_a).status_code == 303
    da_goi = len(fake_ai.da_goi)

    r = _hoi(khach_a, "Cau thu ba bi chan")
    assert r.status_code == 429
    assert "hết lượt hỏi AI hôm nay" in r.text
    assert "Cau thu ba bi chan" in r.text
    assert "AI không chẩn đoán bệnh" in r.text
    assert len(fake_ai.da_goi) == da_goi


def test_het_han_muc_cua_khach_a_khong_chan_khach_b(khach_a, khach_b, monkeypatch):
    monkeypatch.setattr(settings, "ai_khach_toi_da_moi_ngay", 1)
    assert _hoi(khach_a).status_code == 303
    assert _hoi(khach_a).status_code == 429
    assert _hoi(khach_b).status_code == 303


def test_log_cua_khach_khac_va_id_khong_ton_tai_cho_cung_mot_404(khach_a, khach_b):
    vi_tri_cua_a = _hoi(khach_a).headers["location"]
    cua_nguoi_khac = khach_b.get(vi_tri_cua_a)
    khong_co = khach_b.get(f"/khach/hoi-dap/{KHONG_CO}")
    assert cua_nguoi_khac.status_code == khong_co.status_code == 404
    assert cua_nguoi_khac.text == khong_co.text


def test_log_cua_nhan_vien_khach_khong_doc_duoc(khach_a, db, the_gioi):
    from app.ai import service as nv

    log = nv.hoi_dap(db, FakeProvider(), the_gioi["receptionist"].id, "Cau cua nhan vien")
    r = khach_a.get(f"/khach/hoi-dap/{log.log_id}")
    assert r.status_code == 404
    assert db.query(AiLog).filter(AiLog.user_id.is_not(None)).count() == 1


def test_chua_dang_nhap_ve_trang_dang_nhap_khach(the_gioi):
    c = TestClient(app)
    for r in (c.get("/khach/hoi-dap", follow_redirects=False), c.post("/khach/hoi-dap", data={"cau_hoi": "x"}, follow_redirects=False), c.get("/khach/hoi-dap/1", follow_redirects=False)):
        assert r.status_code == 303
        assert r.headers["location"] == "/khach/dang-nhap"


def test_cookie_nhan_vien_khong_dung_duoc_cong_khach(the_gioi):
    c = TestClient(app)
    r = c.post("/login", data={"username": the_gioi["manager"].username, "password": "matkhau123"}, follow_redirects=False)
    assert r.status_code == 303
    r = c.get("/khach/hoi-dap", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/khach/dang-nhap"


def test_menu_cong_khach_co_link_hoi_ai(khach_a):
    assert 'href="/khach/hoi-dap"' in khach_a.get("/khach/hoi-dap").text
