"""Test ba tính năng AI qua HTTP — P7 chặng 2.

TC-084, TC-085, TC-086, TC-089, TC-090, TC-091, TC-099, TC-100 · các ca G-16 → G-19.

Cách tính toán và guardrail đã kiểm kỹ ở tầng unit (`tests/unit/test_ai_service.py`); ở đây
chỉ kiểm phần thuộc tầng HTTP: phân quyền, Post/Redirect/Get, trang không vỡ khi AI lỗi, và
dòng khuyến cáo có thật sự hiện trên màn hình hay không.

Fixture `client` đã thay `lay_provider` bằng `fake_ai`, nên không test nào chạm mạng.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.ai import prompts
from app.ai.provider import LoiQuaTai
from app.models.ai_log import AiLog
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.services import care_records, clock, scheduling, vaccinations

SO_DIEN_THOAI = "0912345678"
EMAIL = "hang@example.com"
NGAY = "2026-03-12"


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303), f"Đăng nhập {username} thất bại"
    return client


@pytest.fixture
def nen(db, seed_basic, frozen_clock):
    """Một thú cưng, một buổi đã xong (có hồ sơ), một lịch sắp tới, một mũi tiêm đến hạn."""
    chu = Owner(
        full_name="Đỗ Thị Hằng", phone=SO_DIEN_THOAI, email=EMAIL,
        address="So 12 ngo 3 Kim Ma, Ha Noi",
    )
    db.add(chu)
    db.flush()
    pet = Pet(owner_id=chu.id, name="Mực", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=Decimal("150000"))
    db.add_all([pet, dv])
    db.commit()

    cs, lt = seed_basic["caretaker1"], seed_basic["receptionist"]

    def dat(bat_dau):
        with clock.freeze(bat_dau - timedelta(days=1)):
            return scheduling.dat_lich(
                db, thu_cung_id=pet.id, dich_vu_id=dv.id, nhan_vien_id=cs.id,
                bat_dau=bat_dau, nguoi_tao_id=lt.id,
            )

    da_xong = dat(datetime(2026, 3, 11, 9, 0))
    with clock.freeze(da_xong.end_at):
        care_records.ghi_ho_so(
            db, da_xong.id, nguoi_ghi_id=cs.id,
            tinh_trang=f"Da khô. Khách gửi ảnh qua {EMAIL}, gọi {SO_DIEN_THOAI}",
        )

    sap_toi = dat(datetime(2026, 3, 20, 9, 0))
    mui = vaccinations.ghi_mui_tiem(
        db, pet.id, "Dại", date(2025, 3, 1), han_nhac=date(2026, 3, 20)
    )
    return {"pet": pet, "da_xong": da_xong, "sap_toi": sap_toi, "mui": mui}


def theo_chuyen_huong(client, r):
    """Đi theo Location của Post/Redirect/Get, trả về trang kết quả."""
    assert r.status_code == 303, r.text[:300]
    return client.get(r.headers["location"])


# --- Nhắc lịch (US-24) -------------------------------------------------------------


def test_soan_tin_nhac_lich_tu_luoi_lich_ra_trang_ket_qua(client, db, nen, fake_ai):
    """Nút trên lưới lịch dẫn tới một trang có nội dung sửa được."""
    fake_ai.phan_hoi = "Chào anh/chị, bé Mực có lịch tắm lúc 09:00 ngày 20/03."
    dang_nhap(client, "letan")

    r = client.post(
        f"/ai/nhac-lich/lich-hen/{nen['sap_toi'].id}",
        data={"tu": f"/appointments?ngay={NGAY}"},
        follow_redirects=False,
    )
    trang = theo_chuyen_huong(client, r)

    assert "bé Mực có lịch tắm" in trang.text
    assert "<textarea" in trang.text  # sửa được trước khi gửi
    assert "AI không thay thế chẩn đoán của bác sĩ thú y" in trang.text


def test_nut_soan_tin_nhac_co_tren_luoi_lich_va_tro_dung_duong_dan(client, db, nen):
    """Đi bằng chính nút trên trang, không tự dựng URL."""
    dang_nhap(client, "letan")

    # Lưới mở đúng NGÀY CỦA LỊCH ấy (20/03), không phải "hôm nay" của đồng hồ cố định.
    trang = client.get("/appointments?ngay=2026-03-20")

    assert f'action="/ai/nhac-lich/lich-hen/{nen["sap_toi"].id}"' in trang.text
    assert "Soạn tin nhắc (AI)" in trang.text


def test_le_tan_sua_tin_nhan_roi_chot_thi_ban_sua_duoc_dung(client, db, nen, fake_ai):
    """TC-084: AI chỉ soạn nháp, người quyết định.

    Bản chốt phải là bản đã sửa, còn `ai_logs.response` vẫn giữ nguyên bản AI trả về — đó là
    bằng chứng cho báo cáo cuối kỳ.
    """
    fake_ai.phan_hoi = "Bản nháp của AI."
    dang_nhap(client, "letan")
    r = client.post(
        f"/ai/nhac-lich/lich-hen/{nen['sap_toi'].id}", data={"tu": "/appointments"},
        follow_redirects=False,
    )
    ma_log = int(r.headers["location"].split("/ket-qua/")[1].split("?")[0])

    da_sua = "Chào chị Hằng, 9h sáng mai em đón bé Mực nhé."
    trang = client.post(f"/ai/ket-qua/{ma_log}/chot", data={"noi_dung": da_sua, "tu": "/appointments"})

    assert da_sua in trang.text
    assert "Bản nháp của AI." not in trang.text
    assert db.get(AiLog, ma_log).response == "Bản nháp của AI."


def test_nhan_vien_cham_soc_khong_soan_duoc_tin_nhac(client, db, nen):
    """Phân quyền đã chốt 18/09: nhắc lịch là việc của quầy."""
    dang_nhap(client, "chamsoc1")

    r = client.post(f"/ai/nhac-lich/lich-hen/{nen['sap_toi'].id}", data={"tu": "/appointments"})

    assert r.status_code == 403


def test_nhan_vien_cham_soc_khong_mo_duoc_ket_qua_nhac_lich_cua_nguoi_khac(client, db, nen, fake_ai):
    """Ẩn nút là chưa đủ — gõ thẳng đường dẫn trang kết quả cũng phải bị chặn."""
    dang_nhap(client, "letan")
    r = client.post(
        f"/ai/nhac-lich/lich-hen/{nen['sap_toi'].id}", data={"tu": "/appointments"},
        follow_redirects=False,
    )
    duong_dan = r.headers["location"]

    client.post("/logout")
    dang_nhap(client, "chamsoc1")

    assert client.get(duong_dan).status_code == 403


def test_nhac_lich_tiem_di_tu_trang_tiem_phong(client, db, nen, fake_ai):
    """TC-083 ở tầng HTTP: nút nằm trên danh sách đến hạn."""
    fake_ai.phan_hoi = "Bé Mực tới hạn tiêm nhắc vắc-xin Dại."
    dang_nhap(client, "letan")

    danh_sach = client.get("/vaccinations")
    assert f'action="/ai/nhac-lich/tiem/{nen["mui"].id}"' in danh_sach.text

    r = client.post(f"/ai/nhac-lich/tiem/{nen['mui'].id}", data={"tu": "/vaccinations"},
                    follow_redirects=False)
    trang = theo_chuyen_huong(client, r)

    assert "vắc-xin Dại" in trang.text
    assert prompts.NHAC_XAC_NHAN_TIEM in trang.text


# --- Tóm tắt hồ sơ (US-25) ----------------------------------------------------------


def test_tom_tat_ho_so_tu_trang_thu_cung(client, db, nen, fake_ai):
    """TC-086."""
    fake_ai.phan_hoi = "Bé Mực tắm ngày 11/03, da khô."
    dang_nhap(client, "letan")

    trang_pet = client.get(f"/pets/{nen['pet'].id}")
    assert f'action="/ai/tom-tat/{nen["pet"].id}"' in trang_pet.text

    r = client.post(f"/ai/tom-tat/{nen['pet'].id}", data={"tu": f"/pets/{nen['pet'].id}"},
                    follow_redirects=False)
    trang = theo_chuyen_huong(client, r)

    assert "da khô" in trang.text
    assert prompts.DISCLAIMER in trang.text


def test_nhan_vien_cham_soc_van_tom_tat_duoc(client, db, nen, fake_ai):
    """Phân quyền đã chốt: tóm tắt và hỏi đáp mở cho cả ba vai trò."""
    dang_nhap(client, "chamsoc1")

    r = client.post(f"/ai/tom-tat/{nen['pet'].id}", data={}, follow_redirects=False)

    assert r.status_code == 303


def test_thu_cung_chua_co_ho_so_thi_bao_thieu_du_lieu_khong_vo_trang(client, db, nen, fake_ai):
    """Ca G-20 ở tầng HTTP: báo rõ ràng, và không gọi API."""
    moi = Pet(owner_id=nen["pet"].owner_id, name="Mun", species="Mèo")
    db.add(moi)
    db.commit()
    dang_nhap(client, "letan")

    r = client.post(f"/ai/tom-tat/{moi.id}", data={})

    assert r.status_code == 400
    assert "chưa có hồ sơ" in r.text
    assert fake_ai.da_goi == []


# --- Hỏi đáp (US-26) ----------------------------------------------------------------


def test_hoi_dap_tra_loi_va_luon_kem_khuyen_cao(client, db, nen, fake_ai):
    """TC-089 · G-01 → G-03."""
    fake_ai.phan_hoi = "Nên tắm cho chó 2–4 tuần một lần."
    dang_nhap(client, "letan")

    r = client.post("/ai/hoi-dap", data={"cau_hoi": "Bao lâu nên tắm cho chó?"},
                    follow_redirects=False)
    trang = theo_chuyen_huong(client, r)

    assert "2–4 tuần" in trang.text
    assert prompts.DISCLAIMER in trang.text


def test_che_do_gia_lap_ghi_ro_tren_trang_ket_qua_khong_gan_ten_gemini(client, db, nen):
    """Người dùng 19/09 hỏi thời tiết ở chế độ fake, thấy câu mẫu kèm "Trả lời bởi:
    gemini-3.5-flash" và tưởng Gemini trả lời sai."""
    from app.ai.fake import FakeProvider
    from app.ai.service import lay_provider

    client.app.dependency_overrides[lay_provider] = lambda: FakeProvider(tinh_quota=False)
    dang_nhap(client, "letan")

    r = client.post("/ai/hoi-dap", data={"cau_hoi": "Hôm nay thời tiết Hà Nội thế nào"},
                    follow_redirects=False)
    trang = theo_chuyen_huong(client, r)

    assert "AI giả lập — không gọi Gemini" in trang.text
    assert "gemini-" not in trang.text


