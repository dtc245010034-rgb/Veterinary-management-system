# Demo Petcare cho thầy cô — thứ Bảy 31/10/2026

Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI. Tài liệu này dành cho **người trình bày**: làm theo từng bước từ trên xuống,
mỗi bước ghi rõ bấm gì, thấy gì, và nó trả lời mục nào của [đề bài](de-bai.md). Từng bước đã được kiểm ngày 28/10 bằng yêu cầu HTTP tới
server thật trên máy Linux của dự án (`demo.db` dựng mới, Gemini thật); **chưa ai bấm tay từng nút trên trình duyệt** — lượt tập dượt ở mục 1.2 chính là lần đó.
Chỗ nào chưa kiểm được thì có ghi rõ.

**Thời lượng:** khoảng 30 phút đầy đủ, hoặc 12 phút nếu chỉ làm các phần có dấu ★ (A, D, E, G, I, J).

## 0. Một trang tóm tắt

| Việc | Lệnh (chạy ở thư mục dự án) |
|---|---|
| Dựng dữ liệu demo (**sáng 31/10**, ~5 giây) | `.venv/bin/python tools/tao_du_lieu_demo.py` |
| Chạy với **Gemini thật** | `DATABASE_URL=sqlite:///demo.db .venv/bin/python run.py --no-open` |
| Chạy với **AI giả** (dự phòng) | `AI_PROVIDER=fake DATABASE_URL=sqlite:///demo.db .venv/bin/python run.py --no-open` |
| Mở trình duyệt | `http://127.0.0.1:8000/login` |
| Mật khẩu của **mọi** tài khoản | `matkhau123` |

Đừng chạy `python run.py` trơn: nó sẽ dùng `petcare.db` (CSDL thật), không phải `demo.db`.

## 1. Chuẩn bị

### 1.1 Dựng `demo.db` lúc nào

Mọi ngày giờ trong dữ liệu demo **tính từ lúc chạy script**, không cố định. **Dựng trước để tập dượt thì được, thoải mái** (5 giây, xóa dựng lại không mất gì).
Còn bản **dùng để demo**, hãy dựng lại **sáng 31/10**: đó là cách duy nhất để từng chữ trong tài liệu này đúng. Đã mô phỏng (28/10) việc dựng lúc 9:00 ngày 30/10
rồi xem lúc sáng 31/10, kết quả:

| Thứ | Dựng sáng 31/10 | Dựng trước một ngày (9:00 ngày 30/10) |
|---|---|---|
| Lịch hôm nay | 10 lịch giờ cố định 09:00 → 16:00 (nếu dựng buổi sáng) | Chỉ 6 lịch rải ngẫu nhiên, thưa hơn |
| Lịch "hôm qua" để **Ghi hồ sơ** (phần E, G) | Lịch Đậu Đỏ 12:00 của nhân viên `chamsoc1` | Có 10 lịch đã qua giờ, **nhưng chỉ khi dựng buổi sáng**; dựng sau 16:00 thì "hôm qua" không có lịch nào ghi hồ sơ được |
| Lịch chờ duyệt có sẵn (2 lịch) | Còn sống | **Hết hạn sau 24 giờ**: xem lúc 8:00 sáng 31/10 còn, xem lúc 10:00 đã mất |
| Mũi tiêm đến hạn trong 7 ngày | 6 ca | 5 ca (một ca đã thành quá hạn) |

Hai lịch chờ duyệt có sẵn **không** cần cho kịch bản (phần J tự tạo yêu cầu mới), nên dựng trước một ngày vẫn demo được; nhưng bạn sẽ phải tự kiểm lại phần E và G.
Script sinh lịch hôm nay theo giờ cố định 09:00, 10:30, 13:00, 14:30, 16:00 cho từng nhân viên; giờ đã qua so với lúc dựng bị bỏ (hệ thống không cho đặt lịch trong
quá khứ), nên dựng **buổi sáng**, không dựng muộn.

`demo.db` bị `.gitignore` nên **không có sẵn trong repo**: trên máy sạch phải dựng. Dựng lại sẽ **xóa sạch** `demo.db` cũ: dừng server trước, và **đừng dựng lại giữa buổi demo**.

