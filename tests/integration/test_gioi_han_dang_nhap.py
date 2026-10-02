"""Giới hạn đăng nhập sai qua HTTP (R-1, rà soát 02/10).

Tái hiện lỗi: 30 lần POST /login sai liên tiếp đều trả 401, rồi đăng nhập đúng vẫn qua.
Bộ đếm là trạng thái toàn cục của tiến trình, nên fixture autouse trong conftest xóa nó trước mỗi test.
"""

from datetime import datetime, timedelta

from app.services import clock
from app.services.login_throttle import KHOA_DAU_GIAY, MIEN_PHI

T0 = datetime(2026, 10, 2, 9, 0, 0)


def thu(client, username="letan", password="sai-mat-khau"):
    return client.post("/login", data={"username": username, "password": password})


def test_sai_lien_tuc_den_nguong_thi_lan_tiep_theo_bi_429(client, seed_basic):
    with clock.freeze(T0):
        for _ in range(MIEN_PHI):
            assert thu(client).status_code == 401

        r = thu(client)

    assert r.status_code == 429
    assert "quá nhiều lần" in r.text
    assert r.headers["retry-after"] == str(KHOA_DAU_GIAY)


def test_dang_khoa_thi_mat_khau_DUNG_cung_bi_chan(client, seed_basic):
    # Nếu mật khẩu đúng được qua khi đang khóa thì khóa vô nghĩa: kẻ tấn công cứ thử tiếp.
    with clock.freeze(T0):
        for _ in range(MIEN_PHI):
            thu(client)

        r = thu(client, password=seed_basic["mat_khau"])

    assert r.status_code == 429
    assert "set-cookie" not in r.headers


def test_het_thoi_gian_khoa_thi_dang_nhap_dung_lai_duoc(client, seed_basic):
    with clock.freeze(T0):
        for _ in range(MIEN_PHI):
            thu(client)
    with clock.freeze(T0 + timedelta(seconds=KHOA_DAU_GIAY)):
        r = thu(client, password=seed_basic["mat_khau"])

    assert r.status_code == 200 or r.status_code == 303


def test_tai_khoan_khac_khong_bi_khoa_theo(client, seed_basic):
    with clock.freeze(T0):
        for _ in range(MIEN_PHI):
            thu(client, "letan")

        r = thu(client, "quanly", seed_basic["mat_khau"])

    assert r.status_code in (200, 303)


def test_dang_nhap_dung_giua_chung_xoa_bo_dem(client, seed_basic):
    with clock.freeze(T0):
        for _ in range(MIEN_PHI - 1):
            thu(client)
        assert thu(client, password=seed_basic["mat_khau"]).status_code in (200, 303)
        for _ in range(MIEN_PHI - 1):
            assert thu(client).status_code == 401


def test_ten_khong_ton_tai_cung_bi_dem_nhu_ten_that(client, seed_basic):
    # Nếu chỉ đếm tên có thật thì phản hồi 429 lộ tên nào tồn tại (TC-002).
    with clock.freeze(T0):
        for _ in range(MIEN_PHI):
            thu(client, "khong-co-nguoi-nay")

        r = thu(client, "khong-co-nguoi-nay")

    assert r.status_code == 429
