# Lộ trình dự án

Đề bài: [`../đề-bài.md`](../đề-bài.md) · Yêu cầu: [`user-stories.md`](user-stories.md) · Kiểm thử: [`testing/test-strategy.md`](testing/test-strategy.md)

Chín phase, gắn với bốn mốc nộp của môn học. Mỗi phase sinh ra một kế hoạch riêng trong
[`plans/`](plans/) và kết thúc bằng một báo cáo kiểm thử trong [`testing/reports/`](testing/reports/).

**Nguyên tắc chia phase:** mỗi phase phải chạy được và test được ngay khi xong, không phải "làm hết
model rồi mới làm router". Phase nào cũng để lại một hệ thống hoạt động, chỉ là ít chức năng hơn.

---

## Bảng tổng quan

| Phase | Nội dung | Mốc | User story | Test case | Definition of Done |
|---|---|---|---|---|---|
| **P0** | Bộ context, đặc tả, chiến lược kiểm thử | KT1 | — | — | Tài liệu đủ, ma trận test lập xong |
| **P1** | Scaffold, auth, phân quyền 3 vai trò | KT2 | US-01→03 | TC-001→012 | Unit + integration xanh; smoke P1 |
| **P2** | CRUD chủ nuôi, thú cưng, dịch vụ, gói | KT2 | US-04→09 | TC-013→031 | Unit + integration xanh; smoke P1–P2 |
| **P3** | Đặt/đổi/hủy lịch, **chống trùng lịch** | KT2 | US-10→14 | TC-032→052 | 21 TC lịch hẹn xanh; regression xanh |
| **P4** | Hồ sơ chăm sóc, lịch tiêm nhắc lại | KT2 | US-15→18 | TC-053→064 | Regression xanh; smoke P1–P4 |
| **P5** | Hóa đơn, thanh toán | KT3 | US-19→21 | TC-065→075, TC-101 | Regression xanh; **e2e xuyên suốt chạy được** |
| **P6** | Thống kê | KT3 | US-22, US-23 | TC-076→081 | Regression xanh |
| **P7** | 3 tính năng AI + guardrail | KT3 | US-24→28 | TC-082→100 | 20 ca guardrail xanh; chạy tay với Gemini thật |
| **P8** | README, báo cáo, slide, rà dữ liệu cá nhân | Cuối kỳ | — | TC-102 | Ma trận test không còn ô ⬜ |

---

## Chi tiết từng phase

### P0 — Bộ context và đặc tả · **KT1**

Dựng tài liệu ngữ cảnh mà mọi phiên agent phải đọc, cơ chế hook ghi log phiên, và chiến lược kiểm thử.
Chưa viết code ứng dụng.

Kế hoạch: [`plans/2026-09-04-kt1-bo-context-va-dac-ta.md`](plans/2026-09-04-kt1-bo-context-va-dac-ta.md)

Đáp ứng yêu cầu đề bài mục 6: *"KT1: Dùng AI phân tích nghiệp vụ đặt lịch, chăm sóc, nhắc lịch;
thiết kế use case và ERD."*

**DoD:** `user-stories.md`, `erd.md`, `architecture.md`, `ai-safety.md`, `testing/` đủ 4 file;
mọi chức năng đề bài map được tới user story; hook chạy được.

### P1 — Nền tảng và xác thực · KT2

`requirements.txt`, `app/main.py`, `config.py`, `db.py`, `security.py`, model `users`, đăng nhập bằng
session cookie, dependency kiểm tra vai trò, layout Jinja2 chung, `tests/conftest.py` với đủ 5 fixture.

Phase này dựng luôn `services/clock.py` — điểm lấy thời gian duy nhất của hệ thống. Làm ngay từ đầu vì
nếu để sau, mọi chỗ đã gọi `datetime.now()` trực tiếp đều phải sửa lại, và các ca test phụ thuộc ngày
sẽ không viết được.

**DoD:** đăng nhập 3 vai trò chạy được; TC-001→012 xanh; smoke P1 tick đủ.

### P2 — Dữ liệu nền · KT2

Model và CRUD cho `owners`, `pets`, `services`, `service_packages`, `package_items`. Trang tìm kiếm
không dấu. Cơ chế ngưng bán dịch vụ thay vì xóa.

**DoD:** TC-013→031 xanh; smoke P1–P2 tick đủ.

### P3 — Lịch hẹn · KT2 · **phase khó nhất phần quản lý**

`services/scheduling.py` với quy tắc trùng lịch, router và giao diện lưới lịch, đổi lịch, hủy lịch.

Đề bài nêu đích danh ở mục 6: *"KT2: … debug trùng lịch."* 21 test case của phase này là phần trả lời
cho yêu cầu đó. Sáu ca biên đáng chú ý nhất: giao nhau một phần, liền kề, bao trọn, nằm gọn bên trong,
trùng thú cưng khác nhân viên, và lịch đã hủy không tính.

