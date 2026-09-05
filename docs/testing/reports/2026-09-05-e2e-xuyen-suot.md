# Báo cáo — `tests/e2e/test_full_flow.py`, TC-101 bước 1 → 6

- **Ngày:** 2026-09-05
- **Kế hoạch:** [`../../plans/2026-09-05-e2e-xuyen-suot.md`](../../plans/2026-09-05-e2e-xuyen-suot.md)
- **Phase gốc:** P5 — kéo lên sớm theo yêu cầu của người dùng

## 1. Test này khác gì bốn tầng đã có

Mọi test tầng HTTP hiện có đều gọi thẳng địa chỉ và tự dựng dữ liệu form:

```python
client.post("/appointments", data={"thu_cung_id": "1", "nhan_vien_id": "3", ...})
```

Người dùng thì không làm thế. Họ bấm vào link đang hiện, và trình duyệt gửi **toàn bộ** trường trong
form — kể cả trường họ không chạm tới. Khoảng cách giữa hai điều đó chính là chỗ năm trong chín lỗi
của ngày 05/09 đã trốn.

`test_full_flow.py` đóng khoảng cách ấy bằng một trình duyệt tí hon (`TrinhDuyet`, ~120 dòng, chỉ
dùng `html.parser` của thư viện chuẩn):

| Quy tắc | Cài đặt |
|---|---|
| Chỉ đi bằng link có thật | `bam("Chủ nuôi")` tìm thẻ `<a>` có chữ đó; không thấy thì đỏ |
| Địa chỉ gõ tay | đúng một lần, `mo("/")` |
| Gửi form như trình duyệt | gửi mọi trường của form, gồm `hidden` và giá trị mặc định |
| `<select>` không có `selected` | lấy **option đầu tiên** — đúng hành vi trình duyệt |
| Chọn theo nhãn, không theo id | `thu_cung_id="Miu"`, không phải `thu_cung_id="1"` |
| Gửi trường không có trong form | ném lỗi ngay: lỗi của test, không phải của hệ thống |
| Ô `checkbox`/`radio` | ném `NotImplementedError` thay vì đoán — dự án chưa dùng ô nào như vậy |

Chạy trên **CSDL file thật**, mỗi request một session riêng đúng như production. Fixture `db` dùng
chung một session cho cả test lẫn ứng dụng nên lỗi "quên commit" không lộ ra; ở đây thì lộ.

## 2. Kịch bản

Bước 1 → 6 của [`../test-strategy.md`](../test-strategy.md) mục 6: lễ tân đăng nhập → tạo chủ nuôi →
tạo hai thú cưng → đặt lịch → đặt lịch chèn giờ cho con thứ hai và **bị từ chối** → đổi lịch sang
khung trống → nhân viên chăm sóc đăng nhập, ghi hồ sơ → lịch chuyển *Hoàn thành* → lễ tân quay lại
thì không còn nút Đổi/Hủy.

Bước 7 → 11 cần hóa đơn, thống kê và AI. TC-101 vì vậy để **🟡**, không tick ✅.

Một chi tiết cố ý trong dữ liệu mẫu: có **hai** nhân viên chăm sóc, và người được phân lịch
(`Le Van Cham`) **không** phải người đứng đầu danh sách (`Bui Thi An`, xếp theo tên). Chỉ một nhân
viên thì bước "đổi lịch giữ nguyên người thực hiện" xanh một cách tình cờ.

## 3. Chứng minh test bắt được lỗi

Test viết sau code nên xanh ngay lần chạy đầu — theo bài học số 3 trong CLAUDE.md mục 9, như vậy chưa
chứng minh gì. Bốn thử nghiệm đột biến:

| Đột biến | Kết quả | Assert nào đỏ |
|---|---|---|
| Bỏ `selected` ở ô chọn nhân viên trong form đổi lịch | **đỏ** | `"Miu" in van_ban` ở *Lịch của tôi* — lịch đã sang tên người khác |
| Tắt kiểm tra trùng lịch | **đỏ** | `ma == 400` ở bước đặt lịch chèn giờ |
| `performed_at` lấy `clock.now()` thay vì giờ buổi chăm sóc | **đỏ** | ngày giờ trong lịch sử của thú cưng |
| `db.commit()` → `db.flush()` khi tạo chủ nuôi | **đỏ** | tên chủ nuôi không có trong danh sách sau khi thêm |

Sau khi hoàn nguyên cả bốn: xanh lại.

**Kết quả quan trọng nhất:** chạy riêng đột biến thứ nhất trên `tests/unit` + `tests/integration` →
**344/344 vẫn xanh, exit code 0.** Chỉ e2e đỏ. Đây là bằng chứng số cho thấy tầng này không trùng lặp
ba tầng kia: nó bắt đúng loại lỗi mà cách viết test cũ không thể chạm tới.

## 4. Kết quả chạy

```
$ pytest
345 passed in 31.30s

$ pytest tests/unit          240 passed in 11.82s   (ngân sách 15s)
$ pytest tests/integration   104 passed in 20.01s   (ngân sách 30s)
$ pytest tests/e2e             1 passed in  4.34s   (ngân sách: vài phút)
```

## 5. Giới hạn cần nói rõ

- Trình duyệt tí hon **không chạy JavaScript và không dựng bố cục**. Nó chứng minh luồng đi được và
  form gửi đúng; nó không thay được mắt người. Ba lỗi giao diện của ngày 05/09 (CSS thiếu
  `textarea`, bảng tràn ngang, thông báo lỗi đặt xa ô nhập) đều nằm ngoài tầm của nó.
- Một trang có hai form cùng nhãn nút sẽ làm test đỏ với thông báo "không rõ bấm cái nào". Cố ý:
  đoán bừa form nào cũng là mở lại đúng cánh cửa mà file này sinh ra để đóng.
