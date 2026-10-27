# Kế hoạch — Sửa lỗi B-2 (thư giả không hiện ra terminal)

**Trạng thái: XONG phần việc của agent (28/10/2026).** Yêu cầu của người dùng 28/10: sửa B-2 rồi commit và push lên `main`
(người dùng đã cho phép commit/push khi mọi bước kiểm chứng đạt). B-2 đã nằm sẵn trong báo cáo tiến độ 03/10 là lỗi mức
trung bình chờ quyết; lần này người dùng quyết sửa.

Nguyên nhân: `app/mail/console.py` gọi `log.info(...)` trên logger `app.mail`; không nơi nào cấu hình logger này và uvicorn chỉ
cấu hình logger của nó, nên bản ghi INFO rơi về handler mặc định của Python (chỉ in từ WARNING) và bị bỏ.

## Các bước

- [x] 1. Test ĐỎ trước: tiến trình mới `import app.main` rồi `ConsoleMailer().gui(...)`, đọc stderr thật (không dùng `caplog`).
      → verify: chạy trên code cũ ra `assert 'Xác minh email' in ''`.
- [x] 2. Sửa tối thiểu: `cau_hinh_log_thu()` trong `app/mail/console.py` (handler stderr, INFO, `propagate=False`, idempotent),
      gọi một lần ở `app/main.py` — nơi cả `run.py`, `uvicorn app.main:app` và Docker đều đi qua.
      → verify: test ở bước 1 xanh; không đổi `log.info` thành `log.warning`; không đụng SMTP.
- [x] 3. Luật chế độ công khai (`--public-url`) từ chối `MAIL_PROVIDER=console` vẫn đúng.
      → verify: `test_che_do_cong_khai_voi_mail_console_tu_choi_khoi_dong` xanh.
- [x] 4. Kiểm đột biến: gỡ lời gọi trong `main.py`, bỏ guard idempotent, đổi `propagate` → test tương ứng đỏ, hoàn nguyên.
- [x] 5. Cập nhật tài liệu: README mục 6/8/10/12, `HUONG-DAN-SU-DUNG.md`, báo cáo tiến độ, báo cáo P9, `codebase-map.md`,
      `test-cases.md` (TC-146).
- [x] 6. `pytest` toàn bộ xanh (1 ca bỏ qua duy nhất: hook PowerShell); `AI_PROVIDER=fake python tools/kiem_tra_song.py` 150/150.
- [x] 7. Kiểm tay trên server uvicorn thật, CSDL tạm: đăng ký và quên mật khẩu đều in thư, mở liên kết được; `petcare.db` không đổi.
- [x] 8. Commit một lần và `git push origin main` (hash và trạng thái CI ghi ở báo cáo cuối phiên, không chép vào đây để khỏi tự tham chiếu).

## Đợt 2 (cùng ngày) — phần còn thiếu sau lượt đầu

Người dùng yêu cầu làm nốt hai việc lượt đầu chưa làm: kiểm Docker thật, và sửa B-1.

- [x] 9. Kiểm thư giả trong container thật: `docker compose up -d --build` bằng project riêng `petcare-b2check` (cổng 8791, không
      đụng volume của project `petcare`), đăng ký và quên mật khẩu, đọc `docker compose logs`, rồi `down -v --rmi local`.
      → verify: cả hai thư hiện trong log container; không còn container/volume/image của project kiểm.
- [x] 10. B-1: test ĐỎ trước (phép canh hình dạng trong `test_architecture.py`), rồi quy tắc `input[type="radio"|"checkbox"]` +
      `label.lua-chon` ở cuối `style.css`, thêm class vào `lien_ket_khach.html`.
      → verify: đo Chrome thật trước/sau (855×44px → 13×13px, cùng hàng với chữ); kiểm đột biến; `pytest` toàn bộ xanh.
- [ ] 11. Commit đợt 2 — **chưa làm**: người dùng chưa bảo commit/push cho đợt này.

Không tick ô nào trong `docs/testing/smoke-checklist.md`: đó là việc người dùng tự bấm tay (còn 29 ô: 6 của P8, 23 của P9).