**DoD:** TC-032→052 xanh, **đặc biệt TC-038** (liền kề phải được chấp nhận) và **TC-046** (đổi lịch
không tự so sánh với chính nó) — hai ca này bắt đúng hai lỗi kinh điển của kiểm tra trùng khoảng;
regression toàn bộ xanh.

### P4 — Hồ sơ chăm sóc và tiêm phòng · KT2

`care_records` gắn 1–1 với lịch hẹn, `vaccinations` với danh sách đến hạn. Màn hình tiêm phòng phải
ghi rõ đây là thông tin, không phải chỉ định y tế.

**DoD:** TC-053→064 xanh; regression xanh; smoke P1–P4 tick đủ.

### P5 — Hóa đơn và thanh toán · KT3

`services/billing.py`, `invoices`, `invoice_items`, `payments`. Hai điểm dễ sai: đơn giá phải **chép**
vào dòng hóa đơn chứ không tham chiếu bảng giá, và tổng thanh toán không được vượt số phải trả.

Phase này cũng viết `tests/e2e/test_full_flow.py` — tới đây hệ thống đã đủ mắt xích để chạy được kịch
bản xuyên suốt 11 bước.

**DoD:** TC-065→075 xanh; **TC-101 (e2e) chạy được**; regression xanh.

### P6 — Thống kê · KT3

`services/stats.py`: lượt dịch vụ, doanh thu, khách quay lại. Doanh thu tính trên `payments` (tiền
thực nhận), không tính trên `invoices` — đây là chỗ dễ nhầm nhất của phase.

**DoD:** TC-076→081 xanh; regression xanh.

### P7 — Tích hợp AI · KT3 · **phase khó nhất phần AI**

`app/ai/` đầy đủ: `provider.py`, `gemini.py`, `fake.py`, `prompts.py`, `service.py`. Ba tính năng
nhắc lịch, tóm tắt, hỏi đáp. Lọc dữ liệu cá nhân. Ghi `ai_logs`. Xử lý lỗi không làm vỡ trang.

Đáp ứng yêu cầu đề bài mục 6: *"KT3: Dùng AI thiết kế prompt an toàn, test câu hỏi vượt phạm vi y tế
thú y."*

Phase này có hai lượt kiểm thử: tự động với `FakeProvider` (TC-082→100), và **chạy tay với Gemini
thật** cho 20 ca G-01→G-20, chép nguyên câu hỏi/phản hồi vào báo cáo. Lượt thứ hai là bắt buộc — test
tự động chỉ kiểm chứng được phần guardrail nằm trong code của chúng ta, không kiểm chứng được mô hình
thật có tuân thủ hay không.

**DoD:** TC-082→100 xanh; 20 ca guardrail chạy với Gemini thật, kết quả dán vào
`testing/reports/`; smoke P7 tick đủ cả hai lượt.

### P8 — Hoàn thiện và nộp · Cuối kỳ

README hoàn chỉnh, báo cáo, slide, rà soát dữ liệu cá nhân trong `ai_logs`. Kiểm tra dựng lại hệ thống
từ CSDL trống trên máy sạch.

Đáp ứng yêu cầu đề bài mục 6: *"Cuối kỳ: Dùng AI viết README, báo cáo, slide và review dữ liệu cá nhân."*

Cân nhắc lại việc dựng CI ở phase này nếu dự án được đẩy lên GitHub.

**DoD:** ma trận [`testing/test-cases.md`](testing/test-cases.md) không còn ô ⬜; toàn bộ suite xanh;
smoke P8 tick đủ; báo cáo dựng được từ chính `docs/` và `docs/sessions/`.

---

## Vì sao thứ tự này

Ba ràng buộc quyết định thứ tự trên:

1. **Phân quyền phải có trước** mọi thứ khác, vì gần như mọi user story đều có điều kiện về vai trò.
   Thêm phân quyền sau khi đã viết xong router là phải sửa lại toàn bộ router.
2. **Lịch hẹn trước hồ sơ chăm sóc trước hóa đơn** — đây là chuỗi phụ thuộc nghiệp vụ thật: hồ sơ gắn
   với lịch hẹn, hóa đơn gắn với lịch đã hoàn thành. Đảo thứ tự thì phải dựng dữ liệu giả để test.
3. **AI làm cuối** vì hai tính năng AI quan trọng nhất (nhắc lịch, tóm tắt hồ sơ) cần dữ liệu lịch hẹn
   và hồ sơ chăm sóc có thật. Làm AI trước thì chỉ test được với dữ liệu bịa, và guardrail sẽ được
   kiểm chứng trên tình huống không giống thực tế.

Rủi ro lớn nhất của thứ tự này là **AI dồn vào cuối, sát mốc KT3**. Giảm thiểu bằng cách viết
[`ai-safety.md`](ai-safety.md) đầy đủ ngay từ P0 — khi tới P7, phần khó nhất là thiết kế prompt và bộ
ca guardrail đã xong, chỉ còn việc cài đặt.
