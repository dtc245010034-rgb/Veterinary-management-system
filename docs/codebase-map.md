# Bản đồ mã nguồn

> **File này bắt buộc cập nhật mỗi khi thêm, xóa hoặc đổi vai trò một file.** Đây là thứ đầu tiên
> agent đọc ở mỗi phiên làm việc (xem [`../CLAUDE.md`](../CLAUDE.md) mục 6). Bản đồ lệch thực tế thì
> phiên sau sẽ làm việc dựa trên thông tin sai.

**Cập nhật lần cuối:** 2026-09-27 (phiên 25–27/09 — **dựng CI GitHub Actions** · **đặc tả theo kịp 12 lỗi đã sửa** · **xử lý 3 việc tồn** · **lên kế hoạch P9 cổng khách hàng sau buổi giảng viên kiểm tiến độ**) · **Trạng thái:** **P0→P7 xong cả tám phase; P8 đang làm. KHÔNG CÒN LỖI NÀO TỒN.** **906 test xanh.** Tiến độ từng phase: [`roadmap.md`](roadmap.md)

> ## Làm tiếp — đọc mục này trước tiên
>
> **1. VIỆC LỚN NHẤT ĐANG CHỜ: P9 — cổng khách hàng.**
> [`plans/2026-09-25-p9-cong-khach-hang.md`](plans/2026-09-25-p9-cong-khach-hang.md) — **29 ô,
> CHƯA DUYỆT**, viết sau buổi giảng viên kiểm tra tiến độ 25/09. Mười quyết định đã chốt qua hai
> vòng hỏi; kế hoạch chờ người dùng duyệt trước khi gõ code. **Đọc cả mục 1 và mục 2 của file đó
> trước khi bàn lại bất cứ điều gì** — bốn nhận xét của giảng viên và phản biện có bằng chứng đều
> nằm ở đó, đừng tranh luận lại từ đầu.
>
> **Ô 0.1 đã chốt ngày 27/09: đổi fixture `db`** sang dựng schema một lần mỗi phiên + rollback từng
> test. Lý do làm trước mọi thứ khác: P9 sẽ thêm ~250–350 test, đổi fixture trên 906 test rẻ hơn hẳn
> trên 1200. **Đây là việc đầu tiên của phiên sau.** Chưa gõ dòng nào.
>
> **2. Việc đã duyệt, chưa làm:**
> [`plans/2026-09-25-ragas-bo-do-ai.md`](plans/2026-09-25-ragas-bo-do-ai.md) — bộ đo chất lượng AI,
> **12 ô chưa tick**. Người dùng đã chốt đủ 4 quyết định. Tóm tắt: chấm `G-01→G-13` **bằng luật
> code** (0 lượt gọi), cộng **RAGAS `Faithfulness` chỉ cho tóm tắt hồ sơ** qua một wrapper gọi ngược
> vào `goi_co_xoay`. Giám khảo phải là model **khác** model bị chấm. Đặt ở `app/ai/danh_gia.py`.
> `ragas` **không** vào `requirements.txt`.
>
> **3. Việc lớn của P8 chưa bắt đầu:** README hoàn chỉnh · **báo cáo cuối kỳ** · **slide**.
> **CI đã dựng xong 25/09** — xem mục `.github/` bên dưới. Lượt chạy đầu tiên là phép thử thật
> của job Linux: dự án chưa từng chạy trên Linux, nên **đỏ ở đó chưa chắc là lỗi code**.
>
> **4. Sáu ô smoke P8 chờ người dùng bấm tay.** Bốn trong sáu ô **đã có sẵn bằng chứng** kiểm bằng
> lệnh, ghi trong [`sessions/2026-09-24-01.md`](sessions/2026-09-24-01.md) — agent không tick vì ô
> smoke đo trải nghiệm trên trình duyệt.
>
> **5. Việc treo còn lại:**
> - **Ngân sách thời gian test — ĐÃ CHỐT 27/09, xem ô 0.1 ở mục 1.** Ngưỡng thật là **100s**
>   (`test-strategy.md`, nới lần hai 18/09) — **không phải 90s**; con số 90s là của lần nới
>   13/09 còn sót trong `roadmap.md` rồi bị chép qua **năm** tài liệu suốt ba phiên. Đo 25/09
>   qua bảy lượt: **101–148s** cho cùng một bộ test cùng một ngày — dao động theo tải máy rộng
>   hơn cả mức vượt ngưỡng. Đã truy nguyên nhân: **không test nào đáng cắt** (20 ca chậm nhất
>   cộng lại chỉ ~24s), chi phí rải đều ở fixture — `create_all` từng test tốn
>   **25,6 ms × 906 ≈ 23s**. Có phép canh số 55 giữ con số ngưỡng khỏi bị chép lệch lần nữa.
> - **M-08 chưa kiểm bằng Gemini thật** (mới kiểm ở mức prompt) — tốn 1 lượt quota.
>
> ---
>
> ### Đã xong, đừng làm lại
>
> **Hết lỗi tồn.** Toàn bộ 18 lỗi của lượt rà 19/09 cộng D-02 đã xử lý qua bốn đợt: 3 lỗi cao
> (19/09) · 4 lỗi ưu tiên (20/09) · M-06 · **11 lỗi cuối** (24/09). Cả 11 lỗi cuối đều **tái hiện
> bằng Chrome trước khi sửa và nghiệm thu lại bằng Chrome sau khi sửa** — xem
> [báo cáo](testing/reports/2026-09-19-ra-luong-P1-P7.md) mục "Đã sửa ngày 24/09 (phần 2)".
>
> **Con số lỗi từng bị đếm sai hai lần** (ghi 11 nhưng liệt kê 12 mã từ 20/09, rồi thành 10). Nay là
> **0**, và cách đếm ghi lại trong báo cáo để không lặp.
>
> ### Ngữ cảnh dễ mất, ghi lại ở đây
>
> - **Giảng viên đã kiểm tiến độ ngày 25/09 và nêu bốn điểm.** Phản biện có bằng chứng nằm ở
>   mục 1 của [`plans/2026-09-25-p9-cong-khach-hang.md`](plans/2026-09-25-p9-cong-khach-hang.md).
>   Hai điều **đừng bàn lại từ đầu**:
>   - *"Không phải lập trình hướng đối tượng"* — **sai về sự kiện**: `app/` có **35 class**, gồm
>     mẫu Strategy (`AIProvider` ← `GeminiProvider`/`FakeProvider`) và cây kế thừa ngoại lệ ba
>     tầng. Người dùng đã xác nhận OOP **không phải tiêu chí chấm** → **không refactor**.
>   - *"Cho khách xem bảng lịch nhân viên"* — làm theo nghĩa đen là **rò dữ liệu**:
>     `appointments.html` render tên thú cưng, họ tên chủ nuôi và link `/owners/{id}`. Đã chốt:
>     khách chỉ thấy **khung trống theo từng nhân viên**.
> - **Vì sao KHÔNG nối tài khoản khách theo số điện thoại** (dù đó là cách tiện nhất):
>   `owners.phone` **không UNIQUE**, và `requirements.txt` **không có thư viện gửi mail/SMS nào**
>   → ai biết số điện thoại của một khách là **chiếm được** hồ sơ thú cưng, lịch sử chăm sóc và
>   hóa đơn của người đó. Nặng hơn mọi lỗi của lượt rà 19/09. Đã chốt: **xác minh email** (bài
>   toán "email này là của ai") **cộng lễ tân duyệt yêu cầu nối** (bài toán "người này là chủ
>   nuôi nào") — hai bài toán khác nhau, đừng gộp lại. Thêm dữ kiện: **chỉ 1/4 chủ nuôi trong
>   `petcare.db` có email**, `seed.py` không đặt email cho ai.
> - **Cạm bẫy của hook `session-stop.ps1`:** nó xóa mọi log phiên có **≥5** lần chuỗi
>   `_(chua ghi)_`. Một log phiên **mô tả chính cơ chế đó** mà trích chuỗi 5 lần sẽ **bị hook
>   xóa im lặng, dù đã điền đầy đủ**. `sessions/2026-09-25-01.md` hiện trích 1 lần nên an toàn.
>   Phép canh `dem_log_phien_da_ghi` dùng cùng ngưỡng nên có cùng điểm mù. **Chưa sửa** — sửa
>   hook là việc cần người dùng quyết.
> - **Bộ test có dấu hiệu flaky:** lượt chạy 27/09 ra `901 passed, 5 errors`, chạy lại ngay sau
>   đó **906 passed** hai lần liền. Không xác định được 5 ca nào vì output đã bị cắt. Bốn ca duy
>   nhất chạm hệ thống tập tin thật là `test_seed.py` (2), `e2e/test_full_flow.py` (1),
>   `test_hooks.py` (1) — **không đủ 5 nên đừng kết luận là chúng**. CI nay chạy mỗi lần push và
>   sẽ giữ log đầy đủ; đó là chỗ để bắt lại chuyện này.
> - **Quota AI là ~20 lượt cho MỖI model, 4 model → ~80 lượt/ngày**, không phải 20. Cơ chế xoay ca
>   ở `app/ai/quota.py` sinh ra đúng vì *"một model là không đủ để chạy 20 ca guardrail"*.
> - **`G-14 → G-20` không cần model thật** — `ai-safety.md` chốt chúng là "việc của code", đã có
>   test tự động xanh. Đừng đưa chúng ra Gemini.
> - **`python -m app.ai.quota --guardrail` đã chạy được** `G-01→G-13` và sinh báo cáo Markdown; nó
>   **cố ý để trống cột "Đạt?"** cho người đọc. Bộ đo mới **cộng thêm cột máy chấm, không thay thế**.
> - **Repo trộn CRLF với LF theo từng file**, không có quy ước chung. Mỗi file giữ kiểu của chính nó.
>   Sửa file bằng Python thì phải đọc ra, quy về LF, thay, rồi ghi lại đúng kiểu cũ — xem
>   `CLAUDE.md` mục 9 dòng 5. Đã mất hai lần trong ngày 24/09 vì chuyện này.
> - **Bấm nút bằng `ref` của tiện ích Chrome không gửi form** trong ứng dụng này; phải bấm bằng tọa
>   độ hoặc gọi `form.submit()`. Đăng xuất là **POST**, `GET /logout` trả 405.
>
> ### Trạng thái máy
>
> `petcare.db` **sạch**: 3 chủ nuôi, 9 lịch hẹn, 2 hóa đơn, không nợ âm. Mọi lượt rà đều chạy trên
> **bản sao** trong scratchpad, không đụng CSDL thật. Bản sao lưu:
> `petcare.bang-chung-ai-2026-09-20.db` (**không vào git**) — xem mục dưới.
>
> ### Hai file `.db` trên máy, và vì sao chỉ còn hai
>
> | File | Vai trò |
> |---|---|
> | `petcare.db` | **CSDL đang chạy** (`.env` trỏ vào) và kiêm luôn CSDL demo. Có `ai_logs` **id 1..29** |
> | `petcare.bang-chung-ai-2026-09-20.db` | **Kho bằng chứng, chỉ đọc.** Đổi tên 25/09 từ `petcare.truoc-khoi-phuc-2026-09-20.db` |
>
> **Mọi trích dẫn `ai_logs #N` trong tài liệu ngày 19–20/09 đều đối chiếu vào file bằng chứng, KHÔNG
> phải `petcare.db`.** Các bản ghi #30, #31, #38, #40→#45 đã biến mất khỏi `petcare.db` khi nó được
> khôi phục từ bản sao lưu ngày 20/09; nơi duy nhất còn chúng là file bằng chứng (46 bản ghi). File
> này cũng là bản duy nhất còn giữ trạng thái hỏng **D-01** (nợ âm hóa đơn #3) và **ba lịch ngoài giờ
> mở cửa** — ba bản ghi tái hiện M-06 mà hệ thống nay không tạo ra được nữa.
>
> **Cạm bẫy khi đọc trích dẫn:** id `ai_logs` bị dùng lại ở mọi bản sao CSDL, nên cùng một con số trỏ
> vào bản ghi khác nhau tùy file. Ví dụ `#30` là tin nhắc lịch do `gemini-3.6-flash` sinh trong file
> bằng chứng, nhưng lại là một câu hỏi đáp của `fake` trong các bản sao dựng sau này. **Trích dẫn
> `ai_logs` phải nói rõ file**, nếu không thì không kiểm chứng lại được.
>
> `petcare.backup-2026-09-19.db` **đã xóa ngày 25/09** sau khi đối chiếu **từng dòng của cả 14 bảng**
> và chứng minh `petcare.db` chứa trọn vẹn nội dung của nó (0 dòng riêng). Các tài liệu ngày 19–20/09
> còn nhắc tên file này là **mốc lịch sử**, giữ nguyên không sửa.
>
> **Test không dùng file `.db` nào trên đĩa** — `conftest.py` dùng SQLite in-memory, `test_seed.py` và
> e2e dùng `tmp_path`. Và **không file `.db` nào cần để dựng lại dự án**: `create_all` cộng
> `python -m app.seed` là đủ.
> `.env` đang `AI_PROVIDER=gemini`. **Đã push tới `786b2f1`; 0 commit tồn ở máy**; kiểm lại remote:
> không có `.env`, không có file `.db` nào.
>
> ### Đọc để lấy lại ngữ cảnh
>
> [`sessions/2026-09-25-01.md`](sessions/2026-09-25-01.md) (phiên gần nhất — CI và đặc tả, kèm
> bảng **luật → test** và cách xử lý xuống dòng trên file trộn CRLF/LF) →
> [`sessions/2026-09-24-01.md`](sessions/2026-09-24-01.md) (**sáu phần** — dài nhưng là nguồn
> đầy đủ nhất về đợt sửa lỗi) → [`sessions/2026-09-20-05.md`](sessions/2026-09-20-05.md)
> (bốn phần) → [`sessions/2026-09-19-01.md`](sessions/2026-09-19-01.md) (năm phần, nền của mọi
> quyết định).

### `app/ai/` — tầng AI, từ P7

| File | Vai trò |
|---|---|
| `ai/provider.py` | Interface `AIProvider` + sáu lớp lỗi đã phân loại (lớp gốc `LoiAI`, `LoiQuaTai`, `LoiKetNoi` — mất mạng, không tính lượt — `LoiHetQuota`, `LoiModelKhongCo`, `LoiCauHinh`). Phân loại lỗi là điều kiện để xoay ca model |
| `ai/gemini.py` | Một lần gọi REST `generateContent` qua `urllib`, không thêm thư viện. Đọc `details` của lỗi 429 để phân biệt hết lượt **theo phút** và **theo ngày**; tách lỗi không kết nối được (`LoiKetNoi`) khỏi timeout; gửi `thinkingBudget` theo cấu hình |
| `ai/fake.py` | `FakeProvider`: ghi lại mọi `(model, system, user)`, cài được phản hồi và lỗi **theo từng model** — nền tảng của test xoay ca và test US-28. `tinh_quota` mặc định `True` (đóng vai Gemini trong test); chế độ fake của ứng dụng dùng `tinh_quota=False` |
| `ai/prompts.py` | `DISCLAIMER`, ba system prompt, câu từ chối thuốc, câu nhắc xác nhận lịch tiêm, các hàm dựng prompt. Thuần, không chạm CSDL |
| `ai/guardrail.py` | `la_cau_xin_thuoc()` (chặn trước khi gọi), `chua_lieu_luong()` (soát phản hồi), `xoa_lien_he()` (bỏ SĐT/email khỏi văn bản tự do). So theo **từ nguyên vẹn** trên chuỗi đã bỏ dấu |
| `ai/quota.py` | Ngày quota theo **giờ Pacific**, luật xoay ca model, đếm lượt, bảng quota, `goi_co_xoay()`. Kèm CLI `python -m app.ai.quota` (`--hoi`, `--guardrail`, `--model`, `--dat-lai`) |
| `ai/service.py` | Ba tính năng AI + `lay_provider()`. **Cửa duy nhất router được import** — có phép canh trong `test_architecture.py` |

---

## Hiện có

### Gốc dự án

| File | Vai trò |
|---|---|
| `CLAUDE.md` | Nguyên tắc làm việc + ngữ cảnh dự án + quy trình mỗi phiên + luật kiểm thử + **mục 10: quy ước làm việc với người dùng** (chuyển từ bộ nhớ agent vào repo ngày 25/09, có phép canh giữ) |
| `đề-bài.md` | Đề bài gốc của môn học. **Không sửa** |
| `README.md` | Giới thiệu, cách chạy, cách chạy test |
| `run.py` | **Chạy dự án bằng một lệnh** (chỉ thư viện chuẩn): tạo `.venv`, cài `requirements.txt` khi file đổi, tạo `.env` từ `.env.example` với `SECRET_KEY` ngẫu nhiên, seed khi CSDL chưa có, chọn cổng trống, chạy uvicorn, mở trình duyệt. Lệnh con: `reset` (xóa SQLite sau xác nhận), `status`, `test`; cờ `--check` (đợi `/login` 200 rồi tắt, dùng trong CI). **Cam kết: `.env` có sẵn không bao giờ bị ghi đè** — chỉ dòng `SECRET_KEY` bị thay khi thiếu hoặc còn giá trị mặc định |
| `test.py` | Lối tắt của `python run.py test`: truyền nguyên tham số cho pytest, trả nguyên mã thoát |
| `.gitignore` | Bỏ qua `.venv`, `__pycache__`, `*.db`, `.env`, `.claude/settings.local.json` |
| `.env.example` | Mẫu biến môi trường: khóa, **`SESSION_HTTPS_ONLY`, `APP_ORIGIN`**, **danh sách model Gemini**, ước tính hạn mức, `GEMINI_THINKING_BUDGET`, ngân sách thời gian mỗi lượt gọi AI. `.env` thật không vào repo. Có phép canh: mọi biến trong `config.py` phải có mặt ở đây |

### `.claude/` — cấu hình agent, nằm trong repo

| File | Vai trò |
|---|---|
| `settings.json` | Đăng ký hook `SessionStart` và `Stop`. **Được commit** |
| `hooks/session-start.ps1` | Tạo `docs/sessions/YYYY-MM-DD-NN.md`, in nhắc nhở, cảnh báo nếu sai thư mục làm việc |
| `hooks/session-stop.ps1` | Chạy sau **mỗi lượt**: xóa **mọi** file log còn rỗng (mọi ngày, không chỉ file mới nhất), nhắc cập nhật codebase-map và checklist plan |

### `.github/` — CI, từ 25/09

| File | Vai trò |
|---|---|
| `workflows/ci.yml` | Chạy toàn bộ bộ test mỗi lần push lên `main` và mỗi pull request, trên **cả `windows-latest` lẫn `ubuntu-latest`** (`fail-fast: false` để Linux đỏ vẫn biết Windows xanh hay không). **Cố ý không tạo `.env`**: job xanh chính là bằng chứng suite chạy được bằng giá trị mặc định của `config.py`, tức người chấm clone repo về là test được ngay. Chạy `pytest -rs` để chỗ bỏ qua hiện ra trong log thay vì lẫn vào màu xanh — **Windows 0 ca bỏ qua, Linux đúng 1** (`test_hooks.py`, nó tìm lệnh `powershell` chứ không phải `pwsh`) **Job thứ hai `run-py`** (thêm 02/10) chạy `python run.py --no-open --check` trên máy sạch cả hai hệ: run.py tự dựng `.venv`, `.env`, seed rồi khởi động uvicorn thật và đợi `/login` trả 200 — đường có `.env`, ngược với job pytest |

### `docs/`

| File | Vai trò |
|---|---|
| `user-stories/README.md` | Mục lục đặc tả: bảng 9 nhóm với số story và số tiêu chí, quy ước ba mục, bảng đối chiếu với đề bài. 28 user story, **118** tiêu chí Given/When/Then (60 chấp nhận + 58 biên) — tách file ngày 02/10, xem [kế hoạch P9](plans/2026-09-25-p9-cong-khach-hang.md) |
| `user-stories/a-dang-nhap-phan-quyen.md` | Nhóm A · US-01→03: 15 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/b-chu-nuoi-thu-cung.md` | Nhóm B · US-04→06: 19 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/c-dich-vu-bang-gia.md` | Nhóm C · US-07→09: 11 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/d-lich-hen.md` | Nhóm D · US-10→14: 23 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/e-ho-so-cham-soc.md` | Nhóm E · US-15→16: 6 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/f-tiem-phong.md` | Nhóm F · US-17→18: 7 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/g-hoa-don-thanh-toan.md` | Nhóm G · US-19→21: 12 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/h-thong-ke.md` | Nhóm H · US-22→23: 6 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/i-chuc-nang-ai.md` | Nhóm I · US-24→28: 19 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `erd.md` | 14 bảng, sơ đồ Mermaid, mô tả cột và ràng buộc |
| `architecture.md` | Cây thư mục, ranh giới ba lớp, 3 sequence diagram, cách xử lý lỗi |
| `ai-safety.md` | System prompt 3 tính năng (có phép canh khớp `prompts.py`), `DISCLAIMER`, 20 ca guardrail G-01→G-20, kết quả chạy Gemini thật 19/09 |
| `codebase-map.md` | File này |
| `roadmap.md` | Lộ trình P0→P8 gắn với mốc KT1/KT2/KT3/cuối kỳ, kèm Definition of Done |
| `plans/README.md` | Quy ước lưu kế hoạch đã duyệt |
| `plans/YYYY-MM-DD-<slug>.md` | Một file mỗi kế hoạch đã duyệt, kèm checklist tick trong lúc làm. Hiện có 22: KT1/P0, P1, P2a, P2b, P3, P4, P5, e2e xuyên suốt, trả nợ kiến trúc, P6, dọn việc tồn P6, P7, rà soát P1→P7, sửa lỗi cao sau rà soát, chế độ AI giả lập, vá dữ liệu và sửa 4 lỗi ưu tiên (20/09), M-06 giờ mở cửa (24/09), 11 lỗi còn lại (24/09), **bộ đo AI có RAGAS (25/09 — đã duyệt, chưa làm)**, **CI và đặc tả theo kịp (25/09)**, **P9 cổng khách hàng (25/09 — CHƯA DUYỆT)**, **`run.py`/`test.py` và chặng bảo mật 0.5 trước P9 (02/10 — đã duyệt, Phiên 1 đang làm)** |
| `sessions/README.md` | Quy ước log phiên làm việc |
| `sessions/YYYY-MM-DD-NN.md` | Một file mỗi phiên chat, hook tạo khung sẵn. Hiện có 16 |
| `testing/test-strategy.md` | 4 tầng test, 3 luật chống test giả, fixture, kịch bản e2e |
| `testing/test-cases.md` | Ma trận truy vết US → TC → file test, 133 test case — 131 ✅ · 0 🟡 · 1 ⬜ (TC-102 smoke) · 1 ➖ ngoài phạm vi (24/09 thêm TC-121 → TC-133; 20/09 thêm TC-117 → TC-120) |
| `testing/smoke-checklist.md` | Checklist bấm tay theo từng phase |
| `testing/reports/README.md` | Mẫu báo cáo kiểm thử cuối phase |
| `testing/reports/YYYY-MM-DD-Pn.md` | Một file mỗi phase, chứa output pytest thật. Hiện có 25: mỗi phase một file, cộng sáu báo cáo rà luồng bằng trình duyệt (bản 19/09 kèm ảnh trong `anh-2026-09-19/`), một báo cáo rà bổ sung bằng HTTP (20/09, bốn phần lượt 19/09 chưa chạm), một báo cáo rà bằng Chrome trước khi sửa (20/09), một báo cáo trả nợ, một báo cáo dọn việc tồn và một báo cáo chạy Gemini thật (sinh bởi `python -m app.ai.quota --guardrail`) |

### Ứng dụng (`app/`) — từ P1

| File | Vai trò |
|---|---|
| `main.py` | Khởi tạo FastAPI, session middleware, **middleware `Cache-Control: no-store` cho mọi trang trừ `/static`** (L-02), **middleware `chan_cheo_nguon` trả 403 cho yêu cầu ghi từ trang khác** (R-2), **middleware `them_header_bao_mat` (lớp ngoài cùng, R-4)**, cờ `https_only` của session từ `SESSION_HTTPS_ONLY`, gọi `nang_cap_schema` sau `create_all`, đăng ký router, **từ chối khởi động khi `SECRET_KEY` còn mặc định** (S1), 3 trình xử lý lỗi (403/404 ra trang có bố cục, chưa đăng nhập thì chuyển về `/login`, `LoiNghiepVu` lọt khỏi router → trang 404/400 thay vì 500 — H-03) |
| `config.py` | Đọc `.env` qua pydantic-settings: `DATABASE_URL`, `SECRET_KEY`, `AI_PROVIDER`, `GEMINI_API_KEY`, **`SESSION_HTTPS_ONLY`** (cờ Secure cho cookie phiên), **`APP_ORIGIN`** (địa chỉ công khai được tin ở bước chặn POST từ trang khác). Hằng `SECRET_KEY_MAC_DINH` để `main.py` chặn khởi động với khóa công khai (S1) |
| `db.py` | `Base`, `engine`, `SessionLocal`, `get_db()`. Bật `PRAGMA foreign_keys` cho từng kết nối SQLite |
| `security.py` | `hash_password()`, `verify_password()` — bcrypt trực tiếp, không qua passlib; `la_post_cheo_nguon()` — quyết định yêu cầu ghi có đến từ trang web khác không (R-2) |
| `app/auth.py` | Session cookie (mang `sv` = `session_version`, so khi đọc — R-3), `nguoi_dung_hien_tai`, `yeu_cau_vai_tro()`, ngoại lệ `ChuaDangNhap`. Ghi kèm thư mục để không lẫn với `routers/auth.py` |
| `templates.py` | Cấu hình Jinja2 dùng chung, filter `tien` (`{{ so|tien }}`), và hàm `che_do_ai_gia_lap()` cho template biết đang chạy `AI_PROVIDER=fake` |
| `seed.py` | 4 tài khoản, 3 chủ nuôi, 5 thú cưng, 5 dịch vụ, 2 gói, 8 lịch hẹn, 3 hồ sơ chăm sóc, 5 mũi tiêm, 2 hóa đơn, 2 lần thanh toán. Hóa đơn và lần trả mang **ngày của buổi chăm sóc** (lập trong `clock.freeze`), không phải ngày chạy seed. Hóa đơn dựng **qua `billing.py`** chứ không gán trạng thái tay. Chạy `python -m app.seed`, không sinh trùng |
| `models/__init__.py` | Gom mọi model — `create_all` chỉ tạo bảng đã được import |
| `models/user.py` | Bảng `users` (có `session_version` — R-3) + hằng `VAI_TRO`, `TEN_VAI_TRO` |
| `models/ai_log.py` | Bảng `ai_logs` — nhật ký gọi AI. Cột `model` NULL nghĩa là **không có lời gọi nào đi ra** (guardrail chặn trước hoặc thiếu dữ liệu) |
| `models/ai_quota.py` | Bảng `ai_quota` — lượt đã dùng, hạn mức thật, trạng thái nghỉ/hết lượt/bị tắt của từng model theo từng ngày quota |
| `models/owner.py` | Bảng `owners`. `search_name` tự đồng bộ qua `@validates` |
| `models/pet.py` | Bảng `pets` + hằng `GIOI_TINH` (template dựng ô chọn từ đó, services kiểm theo đó — L-03). CHECK `weight_kg > 0`; ngày sinh kiểm ở tầng services |
| `models/service.py` | Bảng `services`. `price` kiểu `Numeric(12,2)`, **không** `Float` |
| `models/service_package.py` | `service_packages` + `package_items`, property `tong_gia_le`, `tiet_kiem` |
| `models/appointment.py` | Bảng `appointments`, hằng `TRANG_THAI`, 2 index phục vụ kiểm trùng |
| `services/clock.py` | `now()` và `freeze()` — điểm lấy thời gian duy nhất của hệ thống. `freeze()` dùng khi test và ở `seed.py` |
| `services/tien.py` | `doc_tien()` — đọc số tiền người dùng gõ. **Chỉ nhận số nguyên đồng**; dấu chấm/phẩy/khoảng trắng là phân cách nghìn, chuỗi có phần lẻ bị từ chối (L-03). Gom lại từ hai bản chép tay từng nằm ở `routers/services.py` và `routers/invoices.py` |
| `services/text.py` | `chuan_hoa()` — bỏ dấu tiếng Việt cho tìm kiếm, xử lý riêng chữ `đ` |
| `services/errors.py` | `LoiNghiepVu` — lỗi nghiệp vụ, thông điệp hiển thị thẳng cho người dùng. Lớp con `LoiKhongTimThay` cho mọi lần tra theo id không thấy bản ghi (H-03) |
| `services/schema.py` | `nang_cap_schema(engine, metadata)` — thêm cột còn thiếu bằng `ALTER TABLE ... ADD COLUMN`, chạy lại an toàn; `create_all` chỉ tạo bảng thiếu chứ không thêm cột. Gọi trong `lifespan` ngay sau `create_all`. Từ chối cột không thể thêm (PK, UNIQUE, NOT NULL không có `server_default`) bằng `LoiNangCap` |
| `services/login_throttle.py` | `GioiHanDangNhap` (R-1): giới hạn đăng nhập sai theo cặp (IP, tên đăng nhập), miễn phí 5 lần rồi khóa 30 giây, mỗi lần sai tiếp theo gấp đôi, trần 900 giây; đăng nhập đúng xóa bộ đếm; quên sau 3600 giây không hoạt động. Lưu trong bộ nhớ tiến trình, có khóa luồng. Singleton `gioi_han_dang_nhap`
| `models/care_record.py` | Bảng `care_records` — hồ sơ chăm sóc, quan hệ 1–1 với lịch hẹn (`appointment_id` UNIQUE) |
| `models/vaccination.py` | Bảng `vaccinations` — mũi tiêm và hạn nhắc lại; property `qua_han` |
| `services/users.py` | Nghiệp vụ tài khoản nhân viên: tạo, **sửa**, khóa, mở khóa, danh sách, **đặt lại và tự đổi mật khẩu**. Chặn quản lý tự khóa mình và tự bỏ vai trò quản lý. `kiem_mat_khau()` là cửa chung của **cả ba** đường đặt mật khẩu (M-04) |
| `services/owners.py` | Nghiệp vụ chủ nuôi và thú cưng: tạo, sửa, xóa, tra cứu. Giữ **mọi phép kiểm dữ liệu nhập**: định dạng số điện thoại và email (M-05), `chuan_hoa_so_dien_thoai()` dùng chung với phép kiểm trùng (M-07), trần độ dài chuỗi, cân nặng, tuổi, danh sách giới tính (L-03) |
| `services/catalog.py` | Nghiệp vụ dịch vụ và gói. `danh_sach_dang_ban()` là danh sách P3 và P5 sẽ dùng. Thời lượng có **cận trên** `PHUT_LAM_VIEC_MOI_NGAY` nhập từ `scheduling` — nhập một hằng số chứ không gọi hàm, nên hai service vẫn tách ra được (M-06) |
| `services/care_records.py` | Nghiệp vụ hồ sơ chăm sóc. Thao tác **duy nhất** đưa lịch hẹn về `done` |
| `services/scheduling.py` | **Quy tắc chống trùng lịch**, **luật giờ mở cửa** (`_kiem_gio_lam_viec` — cả buổi phải nằm trọn trong `GIO_MO_CUA`–`GIO_DONG_CUA` cùng một ngày, áp cho cả đặt lẫn đổi lịch; M-06 sửa 24/09), đặt/đổi/hủy lịch, gợi ý khung trống, `so_lich_chua_lam_theo_nhan_vien()` cho cảnh báo nhân viên đã khóa (S4). Đổi lịch kiểm nhân viên **cả khi giữ nguyên người**. Khoảng nửa mở `[start, end)`. Hủy lịch còn chặn khi lịch đang có hóa đơn chưa hủy (US-21) — biết model `Invoice`, không gọi sang `billing.py` |
| `services/vaccinations.py` | Nghiệp vụ tiêm phòng: ghi mũi, hồ sơ tiêm, danh sách đến hạn. Chỉ tính mũi mới nhất của mỗi loại vắc-xin; tên vắc-xin gõ khác hoa thường/dấu được quy về tên đã có của chính thú cưng đó (S2) |
| `models/invoice.py` | Bảng `invoices` và `invoice_items`. Hằng `TRANG_THAI_CON_HIEU_LUC` cho `scheduling.py` dùng khi chặn hủy lịch. `unit_price` và `description` **chép** lúc lập, không tham chiếu `services`; property `da_tra`, `con_no` |
| `models/payment.py` | Bảng `payments` — từng lần khách trả; CHECK `amount > 0` |
| `services/billing.py` | Nghiệp vụ hóa đơn: lập, thu tiền, hủy. Đường **duy nhất** ghi `payments` và trạng thái hóa đơn. Lập hóa đơn cho lịch có hóa đơn **đã hủy** thì mở lại chính hóa đơn đó theo giá và ngày hiện tại (S4 → S3 trong kế hoạch P7) |
| `services/stats.py` | Thống kê theo kỳ: `thong_ke()`, `ky_mac_dinh(den_ngay)`. Có `so_lich_qua_gio_chua_ghi` — lịch đã qua giờ mà chưa ai ghi hồ sơ (S5). Ba mốc ngày cố ý khác nhau — lượt và khách theo ngày hẹn (mọi lịch chưa hủy), doanh thu theo ngày thu (`payments`), chưa thu theo ngày lập. Tính trong Python để dùng lại `Invoice.con_no`; **không** lọc dịch vụ đã ngưng bán |
| `routers/auth.py` | `/login` (có giới hạn đăng nhập sai — R-1), `/logout` (thu hồi phiên — R-3), `/`, và `/doi-mat-khau` — tự đổi mật khẩu đặt ở đây vì cả ba vai trò đều dùng được, trong khi cả router `/users` chặn người không phải quản lý |
| `routers/users.py` | `/users` — quản lý tài khoản, chỉ vai trò `manager`. Thêm `/{id}/sua` và `/{id}/dat-lai-mat-khau` (M-02, 20/09). Chỉ HTTP, nghiệp vụ ở `services/users.py` |
| `routers/owners.py` | `/owners`, `/owners/{id}`, `/owners/{id}/sua`, `/owners/{id}/pets`, `/pets/{id}/xoa`. Hai đường dẫn xóa có **GET trang xác nhận** và POST làm việc thật — GET không đổi dữ liệu |
| `routers/services.py` | `/services` và `/services/goi` — chỉ `manager` sửa |
| `routers/care_records.py` | `/appointments/{id}/ho-so` — ghi và xem hồ sơ chăm sóc |
| `routers/pets.py` | `/pets/{id}` — trang chi tiết thú cưng, gộp lịch sử chăm sóc và hồ sơ tiêm (TC-020); `/pets/{id}/sua` (M-02) đặt ở đây để lỗi render lại đúng trang người dùng đang đứng; dùng chung `doc_ngay_form`/`doc_so_form` của `routers/owners.py` |
| `routers/vaccinations.py` | `/vaccinations` danh sách đến hạn; `/pets/{id}/vaccinations` ghi mũi tiêm |
| `routers/invoices.py` | `/invoices` danh sách, `/invoices/{id}` chi tiết, thu tiền, hủy hóa đơn. Cả router chặn `caretaker`. `GET /invoices/{id}/huy` là trang xác nhận, `POST` cùng đường dẫn mới hủy thật |
| `routers/stats.py` | `/stats?tu_ngay=&den_ngay=` — cả router chỉ `manager` (TC-006). Ô ngày trống → kỳ mặc định, tính lùi từ "Đến ngày" nếu đã chọn; ngày sai dạng → trang báo lỗi 400 tiếng Việt, giữ ngày đã nhập |
| `routers/ai.py` | `/ai/...` — soạn tin nhắc, tóm tắt, hỏi đáp, trang kết quả dùng chung, trang quota (chỉ `manager`). Theo mẫu **Post/Redirect/Get**: tải lại trang kết quả không gọi AI lần nữa. Chỉ import `app/ai/service.py`. `_quay_lai()` bỏ ký tự điều khiển rồi mới xét, và coi `\` ngang `/` (M-01) |
| `routers/appointments.py` | `/appointments` lưới lịch + đặt/đổi/hủy; `/appointments/cua-toi` lịch riêng của nhân viên chăm sóc |
| `templates/base.html` | Bố cục chung, menu hiện theo vai trò |
| `templates/_ai_gia_lap.html` | Dòng cảnh báo "Đang chạy chế độ AI giả lập", `include` vào ba trang AI. Có từ 19/09 sau khi người dùng tưởng câu mẫu của `fake` là Gemini trả lời sai |
| `templates/xac_nhan.html` | Trang hỏi lại dùng chung cho mọi thao tác cần xác nhận. Nhận `tieu_de`, `thong_tin`, `canh_bao`, `hanh_dong` (URL POST), `quay_lai`, `nut`, và tùy chọn `truong_an` (ô ẩn giữ dữ liệu đã gõ — M-07) + `kieu_nut`. Cố ý không dùng `confirm()` của JavaScript |
| `templates/login.html` · `home.html` · `users.html` · `error.html` | Các trang từ P1. `users.html` từ 20/09 có ô sửa họ tên + vai trò ngay trên dòng và ô đặt lại mật khẩu (M-02) |
| `templates/doi_mat_khau.html` | Trang tự đổi mật khẩu, mở cho **mọi vai trò** (M-02, 20/09). Bắt nhập mật khẩu hiện tại — khác đường "quản lý đặt lại" ở `/users` |
| `templates/owners.html` | Danh sách, tra cứu, form thêm chủ nuôi |
| `templates/owner_detail.html` | Chi tiết chủ nuôi, danh sách thú cưng, form thêm thú cưng |
| `templates/services.html` | Bảng giá, gói dịch vụ, form thêm dịch vụ và tạo gói |
| `templates/care_record_form.html` | Form ghi hồ sơ, hoặc nội dung hồ sơ đã ghi |
| `templates/pet_detail.html` | Trang chi tiết thú cưng: lịch sử chăm sóc + hồ sơ tiêm + form ghi mũi tiêm |
| `templates/vaccinations.html` | Danh sách đến hạn tiêm, có nhãn **Quá hạn** và dòng khuyến cáo bác sĩ thú y |
| `templates/invoices.html` | Danh sách hóa đơn, chưa thu lên đầu |
| `templates/invoice_detail.html` | Chi tiết hóa đơn: các dòng, lịch sử thanh toán, form thu tiền, nút hủy |
| `templates/ai_ket_qua.html` | Trang kết quả dùng chung cho ba tính năng. Nhắc lịch có ô sửa + nút Chốt + nút Sao chép; khuyến cáo đặt **trên** nội dung nên hiện cả khi AI lỗi |
| `templates/ai_hoi_dap.html` | Ô hỏi đáp, chặn bấm đúp bằng JS |
| `templates/ai_quota.html` | Bảng lượt gọi từng model cho quản lý, kèm nút đặt lại trạng thái |
| `templates/stats.html` | Form chọn kỳ, bốn thẻ số (lượt, doanh thu, chưa thu, tỉ lệ quay lại), bảng theo dịch vụ, trạng thái rỗng; một dòng giải thích ba mốc ngày |
| `templates/appointments.html` | Lưới lịch, form đặt lịch, cột thao tác đổi/hủy, khung trống khi bị từ chối. Dùng chung cho `/appointments` và `/appointments/cua-toi` |
| `static/style.css` | Toàn bộ CSS, một file, không build tool |

### Kiểm thử (`tests/`) — từ P1

| File | Vai trò |
|---|---|
| `conftest.py` | 5 fixture: `db` (CSDL in-memory riêng cho từng test, **bảng sao từ ảnh dựng sẵn `khung_csdl_rong`** — đổi 02/10, xem `test_conftest_db.py`), `client`, `frozen_clock`, `fake_ai` (khung, dùng từ P7), `seed_basic` (chỉ 4 tài khoản); cộng `bam_mat_khau_mau` băm mật khẩu mẫu một lần cho cả phiên test |
| `unit/test_security.py` | Băm mật khẩu (TC-005) |
| `unit/test_clock.py` | Cố định thời gian |
| `unit/test_models_user.py` | Ràng buộc bảng `users`: UNIQUE username, CHECK role |
| `unit/test_text.py` | Chuẩn hóa chuỗi tiếng Việt, gồm bẫy chữ `đ` |
| `unit/test_tien.py` | Đọc số tiền: phân cách nghìn, từ chối phần lẻ, `NaN`/`Infinity`, ô trống, số âm (L-03) |
| `unit/test_models_owner_pet.py` | Ràng buộc `owners`, `pets`, khóa ngoại, `search_name` |
| `unit/test_users_service.py` | Nghiệp vụ tài khoản: tạo, băm mật khẩu, trùng username, chặn tự khóa; `thu_hoi_phien` và các thao tác tăng `session_version` (R-3) |
| `unit/test_architecture.py` | **Canh ranh giới dự án** (55 phép canh), không kiểm chức năng: router không ghi thẳng CSDL, `services/` không import fastapi, router không import thẳng `app/ai`, mọi loại ô nhập dùng chung quy tắc khung, link tài liệu, `erd.md` khớp model tới từng cột (tập cột, NOT NULL, UNIQUE, FK), `codebase-map` đủ file (so **đuôi đường dẫn**, không so mỗi tên file — xem kẽ hở đã vá 13/09), hàm public có test gọi thẳng, class trong template có quy tắc CSS, chuỗi trạng thái tiền chỉ nằm ở model và service hóa đơn, thông báo lỗi không lộ mã phase, link menu nào cũng có thẻ trên trang chủ, dòng Trạng thái trong README khớp phase mới nhất, số kế hoạch/log phiên/báo cáo ghi trong chính file này khớp số file thật, ba system prompt in trong `ai-safety.md` khớp từng chữ với `prompts.py`, mọi biến trong `config.py` đều có mặt trong `.env.example`, **`CLAUDE.md` có mục 10 và mục 6 trỏ tới nó**. Phép canh đếm số log phiên **bỏ qua khung rỗng hook `SessionStart` vừa tạo** — đếm cả nó thì phép canh đỏ ở đầu mọi phiên chưa kịp ghi log, tức tự báo động giả (sửa 25/09, có test cô lập `dem_log_phien_da_ghi`). Phép canh **ngưỡng thời gian test**: mọi câu "vượt ngưỡng Ns" trong `docs/` phải khớp `test-strategy.md` — con số 90s từng bị chép lệch qua năm tài liệu, ba phiên |
| `unit/test_khoi_dong.py` | Lifespan từ chối khởi động với `SECRET_KEY` mặc định (S1). Gọi thẳng `lifespan`, engine in-memory |
| `unit/test_prompts.py` | Dựng prompt, ba system prompt, chèn `DISCLAIMER` (TC-082, 083, 088, 096) |
| `unit/test_guardrail.py` | Ba phép chặn trong code, nặng về **ca âm**: "nhân viên" không được coi là hỏi liều (TC-093) |
| `unit/test_ai_service.py` | Ba tính năng AI ở tầng nghiệp vụ, lọc dữ liệu cá nhân, ghi `ai_logs` (TC-082→098) |
| `unit/test_ai_quota.py` | Xoay ca model, ngày quota theo giờ Pacific, đếm lượt, bảng quota (TC-103→112) |
| `unit/test_gemini.py` | Đọc phản hồi và phân loại lỗi HTTP; chỉ thay `urlopen` — ranh giới ngoài |
| `unit/test_hooks.py` | Chạy thật hook `session-stop.ps1` trên bản sao dựng trong thư mục tạm: mọi log rỗng bị dọn, log đã điền (kể cả điền dở) còn nguyên. Tự bỏ qua khi máy không có PowerShell |
| `unit/test_conftest_db.py` | Canh fixture `db`: đủ bảng của mọi model, và **một dòng commit ở test trước không lọt sang test sau** (hai ca đứng liền nhau, phụ thuộc thứ tự khai báo). Đột biến 02/10: đổi `db` thành `scope="module"` thì ca thứ hai đỏ |
| `unit/test_run.py` | Test `run.py` (19 ca): `parse_env`, `ensure_env` **không ghi đè `.env` có sẵn (so từng byte)**, chỉ thay đúng dòng `SECRET_KEY` khi còn giá trị mặc định, khóa sinh ra đủ dài và khác nhau mỗi lần, chọn cổng, đường dẫn venv theo hệ điều hành, `db_file` từ chối CSDL không phải SQLite, lệnh con mặc định là `up`. Đột biến 02/10: vô hiệu nhánh `giu` thì hai ca đỏ |
| `unit/test_schema_upgrade.py` | `nang_cap_schema` (8 ca, gồm ca nâng cấp bảng `users` cũ lên có `session_version`): dựng DB từ schema cũ, chạy hai lần, cột có đúng một lần, dữ liệu cũ còn nguyên, từ chối cột không thêm được |
| `unit/test_login_throttle.py` | `GioiHanDangNhap` (13 ca): ngưỡng, khóa tăng dần, trần, đặt lại khi thành công, cách ly theo IP và tên đăng nhập, quên sau thời gian nghỉ, mật khẩu đúng vẫn bị từ chối khi đang khóa |
| `unit/test_csrf_origin.py` | `la_post_cheo_nguon` (27 ca, R-2, gồm các ca `APP_ORIGIN`): `Origin` khác `Host`, `Sec-Fetch-Site` khác `same-origin`/`none`, `Origin: null`, cổng khác, đuôi host giả; GET/HEAD/OPTIONS không bị kiểm; thiếu cả hai header thì qua
| `unit/test_cau_hinh_phien.py` | `SESSION_HTTPS_ONLY` đi từ biến môi trường tới `SessionMiddleware` (3 ca, mỗi giá trị một tiến trình riêng vì middleware dựng lúc import) |
| `unit/test_owners_service.py` | Nghiệp vụ chủ nuôi, thú cưng, tra cứu |
| `unit/test_models_service.py` | Ràng buộc `services`, gói, và **kiểu tiền `Decimal`** |
| `unit/test_catalog_service.py` | Nghiệp vụ dịch vụ, ngưng bán, gói |
| `unit/test_models_appointment.py` | Ràng buộc `appointments`: `end_at > start_at`, CHECK trạng thái |
| `unit/test_models_care_record.py` | Ràng buộc CSDL của `care_records` |
| `unit/test_models_vaccination.py` | Ràng buộc CSDL của `vaccinations`: CHECK `dose_no > 0`, `next_due_at >= given_at` |
| `unit/test_care_records_service.py` | Nghiệp vụ hồ sơ chăm sóc, lịch sử, ba trường suy từ lịch hẹn |
| `unit/test_vaccinations_service.py` | Nghiệp vụ tiêm phòng, ranh giới ngày, luật "chỉ tính mũi mới nhất" (TC-059→062) |
| `unit/test_billing_service.py` | Nghiệp vụ hóa đơn và thanh toán, gồm ca đổi giá dịch vụ không làm đổi hóa đơn cũ (TC-065→073) |
| `unit/test_stats_service.py` | Thống kê: TC-076 → TC-081, bất biến "bảng theo dịch vụ cộng lại bằng tổng", mốc ngày đầu/cuối kỳ, hóa đơn lập kỳ trước thu kỳ này, dịch vụ đã ngưng bán, kỳ mặc định. Dữ liệu đi qua luồng thật: đặt lịch → ghi hồ sơ → lập hóa đơn → thu tiền |
| `unit/test_scheduling.py` | **6 ca biên trùng lịch**, gợi ý khung trống, đổi lịch (TC-044→047), hủy lịch (TC-048, TC-049), chặn hủy lịch còn hóa đơn (TC-074, TC-075) |
| `integration/test_auth.py` | Đăng nhập (TC-001→004) |
| `integration/test_gioi_han_dang_nhap.py` | R-1 qua HTTP (6 ca): chuỗi đăng nhập sai bị 429 kèm `Retry-After`, người dùng/IP khác không bị ảnh hưởng, đăng nhập đúng xóa bộ đếm |
| `integration/test_chan_cheo_nguon.py` | R-2 qua HTTP (6 ca, gồm `APP_ORIGIN`): POST đổi trạng thái kèm `Origin` lạ bị 403 và **không được thực thi**, cùng host vẫn chạy, không header vẫn chạy, đăng nhập từ trang lạ cũng bị chặn, GET không bị chặn
| `integration/test_header_bao_mat.py` | R-4 (5 ca): `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` có trên trang thường, `/static`, trang 404, chuyển hướng và cả phản hồi 403 của middleware khác |
| `integration/test_thu_hoi_phien.py` | R-3 (6 ca): cookie cũ sau đăng xuất / đổi mật khẩu / đặt lại mật khẩu / khóa rồi mở khóa đều bị 303; máy vừa đổi mật khẩu không bị đá; cookie cũ chưa có `sv` vẫn hợp lệ |
| `integration/test_users.py` | Phân quyền và quản lý tài khoản (TC-007, 008, 010→012) |
| `integration/test_owners.py` | Chủ nuôi, thú cưng, tra cứu qua HTTP (TC-013→023) |
| `integration/test_services.py` | Dịch vụ, bảng giá, gói qua HTTP (TC-024→031) |
| `integration/test_care_records.py` | Ghi hồ sơ và trang thú cưng qua HTTP (TC-053, TC-054, TC-057, TC-058) |
| `integration/test_vaccinations.py` | Ghi mũi tiêm, danh sách đến hạn, link menu, khuyến cáo bác sĩ (TC-059, TC-063, TC-064, TC-020) |
| `integration/test_invoices.py` | Hóa đơn qua HTTP: nút trên lưới lịch, thu tiền, hủy, phân quyền (TC-065, TC-068→070, TC-072) |
| `integration/test_ai.py` | Ba tính năng AI qua HTTP: phân quyền, Post/Redirect/Get, AI lỗi không vỡ trang, `ai_logs` sạch dữ liệu liên hệ (TC-084→100) |
| `integration/test_stats.py` | Trang thống kê qua HTTP: TC-006 và lễ tân → 403, kỳ mặc định, kỳ trống, ngày ngược, ngày sai định dạng |
| `integration/test_seed.py` | Chạy `python -m app.seed` trong tiến trình riêng trên CSDL tạm; ngày lập hóa đơn = ngày buổi chăm sóc, ngày thu = ngày lập; dòng tổng kết đếm đúng số lịch hẹn (R-5) |
| `integration/test_khong_tim_thay.py` | Quét mọi đường dẫn theo id với bản ghi không tồn tại: không bao giờ 500; chín chỗ từng lỗi phải ra 404 (TC-115, H-03) |
| `integration/test_appointments.py` | Đặt/đổi/hủy lịch qua HTTP, lịch theo vai trò (TC-035, TC-043, TC-050→052, TC-009) |
| `e2e/test_full_flow.py` | **Kịch bản xuyên suốt TC-101 đủ 11 bước** trên CSDL file thật, đi bằng link và nút lấy từ HTML — không tự dựng URL. Chứa `TrinhDuyet`, trình duyệt tí hon gửi form đúng như trình duyệt |

### Cấu hình

| File | Vai trò |
|---|---|
| `requirements.txt` | Phụ thuộc, đã pin phiên bản. Có `tzdata` vì Windows không sẵn dữ liệu múi giờ, mà quota reset theo giờ Pacific |
| `pytest.ini` | `pythonpath`, `testpaths`, `filterwarnings = error` |

---

## Chưa có — sẽ thêm theo phase

Cấu trúc dưới đây theo [`architecture.md`](architecture.md). Khi một file được tạo, chuyển nó lên
mục "Hiện có" và ghi rõ vai trò thật, rồi xóa dòng ở đây.

| Đường dẫn | Vai trò dự kiến | Phase |
|---|---|---|
| ~~`app/schemas/`~~ | **Bỏ.** Qua P1→P3 form đọc thẳng bằng `Form()` và kiểm ở `services/` là đủ; thêm một tầng Pydantic nữa chỉ để lặp lại phép kiểm đã có | — |