def test_trang_ai_bao_dang_chay_che_do_gia_lap_chi_khi_cau_hinh_la_fake(client, nen, monkeypatch):
    from app.config import settings

    dang_nhap(client, "quanly")
    monkeypatch.setattr(settings, "ai_provider", "fake")
    for duong in ("/ai/hoi-dap", "/ai/quota"):
        assert "Đang chạy chế độ AI giả lập" in client.get(duong).text, duong

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    assert "Đang chạy chế độ AI giả lập" not in client.get("/ai/hoi-dap").text


def test_moi_luot_hoi_dap_sinh_mot_ban_ghi_ai_logs(client, db, nen, fake_ai):
    """TC-091."""
    dang_nhap(client, "letan")

    client.post("/ai/hoi-dap", data={"cau_hoi": "Cắt móng cho mèo bao lâu một lần?"})

    logs = db.query(AiLog).all()
    assert len(logs) == 1
    assert logs[0].feature == "qa"


def test_tai_lai_trang_ket_qua_khong_goi_ai_them_lan_nua(client, db, nen, fake_ai):
    """Post/Redirect/Get: F5 trên trang kết quả là đọc lại bản ghi, không đốt thêm quota."""
    dang_nhap(client, "letan")
    r = client.post("/ai/hoi-dap", data={"cau_hoi": "Chải lông cho mèo thế nào?"},
                    follow_redirects=False)
    duong_dan = r.headers["location"]

    client.get(duong_dan)
    client.get(duong_dan)

    assert len(fake_ai.da_goi) == 1
    assert db.query(AiLog).count() == 1


