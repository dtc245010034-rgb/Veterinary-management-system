"""Test đăng nhập qua HTTP.

Phục vụ US-01: TC-001 (đăng nhập đúng), TC-002 (sai mật khẩu không lộ thông tin),
TC-003 (tài khoản bị khóa), TC-004 (chưa đăng nhập bị chuyển về trang đăng nhập).
"""

import pytest

from app.models.user import User
from app.security import hash_password


def test_dang_nhap_dung_mat_khau_vao_duoc_he_thong(client, seed_basic):
    """TC-001."""
    r = client.post(
        "/login",
        data={"username": "letan", "password": "matkhau123"},
        follow_redirects=True,
    )

    assert r.status_code == 200
    assert "Tran Thi Le" in r.text


def test_sai_mat_khau_bi_tu_choi(client, seed_basic):
    """TC-002, phần một: sai mật khẩu thì không vào được."""
    r = client.post("/login", data={"username": "letan", "password": "sai-mat-khau"})

    assert r.status_code == 401
    assert "Tên đăng nhập hoặc mật khẩu không đúng" in r.text


def test_bao_loi_giong_het_nhau_du_tai_khoan_co_ton_tai_hay_khong(client, seed_basic):
    """TC-002, phần hai: không được tiết lộ tài khoản có tồn tại hay không.

    Nếu hai trường hợp trả về thông báo khác nhau, kẻ tấn công dò được danh sách tên
    đăng nhập hợp lệ chỉ bằng cách thử và so sánh phản hồi.

    Từ 24/09 trang đăng nhập giữ lại tên đã gõ (L-07), nên hai phản hồi không còn giống
    nhau **từng byte** được nữa — chúng khác đúng ở chuỗi mà chính kẻ tấn công vừa gõ
    vào. Đó không phải rò rỉ: nó không nói gì về việc tài khoản có tồn tại hay không.
    Nên phép so bỏ phần echo đó ra rồi mới so; mọi khác biệt còn lại vẫn là lỗi.
    """
    r_co_that = client.post("/login", data={"username": "letan", "password": "sai"})
    r_khong_co = client.post("/login", data={"username": "khong-ton-tai", "password": "sai"})

    assert r_co_that.status_code == r_khong_co.status_code

    # Thay chính chuỗi đã gõ bằng một chỗ giữ chỗ chung, rồi so phần còn lại.
    a = r_co_that.text.replace("letan", "___")
    b = r_khong_co.text.replace("khong-ton-tai", "___")
    assert a == b

    # Và phép so trên phải thật sự nhìn thấy khác biệt nếu có: nếu bỏ echo ra mà hai
    # trang vẫn khác nhau thì `a == b` đã đỏ. Kiểm thêm rằng chuỗi echo đúng là thứ duy
    # nhất khác — nếu không, phép chuẩn hóa ở trên đang giấu một rò rỉ thật.
    assert r_co_that.text != r_khong_co.text
    assert 'value="letan"' in r_co_that.text


def test_tai_khoan_bi_khoa_khong_dang_nhap_duoc(client, db):
    """TC-003: đúng mật khẩu nhưng tài khoản đã ngưng hoạt động thì vẫn bị từ chối."""
    db.add(
        User(
            username="danghi",
            password_hash=hash_password("matkhau123"),
            full_name="Nguoi Da Nghi",
            role="caretaker",
            is_active=False,
        )
    )
    db.commit()

    r = client.post("/login", data={"username": "danghi", "password": "matkhau123"})

    assert r.status_code == 401
    assert "ngưng hoạt động" in r.text


def test_chua_dang_nhap_bi_chuyen_ve_trang_dang_nhap(client):
    """TC-004."""
    r = client.get("/", follow_redirects=False)

    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_dang_xuat_thi_mat_quyen_truy_cap(client, seed_basic):
    client.post("/login", data={"username": "letan", "password": "matkhau123"})

    client.post("/logout")
    r = client.get("/", follow_redirects=False)

    assert r.status_code == 303



# --- Lỗi tìm được khi rà bằng chuột trên trình duyệt (P4) ------------------------


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


