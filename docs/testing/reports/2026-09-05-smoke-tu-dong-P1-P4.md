# Báo cáo — Chạy smoke test P1 → P4 chặng 1 bằng trình duyệt thật

- **Ngày:** 2026-09-05
- **Cách chạy:** agent điều khiển Chrome qua extension Claude in Chrome, bấm chuột thật trên
  `http://127.0.0.1:8000` với CSDL seed sạch
- **Phạm vi:** 46 ô của các khối P1, P2, P3 chặng 1, P3 chặng 2, P4 chặng 1

## 1. Vì sao chạy, và giới hạn của cách chạy này

Người dùng yêu cầu kiểm luồng để tìm lỗi hệ thống trước khi tự tick checklist. Cần nói rõ ngay:
**agent bấm không thay thế được người bấm.** Agent kiểm được luồng có thông không, nút có hiện đúng
lúc không, thông báo có đúng chữ không. Agent **không** thay được nhận xét kiểu "bảng này chật quá",
"màu này chưa đủ rõ" — mà chính loại nhận xét đó đã tìm ra ba lỗi trước đây (giá gói đắt hơn mua lẻ,
ERD không render, ô tick cho chức năng chưa có).

Vì vậy các ô trong [`../smoke-checklist.md`](../smoke-checklist.md) **vẫn để trống** cho người dùng
tick. Báo cáo này là kết quả chạy của agent, ghi riêng.

## 2. Kết quả theo khối

| Khối | Đạt | Ghi chú |
|---|---|---|
| P1 — Đăng nhập, phân quyền | 8/8 | |
| P2 — Chủ nuôi, thú cưng, dịch vụ | 13/15 | 1 ô không đạt, 1 ô đạt một phần |
| P3 chặng 1 — Đặt lịch, chống trùng | 8/8 | |
| P3 chặng 2 — Đổi, hủy, xem theo vai trò | 5/5 | |
| P4 chặng 1 — Hồ sơ chăm sóc | 9/10 | ô `chamsoc2` gõ thẳng URL chỉ kiểm được bằng httpx (400) |

Ba lỗi đã sửa buổi sáng cùng ngày đều kiểm chứng lại bằng mắt: tên thú cưng thành link, quản lý ghi
hồ sơ xong về đúng trang thấy được lịch, xóa thú cưng còn tham chiếu ra 400 chứ không 500.

## 3. Sáu lỗi tìm được — và tất cả đều đã sửa

### Lỗi 1 — Đổi lịch của nhân viên đã khóa làm lịch âm thầm đổi chủ

Nghiêm trọng nhất. Kịch bản đi qua đúng luồng bình thường:

1. Quản lý khóa `chamsoc2` (đúng theo ô smoke P1 về tài khoản bị khóa)
2. Mở lưới lịch — lịch cũ của Phạm Thị Sóc vẫn hiện, đúng như thiết kế
3. Ô chọn nhân viên trong nút "Đổi" chỉ liệt kê nhân viên **đang hoạt động**, nên không option nào
   được chọn và trình duyệt gửi option **đầu tiên**
4. Bấm "Đổi" mà **không sửa gì** → hệ thống trả lời *"Nhân viên **Lê Văn Chăm** đã có lịch
   09:00–09:45 ngày 06/09."*

Nó đã cố chuyển lịch sang người khác. Chỉ bị chặn nhờ trùng giờ — nếu Lê Văn Chăm rảnh thì lịch đổi
chủ mà không ai biết.

**Sửa:** khi nhân viên của lịch không còn trong danh sách phân lịch, form vẫn chèn họ làm lựa chọn
đang chọn, ghi rõ "(đã ngưng)". Lớp chặn thứ hai ở tầng services (không phân lịch cho người đã khóa)
vốn đã đúng — test xác nhận.

### Lỗi 2 — Cảnh báo trùng số điện thoại không tồn tại trong luồng

Thêm chủ nuôi với số đã có → tạo thành công, **không cảnh báo gì**. US-04 yêu cầu cảnh báo.

Khối cảnh báo có sẵn trong template từ P2a nhưng chỉ hiện khi tự gõ `GET /owners?sdt_kiem_tra=…` —
**không nút nào trong giao diện sinh ra URL đó.** Và TC-015 vẫn ✅ suốt từ P2a vì test gọi thẳng
chính URL ấy:

```python
r = client.get("/owners?sdt_kiem_tra=0912345678")   # URL không ai tới được
```

**Sửa:** sau khi tạo, nếu còn chủ nuôi khác dùng số đó thì chuyển hướng kèm cảnh báo.
`tim_theo_so_dien_thoai()` nhận thêm `bo_qua_id` để không tự liệt kê bản ghi vừa tạo — nói "đã có
người dùng số này" mà trỏ vào chính nó thì vô nghĩa. Test cũ được **viết lại** để đi qua form.

### Lỗi 3 — URL không khớp route nào trả JSON thô

`/khong-co-trang-nay` → `{"detail":"Not Found"}` trên nền đen, trong khi `/pets/9999` ra trang 404 có
bố cục. **Link "Thống kê" trong menu quản lý dẫn thẳng vào đó.**

