# Kế hoạch — P9 chặng 2: Docker, `run.py docker` và chế độ `--public-url`

**Trạng thái: ĐÃ DUYỆT 02/10/2026** ("bắt đầu chặng 2 đi", sau khi duyệt P9). Gộp ba nhóm ô vì chúng dùng chung một thứ:
ô 2.1–2.3 của [kế hoạch P9](2026-09-25-p9-cong-khach-hang.md) và ô 5.1–5.2 của
[kế hoạch 02/10](2026-10-02-run-py-va-bao-mat-truoc-p9.md).

## Quyết định thiết kế (đã tự chốt, người dùng sửa được)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | Chế độ công khai = `SESSION_HTTPS_ONLY=true`. Ứng dụng **từ chối khởi động** khi ở chế độ này mà còn tài khoản dùng mật khẩu `matkhau123` | Đặt luật trong `lifespan` (cạnh kiểm `SECRET_KEY`) thì phủ cả `run.py`, Docker lẫn chạy tay; đặt trong `run.py` thì chạy `uvicorn` thẳng là lách được |
| 2 | `--public-url` **không ghi vào `.env`**; truyền qua biến môi trường của tiến trình con | `.env` là của người dùng (cam kết "không ghi đè"); tunnel đổi địa chỉ mỗi lần |
| 3 | Mật khẩu seed lấy từ biến `SEED_MAT_KHAU`; không đặt thì vẫn là `matkhau123` (chạy cục bộ không đổi). Chế độ công khai: `run.py` sinh chuỗi ngẫu nhiên, seed in ra **một lần** | Giữ nguyên trải nghiệm demo trên máy mình, nhưng bản công khai không bao giờ có mật khẩu đoán được |
| 4 | Image: `python:3.14-slim` (đổi từ 3.12 lúc làm, để trùng bản Python của CI), chạy bằng user thường, CSDL ở volume `/data`, seed nếu `/data/petcare.db` chưa có (một dòng `sh -c` trong `CMD`, không thêm file `.sh` vì CRLF/LF trên Windows) | Ít file nhất mà vẫn chạy được trên máy sạch |
| 5 | `.dockerignore` loại `.env`, `*.db`, `.venv`, `.git`; có test canh | Bí mật không được "nướng" vào image |
| 6 | Giữ SQLite một worker; đường chuyển PostgreSQL chỉ **ghi trong `docs/trien-khai.md`**, không làm | Quyết định #9 của P9 |
| 7 | CI: job `docker` chỉ chạy Ubuntu (Windows runner không chạy container Linux) | |

## Danh sách ô

Mỗi ô có code: test đỏ-trước → xanh → một lượt đột biến (CLAUDE.md mục 7).

- [x] 2.0.1 `MAT_KHAU_MAC_DINH` chuyển từ `app/seed.py` sang `app/config.py`; thêm `SEED_MAT_KHAU` (config + `.env.example`); seed dùng nó.
      → verify: test seed với `SEED_MAT_KHAU` đặt thì đăng nhập được bằng mật khẩu đó, không đặt thì `matkhau123`.
- [x] 2.0.2 `users.tai_khoan_con_mat_khau_mac_dinh(db)` + `lifespan` từ chối khi `SESSION_HTTPS_ONLY` và còn tài khoản như thế.
      → verify: ca biên — tài khoản **bị khóa** vẫn tính (đăng nhập lại được khi mở khóa); đổi mật khẩu xong thì qua; chế độ thường không kiểm.
- [x] 2.1 `run.py`: hàm thuần `public_env(url)`, `new_seed_password()`, `compose_args(...)`; `parse_args` nhận `docker [up|down|logs|reset]` và `--public-url`.
- [x] 2.2 `run.py up --public-url`: truyền biến môi trường, sinh mật khẩu seed khi CSDL trống. (ô 5.2 kế hoạch 02/10)
- [x] 2.3 `Dockerfile`, `.dockerignore`, `docker-compose.yml` + `tests/unit/test_docker_files.py`.
- [x] 2.4 `run.py docker up|down|logs|reset` + `--check`. (ô 5.1 kế hoạch 02/10)
      → verify: chạy thật trên máy này (có Docker 29.1.3): `up --check` ra `/login` 200; log lệnh và kết quả vào log phiên. *(Xong: 1 phút 56 giây lần đầu; chi tiết ở log phiên Phần 6. Máy chỉ có `docker-compose` 1.29.2, không có plugin `compose` v2 — nên đường v2 mới kiểm bằng test đơn vị, chưa chạy thật.)*
- [ ] 2.5 CI: job `docker` dựng image và chạy `python run.py docker up --check`. (ô 2.2 P9)
      → verify: workflow xanh ở lần đẩy tiếp theo. *(02/10: job đã viết, YAML đọc được, cùng lệnh chạy xanh trên máy này; **chưa chạy trên GitHub** nên chưa tick.)*
- [x] 2.6 `docs/trien-khai.md`: cách chạy venv/Docker/công khai, đường chuyển PostgreSQL, giới hạn đã biết (bộ đếm đăng nhập sai trong bộ nhớ, một worker). (ô 2.3 P9)
- [x] 2.7 Cập nhật `codebase-map.md`, `README.md`, `plans/README.md`, `test-cases.md`, `architecture.md`; điền log phiên; tick ô 2.1–2.3 của P9 và 5.1–5.2 của kế hoạch 02/10.