def test_url_khong_khop_route_nao_van_hien_trang_loi_co_bo_cuc(client, seed_basic):
    """TC-007 mở rộng: 404 do không khớp route cũng phải là trang, không phải JSON.

    Handler đăng ký trên `fastapi.HTTPException`, còn route không khớp ném
    `starlette.HTTPException` — lớp cha. Đăng ký ở lớp con không bắt được lớp cha, nên
    `/stats` (link có sẵn trong menu quản lý) trả `{"detail":"Not Found"}` trên nền đen.
    """
    dang_nhap(client, "quanly")

    r = client.get("/khong-co-trang-nay")

    assert r.status_code == 404
    assert "Không tìm thấy trang" in r.text
    assert "detail" not in r.text


def test_trang_loi_404_khong_hien_chu_tieng_anh_cua_framework(client, seed_basic):
    """Trang 404 có bố cục rồi, nhưng dòng mô tả vẫn là "Not Found" của Starlette.

    Người dùng từng gặp trang này qua link **Thống kê** trong menu quản lý, trước khi P6
    dựng trang đó. CLAUDE.md mục 5: thông báo hiển thị cho người dùng viết bằng tiếng Việt.
    Ca 403 không dính vì thông điệp do chính dự án viết.
    """
    dang_nhap(client, "quanly")

    r = client.get("/khong-co-trang-nay")

    assert "Not Found" not in r.text
    assert "Đường dẫn này không tồn tại" in r.text


def test_trang_loi_403_van_giu_nguyen_thong_diep_cua_du_an(client, seed_basic):
    """Ca biên: chỉ thay chữ mặc định của framework, không nuốt thông điệp mình viết."""
    dang_nhap(client, "letan")

    r = client.get("/users")

    assert r.status_code == 403
    assert "Bạn không có quyền" in r.text


@pytest.mark.parametrize("username", ["quanly", "letan", "chamsoc1"])
def test_moi_vai_tro_deu_co_link_menu_toi_bang_gia_dich_vu(client, seed_basic, username):
    """Bảng phân quyền US-02 cho cả ba vai trò quyền xem dịch vụ.

    Trước đây chỉ `manager` có link; lễ tân và nhân viên mở được trang nhưng phải gõ URL.
    """
    dang_nhap(client, username)

    r = client.get("/")

    assert 'href="/services"' in r.text


# --- L-01: thẻ trang chủ phải khớp thanh điều hướng THEO TỪNG VAI TRÒ -------------
#
# `test_architecture.py::test_moi_link_tren_thanh_dieu_huong_deu_co_the_tren_trang_chu`
# chỉ so danh sách đường dẫn gộp chung, và nói rõ trong docstring rằng phần vai trò phải
# kiểm bằng integration test. Chỗ đó bỏ trống suốt, nên L-01 lọt: lễ tân có link "Dịch
# vụ" trên thanh điều hướng mà không có thẻ; nhân viên chăm sóc thiếu cả "Chủ nuôi" lẫn
# "Dịch vụ". Đo lại bằng Chrome 24/09: lễ tân 6 menu / 5 thẻ, chăm sóc 5 menu / 3 thẻ.
#
# Trang chủ là màn hình đầu tiên sau khi đăng nhập. Chức năng có trên thanh điều hướng mà
# không có thẻ thì người dùng mới không biết là mình được phép làm.

import re


def dang_nhap(client, username, password="matkhau123"):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code in (200, 303)
    return client


