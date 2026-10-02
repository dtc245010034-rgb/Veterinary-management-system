# Kế hoạch P9 — Cổng khách hàng, đóng gói, và làm lại đặc tả

**Trạng thái: ĐÃ DUYỆT 02/10/2026** (người dùng: "Commit và push và duyệt P9"). Chặng 0 và 1 xong; chặng 2 xong về code (còn ô 2.2: job CI `docker` chờ chạy trên GitHub); chặng 3 xong về code (02/10, xem [kế hoạch chặng 3](2026-10-02-p9-chang3-email.md)); chặng 4 là việc kế tiếp. Viết sau buổi giảng viên kiểm tra tiến độ
ngày 25/09. Mười quyết định bên dưới đã được người dùng trả lời qua hai vòng hỏi; kế hoạch này là
bản chốt lại để người dùng duyệt trước khi gõ dòng code đầu tiên.

---

## 1. Bốn nhận xét của giảng viên, và phản biện có bằng chứng

### 1.1 "Đặc tả gộp hết vào một file" — **đúng, sửa**

`docs/user-stories.md` hiện là **một file, 28 user story, 118 tiêu chí**. Mỗi US có mục tiêu
(*"Là… tôi muốn… để…"*) và các dòng `Given/When/Then`, nhưng **điều kiện biên bị trộn lẫn** vào
cùng danh sách tiêu chí, không tách ra. Nhận xét chính xác.

### 1.2 "Không phải lập trình hướng đối tượng" — **sai về mặt sự kiện**

`app/` có **35 class**, gồm đúng những thứ dùng để chấm OOP:

| Khái niệm OOP | Hiện thân trong dự án |
|---|---|
| Đa hình / mẫu Strategy | `AIProvider` (Protocol) ← `GeminiProvider`, `FakeProvider` — chính nó cho phép 906 test chạy offline |
| Kế thừa nhiều tầng | `LoiAI` ← `LoiQuaTai` ← `LoiKetNoi`, cộng `LoiHetQuota`, `LoiModelKhongCo`, `LoiCauHinh` |
| Đóng gói hành vi trong thực thể | `Invoice.da_tra`, `Invoice.con_no`, `Vaccination.qua_han`, `ServicePackage.tiet_kiem`, `User.ten_vai_tro` |
| Lớp cơ sở chung | `Base(DeclarativeBase)` cho 14 thực thể |

Thứ dự án **cố ý không làm** là bọc quy tắc nghiệp vụ **không có trạng thái** vào class — một class
không giữ state chỉ là namespace có thêm thủ tục, và `CLAUDE.md` mục 2 cấm đúng điều đó.

**Phần công bằng cho giảng viên:** có một lỗ hổng OOP *thật* — mô hình miền đang **thiếu máu**
(anemic domain model), nghiệp vụ nằm ở `services/` dạng hàm còn thực thể chỉ giữ dữ liệu. Nhưng
người dùng đã xác nhận **OOP không phải tiêu chí chấm**, nó chỉ là ví dụ cho *tính mở rộng*. Nên:
**không refactor**, dồn sức vào thứ giảng viên thực sự lo — khả năng mở rộng và đóng gói.

### 1.3 "Đóng khung, mở rộng kém — ví dụ Docker" — **đúng, sửa**

Dự án chỉ chạy được bằng `venv` trên Windows. Đóng gói Docker phục vụ thẳng một mục DoD **đã có
sẵn** của P8: *"Kiểm tra dựng lại hệ thống từ CSDL trống trên máy sạch."* Điều kiện tiên quyết vừa
đạt hôm nay: CI đã chứng minh bộ test chạy được trên Linux.

### 1.4 "Khách phải biết lịch trống trước khi đặt" — **đúng vấn đề, sai cách làm theo nghĩa đen**

Năng lực **đã có**: `scheduling.khung_gio_trong()` (dòng 108). Lỗi nằm ở chỗ nó **chỉ hiện sau khi
đặt lịch bị từ chối** (`routers/appointments.py:216` lấy từ exception).

