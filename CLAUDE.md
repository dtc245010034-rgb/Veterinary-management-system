# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# 5. Ngữ cảnh dự án

**Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI.** Cửa hàng dịch vụ thú cưng quản lý
chủ nuôi, thú cưng, lịch spa/tắm/grooming, lịch tiêm nhắc lại, hóa đơn; AI hỗ trợ sinh tin nhắn
nhắc lịch, tóm tắt hồ sơ chăm sóc và trả lời câu hỏi chăm sóc cơ bản ở mức tham khảo.

Đề bài đầy đủ: [`đề-bài.md`](đề-bài.md). Lộ trình: [`docs/roadmap.md`](docs/roadmap.md).

Dự án được làm bằng **vibe code** — phần lớn code do AI agent sinh qua nhiều phiên chat. Vì vậy
tài liệu, test và code phải luôn đi song song; xem mục 6.

## Stack

| Hạng mục | Lựa chọn |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| CSDL | SQLite (`petcare.db`) |
| Frontend | Jinja2 server-rendered + HTML/JS thuần, không build tool |
| AI Engine | Gemini API sau adapter `AIProvider`; `FakeProvider` dùng khi test |
| Kiểm thử | pytest, 4 tầng — xem [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md) |

## Quy ước ngôn ngữ

- **Tài liệu, comment, thông báo lỗi hiển thị cho người dùng: tiếng Việt.**
- **Định danh code, tên bảng, tên cột, tên hàm, tên biến, tên file: tiếng Anh không dấu.**
  Ví dụ: `owner`, `pet`, `appointment`, `care_record`, `invoice`.
- Thông điệp commit: tiếng Việt không dấu, dạng `<loại>: <mô tả>`.

## Vai trò người dùng

`manager` (quản lý) · `receptionist` (lễ tân) · `caretaker` (nhân viên chăm sóc)

---

# 6. Quy trình mỗi phiên làm việc

## Mở phiên — làm đủ 3 việc này trước khi làm bất cứ gì khác

1. **Làm việc tại `C:\hethongquanlythucung`.** Nếu thư mục hiện tại không phải đây thì chuyển vào
   trước. Mọi đường dẫn trong tài liệu đều tương đối so với thư mục này.
2. Đọc [`docs/codebase-map.md`](docs/codebase-map.md) để biết hiện có những file nào, làm gì.
3. Đọc file log phiên gần nhất trong [`docs/sessions/`](docs/sessions/). Nếu đang làm dở một kế
   hoạch, đọc file tương ứng trong [`docs/plans/`](docs/plans/) và xem checklist còn ô nào chưa tick.

## Đóng phiên — bắt buộc nếu phiên có thay đổi code

1. Chạy test tầng unit + integration, ghi lại kết quả thật.
2. Cập nhật `docs/codebase-map.md` nếu có thêm/xóa/đổi vai trò file.
3. Điền đầy đủ file log phiên `docs/sessions/YYYY-MM-DD-NN.md` (hook đã tạo sẵn khung), gồm cả
   mục **Kết quả test**.

Không được để việc cập nhật tài liệu trôi sang phiên sau. Báo cáo cuối kỳ được dựng từ chính các
file này, nên tài liệu lệch code đồng nghĩa với báo cáo sai.

## Luật kế hoạch

Mỗi khi một kế hoạch được người dùng duyệt, **chép ngay vào `docs/plans/YYYY-MM-DD-<slug>.md`**
với checklist `[ ]` cho từng bước, và tick `[x]` trong lúc thực hiện. Kế hoạch không được chỉ nằm
ngoài repo.

---

# 7. Luật kiểm thử

Chiến lược đầy đủ: [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md).
Ma trận truy vết: [`docs/testing/test-cases.md`](docs/testing/test-cases.md).

## Ba luật chống test giả

Rủi ro lớn nhất khi sinh test bằng AI là test luôn xanh nhưng không chứng minh điều gì.

1. **Không mock chính lớp đang test.** Mock chỉ dành cho ranh giới ngoài: API Gemini, thời gian hệ thống.
2. **Mỗi bug fix phải có test tái hiện được bug** — chạy đỏ trước khi sửa, xanh sau khi sửa. Không có
   bước "đỏ trước" thì không chứng minh được test có tác dụng.
3. **Test AI phải assert nội dung thật**, không chỉ assert "không ném exception": phản hồi có câu
   khuyến cáo bác sĩ thú y, không chứa từ khóa chẩn đoán bệnh hay liều lượng thuốc.

## Hai luật bao phủ

- Mỗi hàm public trong `app/services/` có tối thiểu **1 test happy path + 1 test biên**.
- Mọi thay đổi trong `app/ai/` phải kèm test guardrail.