def _duong_dan_tren_trang_chu(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.text

    khoi_nav = html[html.index("<nav>") : html.index("</nav>")]
    khoi_the = html[html.index('class="luoi-the"') : html.rindex("</div>")]

    nav = {h for h in re.findall(r'href="(/[^"]*)"', khoi_nav)}
    the = {h for h in re.findall(r'href="(/[^"]*)"', khoi_the)}
    return nav, the


@pytest.mark.parametrize("username", ["quanly", "letan", "chamsoc1"])
def test_moi_link_menu_deu_co_the_tuong_ung_theo_tung_vai_tro(client, seed_basic, username):
    dang_nhap(client, username)

    nav, the = _duong_dan_tren_trang_chu(client)

    assert nav - the == set(), (
        f"Vai trò {username}: có trên thanh điều hướng nhưng thiếu thẻ trang chủ: "
        f"{sorted(nav - the)}"
    )


@pytest.mark.parametrize("username", ["quanly", "letan", "chamsoc1"])
def test_khong_co_the_nao_tro_toi_cho_vai_tro_khong_vao_duoc(client, seed_basic, username):
    """Chiều ngược lại: thẻ mà không có link menu nghĩa là thẻ thừa hoặc menu thiếu.

    Không có ca này thì bản vá dễ đi quá tay — thêm mọi thẻ cho mọi vai trò, kể cả thẻ
    dẫn tới trang họ sẽ nhận 403.
    """
    dang_nhap(client, username)

    nav, the = _duong_dan_tren_trang_chu(client)

    assert the - nav == set(), (
        f"Vai trò {username}: có thẻ trang chủ nhưng thiếu link trên thanh điều hướng: "
        f"{sorted(the - nav)}"
    )


# --- L-07: đăng nhập sai không được xóa tên đã gõ --------------------------------
#
# Đo bằng Chrome 24/09: sai mật khẩu → thông báo hiện đúng nhưng ô tên đăng nhập rỗng,
# nên người dùng phải gõ lại cả hai ô dù chỉ sai một.


def test_dang_nhap_sai_van_giu_lai_ten_da_go(client, seed_basic):
    r = client.post("/login", data={"username": "letan", "password": "sai-mat-khau"})

    assert r.status_code == 401
    assert 'value="letan"' in r.text


def test_dang_nhap_sai_KHONG_giu_lai_mat_khau(client, seed_basic):
    """Ranh giới của bản vá: tiện thì tiện, nhưng mật khẩu không được nằm trong HTML.

    Máy quầy dùng chung, và HTML còn nằm lại trong bộ nhớ đệm của trình duyệt.
    """
    r = client.post("/login", data={"username": "letan", "password": "bi-mat-123"})

    assert "bi-mat-123" not in r.text


def test_tai_khoan_bi_khoa_cung_giu_lai_ten(client, db, seed_basic):
    """Đường báo lỗi thứ hai có nhánh render riêng — bài học 4."""
    seed_basic["receptionist"].is_active = False
    db.commit()

    r = client.post("/login", data={"username": "letan", "password": "matkhau123"})

    assert r.status_code == 401
    assert 'value="letan"' in r.text


# --- L-02: trang đã đăng nhập không được nằm lại trong bộ nhớ đệm -----------------
#
# Đo bằng Chrome 24/09: `/`, `/owners`, `/invoices`, `/login` đều KHÔNG có header
# `Cache-Control`. Hậu quả: đăng xuất rồi bấm Back vẫn thấy tên nhân viên và danh sách
# khách kèm số điện thoại. Rủi ro thật trên máy quầy dùng chung, và phiên sống 14 ngày.


@pytest.mark.parametrize("duong_dan", ["/", "/owners", "/invoices", "/appointments"])
def test_trang_da_dang_nhap_co_header_khong_luu_dem(client, seed_basic, duong_dan):
    dang_nhap(client, "quanly")

    r = client.get(duong_dan)

    assert "no-store" in r.headers.get("cache-control", "")


def test_trang_dang_nhap_cung_khong_luu_dem(client, seed_basic):
    """Trang `/login` cũng phải no-store: bấm Back về nó sau khi đăng nhập mà trình duyệt
    dựng lại từ bộ nhớ đệm thì ô tên đăng nhập của người trước vẫn còn."""
    r = client.get("/login")

    assert "no-store" in r.headers.get("cache-control", "")


def test_tep_tinh_van_duoc_luu_dem(client, seed_basic):
    """Ca đối chứng: đừng tắt bộ nhớ đệm của cả CSS — nó không chứa dữ liệu ai cả,
    và tải lại mỗi lần là phí băng thông cho đúng một thứ không bí mật."""
    r = client.get("/static/style.css")

    assert r.status_code == 200
    assert "no-store" not in r.headers.get("cache-control", "")
