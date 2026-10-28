#!/bin/sh
# Build CSS tĩnh cho trang đăng nhập (chạy 1 lần ở máy có mạng, rồi commit kết quả).
# Cần Node.js. Chạy từ thư mục tools/tailwind:  sh build.sh
set -e
cd "$(dirname "$0")"
npx --yes tailwindcss@3.4.17 -c tailwind.config.js -i input.css -o ../../static/login-tailwind.css --minify
echo "Đã tạo static/login-tailwind.css"
# Font Awesome 6.4.0 (cần cả thư mục webfonts) và Be Vietnam Pro: tải về static/vendor/ rồi trỏ @font-face tới đó.
