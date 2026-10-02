"""Giới hạn đăng nhập sai (R-1, rà soát 02/10): 30 lần sai liên tiếp vẫn bị trả 401.

Khóa theo CẶP (IP, tên đăng nhập), không theo riêng tên đăng nhập: khóa theo tên thì kẻ lạ chỉ cần
gõ sai `quanly` vài lần là khóa được quản lý thật ra ngoài. Trễ tăng gấp đôi mỗi lần sai tiếp.

Thời gian là ranh giới ngoài duy nhất được thay thế (`clock.freeze`); chính lớp giới hạn thì dùng thật.
"""

from datetime import datetime, timedelta

from app.services import clock
from app.services.login_throttle import (
    KHOA_DAU_GIAY,
    KHOA_TOI_DA_GIAY,
    MIEN_PHI,
    GioiHanDangNhap,
    tao_khoa,
)

T0 = datetime(2026, 10, 2, 9, 0, 0)
K = tao_khoa("1.2.3.4", "letan")


def sai(gh, khoa, n, luc=T0):
    with clock.freeze(luc):
        for _ in range(n):
            gh.ghi_that_bai(khoa)


def cho(gh, khoa, luc):
    with clock.freeze(luc):
        return gh.con_phai_cho(khoa)


def test_chua_sai_lan_nao_thi_khong_phai_cho():
    assert cho(GioiHanDangNhap(), K, T0) == 0


def test_sai_duoi_nguong_mien_phi_van_duoc_thu_ngay():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI - 1)

    assert cho(gh, K, T0) == 0


def test_sai_dung_nguong_thi_bi_khoa_khoa_dau():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI)

    assert cho(gh, K, T0) == KHOA_DAU_GIAY


def test_het_khoa_dung_luc_va_con_lai_giam_dan():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI)

    assert cho(gh, K, T0 + timedelta(seconds=KHOA_DAU_GIAY - 1)) == 1
    assert cho(gh, K, T0 + timedelta(seconds=KHOA_DAU_GIAY)) == 0


def test_sai_tiep_sau_khi_het_khoa_thi_khoa_gap_doi():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI)
    lan_hai = T0 + timedelta(seconds=KHOA_DAU_GIAY)
    sai(gh, K, 1, lan_hai)

    assert cho(gh, K, lan_hai) == 2 * KHOA_DAU_GIAY


def test_khoa_khong_vuot_tran():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI + 40)

    assert cho(gh, K, T0) == KHOA_TOI_DA_GIAY


def test_thanh_cong_xoa_bo_dem():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI - 1)
    gh.xoa(K)
    sai(gh, K, MIEN_PHI - 1)

    assert cho(gh, K, T0) == 0


def test_nguoi_khac_hoac_ip_khac_khong_bi_anh_huong():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI)

    assert cho(gh, tao_khoa("1.2.3.4", "quanly"), T0) == 0
    assert cho(gh, tao_khoa("9.9.9.9", "letan"), T0) == 0


def test_ten_dang_nhap_khong_phan_biet_hoa_thuong_va_khoang_trang():
    # Nếu "Letan" và "letan" là hai khóa thì gõ đổi hoa-thường là né được giới hạn.
    gh = GioiHanDangNhap()
    sai(gh, tao_khoa("1.2.3.4", "Letan "), MIEN_PHI)

    assert cho(gh, tao_khoa("1.2.3.4", "letan"), T0) == KHOA_DAU_GIAY


def test_sai_rai_rac_qua_lau_khong_cong_don():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI - 1)
    sau_hai_gio = T0 + timedelta(hours=2)
    sai(gh, K, 1, sau_hai_gio)

    assert cho(gh, K, sau_hai_gio) == 0


def test_thu_trong_luc_dang_khoa_khong_keo_dai_khoa():
    # Kẻ tấn công không được giữ nạn nhân bị khóa mãi bằng cách bấm liên tục.
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI)
    giua = T0 + timedelta(seconds=10)
    with clock.freeze(giua):
        gh.con_phai_cho(K)
        gh.con_phai_cho(K)

    assert cho(gh, K, T0 + timedelta(seconds=KHOA_DAU_GIAY)) == 0


def test_reset_xoa_het():
    gh = GioiHanDangNhap()
    sai(gh, K, MIEN_PHI)
    gh.reset()

    assert cho(gh, K, T0) == 0


def test_don_dep_bo_muc_cu_khi_bang_qua_lon(monkeypatch):
    import app.services.login_throttle as lt

    monkeypatch.setattr(lt, "TOI_DA_MUC_NHO", 3)
    gh = GioiHanDangNhap()
    for i in range(3):
        sai(gh, tao_khoa("1.1.1.1", f"u{i}"), 1)
    sau_hai_gio = T0 + timedelta(hours=2)
    sai(gh, K, 1, sau_hai_gio)

    assert list(gh._muc) == [K]
