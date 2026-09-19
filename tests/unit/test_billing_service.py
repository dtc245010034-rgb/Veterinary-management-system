"""Test cho app/services/billing.py — hóa đơn và thanh toán.

Phục vụ US-19, US-20 — TC-065 → TC-073.

Đây là phase đề bài yêu cầu đích danh phải có test. Hai điều được kiểm kỹ nhất, vì cả hai
đều là loại sai **âm thầm** — không exception, không lỗi 500, chỉ có con số sai:

1. Đơn giá được CHÉP vào dòng hóa đơn. Đổi giá dịch vụ tháng sau không được làm đổi hóa
   đơn tháng trước.
2. Cột `status` luôn khớp giá trị suy lại từ payments, ở **từng bước** của chuỗi chuyển
   trạng thái chứ không chỉ bước cuối.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.appointment import Appointment
from app.models.invoice import Invoice
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.services import billing as nv
from app.services import care_records, clock, scheduling
from app.services.errors import LoiNghiepVu

BAY_GIO = datetime(2026, 3, 12, 8, 0)
GIA_GOC = Decimal("150000")


def gio(h: int, p: int = 0, ngay: int = 12) -> datetime:
    return datetime(2026, 3, ngay, h, p)


@pytest.fixture
def nen(db, frozen_clock):
    return _dung_nen(db)


def _dung_nen(db) -> dict:
    o = Owner(full_name="Đỗ Thị Hằng", phone="0912345678")
    db.add(o)
    db.flush()

    pet = Pet(owner_id=o.id, name="Mực", species="Chó")
    dv = Service(code="TAM", name="Tắm và sấy", duration_min=60, price=GIA_GOC)
    cs = User(username="cs1", password_hash="b", full_name="Lê Văn Chăm", role="caretaker")
    lt = User(username="letan", password_hash="b", full_name="Trần Thị Lễ", role="receptionist")
    db.add_all([pet, dv, cs, lt])
    db.commit()
    return {"chu": o, "pet": pet, "dv": dv, "cs": cs, "letan": lt}


def _dat(db, nen, bat_dau=None) -> Appointment:
    with clock.freeze(BAY_GIO):
        return scheduling.dat_lich(
            db,
            thu_cung_id=nen["pet"].id,
            dich_vu_id=nen["dv"].id,
            nhan_vien_id=nen["cs"].id,
            bat_dau=bat_dau or gio(9),
            nguoi_tao_id=nen["letan"].id,
        )


def lich_xong(db, nen, bat_dau=None) -> Appointment:
    """Một lịch đã `done` — đi qua đúng luồng thật: đặt lịch rồi ghi hồ sơ chăm sóc."""
    lich = _dat(db, nen, bat_dau)
    with clock.freeze(lich.end_at):
        care_records.ghi_ho_so(
            db, lich.id, nguoi_ghi_id=nen["cs"].id, tinh_trang="Da sạch, tai khô."
        )
    return lich


# --- Lập hóa đơn -----------------------------------------------------------------


def test_lap_hoa_don_tu_lich_done_ra_trang_thai_chua_thu(db, nen):
    """TC-065 happy path."""
    lich = lich_xong(db, nen)

    hd = nv.lap_hoa_don(db, lich.id)

    assert hd.id is not None
    assert hd.status == "unpaid"
    assert hd.owner_id == nen["chu"].id
    assert hd.appointment_id == lich.id
    assert hd.total_amount == GIA_GOC
    assert hd.con_no == GIA_GOC
    assert hd.da_tra == Decimal("0")


def test_dong_hoa_don_chep_lai_ten_va_don_gia_cua_dich_vu(db, nen):
    """TC-065: đơn giá chốt tại thời điểm lập, không phải tham chiếu."""
    lich = lich_xong(db, nen)

    hd = nv.lap_hoa_don(db, lich.id)

    assert len(hd.dong) == 1
    dong = hd.dong[0]
    assert dong.service_id == nen["dv"].id
    assert dong.description == "Tắm và sấy"
    assert dong.qty == 1
    assert dong.unit_price == GIA_GOC
    assert dong.amount == GIA_GOC


def test_doi_gia_dich_vu_khong_lam_doi_hoa_don_cu(db, nen):
    """TC-066 — ca đắt giá nhất của phase.

    Không có test này, việc tham chiếu `services.price` thay vì chép sẽ chạy xanh suốt
    P5 và chỉ lộ ra khi sổ sách tháng trước tự đổi số.
    """
    lich = lich_xong(db, nen)
    hd = nv.lap_hoa_don(db, lich.id)
    ma_hd = hd.id

    nen["dv"].price = Decimal("200000")
    nen["dv"].name = "Tắm và sấy (giá mới)"
    db.commit()
    db.expire_all()  # buộc đọc lại từ CSDL, không lấy đối tượng còn trong bộ nhớ

    lai = nv.lay_hoa_don(db, ma_hd)
    assert lai.total_amount == GIA_GOC
    assert lai.dong[0].unit_price == GIA_GOC
    assert lai.dong[0].description == "Tắm và sấy"


def test_tong_tien_bang_so_luong_nhan_don_gia(db, nen):
    """TC-066: `total_amount` suy từ các dòng, không nhận từ ngoài."""
    lich = lich_xong(db, nen)

    hd = nv.lap_hoa_don(db, lich.id)

    assert hd.total_amount == sum(d.qty * d.unit_price for d in hd.dong)


def test_lap_hoa_don_tu_lich_chua_hoan_thanh_bi_tu_choi(db, nen):
    """TC-067 — ca biên."""
    lich = _dat(db, nen)  # mới `booked`, chưa ai ghi hồ sơ

    with pytest.raises(LoiNghiepVu) as loi:
        nv.lap_hoa_don(db, lich.id)

    assert "hoàn thành" in str(loi.value).lower()
    assert db.query(Invoice).count() == 0


def test_lap_hoa_don_tu_lich_da_huy_bi_tu_choi(db, nen):
    """TC-067 — nhánh còn lại của cùng phép kiểm."""
    lich = _dat(db, nen)
    with clock.freeze(BAY_GIO):
        scheduling.huy_lich(db, lich.id, ly_do="Khách bận.")

    with pytest.raises(LoiNghiepVu):
        nv.lap_hoa_don(db, lich.id)


def test_lap_hoa_don_lan_hai_cho_cung_lich_bi_tu_choi(db, nen):
    """TC-068."""
    lich = lich_xong(db, nen)
    nv.lap_hoa_don(db, lich.id)

    with pytest.raises(LoiNghiepVu) as loi:
        nv.lap_hoa_don(db, lich.id)

    assert "hóa đơn" in str(loi.value).lower()
    assert db.query(Invoice).count() == 1


def test_lap_hoa_don_cho_lich_khong_ton_tai_bi_tu_choi(db, nen):
    with pytest.raises(LoiNghiepVu):
        nv.lap_hoa_don(db, 999)


# --- Ghi nhận thanh toán ---------------------------------------------------------


def test_tra_du_mot_lan_thi_thanh_da_thu_du(db, nen):
    """TC-069 happy path."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    nv.ghi_nhan_thanh_toan(db, hd.id, GIA_GOC)

    assert hd.status == "paid"
    assert hd.con_no == Decimal("0")
    assert hd.da_tra == GIA_GOC