Nhưng "cho khách xem bảng lịch nhân viên đang có" theo nghĩa đen là **rò dữ liệu**:
`appointments.html` đang render **tên thú cưng, họ tên chủ nuôi, và link tới `/owners/{id}`**. Đưa
nguyên bảng đó cho khách là vi phạm chính yêu cầu *"review dữ liệu cá nhân"* của đề bài mục 6.

→ Người dùng đã chốt: **hiện khung trống theo từng nhân viên**, có tên nhân viên, **không** có bất
kỳ dữ liệu nào của khách khác.

---

## 2. Rủi ro nặng nhất, phát hiện khi hỏi lại — và vì sao phương án tiện nhất bị loại

Người dùng muốn khách **tự đăng ký**. Cách tiện nhất là nối tài khoản mới với hồ sơ chủ nuôi cũ
**theo số điện thoại**. Đã loại, vì:

- `owners.phone` có index nhưng **không UNIQUE**;
- **không có bất kỳ thư viện gửi mail hay SMS nào** trong `requirements.txt` → không xác minh được
  ai là chủ của số đó;
- ⇒ **ai biết số điện thoại của một khách là chiếm được** hồ sơ thú cưng, lịch sử chăm sóc và hóa
  đơn của người đó. Nặng hơn mọi lỗi trong lượt rà 19/09.

Và một dữ kiện nữa làm hỏng cả phương án "xác minh email rồi tự nối": **chỉ 1/4 chủ nuôi trong
`petcare.db` có email**, `seed.py` không đặt email cho ai, vì email là ô không bắt buộc (US-04).

**Kết luận: xác minh email và nối hồ sơ là HAI bài toán khác nhau.**

| Bài toán | Giải bằng |
|---|---|
| "Email này có thật và là của người đăng ký?" | Xác minh email — đồng thời cho luôn kênh quên mật khẩu |
| "Người này là chủ nuôi nào trong shop?" | **Lễ tân duyệt yêu cầu nối** — con người nhận diện, không dựa vào dữ liệu ai cũng đoán được |

---

## 3. Mười quyết định đã chốt

| # | Quyết định |
|---|---|
| 1 | Tách `user-stories.md` thành nhiều file, mỗi US có **Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên** |
| 2 | **Không** refactor OOP — chỉ là ví dụ về mở rộng, không phải tiêu chí chấm |
| 3 | Cổng khách **đầy đủ**: tự đăng ký + đặt lịch + dùng AI |
| 4 | Bảng **khung trống theo từng nhân viên**, hiện **trước** khi đặt |
| 5 | Thêm thư viện gửi email, **xác minh email** khi đăng ký |
| 6 | Nối hồ sơ cũ qua **yêu cầu nối, lễ tân duyệt** |
| 7 | Lịch khách đặt vào trạng thái **chờ duyệt**, **có giữ chỗ**, kèm **hạn tự hủy** và **trần số lịch chờ** |
| 8 | AI cho khách: **chỉ hỏi đáp (US-26)**, có **hạn mức ngày theo tài khoản** |
| 9 | **Docker, giữ SQLite**; ghi rõ đường chuyển PostgreSQL trong tài liệu |
| 10 | Còn nhiều thời gian (>2 tuần) — làm hết, không cắt |

---

## 4. Ranh giới phải giữ

- **Không một route nào của khách được trả dữ liệu của khách khác.** Đây là ranh giới số một.
- **Không gửi mail thật trong test.** Dùng `FakeMailer` — lặp đúng mẫu `AIProvider`/`FakeProvider`
  đã có. Tiện thể: đây là **mẫu Strategy thứ hai**, trả lời luôn nhận xét OOP mà không tốn công.
- **Không sửa test để màu xanh.** Thêm `pending` đụng **37 chỗ** dùng trạng thái lịch hẹn trong
  5 file — soát cả lớp, đúng `CLAUDE.md` mục 9 dòng 4.
- **Bí mật SMTP vào `.env`, không vào repo.** Phép canh `.env.example` (số 50) sẽ bắt nếu thiếu biến.
- **Mỗi bug/hành vi mới phải có test đỏ-trước và một lượt đột biến** — mục 7.
- Đặc tả và `test-cases.md` đi cùng code trong **cùng một chặng**, không để trôi.

---

## 5. Ba đề xuất để làm thông minh hơn, không chỉ làm nhiều hơn