### 1.2 Ngày 30/10 — tập dượt một lượt (~45 phút, bấm tay trên trình duyệt)

- [ ] Dựng `demo.db`, chạy với Gemini thật, đi hết kịch bản mục 3 một lần.
- [ ] Mở `/ai/quota` (đăng nhập `quanly`) xem hạn mức và **giờ reset**. Hạn mức Gemini tính theo giờ Mỹ; ngày 28/10 trang này ghi
  "reset lúc 14:00 giờ Việt Nam". Cả kịch bản chỉ gọi Gemini khoảng 4–5 lượt (nhắc lịch, nhắc tiêm, tóm tắt, hỏi đáp thường), còn bốn model ước tính 20 lượt mỗi model và tự xoay ca, nên hạn mức không phải nỗi lo;
  nếu muốn chắc thì tập dượt **trước giờ reset** để lượt tập thuộc ngày hạn mức cũ.
- [ ] Chụp lại màn hình kết quả AI thật (nhắc lịch, tóm tắt, hỏi đáp) để có ảnh dự phòng.
- [ ] Sau khi tập xong: dừng server (Ctrl+C), **xóa dữ liệu tập dượt** bằng cách dựng lại `demo.db` vào sáng 31/10.

### 1.3 Sáng 31/10, trước giờ demo ít nhất 30 phút

- [ ] Dừng mọi server đang chạy, rồi `.venv/bin/python tools/tao_du_lieu_demo.py`. Phải thấy `=== DEMO ===` và dòng
  `Thêm: … lịch sắp tới …`. (Script xóa `demo.db` cũ và dựng lại từ đầu.)
- [ ] Chạy server bằng lệnh Gemini thật ở mục 0. Terminal in `Application startup complete.` Để terminal này **luôn hiện được trên màn
  hình** — thư giả của phần cổng khách (mục K) hiện ở đây.
- [ ] Mở `http://127.0.0.1:8000/login`, đăng nhập `quanly`. Vào **Trợ lý AI**: nếu thấy khung vàng "Đang chạy chế độ AI giả lập" nghĩa là đang
  dùng AI giả (xem mục 5). Không thấy khung đó là đang dùng Gemini thật.
- [ ] Kiểm tra mạng (Gemini cần Internet): hỏi thử một câu ở **Trợ lý AI**, ví dụ *"Bao lâu nên tắm cho chó một lần?"*. Một lượt mất khoảng 2–3 giây
  (đo ngày 28/10).
- [ ] Chuẩn bị **hai cửa sổ trình duyệt**: một cửa sổ thường (nhân viên) và một cửa sổ **ẩn danh** (khách và nhân viên thứ hai). Một trình duyệt chỉ
  giữ **một danh tính** mỗi lần: đăng nhập nhân viên sẽ đẩy phiên khách ra và ngược lại.
- [ ] Máy cắm điện, tắt chế độ ngủ, đóng thông báo. Cổng 8000 bận thì thêm `--port 8001` vào lệnh và dùng cổng đó trong mọi địa chỉ.

## 2. Tài khoản có sẵn

Mật khẩu chung `matkhau123`.

**Nhân viên** — đăng nhập tại `/login`:

| Tên đăng nhập | Vai trò | Dùng cho phần |
|---|---|---|
| `quanly` | Quản lý, làm được mọi việc | A, G, H, I |
| `letan` | Lễ tân | C, D, F, J, K |
| `chamsoc1` | Nhân viên chăm sóc (tên hiển thị **Lê Văn Chăm**) | A, E |
| `chamsoc2` | Nhân viên chăm sóc (**Phạm Thị Sóc**) | — |

**Khách** — đăng nhập tại `/khach/dang-nhap`:

| Email | Tình trạng | Dùng cho phần |
|---|---|---|
| `khach1@demo.test` | Đã nối hồ sơ (Đỗ Thị Hằng) | K |
| `khach2@demo.test` | Đã nối hồ sơ (Trần Quốc Đạt) | — |
| `khach3@demo.test` | Đã nối hồ sơ (Nguyễn Minh Anh) | — |
| `khach4@demo.test` | Đang **chờ lễ tân duyệt** nối hồ sơ | — |
| `khach5@demo.test` | Bị **từ chối** nối hồ sơ (kèm lý do) | — |
| `khach6@demo.test` | Mới đăng ký, **chưa gửi** yêu cầu nối hồ sơ (Võ Thanh Tâm, số điện thoại `0901000003`) | K |
| `khach7@demo.test` | **Đã dùng hết 10 lượt AI** trong ngày | K |

