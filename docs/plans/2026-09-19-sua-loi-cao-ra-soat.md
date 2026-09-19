# Sửa ba lỗi mức cao tìm được khi rà soát P1 → P7

> **Duyệt ngày:** 2026-09-19 — người dùng chọn "3 lỗi cao H-01 → H-03" sau khi đọc
> [`../testing/reports/2026-09-19-ra-luong-P1-P7.md`](../testing/reports/2026-09-19-ra-luong-P1-P7.md).
> Mỗi lỗi: **test đỏ-trước → sửa → xanh → đột biến → soát cả lớp lỗi**.

## H-01 · Thu tiền đồng thời vượt số còn nợ

**Nguyên nhân:** pysqlite không mở transaction cho `SELECT`, nên `ghi_nhan_thanh_toan` đọc `con_no`
ngoài khóa; request thứ hai đọc số cũ trước khi request thứ nhất commit.

**Cách sửa:** trước khi đọc số còn nợ, chạy một câu `UPDATE` trên chính dòng hóa đơn để giành khóa
ghi (pysqlite mở `BEGIN` trước câu ghi đầu tiên; request kia phải chờ tới khi commit xong), rồi
`refresh` hóa đơn để đọc số liệu mới nhất.

**Test:** hai session trên cùng CSDL — session B đọc hóa đơn trước, session A thu và commit, rồi B
thu tiếp. Trước khi sửa B thu được (nợ âm); sau khi sửa B bị từ chối "vượt quá số còn nợ".

## H-02 · Ngày sai định dạng khi đặt/đổi lịch bị quy về hôm nay (S7)

**Cách sửa:** `dat_lich` và `doi_lich` trong `routers/appointments.py` đọc ngày bằng hàm chặt —
ngày trống hoặc sai định dạng → 400 "Ngày không đúng định dạng.", không đụng dữ liệu. Giữ
`_doc_ngay` dễ dãi cho trang GET và cho `huy`/`hoa-don` (ở đó ngày chỉ dùng để quay về lưới lịch).

**Test:** đổi lịch với `ngay=abc` → 400, giờ lịch giữ nguyên; đặt lịch với `ngay=2026-13-45` → 400,
không sinh lịch mới.

## H-03 · Lỗi 500 khi bản ghi không tồn tại

**Nguyên nhân chung:** 19 chỗ ném `LoiNghiepVu("Không tìm thấy …")`, nhưng `main.py` không có trình
xử lý chung cho `LoiNghiepVu` — router nào quên `try/except` là thành 500.

**Cách sửa (cả lớp lỗi):** thêm `LoiKhongTimThay(LoiNghiepVu)` cho các lần tra theo id; trình xử lý
chung trong `main.py`: `LoiKhongTimThay` → trang lỗi 404, `LoiNghiepVu` còn lọt → trang lỗi 400.
Là lớp con nên mọi `except LoiNghiepVu` đang có giữ nguyên hành vi.

**Test:** tham số hóa mọi route theo id đã biết lỗi (7 chỗ lúc rà + `GET /owners/{id}` +
`POST /services/goi/{id}/ban-lai` tìm thêm khi đọc code) → 404 với thông báo tiếng Việt.

## Checklist

- [x] H-01 test đỏ → sửa `billing.ghi_nhan_thanh_toan` → xanh → đột biến
- [x] H-02 test đỏ → sửa `routers/appointments.py` → xanh → đột biến
- [x] H-03 test đỏ → `LoiKhongTimThay` + trình xử lý trong `main.py` → xanh → đột biến
- [x] Kiểm lại trên server thật bằng Chrome: ba kịch bản của báo cáo rà soát
- [x] Toàn bộ pytest, `test-cases.md`, `roadmap.md` (S7 đã sửa), `codebase-map.md`, báo cáo, log phiên