### 5.1 Quyết chuyện fixture test **trước**, không phải sau

Cổng khách sẽ thêm ước chừng **250–350 test**. Bộ test hiện **906 ca, 101–148s**, đã chạm ngưỡng
100s. Thêm 300 ca nữa là **~150–200s**, và lúc đó việc đổi fixture `db` sẽ phải đụng **1200 test**
thay vì 906.

Hướng đã biết từ 11/09 (dựng schema một lần mỗi phiên + rollback từng test, ước giảm ~20s) bị hoãn
**vì lúc đó đang trước P7 — phase khó nhất**. P7 xong rồi, lý do hoãn không còn. **Làm bây giờ rẻ
hơn làm sau.** Đây là ô đầu tiên của kế hoạch, và nó vẫn cần người dùng chốt.

### 5.2 Một điểm chặn quyền sở hữu, có phép canh giữ — thay vì soát tay 50 route

Cách ly dữ liệu theo dòng là chỗ **chắc chắn** sẽ sinh lỗi nếu làm thủ công. Đề xuất theo đúng idiom
của dự án:

- một hàm duy nhất `yeu_cau_so_huu(nguoi_dung, ban_ghi)` ném `KhongCoQuyen`;
- một **phép canh kiến trúc** bắt mọi handler trong `routers/khach/` phải đi qua hàm đó.

Một phép canh thắng năm mươi lượt soát tay. Dự án đã có 55 phép canh, cơ chế này là thứ nó làm tốt
nhất.

### 5.3 Hạn mức AI theo khách: **không cần bảng mới**

`ai_logs` **đã có sẵn `user_id`** (dòng 36). Hạn mức ngày cho từng tài khoản đếm thẳng từ đó:
`count(*) where user_id = ? and created_at >= đầu ngày`. Không thêm bảng, không thêm migration,
và có sẵn nhật ký để đối chiếu khi tranh cãi. `ai_quota` giữ nguyên vai trò đếm theo `(model, ngày)`.

---

## 6. Các chặng

### Chặng 0 — Quyết trước khi gõ code

- [x] 0.1 Chốt hướng xử lý ngân sách thời gian test (xem 5.1). *Người dùng duyệt thứ tự "Phiên 2 = chặng 0" ở kế hoạch 02/10; chốt kỹ thuật: sao ảnh schema thay vì rollback — xem 0.2.*
- [x] 0.2 Nếu chốt đổi fixture `db`: làm ngay trên 906 test, đo trước–sau. *(02/10: đo CPU giảm ~7s/44s; con số "~20s" ở mục 5.1 nói quá — xem log phiên 2026-10-02-01.)*
      → verify: suite xanh đủ 906 ca, ghi lại thời gian trước và sau.

### Chặng 1 — Tách và làm lại đặc tả *(việc giảng viên nhận xét trực tiếp)*

- [x] 1.1 Tách `docs/user-stories.md` thành `docs/user-stories/` — **9 file theo đúng 9 nhóm A–I
      đã có sẵn**, cộng `README.md` làm mục lục và bảng đối chiếu đề bài.
      *(02/10: `docs/user-stories/` có 9 file nhóm + README; file cũ đã xóa.)*
- [x] 1.2 Viết lại **từng US** theo ba mục: **Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên**.
      Tách các tiêu chí biên đang nằm lẫn ra đúng mục của nó.
      → verify: đếm lại tổng tiêu chí bằng lệnh, phải **không mất** tiêu chí nào so với 118.
      *(02/10: 60 chấp nhận + 58 biên = 118; so từng dòng `- Given` với `git show HEAD:docs/user-stories.md` — giống hệt, chỉ khác đường dẫn link.)*
- [x] 1.3 Sửa link ở **23 tài liệu** đang trỏ tới `user-stories.md`.
      → verify: `test_moi_link_tuong_doi_trong_tai_lieu_deu_ton_tai` xanh.
      *(02/10: đếm lại thực tế chỉ **11** tài liệu có link, không phải 23 — số 23 đếm cả chỗ nhắc tên không phải link ở log và kế hoạch cũ; những chỗ đó là lịch sử nên giữ nguyên chữ.)*
