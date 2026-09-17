"""Test cho app/ai/quota.py — xoay ca model và ước tính quota.

TC-103 → TC-112 (mã mới của P7, xem docs/testing/test-cases.md).

Mọi ca dùng `FakeProvider` cài lỗi **theo từng model**, nên luật xoay được kiểm bằng chính
provider của tầng test chứ không phải bằng cách mock hàm đang kiểm (CLAUDE.md mục 7 luật 1).

Bốn model trong cấu hình test cố định để thứ tự ưu tiên kiểm được:
`m1 → m2 → m3 → m4`.
"""

from datetime import datetime, timedelta

import pytest

from app.ai import quota as nv
from app.ai.fake import FakeProvider
from app.ai.provider import (
    LoiAI,
    LoiCauHinh,
    LoiHetQuota,
    LoiModelKhongCo,
    LoiQuaTai,
)
from app.config import settings
from app.models.ai_quota import AiQuota
from app.services import clock

BAY_GIO = datetime(2026, 3, 12, 8, 0)  # = MOC_THOI_GIAN của conftest


@pytest.fixture
def bon_model(monkeypatch):
    monkeypatch.setattr(settings, "gemini_models", "m1,m2,m3,m4")
    monkeypatch.setattr(settings, "gemini_rpd_uoc_tinh", 20)
    return ["m1", "m2", "m3", "m4"]


def goi(db, provider, **kw):
    return nv.goi_co_xoay(db, provider, system="S", user="U", **kw)


# --- Ngày quota theo giờ Pacific ---------------------------------------------------


def test_ngay_quota_doi_luc_14h_gio_viet_nam_vao_mua_he_my():
    """Mùa hè bên Mỹ (PDT, UTC-7): 00:00 Pacific = 14:00 giờ Việt Nam.

    Tính bằng ZoneInfo chứ không cộng trừ số giờ cố định — lệch giờ mùa hè đổi hai lần mỗi năm.
    """
    assert nv.ngay_quota(datetime(2026, 7, 1, 13, 59)).isoformat() == "2026-06-30"
    assert nv.ngay_quota(datetime(2026, 7, 1, 14, 0)).isoformat() == "2026-07-01"


def test_ngay_quota_doi_luc_15h_gio_viet_nam_vao_mua_dong_my():
    """Mùa đông (PST, UTC-8): mốc lùi thành 15:00 giờ Việt Nam."""
    assert nv.ngay_quota(datetime(2026, 1, 15, 14, 59)).isoformat() == "2026-01-14"
    assert nv.ngay_quota(datetime(2026, 1, 15, 15, 0)).isoformat() == "2026-01-15"


def test_moc_reset_ke_tiep_luon_o_tuong_lai_va_theo_gio_viet_nam(frozen_clock):
    moc = nv.moc_reset_ke_tiep()

    assert moc > BAY_GIO
    assert moc.hour in (14, 15) and moc.minute == 0


# --- Thứ tự ưu tiên ----------------------------------------------------------------


def test_luon_thu_model_dau_tien_khi_moi_model_deu_khoe(db, frozen_clock, bon_model):
    fake = FakeProvider(phan_hoi="xong")

    noi_dung, model = goi(db, fake)

    assert (noi_dung, model) == ("xong", "m1")
    assert fake.cac_model_da_thu == ["m1"]


def test_model_dau_qua_tai_thi_xoay_sang_model_ke(db, frozen_clock, bon_model):
    """503 đã xảy ra thật khi gọi thử ngày 17/09, không phải ca giả định."""
    fake = FakeProvider(loi_theo_model={"m1": LoiQuaTai("quá tải")})

    _, model = goi(db, fake)

    assert model == "m2"
    assert fake.cac_model_da_thu == ["m1", "m2"]


def test_model_qua_tai_duoc_cho_nghi_roi_quay_lai_khi_het_gio_nghi(db, frozen_clock, bon_model):
    """Ưu tiên theo thứ tự (quyết định Q4): hết giờ nghỉ thì lại thử model tốt nhất trước."""
    fake = FakeProvider(loi_theo_model={"m1": [LoiQuaTai("quá tải")]})
    goi(db, fake)

    with clock.freeze(BAY_GIO + timedelta(seconds=30)):
        assert goi(db, fake)[1] == "m2", "còn trong giờ nghỉ mà đã quay lại m1"

    with clock.freeze(BAY_GIO + timedelta(seconds=settings.ai_nghi_giay + 1)):
        assert goi(db, fake)[1] == "m1"


def test_het_quota_theo_ngay_thi_bo_model_ca_ngay_va_ghi_gioi_han_that(db, frozen_clock, bon_model):
    fake = FakeProvider(
        loi_theo_model={"m1": LoiHetQuota("hết lượt", theo_ngay=True, gioi_han=20)}
    )

    goi(db, fake)

    dong = db.query(AiQuota).filter_by(model="m1").one()
    assert dong.exhausted is True
    assert dong.daily_limit == 20
    # Hết giờ nghỉ cũng không quay lại: đây là hạn mức ngày, không phải nhất thời.
    with clock.freeze(BAY_GIO + timedelta(hours=3)):
        assert nv.chon_thu_tu(db) == ["m2", "m3", "m4"]


