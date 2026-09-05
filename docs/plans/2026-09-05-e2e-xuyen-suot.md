# Kế hoạch — Kéo `tests/e2e/test_full_flow.py` lên sớm (TC-101, bước 1→6)

- **Ngày:** 2026-09-05
- **Người duyệt:** người dùng — *"kéo test_full_flow.py lên làm sớm đi"*
- **Phase gốc:** P5 (theo [`../roadmap.md`](../roadmap.md)); kéo lên sau P4 chặng 1

## Vì sao kéo lên

Chín lỗi tìm được ngày 05/09 đều lọt qua toàn bộ test tầng HTTP. Năm trong số đó cùng một gốc:
**test đi theo URL, người dùng đi theo link và theo trạng thái.** Test tự dựng
`client.post("/appointments", data={...})` nên không bao giờ chạm tới thứ trình duyệt thật gửi đi —
mà chính thứ đó (ô `<select>` không có option nào `selected` thì gửi option đầu tiên) là nguyên nhân
lỗi nặng nhất: đổi lịch của nhân viên đã khóa làm lịch âm thầm sang tên người khác.

Đợi tới P5 mới viết e2e nghĩa là hai phase nữa trôi qua mà không có lưới nào bắt loại lỗi này.

## Ràng buộc thiết kế — điều kiện để test có giá trị

1. Kịch bản **chỉ được đi theo link và nút lấy từ HTML trả về**. Địa chỉ gõ tay duy nhất là `/`.
2. Form phải được gửi **đúng như trình duyệt gửi**: mọi trường trong form (kể cả `hidden`), và
   `<select>` không có option `selected` thì lấy **option đầu tiên**.
3. Chọn trong `<select>` bằng **nhãn nhìn thấy**, không bằng id — người dùng không biết id.
4. Gửi một trường không có trong form là lỗi của test, không phải của hệ thống → báo lỗi ngay.
5. Chạy trên **CSDL file thật**, mỗi request một session riêng như production, để bắt được lỗi
   "quên commit" mà fixture in-memory dùng chung session che mất.

## Phạm vi

Kịch bản 11 bước ở [`../testing/test-strategy.md`](../testing/test-strategy.md) mục 6 cần tới P7 mới
đủ mắt xích. Chặng này làm **bước 1 → 6**; bước 7→11 (hóa đơn, thanh toán, AI, thống kê) nối tiếp ở
P5, P6, P7. TC-101 vì vậy để 🟡, không được tick ✅.

## Checklist

- [x] 1. Viết `tests/e2e/test_full_flow.py`: trình duyệt tí hon (bóc link + form từ HTML) và kịch bản
      bước 1→6 → verify: `pytest tests/e2e` xanh
- [x] 2. Chứng minh test bắt được lỗi bằng 3 thử nghiệm đột biến → verify: mỗi đột biến làm e2e đỏ,
      hoàn nguyên xong xanh lại
- [x] 3. Cập nhật `docs/testing/test-cases.md`: TC-101 ⬜ → 🟡 kèm ghi chú phạm vi bước 1→6
- [x] 4. Cập nhật `docs/codebase-map.md`: chuyển `tests/e2e/test_full_flow.py` sang mục "Hiện có"
- [x] 5. Cập nhật `docs/testing/test-strategy.md` mục 6: đánh dấu bước nào đã chạy được
- [x] 6. Chạy lại toàn bộ suite → verify: số thật ghi vào log phiên

## Kết quả

Xong cả 6 bước. Báo cáo: [`../testing/reports/2026-09-05-e2e-xuyen-suot.md`](../testing/reports/2026-09-05-e2e-xuyen-suot.md).

Điểm đáng ghi nhất: đột biến "bỏ dấu `selected` ở ô chọn nhân viên" làm e2e đỏ trong khi **cả 344
test unit + integration vẫn xanh**. Tầng e2e không trùng lặp ba tầng kia.
