# Báo cáo — Rà luồng P5 chặng 2 bằng trình duyệt thật

- **Ngày:** 2026-09-08 (phiên bắt đầu tối 07/09)
- **Cách chạy:** agent điều khiển Chrome qua extension Claude in Chrome, bấm chuột thật trên
  `http://127.0.0.1:8000` với CSDL seed sạch
- **Mục đích:** tìm lỗi trước khi người dùng smoke test khối P5 chặng 2

## 1. Giới hạn của cách chạy này

Như ba lần trước: **agent bấm không thay thế được người bấm.** Agent kiểm được luồng có thông
không, nút có hiện đúng lúc không, con số có đúng không. Nó không thay được câu "nhìn rối quá".

Các ô trong [`../smoke-checklist.md`](../smoke-checklist.md) vẫn để trống cho người dùng tick.

## 2. Hai ô chính của chặng 2 chạy đúng

Dựng lại đúng cảnh tab cũ: mở lưới lịch khi lịch còn "Đã đặt", tab kia ghi hồ sơ rồi lập hóa đơn,
quay lại tab cũ bấm **Hủy**.

| Bấm | Hệ thống trả lời |
|---|---|
| Hủy khi hóa đơn còn hiệu lực | *"Lịch này đã có hóa đơn **#3 (chưa thu)** nên không hủy được. Hủy hóa đơn ở trang hóa đơn trước; buổi chăm sóc đã ghi nhận hoàn thành thì vẫn giữ nguyên trong sổ."* |
| Hủy hóa đơn rồi bấm Hủy lại | *"Lịch ở trạng thái "Hoàn thành" nên không hủy được."* — **không nhắc hóa đơn nữa** |

Đúng hai lớp chặn độc lập như đã thiết kế. Lưới lịch cũng cập nhật theo: dòng đó đổi từ "Xem hóa
đơn" sang **"Hóa đơn đã hủy"**.

**Một phát hiện làm khối smoke dễ tick hơn:** không cần mở hai tab. Sau lần bấm Hủy thứ nhất, chỉ
cần bấm **Back** của trình duyệt là trang cũ hiện lại nguyên vẹn kèm cả ô lý do đã gõ — bfcache giữ
lại DOM cũ. Khối smoke đã được viết lại theo cách này.

## 3. Hai lỗi tìm được — cả hai đã sửa

### Lỗi 1 — Hủy nhầm hóa đơn xong là vào ngõ cụt câm

Lập lại hóa đơn cho lịch có hóa đơn **đã hủy** báo:

> Lịch này đã có hóa đơn #3 (đã hủy). Mỗi lịch hẹn chỉ một hóa đơn.

Câu này đúng nhưng **cụt**. Người dùng đang đứng ở lưới lịch: hóa đơn cũ đã hủy nên không mở ra làm
gì được, lịch thì không hủy được, và không có chữ nào nói phải làm sao. Đây đúng lớp lỗi *"ngõ cụt
câm"* đã sửa ở chặng 1 — nhưng khi đó chỉ sửa **trang hóa đơn**, bỏ sót thông báo trên **lưới lịch**.
Bài học 4 mục 9 (*sửa một lỗi thì soát cả lớp*) lẽ ra đã bắt được từ hôm đó.

**Sửa:** khi hóa đơn cũ đã hủy, thông báo nói tiếp bước kế — *"Cần thu tiền cho buổi này thì đặt một
lịch mới rồi lập hóa đơn cho lịch đó; buổi cũ vẫn giữ nguyên trong sổ."* Khi hóa đơn cũ **còn hiệu
lực** thì không thêm câu đó: việc phải làm là mở hóa đơn ra, và lưới lịch đã có sẵn nút "Xem hóa
đơn". Bày nhầm câu "đặt lịch mới" cho ca đó sẽ đẻ ra lịch rác — có test biên giữ đúng chỗ này.

Kèm theo: docstring của test cũ đang nói đường đi tiếp là *"hủy luôn lịch hẹn (US-21) rồi đặt lại"*
— chính là điều chặng 2 vừa chứng minh là không làm được. Đã sửa.

### Lỗi 2 — Trang 404 hiện chữ tiếng Anh

Bấm link **Thống kê** (trang thuộc P6, chưa dựng) ra trang 404 có bố cục tử tế, tiêu đề tiếng Việt,
nhưng dòng mô tả là **"Not Found"** — chuỗi mặc định của Starlette. Vi phạm CLAUDE.md mục 5.

Ca 403 không dính vì thông điệp do chính dự án viết ra.

**Sửa:** chỉ thay khi `detail` đúng bằng cụm mặc định của mã lỗi (`HTTPStatus(...).phrase`); thông
điệp do dự án tự viết giữ nguyên. Có test biên cho vế thứ hai, vì cách sửa cẩu thả — ghi đè mọi
thông điệp — sẽ nuốt mất câu tiếng Việt của 403 và của trang hóa đơn không tồn tại.

## 4. Chứng minh test bắt được lỗi

