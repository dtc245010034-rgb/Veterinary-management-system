# Kế hoạch — P9 chặng 4: Tài khoản khách hàng và cách ly dữ liệu

**Trạng thái: 4a, 4b, 4c đã xong 02/10/2026 (người dùng: "tiếp tục 4b và 4c đi")** ("tiếp tục p9 đi"; người dùng chọn **bảng riêng `customers`** khi được hỏi). Thay thế các ô 4.1–4.5
của [kế hoạch P9](2026-09-25-p9-cong-khach-hang.md). Chia ba đợt: **4a** tài khoản (đăng ký · xác minh · đăng nhập · quên mật khẩu),
**4b** nối hồ sơ chủ nuôi, **4c** cách ly dữ liệu (`yeu_cau_so_huu`, phép canh, quét IDOR).

## Phản biện kế hoạch gốc (đã đối chiếu với code)

| # | Kế hoạch gốc nói | Vấn đề | Quyết định |
|---|---|---|---|
| 1 | 4.1: thêm vai trò `customer` vào `VAI_TRO` | `users.role` có `CHECK (role IN (3 vai trò))` trong CSDL. SQLite không sửa được CHECK; `nang_cap_schema` chỉ thêm cột. `petcare.db` và volume Docker đang có sẽ **nổ 500 ngay khi tạo khách đầu tiên**. Sửa được chỉ bằng dựng lại bảng `users` trong khi `appointments`, `care_records`, `ai_logs` trỏ FK vào nó | **Bảng riêng `customers`.** Không đụng `users` |
| 2 | 4.1: thêm vai trò vào `users` | 25 chỗ ở 11 router chỉ đòi `nguoi_dung_hien_tai` ("đã đăng nhập"): `/owners`, `/pets`, `/services`, `/vaccinations`… Khách chung bảng thì **mở được danh sách chủ nuôi kèm số điện thoại** ngay khi vai trò tồn tại. Phải sửa từng chỗ (đúng loại lỗi "soát tay 50 route" mà mục 5.2 muốn tránh) | Khách dùng **khóa phiên khác** (`customer_id`); mọi dependency nhân viên chỉ đọc `user_id` nên **không có đường nào** để cookie khách thành người dùng nhân viên. Mặc định từ chối thay vì mặc định cho phép |
| 3 | 4.1: `owners.user_id` UNIQUE | `nang_cap_schema` **từ chối** thêm cột UNIQUE vào bảng có sẵn (`LoiNangCap`) → ứng dụng không khởi động được trên CSDL cũ | Khóa nằm ở phía khách: `customers.owner_id` (bảng mới nên UNIQUE được tạo lúc `create_all`). `owners` **không đổi** |
| 4 | 5.3: đếm hạn mức AI từ `ai_logs.user_id` | `ai_logs.user_id` là FK tới `users`, khách không có dòng ở đó | Chặng 7 thêm `ai_logs.customer_id` (cột nullable, `ALTER ADD COLUMN` được). Ghi ở đây để chặng 7 không dựng trên giả định sai |
| 5 | 4.2: đăng ký rồi gửi mail xác minh | Hai điểm yếu của luồng quen thuộc: (a) **liệt kê email** — báo "email đã đăng ký" cho phép dò xem ai là khách; (b) **link trong mail dựng từ header `Host`** — kẻ gửi `Host` giả khiến mail đặt lại mật khẩu chứa link về trang của kẻ đó | (a) Đăng ký và quên mật khẩu **luôn trả cùng một thông báo**, dù email đã có hay chưa. (b) Link dựng từ `APP_ORIGIN`; bản công khai mà thiếu `APP_ORIGIN` thì từ chối gửi. Chỉ máy phát triển (không `APP_ORIGIN`) mới rơi về địa chỉ request |
| 6 | (không nói) | Đã hứa ở chặng 3: công khai mà `MAIL_PROVIDER=console` thì link xác minh nằm trong log, khách không nhận được gì | Từ chối khởi động ở `lifespan` (cùng chỗ với luật mật khẩu mẫu) |
| 7 | Bảng rủi ro: "giới hạn lượt đăng ký" | Không nói giới hạn theo gì. Theo email thì kẻ xấu đổi email vô hạn; chỉ theo IP thì sau NAT dùng chung | Theo **IP** cho đăng ký + quên mật khẩu, dùng lại cơ chế `GioiHanDangNhap` (trong bộ nhớ, đã có test). Giới hạn theo email chưa làm: ghi vào "Giới hạn đã biết" |
| 9 | Đăng ký rồi mới gửi mail xác minh (khách điền mật khẩu ngay) | Dòng `customers` tồn tại trước khi chủ hộp thư xác nhận → kẻ xấu **đăng ký trước** bằng email của người khác với mật khẩu của hắn, rồi chờ nạn nhân "quên mật khẩu" hay đăng nhập nhầm | **Đăng ký chỉ nhập email.** Thư mang link; mở link mới điền tên + mật khẩu; **POST** mới tạo dòng. Không có tài khoản chưa xác minh, nên không cần cột `email_verified_at` |
| 8 | Đăng nhập chung một trang | Một trình duyệt có thể đang giữ phiên nhân viên khi khách đăng nhập (máy quầy dùng chung) → hai danh tính trong một cookie | Đăng nhập bên nào **xóa khóa phiên của bên kia**. Có test hai chiều |