**Không đặt mục tiêu coverage phần trăm** — chỉ tiêu coverage đẻ ra test chạy qua code mà không
kiểm tra gì.

---

# 8. Ranh giới kiến trúc

Chi tiết: [`docs/architecture.md`](docs/architecture.md).

- `app/routers/` chỉ làm HTTP: parse request, kiểm tra quyền, render. **Không chứa logic nghiệp vụ.**
- `app/services/` chứa toàn bộ logic nghiệp vụ, test được mà không cần khởi động app.
- `app/ai/` không được import trực tiếp từ router; mọi lời gọi đi qua `app/ai/service.py`.

Ranh giới này là điều kiện để tầng unit test tồn tại. Logic lọt vào router thì chỉ còn integration
test — chậm và khó truy nguyên lỗi.

## Quy tắc an toàn AI

Xem [`docs/ai-safety.md`](docs/ai-safety.md). Hai điều tuyệt đối:

- AI **không chẩn đoán bệnh, không kê thuốc hay liều lượng**; mọi phản hồi liên quan sức khỏe phải
  kèm khuyến cáo liên hệ bác sĩ thú y.
- **Không gửi số điện thoại, email, địa chỉ chủ nuôi sang API AI.** Chỉ gửi dữ liệu chăm sóc thú cưng.

---

# 9. Bài học — luật phân loại

**Khi phát hiện một lỗi do chính mình gây ra lần thứ hai, phải phân loại trước khi đóng phiên:**

- **Tự động hóa được** → thêm test vào [`tests/unit/test_architecture.py`](tests/unit/test_architecture.py).
- **Không tự động hóa được** → thêm **một dòng** vào danh sách dưới đây.
- Danh sách này có **trần cứng 5 dòng**. Muốn thêm dòng thứ 6 thì phải xóa một dòng hoặc tự động hóa
  một dòng cũ. Chính cái trần giữ nó còn được đọc; không trần thì sau vài phase nó thành nghĩa địa.

Chỉ ghi vào log phiên là **chưa đủ**: luật mục 6 chỉ bắt đọc log *gần nhất*, nên bài học viết ở log
phiên này sẽ khuất tầm nhìn ngay khi có hai phiên nữa.

## Danh sách (4/5 dòng)

1. **Test đỏ thì nghi test trước khi nghi code.** Ba lần lỗi nằm ở test hoặc script kiểm chứng chứ
   không ở code. Gốc chung: viết cứng giả định về dữ liệu thay vì đọc từ fixture. — *không tự động
   hóa được*
2. **Chỉ khẳng định thứ kiểm được thật.** Bốn lần tài liệu mô tả chức năng chưa tồn tại. Khi chia một
   phase thành nhiều chặng, tách khối checklist theo chặng **trước khi** đưa người dùng tick —
   trách nhiệm của agent, không phải người tick. — *canh một phần bởi
   `test_moi_link_tuong_doi_trong_tai_lieu_deu_ton_tai` và `test_moi_file_app_va_tests_deu_co_trong_codebase_map`*
3. **Test viết sau code xanh ngay không chứng minh gì.** Phải làm hỏng code có chủ đích và xác nhận
   đúng test tương ứng đỏ, rồi hoàn nguyên — và **khẳng định đột biến đã thật sự vào file**: repo
   trộn LF với CRLF, chuỗi tìm-thay viết theo kiểu xuống dòng LF sẽ không khớp, và kết quả đọc ra
   là "test không bắt được lỗi" trong khi code còn nguyên vẹn. **Đột biến sống sót thì nghi chính nó
   trước**: 18/09 hai lần — một lần đổi tên lớp CSS trong khi test assert câu chữ (đột biến vô hại),
   một lần chỉ vô hiệu một nhánh trong ba nhánh cùng bắt (đột biến quá nhẹ). Ca thứ hai hóa ra là kẽ
   hở thật và đáng thêm test; ca thứ nhất chỉ là đột biến viết sai. — *không tự động hóa được*
4. **Sửa một lỗi thì soát cả lớp lỗi, không chỉ ca vừa thấy.** Hai lần: thiếu link menu — sửa "Dịch
   vụ" xong bỏ sót "Chủ nuôi"; chặn xóa thú cưng — chặn `appointments` xong bỏ sót `vaccinations`,
   lỗi 500 quay lại nguyên vẹn. Hỏi "còn chỗ nào cùng dạng?" trước khi đóng. — *không tự động hóa
   được*

Ranh giới kiến trúc và bao phủ hàm public **đã rời khỏi danh sách này** vì tự động hóa được — xem
`test_architecture.py`. Đó là kết quả mong muốn: danh sách càng ngắn nghĩa là càng nhiều bài học đã
thành máy canh.