def test_tra_mot_phan_thi_thanh_thu_mot_phan_va_con_no_dung_so(db, nen):
    """TC-070."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("50000"))

    assert hd.status == "partial"
    assert hd.da_tra == Decimal("50000")
    assert hd.con_no == Decimal("100000")


def test_tra_not_phan_con_lai_thi_thanh_da_thu_du(db, nen):
    """TC-071 — và kiểm cột `status` khớp giá trị suy lại ở TỪNG bước."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    assert hd.status == nv.trang_thai_tinh_lai(hd) == "unpaid"

    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("50000"))
    assert hd.status == nv.trang_thai_tinh_lai(hd) == "partial"

    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("100000"))
    assert hd.status == nv.trang_thai_tinh_lai(hd) == "paid"
    assert hd.con_no == Decimal("0")
    assert len(hd.thanh_toan) == 2


def test_tra_vuot_so_phai_tra_bi_tu_choi(db, nen):
    """TC-072 — ca biên."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    with pytest.raises(LoiNghiepVu) as loi:
        nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("150001"))

    assert "còn nợ" in str(loi.value).lower()
    assert hd.status == "unpaid"
    assert hd.thanh_toan == []


def test_tra_dung_bang_so_con_no_thi_duoc_chap_nhan(db, nen):
    """TC-072 — mép trên của khoảng hợp lệ, đúng chỗ hay bị lệch một đơn vị."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("120000"))

    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("30000"))

    assert hd.status == "paid"
    assert hd.con_no == Decimal("0")