- [x] 1.4 Phép canh mới: mỗi file US phải có đủ ba mục, và mọi mã `US-xx` nhắc trong
      `test-cases.md` phải tồn tại.
      → verify: đột biến xóa một mục, xác nhận đỏ đúng chỗ.
      *(02/10: 3 phép canh trong `test_architecture.py`; 3 đột biến — bỏ tiêu đề mục biên, trùng mã US-05, nhắc US-99 — đều bị bắt đúng phép canh.)*

### Chặng 2 — Đóng gói Docker

- [x] 2.1 `Dockerfile` + `docker-compose.yml`: volume cho `petcare.db`, `SECRET_KEY` truyền qua
      biến môi trường (app từ chối khởi động với khóa mặc định — S1).
- [ ] 2.2 CI thêm job dựng image và chạy thử container.
      → verify: `docker compose up` trên máy sạch ra trang đăng nhập.
- [x] 2.3 `docs/trien-khai.md`: cách chạy, và **đường chuyển sang PostgreSQL** khi cần.

### Chặng 3 — Hạ tầng gửi email

- [x] 3.1 `app/mail/`: Protocol `GuiMail` ← `SmtpMailer`, `FakeMailer`. Lặp đúng mẫu `AIProvider`.
      → verify: test dùng `FakeMailer`, **không lượt gửi thật nào** trong suite.
- [x] 3.2 Token xác minh: **hết hạn** và **dùng một lần**.
      → verify: ca biên token hết hạn, token dùng lại, token của người khác.
- [x] 3.3 Biến SMTP vào `.env.example`.
      → verify: phép canh `.env.example` đầy đủ (số 50) xanh.

### Chặng 4 — Vai trò khách hàng và cách ly dữ liệu

