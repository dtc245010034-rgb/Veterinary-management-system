"""Test cho app/security.py — băm và kiểm tra mật khẩu.

Phục vụ TC-005 (US-01): mật khẩu lưu trong CSDL phải là chuỗi băm, không phải bản gốc.

bcrypt cố ý chậm (~1,5s mỗi lần băm trên máy phát triển) — đó là điểm mạnh khi chạy thật.
Vì vậy chỉ những test thực sự cần một chuỗi băm mới mới gọi hash_password; các test còn
lại dùng chung fixture bam_san.
"""

import pytest

from app.security import hash_password, verify_password

MAT_KHAU = "matkhau123"


@pytest.fixture(scope="module")
def bam_san():
    """Một chuỗi băm dùng chung cho các test chỉ cần kiểm tra, không cần băm mới."""
    return hash_password(MAT_KHAU)


def test_bam_mat_khau_khong_chua_ban_goc(bam_san):
    """Chuỗi băm không được chứa mật khẩu gốc dưới bất kỳ dạng nào."""
    assert bam_san != MAT_KHAU
    assert MAT_KHAU not in bam_san


def test_kiem_tra_dung_mat_khau_tra_ve_true(bam_san):
    assert verify_password(MAT_KHAU, bam_san) is True


def test_kiem_tra_sai_mat_khau_tra_ve_false(bam_san):
    assert verify_password("matkhau-sai", bam_san) is False


def test_hai_lan_bam_cung_mat_khau_cho_hai_chuoi_khac_nhau(bam_san):
    """Có salt ngẫu nhiên thì hai bản băm phải khác nhau, dù cùng mật khẩu.

    Không có salt, hai người dùng đặt cùng mật khẩu sẽ có cùng chuỗi băm — lộ ngay
    khi CSDL bị đọc trộm. Test này bắt buộc phải băm mới một lần để so sánh.
    """
    assert hash_password(MAT_KHAU) != bam_san


def test_mat_khau_rong_bi_tu_choi():
    with pytest.raises(ValueError):
        hash_password("")
