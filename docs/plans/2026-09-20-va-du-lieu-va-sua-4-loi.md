# Kế hoạch 20/09 — vá dữ liệu D-01 và sửa 4 lỗi ưu tiên

**Người dùng duyệt:** 20/09, qua hai vòng hỏi (6 câu). **Mốc code khi bắt đầu:** `1ce61f2`
· Nguồn lỗi: [`../testing/reports/2026-09-19-ra-luong-P1-P7.md`](../testing/reports/2026-09-19-ra-luong-P1-P7.md)
· [`../testing/reports/2026-09-20-ra-bo-sung-P1-P7.md`](../testing/reports/2026-09-20-ra-bo-sung-P1-P7.md)

## Quyết định người dùng đã chốt

| # | Câu hỏi | Chốt |
|---|---|---|
| 1 | Vá D-01 cách nào | **Khôi phục từ `petcare.backup-2026-09-19.db`** — mất toàn bộ dữ liệu rà "Rà 19/09" |
| 2 | Sửa lỗi nào | **M-02, M-01, M-04, M-08** (4 lỗi ưu tiên) |
| 3 | M-02 tới đâu | **Đầy đủ**: sửa chủ nuôi + thú cưng + tài khoản + mật khẩu |
| 4 | Rà Chrome lúc nào | **Rà trước, gom lỗi, rồi sửa một thể** |
| 5 | Mật khẩu: ai đặt cho ai | **Cả hai** — quản lý đặt lại cho nhân viên, và mọi vai trò tự đổi (phải nhập mật khẩu cũ) |
| 6 | Quy tắc mật khẩu | **≥ 8 ký tự**, một luật duy nhất |

**Người dùng tự tick smoke sau** — agent không tick ô smoke nào (bài học 2).

## Thứ tự và lý do

Vá D-01 **trước** lượt rà, vì rà trên dữ liệu đã sạch thì con số thống kê mới đối chiếu được.
Lượt rà chạy trên **bản sao** của CSDL đã khôi phục (cổng 8001) để `petcare.db` thật giữ nguyên
trạng thái sạch cho người dùng bấm smoke — lượt rà 19/09 chạy thẳng trên CSDL thật và chính nó
đẻ ra đống rác giờ phải xóa.

---

## Chặng 0 — Vá D-01

- [x] Sao lưu `petcare.db` hiện tại sang `petcare.truoc-khoi-phuc-2026-09-20.db` (không vào git)
- [x] Khôi phục `petcare.db` từ `petcare.backup-2026-09-19.db`
- [x] Xác minh: không còn hóa đơn nợ âm; số chủ nuôi/thú cưng/dịch vụ về mức seed
- [x] Xác minh trên trang thống kê: Doanh thu và Chưa thu khớp tổng `payments` và `invoices`

## Chặng 1 — Rà toàn hệ thống bằng Chrome, chỉ gom lỗi

Chạy trên **bản sao** trong scratchpad, cổng 8001. Chỉ tìm và ghi, **chưa sửa gì**.

- [x] Dựng bản sao + server 8001; Chrome mở được trang đăng nhập
- [x] R1 Đăng nhập, menu và thẻ trang chủ theo **cả ba vai trò** (soát luôn L-01)
- [x] R2 Chủ nuôi, thú cưng — *đã rà đầy đủ bằng HTTP sáng 20/09 (`2026-09-20-ra-bo-sung-P1-P7.md`); lượt Chrome này chỉ quét 500/trang trắng*
- [x] R3 Dịch vụ và gói: thêm, sửa giá, ngưng bán, bán lại, tạo gói
- [x] R4 Lịch hẹn — *rà kỹ 19/09; lượt này kiểm lại 4 ca cốt lõi: đặt mới ✓, trùng y hệt → 400 ✓, liền kề → nhận ✓, ngày sai → 400 ✓*
- [x] R5 Hồ sơ và tiêm phòng — *rà kỹ 19/09; lượt này kiểm lại: ghi hồ sơ cho lịch tương lai → 400 ✓*
- [x] R6 Hóa đơn — *rà kỹ 19/09 và bằng HTTP sáng 20/09; lượt này kiểm lại: lập hóa đơn cho lịch chưa làm → 400 ✓*
- [x] R7 Thống kê: đối chiếu số với CSDL
- [x] R8 Ba tính năng AI (chế độ `fake`, không tiêu lượt Gemini)
- [x] R9 Bốn lỗi sắp sửa — **tái hiện trên Chrome trước khi sửa**: M-01, M-02, M-04, M-08
- [x] Viết báo cáo `../testing/reports/2026-09-20-ra-chrome-P1-P7.md`

## Chặng 2 — Sửa ba lỗi nhỏ

Mỗi lỗi: **test đỏ trước → sửa → test xanh → đột biến bị bắt** (luật mục 7).
Mỗi lỗi soát cả **lớp lỗi**, không chỉ ca vừa thấy (bài học 4).

- [x] **M-01** chuyển hướng mở `?tu=` — chặn `\`, ký tự điều khiển, và mọi dạng không phải đường dẫn nội bộ
- [x] M-01: soát **mọi** chỗ nhận URL quay lại, không chỉ chỗ đã biết
- [x] **M-04** mật khẩu ≥ 8 ký tự — áp cho cả tạo tài khoản, đặt lại, và tự đổi
- [x] **M-08** tin nhắc tiêm lặp khuyến cáo hai lần — bỏ một trong hai nguồn
- [x] M-08: soát cả ba tính năng AI xem còn chỗ nào nối câu trùng system prompt

## Chặng 3 — Sửa M-02 (việc lớn nhất)

- [x] Sửa **chủ nuôi**: router + form (`sua_chu_nuoi` đã có trong service kèm unit test)
- [x] Sửa **thú cưng**: router + form (`sua_thu_cung` đã có)
- [x] Sửa **tài khoản**: họ tên, vai trò
- [x] **Quản lý đặt lại mật khẩu** cho nhân viên (không cần mật khẩu cũ)
- [x] **Tự đổi mật khẩu** cho mọi vai trò (phải nhập mật khẩu cũ)
- [x] Phân quyền: ai được sửa gì — có test cho từng vai trò
- [x] Cập nhật `user-stories.md`/`test-cases.md` nếu tiêu chí US-03, US-04 đổi trạng thái

## Chặng 4 — Đóng phiên

- [x] Chạy đủ bốn tầng test, ghi số thật
- [x] Cập nhật `codebase-map.md` (file mới, khối "Làm tiếp"), `roadmap.md`, ma trận `test-cases.md`
- [x] Điền log phiên `../sessions/2026-09-20-05.md`
- [x] **Không tick ô smoke nào** — người dùng tự bấm
- [x] Hỏi người dùng có commit không — *đồng ý, commit `0f17f52`; chưa push*
