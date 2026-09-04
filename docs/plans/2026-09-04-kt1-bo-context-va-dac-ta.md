# KT1 — Dựng bộ context cho AI Agent + đặc tả + chiến lược kiểm thử

> **Phase:** P0 · **Mốc:** KT1 · **Duyệt ngày:** 2026-09-04
> Bản chép của kế hoạch đã được duyệt, theo quy ước ở [`README.md`](README.md).

## Checklist thực hiện

- [x] 1. Khởi tạo repo — `git init`, `.gitignore`, `.env.example`
- [x] 2. `CLAUDE.md` dự án — ngữ cảnh, quy trình mỗi phiên, luật kiểm thử
- [x] 3. Hook ghi log phiên trong `.claude/` của dự án
- [x] 4. `docs/user-stories.md` — 28 US, 98 tiêu chí Given/When/Then
- [x] 5. `docs/erd.md` — 13 bảng
- [x] 6. `docs/architecture.md` — ba lớp, 3 sequence diagram
- [x] 7. `docs/ai-safety.md` — prompt và 20 ca guardrail
- [x] 8. `docs/testing/` — 4 file, ma trận 102 test case
- [x] 9. `docs/codebase-map.md`
- [x] 10. `docs/plans/` — README và bản chép kế hoạch này
- [x] 11. `docs/roadmap.md` — P0→P8 kèm Definition of Done
- [x] 12. `README.md` và `docs/sessions/README.md`
- [x] 13. Ghi log phiên + commit

---

## Context

Thư mục `C:\hethongquanlythucung` hiện chỉ có `đề-bài.md` (đề tài "Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI") và `CLAUDE.md` (4 nguyên tắc làm việc chung, chưa có gì riêng cho dự án). Chưa phải git repo, chưa có code.

Dự án sẽ được làm bằng vibe code — phần lớn code do AI agent sinh qua nhiều phiên chat. Hai rủi ro lớn nhất của cách làm này:

1. **Trôi ngữ cảnh** — mỗi phiên agent bắt đầu lại từ đầu, không biết đã quyết định gì, và cuối kỳ báo cáo không khớp code thật.
2. **Test giả** — agent sinh test mock hết mọi thứ, luôn xanh, chứng minh không điều gì; hệ thống trông có kiểm thử nhưng thực chất không có.

Kế hoạch này dựng bộ tài liệu ngữ cảnh mà mọi phiên agent phải đọc, cơ chế hook buộc mỗi phiên ghi lại thay đổi, và chiến lược kiểm thử phân tầng gắn vào quy trình. Kết quả cũng chính là sản phẩm nộp mốc KT1 (phân tích nghiệp vụ, use case, ERD, kế hoạch kiểm thử).

**Chưa viết code ứng dụng trong kế hoạch này.**

## Nguyên tắc bao trùm: mọi ngữ cảnh nằm trong repo

Toàn bộ cấu hình agent, hook, log phiên và kế hoạch đã duyệt phải nằm **bên trong `C:\hethongquanlythucung`** và được commit vào git. Không có gì phụ thuộc vào `~/.claude` (cấu hình cá nhân trên máy). Hệ quả: clone repo về máy khác là agent có đủ ngữ cảnh làm tiếp, và báo cáo cuối kỳ truy vết được từ chính lịch sử repo.

```
C:\hethongquanlythucung\
  .claude\
    settings.json          hook config — COMMIT vào git
    hooks\
      session-start.ps1    COMMIT
      session-stop.ps1     COMMIT
    settings.local.json    (nếu có) — gitignore, chỉ là tuỳ chọn cá nhân
  docs\
    plans\                 kế hoạch đã được duyệt
    sessions\              log từng phiên chat
    testing\               chiến lược, ma trận test, báo cáo kiểm thử
    ...
```

## Quyết định đã chốt

| Hạng mục | Lựa chọn |
|---|---|
| Backend | FastAPI (Python) + SQLAlchemy |
| CSDL | SQLite (file `petcare.db`) |
| Frontend | Jinja2 server-rendered + HTML/JS thuần, không build tool |
| AI Engine | Gemini API, sau adapter `AIProvider` (có `FakeProvider` để test offline) |
| Log phiên | SessionStart hook tạo file + agent tự viết nội dung; Stop hook nhắc chốt |
| Lưu trữ ngữ cảnh | Tất cả trong repo dự án, không dùng `~/.claude` |
| Kiểm thử | pytest, 4 tầng (xem dưới), e2e = 1 test xuyên suốt + checklist thủ công |
| CI | Chưa dựng, cân nhắc lại ở P8 |
| Ngôn ngữ | Tài liệu/comment: tiếng Việt. Định danh code, tên bảng/cột: tiếng Anh |
| Vai trò | `manager` (quản lý), `receptionist` (lễ tân), `caretaker` (nhân viên chăm sóc) |

