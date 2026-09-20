"""Test cho app/services/users.py — nghiệp vụ quản lý tài khoản nhân viên.

Phục vụ US-03 — TC-010 → TC-012.

Bốn quy tắc ở đây trước nằm trong router nên chỉ kiểm được qua HTTP. Chuyển ra tầng
services để kiểm thẳng, không cần khởi động app: quy tắc "quản lý không tự khóa chính
mình" là nghiệp vụ thuần, không dính gì tới HTTP.
"""

import pytest
from sqlalchemy import select

from app.models.user import User
from app.security import verify_password
from app.services import users as nv
from app.services.errors import LoiNghiepVu


# --- Tạo tài khoản ---------------------------------------------------------------


def test_tao_tai_khoan_luu_dung_vai_tro_va_ten(db, seed_basic):
    u = nv.tao_tai_khoan(db, "letan2", "Nguyen Thi Hai", "receptionist", "matkhau456")

    assert u.id is not None
    assert u.username == "letan2"
    assert u.role == "receptionist"
    assert u.is_active is True


def test_tao_tai_khoan_bam_mat_khau_khong_luu_ban_goc(db, seed_basic):
    """TC-005 ở tầng nghiệp vụ: không đâu trong bản ghi còn mật khẩu gốc."""
    u = nv.tao_tai_khoan(db, "letan2", "Nguyen Thi Hai", "receptionist", "matkhau456")

    assert u.password_hash != "matkhau456"
    assert verify_password("matkhau456", u.password_hash)


def test_tao_tai_khoan_trung_username_bi_tu_choi(db, seed_basic):
    """TC-012. Ràng buộc UNIQUE ở CSDL cũng chặn, nhưng chặn ở đây mới có thông báo đọc được."""
    with pytest.raises(LoiNghiepVu) as loi:
        nv.tao_tai_khoan(db, "letan", "Trung ten dang nhap", "receptionist", "matkhau456")

    assert "letan" in str(loi.value)


def test_tao_tai_khoan_vai_tro_khong_hop_le_bi_tu_choi(db, seed_basic):
    """Ba vai trò là cố định. Vai trò lạ lọt vào sẽ làm mọi phép kiểm quyền sau đó vô nghĩa."""
    with pytest.raises(LoiNghiepVu):
        nv.tao_tai_khoan(db, "aidong", "Vai tro la", "admin", "matkhau456")

    assert db.query(User).filter_by(username="aidong").first() is None


# --- Khóa và mở khóa -------------------------------------------------------------


def test_khoa_tai_khoan_chuyen_is_active_ve_false(db, seed_basic):
    """TC-011."""
    letan = seed_basic["receptionist"]
    quan_ly = seed_basic["manager"]

    nv.khoa_tai_khoan(db, letan.id, nguoi_thao_tac_id=quan_ly.id)

    assert letan.is_active is False


def test_quan_ly_khong_tu_khoa_chinh_minh(db, seed_basic):
    """Ca biên quan trọng nhất của nhóm này.

    Tự khóa mình sẽ đẩy quản lý ra khỏi hệ thống, và không còn ai mở lại được — hệ thống
    khóa cứng, chỉ sửa được bằng cách vào thẳng CSDL.
    """
    quan_ly = seed_basic["manager"]

    with pytest.raises(LoiNghiepVu):
        nv.khoa_tai_khoan(db, quan_ly.id, nguoi_thao_tac_id=quan_ly.id)

    assert quan_ly.is_active is True


def test_khoa_tai_khoan_khong_ton_tai_bi_tu_choi(db, seed_basic):
    with pytest.raises(LoiNghiepVu):
        nv.khoa_tai_khoan(db, 9999, nguoi_thao_tac_id=seed_basic["manager"].id)


def test_mo_khoa_tai_khoan_chuyen_is_active_ve_true(db, seed_basic):
    letan = seed_basic["receptionist"]
    nv.khoa_tai_khoan(db, letan.id, nguoi_thao_tac_id=seed_basic["manager"].id)

    nv.mo_khoa_tai_khoan(db, letan.id)

    assert letan.is_active is True


