# Báo cáo — Rà luồng P4 chặng 2 bằng trình duyệt thật

- **Ngày:** 2026-09-06
- **Cách chạy:** agent điều khiển Chrome qua extension Claude in Chrome, bấm chuột thật trên
  `http://127.0.0.1:8000` với CSDL seed sạch
- **Mục đích:** tìm lỗi trước khi người dùng smoke test khối P4 chặng 2

## 1. Giới hạn của cách chạy này

Giống lần trước: **agent bấm không thay thế được người bấm.** Agent kiểm được luồng có thông không,
nút có hiện đúng lúc không, thông báo có đúng chữ không. Nó không thay được nhận xét kiểu "nhãn này
chưa đủ nổi" — dù lần này chính agent bắt được một lỗi thuộc loại đó, vì nó đối chiếu class trong
template với file CSS chứ không nhìn màu.

Các ô trong [`../smoke-checklist.md`](../smoke-checklist.md) vẫn để trống cho người dùng tick.

## 2. Năm lỗi tìm được — tất cả đã sửa

### Lỗi 1 — Xóa thú cưng chỉ có hồ sơ tiêm → trang đen "Internal Server Error"

Nặng nhất, và là **lỗi cũ mở lại**. Kịch bản đi qua đúng luồng bình thường:

1. Ghi một mũi tiêm cho Sữa (con vật chưa từng có lịch hẹn)
2. Vào trang chủ nuôi, bấm **Xóa** ở dòng của Sữa
3. Nhận về màn hình đen với đúng bốn chữ `Internal Server Error`

Phép chặn viết ở P4 chặng 1 hỏi đúng một câu — *"thú cưng này còn lịch hẹn không?"*:

```python
if db.scalar(select(Appointment).where(Appointment.pet_id == p.id)) is not None:
    raise LoiNghiepVu(...)
```

Bảng `vaccinations` thêm ở chặng 2 cũng trỏ vào `pets`. Thú cưng chỉ có hồ sơ tiêm lọt qua phép
chặn, rơi xuống khóa ngoại, `IntegrityError` bay ra thành 500.

**Sửa:** để khóa ngoại quyết định thay vì tự liệt kê bảng — xóa, bắt `IntegrityError`, `rollback`,
đổi thành `LoiNghiepVu`. Cách này chặn sẵn mọi bảng sẽ thêm ở P5–P7 (`invoices`, `payments`…) mà
không phải nhớ sửa lại hàm. Đổi lại, thông báo không nói được chính xác loại dữ liệu nào đang giữ;
chấp nhận, vì im lặng hỏng nặng hơn nói chung chung. Code sau khi sửa **ngắn hơn** trước.

### Lỗi 2 — Nhân viên chăm sóc không có link menu tới "Chủ nuôi"

Bảng phân quyền US-02 cho `caretaker` quyền **xem** chủ nuôi và thú cưng, và trang mở được thật —
đúng chế độ chỉ xem, không có form thêm, không có nút xóa. Nhưng thanh điều hướng chỉ hiện link cho
`manager` và `receptionist`, nên nhân viên chăm sóc phải tự gõ URL để tra lịch sử con vật mình sắp
chăm.

**Đây là lần thứ hai cùng một dạng lỗi.** Hôm qua tìm ra link "Dịch vụ" thiếu với hai vai trò, sửa
xong chỉ sửa đúng dòng đó chứ không soát lại cả bảng phân quyền — nên dòng "Chủ nuôi" vẫn sai suốt
từ P2a.

### Lỗi 3 — Ba class CSS không tồn tại

| Class | Dùng ở | Ý đồ | Thực tế |
|---|---|---|---|
| `chinh-nhe` | link "Ghi hồ sơ" trên lưới lịch (P4 chặng 1) | nổi hơn link thường | link thường |
| `bat-buoc` | dấu `*` ở ô bắt buộc (P4 chặng 1) | dấu sao đỏ | chữ đen |
| `dong-canh-bao` | dòng quá hạn (P4 chặng 2) | nền cảnh báo | không có gì |

