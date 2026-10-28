# Build Tailwind tĩnh cho trang đăng nhập

Hiện `_dang_nhap_moi.html` nạp Tailwind từ CDN (dịch CSS ngay trong trình duyệt), nên mất mạng là vỡ giao diện.

1. `sh tools/tailwind/build.sh` → tạo `static/login-tailwind.css`.
2. Trong `_dang_nhap_moi.html`: xóa thẻ `<script src="https://cdn.tailwindcss.com">` và khối `tailwind.config = {...}`,
   thêm `<link rel="stylesheet" href="/static/login-tailwind.css">`.
3. Tải Font Awesome 6.4.0 (css + webfonts) và font Be Vietnam Pro về `static/vendor/`, đổi 2 thẻ `<link>` CDN trong cùng file.
4. Sau đó gỡ ngoại lệ `_dang_nhap_moi.html` trong `tests/unit/test_architecture.py` (nếu có).

Lưu ý: `content` đã gồm cả 3 template vì JS trong trang gán class động (hàm `set(...)`) — Tailwind quét được vì chúng là chuỗi nguyên văn.