## Kiến trúc mục tiêu (tài liệu mô tả, code ở phase sau)

Ba lớp, không có lớp repository riêng (YAGNI — SQLAlchemy session đã đủ):

```
app/
  main.py          FastAPI app, đăng ký router
  config.py        đọc .env (GEMINI_API_KEY, DB_URL, AI_PROVIDER)
  db.py            engine + get_db()
  security.py      hash mật khẩu, session cookie, decorator phân quyền
  models/          SQLAlchemy: user, owner, pet, service, package,
                   appointment, care_record, vaccination, invoice, payment, ai_log
  schemas/         Pydantic request/response
  services/        nghiệp vụ thuần, không phụ thuộc HTTP
    scheduling.py    đặt/đổi/hủy lịch + kiểm tra trùng lịch
    billing.py       lập hóa đơn, ghi nhận thanh toán
    stats.py         thống kê lượt dịch vụ, doanh thu, khách quay lại
  ai/
    provider.py      interface AIProvider (generate(system, user) -> str)
    gemini.py        GeminiProvider
    fake.py          FakeProvider (deterministic, dùng trong test)
    prompts.py       system prompt + guardrail
    service.py       3 use case: reminder / summary / qa
  routers/         auth, owners, pets, services, appointments,
                   care_records, invoices, stats, ai
  templates/  static/

tests/
  conftest.py      fixture: DB in-memory, TestClient, seed data, FakeProvider
  unit/            test services/ thuần — không DB thật, không HTTP
  integration/     test qua TestClient + SQLite in-memory
  e2e/
    test_full_flow.py   1 kịch bản xuyên suốt trên DB file thật
```

**Quy tắc ranh giới:** `routers/` chỉ làm HTTP (parse, phân quyền, render). Mọi logic nghiệp vụ nằm ở `services/`, test được mà không cần khởi động app. `ai/` không được import trực tiếp từ `routers/` mà đi qua `ai/service.py`. Ranh giới này chính là thứ cho phép tầng unit test tồn tại — nếu logic nằm lẫn trong router thì chỉ còn integration test, chậm và khó truy nguyên.

Hai điểm nghiệp vụ khó nhất, đề bài nêu đích danh, được đặc tả kỹ nhất:
1. **Chống trùng lịch** — cùng `staff_id` mà khoảng `[start_at, end_at)` giao nhau, hoặc cùng `pet_id` mà giao nhau → từ chối. Áp dụng cho cả tạo mới và đổi lịch; lịch đã hủy không tính.
2. **Guardrail AI** — không chẩn đoán bệnh, không kê thuốc/liều; mọi phản hồi về sức khỏe kèm khuyến cáo bác sĩ thú y; câu hỏi ngoài phạm vi thì từ chối lịch sự.

## Chiến lược kiểm thử

Bốn tầng, tần suất khác nhau theo chi phí. Chạy đủ 4 tầng ở mọi phiên sẽ làm vòng lặp chậm đến mức bị bỏ qua.

| Tầng | Phạm vi | Chạy khi nào | Ngân sách |
|---|---|---|---|
| Unit | Hàm trong `services/`, logic guardrail | Mỗi lần sửa code | < 5s |
| Integration | Router + DB in-memory qua `TestClient` | Cuối mỗi phiên | < 30s |
| Regression | Chạy lại **toàn bộ** suite | Trước mỗi commit | < 1 phút |
| Hệ thống hoàn chỉnh | `tests/e2e/test_full_flow.py` + checklist bấm tay | Cuối mỗi phase | vài phút |

"Test hồi quy" không phải loại test riêng phải viết thêm — nó là việc chạy lại toàn bộ suite cũ sau khi thêm code mới. Định nghĩa như vậy tránh phải nuôi hai bộ test song song.

