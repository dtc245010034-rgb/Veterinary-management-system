# P5 — Hóa đơn và thanh toán

> **Phase:** P5 · **Mốc:** KT3 — phase đầu của mốc này · **Duyệt ngày:** 2026-09-06 · **Trạng thái:** ✅ ĐÓNG 08/09 — cả hai chặng xong, smoke tick đủ, 1 ô DoD còn [~] về ngân sách thời gian
>
> Chia hai chặng như P3, P4. Khối smoke tách theo chặng **trước khi** đưa người dùng tick.
> Theo [`../roadmap.md`](../roadmap.md). Quy ước: [`README.md`](README.md).

## Mục tiêu

Lễ tân lập hóa đơn từ lịch đã hoàn thành, ghi nhận tiền khách trả kể cả trả từng phần, và sổ sách
không lệch khi lịch bị hủy.

**User story:** US-19 → US-21 · **Test case:** TC-065 → TC-075 (11 ca) · và nối bước 7→9 của TC-101

Đây là phase đề bài **yêu cầu đích danh phải có test** (mục 4: *"có test cho lịch hẹn, hóa đơn, hồ sơ
và AI"*).

## Checklist

### Sửa tài liệu trước — code phải khớp spec, không phải ngược lại

- [x] 0. `test-cases.md` TC-066 — viết lại cho đúng thứ kiểm được thật ở P5 (xem quyết định 8)

### Chặng 1 — Hóa đơn và thanh toán (dừng lại sau chặng này)

- [x] 1. Ba model `invoices`, `invoice_items`, `payments` + ràng buộc CSDL
- [x] 2. `app/services/billing.py`: `lap_hoa_don`, `ghi_nhan_thanh_toan`, `huy_hoa_don`,
      `trang_thai_tinh_lai`, `danh_sach`, `lay_hoa_don` — TC-065 → TC-073
- [x] 3. Phép canh thứ 8 trong `test_architecture.py`: chuỗi trạng thái hóa đơn chỉ xuất hiện trong
      `models/invoice.py` và `services/billing.py`
- [x] 4. Router + trang `/invoices` (danh sách) và `/invoices/{id}` (chi tiết + form thu tiền)
- [x] 5. Nút "Lập hóa đơn" / "Xem hóa đơn" trên lưới lịch hẹn; link menu cho `manager` và
      `receptionist`; `tien()` thành filter dùng chung
- [x] 6. Dữ liệu mẫu trong `app/seed.py`, báo cáo chặng 1, commit, **dừng cho người dùng xem**

### Chặng 2 — Chặn hủy lịch đã có hóa đơn, và e2e

- [x] 7. `scheduling.huy_lich` chặn khi lịch còn hóa đơn chưa hủy, thông báo nêu mã hóa đơn —
      TC-074, TC-075
- [x] 8. Nối bước 7→9 vào `tests/e2e/test_full_flow.py` → TC-101 lên **9/11 bước**
- [x] 9. Cập nhật `codebase-map.md`, `test-cases.md`, `erd.md` nếu lệch, log phiên
- [x] 10. Báo cáo P5 đầy đủ, khối smoke tách theo chặng, commit

## Chín quyết định

### 1. Hóa đơn chỉ lập từ lịch `done`

ERD cho `invoices.appointment_id` NULL để sau này bán gói không gắn lịch — **không làm**. US-19 chỉ
nói tới lịch hẹn. Cột vẫn nullable theo ERD nhưng không có đường nào trong ứng dụng tạo ra hóa đơn
rời.

### 2. `description` và `unit_price` được CHÉP vào dòng hóa đơn

Không tham chiếu lại `services.price` khi hiển thị. Đây là **quyết định giá trị nhất của phase** và
là điểm roadmap nêu đích danh:

- Hôm nay lập hóa đơn "Tắm và sấy — 150.000đ"
- Tháng sau quản lý tăng giá lên 200.000đ
- Mở lại hóa đơn cũ: nếu tham chiếu, nó **tự đổi thành 200.000đ**, sổ sách tháng trước lệch, doanh
  thu ở P6 sai theo, và không có dấu vết nào

Sai kiểu này **âm thầm**: không exception, không 500, không test đỏ trừ khi có test riêng cho đúng ca
đó. Giá phải trả để làm đúng: hai dòng gán lúc tạo. Ô smoke P5 kiểm thẳng ca đổi giá.

### 3. `total_amount` tính từ các dòng, không nhận từ form

Cùng luật với `end_at` ở P3. Hai nguồn số liệu cho cùng một con số thì sổ sách lệch mà không ai biết.

### 4 + 6. Cột `status` và luật hủy hóa đơn — hai quyết định này phụ thuộc nhau

Trình bày chung vì **quyết định 6 chính là điều kiện an toàn của quyết định 4**.

Cột `status` trộn hai loại thông tin khác hẳn nhau:

| Giá trị | Bản chất |
|---|---|
| `unpaid` / `partial` / `paid` | **Suy được** 100% từ tổng `payments` so với `total_amount` |
| `cancelled` | **Sự kiện độc lập**, không suy được từ đâu |

Cột trộn cache với sự kiện thì dễ vỡ. **Nhưng hủy hóa đơn đã có thanh toán bị chặn** (quyết định 6),
nên `cancelled` và ba trạng thái tiền **loại trừ nhau theo cấu trúc**: không bao giờ tồn tại hóa đơn
vừa `cancelled` vừa có tiền để tranh chấp xem giá trị nào đúng. Còn lại đúng một nguồn sự thật.

Bốn lớp bảo vệ, xếp theo độ chắc:

1. **Chỉ `ghi_nhan_thanh_toan()` được tạo bản ghi `payments`**, và nó luôn kết thúc bằng
   `_dat_lai_trang_thai()` trong cùng transaction. Không có đường nào thêm tiền mà không cập nhật.
2. **Chỉ `huy_hoa_don()` được ghi `cancelled`**, và nó từ chối khi đã có thanh toán.
3. **Hàm public `trang_thai_tinh_lai(hd)`** trả về giá trị suy từ `payments`. Test đi hết chuỗi
   `unpaid → partial → paid` và so cột lưu với giá trị suy ở **từng bước**, không chỉ bước cuối.
4. **Phép canh trong `test_architecture.py`:** bốn chuỗi `'unpaid'`, `'partial'`, `'paid'`,
   `'cancelled'` chỉ được xuất hiện trong `models/invoice.py` và `services/billing.py`. Router hay
   template viết thẳng chuỗi trạng thái là đỏ ngay.

**Giới hạn đã biết, không giấu:** hệ thống không biểu diễn được "khách đã trả rồi nhưng hủy dịch vụ".
Cửa hàng thật gặp chuyện này. Làm hoàn tiền tử tế cần thêm bảng và nằm ngoài đề bài, nên ở đây chỉ
chặn và ghi rõ trong báo cáo.

**Vì sao không bỏ cột và suy hết:** phải thêm `cancelled_at`, tức sửa ERD lần thứ ba — xem lý do ở
quyết định 8. Và mọi truy vấn ở P6 ("hóa đơn chưa thu") sẽ phải join sang `payments` và gộp nhóm thay
vì lọc một cột.

### 5. Số nợ là property tính từ `payments`, không lưu

Suy được thì đừng lưu. Ngược hẳn với quyết định 4, và khác nhau ở đúng một điểm: số nợ không có phần
nào là sự kiện độc lập.

### 7. `scheduling.py` sẽ import model `Invoice`

US-21 buộc lúc hủy lịch phải biết về hóa đơn. Đặt phép kiểm ở router thì vi phạm ranh giới mục 8.
Cho `scheduling` biết model `Invoice` — giống cách nó đã biết `Appointment` — chứ không gọi sang
`billing.py`, để tránh services phụ thuộc chéo nhau.

### 8. Giữ bảng `invoice_items`, và sửa TC-066 cho đúng sự thật

Ở P5 mỗi hóa đơn sinh từ một lịch hẹn nên bảng này **luôn chỉ có đúng một dòng**. Nói thẳng: theo
CLAUDE.md mục 2 thì đây là trừu tượng hóa cho code dùng một lần.

Nhưng cái thật sự sai **không phải cái bảng** — nó tốn khoảng 30 dòng model và một quan hệ. Cái sai
là **TC-066 đang nói dối**: "tổng bằng tổng các dòng" nghe như kiểm phép cộng nhiều số hạng, trong
khi nó luôn cộng đúng một số hạng. Sửa chỗ đó không cần đụng ERD. TC-066 viết lại thành: *"`total_amount`
bằng `qty × unit_price` của dòng dịch vụ, và không đọc lại `services.price` khi hiển thị"*.

Vì sao giữ bảng:

- Hai lần sửa spec trước đây (US-18 mâu thuẫn nội tại; lời nhắc tiêm kẹt vĩnh viễn) đều là **sửa cái
  sai**. Bỏ `invoice_items` sẽ là lần đầu đổi tài liệu đã nộp chỉ vì **bất tiện**. Dự án lấy "tài
  liệu và code đi song song" làm luận điểm chính; đổi tính chất lịch sử tài liệu từ *sửa khi sai*
  sang *sửa khi phiền* đắt hơn 30 dòng code.
- **Không** dùng lý lẽ "P6 sẽ cần": kiểm lại thì P6 không cần thật — lượt dịch vụ đếm được từ
  `appointments`, doanh thu theo dịch vụ chỉ cần `service_id` trên hóa đơn. Nói P6 cần là biện hộ.
- **Không** thêm "dòng phụ thu thủ công" để bảng có ích. Thêm tính năng để biện minh cho một cái bảng
  là lý luận ngược, đúng loại phình phạm vi mà mục 2 cấm.

### 9. Macro `tien()` thành filter dùng chung

Hiện nằm trong `services.html`; P5 cần nó ở 2–3 template nữa. Đăng ký một lần trong
`app/templates.py` thay vì chép đi chép lại.

> **Sửa lúc thực hiện, 06/09 — chặng 1.** Ràng buộc UNIQUE trên `appointment_id` kéo theo một hệ
> quả kế hoạch chưa nói: mỗi lịch hẹn chỉ có **đúng một hóa đơn trong suốt đời nó, kể cả hóa đơn đã
> hủy**. Hủy nhầm thì không lập lại được; đường đi tiếp là hủy luôn lịch hẹn rồi đặt lại. Giữ ràng
> buộc vì nó là thứ duy nhất chặn được hai request cùng lúc. Điều bắt buộc phải làm là để nó lộ ra
> tử tế — có test riêng cho việc lập lại ra `LoiNghiepVu` nêu mã hóa đơn cũ, không phải màn hình đen.

> **Sửa lúc thực hiện, 07/09 — chặng 2, quyết định 7 và US-21.** Bước 7 không làm được đúng như
> viết. Quyết định 1 (*hóa đơn chỉ lập từ lịch `done`*) cộng với luật cũ ở P3 (*`done` là cửa một
> chiều, không hủy được*) khiến **TC-075 không thể đúng**: lịch có hóa đơn thì luôn `done`, nên hủy
> hóa đơn xong vẫn không hủy lịch được. Chạy thử để chắc, không suy luận suông — cả hai lần đều ra
> `Lịch ở trạng thái "Hoàn thành" nên không hủy được.`
>
> Người dùng chọn **sửa spec, giữ luật**: cho hủy lịch `done` sẽ để lại hồ sơ chăm sóc nói buổi đã
> diễn ra gắn với một lịch nói không diễn ra, và kéo theo cách đếm lượt dịch vụ ở P6 — phình phạm vi
> cho một ca hiếm. US-21, TC-075 và khối smoke chặng 2 được viết lại cho khớp thứ hệ thống bảo đảm
> thật: **hai lớp chặn độc lập**, lớp hóa đơn nhả ra khi hóa đơn bị hủy, lớp trạng thái vẫn giữ.
>
> Phép kiểm hóa đơn vẫn được thêm, và chạy **trước** phép kiểm trạng thái — thứ nó thêm vào là
> *thông báo*: nêu mã hóa đơn thay vì chỉ nói lịch đã hoàn thành. Kèm theo, khung "Hóa đơn này đã
> hủy" viết hôm 07/09 đang bảo người dùng *"hãy hủy luôn lịch hẹn"* — việc hệ thống luôn từ chối.
> Đã sửa, và có test kiểm cả hai vế trong cùng một ca.

> **Sửa lúc thực hiện, 06/09 — quyết định 4+6, lớp bảo vệ thứ 4.** Phép canh chỉ nhận **ba** chuỗi
> `unpaid`, `partial`, `paid`, không nhận `cancelled`: chuỗi đó cũng là trạng thái lịch hẹn và đã
> nằm ở bốn file khác, canh cả bốn thì phải mở bốn ngoại lệ và phép canh mất giá trị. Ba chuỗi tiền
> vừa là phần không nhập nhằng vừa là phần nguy hiểm — gán sai `cancelled` thì nhìn thấy ngay, gán
> sai `paid` thì sổ sách lệch trong im lặng.

## Ràng buộc CSDL

| Bảng | Điểm đáng chú ý |
|---|---|
| `invoices` | `appointment_id` **UNIQUE** — chặn hóa đơn thứ hai ở tầng CSDL (TC-068); `total_amount` CHECK ≥ 0; CHECK `status` ∈ 4 giá trị |
| `invoice_items` | `qty` CHECK > 0; `unit_price` CHECK ≥ 0; tiền dùng `Numeric(12,2)`, **không** `Float` |
| `payments` | `amount` CHECK > 0 (TC-073 chặn ở cả hai tầng); `method` ∈ `cash`/`transfer`/`card` |

## Giao diện

- `/invoices` — danh sách, chưa thu xếp lên đầu
- `/invoices/{id}` — chi tiết, các dòng, lịch sử thanh toán, form thu tiền, nút hủy hóa đơn
- Lưới lịch hẹn: nút **"Lập hóa đơn"** với lịch `done` chưa có hóa đơn, **"Xem hóa đơn"** nếu đã có
- Link menu **Hóa đơn** cho `manager` và `receptionist` — `caretaker` không có quyền (US-02)

## Definition of Done

- [x] TC-065 → TC-075 chuyển ✅ (11 ca) — và đóng nốt TC-026, TC-031 treo từ P2
- [x] Tổng `payments` không bao giờ vượt `total_amount`, có test ca biên trả **đúng bằng** số nợ
- [x] Cột `status` khớp `trang_thai_tinh_lai()` ở **từng bước** của chuỗi chuyển trạng thái
- [x] TC-101 lên **9/11 bước**; kịch bản e2e vẫn đi bằng link và nút, không tự dựng URL
- [~] `pytest` toàn bộ xanh, không skip (473 ca) — nhưng tầng unit 23–26s, **trên** ngưỡng xem lại
      20s. Đã kiểm chứng là của máy chứ không của test mới; đo lại ở P6 trên máy rảnh
- [x] Báo cáo trong [`../testing/reports/`](../testing/reports/) có output pytest thật + kết quả đột biến
- [x] Khối smoke P5 tách theo chặng, tick đủ trên trình duyệt thật — **31 ô của P5 đã tick hết**
      (15 chặng 1 + 9 rà 07/09 + 3 chặng 2 + 4 rà 08/09)

## Ngoài phạm vi

Hoàn tiền. Hóa đơn bán gói không gắn lịch. Xuất PDF hoặc in hóa đơn. Thống kê doanh thu (P6) — dù
`payments` chính là nguồn dữ liệu của nó.