## 3. Kịch bản từng bước

Địa chỉ gốc `http://127.0.0.1:8000`. Menu nằm sau nút **☰ Menu**. Chữ **đậm** là tên nút hoặc mục đúng như trên màn hình.

### A ★ Đăng nhập và phân quyền — đề bài 3.1.1 (3 phút)

1. Đăng nhập `quanly`. Trang chủ ghi *"Bạn đang đăng nhập với vai trò Quản lý"*. Bấm **☰ Menu**: có **Chủ nuôi, Lịch hẹn, Dịch vụ, Tiêm phòng,
   Trợ lý AI, Hóa đơn, Lịch chờ duyệt, Liên kết khách, Thống kê, Tài khoản**.
2. **Đăng xuất**, đăng nhập `letan`. Menu **không còn Thống kê và Tài khoản**. Gõ thẳng `/stats` vào thanh địa chỉ: trang *"Lỗi 403 — Không có quyền
   truy cập. Bạn không có quyền truy cập chức năng này."*
3. **Đăng xuất**, đăng nhập `chamsoc1`. Menu chỉ còn **Chủ nuôi, Lịch của tôi, Dịch vụ, Tiêm phòng, Trợ lý AI**. Thử `/invoices` hoặc `/lich-cho-duyet`:
   cùng trang 403.

*Nói với thầy cô:* quyền kiểm ở máy chủ chứ không chỉ ẩn nút trên menu.

### B Chủ nuôi và thú cưng — đề bài 3.1.2 (3 phút)

Đăng nhập `letan`. Menu **Chủ nuôi**.

1. Ô tìm kiếm gõ **`dau do`** (không dấu) rồi bấm **Tìm**: ra thú cưng **Đậu Đỏ** (Mèo, Anh lông ngắn) của **Trần Quốc Đạt**.
2. Kéo xuống **Thêm chủ nuôi**, nhập Họ tên `Nguyễn Thị Demo`, Số điện thoại `0933445566`, Email `demo.chu@example.com`, Địa chỉ `12 Lê Lợi`,
   bấm **Thêm chủ nuôi**. Chủ nuôi mới nằm trong danh sách.
3. Mở chủ nuôi vừa tạo, mục **Thêm thú cưng**: Tên `Bơ`, Loài `Chó`, Giống `Poodle`, Giới tính `Đực`, Ngày sinh `2024-05-01`, Cân nặng (kg) `4.5`,
   bấm **Thêm thú cưng**.
4. Thử nhập Số điện thoại `123` khi thêm chủ nuôi: báo đỏ *"Số điện thoại phải là số Việt Nam 10 chữ số bắt đầu bằng 0, ví dụ 0912345678."*

### C Dịch vụ, bảng giá, gói — đề bài 3.1.3 (2 phút)

Menu **Dịch vụ**. Bảng 5 dịch vụ: Cắt móng (15 phút, 50.000đ), Cắt tỉa lông (60 phút, 250.000đ), Spa toàn diện (90 phút, 450.000đ),
Tắm và sấy (45 phút, 150.000đ), Vệ sinh tai (15 phút, 60.000đ). Bên dưới là 2 gói: **Combo làm đẹp** (giá lẻ 450.000đ, giá gói 400.000đ,
tiết kiệm 50.000đ) và **Combo vệ sinh cơ bản** (260.000đ → 220.000đ). Chỉ cho thầy cô nút **Ngưng bán** (ngưng bán thay vì xóa để lịch và hóa
đơn cũ giữ nguyên).

### D ★ Đặt, đổi, hủy lịch và chống trùng lịch — đề bài 3.1.4 (4 phút)

Đăng nhập `letan`. Menu **Lịch hẹn**: trang mở ở **hôm nay**, đã có lịch của hai nhân viên chăm sóc (nếu trống nghĩa là `demo.db` dựng quá trễ, xem 1.1).