**Kịch bản e2e xuyên suốt** (`tests/e2e/test_full_flow.py`, chạy trên DB file thật, không in-memory): đăng nhập lễ tân → tạo chủ nuôi → tạo thú cưng → đặt lịch → thử đặt lịch trùng và bị từ chối → đổi lịch → nhân viên ghi hồ sơ chăm sóc → lập hóa đơn → ghi nhận thanh toán → AI tóm tắt hồ sơ → quản lý xem thống kê. Một test này đi qua gần hết hệ thống nên bắt được lỗi tích hợp mà unit test không thấy.

**Ba luật chống test giả** (đưa vào `CLAUDE.md`, không chỉ nằm trong tài liệu test):
1. Không mock chính lớp đang test. Mock chỉ dành cho ranh giới ngoài (API Gemini, thời gian hệ thống).
2. Mỗi bug fix phải có test tái hiện được bug — chạy đỏ trước khi sửa, xanh sau khi sửa. Không có bước "đỏ trước" thì không chứng minh được test có tác dụng.
3. Test AI dùng `FakeProvider` nhưng phải assert nội dung thật: có câu khuyến cáo bác sĩ thú y, không chứa từ khóa chẩn đoán/liều lượng. Không được chỉ assert "không ném exception".

**Không đặt mục tiêu coverage %** — nó đẻ ra test chạy qua code mà không kiểm tra gì. Thay bằng luật cụ thể: mỗi hàm public trong `services/` có tối thiểu 1 test happy path + 1 test biên.

## Các bước thực hiện

### 1. Khởi tạo repo
- `git init` tại `C:\hethongquanlythucung`.
- `.gitignore`: `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.db`, `.env`, `.claude/settings.local.json`. **Không** ignore `.claude/settings.json` và `.claude/hooks/`.
- `.env.example` (chưa tạo `.env` thật).
- **Verify:** `git status` chạy được; `git check-ignore .claude/settings.json` không khớp.

### 2. Viết `CLAUDE.md` dự án
Giữ nguyên 4 mục hiện có, thêm phần "Ngữ cảnh dự án", "Quy trình mỗi phiên" và "Luật kiểm thử":

- Tóm tắt đề tài + link `đề-bài.md`; stack và quy ước ngôn ngữ.
- **Luật mở phiên:**
  1. Làm việc tại `C:\hethongquanlythucung`. Nếu thư mục hiện tại không phải đây thì chuyển vào trước khi làm bất cứ việc gì.
  2. Đọc `docs/codebase-map.md` và log phiên gần nhất trong `docs/sessions/`.
  3. Nếu đang làm dở một kế hoạch, đọc file tương ứng trong `docs/plans/`.
- **Luật đóng phiên:** phiên có thay đổi code → bắt buộc (a) chạy unit + integration test, (b) cập nhật `docs/codebase-map.md`, (c) ghi log phiên kèm kết quả test. Tài liệu, test và code đi song song, không để lệch sang phiên sau.
- **Luật kế hoạch:** kế hoạch vừa duyệt phải chép ngay vào `docs/plans/YYYY-MM-DD-<slug>.md` với checklist trạng thái, cập nhật `[x]` trong lúc làm.
- **Luật kiểm thử:** 3 luật chống test giả ở trên + luật "mỗi hàm public trong `services/` có ≥ 1 happy path + 1 biên" + "mọi thay đổi trong `app/ai/` phải kèm test guardrail".
- **Verify:** đọc lại file, không mâu thuẫn với 4 mục gốc.

### 3. Hook ghi log phiên — đặt trong `.claude/` của dự án
- `.claude/hooks/session-start.ps1`:
  - Xác định thư mục gốc dự án từ `$PSScriptRoot\..\..`, không hard-code, không đọc gì từ `~/.claude`.
  - Đếm file trong `docs/sessions/` có tiền tố ngày hôm nay → tạo `docs/sessions/YYYY-MM-DD-NN.md` với header sẵn: Mục tiêu / Quyết định / File thay đổi / **Kết quả test** / Còn dở.
  - In đường dẫn file log, đường dẫn gốc dự án, và nhắc agent đọc `docs/codebase-map.md` + log phiên trước.
  - Nếu thư mục hiện tại khác thư mục gốc dự án → in cảnh báo rõ ràng.
