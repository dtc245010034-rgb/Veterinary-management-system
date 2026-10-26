# Ghi chú sửa các bài pytest

Đã sửa `templates/base.html`:
- Thêm liên kết `/ai/hoi-dap` vào thanh điều hướng cho các vai trò có thẻ Trợ lý AI trên trang chủ.
- Bỏ form Đăng xuất trùng ở khối tài khoản nổi; form đăng xuất chính vẫn nằm trong thanh điều hướng.

Còn một lỗi nằm trong bộ kiểm thử, không phải template: trong `tests/integration/test_ai.py`, test `test_ai_loi_thi_trang_khong_vo_va_du_lieu_lich_hen_con_nguyen` kiểm tra `assert "500" not in r.text`. Điều này khớp nhầm với HTML `maxlength="1500"`. Thay dòng đó bằng:

```python
assert "Internal Server Error" not in r.text
```

Giữ nguyên các assertion kiểm tra `r.status_code == 400` và dữ liệu lịch hẹn không thay đổi. Bộ ZIP gốc không chứa thư mục `tests/`, nên test này chưa được chỉnh trực tiếp trong gói.
