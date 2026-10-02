# Triển khai

Ba cách chạy, từ đơn giản đến công khai ra Internet. Cả ba đi qua `python run.py` để dùng chung
một logic `.env`: chưa có thì tạo từ `.env.example` với `SECRET_KEY` ngẫu nhiên, đã có thì **không
bao giờ ghi đè** (chỉ dòng `SECRET_KEY` được thay khi còn giá trị mặc định).

| Cách | Lệnh | Khi nào dùng |
|---|---|---|
| Máy mình, venv | `python run.py` | Phát triển, demo tại chỗ |
| Docker | `python run.py docker` | Máy sạch không muốn cài Python; môi trường giống CI |
| Công khai tạm | thêm `--public-url https://…` vào một trong hai lệnh trên | Cho người khác thử qua tunnel (xem mục 3) |

## 1. Chạy bằng venv

```
python run.py                 # tạo .venv, cài thư viện, tạo .env, seed, chạy, mở trình duyệt
python run.py --port 9000 --no-open
python run.py reset           # xóa petcare.db (hỏi xác nhận); lần chạy sau seed lại
```

Mật khẩu của mọi tài khoản mẫu là `matkhau123` — **chỉ chấp nhận được khi chạy trên máy mình**.

## 2. Chạy bằng Docker

```
python run.py docker              # = docker up: dựng image, chạy nền, đợi /login rồi mở trình duyệt
python run.py docker logs         # xem log
python run.py docker down         # tắt, GIỮ dữ liệu (volume petcare_petcare-data)
python run.py docker reset        # tắt và XÓA volume (hỏi xác nhận; --yes để bỏ qua)
python run.py docker up --check   # dựng, đợi /login 200, dọn sạch (dùng trong CI)
```

- `run.py` chọn cổng trống (mặc định 8000) và chỉ mở cổng đó cho `127.0.0.1`, không mở ra mạng LAN.
- CSDL SQLite nằm ở volume `/data`: dựng lại image **không mất dữ liệu**. Volume trống thì lần
  khởi động đầu seed dữ liệu mẫu; đã có CSDL thì giữ nguyên.
- `.env` **không** vào image (`.dockerignore`); compose nạp nó lúc chạy qua `env_file`. Vì vậy
  `SECRET_KEY` nằm ngoài image và ngoài git.
- Cần `docker compose` (v2) hoặc `docker-compose` (v1). Với v1, `run.py` chạy `down` (giữ volume) trước
  `up` vì bản 1.x lỗi `KeyError: 'ContainerConfig'` khi tạo lại container trên Docker Engine mới
  (gặp thật trên Ubuntu 24.04 + Docker 29).
- `--check` dùng project riêng (`petcare-check`), nên `down -v` ở cuối không bao giờ đụng dữ liệu của bản đang chạy.

## 3. Công khai ra Internet bằng tunnel

Dự án **không tự mở cổng ra Internet**. Cách được thiết kế là chạy ở `127.0.0.1` rồi cho một tunnel HTTPS
(ngrok, cloudflared…) trỏ vào cổng đó. Tunnel lo chứng chỉ HTTPS; ứng dụng chỉ cần biết địa chỉ công khai.

```
python run.py --public-url https://abc.ngrok.app
python run.py docker up --public-url https://abc.ngrok.app
```

`--public-url` làm bốn việc, **không ghi vào `.env`** (địa chỉ tunnel đổi mỗi lần):

1. Đặt `SESSION_HTTPS_ONLY=true`: cookie phiên có cờ `Secure`.
2. Đặt `APP_ORIGIN` bằng đúng địa chỉ đó, để POST hợp lệ qua tunnel không bị chặn nhầm là "từ trang khác" (R-2).
3. Nếu CSDL chưa có, **sinh mật khẩu seed ngẫu nhiên**, in ra **một lần** trong terminal.
4. Bật luật: **ứng dụng từ chối khởi động nếu còn tài khoản dùng `matkhau123`** (kể cả tài khoản đang bị
   khóa, vì mở khóa là đăng nhập lại được). Luật nằm trong `lifespan` chứ không phải `run.py`, nên chạy
   `uvicorn` thẳng cũng không lách được.

Đã có CSDL từ trước với mật khẩu mẫu thì ứng dụng báo rõ tên tài khoản và dừng. Hai cách gỡ: đổi mật khẩu
từng tài khoản (trên bản chạy cục bộ), hoặc `python run.py reset` / `python run.py docker reset` để seed lại.

Địa chỉ phải là `https://tên-miền[:cổng]`, không có đường dẫn; `http://` bị từ chối.

## 3b. Thử trên một CSDL mới

- **Tự động:** `python tools/kiem_tra_song.py` dựng CSDL tạm + server thật, chạy 150 kiểm tra rồi dọn.
  Không đụng `petcare.db`.
