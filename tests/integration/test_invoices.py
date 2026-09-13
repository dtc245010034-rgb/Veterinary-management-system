"""Test hóa đơn qua HTTP — P5 chặng 1.

Phục vụ US-19, US-20 — TC-065, TC-068, TC-069, TC-070, TC-072 ở mức integration.

Quy tắc nghiệp vụ đã kiểm kỹ ở tests/unit/test_billing_service.py. Ở đây chỉ kiểm phần
thuộc tầng HTTP: nút trên lưới lịch hẹn, phân quyền, form thu tiền, và việc form giữ lại
dữ liệu đã nhập khi báo lỗi.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.services import care_records, clock, scheduling

NGAY = "2026-03-12"
BAY_GIO = datetime(2026, 3, 12, 8, 0)
GIA = Decimal("150000")


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


@pytest.fixture
def nen(db, seed_basic, frozen_clock):
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    pet = Pet(owner_id=o.id, name="Mực", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=GIA)
    db.add_all([pet, dv])
    db.commit()

    return {"chu": o, "pet": pet, "dv": dv, **seed_basic}


def dat_lich(db, nen, gio=9):
    with clock.freeze(BAY_GIO):
        return scheduling.dat_lich(
            db,
            thu_cung_id=nen["pet"].id,
            dich_vu_id=nen["dv"].id,
            nhan_vien_id=nen["caretaker1"].id,
            bat_dau=datetime(2026, 3, 12, gio, 0),
            nguoi_tao_id=nen["receptionist"].id,
        )


def lich_xong(db, nen, gio=9):
    lich = dat_lich(db, nen, gio)
    with clock.freeze(lich.end_at):
        care_records.ghi_ho_so(
            db, lich.id, nguoi_ghi_id=nen["caretaker1"].id, tinh_trang="Da sạch."
        )
    return lich


def lap_hd(client, lich) -> str:
    """Lập hóa đơn từ lưới lịch, trả về đường dẫn trang hóa đơn.

    `follow_redirects=False` vì TestClient mặc định đi theo chuyển hướng, mà ở đây cần
    chính cái Location để biết hóa đơn nào vừa lập.
    """
    r = client.post(
        f"/appointments/{lich.id}/hoa-don", data={"ngay": NGAY}, follow_redirects=False
    )
    assert r.status_code == 303, r.text[:300]
    return r.headers["location"]


# --- Từ lưới lịch hẹn tới hóa đơn ------------------------------------------------


def test_luoi_lich_hien_nut_lap_hoa_don_cho_lich_da_hoan_thanh(client, db, nen):
    lich_xong(db, nen)
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert r.status_code == 200
    assert "Lập hóa đơn" in r.text


def test_luoi_lich_khong_hien_nut_lap_hoa_don_cho_lich_chua_xong(client, db, nen):
    """Ca biên: nút chỉ được hiện khi bấm vào là thành công."""
    dat_lich(db, nen)
    dang_nhap(client, "letan")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert r.status_code == 200
    assert "Lập hóa đơn" not in r.text


def test_lap_hoa_don_tu_luoi_lich_chuyen_thang_sang_trang_hoa_don(client, db, nen):
    """TC-065 qua HTTP."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")

    duong_dan = lap_hd(client, lich)

    assert duong_dan.startswith("/invoices/")
    trang = client.get(duong_dan)
    assert trang.status_code == 200
    assert "Tắm và sấy" in trang.text
    assert "150.000đ" in trang.text
    assert "Chưa thu" in trang.text


def test_sau_khi_lap_luoi_lich_doi_sang_nut_xem_hoa_don(client, db, nen):
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    lap_hd(client, lich)

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Xem hóa đơn" in r.text
    assert "Lập hóa đơn" not in r.text


