# Báo cáo rà soát độc lập — 02/10/2026

Phạm vi: kiểm chứng lại toàn bộ trạng thái dự án **trên máy này**, không tin số liệu trong tài liệu.
Mọi thao tác ghi đều chạy trên **bản sao CSDL** trong thư mục tạm; `petcare.db` thật và repo không bị đụng
(`git status` sạch sau mỗi lượt). Không commit, không push, không tick smoke.

Môi trường: Linux, Python 3.12.3, venv sạch từ `requirements.txt`, không có `.env`, `AI_PROVIDER=fake`.
Commit kiểm: `47b6af1` (local = remote, không có commit tồn).

## 1. Kết luận ngắn

- **Code và bộ test đúng như tài liệu tuyên bố.** 906 ca (905 pass + 1 skip đúng dự báo cho Linux), CI xanh trên cả Ubuntu và Windows.
- Không tìm thấy lỗi chức năng nào trong các luồng đã rà (crawl 4 vai trò, phân quyền, đặt lịch biên, guardrail AI).
- Còn **5 điểm bảo mật/độ cứng** chưa có trong danh sách lỗi của dự án (mục 5) — đều ở mức thấp–vừa, phù hợp cho
  app dùng nội bộ tại quầy; cần quyết định có sửa hay ghi nhận là chấp nhận rủi ro.
- Phase đang ở: **P8 chưa đóng** (6 ô smoke chờ người dùng tick). Việc kế tiếp theo kế hoạch: P9 → bộ đo RAGAS.

## 2. Kết quả đo (đã chạy thật)

| Hạng mục | Kết quả |
|---|---|
| pytest toàn bộ, lượt 1 | `905 passed, 1 skipped in 50.55s` (ca skip: `tests/unit/test_hooks.py:61`, thiếu PowerShell) |
| pytest lặp thêm 3 lượt | cả 3 lượt xanh, không lỗi → **chưa tái hiện được nghi flaky** (tổng 4 lượt) |
| CI GitHub Actions | run #1 commit `47b6af1`: Success, 1m27s, job ubuntu-latest + windows-latest đều xong. Chỉ có cảnh báo Node 20 deprecated và ubuntu-latest sẽ chuyển Ubuntu 26 từ 19/10/2026. Chưa xem log chi tiết số ca từng job |
| Khởi động không `.env` | uvicorn từ chối chạy: `SECRET_KEY vẫn là chuỗi mặc định` — đúng thiết kế |
| Seed | `python -m app.seed` chạy được, mật khẩu chung `matkhau123` |
| Crawl link GET | quanly 28 trang, letan 26, chamsoc1 15, chamsoc2 15 — toàn 200, **0 lỗi 5xx**; băm CSDL trước/sau không đổi (GET không ghi dữ liệu) |
| Chưa đăng nhập | mọi GET/POST thử đều 303 → `/login` |

Đếm lại từ hệ thống tập tin: 21 kế hoạch, 15 log phiên, 25 báo cáo, 28 US, 133 dòng TC
(131 ✅ · 1 ⬜ TC-102 · 1 ➖ TC-027), smoke 149 tick / 6 trống, 688 hàm `def test_` (906 ca sau tham số hóa),
~6.628 dòng trong `app/`, 35 class. Số khớp `codebase-map.md`. Không có `.db`/`.env` nào trong git.

## 3. Ma trận phân quyền (đã đo)

| Đường dẫn | manager | receptionist | caretaker |
|---|---|---|---|
| `/users`, `/stats`, `/ai/quota` | 200 | 403 | 403 |
| `/invoices`, `/invoices/1` | 200 | 200 | 403 |
| `/appointments` | 200 | 200 | 303 → `/appointments/cua-toi` |
| `/services`, `/owners`, `/vaccinations`, `/pets/1`, `/ai/hoi-dap` | 200 | 200 | 200 |
| mọi POST ghi | qua | qua (trừ `POST /users`, `POST /services` → 403) | 403 |

Khớp bảng vai trò trong README.

## 4. Luồng nghiệp vụ đã kiểm (HTTP + Chrome)

- **Đặt lịch** (letan): trùng giờ → 400 kèm gợi ý khung trống; 06:00 và 23:30 → 400 "giờ làm việc 08:00–18:00";
  quá khứ → 400; giờ rác → 400; thú cưng không tồn tại → 400; gán lịch cho quản lý → 400 "Chỉ nhân viên chăm sóc…";
  lịch hợp lệ và lịch liền kề 10:45 → 303. Thông điệp lỗi rõ, tiếng Việt.
- **Tìm kiếm không dấu** (Chrome): `q=dau do` → ra "Đậu Đỏ — Trần Quốc Đạt".
- **Thống kê** (Chrome): 4 lượt, doanh thu 210.000đ, chưa thu 90.000đ, cảnh báo "1 lịch đã qua giờ chưa ghi hồ sơ" — hợp lý với dữ liệu seed.
- **AI (fake) + guardrail**: câu "cho tôi liều thuốc bao nhiêu mg" → bị chặn, trả câu từ chối + khuyến cáo bác sĩ thú y,
  nhật ký ghi `feature=qa`, `model=None` (không gọi API). Trang `/ai/quota` hiển thị đủ 4 model, 20 lượt/model.
- **Open-redirect** `?tu=` ở trang kết quả AI: `//evil.com`, `/\evil.com`, `/<tab>/evil.com`, `https://evil.com` → đều về `/`; chỉ `/ai/hoi-dap` được giữ. Tốt.
- **Khóa tài khoản**: khóa `chamsoc2` → phiên đang mở bị vô hiệu ngay (303), đăng nhập lại 401; mở khóa lại bình thường. Quản lý tự khóa mình → 400. Tốt.
- `ai_logs` bản sao chỉ chứa prompt/response, không có SĐT/email/địa chỉ.

