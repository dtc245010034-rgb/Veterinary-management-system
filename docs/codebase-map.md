# Bản đồ mã nguồn

> **File này bắt buộc cập nhật mỗi khi thêm, xóa hoặc đổi vai trò một file.** Đây là thứ đầu tiên
> agent đọc ở mỗi phiên làm việc (xem [`../CLAUDE.md`](../CLAUDE.md) mục 6). Bản đồ lệch thực tế thì
> phiên sau sẽ làm việc dựa trên thông tin sai.

**Cập nhật lần cuối:** 2026-09-24 (phiên 24/09 — dọn việc tồn, mở P8 phần kiểm chứng được, **sửa M-06 giờ mở cửa**) · **Trạng thái:** **P0→P7 xong cả tám phase; P8 đang làm.** **797 test xanh.** Tiến độ từng phase: [`roadmap.md`](roadmap.md)

> **Làm tiếp — theo thứ tự:**
> 1. **P8 — phần còn lại đều cần người dùng hoặc cần bạn quyết.** Ba ô smoke P8 đã có bằng chứng
>    kiểm chứng bằng lệnh (xem log phiên 24/09) nhưng **agent không tick** — ô smoke là việc bấm tay.
>    Ba ô còn lại: dựng lại trên máy sạch · ma trận hết ô ⬜ (phụ thuộc chính TC-102) · dán output
>    cuối cùng vào báo cáo. **Việc lớn chưa bắt đầu: README hoàn chỉnh, báo cáo cuối kỳ, slide,
>    CI GitHub Actions.**
> 2. **10 lỗi còn lại** của
>    [`testing/reports/2026-09-19-ra-luong-P1-P7.md`](testing/reports/2026-09-19-ra-luong-P1-P7.md):
>    M-03 (giới hạn độ dài câu hỏi AI), M-05 (kiểm SĐT/email), M-07 (cảnh báo SĐT trùng), L-01 → L-07,
>    và **D-02**. **L-01 đã tái hiện bằng ảnh 20/09**: lễ tân thiếu thẻ Dịch vụ; chăm sóc thiếu thẻ
>    Chủ nuôi và Dịch vụ. **Hỏi trước rồi mới sửa** — mỗi lỗi phải có test đỏ-trước và đột biến.
> 3. **Một việc kiểm còn nợ:** M-08 (tin nhắc tiêm lặp khuyến cáo) mới kiểm ở mức **prompt**, chưa
>    chạy với Gemini thật — chế độ `fake` không tự sinh câu khuyến cáo nên không dựng lại được cảnh
>    lặp. Muốn chắc thì chạy một lượt nhắc lịch tiêm với Gemini thật (tốn 1 lượt quota).
>
> **Đã đóng 24/09:** **M-06 (= S6) — giờ mở cửa**: cả buổi phải nằm trọn trong 08:00–18:00 cùng một
> ngày, áp cho cả `dat_lich` lẫn `doi_lich`, cộng cận trên thời lượng dịch vụ ở `catalog` (TC-122,
> 15 test, 4 lượt đột biến). Cộng việc P6 để lại (form đặt lịch trên CSDL trống nay nói rõ còn thiếu gì — TC-121)
> và ba biến `AI_*` thiếu trong `.env.example` mà kế hoạch P7 đã tick nhầm là xong. Thêm **phép canh
> thứ 50**: mọi biến trong `config.py` phải có mặt trong `.env.example`.
>
> **Trạng thái máy:** `petcare.db` **sạch** — 2 hóa đơn, **không nợ âm**, không bản ghi rác. Rà 24/09:
> **29 bản ghi `ai_logs`, không bản ghi nào chứa SĐT/email/địa chỉ chủ nuôi.** Bản sao lưu ở
> `petcare.truoc-khoi-phuc-2026-09-20.db` và `petcare.backup-2026-09-19.db` (cả hai **không vào git**).
> `.env` đang `AI_PROVIDER=gemini`. **Đã push tới `abd4b8c` ngày 24/09 — không còn commit nào tồn ở máy**; kiểm lại trên remote: không có `.env` và không có file `.db` nào.
>
> **Đọc để lấy lại ngữ cảnh:** [`sessions/2026-09-24-01.md`](sessions/2026-09-24-01.md) (phiên gần
> nhất) → [`sessions/2026-09-20-05.md`](sessions/2026-09-20-05.md) (bốn phần) →
> [`sessions/2026-09-19-01.md`](sessions/2026-09-19-01.md) (năm phần, nền của mọi quyết định hiện tại).

