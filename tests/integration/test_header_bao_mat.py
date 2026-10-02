"""R-4 (rà soát 02/10): không trang nào gửi header chống nhúng khung, chống đoán kiểu nội dung hay
giới hạn Referer. Trang công khai mà thiếu `X-Frame-Options` thì có thể bị nhúng vào trang lạ rồi lừa
người dùng bấm nút ẩn dưới lớp phủ (clickjacking).

Header phải có trên MỌI phản hồi: trang thường, tệp tĩnh, trang lỗi và cả phản hồi bị chặn bởi middleware
khác (403 cross-origin).
"""

import pytest

HEADER_BAT_BUOC = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}


def kiem(r):
    for ten, gia_tri in HEADER_BAT_BUOC.items():
        assert r.headers.get(ten) == gia_tri, f"{ten}: {r.headers.get(ten)!r}"


@pytest.mark.parametrize("duong_dan", ["/login", "/static/style.css", "/khong-co-trang-nay"])
def test_moi_loai_phan_hoi_get_deu_co_header_bao_mat(client, seed_basic, duong_dan):
    kiem(client.get(duong_dan, follow_redirects=False))


def test_phan_hoi_chuyen_huong_sau_dang_nhap_co_header_bao_mat(client, seed_basic):
    r = client.post("/login", data={"username": "letan", "password": "matkhau123"}, follow_redirects=False)

    assert r.status_code == 303
    kiem(r)


def test_phan_hoi_403_do_chan_cheo_nguon_cung_co_header_bao_mat(client, seed_basic):
    r = client.post("/login", data={"username": "letan", "password": "x"}, headers={"Origin": "https://evil.com"})

    assert r.status_code == 403
    kiem(r)