def test_mo_khoa_tai_khoan_khong_ton_tai_bi_tu_choi(db, seed_basic):
    with pytest.raises(LoiNghiepVu):
        nv.mo_khoa_tai_khoan(db, 9999)


# --- Danh sách -------------------------------------------------------------------


def test_danh_sach_tai_khoan_sap_theo_vai_tro_roi_ten(db, seed_basic):
    ds = nv.danh_sach_tai_khoan(db)

    assert [u.username for u in ds] == ["chamsoc1", "chamsoc2", "quanly", "letan"]


def test_danh_sach_tai_khoan_van_hien_tai_khoan_da_khoa(db, seed_basic):
    """Khóa không phải xóa — quản lý phải thấy để mở lại được."""
    letan = seed_basic["receptionist"]
    nv.khoa_tai_khoan(db, letan.id, nguoi_thao_tac_id=seed_basic["manager"].id)

    assert letan.id in [u.id for u in nv.danh_sach_tai_khoan(db)]


# --- Độ dài mật khẩu (M-04) ------------------------------------------------------


@pytest.mark.parametrize("mat_khau", ["", "1", "ab", "1234567"])
def test_mat_khau_ngan_hon_8_ky_tu_bi_tu_choi(db, seed_basic, mat_khau):
    """Mật khẩu 1 ký tự tạo được tài khoản và đăng nhập được ngay (M-04).

    Đo bằng Chrome 20/09: `1`, `ab`, `1234567` đều tạo được tài khoản qua form thật.
    Mật khẩu rỗng bị chặn, nhưng bằng JSON thô 422 của framework chứ không phải thông
    báo tiếng Việt (N-02) — nên ca rỗng nằm luôn ở đây để thông báo cũng đọc được.

    NẾU TEST NÀY ĐỎ: `tao_tai_khoan` nhận mật khẩu ngắn hơn ngưỡng.
    """
    with pytest.raises(LoiNghiepVu) as loi:
        nv.tao_tai_khoan(
            db, username="moi", full_name="Người mới", role="receptionist",
            password=mat_khau,
        )

    assert "8" in str(loi.value), "thông báo phải nói rõ ngưỡng để người dùng sửa được"
    assert db.scalar(select(User).where(User.username == "moi")) is None, (
        "tài khoản không được tạo khi mật khẩu bị từ chối"
    )


def test_mat_khau_du_8_ky_tu_thi_tao_duoc(db, seed_basic):
    """Ranh giới: đúng 8 ký tự phải được nhận, không phải 9."""
    tai_khoan = nv.tao_tai_khoan(
        db, username="vua_du", full_name="Vừa đủ", role="receptionist",
        password="12345678",
    )

    assert tai_khoan.id is not None
    assert verify_password("12345678", tai_khoan.password_hash)


@pytest.mark.parametrize("mat_khau", ["", "1", "1234567"])
def test_kiem_mat_khau_tu_choi_chuoi_ngan(mat_khau):
    """Gọi thẳng phép kiểm — cả ba đường đặt mật khẩu đều đi qua nó."""
    with pytest.raises(LoiNghiepVu):
        nv.kiem_mat_khau(mat_khau)


@pytest.mark.parametrize("mat_khau", ["12345678", "mat khau rat dai va an toan"])
def test_kiem_mat_khau_nhan_chuoi_du_dai(mat_khau):
    """Happy path và biên dưới (đúng 8 ký tự): không được ném gì."""
    nv.kiem_mat_khau(mat_khau)


# --- Sửa tài khoản và mật khẩu (M-02) --------------------------------------------


def test_sua_tai_khoan_doi_ho_ten_va_vai_tro(db, seed_basic):
    """US-03 nói "tạo, **sửa**, khóa" — phần sửa chưa từng tồn tại (M-02)."""
    letan = seed_basic["receptionist"]

    nv.sua_tai_khoan(db, letan.id, full_name="Trần Thị Lễ Tân", role="manager")

    assert (letan.full_name, letan.role) == ("Trần Thị Lễ Tân", "manager")