Nguyên nhân: handler đăng ký trên `fastapi.HTTPException`, còn route không khớp ném
`starlette.HTTPException` — lớp **cha**. Handler ở lớp con không bắt được lớp cha. Docstring của
chính hàm đó viết "404 hiển thị thành trang có bố cục, không phải JSON" — sai với ca này.

**Sửa:** đăng ký trên lớp Starlette; `fastapi.HTTPException` kế thừa nên một handler bắt cả hai.

### Lỗi 4 — CSS không tạo kiểu cho `textarea`

`style.css` chỉ có `input, select`. Form hồ sơ chăm sóc ở P4 là form **đầu tiên** trong dự án dùng
`<textarea>`, nên ba ô nhập lệch hẳn khỏi nhãn, chữ monospace, không giãn hết chiều rộng.

HTML vẫn đúng nên không test nào bắt được. **Sửa:** thêm `textarea` vào quy tắc khung dùng chung.

### Lỗi 5 — Lễ tân và nhân viên không có link menu "Dịch vụ"

Bảng phân quyền US-02 cho cả ba vai trò quyền **xem** bảng giá. Trang mở được, nhưng chỉ `manager`
có link — hai vai trò kia phải tự gõ URL.

### Lỗi 6 — Ghi chú lỗi thời trên trang chủ nuôi

*"Lịch sử chăm sóc và lịch tiêm sẽ hiển thị ở đây từ phase P4."* P4 chặng 1 xong rồi, và lịch sử nằm
ở `/pets/{id}`. **Sửa:** thay bằng "Bấm tên thú cưng để xem lịch sử chăm sóc và hồ sơ tiêm."

## 4. Ba điểm nhỏ, chưa sửa

- Thông báo lỗi form chủ nuôi hiện phía trên danh sách bên **trái**, cách xa ô nhập bên **phải**. Ô
  smoke đòi "ngay cạnh ô nhập". Sửa đúng cần đổi bố cục trang, để lại cho người dùng quyết định.
- Dữ liệu mẫu chỉ cho mỗi thú cưng **một** hồ sơ nên ô "lịch sử mới nhất lên đầu" không kiểm được
  bằng mắt. Cùng loại với vấn đề đã gặp ở P4 chặng 1: dữ liệu mẫu phải dựng sẵn **trạng thái**.
- Trang lịch hẹn tràn ngang ở bề rộng ~950px vì cột "Thao tác" rộng; chữ "Ghi hồ sơ" xuống hai dòng
  tạo vùng chết ở giữa, agent bấm trượt một lần.

## 5. Chứng minh test bắt được lỗi

Sáu test tái hiện, tất cả **chạy đỏ trước** khi sửa. Sau khi sửa, sáu thử nghiệm đột biến:

| Đột biến | Test đỏ |
|---|---|
| Bỏ option nhân viên đã khóa trong form đổi | `test_form_doi_lich_van_giu_nhan_vien_da_khoa_lam_lua_chon_hien_tai` |
| Không chuyển hướng kèm cảnh báo trùng số | `test_so_dien_thoai_trung_hien_canh_bao_ngay_sau_khi_them` |
| Đăng ký handler trên lớp con | `test_url_khong_khop_route_nao_van_hien_trang_loi_co_bo_cuc` |
| Bỏ `textarea` khỏi quy tắc khung | `test_moi_loai_o_nhap_deu_dung_chung_quy_tac_khung_voi_input` |
| Trả link Dịch vụ về chỉ quản lý | `test_moi_vai_tro_deu_co_link_menu_toi_bang_gia_dich_vu` ×2 |
| Trả lại ghi chú lỗi thời | `test_trang_chi_tiet_chu_nuoi_khong_hua_hen_phase_tuong_lai` |

**Lần đầu, đột biến số 4 KHÔNG đỏ.** Phép kiểm CSS ban đầu chỉ hỏi "có nhắc tới `textarea` ở đâu đó
trong bộ chọn không", mà tôi có thêm một quy tắc `textarea { … }` riêng nên nó vẫn xanh. Đã siết lại
thành: mọi thẻ nhập liệu dùng trong template phải nằm **cùng bộ chọn với `input` ở quy tắc khung**
(`width: 100%`). Chạy lại đột biến → đỏ đúng.

Đáng ghi lại: đây là ví dụ một phép kiểm **xanh vì lý do sai**. Nếu bỏ qua bước đột biến thì nó đã
nằm trong suite như một lá chắn giả.

## 6. Điều rút ra

Lỗi 1 và 2 cùng một gốc với ba lỗi tìm được buổi sáng: **test đi theo URL, người dùng đi theo trạng
thái và theo link.**

- Không test nào bắt được lỗi 1 vì không test nào dựng trạng thái "nhân viên bị khóa nhưng còn lịch cũ".
- Không test nào bắt được lỗi 2 vì test tự gọi URL mà form không bao giờ sinh ra.

Điều này định hình cách viết `tests/e2e/test_full_flow.py`: kịch bản phải **đi theo link và theo nút**
lấy từ HTML trả về, không được tự dựng URL. Viết theo kiểu cũ thì nó sẽ xanh mà vẫn để lọt đúng những
lỗi này.

## 7. Kết quả tự động sau khi sửa

```
$ pytest
344 passed in 29.41s
```

Tăng 9 test so với trước đợt rà (335).