1. Khung **Đặt lịch**: Thú cưng `Bơ — Nguyễn Thị Demo`, Dịch vụ `Tắm và sấy`, Nhân viên chăm sóc `Lê Văn Chăm`, Giờ bắt đầu **một giờ còn ở tương lai**
   (hệ thống từ chối giờ đã qua: *"Không thể đặt lịch trong quá khứ."*) và nhân viên đang rảnh, ví dụ `11:30`. Bấm **Đặt lịch**: dòng mới trạng thái
   **Đã đặt**, dài 45 phút. (Muốn đặt cho ngày khác, đổi ô **Ngày** ở thanh trên rồi bấm **Xem** trước: khung Đặt lịch lấy theo ngày đang xem.)
2. **Trùng lịch:** đặt thêm một lịch cho `Lê Văn Chăm` trước khi lịch trên kết thúc, ví dụ `11:45`. Hệ thống từ chối kiểu *"Nhân viên Lê Văn
   Chăm đã có lịch 11:30–12:15 ngày …. Khung giờ còn trống: …"* và gợi ý giờ trống.
3. **Đổi:** ở dòng lịch vừa tạo, đổi ô giờ sang `12:15` rồi bấm **Đổi**: trạng thái thành **Đã đổi lịch**.
4. **Hủy:** gõ lý do `Khách báo bận` vào ô lý do rồi bấm **Hủy**: trạng thái thành **Đã hủy**.

### E ★ Hồ sơ chăm sóc — đề bài 3.1.5 (2 phút)

Đăng xuất, đăng nhập `chamsoc1`. Menu **Lịch của tôi**, đổi **Ngày** về **hôm qua** rồi bấm **Xem**. Có lịch **Đậu Đỏ — Tắm và sấy 12:00**, trạng thái
**Đã đặt**, có nút **Ghi hồ sơ** (chỉ hiện với lịch đã qua giờ bắt đầu và đúng nhân viên đó).

1. Bấm **Ghi hồ sơ**. Nhập Tình trạng thú cưng `Lông rối vùng bụng, da sạch, hợp tác tốt.`, Việc đã làm `Tắm, sấy, gỡ rối, cắt móng.`, Dặn dò lần sau `Chải lông 2 lần/tuần.`,
   bấm **Lưu hồ sơ**. Lịch thành **Hoàn thành**, nút đổi thành **Xem hồ sơ**.

Lịch hôm nay buổi sáng (09:00, 10:30) cũng thành "đã qua giờ" khi bạn demo vào buổi chiều, và ghi hồ sơ được tương tự.

### F Tiêm phòng và nhắc lịch tiêm — đề bài 3.1.6 (3 phút)

Đăng nhập `letan`. Menu **Tiêm phòng** ("Thú cưng đến hạn tiêm"). Danh sách gồm mũi **Quá hạn** (đỏ) và mũi đến hạn trong 30 ngày tới, hạn gần ở trên cùng;
dữ liệu demo có **vài ca quá hạn và 6 ca đến hạn trong 7 ngày** (cố ý, để trang này không trống). Dòng chữ nhỏ trên bảng: *"Mỗi loại vắc-xin chỉ tính mũi mới nhất"* và
*"không phải chỉ định y tế"*.

1. Mở thú cưng **Đậu Đỏ** (Chủ nuôi → Trần Quốc Đạt → Đậu Đỏ), mục **Hồ sơ tiêm**, **Ghi mũi tiêm**: Tên vắc-xin `Dại`, Mũi thứ mấy `3`, Ngày tiêm **hôm nay**,
   Hạn nhắc lại **cùng ngày năm sau**, bấm **Lưu mũi tiêm**.
2. Quay lại menu **Tiêm phòng**: dòng Dại của Đậu Đỏ **biến mất** khỏi danh sách nhắc, vì đã có mũi mới nhất thay thế (đã kiểm ngày 28/10).

### G ★ Hóa đơn và thanh toán — đề bài 3.1.7 (3 phút)

Đăng nhập `letan`. Menu **Lịch hẹn**, chọn ngày **hôm qua**, bấm **Xem**. Dòng **Đậu Đỏ** (vừa Hoàn thành ở phần E) có nút **Lập hóa đơn**.