def test_sua_tai_khoan_khong_doi_duoc_ten_dang_nhap(db, seed_basic):
    """Tên đăng nhập là thứ người ta nhớ và là khóa tra cứu trong log — không cho đổi."""
    letan = seed_basic["receptionist"]

    nv.sua_tai_khoan(db, letan.id, full_name="Tên mới", role="receptionist")

    assert letan.username == "letan"


def test_sua_tai_khoan_vai_tro_khong_hop_le_bi_tu_choi(db, seed_basic):
    letan = seed_basic["receptionist"]

    with pytest.raises(LoiNghiepVu):
        nv.sua_tai_khoan(db, letan.id, full_name="Tên mới", role="giam_doc")

    assert letan.role == "receptionist"


def test_sua_tai_khoan_ho_ten_trong_bi_tu_choi(db, seed_basic):
    letan = seed_basic["receptionist"]
    ten_cu = letan.full_name  # đọc từ fixture, không viết cứng (bài học 1)

    with pytest.raises(LoiNghiepVu):
        nv.sua_tai_khoan(db, letan.id, full_name="   ", role="receptionist")

    assert letan.full_name == ten_cu


def test_quan_ly_khong_tu_ha_vai_tro_cua_chinh_minh(db, seed_basic):
    """Cùng lớp với "không tự khóa mình": tự hạ vai trò là mất quyền quản lý, không ai mở lại."""
    quanly = seed_basic["manager"]

    with pytest.raises(LoiNghiepVu):
        nv.sua_tai_khoan(
            db, quanly.id, full_name=quanly.full_name, role="receptionist",
            nguoi_thao_tac_id=quanly.id,
        )

    assert quanly.role == "manager"


def test_sua_tai_khoan_khong_ton_tai_bi_tu_choi(db, seed_basic):
    with pytest.raises(LoiNghiepVu):
        nv.sua_tai_khoan(db, 9999, full_name="Ai đó", role="receptionist")


def test_dat_lai_mat_khau_khong_can_mat_khau_cu(db, seed_basic):
    """Quản lý đặt lại cho nhân viên quên mật khẩu — trước đây quên là mất tài khoản."""
    letan = seed_basic["receptionist"]

    nv.dat_lai_mat_khau(db, letan.id, mat_khau_moi="matkhaumoi123")

    assert verify_password("matkhaumoi123", letan.password_hash)
    assert not verify_password("matkhau123", letan.password_hash)


def test_dat_lai_mat_khau_van_theo_luat_do_dai(db, seed_basic):
    """Đường đặt mật khẩu thứ hai cũng phải qua `kiem_mat_khau`, không được bỏ sót."""
    letan = seed_basic["receptionist"]

    with pytest.raises(LoiNghiepVu):
        nv.dat_lai_mat_khau(db, letan.id, mat_khau_moi="123")

    assert verify_password("matkhau123", letan.password_hash), "mật khẩu cũ phải còn nguyên"


def test_doi_mat_khau_phai_nhap_dung_mat_khau_cu(db, seed_basic):
    letan = seed_basic["receptionist"]

    with pytest.raises(LoiNghiepVu):
        nv.doi_mat_khau(db, letan.id, mat_khau_cu="sai_bet", mat_khau_moi="matkhaumoi123")

    assert verify_password("matkhau123", letan.password_hash)


def test_doi_mat_khau_dung_mat_khau_cu_thi_doi_duoc(db, seed_basic):
    letan = seed_basic["receptionist"]

    nv.doi_mat_khau(db, letan.id, mat_khau_cu="matkhau123", mat_khau_moi="matkhaumoi123")

    assert verify_password("matkhaumoi123", letan.password_hash)


def test_doi_mat_khau_van_theo_luat_do_dai(db, seed_basic):
    """Đường đặt mật khẩu thứ ba — cũng không được lọt."""
    letan = seed_basic["receptionist"]

    with pytest.raises(LoiNghiepVu):
        nv.doi_mat_khau(db, letan.id, mat_khau_cu="matkhau123", mat_khau_moi="ngan")

    assert verify_password("matkhau123", letan.password_hash)