## Thiết kế (đợt 4a)

- `app/models/customer.py` → `customers(id, email UNIQUE, full_name, password_hash, is_active, session_version, owner_id NULL UNIQUE FK owners, created_at)` (không có `email_verified_at`: dòng chỉ ra đời sau khi xác minh, xem phản biện #9).
- `app/services/customers.py`: `yeu_cau_dang_ky`, `hoan_tat_dang_ky`, `xac_thuc` (đăng nhập), `yeu_cau_dat_lai`, `dat_lai_mat_khau`, `doi_mat_khau`, `thu_hoi_phien`. Mật khẩu đi qua **`users.kiem_mat_khau()`** (M-04) và `security.hash_password`. Thư gửi qua `GuiMail` truyền vào, không import `app.mail` trực tiếp từ service.
- `app/auth.py`: `dang_nhap_khach_session`, `khach_hien_tai_hoac_none`, `khach_hien_tai` (khóa `customer_id` / `csv`).
- `app/routers/khach_auth.py` (prefix `/khach`): `GET/POST dang-ky` (chỉ email), `GET/POST dang-ky/{token}` (đặt tên + mật khẩu), `GET/POST dang-nhap`, `POST dang-xuat`, `GET/POST quen-mat-khau`, `GET/POST dat-lai/{token}`, `GET /khach` (trang chủ khách). Router chỉ HTTP.
- `GET` trên link trong thư chỉ đọc (`email_tokens.con_hieu_luc`): trình quét link của hộp thư gọi `GET` trước người dùng và sẽ đốt token nếu `GET` tiêu thụ nó. Chỉ **POST** mới dùng token.
- Template riêng `khach_base.html` — không dùng `base.html` (menu nhân viên).
- Cấu hình công khai: `lifespan` từ chối khi `SESSION_HTTPS_ONLY` + (`MAIL_PROVIDER=console` hoặc thiếu `APP_ORIGIN`).

## Danh sách ô

Mỗi ô có code: test đỏ-trước → xanh → một lượt đột biến (CLAUDE.md mục 7).

### Đợt 4a — tài khoản

- [x] 4a.1 Model `Customer` + `erd.md`.
      → verify: phép canh ERD khớp cột; email trùng bị CSDL chặn.
- [x] 4a.2 Service `customers.py`.
      → verify: đăng ký chỉ gửi một thư có link và **chưa tạo dòng nào**; hoàn tất đăng ký mới tạo khách; email đã có → **không** tạo bản ghi thứ hai, **không** ném lỗi khác biệt; token hết hạn/dùng lại bị từ chối; đặt lại mật khẩu thu hồi phiên; mật khẩu yếu bị từ chối bằng đúng `kiem_mat_khau`.
- [x] 4a.3 Phiên khách trong `auth.py`.
      → verify: cookie khách không mở được `/owners`; cookie nhân viên không mở được `/khach`; đăng nhập bên này xóa phiên bên kia.
- [x] 4a.4 Router + template khách.
      → verify: luồng đăng ký → mail → xác minh → đăng nhập qua HTTP thật với `FakeMailer`; đăng ký email đã có và email mới **cùng một phản hồi**; link trong mail dùng `APP_ORIGIN`, bỏ qua `Host` giả; lượt thứ N+1 bị 429.
- [x] 4a.5 Luật khởi động công khai.
      → verify: công khai + `console` → `RuntimeError`; công khai + thiếu `APP_ORIGIN` → `RuntimeError`; chạy cục bộ không bị ảnh hưởng.
- [x] 4a.6 Tài liệu: `codebase-map`, `architecture`, `test-cases`, `plans/README`, `.env.example` nếu có biến mới, log phiên.
      → verify: `test_architecture.py` xanh; chạy lại toàn bộ test.

### Đợt 4b — nối hồ sơ (thiết kế chốt 02/10)

Khách **không tự nhận** hồ sơ chủ nuôi: khách gửi yêu cầu (số điện thoại + ghi chú), **lễ tân đối chiếu rồi chọn** hồ sơ nào được nối. Ba điểm phản biện:

| # | Vấn đề | Quyết định |
|---|---|---|
| 10 | Cho khách nhập số điện thoại rồi **tự nối** nếu khớp = ai biết số của người khác là xem được toàn bộ hồ sơ + hóa đơn của họ | Không tự động nối. Số điện thoại chỉ là **gợi ý** cho lễ tân; người quyết định là lễ tân |
| 11 | Lúc gửi yêu cầu mà báo "không có hồ sơ nào khớp" thì khách dò được số nào là chủ nuôi của tiệm | Gửi yêu cầu **không tra** `owners`; luôn trả cùng một thông báo "đã gửi, cửa hàng sẽ liên hệ" |
| 12 | Duyệt nhầm thì người lạ xem được dữ liệu người khác, mà kế hoạch gốc không có đường gỡ | Thêm **gỡ liên kết** (`customers.owner_id = NULL`); có hiệu lực ngay vì mỗi request đọc `owner_id` mới từ CSDL |

- `app/models/link_request.py` → `link_requests(id, customer_id FK, phone, note, status pending/approved/rejected CHECK, owner_id FK NULL, decided_by FK users NULL, decided_at NULL, reject_reason NULL, created_at)`; chỉ mục UNIQUE bán phần: **một yêu cầu `pending` mỗi khách** (chặn đua).
- `app/services/link_requests.py`: `gui_yeu_cau`, `yeu_cau_cua_khach`, `danh_sach_cho_duyet` (kèm hồ sơ ứng viên cùng số), `duyet`, `tu_choi`, `go_lien_ket`, `danh_sach_da_lien_ket`.
- Router nhân viên `app/routers/lien_ket_khach.py` (`manager`, `receptionist`): `GET /lien-ket-khach`, `POST …/{id}/duyet`, `POST …/{id}/tu-choi`, `POST …/tai-khoan/{id}/go`. Router khách: `GET/POST /khach/lien-ket`.

- [x] 4b.1 Model `LinkRequest` + `erd.md`.
      → verify: phép canh ERD khớp; hai yêu cầu `pending` của một khách bị CSDL chặn.
- [x] 4b.2 Service `link_requests.py`.
      → verify: gửi yêu cầu không tra `owners`; đã nối rồi thì không gửi được; duyệt hồ sơ đã thuộc khách khác bị từ chối; duyệt hai lần bị từ chối; từ chối bắt buộc có lý do; gỡ liên kết đưa khách về trạng thái chưa nối.
- [x] 4b.3 Router + template (khách gửi yêu cầu, lễ tân duyệt/từ chối/gỡ, caretaker bị 403).
      → verify: luồng HTTP đầu cuối; **khách chưa được nối không thấy dữ liệu của chủ nuôi nào**.
      (Ở đợt 4b chưa có trang dữ liệu nào cho khách, nên vế "không thấy dữ liệu" mới đúng theo cấu trúc; chứng minh thật nằm ở ô 4c.4.)
- [x] 4b.4 Tài liệu + chạy toàn bộ test.

### Đợt 4c — cách ly dữ liệu (thiết kế chốt 02/10)

Khách xem được **dữ liệu của chính mình** (chủ nuôi đã nối): danh sách và chi tiết thú cưng kèm lịch sử tiêm, lịch hẹn, hóa đơn. **Chưa** mở hồ sơ chăm sóc (ghi chú nội bộ của nhân viên) — hỏi lại khi cần.

| # | Vấn đề | Quyết định |
|---|---|---|
| 13 | Kế hoạch gốc: `yeu_cau_so_huu` ném `KhongCoQuyen` (403) | Khách xin id của người khác mà nhận 403 thì **biết id đó tồn tại**. Trả **404** giống hệt id không có thật, bằng `LoiKhongTimThay` sẵn có |
| 14 | Kế hoạch gốc: phép canh bắt "mọi handler đi qua hàm đó" | Handler không nên chạm CSDL. Router khách-dữ-liệu **chỉ gọi** `app/services/khach_du_lieu.py`; phép canh AST: (a) router đó không import model và không gọi `db.*`; (b) **mọi hàm công khai** của service nhận `khach` và gọi `yeu_cau_so_huu`/`ma_chu_nuoi`; (c) mọi route `/khach/*` ngoài danh sách trang đăng nhập/đăng ký công khai đều phụ thuộc `khach_hien_tai` |

- [x] 4c.1 `app/services/khach_du_lieu.py` + `yeu_cau_so_huu()` (một điểm chặn) + test đơn vị (chủ đúng, chủ khác, chưa nối).
      → verify: đột biến bỏ lượt kiểm ở từng hàm → đúng test đỏ.
- [x] 4c.2 Router `khach_du_lieu.py` + template + menu khách.
- [x] 4c.3 Phép canh trong `test_architecture.py`.
      → verify: đột biến (thêm `db.get` vào router khách, bỏ `yeu_cau_so_huu` khỏi một hàm, thêm route khách không có `khach_hien_tai`) → phép canh đỏ.
- [x] 4c.4 Quét IDOR: mọi đường dẫn theo id của cổng khách với id của người khác, id không tồn tại, khách chưa nối, chưa đăng nhập.
      → verify: **không bao giờ 200, không bao giờ 500**; hai mã 404 giống hệt nhau.
- [x] 4c.5 Tài liệu + chạy toàn bộ test.

## Kết quả đợt 4b và 4c (02/10/2026)

Unit + integration: **xem con số đo cuối ở log phiên [`2026-10-02-01.md`](../sessions/2026-10-02-01.md) Phần 10** (sau 4b: 1198 passed, 1 skipped). Test mới của 4c:
`test_khach_du_lieu_service.py` 28, `test_khach_du_lieu.py` 24, `test_architecture.py` +4 (ba phép canh AST và một ca đối chứng).

Đột biến (đã hoàn nguyên, đã xác nhận đột biến vào file): ở service, bỏ so sánh chủ / bỏ chặn ở từng hàm theo id / đổi 404 thành thông điệp khác / bỏ lọc chủ ở ba danh sách / đảo thứ tự → đúng test đỏ.
Ở router + template + phép canh: thêm `import app.models`, thêm `db.get`, bỏ `khach_hien_tai` ở route dữ liệu và route khác, lộ `note`/tên nhân viên/địa chỉ vào template, đổi 404 thành 403, link trang lỗi về `/`, menu luôn hiện link dữ liệu → đỏ.
**Một đột biến sống sót lần đầu ở tầng HTTP:** danh sách lịch hẹn lấy cả của chủ khác (`Pet.owner_id > 0`) vì test HTTP chỉ khẳng định "có thú cưng của mình" mà không khẳng định "không có của người khác"; tầng unit đã bắt, nhưng thêm khẳng định vào test HTTP rồi giết lại. Ba đột biến sống sót ở service đều tương đương về nghĩa (xem log phiên).

## Giới hạn đã biết (đợt 4b, 4c)

- Khách bị từ chối có thể gửi lại yêu cầu không giới hạn lần (mỗi lần chỉ một yêu cầu chờ); chưa có giới hạn tần suất riêng cho việc này.
- Cổng khách **chỉ xem**: chưa đặt lịch (chặng 5–6); chưa mở hồ sơ chăm sóc (ghi chú nội bộ của nhân viên), cần hỏi lại trước khi mở.
- Các trang dữ liệu của khách tối giản: chưa phân trang, chưa lọc.
- Phép canh `TRANG_KHACH_CONG_KHAI` là danh sách trắng viết tay: thêm trang công khai mới thì phải thêm vào đó có chủ đích.
- Lễ tân đối chiếu bằng số điện thoại + ghi chú do khách tự khai; sai sót của lễ tân khi duyệt nhầm hồ sơ là rủi ro con người, hệ thống chỉ chặn hồ sơ đã thuộc khách khác.

## Kết quả đợt 4a (02/10/2026)

Unit + integration **1141 passed, 1 skipped, 63,32 giây** (trước đợt: 1083 passed). Test mới: `test_customers_service.py` 21, `test_khach_auth.py` 28,
`test_email_tokens_service.py` +2 (`con_hieu_luc`), `test_khoi_dong.py` +4 (luật công khai). Đột biến đã làm và hoàn nguyên; hai đột biến sống sót lần đầu
(bộ đếm quên mật khẩu chưa có test; `client.get(...).status_code == 200` theo redirect nên đỏ-giả) đều đã thêm test/`follow_redirects=False` và giết lại.

## Giới hạn đã biết (đợt 4a)

- Độ trễ gửi mail có thể lộ email đã tồn tại hay chưa (phản hồi giống hệt nhưng thời gian khác nhau).
- Chỉ giới hạn theo IP, chưa theo email: kẻ đổi IP vẫn dồn được thư vào một hộp thư; sau NAT dùng chung thì khách hợp lệ chịu chung bộ đếm.
- Đăng nhập với email không tồn tại không băm giả → thời gian phản hồi khác nhẹ (giống đăng nhập nhân viên).
- Bộ đếm nằm trong bộ nhớ: khởi động lại là mất, nhiều worker thì mỗi worker một bộ.
- `SmtpMailer` chưa thử với nhà cung cấp thật; job CI `docker` chưa chạy trên GitHub.
- ~~Trang `/khach` mới chỉ chào~~ — đã xử lý ở 4b + 4c.
- `python run.py --public-url` giờ đòi `MAIL_PROVIDER=smtp` + `SMTP_*` trong `.env` mới khởi động được.

## Ngoài phạm vi chặng này

Trạng thái `pending`, khung trống, đặt lịch của khách (chặng 5–6); AI cho khách (chặng 7); giới hạn gửi mail theo email; xác thực hai bước.
