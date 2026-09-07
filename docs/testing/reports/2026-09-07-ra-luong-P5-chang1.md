# Báo cáo — Rà luồng P5 chặng 1 bằng trình duyệt thật

- **Ngày:** 2026-09-07
- **Cách chạy:** agent điều khiển Chrome qua extension Claude in Chrome, bấm chuột thật trên
  `http://127.0.0.1:8000` với CSDL seed sạch
- **Mục đích:** tìm lỗi trước khi người dùng smoke test khối P5 chặng 1

## 1. Giới hạn của cách chạy này

Như hai lần trước: **agent bấm không thay thế được người bấm.** Agent kiểm được luồng có thông
không, nút có hiện đúng lúc không, con số có đúng không. Nó không thay được câu "nhìn rối quá".

Các ô trong [`../smoke-checklist.md`](../smoke-checklist.md) vẫn để trống cho người dùng tick.

## 2. Tám lỗi tìm được — tất cả đã sửa

### Lỗi 1 — Không có cách nào đổi giá dịch vụ bằng chuột

Nặng nhất, và nó **chặn đứng ô smoke quan trọng nhất của cả phase**.

Route `POST /services/{id}/sua` có từ P2b, `catalog.sua_dich_vu()` có, test cũ cũng có — nhưng
**không template nào chứa form trỏ tới nó**. Quản lý mở trang Dịch vụ chỉ thấy "Ngưng bán". Nghĩa là
US-07 ("quản lý cập nhật giá") chưa từng dùng được, và ô smoke *"đổi giá dịch vụ → mở lại hóa đơn cũ,
giá vẫn là giá lúc lập"* — thứ chứng minh quyết định giá trị nhất của P5 — không ai bấm được.

Vì sao không ai phát hiện: `test_doi_gia_dich_vu` **gọi thẳng POST** thay vì đi qua form trên trang.
Đây đúng lớp lỗi "route có nhưng thiếu link menu" đã gặp hai lần ở P4 — lần này là route có nhưng
thiếu cả form.

**Sửa:** thêm ô đổi giá ngay trên dòng bảng giá, cùng lối với ô đổi giờ ở lưới lịch hẹn. Ba ô ẩn giữ
nguyên tên, thời lượng, mô tả — route `/sua` ghi đè cả bốn trường, form thiếu ô nào là trường đó bị
xóa trắng; có test riêng cho đúng cái bẫy đó.

Kiểm lại bằng chuột sau khi sửa: đổi giá "Tắm và sấy" 150.000 → 200.000đ, mở lại hóa đơn #1 →
**vẫn 150.000đ**. Quyết định 2 của P5 giờ chứng minh được bằng mắt.

### Lỗi 2 — Thông báo lỗi lộ mã phase của dự án ra cho người dùng

Trả tiền vượt số nợ hiện: *"Số tiền vượt quá số còn nợ của hóa đơn (90.000đ). **P5** chưa làm nghiệp
vụ hoàn tiền."* Lễ tân không biết "P5" là gì — đó là từ vựng của người làm dự án. Vi phạm CLAUDE.md
mục 5 (thông báo cho người dùng viết bằng tiếng Việt của người dùng).

Lỗi này **tự động hóa được** nên thành phép canh, không thành ghi chú: quét chuỗi bên trong
`LoiNghiepVu(...)` tìm mã phase.

### Lỗi 3 — Hóa đơn đã hủy vẫn hiện "Còn nợ 150.000đ"

Ở cả trang chi tiết lẫn cột "Còn nợ" của danh sách. Một hóa đơn đã bỏ mà vẫn ghi số nợ là con số sẽ
bị đi đòi nhầm, và ở P6 nó sẽ chui thẳng vào báo cáo công nợ.

**Sửa ở model, không ở template:** `Invoice.con_no` trả 0 khi trạng thái là đã hủy. Sửa ở template
thì mỗi màn hình mới lại phải nhớ thêm một lần; sửa ở property thì P6 tính đúng sẵn. Số tiền gốc vẫn
tra được ở `total_amount`.