Bốn test mới, hai ca chính **chạy đỏ trước khi sửa**. Hai đột biến:

| Đột biến | Test đỏ |
|---|---|
| Bỏ nhánh gợi ý bước kế khi hóa đơn cũ đã hủy | `test_lap_lai_hoa_don_sau_khi_huy_bi_tu_choi_ro_rang_khong_phai_loi_500` |
| Trả lại `exc.detail` thô cho trang lỗi | `test_trang_loi_404_khong_hien_chu_tieng_anh_cua_framework` |

Mỗi đột biến giết đúng một test; hai test biên (`..._con_hieu_luc_khong_bay_dat_lich_moi` và
`..._403_van_giu_nguyen_thong_diep_cua_du_an`) **vẫn xanh**, đúng vai trò của chúng.

Script đột biến lần này **khẳng định chuỗi cũ có trong file và nội dung đã đổi** trước khi ghi —
đúng bài học 3 vừa bổ sung hôm qua, sau khi một đột biến âm thầm không vào file vì repo trộn LF với
CRLF.

## 5. Đã soát cả lớp lỗi "ngõ cụt câm"

Liệt kê toàn bộ thông báo `LoiNghiepVu` trong `app/services/` và xét từng câu: người đọc có biết
phải làm gì tiếp không?

- **Chỉ một câu là ngõ cụt thật** — câu vừa sửa ở lỗi 1.
- *"Hóa đơn đã hủy nên không ghi nhận thanh toán được"* — chỉ tới được từ tab cũ, và trang đó đã có
  khung giải thích ngay bên dưới.
- *"Lịch ở trạng thái "Hoàn thành" nên không hủy được"* — không có bước tiếp **thật**: trạng thái đó
  là cuối. Nói thêm gì cũng là bịa.
- Các câu còn lại đều nêu điều kiện cần sửa ngay trong câu ("phải ghi lý do", "chuyển hoặc xóa thú
  cưng trước", "ghi hồ sơ chăm sóc cho buổi này trước đã").

## 6. Bốn điều KHÔNG phải lỗi của hệ thống

- **Không có thông báo "đã lưu" sau khi ghi hồ sơ.** Kiểm lại: dự án **không có** cơ chế thông báo
  thành công ở bất cứ đâu — mọi thao tác thành công đều chuyển trang và người dùng thấy dữ liệu đã
  đổi. Nhất quán, không phải chỗ này thiếu.
- **Nút Đăng xuất "không ăn"** — bấm trượt vài pixel. Bấm đúng thì đăng xuất ngay.
- **Trình quản lý mật khẩu Chrome** vẫn điền đè tên đăng nhập, lần thứ ba. Xóa ô rồi gõ lại thì vào
  đúng tài khoản.
- **Phân quyền `caretaker`**: không thấy thẻ Hóa đơn ở trang chủ, `/invoices` và `/invoices/3` đều
  ra 403, lưới "Lịch của tôi" không hiện chữ nào về hóa đơn. Đúng US-02.

## 7. Kiểm hồi quy phần chặng 2 vừa đụng vào

`huy_lich` nay truy vấn thêm bảng hóa đơn, nên phải chắc lịch thường vẫn hủy được: hủy lịch
09:00 của Mực (chưa có hóa đơn) → **thành công**, dòng chuyển xám, lý do hiện tại chỗ. Ngoài ra:
danh sách `/invoices` xếp đúng (chưa thu trên đầu, đã hủy xuống cuối, cột "Còn nợ" của hóa đơn đã
hủy là 0đ), trang thú cưng hiện hồ sơ chăm sóc vừa ghi, trang tiêm phòng vẫn kèm khuyến cáo thú y.

## 8. Kết quả tự động sau khi sửa

```
$ .venv/Scripts/python.exe -m pytest
473 passed in 73.23s
```

Tăng 3 test so với đầu ngày (470 → 473).

## 9. Còn lại, chưa sửa

- **Dữ liệu mẫu ghi mọi hóa đơn và thanh toán vào đúng ngày chạy `seed.py`**, kể cả hóa đơn của buổi
  chăm sóc cách đây một tháng. Chưa sai gì ở P5 nhưng **P6 sẽ vướng**: "doanh thu theo khoảng thời
  gian" mà mọi đồng tiền đều rơi vào một ngày thì không smoke test được. Việc của P6: cho seed lùi
  ngày lập hóa đơn và ngày thu tiền về sát buổi chăm sóc.
- **Link "Thống kê" vẫn trỏ tới `/stats` chưa tồn tại → 404.** Có từ P1, thuộc P6. Trang 404 giờ đã
  nói tiếng Việt, nhưng link vẫn không nên có mặt khi trang chưa dựng.
- **Ô "Số tiền" dùng placeholder bằng đúng số còn nợ** (ví dụ `150000`), nhìn thoáng dễ tưởng đã
  điền sẵn. Vẫn để nguyên chờ người dùng smoke — đây là loại nhận xét chỉ người bấm mới kết luận
  được.