def test_cau_hoi_xin_lieu_thuoc_khong_goi_api_va_van_ra_trang_ket_qua(client, db, nen, fake_ai):
    """G-08 ở tầng HTTP: người dùng vẫn nhận được câu trả lời tử tế, chỉ là không từ AI."""
    dang_nhap(client, "letan")

    r = client.post("/ai/hoi-dap", data={"cau_hoi": "Cho mèo uống paracetamol mấy viên?"},
                    follow_redirects=False)
    trang = theo_chuyen_huong(client, r)

    assert fake_ai.da_goi == []
    assert "không tư vấn thuốc" in trang.text
    assert prompts.DISCLAIMER in trang.text


# --- Lỗi AI (US-24, US-26) ------------------------------------------------------------


def test_ai_loi_thi_trang_khong_vo_va_du_lieu_lich_hen_con_nguyen(client, db, nen, fake_ai):
    """TC-085 · ca G-17."""
    fake_ai.loi_chung = LoiQuaTai("503 quá tải")
    dang_nhap(client, "letan")

    r = client.post(f"/ai/nhac-lich/lich-hen/{nen['sap_toi'].id}", data={"tu": "/appointments"})

    assert r.status_code == 400
    assert "500" not in r.text
    assert "hết lượt miễn phí hôm nay" in r.text
    db.refresh(nen["sap_toi"])
    assert nen["sap_toi"].status == "booked"