Trang vẫn dựng đúng, mọi test vẫn xanh, chỉ là ý đồ không xảy ra. Ba lần trong cùng một phase.

### Lỗi 4 — Nhãn "Quá hạn" dùng chung kiểu với "Đã hủy"

`nhan-cancelled` là nền xám nhạt, chữ mờ — kiểu dành cho việc **đã bỏ**. Quá hạn tiêm là việc **phải
làm**, nên nó đang được làm nhòe đi đúng lúc cần nổi lên. Thêm `.nhan-qua-han` nền đỏ nhạt chữ đỏ.

### Lỗi 5 — Form ghi mũi tiêm xóa sạch dữ liệu khi báo lỗi

Nhập đủ năm ô, sai một ô ngày, bấm Lưu: thông báo hiện đúng, và **cả năm ô trắng trơn**. Phải gõ lại
từ đầu, gồm hai ô ngày. **Sửa:** trả lại nguyên những gì đã nhập.

Cùng vấn đề tồn tại ở form thêm chủ nuôi và form thêm thú cưng từ P2a — đã sửa nốt trong đợt bổ
sung, xem mục 8.

## 3. Bài học biến thành máy canh

Lỗi 3 là loại lặp đúng ba lần và **tự động hóa được**, nên theo CLAUDE.md mục 9 nó thành test chứ
không thành một dòng ghi nhớ: `test_moi_class_dung_trong_template_deu_co_trong_css`.

Phép kiểm đầu tiên chỉ đọc class viết cứng nên bắt được `chinh-nhe` và `bat-buoc` mà **bỏ sót đúng
`dong-canh-bao`** — class ấy nằm trong biểu thức Jinja `{{ 'dong-canh-bao' if v.qua_han }}`. Một phép
kiểm bỏ sót chính ca đã sinh ra nó thì gần như vô dụng. Siết lại: đọc thêm chuỗi **có dấu gạch nối**
bên trong biểu thức Jinja — dấu gạch nối phân biệt tên class với chuỗi so sánh thường như
`'cancelled'`, `'manager'`. Chạy lại: bắt đủ ba, không có dương tính giả.

Lỗi 1 và lỗi 2 chung một gốc **không tự động hóa được**, nên nó thành dòng thứ tư trong danh sách ở
CLAUDE.md mục 9: *sửa một lỗi thì soát cả lớp lỗi, không chỉ ca vừa thấy.*

## 4. Chứng minh test bắt được lỗi

Bốn test tái hiện, tất cả **chạy đỏ trước** khi sửa:

| Test | Đỏ vì |
|---|---|
| `test_xoa_thu_cung_chi_co_ho_so_tiem_bi_chan_khong_phai_loi_500` (U) | `IntegrityError` |
| `test_xoa_thu_cung_chi_co_ho_so_tiem_ra_400_khong_phai_500` (I) | viết sau khi sửa — chứng minh bằng đột biến |
| `test_moi_vai_tro_deu_co_link_menu_toi_trang_chu_nuoi` (I, ×3 vai trò) | không có `href="/owners"` |
| `test_form_mui_tiem_giu_lai_du_lieu_da_nhap_khi_bao_loi` (I) | không có `value=` nào |
| `test_moi_class_dung_trong_template_deu_co_trong_css` (U) | ba class thiếu |

Test integration của lỗi 1 viết **sau** khi sửa nên xanh ngay — không chứng minh gì. Đột biến: bỏ
`try/except IntegrityError` → **bốn** test đỏ, gồm cả hai test cũ của ca "còn lịch hẹn". Hoàn nguyên:
xanh lại.

## 5. Kiểm chứng lại bằng mắt sau khi sửa

Cả năm chỗ đều xem lại trên trình duyệt thật với CSDL seed sạch:

- Bấm Xóa trên Sữa → thông báo tiếng Việt trong khung đỏ ngay dưới tên chủ nuôi, không còn trang đen
- Nhãn **Quá hạn** giờ là viên thuốc đỏ nhạt, dòng của nó có nền hồng rất nhạt
- Đăng nhập `chamsoc1` → thanh điều hướng có **Chủ nuôi**
- Nhập sai hạn nhắc → thông báo hiện, và cả năm ô vẫn còn nguyên chữ vừa gõ

## 6. Một điều KHÔNG phải lỗi của hệ thống

Có lúc gõ `chamsoc1` vào ô tên đăng nhập mà lại vào được bằng tài khoản quản lý. Đã kiểm
`dang_nhap_session` — nó gán thẳng `request.session[KHOA_SESSION] = user.id`, không có lỗi giữ phiên
cũ. Nguyên nhân là **trình quản lý mật khẩu của Chrome tự điền đè** ô tên đăng nhập khi ô mật khẩu
được focus; ảnh chụp cho thấy hai ô nền xanh đặc trưng của autofill. Điền mật khẩu trước, tên đăng
nhập sau thì đúng.

Ghi lại vì đây đúng loại hiện tượng dễ bị kết luận nhầm thành lỗi phân quyền.

## 7. Kết quả tự động sau khi sửa

```
$ pytest
398 passed in 41.70s
```

Tăng 7 test so với trước đợt rà (391).

## 8. Sửa nốt các điểm nhỏ tồn đọng — bổ sung cùng ngày

Người dùng yêu cầu dọn nốt danh sách "chưa sửa". Năm việc, tất cả đã xong:

| Việc | Cách sửa |
|---|---|
| Form chủ nuôi và form thú cưng mất dữ liệu khi báo lỗi | Trả lại giá trị đã nhập, như đã làm cho form mũi tiêm |
| Thông báo lỗi form chủ nuôi nằm xa ô nhập | Tách hai chỗ: `loi` cho lỗi cả trang (xóa chủ nuôi), `loi_nhap` hiện **trong** khung nhập |
| Lưới lịch hẹn tràn ngang ở ~1030px | `.hai-cot.cot-rong` xếp dọc từ 1100px thay vì 820px — bảng lấy trọn bề ngang |
| Link "Ghi hồ sơ" xuống hai dòng tạo vùng chết | `td.thao-tac .chinh-nhe { white-space: nowrap }` |
| Dữ liệu mẫu chỉ cho mỗi thú cưng một hồ sơ | Mực có thêm buổi cách đó gần một tháng — ô smoke "mới nhất lên đầu" nay nhìn ra được |
| `xoa_chu_nuoi` sẽ lặp lỗi 500 ở P5 | Giữ phép kiểm rõ ràng cho ca đã biết (thông báo nói được phải làm gì), thêm `IntegrityError` làm lớp chặn cuối |

Bốn test tái hiện, tất cả **đỏ trước**: hai test giữ dữ liệu form, một test vị trí thông báo lỗi, một
test lớp chặn cuối của `xoa_chu_nuoi` (dựng một bảng phụ trỏ vào `owners` để đóng vai bảng sẽ thêm ở
P5). Sau khi sửa: **402 passed**.

Chỗ sửa vị trí thông báo lỗi suýt hỏng một thứ khác: dời khối `loi` vào trong form làm lỗi *"xóa chủ
nuôi còn thú cưng"* cũng rơi vào khung "Thêm chủ nuôi" — sai chỗ. Phát hiện ngay khi đọc lại, tách
thành hai biến.

## 9. Còn lại, chưa sửa

- **Thanh điều hướng vỡ ở cửa sổ hẹp (~800px):** các mục menu xuống hai dòng và tràn khỏi khung
  cao 56px. Dự án nhắm màn hình để bàn nên chưa sửa; nếu cần chạy trên máy tính bảng thì phải làm.
- Form thêm chủ nuôi ở trang chi tiết chủ nuôi (`owner_detail.html`) vẫn để thông báo lỗi ở đầu
  trang, vì trang đó có hai nguồn lỗi khác nhau (thêm thú cưng, và xóa thú cưng/chủ nuôi).
