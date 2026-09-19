"""Mọi đường dẫn theo id gặp bản ghi không còn tồn tại phải ra trang lỗi, không phải 500.

Lỗi H-03 tìm được khi rà 19/09: 7 đường dẫn trả "Internal Server Error" khi id không tồn
tại — hai lễ tân cùng mở một thú cưng, người này xóa xong, người kia bấm "Xóa" trên trang
cũ. Đọc code thấy thêm hai chỗ cùng dạng mà lượt rà chưa chạm (`GET /owners/{id}`,
`/services/goi/{id}/ban-lai`). Quét hết thay vì chỉ các ca đã thấy — bài học 4 CLAUDE.md.
"""

import pytest
from fastapi.testclient import TestClient

KHONG_CO = 99999

DUONG_DAN = [
    ("GET", "/owners/{id}"),
    ("GET", "/owners/{id}/xoa"),
    ("GET", "/pets/{id}"),
    ("GET", "/pets/{id}/xoa"),
    ("GET", "/invoices/{id}"),
    ("GET", "/invoices/{id}/huy"),
    ("GET", "/appointments/{id}/ho-so"),
    ("GET", "/ai/ket-qua/{id}"),
    ("POST", "/owners/{id}/xoa"),
    ("POST", "/owners/{id}/pets"),
    ("POST", "/pets/{id}/xoa"),
    ("POST", "/pets/{id}/vaccinations"),
    ("POST", "/services/{id}/sua"),
    ("POST", "/services/{id}/ngung-ban"),
    ("POST", "/services/{id}/ban-lai"),
    ("POST", "/services/goi/{id}/ngung-ban"),
    ("POST", "/services/goi/{id}/ban-lai"),
    ("POST", "/appointments/{id}/doi"),
    ("POST", "/appointments/{id}/huy"),
    ("POST", "/appointments/{id}/hoa-don"),
    ("POST", "/appointments/{id}/ho-so"),
    ("POST", "/invoices/{id}/thanh-toan"),
    ("POST", "/invoices/{id}/huy"),
    ("POST", "/users/{id}/khoa"),
    ("POST", "/users/{id}/mo-khoa"),
    ("POST", "/ai/nhac-lich/lich-hen/{id}"),
    ("POST", "/ai/nhac-lich/tiem/{id}"),
    ("POST", "/ai/tom-tat/{id}"),
    ("POST", "/ai/ket-qua/{id}/chot"),
]


# Chín đường dẫn từng trả 500: không route nào bắt lỗi, nên trang lỗi chung phải nói đúng
# là "không tìm thấy" (404) chứ không phải "dữ liệu sai" (400).
TUNG_LOI_500 = [
    ("GET", "/owners/{id}"),
    ("GET", "/owners/{id}/xoa"),
    ("GET", "/pets/{id}/xoa"),
    ("POST", "/owners/{id}/pets"),
    ("POST", "/pets/{id}/xoa"),
    ("POST", "/services/{id}/ngung-ban"),
    ("POST", "/services/{id}/ban-lai"),
    ("POST", "/services/goi/{id}/ngung-ban"),
    ("POST", "/services/goi/{id}/ban-lai"),
]


@pytest.fixture
def quan_ly(client, seed_basic):
    """Quản lý vào được mọi chức năng, nên không đường dẫn nào bị chặn 403 trước khi tới
    chỗ tra id. Tắt raise_server_exceptions để thấy đúng mã 500 người dùng thấy."""
    c = TestClient(client.app, raise_server_exceptions=False)
    r = c.post("/login", data={"username": "quanly", "password": "matkhau123"})
    assert r.status_code == 200
    return c


@pytest.mark.parametrize("phuong_thuc, mau", DUONG_DAN, ids=[f"{p} {u}" for p, u in DUONG_DAN])
def test_id_khong_ton_tai_ra_trang_loi_khong_phai_500(quan_ly, phuong_thuc, mau):
    r = quan_ly.request(phuong_thuc, mau.format(id=KHONG_CO), follow_redirects=False)

    assert r.status_code in (400, 404), f"{phuong_thuc} {mau} → {r.status_code}"
    assert "Internal Server Error" not in r.text


@pytest.mark.parametrize("phuong_thuc, mau", TUNG_LOI_500, ids=[f"{p} {u}" for p, u in TUNG_LOI_500])
def test_ban_ghi_da_bi_xoa_ra_trang_404_noi_ro_khong_tim_thay(quan_ly, phuong_thuc, mau):
    r = quan_ly.request(phuong_thuc, mau.format(id=KHONG_CO), follow_redirects=False)

    assert r.status_code == 404
    assert "Không tìm thấy" in r.text