def test_het_quota_theo_phut_chi_nghi_dung_thoi_gian_google_bao(db, frozen_clock, bon_model):
    """Phân biệt hai loại 429. Coi nhầm 429/phút là 429/ngày thì bỏ oan model tới nửa đêm."""
    fake = FakeProvider(
        loi_theo_model={"m1": [LoiHetQuota("chờ chút", theo_ngay=False, thu_lai_sau=30)]}
    )

    goi(db, fake)

    dong = db.query(AiQuota).filter_by(model="m1").one()
    assert dong.exhausted is False
    assert dong.cooldown_until == BAY_GIO + timedelta(seconds=30)
    with clock.freeze(BAY_GIO + timedelta(seconds=31)):
        assert goi(db, fake)[1] == "m1"


def test_model_bi_google_tat_thi_loai_han_khong_thu_lai_ngay_hom_sau(db, frozen_clock, bon_model):
    """404 — đã gặp thật với `gemini-2.5-flash` ngày 17/09."""
    fake = FakeProvider(loi_theo_model={"m1": LoiModelKhongCo("no longer available")})

    goi(db, fake)

    assert nv.chon_thu_tu(db) == ["m2", "m3", "m4"]
    with clock.freeze(BAY_GIO + timedelta(days=1)):
        assert "m1" not in nv.chon_thu_tu(db)


def test_khoa_api_sai_thi_dung_ngay_khong_thu_model_khac(db, frozen_clock, bon_model):
    """Đổi model không cứu được khóa sai — thử tiếp chỉ tốn thời gian của người đang đợi."""
    fake = FakeProvider(loi_chung=LoiCauHinh("API key not valid"))

    with pytest.raises(LoiCauHinh):
        goi(db, fake)

    assert fake.cac_model_da_thu == ["m1"]


def test_het_sach_model_thi_bao_loi_tieng_viet_khong_vo_trang(db, frozen_clock, bon_model):
    fake = FakeProvider(loi_chung=LoiQuaTai("quá tải"))

    with pytest.raises(LoiAI, match="hết lượt miễn phí hôm nay"):
        goi(db, fake)

    assert fake.cac_model_da_thu == ["m1", "m2", "m3", "m4"]


def test_model_cham_muc_uoc_tinh_bi_day_xuong_cuoi_nhung_van_duoc_thu(db, frozen_clock, bon_model):
    """Ước tính có thể sai, nên đừng bỏ hẳn: chỉ nhường chỗ cho model chắc chắn còn lượt."""
    for _ in range(settings.gemini_rpd_uoc_tinh):
        nv.ghi_lan_goi(db, "m1")

    assert nv.chon_thu_tu(db) == ["m2", "m3", "m4", "m1"]


def test_gioi_han_that_da_dung_het_thi_khong_thu_nua(db, frozen_clock, bon_model):
    """Khác ca trên: số do Google báo thì cố gọi chỉ chắc chắn ăn thêm một lỗi 429."""
    nv.ghi_het_quota(db, "m1", LoiHetQuota("hết", theo_ngay=True, gioi_han=20))

    with clock.freeze(BAY_GIO + timedelta(days=1)):
        for _ in range(20):
            nv.ghi_lan_goi(db, "m1")

        assert "m1" not in nv.chon_thu_tu(db)


def test_ghim_model_thi_khong_xoay_sang_model_khac(db, frozen_clock, bon_model):
    """Dùng khi chạy bộ ca guardrail: báo cáo phải nói rõ model nào trả lời câu nào."""
    fake = FakeProvider(loi_theo_model={"m2": LoiQuaTai("quá tải")})

    assert goi(db, fake, ghim_model="m3")[1] == "m3"

    with pytest.raises(LoiAI):
        goi(db, fake, ghim_model="m2")
    assert fake.cac_model_da_thu == ["m3", "m2"]


def test_ghim_model_khong_co_trong_cau_hinh_thi_bao_loi(db, frozen_clock, bon_model):
    with pytest.raises(LoiAI, match="không có trong GEMINI_MODELS"):
        goi(db, FakeProvider(), ghim_model="model-la")


def test_ngan_sach_thoi_gian_cat_chuoi_thu_khong_de_treo_trang(db, frozen_clock, bon_model, monkeypatch):
    """Bốn model cùng quá hạn chờ thì tổng thời gian chờ phải có trần.

    Mỗi lần gọi làm đồng hồ nhảy 30 giây, ngân sách 45 giây → chỉ kịp hai model.
    """
    monkeypatch.setattr(settings, "ai_tong_giay", 45)
    dong_ho = {"luc": BAY_GIO}
    monkeypatch.setattr(clock, "now", lambda: dong_ho["luc"])

    class ChamChap(FakeProvider):
        def tra_loi(self, model, system, user, timeout):
            dong_ho["luc"] += timedelta(seconds=30)
            return super().tra_loi(model, system, user, timeout)

    fake = ChamChap(loi_chung=LoiQuaTai("quá hạn chờ"))

    with pytest.raises(LoiAI):
        goi(db, fake)

    assert fake.cac_model_da_thu == ["m1", "m2"]