1. Bấm **Lập hóa đơn**: trang *Hóa đơn #…* trạng thái **Chưa thu**, "Tắm và sấy 1 × 150.000đ", **Còn nợ 150.000đ**, kèm ghi chú đơn giá được chốt tại thời điểm lập.
2. **Ghi nhận thanh toán:** Số tiền `50000`, Hình thức **Tiền mặt**, bấm **Ghi nhận**: trạng thái **Thu một phần**.
3. Thử Số tiền `9999999`: báo *"Số tiền vượt quá số còn nợ của hóa đơn (100.000đ). Cửa hàng chưa dùng chức năng hoàn tiền trên hệ thống."*
4. Thu nốt `100000` bằng **Chuyển khoản**: trạng thái **Đã thu đủ**. Menu **Hóa đơn** liệt kê các hóa đơn với đủ trạng thái (chưa thu, thu một phần,
   đã thu đủ, đã hủy).

### H Thống kê — đề bài 3.1.8 (1 phút)

Đăng xuất, đăng nhập `quanly`. Menu **Thống kê**: **Lượt dịch vụ**, **Doanh thu** (tiền thực nhận), **Chưa thu**, **Khách quay lại** (tỉ lệ khách đến từ 2 ngày
trở lên) và bảng **Theo dịch vụ**. Đổi **Từ ngày / Đến ngày** rồi bấm **Xem** để lọc theo kỳ. Con số cụ thể thay đổi theo ngày dựng `demo.db`, đừng
đọc theo tài liệu này.

### I ★ Ba chức năng AI — đề bài 3.2 (5 phút)

Đăng nhập `letan` (hoặc `quanly`). Chờ khoảng 2–3 giây mỗi lượt Gemini thật. Mọi kết quả AI đều có dòng *"Nội dung do AI soạn, chỉ mang tính tham khảo. AI không thay
thế chẩn đoán của bác sĩ thú y."*, cuối trang ghi **"Trả lời bởi: gemini-3.6-flash"** (tên model đang dùng).

1. **Nhắc lịch chăm sóc (3.2.1):** menu **Lịch hẹn**, chọn một lịch **sắp tới** (cột giờ lớn hơn giờ hiện tại), bấm **Soạn tin nhắc (AI)**. Trang *Nhắc lịch* có **Tin nhắn
   nháp** sửa trực tiếp được, rồi **Chốt tin nhắn** và **Sao chép**. Với lịch **đã qua giờ**, hệ thống từ chối: *"Buổi này đã qua giờ hẹn, không nhắc nữa."*
2. **Nhắc lịch tiêm (3.2.1):** menu **Tiêm phòng**, bấm **Soạn tin nhắc (AI)** ở một dòng. Tin nhắn nêu tên thú cưng, vắc-xin, hạn nhắc, và luôn kết bằng
   lời khuyên xác nhận với bác sĩ thú y.
3. **Tóm tắt hồ sơ chăm sóc (3.2.2):** mở thú cưng **Đậu Đỏ**, bấm **Tóm tắt bằng AI**. AI tóm tắt các lượt chăm sóc đã ghi.
4. **Hỏi đáp (3.2.3):** menu **Trợ lý AI**.
   - Hỏi `Bao lâu nên tắm cho mèo lông ngắn một lần?` bấm **Hỏi AI**: có câu trả lời và lời khuyên liên hệ bác sĩ thú y khi thú cưng có dấu hiệu bất thường.
   - Hỏi `Chó bị tiêu chảy thì cho uống thuốc gì, liều bao nhiêu?`: hệ thống **chặn trước khi gọi AI** và trả lời *"Xin lỗi, hệ thống không tư vấn thuốc, liều lượng hay cách
     điều trị cho thú cưng. Việc dùng thuốc phải do bác sĩ thú y chỉ định sau khi khám trực tiếp."*, dòng cuối ghi **"không gọi API — hệ thống tự trả lời"**. Đây là cảnh báo
     "không thay thế bác sĩ thú y" mà đề bài mục 4 yêu cầu.
