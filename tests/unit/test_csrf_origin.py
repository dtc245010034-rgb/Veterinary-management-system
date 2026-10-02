"""Chặn POST từ trang web khác (R-2, rà soát 02/10): ứng dụng không có token CSRF, chỉ dựa vào
`SameSite=Lax` của cookie — không đủ khi ứng dụng công khai ra Internet.

Luật: POST/PUT/PATCH/DELETE bị từ chối nếu trình duyệt tự khai nó đến từ chỗ khác — `Origin` không cùng
host với `Host`, hoặc `Sec-Fetch-Site` khác `same-origin`/`none`. Không có cả hai header (curl, TestClient,
script) thì cho qua: CSRF là tấn công BẰNG TRÌNH DUYỆT, mà trình duyệt thì luôn gửi ít nhất một trong hai.
"""

import pytest

from app.security import la_post_cheo_nguon


@pytest.mark.parametrize(
    "origin, site, host",
    [
        ("http://127.0.0.1:8000", "same-origin", "127.0.0.1:8000"),
        ("http://127.0.0.1:8000", None, "127.0.0.1:8000"),
        (None, "same-origin", "127.0.0.1:8000"),
        (None, "none", "127.0.0.1:8000"),
        (None, None, "127.0.0.1:8000"),  # curl / TestClient
        ("https://abc.ngrok.app", "same-origin", "abc.ngrok.app"),
    ],
)
def test_yeu_cau_cung_nguon_hoac_khong_phai_trinh_duyet_duoc_qua(origin, site, host):
    assert la_post_cheo_nguon("POST", origin, site, host) is False


@pytest.mark.parametrize(
    "origin, site",
    [
        ("https://evil.com", None),
        ("https://evil.com", "cross-site"),
        ("null", None),  # iframe sandbox hoặc chuyển hướng ẩn danh: không tin
        (None, "cross-site"),
        (None, "same-site"),  # tên miền anh em hoặc cổng khác trên cùng máy
        ("http://127.0.0.1:9999", None),  # cùng IP khác cổng
        ("http://127.0.0.1:8000.evil.com", None),  # đuôi giống nhưng khác host
    ],
)
def test_yeu_cau_tu_trang_khac_bi_chan(origin, site):
    assert la_post_cheo_nguon("POST", origin, site, "127.0.0.1:8000") is True


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_phuong_thuc_doc_khong_bi_kiem(method):
    assert la_post_cheo_nguon(method, "https://evil.com", "cross-site", "127.0.0.1:8000") is False


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "post"])
def test_moi_phuong_thuc_ghi_deu_bi_kiem(method):
    assert la_post_cheo_nguon(method, "https://evil.com", None, "127.0.0.1:8000") is True


# --- APP_ORIGIN: địa chỉ công khai khi đứng sau tunnel/proxy đổi Host ---------------------


@pytest.mark.parametrize("origin_tin_cay", ["https://abc.ngrok.app", "https://abc.ngrok.app/"])
def test_origin_trung_app_origin_duoc_qua_du_host_nhan_duoc_khac(origin_tin_cay):
    # Tunnel chuyển yêu cầu vào máy với Host nội bộ; trình duyệt vẫn gửi Origin là địa chỉ công khai.
    assert la_post_cheo_nguon("POST", "https://abc.ngrok.app", None, "127.0.0.1:8000", origin_tin_cay) is False


def test_origin_khac_app_origin_van_bi_chan():
    assert la_post_cheo_nguon("POST", "https://evil.com", None, "127.0.0.1:8000", "https://abc.ngrok.app") is True


def test_app_origin_rong_khong_mo_cua_cho_origin_rong_hay_null():
    assert la_post_cheo_nguon("POST", "null", None, "127.0.0.1:8000", "") is True


def test_app_origin_khong_cuu_duoc_yeu_cau_co_sec_fetch_site_cross_site():
    assert la_post_cheo_nguon("POST", "https://abc.ngrok.app", "cross-site", "127.0.0.1:8000", "https://abc.ngrok.app") is True


def test_origin_rong_khong_khop_app_origin_rong():
    # Header `Origin:` có mặt nhưng rỗng không phải "thiếu header": nếu coi "" == "" là khớp thì
    # APP_ORIGIN chưa đặt sẽ mở cửa cho đúng kiểu yêu cầu này.
    assert la_post_cheo_nguon("POST", "", None, "127.0.0.1:8000", "") is True