def test_moi_lan_thu_khong_duoc_cho_lau_hon_thoi_gian_con_lai(db, frozen_clock, bon_model, monkeypatch):
    """Ca biên của ngân sách: lần thử cuối chỉ được phần thời gian còn lại."""
    monkeypatch.setattr(settings, "ai_tong_giay", 10)
    monkeypatch.setattr(settings, "ai_moi_lan_giay", 25)
    fake = FakeProvider()

    goi(db, fake)

    assert fake.da_goi[0].model == "m1"


# --- Đếm lượt ----------------------------------------------------------------------


def test_goi_thanh_cong_tinh_mot_luot(db, frozen_clock, bon_model):
    goi(db, FakeProvider())

    assert db.query(AiQuota).filter_by(model="m1").one().request_count == 1


def test_qua_tai_van_tinh_luot_nhung_429_va_404_thi_khong(db, frozen_clock, bon_model):
    """Lời gọi 503 đã tới server nên nhiều khả năng vẫn bị tính; 429 và 404 thì chắc chắn không."""
    fake = FakeProvider(
        loi_theo_model={
            "m1": LoiQuaTai("quá tải"),
            "m2": LoiHetQuota("hết lượt", theo_ngay=True),
            "m3": LoiModelKhongCo("đã tắt"),
        }
    )

    goi(db, fake)

    dem = {d.model: d.request_count for d in db.query(AiQuota).all()}
    assert dem["m1"] == 1
    assert dem["m2"] == 0
    assert dem["m3"] == 0
    assert dem["m4"] == 1  # model trả lời được


# --- Bảng hiển thị và đặt lại -------------------------------------------------------


def test_bang_quota_danh_dau_model_dang_dung_va_phan_biet_so_that_voi_uoc_tinh(db, frozen_clock, bon_model):
    nv.ghi_lan_goi(db, "m1")
    nv.ghi_het_quota(db, "m2", LoiHetQuota("hết", theo_ngay=True, gioi_han=15))

    bang = {d.model: d for d in nv.bang_quota(db)}

    assert (bang["m1"].da_dung, bang["m1"].gioi_han, bang["m1"].gioi_han_that) == (1, 20, False)
    assert (bang["m2"].gioi_han, bang["m2"].gioi_han_that) == (15, True)
    assert bang["m2"].trang_thai == "hết lượt hôm nay"
    assert bang["m1"].dang_dung is True
    assert [d.dang_dung for d in nv.bang_quota(db)].count(True) == 1


def test_dong_bang_quota_in_ra_dung_mau_nguoi_dung_yeu_cau(db, frozen_clock, bon_model):
    """Mẫu đã chốt: `▸ model: đã dùng/~ước tính ⬅️ đang dùng`, số thật thì không có dấu ~."""
    nv.ghi_lan_goi(db, "m1")

    dong = nv.bang_quota(db)[0]

    assert str(dong) == "▸ m1: 1/~20 ⬅️ đang dùng"


def test_dat_lai_xoa_trang_thai_chan_nhung_giu_so_luot_da_dem(db, frozen_clock, bon_model):
    """Đặt lại là để sửa phán đoán sai của hệ thống, không phải để làm đẹp con số."""
    nv.ghi_lan_goi(db, "m1")
    nv.ghi_het_quota(db, "m1", LoiHetQuota("hết", theo_ngay=True))
    nv.ghi_model_khong_co(db, "m2", "đã tắt")
    nv.ghi_qua_tai(db, "m3")

    nv.dat_lai(db)

    assert nv.chon_thu_tu(db) == ["m1", "m2", "m3", "m4"]
    assert db.query(AiQuota).filter_by(model="m1").one().request_count == 1


def test_gioi_han_tra_ve_so_uoc_tinh_cho_toi_khi_google_bao_so_that(db, frozen_clock, bon_model):
    """Dấu `~` trên màn hình sinh ra từ đúng cờ thứ hai của hàm này."""
    assert nv.gioi_han(db, "m1") == (settings.gemini_rpd_uoc_tinh, False)

    nv.ghi_het_quota(db, "m1", LoiHetQuota("hết", theo_ngay=True, gioi_han=15))

    assert nv.gioi_han(db, "m1") == (15, True)


def test_gioi_han_that_hoc_hom_qua_van_dung_cho_hom_nay(db, frozen_clock, bon_model):
    """Hạn mức không đổi theo ngày, nên học một lần là dùng mãi — biên của ca trên."""
    nv.ghi_het_quota(db, "m1", LoiHetQuota("hết", theo_ngay=True, gioi_han=15))

    with clock.freeze(BAY_GIO + timedelta(days=1)):
        assert nv.gioi_han(db, "m1") == (15, True)