def test_lap_hoa_don_lan_hai_bao_loi_ngay_tren_luoi_lich(client, db, nen):
    """TC-068 qua HTTP: thông báo phải quay về đúng lưới ngày đang xem."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    lap_hd(client, lich)

    r = client.post(f"/appointments/{lich.id}/hoa-don", data={"ngay": NGAY})

    assert r.status_code == 400
    assert "đã có hóa đơn" in r.text
    assert "Mực" in r.text  # vẫn là lưới lịch, không phải trang trắng


def test_lap_hoa_don_cho_lich_chua_xong_bao_loi_khong_phai_500(client, db, nen):
    """TC-067 qua HTTP."""
    lich = dat_lich(db, nen)
    dang_nhap(client, "letan")

    r = client.post(f"/appointments/{lich.id}/hoa-don", data={"ngay": NGAY})

    assert r.status_code == 400
    assert "hoàn thành" in r.text


# --- Thu tiền --------------------------------------------------------------------


def test_thu_du_tien_thi_trang_hoa_don_bao_da_thu_du(client, db, nen):
    """TC-069 qua HTTP."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    r = client.post(
        f"{ma}/thanh-toan", data={"so_tien": "150000", "hinh_thuc": "cash"},
        follow_redirects=False,
    )

    assert r.status_code == 303
    trang = client.get(ma)
    assert "Đã thu đủ" in trang.text
    assert "Tiền mặt" in trang.text


def test_thu_mot_phan_con_no_hien_dung_so(client, db, nen):
    """TC-070 qua HTTP."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    client.post(f"{ma}/thanh-toan", data={"so_tien": "50.000", "hinh_thuc": "transfer"})

    trang = client.get(ma)
    assert "Thu một phần" in trang.text
    assert "100.000đ" in trang.text
    assert "Chuyển khoản" in trang.text


def test_thu_vuot_bao_loi_va_giu_lai_so_da_nhap(client, db, nen):
    """TC-072 qua HTTP, kèm luật "báo lỗi không được xóa ô nhập" đã học ở P4."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    r = client.post(f"{ma}/thanh-toan", data={"so_tien": "999999", "hinh_thuc": "card"})

    assert r.status_code == 400
    assert "còn nợ" in r.text
    assert 'value="999999"' in r.text
    assert 'value="card" selected' in r.text


def test_so_tien_khong_phai_so_bao_loi_tieng_viet(client, db, nen):
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    r = client.post(f"{ma}/thanh-toan", data={"so_tien": "abc", "hinh_thuc": "cash"})

    assert r.status_code == 400
    assert "phải là một số" in r.text


@pytest.mark.parametrize("so_tien", ["NaN", "sNaN", "Infinity"])
def test_so_tien_nan_hay_vo_cuc_bao_loi_khong_ra_loi_500(client, db, nen, so_tien):
    """Lỗi thật, rà bằng trình duyệt 11/09: gõ "NaN" vào ô số tiền → màn hình đen 500.

    `Decimal("NaN")` là một Decimal hợp lệ nên lọt qua bước đọc số, rồi phép so
    `so_tien <= 0` ném `decimal.InvalidOperation`. "Infinity" không làm vỡ trang nhưng bị
    báo nhầm là "vượt quá số còn nợ" — cũng phải là "không phải một số".
    """
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    r = client.post(f"{ma}/thanh-toan", data={"so_tien": so_tien, "hinh_thuc": "cash"})

    assert r.status_code == 400
    assert "phải là một số" in r.text


def test_hoa_don_da_thu_du_thi_khong_con_form_thu_tien(client, db, nen):
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)
    client.post(f"{ma}/thanh-toan", data={"so_tien": "150000", "hinh_thuc": "cash"})

    trang = client.get(ma)

    assert "Ghi nhận thanh toán" not in trang.text