def test_hai_lan_thu_chong_nhau_khong_vuot_so_con_no(db, nen):
    """Lỗi H-01 tìm được khi rà 19/09: hai máy thu cùng lúc → nợ âm, doanh thu đội lên.

    Dựng đúng thứ tự đã gây lỗi: lần thu thứ hai ĐỌC hóa đơn trước khi lần thứ nhất commit,
    rồi mới ghi. Session thứ hai là một request khác, không phải mock.
    """
    from sqlalchemy.orm import Session

    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    may_hai = Session(bind=db.get_bind())
    try:
        # Giữ tham chiếu như một request đang chạy dở giữ hóa đơn nó vừa đọc. Không giữ thì
        # identity map bỏ đối tượng cũ, lần đọc sau lấy số mới và test xanh giả — đã gặp.
        da_doc = nv.lay_hoa_don(may_hai, hd.id)
        assert da_doc.con_no == GIA_GOC  # máy hai đã đọc số cũ

        nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("100000"))  # máy một thu và commit

        with pytest.raises(LoiNghiepVu, match="còn nợ"):
            nv.ghi_nhan_thanh_toan(may_hai, hd.id, Decimal("100000"))
    finally:
        may_hai.close()

    db.refresh(hd)
    assert hd.da_tra == Decimal("100000")
    assert hd.con_no == Decimal("50000")