## 5. Điểm tồn đọng (chưa sửa — theo luật mục 10 chờ người dùng chọn)

> **Cập nhật cuối ngày 02/10:** cả năm mục R-1…R-5 **đã sửa** trong chặng 0.5 của
> [kế hoạch 02/10](docs/plans/2026-10-02-run-py-va-bao-mat-truoc-p9.md), mỗi mục có test đỏ-trước và
> một lượt đột biến (chi tiết ở [log phiên](docs/sessions/2026-10-02-01.md), Phần 3–4). Bảng dưới
> giữ nguyên làm bằng chứng lúc phát hiện. Giới hạn còn lại: cờ `Secure` chưa kiểm được trên HTTPS
> thật; bộ đếm đăng nhập sai nằm trong bộ nhớ nên mất khi khởi động lại.

| # | Mức | Mô tả | Cách tái hiện | Gợi ý |
|---|---|---|---|---|
| R-1 | Trung bình | **Không giới hạn số lần đăng nhập sai.** 30 lần sai liên tiếp vẫn 401, sau đó đăng nhập đúng vẫn qua | vòng lặp `POST /login` với mật khẩu sai | đếm lần sai theo tên đăng nhập + IP, khóa tạm vài phút; test đỏ trước |
| R-2 | Trung bình | **Không có CSRF token**, chỉ dựa `SameSite=Lax`. POST đổi trạng thái (`/users/{id}/khoa`…) chạy được khi thiếu Origin/Referer | `POST /users/3/khoa` không kèm header nào, 303 | kiểm Origin/Referer cho mọi POST, hoặc token trong form |
| R-3 | Thấp–TB | **Đăng xuất không thu hồi cookie đã sao chép**: cookie cũ vẫn trả 200 sau `POST /logout` (phiên là cookie ký không có trạng thái phía server) | lấy cookie, đăng xuất, gửi lại cookie | số phiên (`session_version`) lưu theo user, tăng khi đăng xuất/đổi mật khẩu |
| R-4 | Thấp | **Thiếu header bảo mật**: chỉ có `Cache-Control: no-store`; không có `X-Frame-Options`/CSP `frame-ancestors`, `X-Content-Type-Options`, `Referrer-Policy` | `curl -I` | thêm middleware một chỗ |
| R-5 | Rất thấp | Thông điệp seed in "5 lịch hẹn" nhưng CSDL thực có 8 (`app/seed.py:244`: biến `lich_moi` chỉ đếm 4 lịch ngày mai + 1 lịch chưa ghi hồ sơ; 3 lịch `done` kèm hồ sơ được tính vào "3 hồ sơ chăm sóc", không vào "lịch hẹn") | `python -m app.seed` rồi đếm bảng `appointments` | sửa dòng in cho đúng số thực |

Ghi chú: cookie không có cờ `Secure` là bình thường trên localhost; chỉ cần khi triển khai HTTPS.
Cookie có `HttpOnly` và `SameSite=Lax` (đã đo).

Các điểm còn mở từ tài liệu dự án (không đổi): M-08 chưa kiểm bằng Gemini thật (máy này không có khóa); bẫy hook
`session-stop.ps1` (xóa log có ≥5 chuỗi `_(chua ghi)_`); TC-102 còn ⬜.

## 6. Chưa kiểm (nói thẳng)

- Gemini thật (không có khóa) — chỉ kiểm bằng `fake`.
- Thao tác hóa đơn/thu tiền/hủy, hồ sơ chăm sóc, tiêm phòng qua giao diện Chrome: mới kiểm tới mức quyền truy cập và crawl, chưa nhập dữ liệu từng form.
- Bố cục điện thoại/responsive, console trình duyệt: chưa rà. (Tiện ích Chrome trên máy gọi `/hybridaction/zybTrackerStatisticsAction` vào localhost gây 404 nhiễu — không phải lỗi app.)
- Log chi tiết số ca của từng job CI.
- Mutation testing: chưa chạy lượt nào trong phiên này.

## 7. Kế hoạch tiếp theo (đề xuất, đúng thứ tự trong `roadmap.md`/kế hoạch)

1. **Người dùng tick 6 ô smoke P8** (xóa `petcare.db` chạy lại; làm theo README trên máy sạch; `.env` không trong repo; rà `ai_logs`; ma trận không còn ⬜; dán pytest xanh vào báo cáo cuối) → đóng P8.
2. **Chọn nhóm lỗi R-1…R-5** để sửa (đề xuất R-1 + R-2 trước, mỗi cái kèm test đỏ-trước). Nếu muốn giữ phạm vi, ghi R-3/R-4 là rủi ro chấp nhận.
3. **P9 — cổng khách hàng** (29 ô, chưa duyệt): ô 0.1 đổi fixture `db` (dựng schema một lần/phiên + rollback từng test) làm trước vì nó cũng giảm nguy cơ flaky.
4. **Bộ đo AI có RAGAS** (12 ô, đã duyệt, chưa làm).
5. README hoàn chỉnh, báo cáo cuối kỳ, slide.

## 8. Ghi chú về vị trí file này

File đặt ở gốc repo, **chưa vào `docs/`**: thêm vào `docs/testing/reports/` sẽ làm đổi số báo cáo (25 → 26), đòi cập nhật `codebase-map.md`,
và tên file mới nhất phải nêu mã phase khớp dòng Trạng thái README (`test_architecture.py`). Nếu muốn lưu chính thức, cần
đổi tên theo quy ước và cập nhật hai chỗ đó.