def test_hoa_don_cu_van_hien_du_khi_dich_vu_da_ngung_ban(client, db, nen):
    """TC-031.

    Không có mutation nào giết được test này ở P5: không dòng code nào lọc dịch vụ theo
    `is_active` khi hiển thị hóa đơn, nên nó xanh nhờ chính quyết định chép `description`
    và `unit_price` vào dòng hóa đơn. Giữ lại vì đó đúng là chỗ dễ hỏng ở phase sau —
    thống kê doanh thu (P6) mà join sang `services` và lọc dịch vụ đang bán sẽ làm hóa đơn
    cũ biến mất khỏi sổ, âm thầm.
    """
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    nen["dv"].is_active = False
    db.commit()

    trang = client.get(ma)

    assert trang.status_code == 200
    assert "Tắm và sấy" in trang.text
    assert "150.000đ" in trang.text


# --- Hủy hóa đơn -----------------------------------------------------------------


def test_huy_hoa_don_chua_thu_dong_nao(client, db, nen):
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    r = client.post(f"{ma}/huy", follow_redirects=False)

    assert r.status_code == 303
    assert "Đã hủy" in client.get(ma).text


def test_nut_huy_hoa_don_dan_sang_trang_xac_nhan_chu_khong_huy_ngay(client, db, nen):
    """Mỗi lịch chỉ lập được một hóa đơn trọn đời — bấm nhầm là mất hẳn buổi đó.

    Nút phải là link GET sang trang xác nhận, không phải form POST hủy thẳng.
    """
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    trang = client.get(ma)

    assert f'href="{ma}/huy"' in trang.text


def test_trang_xac_nhan_huy_hoa_don_noi_ro_hau_qua_va_chua_huy_gi(client, db, nen):
    """GET chỉ được hỏi lại, tuyệt đối không đổi dữ liệu."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    trang = client.get(f"{ma}/huy")

    assert trang.status_code == 200
    assert "không lập lại hóa đơn được" in trang.text
    assert "Đã hủy" not in client.get(ma).text


def test_hoa_don_da_co_thanh_toan_khong_con_nut_huy(client, db, nen):
    """Ca biên: nút không được hiện khi bấm vào là bị từ chối."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)
    client.post(f"{ma}/thanh-toan", data={"so_tien": "50000", "hinh_thuc": "cash"})

    trang = client.get(ma)

    assert "Hủy hóa đơn" not in trang.text


# --- Danh sách và phân quyền -----------------------------------------------------


def test_danh_sach_hoa_don_rong_van_chi_duong_di_tiep(client, nen):
    dang_nhap(client, "letan")

    r = client.get("/invoices")

    assert r.status_code == 200
    assert "Chưa có hóa đơn nào" in r.text


def test_menu_co_link_hoa_don_cho_quan_ly_va_le_tan(client, nen):
    for tai_khoan in ("quanly", "letan"):
        dang_nhap(client, tai_khoan)
        r = client.get("/invoices")
        assert 'href="/invoices"' in r.text, tai_khoan


def test_nhan_vien_cham_soc_khong_thay_link_hoa_don(client, nen):
    """US-02: `caretaker` không có quyền nào ở mục hóa đơn, kể cả xem."""
    dang_nhap(client, "chamsoc1")

    r = client.get("/appointments/cua-toi")

    assert r.status_code == 200
    assert 'href="/invoices"' not in r.text


def test_nhan_vien_cham_soc_mo_thang_trang_hoa_don_bi_tu_choi(client, db, nen):
    """Ẩn link là chưa đủ — gõ thẳng URL phải ra 403."""
    lich_xong(db, nen)
    dang_nhap(client, "chamsoc1")

    assert client.get("/invoices").status_code == 403


def test_nhan_vien_cham_soc_khong_thay_nut_lap_hoa_don_tren_lich_cua_minh(client, db, nen):
    lich_xong(db, nen)
    dang_nhap(client, "chamsoc1")

    r = client.get(f"/appointments/cua-toi?ngay={NGAY}")

    assert r.status_code == 200
    assert "Lập hóa đơn" not in r.text


def test_mo_hoa_don_khong_ton_tai_ra_404_khong_phai_500(client, nen):
    dang_nhap(client, "letan")

    r = client.get("/invoices/999")

    assert r.status_code == 404
    assert "Không tìm thấy hóa đơn" in r.text