def test_hai_may_thu_that_su_dong_thoi_khong_vuot_so_con_no(tmp_path, frozen_clock):
    """H-01 với hai luồng thật trên CSDL file — test trên chỉ chạy tuần tự.

    Test tuần tự vẫn xanh nếu bỏ câu UPDATE giành khóa và chỉ giữ `refresh`: đọc lại xong
    vẫn có thể bị lần thu kia chen vào trước khi ghi. Ở đây máy một đã ghi nhưng giữ
    transaction mở 0,5 giây trước khi commit; máy hai thu đúng lúc đó.
    """
    import threading
    import time

    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401 — đăng ký mọi bảng trước create_all
    from app.db import Base

    engine = create_engine(
        f"sqlite:///{tmp_path / 'dong_thoi.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Phien = sessionmaker(bind=engine, autoflush=False)

    with Phien() as s:
        nen = _dung_nen(s)
        hd_id = nv.lap_hoa_don(s, lich_xong(s, nen).id).id

    may_mot, may_hai = Phien(), Phien()
    mot_da_ghi = threading.Event()

    @event.listens_for(may_mot, "before_commit")
    def _giu_transaction_mo(session):
        mot_da_ghi.set()
        time.sleep(0.5)

    ket_qua: dict[str, object] = {}

    def thu(ten, phien, cho=None):
        if cho is not None:
            cho.wait(5)
        try:
            nv.ghi_nhan_thanh_toan(phien, hd_id, Decimal("100000"))
            ket_qua[ten] = "thu được"
        except LoiNghiepVu as loi:
            ket_qua[ten] = str(loi)

    luong = [
        threading.Thread(target=thu, args=("mot", may_mot)),
        threading.Thread(target=thu, args=("hai", may_hai, mot_da_ghi)),
    ]
    try:
        for t in luong:
            t.start()
        for t in luong:
            t.join(15)

        assert ket_qua["mot"] == "thu được"
        assert "còn nợ" in ket_qua["hai"]
        with Phien() as s:
            assert nv.lay_hoa_don(s, hd_id).da_tra == Decimal("100000")
    finally:
        may_mot.close()
        may_hai.close()
        engine.dispose()


@pytest.mark.parametrize("so_tien", [Decimal("0"), Decimal("-1000")])
def test_so_tien_khong_duong_bi_tu_choi(db, nen, so_tien):
    """TC-073."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    with pytest.raises(LoiNghiepVu):
        nv.ghi_nhan_thanh_toan(db, hd.id, so_tien)

    assert hd.thanh_toan == []


def test_thieu_so_tien_bi_tu_choi(db, nen):
    """Ô trống trên form về tới đây là None, không phải 0."""
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    with pytest.raises(LoiNghiepVu):
        nv.ghi_nhan_thanh_toan(db, hd.id, None)


def test_hinh_thuc_thanh_toan_la_chuoi_la_bi_tu_choi(db, nen):
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    with pytest.raises(LoiNghiepVu):
        nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("1000"), hinh_thuc="bitcoin")


def test_khong_thu_tien_duoc_tren_hoa_don_da_huy(db, nen):
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    nv.huy_hoa_don(db, hd.id)

    with pytest.raises(LoiNghiepVu):
        nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("1000"))


# --- Hủy hóa đơn -----------------------------------------------------------------


def test_huy_hoa_don_chua_thu_dong_nao(db, nen):
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    nv.huy_hoa_don(db, hd.id)

    assert hd.status == "cancelled"


def test_huy_hoa_don_da_co_thanh_toan_bi_chan(db, nen):
    """Ca biên giữ cho `cancelled` và ba trạng thái tiền loại trừ nhau.

    Nếu chỗ này lọt, sẽ tồn tại hóa đơn vừa `cancelled` vừa có tiền, và không ai trả lời
    được câu "hóa đơn này thu được bao nhiêu" — cột lưu nói một đằng, payments nói một nẻo.
    """
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("50000"))

    with pytest.raises(LoiNghiepVu) as loi:
        nv.huy_hoa_don(db, hd.id)

    assert "thanh toán" in str(loi.value).lower()
    assert hd.status == "partial"


def test_hoa_don_da_huy_thi_so_no_ve_khong(db, nen):
    """Hóa đơn đã hủy không còn nợ ai đồng nào.

    Để nguyên `con_no` bằng tổng tiền thì màn hình danh sách hiện "còn nợ 150.000đ" trên
    một hóa đơn đã bỏ — con số đó sẽ bị đi đòi, và ở P6 nó sẽ chui vào báo cáo công nợ.
    """
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)

    nv.huy_hoa_don(db, hd.id)

    assert hd.con_no == Decimal("0")
    assert hd.total_amount == GIA_GOC  # số tiền gốc vẫn tra cứu được


def test_huy_hoa_don_lan_hai_bi_chan(db, nen):
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    nv.huy_hoa_don(db, hd.id)

    with pytest.raises(LoiNghiepVu):
        nv.huy_hoa_don(db, hd.id)


def test_lap_lai_hoa_don_da_huy_thi_mo_lai_chinh_hoa_don_do(db, nen):
    """Lỗ hổng S3 (kế hoạch P7 chặng 0) — thay giới hạn "một hóa đơn trọn đời" của P5.

    `appointment_id` là UNIQUE, nên trước đây hủy nhầm là buổi đó mất hẳn hóa đơn. Lối lách
    từng được gợi ý — đặt một lịch mới — không đi được: lịch không đặt vào quá khứ, và nếu
    đặt được thì thống kê đếm dôi một lượt. Hóa đơn đã hủy luôn chưa có đồng nào
    (`huy_hoa_don` chặn khi đã thu), nên mở lại chính nó là an toàn và giữ nguyên UNIQUE.
    """
    lich = lich_xong(db, nen)
    hd = nv.lap_hoa_don(db, lich.id)
    nv.huy_hoa_don(db, hd.id)

    lai = nv.lap_hoa_don(db, lich.id)

    assert lai.id == hd.id
    assert lai.status == "unpaid"
    assert lai.status == nv.trang_thai_tinh_lai(lai)
    assert lai.con_no == GIA_GOC
    assert db.query(Invoice).count() == 1


def test_lap_lai_hoa_don_da_huy_chep_gia_va_ngay_lap_moi(db, nen):
    """Biên của ca trên: hóa đơn mở lại là hóa đơn lập HÔM NAY với giá HÔM NAY.

    Giữ giá cũ thì khách bị tính theo bảng giá đã bỏ; giữ ngày lập cũ thì số "chưa thu"
    của thống kê rơi vào kỳ đã qua.
    """
    lich = lich_xong(db, nen)
    hd = nv.lap_hoa_don(db, lich.id)
    nv.huy_hoa_don(db, hd.id)
    ngay_lap_cu = hd.issued_at
    nen["dv"].price = Decimal("180000")
    db.commit()

    with clock.freeze(datetime(2026, 3, 20, 10, 0)):
        lai = nv.lap_hoa_don(db, lich.id)

    assert [(d.unit_price, d.amount) for d in lai.dong] == [(Decimal("180000"), Decimal("180000"))]
    assert lai.total_amount == Decimal("180000")
    assert lai.issued_at == datetime(2026, 3, 20, 10, 0) != ngay_lap_cu


def test_lap_lai_hoa_don_khi_hoa_don_cu_con_hieu_luc_khong_bay_dat_lich_moi(db, nen):
    """Ca biên của test trên: hóa đơn cũ CHƯA hủy thì bước tiếp theo khác hẳn.

    Ở đây hóa đơn cũ vẫn dùng được — việc phải làm là mở nó ra, không phải đặt lịch mới.
    Bày nhầm câu đó sẽ đẻ ra lịch rác. Test này giữ cho lời khuyên bám theo trạng thái
    hóa đơn chứ không nói bừa một câu cho cả hai ca.
    """
    lich = lich_xong(db, nen)
    hd = nv.lap_hoa_don(db, lich.id)

    with pytest.raises(LoiNghiepVu) as loi:
        nv.lap_hoa_don(db, lich.id)

    assert f"#{hd.id}" in str(loi.value)
    assert "đặt một lịch mới" not in str(loi.value)


# --- Truy vấn --------------------------------------------------------------------


def test_danh_sach_dua_hoa_don_chua_thu_len_dau(db, nen):
    xong1 = lich_xong(db, nen, gio(9))
    xong2 = lich_xong(db, nen, gio(11))
    da_thu = nv.lap_hoa_don(db, xong1.id)
    nv.ghi_nhan_thanh_toan(db, da_thu.id, GIA_GOC)
    chua_thu = nv.lap_hoa_don(db, xong2.id)

    ds = nv.danh_sach(db)

    assert [hd.id for hd in ds] == [chua_thu.id, da_thu.id]


def test_danh_sach_rong_khi_chua_co_hoa_don_nao(db, nen):
    assert nv.danh_sach(db) == []


def test_lay_hoa_don_khong_ton_tai_bao_loi_nghiep_vu(db, nen):
    """Ca biên: đọc thẳng /invoices/999 phải ra thông báo tiếng Việt, không phải 500."""
    with pytest.raises(LoiNghiepVu):
        nv.lay_hoa_don(db, 999)


def test_lay_hoa_don_tra_ve_du_dong_va_lich_su_thanh_toan(db, nen):
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    nv.ghi_nhan_thanh_toan(db, hd.id, Decimal("50000"))
    db.expire_all()

    lai = nv.lay_hoa_don(db, hd.id)

    assert len(lai.dong) == 1
    assert len(lai.thanh_toan) == 1
    assert lai.thanh_toan[0].amount == Decimal("50000")


def test_hoa_don_theo_lich_chi_tra_ve_lich_da_co_hoa_don(db, nen):
    """Lưới lịch hẹn dựa vào đúng dict này để chọn hiện nút nào."""
    co = lich_xong(db, nen, gio(9))
    chua = lich_xong(db, nen, gio(11))
    hd = nv.lap_hoa_don(db, co.id)

    bang = nv.hoa_don_theo_lich(db, [co.id, chua.id])

    assert bang[co.id].id == hd.id
    assert chua.id not in bang


def test_hoa_don_theo_lich_voi_danh_sach_rong(db, nen):
    """Ca biên: lưới ngày không có lịch nào — không được ném lỗi, không truy vấn thừa."""
    assert nv.hoa_don_theo_lich(db, []) == {}


def test_trang_thai_tinh_lai_cua_hoa_don_da_huy_van_la_da_huy(db, nen):
    """Ca biên của `trang_thai_tinh_lai`: `cancelled` không suy được từ payments.

    Hàm phải trả lại đúng `cancelled` chứ không "sửa" nó thành `unpaid`.
    """
    hd = nv.lap_hoa_don(db, lich_xong(db, nen).id)
    nv.huy_hoa_don(db, hd.id)

    assert nv.trang_thai_tinh_lai(hd) == "cancelled"