- [x] 4.1 ~~Thêm vai trò `customer` vào `VAI_TRO`; thêm `owners.user_id`~~ — **đổi hướng 02/10:** bảng riêng `customers` (xem [kế hoạch chặng 4](2026-10-02-p9-chang4-tai-khoan-khach.md), phản biện #1–#3); khóa nối nằm ở `customers.owner_id`.
      → verify: soát mọi chỗ duyệt `VAI_TRO`; `erd.md` cập nhật tới từng cột.
- [x] 4.2 Đăng ký · xác minh email · đăng nhập · quên mật khẩu. *(Xong 02/10, đợt 4a.)*
      → verify: mật khẩu đi qua `kiem_mat_khau()` như ba đường hiện có (M-04).
- [ ] 4.3 Yêu cầu nối hồ sơ + màn duyệt của lễ tân.
      → verify: khách chưa được nối **không** thấy dữ liệu của bất kỳ chủ nuôi nào.
- [ ] 4.4 `yeu_cau_so_huu()` + **phép canh** bắt mọi router của khách đi qua nó (xem 5.2).
      → verify: đột biến bỏ một lượt kiểm, xác nhận phép canh đỏ.
- [ ] 4.5 Quét IDOR: mọi đường dẫn theo id của cổng khách, với id của người khác.
      → verify: mở rộng `test_khong_tim_thay.py` — **không bao giờ 200, không bao giờ 500**.

### Chặng 5 — Trạng thái chờ duyệt

- [ ] 5.1 Thêm `pending` vào `TRANG_THAI`; soát **cả 37 chỗ** dùng trạng thái trong 5 file
      (`appointment.py`, `invoice.py`, `billing.py`, `care_records.py`, `scheduling.py`).
      → verify: liệt kê từng chỗ và kết luận cho từng chỗ, dán vào log phiên.
- [ ] 5.2 `pending` **giữ chỗ** trong phép chống trùng; **hạn tự hủy**; **trần số lịch chờ** mỗi khách.
      → verify: ca hai khách xin cùng khung · ca quá hạn tự hủy · ca chạm trần.
- [ ] 5.3 Màn duyệt của lễ tân: duyệt / từ chối kèm lý do.
      → verify: lịch bị từ chối **trả lại khung giờ** cho người khác.

### Chặng 6 — Bảng khung trống theo nhân viên

- [ ] 6.1 Trang khung trống cho khách: theo ngày và dịch vụ, **nhóm theo nhân viên**, dùng lại
      `khung_gio_trong()`.
- [ ] 6.2 **Phép canh chống rò dữ liệu**: template của cổng khách không được render tên chủ nuôi
      hay tên thú cưng không thuộc về người đang đăng nhập.
      → verify: đột biến thêm một cột tên khách, xác nhận phép canh đỏ.
- [ ] 6.3 Nối từ khung trống sang form đặt lịch — bấm vào khung là điền sẵn giờ.

### Chặng 7 — AI cho khách

- [ ] 7.1 Khách chỉ dùng **US-26 hỏi đáp**; hạn mức ngày theo tài khoản, đếm từ `ai_logs.user_id`.
      → verify: ca chạm hạn mức **không gọi API** và không ghi log gọi.
- [ ] 7.2 Guardrail áp y nguyên cho khách; cập nhật `ai-safety.md` nói rõ khách **không** gửi hồ sơ
      thú cưng sang AI.
      → verify: test guardrail chạy với tài khoản `customer`.

### Chặng 8 — Đặc tả, tài liệu, đóng phase

- [ ] 8.1 Viết US mới cho cổng khách **trong cấu trúc mới** của chặng 1 (không viết vào file cũ rồi
      tách lại lần nữa).
- [ ] 8.2 Cập nhật `test-cases.md`, `erd.md`, `architecture.md`, `ai-safety.md`, `codebase-map.md`.
- [ ] 8.3 `roadmap.md`: thêm **P9** kèm DoD, sửa câu "Chín phase" thành mười.
- [ ] 8.4 Báo cáo kiểm thử P9 + khối smoke P9 cho người dùng tick.

---

**Tổng: 29 ô** (đếm bằng lệnh, không chép tay).

---

## 7. Vì sao thứ tự này

1. **Chặng 0 trước hết** — đổi fixture khi còn 906 test rẻ hơn khi đã 1200 test.
2. **Đặc tả (chặng 1) trước cổng khách** — vì cổng khách sẽ đẻ ra ~10 US mới. Tách cấu trúc trước
   thì viết một lần; làm ngược lại thì viết vào file cũ rồi phải tách lại.
3. **Email (chặng 3) trước vai trò khách (chặng 4)** — đăng ký không chạy được nếu chưa gửi được mail.
4. **Cách ly dữ liệu (4.4, 4.5) trước mọi màn hình của khách** — dựng màn hình trước rồi vá quyền sau
   là cách chắc chắn nhất để bỏ sót một route.
5. **AI cuối cùng** — nó phụ thuộc vào vai trò `customer` đã tồn tại và đã được cách ly.

---

## 8. Rủi ro đã biết

| Rủi ro | Cách xử lý |
|---|---|
| Khách thấy dữ liệu khách khác (IDOR) | Điểm chặn duy nhất + phép canh (5.2) + quét ở 4.5 + phép canh template ở 6.2 |
| Thêm `pending` làm sai thống kê / hóa đơn / chống trùng | Soát cả 37 chỗ ở 5.1, liệt kê từng chỗ ra log phiên |
| Đăng ký bị lạm dụng, gửi mail rác | Token hết hạn + dùng một lần; giới hạn lượt đăng ký |
| Khách đốt sạch quota AI của shop | Hạn mức ngày theo tài khoản, đếm từ `ai_logs.user_id` |
| Giữ chỗ vô hạn bằng lịch chờ duyệt | Hạn tự hủy + trần số lịch chờ mỗi khách (5.2) |
| Bộ test vượt 200s, không ai chạy nữa | Chặng 0 làm trước |
| Bí mật SMTP lọt vào repo công khai | `.env` không vào git; phép canh `.env.example` |
| Test gửi mail thật ra ngoài | `FakeMailer`, và test khẳng định không có lượt gửi thật nào |

---

## 9. Việc của P8 vẫn còn treo, không bị kế hoạch này thay thế

- **Bộ đo chất lượng AI** — `2026-09-25-ragas-bo-do-ai.md`, 12 ô chưa tick, đã duyệt.
- **README hoàn chỉnh · báo cáo cuối kỳ · slide.**
- **6 ô smoke P8** chờ người dùng bấm tay.