# --- Lỗi tìm ra khi rà bằng trình duyệt ngày 07/09 -------------------------------


def _khoi_the(html: str) -> str:
    """Phần lưới thẻ trên trang chủ, không tính thanh điều hướng.

    Thanh điều hướng cũng chứa `/invoices` nên assert trên cả trang sẽ xanh ngay cả khi
    trang chủ thiếu thẻ — đúng loại test xanh mà không chứng minh gì.
    """
    dau = html.index('<div class="luoi-the">')
    return html[dau : html.index("</div>", dau)]


def test_trang_chu_co_the_hoa_don_cho_quan_ly_va_le_tan(client, nen):
    """Thêm link menu mà quên trang chủ là lặp lại đúng lớp lỗi đã gặp ở P4."""
    for tai_khoan in ("quanly", "letan"):
        dang_nhap(client, tai_khoan)
        assert "/invoices" in _khoi_the(client.get("/").text), tai_khoan


def test_trang_chu_khong_co_the_hoa_don_cho_nhan_vien_cham_soc(client, nen):
    dang_nhap(client, "chamsoc1")

    assert "/invoices" not in _khoi_the(client.get("/").text)


def test_hoa_don_da_huy_khong_con_no_dong_nao(client, db, nen):
    """Hóa đơn đã hủy mà vẫn hiện "còn nợ 150.000đ" là con số sẽ bị đi đòi nhầm."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)
    client.post(f"{ma}/huy")

    trang = client.get(ma)
    danh_sach = client.get("/invoices")

    assert "150.000đ" not in trang.text.split("Còn nợ")[1][:80]
    assert "Đã hủy" in danh_sach.text


def test_luoi_lich_noi_ro_hoa_don_da_bi_huy(client, db, nen):
    """Bấm "Xem hóa đơn" rồi mới biết nó đã hủy, và không lập lại được, là ngõ cụt câm."""
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)
    client.post(f"{ma}/huy")

    r = client.get(f"/appointments?ngay={NGAY}")

    assert "Hóa đơn đã hủy" in r.text


def test_trang_hoa_don_da_huy_noi_ro_buoc_tiep_theo(client, db, nen):
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)
    client.post(f"{ma}/huy")

    trang = client.get(ma)

    assert "không lập lại được" in trang.text


def test_huy_lich_khi_con_hoa_don_hien_ma_hoa_don_cho_le_tan(client, db, nen):
    """TC-074 ở tầng HTTP.

    Lưới lịch không hiện nút Hủy cho lịch đã xong, nên ca này tới từ một tab cũ mở sẵn
    hoặc từ POST gọi thẳng. Ẩn nút là chưa đủ — máy chủ phải chặn thật, và phải nói ra
    hóa đơn nào đang giữ buổi đó lại.
    """
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)

    r = client.post(
        f"/appointments/{lich.id}/huy", data={"ngay": NGAY, "ly_do": "Khách báo bận"}
    )

    assert r.status_code == 400
    assert ma.rsplit("/", 1)[-1] in r.text


def test_trang_hoa_don_da_huy_khong_bay_cach_lam_ma_he_thong_tu_choi(client, db, nen):
    """Khung hướng dẫn từng bảo “hãy hủy luôn lịch hẹn” — việc hệ thống luôn từ chối.

    Kiểm cả hai vế trong một ca, vì tách ra thì mỗi vế đều xanh mà lời khuyên vẫn sai:
    máy chủ thật sự từ chối hủy lịch đã xong, và trang hóa đơn không bày cách làm đó.
    """
    lich = lich_xong(db, nen)
    dang_nhap(client, "letan")
    ma = lap_hd(client, lich)
    client.post(f"{ma}/huy")

    r = client.post(
        f"/appointments/{lich.id}/huy", data={"ngay": NGAY, "ly_do": "Buổi không diễn ra"}
    )

    assert r.status_code == 400
    assert "hủy luôn lịch hẹn" not in client.get(ma).text