- `.claude/hooks/session-stop.ps1`: nếu file log vẫn chỉ có header → xóa để không sinh rác; ngược lại in nhắc kiểm tra `docs/codebase-map.md`, `docs/plans/` và mục Kết quả test đã điền chưa.
- `.claude/settings.json` (project-level, được commit): đăng ký `SessionStart` và `Stop`, gọi qua `powershell -NoProfile -ExecutionPolicy Bypass -File`, đường dẫn qua `$CLAUDE_PROJECT_DIR`.
- **Verify:** chạy tay `session-start.ps1` → tạo đúng file log; chạy `session-stop.ps1` ngay sau → file rỗng bị xóa. Mở phiên chat mới trong thư mục dự án → hook chạy tự động.

> Giới hạn cần biết: hook không tự đổi được thư mục làm việc của Claude Code — nó chỉ phát hiện và cảnh báo. "Vào đúng thư mục" được bảo đảm bằng cảnh báo của hook cộng luật trong `CLAUDE.md`.

### 4. `docs/user-stories.md`
Nhóm theo 3 vai trò, mỗi story có ID (`US-01`…), mô tả "Là <vai trò>, tôi muốn… để…", và **tiêu chí chấp nhận Given/When/Then** — nguồn trực tiếp để sinh test.

Bao phủ đủ 8 chức năng quản lý + 3 chức năng AI. Các story viết kỹ nhất:
- Đặt lịch khi khung giờ đã có người → từ chối và gợi ý khung trống.
- Đổi lịch sang khung giờ trùng → từ chối, giữ nguyên lịch cũ.
- Hủy lịch đã lập hóa đơn → chặn, yêu cầu hủy hóa đơn trước.
- Hỏi AI câu hỏi có dấu hiệu bệnh lý → trả lời tham khảo + khuyến cáo bác sĩ thú y, không chẩn đoán.
- **Verify:** bảng đối chiếu cuối file cho thấy mỗi chức năng ở mục 3.1 và 3.2 của đề bài map tới ≥ 1 US.

### 5. `docs/erd.md`
Mermaid `erDiagram` + bảng mô tả từng thực thể (cột, kiểu, ràng buộc, ý nghĩa).

Thực thể: `users`, `owners`, `pets`, `services`, `service_packages`, `package_items`, `appointments`, `care_records`, `vaccinations`, `invoices`, `invoice_items`, `payments`, `ai_logs`.

Ràng buộc quan trọng: `appointments.status` ∈ {booked, rescheduled, cancelled, done}; `invoices.status` ∈ {unpaid, partial, paid}; `vaccinations.next_due_at` là nguồn nhắc tiêm; `ai_logs` lưu prompt/response phục vụ báo cáo và kiểm chứng guardrail.
- **Verify:** mọi bảng có ≥ 1 US dùng đến; không bảng thừa.

### 6. `docs/architecture.md`
Cây thư mục (gồm cả `tests/`), trách nhiệm từng lớp, quy tắc ranh giới, sequence diagram Mermaid cho 3 luồng: đặt lịch, lập hóa đơn, AI tóm tắt hồ sơ. Nêu rõ vì sao ranh giới router/service là điều kiện để unit test tồn tại.

### 7. `docs/ai-safety.md`
- System prompt tiếng Việt cho từng use case (reminder / summary / qa), phát triển từ prompt mẫu trong đề bài.
- Chủ đề cấm: chẩn đoán bệnh, kê thuốc/liều, thay thế khám thú y.
- Câu cảnh báo chuẩn, chèn cố định vào mọi phản hồi nhóm sức khỏe.
- Bộ ca kiểm thử guardrail (câu hỏi vượt phạm vi + kết quả mong đợi) — dùng trực tiếp cho test ở KT3, và được tham chiếu từ `docs/testing/test-cases.md`.
- Quy tắc dữ liệu cá nhân: không gửi số điện thoại/địa chỉ chủ nuôi sang API AI.

### 8. `docs/testing/` — 4 file
- `test-strategy.md`: bảng 4 tầng, tầng nào chạy khi nào, cấu trúc `tests/`, quy ước đặt tên (`test_<đối tượng>_<tình huống>_<kỳ vọng>`), 3 luật chống test giả, lý do không dùng coverage %.
- `test-cases.md`: **ma trận truy vết `US-xx → TC-xx → mức test → file test → trạng thái`**. Đây là bằng chứng mọi yêu cầu đều có test, và đề bài yêu cầu đích danh test cho lịch hẹn, hóa đơn, hồ sơ và AI. Ở KT1 điền cột US/TC/mức, cột file test và trạng thái để trống, các phase sau điền dần.
- `smoke-checklist.md`: kịch bản bấm tay qua trình duyệt cuối mỗi phase, dạng checklist có ô tick.
- `reports/README.md`: quy ước file `YYYY-MM-DD-Pn.md` chứa output pytest thật + kết quả smoke.
- **Verify:** mọi US ở bước 4 xuất hiện trong ma trận `test-cases.md`.

