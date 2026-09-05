# P4 — Hồ sơ chăm sóc và tiêm phòng

> **Phase:** P4 · **Mốc:** KT2 — phase cuối của mốc này · **Duyệt ngày:** 2026-09-05 · **Trạng thái:** code xong,
> chờ smoke chặng 2
>
> Chia hai chặng như P3. **Khối smoke tách theo chặng ngay từ đầu** — áp dụng luật ở đầu
> [`../testing/smoke-checklist.md`](../testing/smoke-checklist.md), lần này không đợi phạm rồi sửa.
> Theo [`../roadmap.md`](../roadmap.md). Quy ước: [`README.md`](README.md).

## Mục tiêu

Nhân viên chăm sóc ghi lại việc đã làm sau mỗi buổi; lễ tân tra được lịch sử của từng thú cưng và
danh sách thú cưng đến hạn tiêm.

**User story:** US-15 → US-18, và TC-020 hoãn từ P2a · **Test case:** TC-053 → TC-064 (12 ca)

## Checklist

### Sửa tài liệu trước — code phải khớp spec, không phải ngược lại

- [x] 0a. `user-stories.md` US-18 — viết lại khoảng lấy, gỡ mâu thuẫn nội tại
- [x] 0b. `test-cases.md` TC-062 — sửa theo US-18
- [x] 0c. `erd.md` `vaccinations.given_at` — kiểm ở tầng services, không CHECK

### Chặng 1 — Hồ sơ chăm sóc (dừng lại sau chặng này)

- [x] 1. Model `care_records` + ràng buộc CSDL
- [x] 2. `app/services/care_records.py` — TC-053 → TC-056
- [x] 3. Router + nút "Ghi hồ sơ" trên trang lịch của nhân viên
- [x] 4. Lịch sử chăm sóc — TC-057, TC-058
- [x] 5. Hồ sơ mẫu trong `seed_basic` và `app/seed.py`
- [x] 6. Báo cáo chặng 1, commit, **dừng cho người dùng xem**

### Chặng 2 — Tiêm phòng và trang thú cưng

- [x] 7. Model `vaccinations` + `app/services/vaccinations.py` — TC-059 → TC-061
- [x] 8. Danh sách đến hạn — TC-062 → TC-064
- [x] 9. Trang `/pets/{id}` gộp lịch sử chăm sóc + hồ sơ tiêm — TC-020 hoãn từ P2a
- [x] 10. **Sửa lỗi có sẵn:** xóa thú cưng còn tham chiếu → 500, test tái hiện đỏ trước _(làm sớm ở chặng 1 — xem Điều chỉnh)_
- [x] 11. Cập nhật `codebase-map.md`, `test-cases.md`, log phiên
- [x] 12. Báo cáo P4 đầy đủ, smoke, commit

## Chín quyết định

Bảy quyết định ban đầu, sau khi tự phản biện thành chín. Bốn điểm B–E dưới đây là phần sửa.

### 1. `done` chỉ đặt được qua việc ghi hồ sơ

Không có nút "đánh dấu hoàn thành" riêng. Trạng thái phản ánh việc đã làm thật, không phải nhãn bấm
tay. Đây cũng là chỗ đóng vòng với P3: sau khi `done`, nút Đổi/Hủy biến mất.

**Hệ quả phải nói rõ:** hệ thống **không biểu diễn được** trạng thái "buổi chăm sóc đã diễn ra nhưng
chưa ai ghi hồ sơ". Nhân viên quên ghi thì lịch nằm `booked` vĩnh viễn và P6 không đếm nó là lượt
dịch vụ đã làm.

Vẫn không thêm nút riêng: hai đường tới cùng một trạng thái thì `done` mất nghĩa "đã có hồ sơ", và
mọi thứ dựa vào nó ở P6, P7 đều lung lay. Thay vào đó **ghi vào roadmap P6**: đếm số lịch đã qua giờ
mà vẫn `booked`, hiện như chỉ báo "hồ sơ còn thiếu". Biến khuyết điểm của mô hình thành một con số
hữu ích thay vì giấu đi.

### 2. `performed_at` lấy từ `appointment.start_at`, không phải lúc bấm nút

Nhân viên ghi hồ sơ sáng hôm sau thì buổi chăm sóc vẫn phải nằm đúng chỗ trong lịch sử. Lấy
`clock.now()` sẽ làm sai thứ tự ở TC-057.

Đây là bản sao, mà bản sao thì có thể lệch. Lý do nó **không thể** lệch: lịch `done` không đổi giờ
được nữa, `TRANG_THAI_SUA_DUOC` ở P3 đã chặn. **P4 đang dựa vào một ràng buộc của P3** — nếu ai nới
`TRANG_THAI_SUA_DUOC` ở phase sau thì `performed_at` âm thầm sai. Ghi rõ trong docstring.

### 3. `pet_id` suy ra từ lịch hẹn, không nhận từ form