def test_ai_loi_thi_dong_khuyen_cao_van_hien(client, db, nen, fake_ai):
    """TC-090 · ca G-19: khuyến cáo nằm trong template nên không phụ thuộc phản hồi AI."""
    fake_ai.loi_chung = LoiQuaTai("503 quá tải")
    dang_nhap(client, "letan")

    r = client.post(f"/ai/tom-tat/{nen['pet'].id}", data={})

    assert "AI không thay thế chẩn đoán của bác sĩ thú y" in r.text


def test_ai_loi_o_trang_hoi_dap_giu_lai_cau_da_go(client, db, nen, fake_ai):
    fake_ai.loi_chung = LoiQuaTai("503 quá tải")
    dang_nhap(client, "letan")

    r = client.post("/ai/hoi-dap", data={"cau_hoi": "Bao lâu nên tắm cho chó?"})

    assert r.status_code == 400
    assert "Bao lâu nên tắm cho chó?" in r.text


def test_loi_ai_van_ghi_log_bao_loi(client, db, nen, fake_ai):
    """TC-100 · ca G-18."""
    fake_ai.loi_chung = LoiQuaTai("503 quá tải")
    dang_nhap(client, "letan")

    client.post("/ai/hoi-dap", data={"cau_hoi": "Bao lâu nên tắm cho chó?"})

    log = db.query(AiLog).one()
    assert log.is_error is True
    assert log.response is None


# --- Dữ liệu cá nhân (US-28) ----------------------------------------------------------


def test_ai_logs_khong_luu_so_dien_thoai_hay_email_cua_khach(client, db, nen, fake_ai):
    """TC-099 · ca G-16. Ghi chú hồ sơ trong fixture cố ý có cả hai."""
    dang_nhap(client, "letan")

    client.post(f"/ai/tom-tat/{nen['pet'].id}", data={})
    client.post(f"/ai/nhac-lich/lich-hen/{nen['sap_toi'].id}", data={"tu": "/appointments"})

    assert db.query(AiLog).count() == 2
    for log in db.query(AiLog).all():
        assert SO_DIEN_THOAI not in log.prompt
        assert EMAIL not in log.prompt
        assert "Đỗ Thị Hằng" not in log.prompt


# --- Trang quota (chỉ quản lý) ---------------------------------------------------------


def test_quan_ly_xem_duoc_bang_quota(client, db, nen, fake_ai):
    dang_nhap(client, "quanly")

    r = client.get("/ai/quota")

    assert r.status_code == 200
    assert "gemini-3.6-flash" in r.text
    assert "ước tính" in r.text


@pytest.mark.parametrize("username", ["letan", "chamsoc1"])
def test_khong_phai_quan_ly_thi_khong_mo_duoc_trang_quota(client, db, nen, username):
    dang_nhap(client, username)

    assert client.get("/ai/quota").status_code == 403
    assert client.post("/ai/quota/dat-lai").status_code == 403


def test_dat_lai_quota_xoa_trang_thai_chan(client, db, nen, fake_ai):
    from app.ai import quota

    quota.ghi_model_khong_co(db, "gemini-3.6-flash", "đã tắt")
    dang_nhap(client, "quanly")

    r = client.post("/ai/quota/dat-lai", follow_redirects=True)

    assert "Đã đặt lại trạng thái" in r.text
    assert "không còn khả dụng" not in r.text


# --- Đường dẫn quay lại ----------------------------------------------------------------


def test_duong_dan_quay_lai_ra_ngoai_he_thong_bi_bo_qua(client, db, nen, fake_ai):
    """`//evil.com` là URL hợp lệ với trình duyệt — nhận nó là mở đường chuyển hướng ra ngoài."""
    dang_nhap(client, "letan")

    r = client.post(f"/ai/tom-tat/{nen['pet'].id}", data={"tu": "//evil.com"},
                    follow_redirects=False)
    trang = theo_chuyen_huong(client, r)

    assert "//evil.com" not in trang.text
    assert 'href="/"' in trang.text