- **Tự bấm:** `python run.py reset` (xóa `petcare.db`, hỏi xác nhận) rồi `python run.py`; hoặc giữ nguyên
  `petcare.db` và dùng file riêng:
  `DATABASE_URL=sqlite:///thu-nghiem.db python -m app.seed` rồi
  `DATABASE_URL=sqlite:///thu-nghiem.db uvicorn app.main:app --port 8001` (`*.db` đã nằm trong `.gitignore`).
- **Docker:** `python run.py docker reset` xóa volume; lần `up` sau seed lại từ đầu.

Ngày giờ của dữ liệu mẫu tính từ lúc chạy seed, nên CSDL cũ có lịch "ngày mai" đã thành quá khứ.

## 3c. Cấu hình gửi email (P9 chặng 3)

Cổng khách (`/khach`, P9 chặng 4) gửi mail khi đăng ký và quên mật khẩu.

| `MAIL_PROVIDER` | Hành vi |
|---|---|
| `console` (mặc định) | In thư ra log `app.mail`. Chạy cục bộ không cần SMTP. **Không dùng cho bản công khai**: link xác minh nằm trong log, khách không nhận được gì |
| `smtp` | Gửi thật qua `SMTP_HOST`/`SMTP_PORT`, STARTTLS mặc định. Với Gmail: bật xác minh hai bước rồi dùng **mật khẩu ứng dụng** làm `SMTP_PASSWORD`, `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587` |

**Bản công khai bắt buộc `smtp` và `APP_ORIGIN`:** bật `SESSION_HTTPS_ONLY` (hoặc `--public-url`) mà `MAIL_PROVIDER=console` hay thiếu `APP_ORIGIN` thì ứng dụng **từ chối khởi động** — khách sẽ không nhận được thư, và link trong thư dựng từ `APP_ORIGIN` chứ không từ header `Host`. Vì vậy `--public-url` cần `MAIL_PROVIDER=smtp` + `SMTP_*` đã có trong `.env`.

Tên lạ (gõ nhầm `smpt`) là lỗi cấu hình, không âm thầm rơi về `console`. **Chưa thử với nhà cung cấp thật** — xem kế hoạch chặng 3.

## 4. Chuyển sang PostgreSQL (chỉ ghi lại, chưa làm)

Quyết định #9 của [kế hoạch P9](plans/2026-09-25-p9-cong-khach-hang.md): giữ SQLite một worker. Khi nào
đổi và đổi những gì:

- **Dấu hiệu cần đổi:** nhiều người ghi cùng lúc làm SQLite báo `database is locked`, hoặc cần chạy
  nhiều worker/nhiều máy.
- **Phần mềm:** thêm `psycopg[binary]` vào `requirements.txt`, đặt `DATABASE_URL=postgresql+psycopg://user:pass@host/db`.
  SQLAlchemy lo phần còn lại; `app/` không dùng cú pháp riêng của SQLite.
- **Cần kiểm lại (chưa thử cái nào trên PostgreSQL):** `app/services/schema.py` — `nang_cap_schema` dựng
  `ALTER TABLE … ADD COLUMN` từ model; các truy vấn có so sánh ngày giờ trong `app/services/`; và
  `python run.py reset` vốn chỉ xóa file SQLite (từ chối URL khác).
- **Docker:** thêm service `db` (`postgres:16-alpine`) vào `docker-compose.yml`, bỏ `VOLUME /data` và dòng
  kiểm `/data/petcare.db` trong `CMD` của `Dockerfile`; thay bằng một bước chờ DB và seed bằng cờ riêng.
- **Chưa có:** bộ test chạy trên PostgreSQL. CI hiện chỉ chạy SQLite.

## 5. Giới hạn đã biết

| Giới hạn | Hệ quả | Hướng xử lý nếu cần |
|---|---|---|
| Bộ đếm đăng nhập sai (R-1) nằm **trong bộ nhớ** | Khởi động lại là đếm lại từ 0; nhiều worker thì mỗi worker đếm riêng | Giữ một worker, hoặc lưu bộ đếm vào CSDL |
| Đăng xuất thu hồi **mọi thiết bị** (`session_version` theo tài khoản) | Một người đăng xuất thì máy khác của chính họ cũng bị đá ra | Số phiên theo thiết bị — chưa làm |
| Chưa có `Content-Security-Policy` | Đã có `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` nhưng không chặn được script chèn vào | Thêm CSP sau khi rà JS nội tuyến trong template |
| Cờ `Secure` mới kiểm ở mức **header** | Kiểm thật: `Set-Cookie … secure` có mặt khi bật. Chưa kiểm trên HTTPS thật qua tunnel | Chạy `--public-url` với một tunnel thật rồi đăng nhập bằng trình duyệt |
| SQLite một ghi tại một thời điểm | Đủ cho cửa hàng nhỏ; sẽ nghẽn nếu cổng khách hàng (P9) có nhiều người đặt lịch cùng lúc | Mục 4 |
| Image cài cả `pytest`, `httpx` | Thừa vài MB | Tách `requirements-dev.txt` nếu image thành mối bận tâm |
| `docker-compose` 1.x chỉ là đường lùi | Chưa kiểm trên Windows (Docker Desktop dùng v2) | Dùng `docker compose` v2 |