Cho người dùng nhập thì hai nguồn sẽ lệch và lịch sử của thú cưng sai mà không ai biết.

**Nói thật:** cột này **thừa** — suy được bằng một join qua `appointments`, và lý do "truy vấn nhanh"
trong ERD không đứng vững ở quy mô này. Vẫn giữ vì ERD là sản phẩm đã nộp ở KT1 và giá phải trả chỉ
là một dòng gán. Đây là chỗ **duy nhất** trong P4 theo tài liệu thay vì theo YAGNI.

### 4. Quyền ghi hồ sơ — và `staff_id` lấy từ đâu

`caretaker` chỉ cho lịch của **chính mình** (TC-054); `manager` cho mọi lịch; `receptionist` chỉ xem
— theo bảng phân quyền US-02.

**`care_records.staff_id` LUÔN lấy từ `appointment.staff_id`, không bao giờ từ người đang đăng
nhập.** Lấy `current_user.id` là phản xạ tự nhiên và sai: quản lý ghi hộ một buổi sẽ làm lịch sử ghi
quản lý là người tắm chó, trong khi US-16 đòi mỗi dòng có tên người **làm việc**. Cần test riêng cho
ca quản lý ghi hộ.

### 5. Chặn ghi hồ sơ cho lịch chưa diễn ra và lịch đã hủy

Lịch `cancelled` gần như không tới được qua giao diện — nút sẽ không hiện. Ràng buộc đó là lớp chặn
cuối, rẻ, giữ.

**Lỗ thật là lịch chưa diễn ra:** nút hiện ngay trên lịch tuần sau trong danh sách của nhân viên, bấm
vào là có hồ sơ cho buổi chưa xảy ra, đồng thời khóa luôn khả năng đổi/hủy. Chặn khi
`start_at > clock.now()`.

### 6. `given_at ≤ hôm nay` kiểm ở tầng services, không phải CHECK

Giống hệt `pets.birth_date` ở P2a: CHECK trong SQLite phải gọi `date('now')`, đi vòng qua
`clock.py` và test không cố định được thời gian. **ERD đang ghi sai chỗ này** — bước 0c sửa.

### 7. Danh sách đến hạn tiêm bao gồm cả bản ghi đã quá hạn

Khoảng lấy: **từ quá khứ tới hôm nay + 30 ngày**, sắp theo hạn tăng dần, quá hạn có nhãn riêng.

Quyết định này **mâu thuẫn với chữ trong US-18 và TC-062** đang có. Và US-18 tự mâu thuẫn: tiêu chí
một nói "chỉ thấy hạn trong 30 ngày tới", tiêu chí hai nói "quá hạn phải được đánh dấu rõ" — theo
tiêu chí một thì không bản ghi quá hạn nào lọt vào để mà đánh dấu.

**Sửa spec công khai ở bước 0a–0b trước khi code.** Im lặng code khác spec chính là lỗi lặp số một
của dự án.

### 8. Sửa lỗi có sẵn: xóa thú cưng còn tham chiếu → 500

Không phải chức năng mới của P4, mà là lỗi đang sống trong code từ P3:

```
Thú cưng có 1 lịch hẹn. Gọi xoa_thu_cung():
  → IntegrityError: FOREIGN KEY constraint failed
```

Router chỉ bắt `LoiNghiepVu` nên `IntegrityError` bay ra thành 500. `xoa_chu_nuoi` đã chặn tử tế từ
P2a; `xoa_thu_cung` thì không, và không test nào phủ ca này.

P4 làm nặng thêm vì thú cưng sắp có thêm `care_records` và `vaccinations` trỏ vào. Sửa theo đúng luật
của `xoa_chu_nuoi`, **test tái hiện chạy đỏ trước** (luật 2 chống test giả).

### 9. Tách khối smoke theo chặng ngay từ đầu

Bốn lần trước có ô được tick cho thứ chưa kiểm được. Lần này khối smoke P4 tách sẵn thành chặng 1 và
chặng 2 trước khi đưa, và mỗi ô phải qua câu hỏi: *dựng được trạng thái ban đầu bằng giao diện hiện
tại không?*

## Ràng buộc CSDL

| Bảng | Điểm đáng chú ý |
|---|---|
| `care_records` | `appointment_id` **UNIQUE** — chặn hồ sơ thứ hai ở tầng CSDL (TC-055); tầng service chặn lại để có thông báo tiếng Việt thay vì `IntegrityError` |
| | `condition_note` NOT NULL — bắt buộc (TC-056) |
| `vaccinations` | `dose_no` CHECK > 0; `next_due_at` CHECK ≥ `given_at` (TC-060); `given_at ≤ hôm nay` kiểm ở service |

## Giao diện