### `app/ai/` — tầng AI, từ P7

| File | Vai trò |
|---|---|
| `ai/provider.py` | Interface `AIProvider` + sáu lớp lỗi đã phân loại (lớp gốc `LoiAI`, `LoiQuaTai`, `LoiKetNoi` — mất mạng, không tính lượt — `LoiHetQuota`, `LoiModelKhongCo`, `LoiCauHinh`). Phân loại lỗi là điều kiện để xoay ca model |
| `ai/gemini.py` | Một lần gọi REST `generateContent` qua `urllib`, không thêm thư viện. Đọc `details` của lỗi 429 để phân biệt hết lượt **theo phút** và **theo ngày**; tách lỗi không kết nối được (`LoiKetNoi`) khỏi timeout; gửi `thinkingBudget` theo cấu hình |
| `ai/fake.py` | `FakeProvider`: ghi lại mọi `(model, system, user)`, cài được phản hồi và lỗi **theo từng model** — nền tảng của test xoay ca và test US-28. `tinh_quota` mặc định `True` (đóng vai Gemini trong test); chế độ fake của ứng dụng dùng `tinh_quota=False` |
| `ai/prompts.py` | `DISCLAIMER`, ba system prompt, câu từ chối thuốc, câu nhắc xác nhận lịch tiêm, các hàm dựng prompt. Thuần, không chạm CSDL |
| `ai/guardrail.py` | `la_cau_xin_thuoc()` (chặn trước khi gọi), `chua_lieu_luong()` (soát phản hồi), `xoa_lien_he()` (bỏ SĐT/email khỏi văn bản tự do). So theo **từ nguyên vẹn** trên chuỗi đã bỏ dấu |
| `ai/quota.py` | Ngày quota theo **giờ Pacific**, luật xoay ca model, đếm lượt, bảng quota, `goi_co_xoay()`. Kèm CLI `python -m app.ai.quota` (`--hoi`, `--guardrail`, `--model`, `--dat-lai`) |
| `ai/service.py` | Ba tính năng AI + `lay_provider()`. **Cửa duy nhất router được import** — có phép canh trong `test_architecture.py` |

---

## Hiện có

### Gốc dự án

| File | Vai trò |
|---|---|
| `CLAUDE.md` | Nguyên tắc làm việc + ngữ cảnh dự án + quy trình mỗi phiên + luật kiểm thử |
| `đề-bài.md` | Đề bài gốc của môn học. **Không sửa** |
| `README.md` | Giới thiệu, cách chạy, cách chạy test |
| `.gitignore` | Bỏ qua `.venv`, `__pycache__`, `*.db`, `.env`, `.claude/settings.local.json` |
| `.env.example` | Mẫu biến môi trường: khóa, **danh sách model Gemini**, ước tính hạn mức, `GEMINI_THINKING_BUDGET`, ngân sách thời gian mỗi lượt gọi AI. `.env` thật không vào repo. Có phép canh: mọi biến trong `config.py` phải có mặt ở đây |

### `.claude/` — cấu hình agent, nằm trong repo

| File | Vai trò |
|---|---|
| `settings.json` | Đăng ký hook `SessionStart` và `Stop`. **Được commit** |
| `hooks/session-start.ps1` | Tạo `docs/sessions/YYYY-MM-DD-NN.md`, in nhắc nhở, cảnh báo nếu sai thư mục làm việc |
| `hooks/session-stop.ps1` | Chạy sau **mỗi lượt**: xóa **mọi** file log còn rỗng (mọi ngày, không chỉ file mới nhất), nhắc cập nhật codebase-map và checklist plan |

### `docs/`