### Lỗi 4 — Hóa đơn đã hủy là ngõ cụt câm

Lịch hẹn có hóa đơn đã hủy vẫn hiện nút **"Xem hóa đơn"**. Bấm vào thấy một hóa đơn đã hủy, không có
thao tác nào, và không lập lại được — vì `appointment_id` là UNIQUE nên mỗi lịch chỉ gắn được một hóa
đơn trong suốt đời nó. Người dùng không có cách nào biết phải làm gì tiếp.

**Sửa:** lưới lịch nói thẳng **"Hóa đơn đã hủy"** ngay trên dòng, và trang hóa đơn đã hủy có khung
nói rõ bước tiếp theo (hủy luôn lịch hẹn, hoặc đặt lại một lịch mới rồi lập hóa đơn cho nó). Giới hạn
vẫn còn nguyên — nhưng nó thôi câm.

### Lỗi 5 — Trang chủ không có thẻ "Hóa đơn"

P5 thêm link vào thanh điều hướng nhưng quên trang chủ, nơi người dùng nhìn đầu tiên sau khi đăng
nhập. **Lần thứ ba của cùng một lớp lỗi** (P2b quên link "Dịch vụ", P4 quên link "Chủ nuôi").

Lần này tự động hóa được: phép canh mới so danh sách đường dẫn trong thanh điều hướng với trang chủ.
Theo CLAUDE.md mục 9, lặp lần ba mà tự động hóa được thì thành test chứ không thành dòng ghi nhớ.

### Lỗi 6 — Buổi chăm sóc chưa lập hóa đơn nằm cách đây một tháng

Dữ liệu mẫu chừa một buổi `done` chưa có hóa đơn để bấm thử nút "Lập hóa đơn" — nhưng lại chừa đúng
buổi **cách đây 29 ngày**. Lưới lịch mở theo ngày, nên người kiểm thử mở lịch hôm nay, hôm qua, không
thấy nút đâu cả.

**Sửa:** đổi thứ tự trong `PHAN_DA_TRA` để buổi được chừa là buổi **hôm qua**. Giờ một màn hình lịch
06/09 có đủ ba trạng thái cạnh nhau: "Xem hóa đơn", "Lập hóa đơn", "Ghi hồ sơ".

### Lỗi 7 — Hai link hành động dính vào nhau

Trên lưới lịch, "Xem hồ sơ" và "Xem hóa đơn" nằm sát nhau, hai màu khác nhau, đọc như một cụm và
vùng bấm chạm nhau. Cùng loại với lỗi "link xuống hai dòng tạo vùng chết" đã sửa ở P4.

### Lỗi 8 — Thanh điều hướng của quản lý vỡ sớm hơn trước

Menu quản lý nay có 7 mục nên cần khoảng **1040px** mới xếp được một dòng; hẹp hơn thì chữ trong từng
mục tự xuống dòng ("Chủ / nuôi") và thanh trông như hỏng. Trước P5 ngưỡng đó là ~986px, tức cửa sổ
1024px — cỡ rất thường gặp — vừa mới rơi qua ngưỡng vì đúng cái link P5 thêm vào.

Ghi chú "thanh điều hướng vỡ ở ~800px" trong báo cáo 06/09 để lại vì dự án nhắm màn hình để bàn; giờ
nó vỡ ở cỡ màn hình để bàn nên phải sửa. **Sửa:** `min-height` thay cho chiều cao cố định, cho cả
thanh xuống dòng, và mỗi mục giữ nguyên chữ. Màn rộng nhìn y hệt trước.

## 3. Chứng minh test bắt được lỗi

Sáu test tái hiện, tất cả **chạy đỏ trước** khi sửa; hai phép canh kiến trúc cũng đỏ trước:

| Đột biến | Test đỏ |
|---|---|
| Bỏ thẻ "Hóa đơn" khỏi trang chủ | `test_trang_chu_co_the_hoa_don_cho_quan_ly_va_le_tan`, và phép canh nav↔trang chủ |
| Hóa đơn đã hủy vẫn tính còn nợ | 2 test (unit + integration) |
| Lưới lịch không nói hóa đơn đã hủy | `test_luoi_lich_noi_ro_hoa_don_da_bi_huy` |
| Trang hóa đơn đã hủy không nói bước tiếp theo | `test_trang_hoa_don_da_huy_noi_ro_buoc_tiep_theo` |
| Bỏ form đổi giá khỏi bảng giá | `test_trang_dich_vu_co_form_sua_gia` |
| Bỏ ô ẩn `mo_ta` khỏi form đổi giá | `test_luu_gia_khong_lam_mat_mo_ta_dich_vu` |
| Nhét lại mã phase vào thông báo lỗi | `test_thong_bao_loi_nghiep_vu_khong_lot_ma_phase_ra_ngoai` |

Mỗi đột biến giết đúng test tương ứng, không đột biến nào sống sót.

**Một phép canh suýt vô dụng.** Phép canh mã phase viết lần đầu dùng regex `LoiNghiepVu\((.*?)\)` —
và **xanh ngay trên chính ca đã sinh ra nó**: thông báo có f-string `{_so(hd.con_no)}` bên trong, nên
regex dừng ở dấu đóng ngoặc đầu tiên, cắt mất đúng đoạn chữ chứa "P5". Đã đổi sang đếm ngoặc lồng
nhau. Đây là lần thứ hai một phép canh mới bỏ sót đúng ca của mình (lần trước: class CSS trong biểu
thức Jinja) — luật rút ra vẫn thế: **viết phép canh xong phải thử làm hỏng lại đúng ca gốc.**

## 4. Ba điều KHÔNG phải lỗi của hệ thống

- **Trình quản lý mật khẩu Chrome lại điền đè tên đăng nhập.** Gõ `chamsoc1`, bấm Đăng nhập, vào
  bằng tài khoản quản lý. Đúng hiện tượng đã ghi trong báo cáo 06/09 mục 6. Ca phân quyền
  `caretaker` không xem được hóa đơn đã có test integration kiểm, nên không kiểm lại bằng tay.
- **`GET /logout` không làm gì** — đăng xuất là một form POST, không có link GET nào trỏ tới nó.
- **CSS và HTML bị Chrome cache** giữa hai lần sửa; phải nạp lại đúng file mới thấy thay đổi.

## 5. Việc dọn thêm: ký tự xuống dòng

Trong lúc sửa, các script python ghi đè file đã đổi toàn bộ ký tự xuống dòng của **70 file** (repo
này trộn cả LF và CRLF tùy file). `git status` phình lên 70 file "đã sửa" trong khi thay đổi thật chỉ
có 12. Đã trả từng file về đúng kiểu xuống dòng của bản trong git; diff cuối cùng đúng 12 file.

## 6. Kết quả tự động sau khi sửa

```
$ .venv/Scripts/python.exe -m pytest
464 passed in 58.16s
```

Tăng 10 test so với trước đợt rà (454). Phép canh kiến trúc: 11.

## 7. Còn lại, chưa sửa

- **Link "Thống kê" trỏ tới `/stats` chưa tồn tại → 404.** Có từ P1, thuộc P6, không sửa kèm. Nay
  trang chủ cũng có thẻ dẫn tới đó. Phép canh nav↔trang chủ **không** bắt được ca này — nó chỉ so hai
  danh sách với nhau, không kiểm route có thật.
- **Ô "Số tiền" dùng placeholder bằng đúng số còn nợ** (ví dụ `90000`), nhìn thoáng dễ tưởng đã điền
  sẵn. Chưa đổi vì `required` chặn được việc gửi form rỗng; nếu người dùng thấy vướng khi smoke thì
  đổi thành gợi ý bằng chữ.
