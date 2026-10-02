# Kế hoạch — `run.py`/`test.py`, nâng cấp schema và bảo mật trước khi mở cổng khách (P9)

**Trạng thái: ĐÃ DUYỆT 02/10/2026** (người dùng chọn "Duyệt, bắt đầu Phiên 1"). Phiên 1–4 xong (chặng 0.5 hoàn tất về code); còn ô 1.4 chờ CI và Docker ở mục 5.

Sinh ra từ [báo cáo rà soát 02/10](../../bao-cao-ra-soat-2026-10-02.md) (R-1 → R-5) và từ yêu cầu của người dùng:
làm hai file `run.py` + `test.py` mẫu CSMS để chạy dự án một lệnh trên máy sạch. Kế hoạch này **không
thay thế** [P9](2026-09-25-p9-cong-khach-hang.md) — nó chèn việc vào trước và bên trong P9.

---

## 1. Các quyết định đã chốt (người dùng trả lời hai vòng hỏi, 02/10)

| # | Quyết định | Lý do / phản biện đã nêu |
|---|---|---|
| 1 | `run.py` chạy bằng **venv thuần** ngay bây giờ; **Docker gắn vào P9 chặng 2** bằng `run.py docker` | Docker đã có sẵn trong P9 (quyết định #9) vì giảng viên nhắc; không viết lại `run.py` hai lần nên tách "backend" ra từ đầu |
| 2 | Làm **trước P9**, gọn trong một phiên | `run.py` chỉ bọc quanh việc chạy app/pytest, không đụng schema hay router nên P9 không chặn nó |
| 3 | Công khai bằng **tunnel tạm khi demo** (ngrok/Cloudflare) | Cần chế độ `--public-url`: cookie Secure, mật khẩu seed ngẫu nhiên, từ chối chạy nếu còn tài khoản mật khẩu mặc định. Làm ở P9 chặng 2, **không** làm ở phiên 1 (YAGNI) |
| 4 | Windows là môi trường chính, Linux/macOS vẫn chạy | CI hiện chạy cả hai hệ |
| 5 | R-1…R-4 + cookie Secure là **chặng 0.5 mới trong P9**, trước khi dựng màn hình khách | Khách tự đăng ký là người lạ; thứ chỉ chấp nhận được với nhân viên quầy thì không chấp nhận được với cổng công khai |
| 6 | Thiếu cột (`owners.user_id`, `users.session_version`): **hàm nâng cấp schema nhỏ, idempotent, có test** | Dự án không có migration — `create_all` chỉ tạo bảng thiếu, không thêm cột; Alembic quá tay cho SQLite một file |
| 7 | R-1 giới hạn đăng nhập sai **theo cặp (IP, tên đăng nhập), trễ tăng dần, lưu bộ nhớ** | Khóa cứng theo tên đăng nhập cho phép kẻ lạ khóa tài khoản `quanly` chỉ bằng cách gõ sai. Đánh đổi: nhiều người chung một IP (NAT) chia nhau độ trễ |
| 8 | `petcare.db` trên máy người dùng **chỉ là dữ liệu demo, xóa được** | `run.py reset` xóa sau khi hỏi xác nhận, không cần sao lưu |
| 9 | Hạn nộp còn **≥ 3 tuần** | Làm đủ theo thứ tự này, không cắt |

Hai thứ cố ý **bỏ** khỏi bản mẫu CSMS: `down`/`logs` (uvicorn chạy foreground, thoát bằng Ctrl+C;
chạy nền ẩn trên Windows chỉ thêm lỗi) và toàn bộ nhánh Docker/Postgres/ngrok.

---

## 2. Thứ tự

1. **Phiên 1 — `run.py` + `test.py`** (mục 3).
2. **Phiên 2 — P9 chặng 0** (ô 0.1/0.2 trong kế hoạch P9: đổi fixture `db`). Không lặp ô ở đây. **Xong 02/10** (hai ô đã tick ở kế hoạch P9).
3. **Phiên 3–4 — chặng 0.5: bảo mật + hàm nâng cấp schema** (mục 4).
4. **P9 chặng 1 → 8** như kế hoạch P9. Riêng chặng 2 (Docker) thêm việc ở mục 5.
5. Sau P9: bộ đo RAGAS, README hoàn chỉnh, báo cáo cuối kỳ, slide (không đổi).

---

## 3. Phiên 1 — `run.py` và `test.py`

Hành vi `python run.py` (mặc định là `up`): kiểm Python đủ mới → tạo `.venv` nếu chưa có → cài
`requirements.txt` khi file đó đổi → **tạo `.env` từ `.env.example` với `SECRET_KEY` ngẫu nhiên, không
bao giờ ghi đè `.env` có sẵn** → seed nếu CSDL trống → chọn cổng trống → chạy uvicorn → mở trình
duyệt. Lệnh khác: `reset` (hỏi xác nhận, xóa `petcare.db`), `status`, `test` (chuyển tiếp tham số
cho pytest). `test.py` chỉ là lối tắt của `run.py test`.

- [x] 1.1 Viết `tests/unit/test_run.py` **trước**: đọc/ghi `.env` (giữ nguyên dòng cũ), không ghi đè
      `.env` có sẵn, `SECRET_KEY` sinh ra đủ dài và khác nhau mỗi lần, chọn cổng trống, nhận biết
      lệnh con. Chạy ra đỏ vì `run.py` chưa có.
      → verify: ghi lại lượt chạy đỏ trong log phiên.
- [x] 1.2 `run.py` ở gốc repo, chỉ dùng thư viện chuẩn, console ép UTF-8, chạy được trên Windows
      lẫn Linux.
      → verify: `tests/unit/test_run.py` xanh.
- [x] 1.3 `test.py` ở gốc repo (lối tắt).
- [ ] 1.4 CI: thêm bước chạy `python run.py` ở chế độ không mở trình duyệt, đợi `/login` trả 200,
      trên cả Windows và Ubuntu.
      → verify: workflow xanh ở lần đẩy tiếp theo (người dùng bảo mới push).
- [x] 1.5 Chạy `python run.py` trong một **bản clone sạch** (không `.venv`, không `.env`, không `.db`)
      trên máy này, đăng nhập thử.
      → verify: ghi lệnh và kết quả vào log phiên; `git status` của repo gốc vẫn sạch.
- [x] 1.6 Đột biến: sửa `run.py` để nó ghi đè `.env` có sẵn, xác nhận test tương ứng **đỏ**, hoàn
      nguyên. Khẳng định đột biến đã vào file (repo trộn LF/CRLF).
- [x] 1.7 Cập nhật README (mục chạy rút từ 5 bước còn 1 lệnh), `codebase-map.md`, bảng trong
      `plans/README.md`, và `.gitignore` nếu cần.
      → verify: `test_architecture.py` xanh.
- [x] 1.8 pytest toàn bộ xanh; điền log phiên `docs/sessions/2026-10-02-NN.md`.

---

## 4. Chặng 0.5 — bảo mật cho việc công khai (nằm trong P9, trước chặng 1)

Mỗi mục: **test đỏ-trước, rồi xanh, rồi một lượt đột biến** (luật mục 7).

- [x] 0.5.1 Hàm nâng cấp schema `ALTER TABLE ... ADD COLUMN` khi cột thiếu, chạy lại an toàn, có test
      trên CSDL dựng từ schema cũ.
      → verify: test dựng DB cũ (không có cột mới), chạy nâng cấp hai lần, cột có đúng một lần.
- [x] 0.5.2 **R-1**: giới hạn đăng nhập sai theo cặp (IP, tên đăng nhập), trễ tăng dần, trả 429.
      → verify: ca chuỗi 30 lần sai bị chặn; ca người dùng khác/IP khác không bị ảnh hưởng; ca đăng nhập
      đúng xóa bộ đếm.
- [x] 0.5.3 **R-2**: từ chối POST có `Origin` khác host hoặc `Sec-Fetch-Site: cross-site`. Request không
      có cả hai header (curl, TestClient) vẫn qua — đây là chủ ý, CSRF là tấn công từ trình duyệt.
      → verify: test POST giả `Origin: https://evil.com` bị 403; 906 test cũ vẫn xanh.
- [x] 0.5.4 **R-3**: cột `users.session_version`; tăng khi đăng xuất, đổi mật khẩu, đặt lại mật khẩu;
      session lưu số phiên bản và so khi đọc.
      → verify: test tái hiện lỗi 02/10 — cookie cũ sau đăng xuất phải bị 303, không còn 200.
- [x] 0.5.5 **R-4**: middleware thêm `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`.
- [x] 0.5.6 `SESSION_HTTPS_ONLY` (cookie Secure) và `APP_ORIGIN` vào `app/config.py` và `.env.example`.
      → verify: phép canh `.env.example` đầy đủ (số 50) xanh.
- [x] 0.5.7 **R-5**: dòng in của seed đếm đúng số lịch hẹn thực tế.
- [x] 0.5.8 Cập nhật `docs/ai-safety.md`/`architecture.md`/`test-cases.md`/`codebase-map.md`, báo cáo kiểm
      thử chặng 0.5.

---

## 5. Việc thêm vào P9 chặng 2 (Docker)

- [ ] 5.1 `run.py docker` (up/down/logs/reset trên compose), dùng chung hàm `.env` với lớp venv.
- [ ] 5.2 Chế độ `--public-url https://...`: cookie Secure, `NODE_ENV`-tương-đương, **mật khẩu seed ngẫu
      nhiên**, từ chối chạy nếu còn tài khoản mật khẩu mặc định (`matkhau123`).
      → verify: test đỏ-trước cho hàm chặn mật khẩu mặc định.

---

## 6. Rủi ro đã biết

| Rủi ro | Cách xử lý |
|---|---|
| `run.py` ghi đè `.env` của người dùng | Test + đột biến ở 1.1/1.6 |
| Chạy trong CI không có `python` mới ở Windows | CI dùng `actions/setup-python` như job pytest |
| R-3 đổi cách đọc session làm vỡ test cũ | Chạy 906 test sau mỗi bước; tăng `session_version` mặc định 0 để cookie hiện có vẫn hợp lệ |
| Giới hạn đăng nhập trong bộ nhớ mất khi khởi động lại | Chấp nhận (SQLite một worker); ghi vào `docs/trien-khai.md` ở chặng 2 |
| Thêm file ở gốc repo làm lệch `codebase-map.md` | Ô 1.7 + phép canh `test_architecture.py` |