| File | Vai trò |
|---|---|
| `user-stories.md` | 28 user story, 104 tiêu chí Given/When/Then, bảng đối chiếu với đề bài |
| `erd.md` | 14 bảng, sơ đồ Mermaid, mô tả cột và ràng buộc |
| `architecture.md` | Cây thư mục, ranh giới ba lớp, 3 sequence diagram, cách xử lý lỗi |
| `ai-safety.md` | System prompt 3 tính năng (có phép canh khớp `prompts.py`), `DISCLAIMER`, 20 ca guardrail G-01→G-20, kết quả chạy Gemini thật 19/09 |
| `codebase-map.md` | File này |
| `roadmap.md` | Lộ trình P0→P8 gắn với mốc KT1/KT2/KT3/cuối kỳ, kèm Definition of Done |
| `plans/README.md` | Quy ước lưu kế hoạch đã duyệt |
| `plans/YYYY-MM-DD-<slug>.md` | Một file mỗi kế hoạch đã duyệt, kèm checklist tick trong lúc làm. Hiện có 17: KT1/P0, P1, P2a, P2b, P3, P4, P5, e2e xuyên suốt, trả nợ kiến trúc, P6, dọn việc tồn P6, P7, rà soát P1→P7, sửa lỗi cao sau rà soát, chế độ AI giả lập, vá dữ liệu và sửa 4 lỗi ưu tiên (20/09), M-06 giờ mở cửa (24/09) |
| `sessions/README.md` | Quy ước log phiên làm việc |
| `sessions/YYYY-MM-DD-NN.md` | Một file mỗi phiên chat, hook tạo khung sẵn. Hiện có 14 |
| `testing/test-strategy.md` | 4 tầng test, 3 luật chống test giả, fixture, kịch bản e2e |
| `testing/test-cases.md` | Ma trận truy vết US → TC → file test, 122 test case — 120 ✅ · 0 🟡 · 1 ⬜ (TC-102 smoke) · 1 ➖ ngoài phạm vi (24/09 thêm TC-121 việc P6 để lại và TC-122 giờ mở cửa; 20/09 thêm TC-117 → TC-120) |
| `testing/smoke-checklist.md` | Checklist bấm tay theo từng phase |
| `testing/reports/README.md` | Mẫu báo cáo kiểm thử cuối phase |
| `testing/reports/YYYY-MM-DD-Pn.md` | Một file mỗi phase, chứa output pytest thật. Hiện có 25: mỗi phase một file, cộng sáu báo cáo rà luồng bằng trình duyệt (bản 19/09 kèm ảnh trong `anh-2026-09-19/`), một báo cáo rà bổ sung bằng HTTP (20/09, bốn phần lượt 19/09 chưa chạm), một báo cáo rà bằng Chrome trước khi sửa (20/09), một báo cáo trả nợ, một báo cáo dọn việc tồn và một báo cáo chạy Gemini thật (sinh bởi `python -m app.ai.quota --guardrail`) |

### Ứng dụng (`app/`) — từ P1