5. **Hạn mức:** đăng nhập `quanly`, mở địa chỉ `/ai/quota` (lễ tân và nhân viên chăm sóc bị 403): bảng 4 model, mỗi model ước tính 20 lượt/ngày, hết lượt model này hệ thống tự chuyển sang model kế.

*Nói với thầy cô:* chỉ nội dung chăm sóc thú cưng được gửi cho AI, không gửi số điện thoại, email hay địa chỉ chủ nuôi
([`ai-safety.md`](ai-safety.md)); kiểm tra tự động `L11` của `tools/kiem_tra_song.py` xác nhận điều này trên mọi prompt đã lưu.

### J ★ Cổng khách hàng: đăng ký, nối hồ sơ, xin đặt lịch (6 phút) — ngoài đề bài

Phần này cho thấy hệ thống làm việc cho cả khách. Dùng **cửa sổ ẩn danh** cho khách, cửa sổ thường cho `letan`.

1. **Đăng ký:** cửa sổ ẩn danh, `http://127.0.0.1:8000/khach/dang-ky`, nhập email `thaycodemo@example.com`, bấm gửi. Trang báo *"Kiểm tra hộp thư của bạn"*. **Nhìn sang
   terminal đang chạy server:** có khối
   `[THƯ GIẢ — không gửi đi] Tới: thaycodemo@example.com | Tiêu đề: Xác minh email để hoàn tất đăng ký Petcare` kèm một liên kết
   `http://127.0.0.1:8000/khach/dang-ky/…`. (Đây là chế độ thử không có máy chủ thư; bản thật dùng `MAIL_PROVIDER=smtp`.)
2. Copy liên kết đó vào trình duyệt: trang *Hoàn tất đăng ký*. Nhập họ tên `Thầy Cô Demo` và mật khẩu `MatKhauDemo-123` hai lần. Vào trang chủ khách, thấy
   *"Tài khoản của bạn chưa được liên kết với hồ sơ thú cưng nào"*.
3. **Nối hồ sơ:** đăng xuất khách, đăng nhập `khach6@demo.test` (Võ Thanh Tâm). Menu **Liên kết hồ sơ**, nhập số điện thoại `0901000003`, ghi chú
   `Mình là chủ của bé Mít và bé Khoai`, bấm **Gửi yêu cầu**: *"Đã gửi yêu cầu… đang chờ cửa hàng"*.
4. Cửa sổ thường, đăng nhập `letan`, menu **Liên kết khách**: có yêu cầu của Võ Thanh Tâm. Chọn ứng viên **Võ Thanh Tâm (0901000003) — Khoai, Mít**, bấm **Duyệt và liên kết**.
5. Quay lại khách `khach6`: menu **Thú cưng** có **Khoai** (Chó, Golden) và **Mít** (Mèo ta), cùng lịch hẹn và hóa đơn của họ.
6. **Xin đặt lịch:** menu **Giờ trống**, chọn thú cưng `Khoai`, dịch vụ `Tắm và sấy`, ngày **ngày mai**, bấm **Xem giờ trống**: bảng giờ trống của từng nhân viên. Bấm một giờ,
   rồi **Gửi yêu cầu**: ở menu **Lịch hẹn** của khách, lịch có trạng thái **Chờ duyệt**.
7. Cửa sổ thường (`letan`), menu **Lịch chờ duyệt**: yêu cầu của Khoai, bấm **Duyệt**. Khách tải lại **Lịch hẹn**: **Đã đặt**.

Phụ (1 phút): đăng nhập `khach7@demo.test`, menu **Hỏi AI** báo *"Hôm nay bạn còn 0 /10 lượt hỏi"* và hỏi thêm sẽ bị từ chối. Đây là giới hạn chống lạm dụng hạn mức Gemini
miễn phí.

### K Chất lượng và kiểm thử — đề bài mục 4 (2 phút)

Đề bài yêu cầu có test cho lịch hẹn, hóa đơn, hồ sơ và AI. Trong terminal thứ hai (hoặc sau khi dừng server):

```
.venv/bin/python -m pytest tests/unit/test_scheduling.py tests/unit/test_billing_service.py tests/unit/test_care_records_service.py tests/unit/test_guardrail.py
```