@pytest.mark.parametrize(
    "duong_dan_doc",
    [
        "/\\vi-du-ngoai.test",       # dấu `\` — trình duyệt coi `/\` y như `//`
        "/\t/vi-du-ngoai.test",      # ký tự tab thật trong chuỗi
        "/\n/vi-du-ngoai.test",      # xuống dòng
        "/\r/vi-du-ngoai.test",      # về đầu dòng
        "//vi-du-ngoai.test",        # ca đã chặn từ trước, giữ để không sửa hỏng
        "https://vi-du-ngoai.test",  # ca đã chặn từ trước
    ],
)
def test_moi_dang_duong_dan_ra_ngoai_deu_bi_bo_qua(client, db, nen, fake_ai, duong_dan_doc):
    """Bốn dạng đầu **lọt qua** phép kiểm cũ — đo bằng Chrome ngày 20/09 (M-01).

    Phép kiểm cũ chỉ chặn chuỗi bắt đầu bằng `//`. Nhưng trình duyệt coi `\\` tương đương
    `/`, và bỏ qua ký tự điều khiển (tab, LF, CR) khi phân giải URL — nên `/\\host` và
    `/<tab>/host` đều đưa người dùng ra máy chủ ngoài. Đo thật trong Chrome: `location.host`
    của nút "Quay lại" ra `vi-du-ngoai.test` với cả bốn dạng.

    NẾU TEST NÀY ĐỎ: `_quay_lai` nhận một chuỗi mà trình duyệt phân giải ra host ngoài.
    """
    dang_nhap(client, "letan")

    r = client.post(
        f"/ai/tom-tat/{nen['pet'].id}",
        data={"tu": duong_dan_doc},
        follow_redirects=False,
    )
    trang = theo_chuyen_huong(client, r)

    assert "vi-du-ngoai.test" not in trang.text, (
        f"{duong_dan_doc!r} lọt vào trang — nút Quay lại trỏ ra ngoài hệ thống"
    )
    assert 'href="/"' in trang.text


def test_menu_co_link_tro_ly_ai_cho_moi_vai_tro(client, db, nen):
    for username in ("quanly", "letan", "chamsoc1"):
        dang_nhap(client, username)
        trang = client.get("/")
        assert '/ai/hoi-dap' in trang.text, f"{username} không thấy link Trợ lý AI"
        client.post("/logout")


# --- L-05: trang kết quả phải hiện lại câu hỏi -----------------------------------
#
# Đo bằng Chrome 24/09: hỏi xong sang trang kết quả thì chỉ thấy câu trả lời. Theo mẫu
# Post/Redirect/Get, trang kết quả là một URL riêng và có thể mở lại sau — không có câu
# hỏi thì không biết câu trả lời đang trả lời cái gì.
#
# Câu hỏi lấy từ `log.prompt`: với tính năng hỏi đáp, `prompt` chính là câu người dùng
# gõ, đã qua `xoa_lien_he`. Không thêm cột, không truyền qua URL.


def test_trang_ket_qua_hoi_dap_hien_lai_cau_hoi(client, seed_basic):
    dang_nhap(client, "letan")
    cau_hoi = "Chó của tôi nên tắm bao lâu một lần?"

    r = client.post("/ai/hoi-dap", data={"cau_hoi": cau_hoi}, follow_redirects=True)

    assert r.status_code == 200
    assert cau_hoi in r.text


def test_mo_lai_trang_ket_qua_van_thay_cau_hoi(client, seed_basic):
    """Post/Redirect/Get: mở lại URL kết quả không gọi AI nữa, nhưng vẫn phải đủ ngữ cảnh."""
    dang_nhap(client, "letan")
    cau_hoi = "Mèo con mấy tuần thì tẩy giun được?"
    r = client.post("/ai/hoi-dap", data={"cau_hoi": cau_hoi}, follow_redirects=True)
    duong_dan = str(r.url)

    lai = client.get(duong_dan)

    assert cau_hoi in lai.text


def test_cau_hoi_qua_dai_bao_loi_tieng_viet_khong_vo_trang(client, seed_basic):
    """M-03 ở tầng HTTP: lỗi phải ra trang có bố cục, không phải JSON thô hay 500."""
    dang_nhap(client, "letan")

    r = client.post("/ai/hoi-dap", data={"cau_hoi": "Chó " * 6000}, follow_redirects=True)

    assert r.status_code == 400
    assert "ký tự" in r.text