| File | Vai trò |
|---|---|
| `main.py` | Khởi tạo FastAPI, session middleware, đăng ký router, **từ chối khởi động khi `SECRET_KEY` còn mặc định** (S1), 3 trình xử lý lỗi (403/404 ra trang có bố cục, chưa đăng nhập thì chuyển về `/login`, `LoiNghiepVu` lọt khỏi router → trang 404/400 thay vì 500 — H-03) |
| `config.py` | Đọc `.env` qua pydantic-settings: `DATABASE_URL`, `SECRET_KEY`, `AI_PROVIDER`, `GEMINI_API_KEY`. Hằng `SECRET_KEY_MAC_DINH` để `main.py` chặn khởi động với khóa công khai (S1) |
| `db.py` | `Base`, `engine`, `SessionLocal`, `get_db()`. Bật `PRAGMA foreign_keys` cho từng kết nối SQLite |
| `security.py` | `hash_password()`, `verify_password()` — bcrypt trực tiếp, không qua passlib |
| `app/auth.py` | Session cookie, `nguoi_dung_hien_tai`, `yeu_cau_vai_tro()`, ngoại lệ `ChuaDangNhap`. Ghi kèm thư mục để không lẫn với `routers/auth.py` |
| `templates.py` | Cấu hình Jinja2 dùng chung, filter `tien` (`{{ so|tien }}`), và hàm `che_do_ai_gia_lap()` cho template biết đang chạy `AI_PROVIDER=fake` |
| `seed.py` | 4 tài khoản, 3 chủ nuôi, 5 thú cưng, 5 dịch vụ, 2 gói, 8 lịch hẹn, 3 hồ sơ chăm sóc, 5 mũi tiêm, 2 hóa đơn, 2 lần thanh toán. Hóa đơn và lần trả mang **ngày của buổi chăm sóc** (lập trong `clock.freeze`), không phải ngày chạy seed. Hóa đơn dựng **qua `billing.py`** chứ không gán trạng thái tay. Chạy `python -m app.seed`, không sinh trùng |
| `models/__init__.py` | Gom mọi model — `create_all` chỉ tạo bảng đã được import |
| `models/user.py` | Bảng `users` + hằng `VAI_TRO`, `TEN_VAI_TRO` |
| `models/ai_log.py` | Bảng `ai_logs` — nhật ký gọi AI. Cột `model` NULL nghĩa là **không có lời gọi nào đi ra** (guardrail chặn trước hoặc thiếu dữ liệu) |
| `models/ai_quota.py` | Bảng `ai_quota` — lượt đã dùng, hạn mức thật, trạng thái nghỉ/hết lượt/bị tắt của từng model theo từng ngày quota |
| `models/owner.py` | Bảng `owners`. `search_name` tự đồng bộ qua `@validates` |
| `models/pet.py` | Bảng `pets`. CHECK `weight_kg > 0`; ngày sinh kiểm ở tầng services |
| `models/service.py` | Bảng `services`. `price` kiểu `Numeric(12,2)`, **không** `Float` |
| `models/service_package.py` | `service_packages` + `package_items`, property `tong_gia_le`, `tiet_kiem` |
| `models/appointment.py` | Bảng `appointments`, hằng `TRANG_THAI`, 2 index phục vụ kiểm trùng |
| `services/clock.py` | `now()` và `freeze()` — điểm lấy thời gian duy nhất của hệ thống. `freeze()` dùng khi test và ở `seed.py` |
| `services/text.py` | `chuan_hoa()` — bỏ dấu tiếng Việt cho tìm kiếm, xử lý riêng chữ `đ` |
| `services/errors.py` | `LoiNghiepVu` — lỗi nghiệp vụ, thông điệp hiển thị thẳng cho người dùng. Lớp con `LoiKhongTimThay` cho mọi lần tra theo id không thấy bản ghi (H-03) |
| `models/care_record.py` | Bảng `care_records` — hồ sơ chăm sóc, quan hệ 1–1 với lịch hẹn (`appointment_id` UNIQUE) |
| `models/vaccination.py` | Bảng `vaccinations` — mũi tiêm và hạn nhắc lại; property `qua_han` |
| `services/users.py` | Nghiệp vụ tài khoản nhân viên: tạo, **sửa**, khóa, mở khóa, danh sách, **đặt lại và tự đổi mật khẩu**. Chặn quản lý tự khóa mình và tự bỏ vai trò quản lý. `kiem_mat_khau()` là cửa chung của **cả ba** đường đặt mật khẩu (M-04) |
| `services/owners.py` | Nghiệp vụ chủ nuôi và thú cưng: tạo, sửa, xóa, tra cứu |
| `services/catalog.py` | Nghiệp vụ dịch vụ và gói. `danh_sach_dang_ban()` là danh sách P3 và P5 sẽ dùng. Thời lượng có **cận trên** `PHUT_LAM_VIEC_MOI_NGAY` nhập từ `scheduling` — nhập một hằng số chứ không gọi hàm, nên hai service vẫn tách ra được (M-06) |
| `services/care_records.py` | Nghiệp vụ hồ sơ chăm sóc. Thao tác **duy nhất** đưa lịch hẹn về `done` |
| `services/scheduling.py` | **Quy tắc chống trùng lịch**, **luật giờ mở cửa** (`_kiem_gio_lam_viec` — cả buổi phải nằm trọn trong `GIO_MO_CUA`–`GIO_DONG_CUA` cùng một ngày, áp cho cả đặt lẫn đổi lịch; M-06 sửa 24/09), đặt/đổi/hủy lịch, gợi ý khung trống, `so_lich_chua_lam_theo_nhan_vien()` cho cảnh báo nhân viên đã khóa (S4). Đổi lịch kiểm nhân viên **cả khi giữ nguyên người**. Khoảng nửa mở `[start, end)`. Hủy lịch còn chặn khi lịch đang có hóa đơn chưa hủy (US-21) — biết model `Invoice`, không gọi sang `billing.py` |
| `services/vaccinations.py` | Nghiệp vụ tiêm phòng: ghi mũi, hồ sơ tiêm, danh sách đến hạn. Chỉ tính mũi mới nhất của mỗi loại vắc-xin; tên vắc-xin gõ khác hoa thường/dấu được quy về tên đã có của chính thú cưng đó (S2) |
| `models/invoice.py` | Bảng `invoices` và `invoice_items`. Hằng `TRANG_THAI_CON_HIEU_LUC` cho `scheduling.py` dùng khi chặn hủy lịch. `unit_price` và `description` **chép** lúc lập, không tham chiếu `services`; property `da_tra`, `con_no` |
| `models/payment.py` | Bảng `payments` — từng lần khách trả; CHECK `amount > 0` |
| `services/billing.py` | Nghiệp vụ hóa đơn: lập, thu tiền, hủy. Đường **duy nhất** ghi `payments` và trạng thái hóa đơn. Lập hóa đơn cho lịch có hóa đơn **đã hủy** thì mở lại chính hóa đơn đó theo giá và ngày hiện tại (S4 → S3 trong kế hoạch P7) |
| `services/stats.py` | Thống kê theo kỳ: `thong_ke()`, `ky_mac_dinh(den_ngay)`. Có `so_lich_qua_gio_chua_ghi` — lịch đã qua giờ mà chưa ai ghi hồ sơ (S5). Ba mốc ngày cố ý khác nhau — lượt và khách theo ngày hẹn (mọi lịch chưa hủy), doanh thu theo ngày thu (`payments`), chưa thu theo ngày lập. Tính trong Python để dùng lại `Invoice.con_no`; **không** lọc dịch vụ đã ngưng bán |
| `routers/auth.py` | `/login`, `/logout`, `/`, và `/doi-mat-khau` — tự đổi mật khẩu đặt ở đây vì cả ba vai trò đều dùng được, trong khi cả router `/users` chặn người không phải quản lý |
| `routers/users.py` | `/users` — quản lý tài khoản, chỉ vai trò `manager`. Thêm `/{id}/sua` và `/{id}/dat-lai-mat-khau` (M-02, 20/09). Chỉ HTTP, nghiệp vụ ở `services/users.py` |
| `routers/owners.py` | `/owners`, `/owners/{id}`, `/owners/{id}/sua`, `/owners/{id}/pets`, `/pets/{id}/xoa`. Hai đường dẫn xóa có **GET trang xác nhận** và POST làm việc thật — GET không đổi dữ liệu |
| `routers/services.py` | `/services` và `/services/goi` — chỉ `manager` sửa |
| `routers/care_records.py` | `/appointments/{id}/ho-so` — ghi và xem hồ sơ chăm sóc |
| `routers/pets.py` | `/pets/{id}` — trang chi tiết thú cưng, gộp lịch sử chăm sóc và hồ sơ tiêm (TC-020); `/pets/{id}/sua` (M-02) đặt ở đây để lỗi render lại đúng trang người dùng đang đứng; dùng chung `doc_ngay_form`/`doc_so_form` của `routers/owners.py` |
| `routers/vaccinations.py` | `/vaccinations` danh sách đến hạn; `/pets/{id}/vaccinations` ghi mũi tiêm |
| `routers/invoices.py` | `/invoices` danh sách, `/invoices/{id}` chi tiết, thu tiền, hủy hóa đơn. Cả router chặn `caretaker`. `GET /invoices/{id}/huy` là trang xác nhận, `POST` cùng đường dẫn mới hủy thật |
| `routers/stats.py` | `/stats?tu_ngay=&den_ngay=` — cả router chỉ `manager` (TC-006). Ô ngày trống → kỳ mặc định, tính lùi từ "Đến ngày" nếu đã chọn; ngày sai dạng → trang báo lỗi 400 tiếng Việt, giữ ngày đã nhập |
| `routers/ai.py` | `/ai/...` — soạn tin nhắc, tóm tắt, hỏi đáp, trang kết quả dùng chung, trang quota (chỉ `manager`). Theo mẫu **Post/Redirect/Get**: tải lại trang kết quả không gọi AI lần nữa. Chỉ import `app/ai/service.py`. `_quay_lai()` bỏ ký tự điều khiển rồi mới xét, và coi `\` ngang `/` (M-01) |
| `routers/appointments.py` | `/appointments` lưới lịch + đặt/đổi/hủy; `/appointments/cua-toi` lịch riêng của nhân viên chăm sóc |
| `templates/base.html` | Bố cục chung, menu hiện theo vai trò |
| `templates/_ai_gia_lap.html` | Dòng cảnh báo "Đang chạy chế độ AI giả lập", `include` vào ba trang AI. Có từ 19/09 sau khi người dùng tưởng câu mẫu của `fake` là Gemini trả lời sai |
| `templates/xac_nhan.html` | Trang hỏi lại dùng chung cho mọi thao tác làm mất dữ liệu. Nhận `tieu_de`, `thong_tin`, `canh_bao`, `hanh_dong` (URL POST), `quay_lai`, `nut`. Cố ý không dùng `confirm()` của JavaScript |
| `templates/login.html` · `home.html` · `users.html` · `error.html` | Các trang từ P1. `users.html` từ 20/09 có ô sửa họ tên + vai trò ngay trên dòng và ô đặt lại mật khẩu (M-02) |
| `templates/doi_mat_khau.html` | Trang tự đổi mật khẩu, mở cho **mọi vai trò** (M-02, 20/09). Bắt nhập mật khẩu hiện tại — khác đường "quản lý đặt lại" ở `/users` |
| `templates/owners.html` | Danh sách, tra cứu, form thêm chủ nuôi |
| `templates/owner_detail.html` | Chi tiết chủ nuôi, danh sách thú cưng, form thêm thú cưng |
| `templates/services.html` | Bảng giá, gói dịch vụ, form thêm dịch vụ và tạo gói |
| `templates/care_record_form.html` | Form ghi hồ sơ, hoặc nội dung hồ sơ đã ghi |
| `templates/pet_detail.html` | Trang chi tiết thú cưng: lịch sử chăm sóc + hồ sơ tiêm + form ghi mũi tiêm |
| `templates/vaccinations.html` | Danh sách đến hạn tiêm, có nhãn **Quá hạn** và dòng khuyến cáo bác sĩ thú y |
| `templates/invoices.html` | Danh sách hóa đơn, chưa thu lên đầu |
| `templates/invoice_detail.html` | Chi tiết hóa đơn: các dòng, lịch sử thanh toán, form thu tiền, nút hủy |
| `templates/ai_ket_qua.html` | Trang kết quả dùng chung cho ba tính năng. Nhắc lịch có ô sửa + nút Chốt + nút Sao chép; khuyến cáo đặt **trên** nội dung nên hiện cả khi AI lỗi |
| `templates/ai_hoi_dap.html` | Ô hỏi đáp, chặn bấm đúp bằng JS |
| `templates/ai_quota.html` | Bảng lượt gọi từng model cho quản lý, kèm nút đặt lại trạng thái |
| `templates/stats.html` | Form chọn kỳ, bốn thẻ số (lượt, doanh thu, chưa thu, tỉ lệ quay lại), bảng theo dịch vụ, trạng thái rỗng; một dòng giải thích ba mốc ngày |
| `templates/appointments.html` | Lưới lịch, form đặt lịch, cột thao tác đổi/hủy, khung trống khi bị từ chối. Dùng chung cho `/appointments` và `/appointments/cua-toi` |
| `static/style.css` | Toàn bộ CSS, một file, không build tool |

### Kiểm thử (`tests/`) — từ P1

| File | Vai trò |
|---|---|
| `conftest.py` | 5 fixture: `db`, `client`, `frozen_clock`, `fake_ai` (khung, dùng từ P7), `seed_basic` (chỉ 4 tài khoản); cộng `bam_mat_khau_mau` băm mật khẩu mẫu một lần cho cả phiên test |
| `unit/test_security.py` | Băm mật khẩu (TC-005) |
| `unit/test_clock.py` | Cố định thời gian |
| `unit/test_models_user.py` | Ràng buộc bảng `users`: UNIQUE username, CHECK role |
| `unit/test_text.py` | Chuẩn hóa chuỗi tiếng Việt, gồm bẫy chữ `đ` |
| `unit/test_models_owner_pet.py` | Ràng buộc `owners`, `pets`, khóa ngoại, `search_name` |
| `unit/test_users_service.py` | Nghiệp vụ tài khoản: tạo, băm mật khẩu, trùng username, chặn tự khóa |
| `unit/test_architecture.py` | **Canh ranh giới dự án** (50 phép canh), không kiểm chức năng: router không ghi thẳng CSDL, `services/` không import fastapi, router không import thẳng `app/ai`, mọi loại ô nhập dùng chung quy tắc khung, link tài liệu, `erd.md` khớp model tới từng cột (tập cột, NOT NULL, UNIQUE, FK), `codebase-map` đủ file (so **đuôi đường dẫn**, không so mỗi tên file — xem kẽ hở đã vá 13/09), hàm public có test gọi thẳng, class trong template có quy tắc CSS, chuỗi trạng thái tiền chỉ nằm ở model và service hóa đơn, thông báo lỗi không lộ mã phase, link menu nào cũng có thẻ trên trang chủ, dòng Trạng thái trong README khớp phase mới nhất, số kế hoạch/log phiên/báo cáo ghi trong chính file này khớp số file thật, ba system prompt in trong `ai-safety.md` khớp từng chữ với `prompts.py`, mọi biến trong `config.py` đều có mặt trong `.env.example` |
| `unit/test_khoi_dong.py` | Lifespan từ chối khởi động với `SECRET_KEY` mặc định (S1). Gọi thẳng `lifespan`, engine in-memory |
| `unit/test_prompts.py` | Dựng prompt, ba system prompt, chèn `DISCLAIMER` (TC-082, 083, 088, 096) |
| `unit/test_guardrail.py` | Ba phép chặn trong code, nặng về **ca âm**: "nhân viên" không được coi là hỏi liều (TC-093) |
| `unit/test_ai_service.py` | Ba tính năng AI ở tầng nghiệp vụ, lọc dữ liệu cá nhân, ghi `ai_logs` (TC-082→098) |
| `unit/test_ai_quota.py` | Xoay ca model, ngày quota theo giờ Pacific, đếm lượt, bảng quota (TC-103→112) |
| `unit/test_gemini.py` | Đọc phản hồi và phân loại lỗi HTTP; chỉ thay `urlopen` — ranh giới ngoài |
| `unit/test_hooks.py` | Chạy thật hook `session-stop.ps1` trên bản sao dựng trong thư mục tạm: mọi log rỗng bị dọn, log đã điền (kể cả điền dở) còn nguyên. Tự bỏ qua khi máy không có PowerShell |
| `unit/test_owners_service.py` | Nghiệp vụ chủ nuôi, thú cưng, tra cứu |
| `unit/test_models_service.py` | Ràng buộc `services`, gói, và **kiểu tiền `Decimal`** |
| `unit/test_catalog_service.py` | Nghiệp vụ dịch vụ, ngưng bán, gói |
| `unit/test_models_appointment.py` | Ràng buộc `appointments`: `end_at > start_at`, CHECK trạng thái |
| `unit/test_models_care_record.py` | Ràng buộc CSDL của `care_records` |
| `unit/test_models_vaccination.py` | Ràng buộc CSDL của `vaccinations`: CHECK `dose_no > 0`, `next_due_at >= given_at` |
| `unit/test_care_records_service.py` | Nghiệp vụ hồ sơ chăm sóc, lịch sử, ba trường suy từ lịch hẹn |
| `unit/test_vaccinations_service.py` | Nghiệp vụ tiêm phòng, ranh giới ngày, luật "chỉ tính mũi mới nhất" (TC-059→062) |
| `unit/test_billing_service.py` | Nghiệp vụ hóa đơn và thanh toán, gồm ca đổi giá dịch vụ không làm đổi hóa đơn cũ (TC-065→073) |
| `unit/test_stats_service.py` | Thống kê: TC-076 → TC-081, bất biến "bảng theo dịch vụ cộng lại bằng tổng", mốc ngày đầu/cuối kỳ, hóa đơn lập kỳ trước thu kỳ này, dịch vụ đã ngưng bán, kỳ mặc định. Dữ liệu đi qua luồng thật: đặt lịch → ghi hồ sơ → lập hóa đơn → thu tiền |
| `unit/test_scheduling.py` | **6 ca biên trùng lịch**, gợi ý khung trống, đổi lịch (TC-044→047), hủy lịch (TC-048, TC-049), chặn hủy lịch còn hóa đơn (TC-074, TC-075) |
| `integration/test_auth.py` | Đăng nhập (TC-001→004) |
| `integration/test_users.py` | Phân quyền và quản lý tài khoản (TC-007, 008, 010→012) |
| `integration/test_owners.py` | Chủ nuôi, thú cưng, tra cứu qua HTTP (TC-013→023) |
| `integration/test_services.py` | Dịch vụ, bảng giá, gói qua HTTP (TC-024→031) |
| `integration/test_care_records.py` | Ghi hồ sơ và trang thú cưng qua HTTP (TC-053, TC-054, TC-057, TC-058) |
| `integration/test_vaccinations.py` | Ghi mũi tiêm, danh sách đến hạn, link menu, khuyến cáo bác sĩ (TC-059, TC-063, TC-064, TC-020) |
| `integration/test_invoices.py` | Hóa đơn qua HTTP: nút trên lưới lịch, thu tiền, hủy, phân quyền (TC-065, TC-068→070, TC-072) |
| `integration/test_ai.py` | Ba tính năng AI qua HTTP: phân quyền, Post/Redirect/Get, AI lỗi không vỡ trang, `ai_logs` sạch dữ liệu liên hệ (TC-084→100) |
| `integration/test_stats.py` | Trang thống kê qua HTTP: TC-006 và lễ tân → 403, kỳ mặc định, kỳ trống, ngày ngược, ngày sai định dạng |
| `integration/test_seed.py` | Chạy `python -m app.seed` trong tiến trình riêng trên CSDL tạm; ngày lập hóa đơn = ngày buổi chăm sóc, ngày thu = ngày lập |
| `integration/test_khong_tim_thay.py` | Quét mọi đường dẫn theo id với bản ghi không tồn tại: không bao giờ 500; chín chỗ từng lỗi phải ra 404 (TC-115, H-03) |
| `integration/test_appointments.py` | Đặt/đổi/hủy lịch qua HTTP, lịch theo vai trò (TC-035, TC-043, TC-050→052, TC-009) |
| `e2e/test_full_flow.py` | **Kịch bản xuyên suốt TC-101 đủ 11 bước** trên CSDL file thật, đi bằng link và nút lấy từ HTML — không tự dựng URL. Chứa `TrinhDuyet`, trình duyệt tí hon gửi form đúng như trình duyệt |

### Cấu hình

| File | Vai trò |
|---|---|
| `requirements.txt` | Phụ thuộc, đã pin phiên bản. Có `tzdata` vì Windows không sẵn dữ liệu múi giờ, mà quota reset theo giờ Pacific |
| `pytest.ini` | `pythonpath`, `testpaths`, `filterwarnings = error` |

---

## Chưa có — sẽ thêm theo phase

Cấu trúc dưới đây theo [`architecture.md`](architecture.md). Khi một file được tạo, chuyển nó lên
mục "Hiện có" và ghi rõ vai trò thật, rồi xóa dòng ở đây.

| Đường dẫn | Vai trò dự kiến | Phase |
|---|---|---|
| ~~`app/schemas/`~~ | **Bỏ.** Qua P1→P3 form đọc thẳng bằng `Form()` và kiểm ở `services/` là đủ; thêm một tầng Pydantic nữa chỉ để lặp lại phép kiểm đã có | — |