Dòng cuối ghi `… passed in …s` (173 ca, khoảng 6 giây ngày 28/10; con số sẽ tăng khi có thêm test). Toàn bộ bộ test chạy bằng `.venv/bin/python -m pytest -rs` (khoảng 80 giây) và phải ra đúng **một** ca bỏ qua (kiểm hook PowerShell, máy
Linux không có PowerShell). Đọc con số thật trên màn hình, đừng chép từ tài liệu. Thầy cô muốn xem cách dùng AI trong quy trình phát triển (đề bài mục 6): mở
[`docs/plans/`](plans/) (kế hoạch từng phase), [`docs/sessions/`](sessions/) (nhật ký từng phiên làm việc với AI) và
[`testing/test-cases.md`](testing/test-cases.md) (ma trận truy vết yêu cầu → test).

## 4. Đối chiếu đề bài

| Mục đề bài | Phần |
|---|---|
| 3.1.1 Đăng nhập và phân quyền | A |
| 3.1.2 Chủ nuôi và thú cưng | B |
| 3.1.3 Dịch vụ, bảng giá, gói | C |
| 3.1.4 Đặt, đổi, hủy lịch | D |
| 3.1.5 Hồ sơ chăm sóc | E |
| 3.1.6 Nhắc tiêm phòng | F |
| 3.1.7 Hóa đơn và thanh toán | G |
| 3.1.8 Thống kê | H |
| 3.2.1 AI nhắc lịch | I.1, I.2 |
| 3.2.2 AI tóm tắt hồ sơ | I.3 |
| 3.2.3 AI hỏi đáp có cảnh báo thú y | I.4 |
| Mục 4 test cho lịch hẹn, hóa đơn, hồ sơ, AI | K |

## 5. Dự phòng: khi có gì đó hỏng

| Tình huống | Làm gì |
|---|---|
| Mất mạng hoặc Gemini trả lỗi / hết hạn mức | Ctrl+C, chạy lại bằng lệnh **AI giả** ở mục 0 (**không** dựng lại `demo.db`, kẻo mất dữ liệu đang demo). Khung vàng *"Đang chạy chế độ AI giả lập"* sẽ hiện: nói thẳng với thầy cô, câu trả lời là câu mẫu cố định. Câu xin thuốc vẫn bị chặn đúng như thật. Đưa ảnh chụp kết quả AI thật chuẩn bị ở 1.2 |
| Lịch hôm nay trống | `demo.db` dựng quá trễ (xem 1.1). Dừng server, dựng lại, chạy lại. Hoặc chọn ngày **ngày mai** ở ô Ngày: có sẵn lịch |
| Quên mất đang ở tài khoản nào | Menu trên cùng ghi tên người đăng nhập và vai trò ở góc phải |
| Cổng 8000 bận | Thêm `--port 8001` vào lệnh, dùng `http://127.0.0.1:8001` |
| Server chết giữa chừng | Chạy lại đúng lệnh cũ (không dựng lại `demo.db`); dữ liệu đã ghi vẫn còn |
| Muốn làm lại từ đầu | Dừng server, `.venv/bin/python tools/tao_du_lieu_demo.py`, chạy lại |
| Đăng nhập sai nhiều lần | Sai 5 lần liên tiếp bị khóa tạm 30 giây (gấp đôi mỗi lần sau đó). Đợi hoặc dùng tài khoản khác |
| Không thấy thư giả ở terminal | Đang chạy bằng Docker thì xem `python run.py docker logs`; chạy thường thì thư hiện ở cửa sổ terminal đã chạy lệnh server |

## 6. Điều nên nói thật nếu thầy cô hỏi

- AI **không chẩn đoán, không kê thuốc hay liều lượng**; mọi câu trả lời về sức khỏe kèm khuyến cáo bác sĩ thú y.
- Hệ thống **chưa có hoàn tiền**; hóa đơn đã thu rồi không hủy được.
- Khách **chưa tự hủy hay đổi lịch**; chỉ xin đặt lịch và chờ lễ tân duyệt.
- Con số hạn mức Gemini trên màn hình là **ước tính** do hệ thống tự đếm, không phải số của Google.

Danh sách đầy đủ ở [`huong-dan-su-dung.md`](huong-dan-su-dung.md) mục 9.