### 9. `docs/codebase-map.md`
Bản đồ file → trách nhiệm, gồm cả file test. Hiện mới có docs và hook, nhưng lập sẵn khung bảng và ghi rõ **bắt buộc cập nhật mỗi khi thêm/xóa/đổi vai trò một file**.

### 10. `docs/plans/`
- `README.md`: quy ước đặt tên `YYYY-MM-DD-<slug>.md`, luật chép kế hoạch vừa duyệt vào đây ngay, mỗi bước có ô `[ ] / [x]`.
- Chép chính kế hoạch này thành `docs/plans/2026-09-04-kt1-bo-context-va-dac-ta.md` kèm checklist 13 bước.

### 11. `docs/roadmap.md`
Mỗi phase có **Definition of Done** gồm điều kiện test:

| Phase | Nội dung | Mốc | DoD |
|---|---|---|---|
| P0 | Bộ context + đặc tả + chiến lược test | KT1 | Tài liệu đủ, ma trận test lập xong |
| P1 | Scaffold, auth, phân quyền 3 vai trò | KT2 | Unit + integration xanh |
| P2 | CRUD chủ nuôi, thú cưng, dịch vụ, gói | KT2 | Unit + integration xanh |
| P3 | Đặt/đổi/hủy lịch + chống trùng lịch | KT2 | Có test trùng lịch, regression xanh |
| P4 | Hồ sơ chăm sóc + lịch tiêm nhắc lại | KT2 | Regression xanh + smoke checklist |
| P5 | Hóa đơn + thanh toán | KT3 | Regression xanh + e2e xuyên suốt |
| P6 | Thống kê | KT3 | Regression xanh |
| P7 | 3 tính năng AI + guardrail | KT3 | Toàn bộ ca guardrail xanh + e2e |
| P8 | README, báo cáo, slide, rà soát dữ liệu cá nhân | Cuối kỳ | Ma trận test điền đủ; cân nhắc CI |

### 12. `README.md` + `docs/sessions/README.md`
README gốc: giới thiệu, stack, cách chạy, cách chạy test (`pytest`, `pytest tests/unit`, …), sơ đồ thư mục `docs/`, và ghi rõ mọi phiên bắt đầu bằng việc vào thư mục dự án. `docs/sessions/README.md`: quy ước đặt tên và cấu trúc file log (gồm mục Kết quả test).

### 13. Ghi log phiên hiện tại + commit
- `docs/sessions/2026-09-04-01.md` ghi lại phiên này: quyết định stack, AI engine, cơ chế log, chiến lược test, phạm vi KT1.
- Một commit: `docs: khoi tao bo context, dac ta va chien luoc kiem thu KT1`.

## Verification tổng thể

1. `git log --oneline` → thấy commit KT1; `git ls-files .claude` → liệt kê `settings.json` và 2 hook (bằng chứng ngữ cảnh nằm trong repo).
2. Chạy `.claude/hooks/session-start.ps1` → tạo đúng `docs/sessions/2026-09-04-NN.md`; chạy `session-stop.ps1` → file rỗng bị xóa.
3. Mở phiên chat Claude Code mới trong thư mục dự án → hook chạy, file log tạo tự động, cảnh báo thư mục làm việc hiện ra.
4. `docs/plans/2026-09-04-kt1-bo-context-va-dac-ta.md` tồn tại, checklist khớp 13 bước.
5. Bảng đối chiếu cuối `docs/user-stories.md`: đủ 8 chức năng quản lý + 3 chức năng AI.
6. Mọi US trong `docs/user-stories.md` có mặt trong ma trận `docs/testing/test-cases.md`; mọi bảng trong `docs/erd.md` được ít nhất một US dùng đến.
7. `architecture.md` và `erd.md` không mâu thuẫn tên bảng/cột.

## Ngoài phạm vi

Không viết code ứng dụng, không viết file test thật, không tạo `.venv`, không cài package, không gọi API Gemini, không dựng CI. Những việc đó thuộc P1 trở đi, mỗi phase một kế hoạch riêng lưu trong `docs/plans/`.