- Nút **"Ghi hồ sơ"** trên `/appointments/cua-toi`, chỉ hiện với lịch của mình, đã diễn ra, còn hiệu lực
- `/pets/{id}` — trang mới, gộp thông tin thú cưng + lịch sử chăm sóc + hồ sơ tiêm (TC-020)
- `/vaccinations` — danh sách đến hạn, có dòng ghi rõ **lịch tiêm cụ thể do bác sĩ thú y quyết định**
  (bắt buộc theo [`../ai-safety.md`](../ai-safety.md) dù màn hình này chưa dính AI)

## Definition of Done

- [x] TC-053 → TC-064 chuyển ✅ (12 ca), và TC-020 hoãn từ P2a cũng ✅
- [x] Lỗi xóa thú cưng còn tham chiếu đã sửa, có test tái hiện từng chạy đỏ
- [x] `pytest` toàn bộ xanh, output sạch, không test nào bị skip
- [x] Ba sửa đổi tài liệu ở bước 0 hoàn tất **trước** khi viết code
- [x] `codebase-map.md` cập nhật đúng thực tế (`test_architecture.py` sẽ tự bắt nếu quên)
- [x] Báo cáo trong [`../testing/reports/`](../testing/reports/) có output pytest thật
- [ ] Khối smoke P4 tách theo chặng, tick đủ trên trình duyệt thật
- [ ] **Mốc KT2 hoàn tất**

## Điều chỉnh so với kế hoạch gốc

**Bước 10 làm sớm ở chặng 1.** Kế hoạch xếp việc sửa lỗi xóa thú cưng vào chặng 2. Đợt rà luồng sau
chặng 1 xác nhận nó trả **500 thật qua HTTP**, và người dùng sắp smoke test — để một lỗi 500 sống
trong app trong lúc người ta bấm thử là không chấp nhận được. Chuyển lên làm ngay.

**Hai lỗi khác không có trong kế hoạch, tìm ra khi rà luồng:**

1. **`/pets/{id}` không có link nào trỏ tới.** Trang tồn tại, chạy đúng, có test HTTP xanh — nhưng
   không ai bấm tới được vì test viết theo URL chứ không đi theo đường bấm. Ô smoke "Mở `/pets/{id}`"
   sẽ buộc người dùng gõ URL bằng tay. Đã thêm link ở tên thú cưng trên trang chủ nuôi và trên lưới
   lịch hẹn.
2. **Quản lý ghi hồ sơ hộ xong bị đẩy sang trang rỗng.** Redirect cứng về `/appointments/cua-toi`,
   mà quản lý không được phân lịch nào nên trang đó luôn trắng — vừa làm xong một việc thì không có
   dấu hiệu nào cho biết đã lưu. Nay điều hướng theo vai trò.

Cả ba đều có test tái hiện chạy **đỏ trước**, đúng luật 2 chống test giả. Cả ba đều là loại lỗi mà
test tầng HTTP viết theo URL không bắt được — chúng chỉ lộ ra khi đi hết luồng như người dùng thật.

## Ngoài phạm vi

Hóa đơn và ràng buộc "hủy lịch đã lập hóa đơn" (TC-021, P5). AI tóm tắt hồ sơ (P7) dù `care_records`
chính là nguồn dữ liệu của nó. Sửa và xóa hồ sơ chăm sóc — US-15 chỉ nói tạo. Chỉ báo "hồ sơ còn
thiếu" ở P6.


## Bổ sung ở chặng 2

**Sửa spec lần hai trước khi code — US-18 và TC-062.** Thiết kế `den_han()` lộ ra một chỗ US-18
chưa nói tới: nếu tính mọi bản ghi trong khoảng thì mũi 1 tiêm năm ngoái, hạn nhắc đã qua, sẽ nằm
lì trong danh sách quá hạn **vĩnh viễn** kể cả khi mũi 2 đã tiêm đúng hạn. Lời nhắc đã hoàn thành
mà không bao giờ tắt được thì cả màn hình mất tác dụng. Thêm tiêu chí **chỉ tính mũi mới nhất của
mỗi loại vắc-xin trên mỗi thú cưng**, sửa công khai ở `user-stories.md` và `test-cases.md` **trước
khi** viết code — cùng cách xử lý như mâu thuẫn US-18 phát hiện ở bước 0.

**Thêm `app/routers/pets.py`.** Trang `/pets/{id}` nằm nhờ trong `care_records.py` từ chặng 1. Sang
chặng 2 nó gộp thêm hồ sơ tiêm nên thuộc về hai miền nghiệp vụ; tách ra router riêng đúng như cây
thư mục đã ghi trong [`../architecture.md`](../architecture.md) từ KT1.

**Ô `checkbox` trong smoke bị bỏ một ô, có ghi lý do.** Trạng thái rỗng của danh sách đến hạn
(TC-064) không dựng được bằng giao diện vì không có chức năng xóa mũi tiêm. Ghi rõ trong checklist
thay vì đưa một ô không ai tick thật được — đúng luật quyết định 9.
