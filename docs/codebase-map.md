# Bản đồ mã nguồn

> **File này bắt buộc cập nhật mỗi khi thêm, xóa hoặc đổi vai trò một file.** Đây là thứ đầu tiên
> agent đọc ở mỗi phiên làm việc (xem [`../CLAUDE.md`](../CLAUDE.md) mục 6). Bản đồ lệch thực tế thì
> phiên sau sẽ làm việc dựa trên thông tin sai.

**Cập nhật lần cuối:** 2026-10-03 (**P9 chặng 7 (AI cho khách) và chặng 8 (đóng phase): đặc tả nhóm J, `README.md` viết lại, báo cáo P9, khối smoke P9**) · **Trạng thái:** **P0→P7 xong; P8 đang làm; P9 chặng 0→8 xong về code và tài liệu (còn ô 2.2: job CI `docker` chờ chạy trên GitHub; khối smoke P9 chờ người dùng tick).** Test ngày 03/10: **1381 passed, 1 skipped** (ca bỏ qua là `test_hooks.py:61`, máy Linux không có PowerShell), 59,22s. Đợt 03/10 sau đó: kiểm thử Chrome lại toàn bộ P9 trên CSDL demo, **hai lỗi chưa sửa chờ người dùng quyết (B-1 giao diện, B-2 thư giả của `MAIL_PROVIDER=console`)**, báo cáo tiến độ [`bao-cao-tien-do.md`](bao-cao-tien-do.md), hướng dẫn cho người không biết IT [`../HUONG-DAN-SU-DUNG.md`](../HUONG-DAN-SU-DUNG.md). Tiến độ từng phase: [`roadmap.md`](roadmap.md)

> ## Làm tiếp — đọc mục này trước tiên
>
> **1. VIỆC LỚN NHẤT: P9 — cổng khách hàng, ĐÃ DUYỆT 02/10/2026.**
> [`plans/2026-09-25-p9-cong-khach-hang.md`](plans/2026-09-25-p9-cong-khach-hang.md) — **chặng 0
> (fixture `db`), chặng 1 (tách đặc tả thành `docs/user-stories/`), chặng 2 (Docker, `run.py
> docker`, `--public-url`), chặng 3 (gửi email: `app/mail/`, bảng `email_tokens`) và **chặng 4 (tài khoản khách: bảng riêng `customers`, đăng ký bằng email, đăng nhập, quên/đổi mật khẩu, phiên tách khỏi nhân viên, luật khởi động công khai; đợt 4b: lễ tân duyệt nối hồ sơ chủ nuôi; đợt 4c: khách xem thú cưng, lịch hẹn, hóa đơn của mình qua một cổng chặn chủ duy nhất `yeu_cau_so_huu`, kèm phép canh AST và quét IDOR)** đã xong.** Còn **ô 2.2/2.5: job CI `docker`** chưa chạy trên GitHub nên chưa
> tick. **Chặng 5 đã làm phần lịch chờ duyệt (`pending`): khách xin lịch, lễ tân duyệt/từ chối, hạn 24 giờ** — xem
> [`plans/2026-10-02-p9-chang5-lich-cho-duyet.md`](plans/2026-10-02-p9-chang5-lich-cho-duyet.md); **chặng 6 thêm trang giờ trống theo nhân viên `/khach/khung-trong`** (bấm một giờ → form xin lịch điền sẵn); **chặng 7 thêm AI hỏi đáp cho khách `/khach/hoi-dap`** (hạn mức theo tài khoản, xem [`plans/2026-10-03-p9-chang7-ai-khach.md`](plans/2026-10-03-p9-chang7-ai-khach.md)). Giới hạn chặng 4 xem
> [`plans/2026-10-02-p9-chang4-tai-khoan-khach.md`](plans/2026-10-02-p9-chang4-tai-khoan-khach.md) cho giới hạn đã biết của chặng 4. Cổng khách: xem thú cưng (kèm lịch sử tiêm), lịch hẹn, hóa đơn và **xin đặt lịch**; chưa xem hồ sơ chăm sóc, chưa tự hủy lịch. **`SmtpMailer` chưa được
> thử với nhà cung cấp thật** (STARTTLS/AUTH chưa có test) — thử tay một lần trước khi công khai, xem
> [`plans/2026-10-02-p9-chang3-email.md`](plans/2026-10-02-p9-chang3-email.md). Chi tiết chặng 2 và giới hạn đã biết:
> [`trien-khai.md`](trien-khai.md), [`plans/2026-10-02-p9-chang2-docker.md`](plans/2026-10-02-p9-chang2-docker.md).
> **Đọc mục 1 và 2 của kế hoạch P9 trước khi bàn lại bất cứ điều gì** — bốn nhận xét của giảng viên
> và phản biện có bằng chứng nằm ở đó.
>
> **Kiểm tra nhanh toàn bộ chức năng trên CSDL mới:** `python tools/kiem_tra_song.py` (150 kiểm tra,
> server thật, không đụng `petcare.db`). Chạy lại sau mỗi chặng P9 để bắt hồi quy ở tầng HTTP thật.
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
| `ai/service.py` | Ba tính năng AI + `lay_provider()`. **Cửa duy nhất router được import** — có phép canh trong `test_architecture.py`. **Chặng 7:** `hoi_dap_khach` (hỏi đáp của khách; dùng chung thân `_hoi_dap` với nhân viên nên guardrail y hệt; kiểm hạn mức ngày TRƯỚC mọi thứ, hết lượt ném `LoiHetHanMuc` mà không gọi API, không ghi log), `so_luot_con_lai_khach`, `so_luot_toi_da_khach`, `lay_log_khach` (log của người khác / của nhân viên / không tồn tại cùng một `LoiKhongTimThay`) |

---

## Hiện có

### Gốc dự án

| File | Vai trò |
|---|---|
| `CLAUDE.md` | Nguyên tắc làm việc + ngữ cảnh dự án + quy trình mỗi phiên + luật kiểm thử + **mục 10: quy ước làm việc với người dùng** (chuyển từ bộ nhớ agent vào repo ngày 25/09, có phép canh giữ) |
| `đề-bài.md` | Đề bài gốc của môn học. **Không sửa** |
| `README.md` | Giới thiệu, cách chạy, cách chạy test |
| `HUONG-DAN-SU-DUNG.md` | **Hướng dẫn sử dụng cho người không biết IT** (03/10): phần mềm làm được gì, ba vai trò và quyền của từng vai trò, cổng khách hàng, cách bật, từng việc hằng ngày làm thế nào, giới hạn. Bản viết cho người dùng cuối; `README.md` là bản cho người cài đặt |
| `run.py` | **Chạy dự án bằng một lệnh** (chỉ thư viện chuẩn): tạo `.venv`, cài `requirements.txt` khi file đổi, tạo `.env` từ `.env.example` với `SECRET_KEY` ngẫu nhiên, seed khi CSDL chưa có, chọn cổng trống, chạy uvicorn, mở trình duyệt. Lệnh con: `reset` (xóa SQLite sau xác nhận), `status`, `test`; cờ `--check` (đợi `/login` 200 rồi tắt, dùng trong CI). **Cam kết: `.env` có sẵn không bao giờ bị ghi đè** — chỉ dòng `SECRET_KEY` bị thay khi thiếu hoặc còn giá trị mặc định | **Chặng 2 P9 (02/10):** lệnh `docker [up\|down\|logs\|reset]` (dùng `docker compose` v2, lùi về `docker-compose` v1; `up --check` dựng, đợi `/login`, `down -v` project riêng `petcare-check`) và cờ `--public-url https://…` (đặt `SESSION_HTTPS_ONLY`, `APP_ORIGIN` qua biến môi trường tiến trình con — **không ghi `.env`**; CSDL trống thì sinh mật khẩu seed ngẫu nhiên in một lần)
| `test.py` | Lối tắt của `python run.py test`: truyền nguyên tham số cho pytest, trả nguyên mã thoát |
| `tools/kiem_tra_song.py` | **Kiểm tra sống trên CSDL mới** (02/10). Một file, hai chế độ: *điều phối* (mặc định) tạo thư mục tạm, đặt `DATABASE_URL` trỏ vào đó, `AI_PROVIDER=fake`, `SECRET_KEY` ngẫu nhiên, chạy `app.seed`, bật uvicorn ở cổng trống, rồi gọi lại chính file này với `--kich-ban`; *kịch bản* đăng nhập bằng 4 tài khoản mẫu và chạy **150 kiểm tra HTTP thật** (phân quyền 3 vai trò × 12 trang, chủ nuôi, thú cưng, dịch vụ/gói, lịch hẹn trùng giờ/ngoài giờ/quá khứ, hồ sơ chăm sóc, hóa đơn và thu tiền, tiêm phòng, tài khoản, đổi mật khẩu, xóa có ràng buộc, thống kê, AI kèm câu xin thuốc, chống dò mật khẩu). Thoát 0/1; đếm phản hồi 500 trong log server; `--giu-lai` giữ thư mục tạm. **Không đụng `petcare.db`, không gọi Gemini.** Không nằm trong `tests/` nên pytest không chạy nó. Đột biến 02/10: đặt `GIO_MO_CUA = 0` thì đúng kiểm tra E4 đỏ |
| `tools/tao_du_lieu_demo.py` | **Dựng CSDL demo** (03/10). Tạo `demo.db` (mặc định, đổi bằng `--out`) từ trống: dữ liệu mẫu của `app.seed` cộng thêm chủ nuôi, thú cưng, lịch hẹn mọi trạng thái, hồ sơ chăm sóc, hóa đơn, tiêm phòng, 7 tài khoản khách (`khach1..7@demo.test`) ở đủ trạng thái, yêu cầu liên kết, lịch chờ duyệt, nhật ký AI. Cố định theo hạt giống nên dựng lại ra đúng bản cũ; **từ chối ghi đè `petcare.db`**. Chạy ứng dụng với nó: `DATABASE_URL=sqlite:///demo.db AI_PROVIDER=fake python run.py` |
| `.gitignore` | Bỏ qua `.venv`, `__pycache__`, `*.db`, `.env`, `.claude/settings.local.json` |
| `.env.example` | Mẫu biến môi trường (gồm khối gửi mail): khóa, **`SESSION_HTTPS_ONLY`, `APP_ORIGIN`**, **danh sách model Gemini**, ước tính hạn mức, `GEMINI_THINKING_BUDGET`, ngân sách thời gian mỗi lượt gọi AI. `.env` thật không vào repo. Có phép canh: mọi biến trong `config.py` phải có mặt ở đây |
| `Dockerfile` | Image `python:3.14-slim` (cùng bản Python với CI), chạy bằng user thường uid 10001, chỉ chép `requirements.txt` và `app/`, CSDL ở volume `/data`; `CMD` seed khi `/data/petcare.db` chưa có rồi chạy uvicorn. Một dòng `sh -c`, không file `.sh` (CRLF của Windows làm hỏng script trong container Linux) |
| `.dockerignore` | Loại `.env`, `*.db`, `.venv`, `.git`, `docs`, `tests`, `*.md` khỏi bối cảnh dựng image — bí mật không được nướng vào image. Có test canh |
| `docker-compose.yml` | Một service `web`: `env_file: .env`, ghi đè `DATABASE_URL` về `/data`, nhận `SESSION_HTTPS_ONLY`/`APP_ORIGIN`/`SEED_MAT_KHAU` từ `run.py` (mặc định tắt), cổng chỉ mở cho `127.0.0.1`, volume có tên `petcare-data`. Giữ `version: "3.8"` để `docker-compose` 1.x đọc được |

### `.claude/` — cấu hình agent, nằm trong repo

| File | Vai trò |
|---|---|
| `settings.json` | Đăng ký hook `SessionStart` và `Stop`. **Được commit** |
| `hooks/session-start.ps1` | Tạo `docs/sessions/YYYY-MM-DD-NN.md`, in nhắc nhở, cảnh báo nếu sai thư mục làm việc |
| `hooks/session-stop.ps1` | Chạy sau **mỗi lượt**: xóa **mọi** file log còn rỗng (mọi ngày, không chỉ file mới nhất), nhắc cập nhật codebase-map và checklist plan |

### `.github/` — CI, từ 25/09

| File | Vai trò |
|---|---|
| `workflows/ci.yml` | Chạy toàn bộ bộ test mỗi lần push lên `main` và mỗi pull request, trên **cả `windows-latest` lẫn `ubuntu-latest`** (`fail-fast: false` để Linux đỏ vẫn biết Windows xanh hay không). **Cố ý không tạo `.env`**: job xanh chính là bằng chứng suite chạy được bằng giá trị mặc định của `config.py`, tức người chấm clone repo về là test được ngay. Chạy `pytest -rs` để chỗ bỏ qua hiện ra trong log thay vì lẫn vào màu xanh — **Windows 0 ca bỏ qua, Linux đúng 1** (`test_hooks.py`, nó tìm lệnh `powershell` chứ không phải `pwsh`) **Job thứ hai `run-py`** (thêm 02/10) chạy `python run.py --no-open --check` trên máy sạch cả hai hệ: run.py tự dựng `.venv`, `.env`, seed rồi khởi động uvicorn thật và đợi `/login` trả 200 — đường có `.env`, ngược với job pytest | **Job thứ ba `docker`** (02/10, chặng 2 P9, chỉ Ubuntu) chạy `python run.py docker up --check`: dựng image thật, chạy container, đợi `/login` 200, dọn sạch. **Chưa từng chạy trên GitHub** — xanh hay đỏ chỉ biết sau lần đẩy tiếp theo

### `docs/`

| File | Vai trò |
|---|---|
| `user-stories/README.md` | Mục lục đặc tả: bảng 10 nhóm (A–J) với số story và số tiêu chí, quy ước ba mục, bảng đối chiếu với đề bài. 36 user story, **185** tiêu chí Given/When/Then (87 chấp nhận + 98 biên) — tách file ngày 02/10, xem [kế hoạch P9](plans/2026-09-25-p9-cong-khach-hang.md) |
| `user-stories/a-dang-nhap-phan-quyen.md` | Nhóm A · US-01→03: 15 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/b-chu-nuoi-thu-cung.md` | Nhóm B · US-04→06: 19 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/c-dich-vu-bang-gia.md` | Nhóm C · US-07→09: 11 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/d-lich-hen.md` | Nhóm D · US-10→14: 23 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/e-ho-so-cham-soc.md` | Nhóm E · US-15→16: 6 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/f-tiem-phong.md` | Nhóm F · US-17→18: 7 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/g-hoa-don-thanh-toan.md` | Nhóm G · US-19→21: 12 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/h-thong-ke.md` | Nhóm H · US-22→23: 6 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/i-chuc-nang-ai.md` | Nhóm I · US-24→28: 19 tiêu chí, mỗi story có Mục tiêu · Tiêu chí chấp nhận · Điều kiện biên |
| `user-stories/j-cong-khach-hang.md` | Nhóm J · US-29→36 (**ngoài đề bài**, vai trò `khach`): 27 chấp nhận + 40 biên — đăng ký email, liên kết hồ sơ, xem dữ liệu của mình, giờ trống, xin lịch, hỏi đáp AI; ba nguyên tắc (khách chỉ thấy dữ liệu của mình, không thao tác thay nhân viên, AI chỉ nhận câu hỏi) |
| `erd.md` | 17 bảng, sơ đồ Mermaid, mô tả cột và ràng buộc |
| `architecture.md` | Cây thư mục, ranh giới ba lớp, 3 sequence diagram, cách xử lý lỗi |
| `trien-khai.md` | Ba cách chạy (venv, Docker, công khai qua tunnel `--public-url`), đường chuyển PostgreSQL (chỉ ghi lại), bảng giới hạn đã biết: bộ đếm đăng nhập sai trong bộ nhớ, đăng xuất đá mọi thiết bị, chưa có CSP, cờ `Secure` mới kiểm ở mức header |
| `bao-cao-tien-do.md` | **Báo cáo tiến độ** (03/10): trạng thái P0→P9, số liệu đếm lại từ lượt chạy test, kết quả kiểm thử Chrome, bug còn lại (B-1, B-2), việc còn sót và việc của người dùng |
| `ai-safety.md` | System prompt 3 tính năng (có phép canh khớp `prompts.py`), `DISCLAIMER`, 20 ca guardrail G-01→G-20, kết quả chạy Gemini thật 19/09 |
| `codebase-map.md` | File này |
| `roadmap.md` | Lộ trình P0→P8 gắn với mốc KT1/KT2/KT3/cuối kỳ, kèm Definition of Done |
| `plans/README.md` | Quy ước lưu kế hoạch đã duyệt |
| `plans/YYYY-MM-DD-<slug>.md` | Một file mỗi kế hoạch đã duyệt, kèm checklist tick trong lúc làm. Hiện có 30: KT1/P0, P1, P2a, P2b, P3, P4, P5, e2e xuyên suốt, trả nợ kiến trúc, P6, dọn việc tồn P6, P7, rà soát P1→P7, sửa lỗi cao sau rà soát, chế độ AI giả lập, vá dữ liệu và sửa 4 lỗi ưu tiên (20/09), M-06 giờ mở cửa (24/09), 11 lỗi còn lại (24/09), **bộ đo AI có RAGAS (25/09 — đã duyệt, chưa làm)**, **CI và đặc tả theo kịp (25/09)**, **P9 cổng khách hàng (25/09 — CHƯA DUYỆT)**, **`run.py`/`test.py` và chặng bảo mật 0.5 trước P9 (02/10 — đã duyệt, Phiên 1 đang làm)**, **P9 chặng 2: Docker, `run.py docker`, `--public-url` (02/10 — đã duyệt, đang làm)**, **P9 chặng 3: hạ tầng gửi email (02/10)**, **P9 chặng 4: tài khoản khách và cách ly dữ liệu (02/10 — 4a, 4b, 4c đã xong)**, **P9 chặng 5: lịch chờ duyệt `pending` (02/10)**, **P9 chặng 6: bảng khung giờ trống theo nhân viên (02/10)**, **P9 chặng 7: AI hỏi đáp cho khách (03/10)**, **P9 chặng 8: đặc tả nhóm J, README, báo cáo P9 (03/10 — xong phần việc của agent)**, **kiểm thử P9, CSDL demo, báo cáo tiến độ, hướng dẫn sử dụng (03/10 — xong phần việc của agent)** |
| `sessions/README.md` | Quy ước log phiên làm việc |
| `sessions/YYYY-MM-DD-NN.md` | Một file mỗi phiên chat, hook tạo khung sẵn. Hiện có 16 |
| `testing/test-strategy.md` | 4 tầng test, 3 luật chống test giả, fixture, kịch bản e2e |
| `testing/test-cases.md` | Ma trận truy vết US → TC → file test, **182 dòng TC** (TC-001 → TC-182; bảng đối chiếu theo nhóm cộng đủ 182) — 180 ✅ · 1 ⬜ (TC-102 smoke) · 1 ➖ ngoài phạm vi (TC-027); TC-145 còn ⬜ ở phần CI. Mọi US-01 → US-36 đều có TC; TC-149 → TC-182 là cổng khách (P9 chặng 4–7) |
| `testing/smoke-checklist.md` | Checklist bấm tay theo từng phase |
| `testing/reports/README.md` | Mẫu báo cáo kiểm thử cuối phase |
| `testing/reports/YYYY-MM-DD-Pn.md` | Một file mỗi phase, chứa output pytest thật. Hiện có 26: mỗi phase một file, cộng sáu báo cáo rà luồng bằng trình duyệt (bản 19/09 kèm ảnh trong `anh-2026-09-19/`), một báo cáo rà bổ sung bằng HTTP (20/09, bốn phần lượt 19/09 chưa chạm), một báo cáo rà bằng Chrome trước khi sửa (20/09), một báo cáo trả nợ, một báo cáo dọn việc tồn và một báo cáo chạy Gemini thật (sinh bởi `python -m app.ai.quota --guardrail`) |

### Ứng dụng (`app/`) — từ P1

| File | Vai trò |
|---|---|
| `main.py` | Khởi tạo FastAPI, session middleware, **middleware `Cache-Control: no-store` cho mọi trang trừ `/static`** (L-02), **middleware `chan_cheo_nguon` trả 403 cho yêu cầu ghi từ trang khác** (R-2), **middleware `them_header_bao_mat` (lớp ngoài cùng, R-4)**, cờ `https_only` của session từ `SESSION_HTTPS_ONLY`, gọi `nang_cap_schema` sau `create_all`, đăng ký router, **từ chối khởi động khi `SECRET_KEY` còn mặc định** (S1), 3 trình xử lý lỗi (403/404 ra trang có bố cục, chưa đăng nhập thì chuyển về `/login`, `LoiNghiepVu` lọt khỏi router → trang 404/400 thay vì 500 — H-03) | **`lifespan` từ chối khởi động ở chế độ công khai** (`SESSION_HTTPS_ONLY`) khi còn tài khoản dùng mật khẩu mẫu (02/10)
| `config.py` | Đọc `.env` qua pydantic-settings: `DATABASE_URL`, `SECRET_KEY`, `AI_PROVIDER`, `GEMINI_API_KEY`, **`SESSION_HTTPS_ONLY`** (cờ Secure cho cookie phiên), **`APP_ORIGIN`** (địa chỉ công khai được tin ở bước chặn POST từ trang khác). Hằng `SECRET_KEY_MAC_DINH` để `main.py` chặn khởi động với khóa công khai (S1) | **`MAT_KHAU_MAC_DINH`** (chuyển từ `seed.py` sang đây, 02/10) và **`SEED_MAT_KHAU`** (mật khẩu seed; trống = mặc định), cùng 8 biến gửi mail `MAIL_PROVIDER`/`MAIL_FROM`/`SMTP_*`/`MAIL_TIMEOUT_GIAY` (P9 chặng 3)
| `db.py` | `Base`, `engine`, `SessionLocal`, `get_db()`. Bật `PRAGMA foreign_keys` cho từng kết nối SQLite |
| `security.py` | `hash_password()`, `verify_password()` — bcrypt trực tiếp, không qua passlib; `la_post_cheo_nguon()` — quyết định yêu cầu ghi có đến từ trang web khác không (R-2) |
| `app/auth.py` | Session cookie (mang `sv` = `session_version`, so khi đọc — R-3), `nguoi_dung_hien_tai`, `yeu_cau_vai_tro()`, ngoại lệ `ChuaDangNhap`; **phiên khách** (`khach_hien_tai`, khóa `customer_id`/`csv`, `ChuaDangNhapKhach`) tách hẳn khóa nhân viên và đăng nhập bên này xóa phiên bên kia. Ghi kèm thư mục để không lẫn với `routers/auth.py` |
| `templates.py` | Cấu hình Jinja2 dùng chung, filter `tien` (`{{ so|tien }}`), và hàm `che_do_ai_gia_lap()` cho template biết đang chạy `AI_PROVIDER=fake` |
| `seed.py` | 4 tài khoản, 3 chủ nuôi, 5 thú cưng, 5 dịch vụ, 2 gói, 8 lịch hẹn, 3 hồ sơ chăm sóc, 5 mũi tiêm, 2 hóa đơn, 2 lần thanh toán. Hóa đơn và lần trả mang **ngày của buổi chăm sóc** (lập trong `clock.freeze`), không phải ngày chạy seed. Hóa đơn dựng **qua `billing.py`** chứ không gán trạng thái tay. Chạy `python -m app.seed`, không sinh trùng | Mật khẩu lấy từ `settings.seed_mat_khau`, trống thì `matkhau123`; dòng in cuối in đúng mật khẩu đã dùng
| `models/__init__.py` | Gom mọi model — `create_all` chỉ tạo bảng đã được import |
| `models/user.py` | Bảng `users` (có `session_version` — R-3) + hằng `VAI_TRO`, `TEN_VAI_TRO` |
| `models/ai_log.py` | Bảng `ai_logs` — nhật ký gọi AI. Cột `model` NULL nghĩa là **không có lời gọi nào đi ra** (guardrail chặn trước hoặc thiếu dữ liệu). **Chặng 7:** chủ dòng là nhân viên (`user_id`) hoặc khách (`customer_id`, INDEX), CHECK đúng một trong hai |
| `models/ai_quota.py` | Bảng `ai_quota` — lượt đã dùng, hạn mức thật, trạng thái nghỉ/hết lượt/bị tắt của từng model theo từng ngày quota |
| `models/email_token.py` | Bảng `email_tokens` (P9 chặng 3) — token xác minh email / đặt lại mật khẩu. Gắn với **(email, mục đích)**, không với tài khoản; chỉ lưu **băm SHA-256** |
| `models/customer.py` | Bảng `customers` (P9 chặng 4) — tài khoản khách, **bảng riêng, không phải vai trò thứ tư của `users`** (`users.role` có CHECK mà SQLite không sửa được). Một dòng chỉ có SAU khi xác minh email; `owner_id` UNIQUE nối hồ sơ chủ nuôi (đợt 4b) |
| `models/link_request.py` | Bảng `link_requests` (P9 chặng 4b) — yêu cầu nối tài khoản khách với hồ sơ chủ nuôi. CHECK `status`, chỉ mục duy nhất từng phần: mỗi khách tối đa một yêu cầu `pending`; `owner_id` `ON DELETE SET NULL` |
| `mail/provider.py` | Interface `GuiMail` + `LoiGuiMail` (P9 chặng 3). Cùng mẫu Strategy với `ai/provider.py` |
| `mail/fake.py` | `FakeMailer`: ghi lại mọi thư, cài được lỗi. Dùng cho test — không thư nào ra khỏi tiến trình |
| `mail/console.py` | `ConsoleMailer`: in thư ra log, cho máy phát triển không có SMTP. **Không dùng cho bản công khai** |
| `mail/smtp.py` | `SmtpMailer`: `smtplib` thư viện chuẩn, STARTTLS, từ chối xuống dòng trong tiêu đề/người nhận, lỗi đổi thành `LoiGuiMail` không lộ mật khẩu |
| `mail/service.py` | `lay_mailer()` chọn bộ gửi theo `MAIL_PROVIDER`; tên lạ là lỗi chứ không rơi về `console` |
| `models/owner.py` | Bảng `owners`. `search_name` tự đồng bộ qua `@validates` |
| `models/pet.py` | Bảng `pets` + hằng `GIOI_TINH` (template dựng ô chọn từ đó, services kiểm theo đó — L-03). CHECK `weight_kg > 0`; ngày sinh kiểm ở tầng services |
| `models/service.py` | Bảng `services`. `price` kiểu `Numeric(12,2)`, **không** `Float` |
| `models/service_package.py` | `service_packages` + `package_items`, property `tong_gia_le`, `tiet_kiem` |
| `models/appointment.py` | Bảng `appointments` (chặng 5: thêm trạng thái `pending`, `customer_id`, `decided_by`; `created_by` cho NULL), hằng `TRANG_THAI`, 2 index phục vụ kiểm trùng |
| `services/clock.py` | `now()` và `freeze()` — điểm lấy thời gian duy nhất của hệ thống. `freeze()` dùng khi test và ở `seed.py` |
| `services/tien.py` | `doc_tien()` — đọc số tiền người dùng gõ. **Chỉ nhận số nguyên đồng**; dấu chấm/phẩy/khoảng trắng là phân cách nghìn, chuỗi có phần lẻ bị từ chối (L-03). Gom lại từ hai bản chép tay từng nằm ở `routers/services.py` và `routers/invoices.py` |
| `services/text.py` | `chuan_hoa()` — bỏ dấu tiếng Việt cho tìm kiếm, xử lý riêng chữ `đ` |
| `services/errors.py` | `LoiNghiepVu` — lỗi nghiệp vụ, thông điệp hiển thị thẳng cho người dùng. Lớp con `LoiKhongTimThay` cho mọi lần tra theo id không thấy bản ghi (H-03) |
| `services/schema.py` | `nang_cap_schema(engine, metadata)` — thêm cột còn thiếu bằng `ALTER TABLE ... ADD COLUMN`, chạy lại an toàn; `create_all` chỉ tạo bảng thiếu chứ không thêm cột. Gọi trong `lifespan` ngay sau `create_all`. Từ chối cột không thể thêm (PK, UNIQUE, NOT NULL không có `server_default`) bằng `LoiNangCap`. **`dung_lai_bang_lich_hen`** (chặng 5): SQLite không sửa được CHECK/NOT NULL nên dựng lại `appointments` (đổi tên, tạo mới, chép dòng, bỏ bảng cũ, tạo lại index) trong một giao dịch với `foreign_keys=OFF` + `legacy_alter_table=ON`; bảng đã có `pending` thì không làm gì. Gọi trong `lifespan` ngay sau `nang_cap_schema`. **`dung_lai_bang_nhat_ky_ai`** (chặng 7): cùng quy trình (chung `_dung_lai_bang`) cho `ai_logs` khi `user_id` còn NOT NULL; gọi sau `dung_lai_bang_lich_hen` |
| `services/login_throttle.py` | `GioiHanDangNhap` (R-1): giới hạn đăng nhập sai theo cặp (IP, tên đăng nhập), miễn phí 5 lần rồi khóa 30 giây, mỗi lần sai tiếp theo gấp đôi, trần 900 giây; đăng nhập đúng xóa bộ đếm; quên sau 3600 giây không hoạt động. Lưu trong bộ nhớ tiến trình, có khóa luồng. Singleton `gioi_han_dang_nhap`
| `services/email_tokens.py` | `cap_token()`, `dung_token()` (P9 chặng 3): hết hạn (24h xác minh / 1h đặt lại), dùng một lần bằng một lệnh `UPDATE … WHERE used_at IS NULL`, mọi thất bại cùng một thông báo. `con_hieu_luc()` xem token **không tiêu thụ** (cho trang `GET`). Dùng bởi `customers.py` |
| `services/customers.py` | Tài khoản khách (P9 chặng 4a): `yeu_cau_dang_ky`/`hoan_tat_dang_ky` (khách đặt mật khẩu **sau** khi bấm link — không có tài khoản chưa xác minh), `xac_thuc`, `yeu_cau_dat_lai`/`dat_lai_mat_khau`, `doi_mat_khau`, `thu_hoi_phien`. Đăng ký và quên mật khẩu **không lộ email có tồn tại hay không**; lỗi gửi thư bị nuốt. Nhận `mailer` từ ngoài |
| `services/link_requests.py` | Nối khách với hồ sơ chủ nuôi (P9 chặng 4b): `gui_yeu_cau` (**không tra `owners`**, không tự nối), `yeu_cau_cua_khach`, `danh_sach_cho_duyet` (kèm hồ sơ gợi ý cùng số, bỏ hồ sơ đã có chủ), `duyet` (chặn hồ sơ đã thuộc khách khác, duyệt hai lần, khách đã nối), `tu_choi` (bắt buộc lý do), `go_lien_ket`, `danh_sach_da_lien_ket`. Không import fastapi |
| `services/khach_du_lieu.py` | Dữ liệu khách được xem (P9 chặng 4c) — **cổng duy nhất** từ cổng khách tới dữ liệu chủ nuôi. `yeu_cau_so_huu(khach, ban_ghi)` là điểm chặn chủ: id của người khác và id không tồn tại cùng ném `LoiKhongTimThay` (404, không 403). `danh_sach_thu_cung`, `chi_tiet_thu_cung` (kèm tiêm phòng), `danh_sach_lich_hen`, `danh_sach_hoa_don`, `chi_tiet_hoa_don`; khách chưa nối nhận danh sách rỗng. Không mở hồ sơ chăm sóc. **Chặng 6:** `khung_trong_cua_khach` (giờ trống trong một ngày, nhóm theo nhân viên đang hoạt động; tính theo cả nhân viên lẫn thú cưng của khách, lịch `pending` còn hạn tính là bận; trả `KhungTrongNhanVien` chỉ có hai trường `nhan_vien`, `gio` nên không lọt dữ liệu người khác; thú cưng người khác = id không tồn tại → 404). **Chặng 5:** `lua_chon_dat_lich` (thú cưng của khách, dịch vụ, nhân viên, số lịch chờ / trần) và `gui_yeu_dat_lich` (thú cưng của người khác = id không tồn tại → 404, rồi mới gọi `scheduling.tao_yeu_cau_lich`). Không import fastapi |
| `models/care_record.py` | Bảng `care_records` — hồ sơ chăm sóc, quan hệ 1–1 với lịch hẹn (`appointment_id` UNIQUE) |
| `models/vaccination.py` | Bảng `vaccinations` — mũi tiêm và hạn nhắc lại; property `qua_han` |
| `services/users.py` | Nghiệp vụ tài khoản nhân viên: tạo, **sửa**, khóa, mở khóa, danh sách, **đặt lại và tự đổi mật khẩu**. Chặn quản lý tự khóa mình và tự bỏ vai trò quản lý. `kiem_mat_khau()` là cửa chung của **cả ba** đường đặt mật khẩu (M-04) | **`tai_khoan_con_mat_khau_mac_dinh(db)`** (02/10): tên đăng nhập còn dùng mật khẩu mẫu, kể cả tài khoản bị khóa; `lifespan` dùng khi bật `SESSION_HTTPS_ONLY`
| `services/owners.py` | Nghiệp vụ chủ nuôi và thú cưng: tạo, sửa, xóa, tra cứu. Giữ **mọi phép kiểm dữ liệu nhập**: định dạng số điện thoại và email (M-05), `chuan_hoa_so_dien_thoai()` dùng chung với phép kiểm trùng (M-07), trần độ dài chuỗi, cân nặng, tuổi, danh sách giới tính (L-03) |
| `services/catalog.py` | Nghiệp vụ dịch vụ và gói. `danh_sach_dang_ban()` là danh sách P3 và P5 sẽ dùng. Thời lượng có **cận trên** `PHUT_LAM_VIEC_MOI_NGAY` nhập từ `scheduling` — nhập một hằng số chứ không gọi hàm, nên hai service vẫn tách ra được (M-06) |
| `services/care_records.py` | Nghiệp vụ hồ sơ chăm sóc. Thao tác **duy nhất** đưa lịch hẹn về `done`. Lịch `pending` (chưa được duyệt) bị chặn ghi hồ sơ |
| `services/scheduling.py` | **Quy tắc chống trùng lịch**, **luật giờ mở cửa** (`_kiem_gio_lam_viec` — cả buổi phải nằm trọn trong `GIO_MO_CUA`–`GIO_DONG_CUA` cùng một ngày, áp cho cả đặt lẫn đổi lịch; M-06 sửa 24/09), đặt/đổi/hủy lịch, gợi ý khung trống (`khung_gio_trong(..., toi_da=SO_GOI_Y)`; `toi_da=None` quét cả ngày mở cửa theo bước 30 phút, khung kết thúc đúng giờ đóng cửa vẫn hợp lệ — chặng 6), `so_lich_chua_lam_theo_nhan_vien()` cho cảnh báo nhân viên đã khóa (S4). Đổi lịch kiểm nhân viên **cả khi giữ nguyên người**. Khoảng nửa mở `[start, end)`. Hủy lịch còn chặn khi lịch đang có hóa đơn chưa hủy (US-21) — biết model `Invoice`, không gọi sang `billing.py`. **Lịch chờ duyệt (chặng 5):** `tao_yeu_cau_lich`, `danh_sach_cho_duyet`, `duyet_lich_cho`, `tu_choi_lich_cho`, `huy_lich_cho_het_han`, `so_lich_cho_cua_khach`. Lịch `pending` **giữ chỗ** `HAN_CHO_DUYET_GIO`=24 giờ — điều kiện giữ chỗ nằm trong truy vấn chống trùng (`_giu_cho`) nên đúng cả khi chưa ai quét; hàm quét chỉ đổi trạng thái hiển thị. Trần `TRAN_LICH_CHO_MOI_KHACH`=3 lịch chờ mỗi khách. Phép kiểm đặt lịch dùng chung (`_kiem_dieu_kien_dat`) cho lễ tân và khách |
| `services/vaccinations.py` | Nghiệp vụ tiêm phòng: ghi mũi, hồ sơ tiêm, danh sách đến hạn. Chỉ tính mũi mới nhất của mỗi loại vắc-xin; tên vắc-xin gõ khác hoa thường/dấu được quy về tên đã có của chính thú cưng đó (S2) |
| `models/invoice.py` | Bảng `invoices` và `invoice_items`. Hằng `TRANG_THAI_CON_HIEU_LUC` cho `scheduling.py` dùng khi chặn hủy lịch. `unit_price` và `description` **chép** lúc lập, không tham chiếu `services`; property `da_tra`, `con_no` |
| `models/payment.py` | Bảng `payments` — từng lần khách trả; CHECK `amount > 0` |
| `services/billing.py` | Nghiệp vụ hóa đơn: lập, thu tiền, hủy. Đường **duy nhất** ghi `payments` và trạng thái hóa đơn. Lập hóa đơn cho lịch có hóa đơn **đã hủy** thì mở lại chính hóa đơn đó theo giá và ngày hiện tại (S4 → S3 trong kế hoạch P7). Lịch `pending` bị chặn lập hóa đơn với thông điệp "chờ duyệt" riêng |
| `services/stats.py` | Thống kê theo kỳ: `thong_ke()`, `ky_mac_dinh(den_ngay)`. Có `so_lich_qua_gio_chua_ghi` — lịch đã qua giờ mà chưa ai ghi hồ sơ (S5). Ba mốc ngày cố ý khác nhau — lượt và khách theo ngày hẹn (mọi lịch chưa hủy), doanh thu theo ngày thu (`payments`), chưa thu theo ngày lập. Tính trong Python để dùng lại `Invoice.con_no`; **không** lọc dịch vụ đã ngưng bán |
| `routers/auth.py` | `/login` (có giới hạn đăng nhập sai — R-1), `/logout` (thu hồi phiên — R-3), `/`, và `/doi-mat-khau` — tự đổi mật khẩu đặt ở đây vì cả ba vai trò đều dùng được, trong khi cả router `/users` chặn người không phải quản lý |
| `routers/khach_auth.py` | `/khach/*` (P9 chặng 4a): đăng ký, `dang-ky/{token}`, đăng nhập/xuất, quên mật khẩu, `dat-lai/{token}`, đổi mật khẩu, trang chủ khách. Liên kết trong thư dựng từ `APP_ORIGIN`, không từ `Host`; `GET` liên kết không tiêu thụ token; đăng ký/quên mật khẩu giới hạn 429 theo IP |
| `routers/khach_lien_ket.py` | `/khach/lien-ket` (P9 chặng 4b): khách xin nối hồ sơ bằng số điện thoại + ghi chú; thấy trạng thái chờ / bị từ chối kèm lý do. Phản hồi không phụ thuộc số có phải chủ nuôi hay không |
| `routers/lien_ket_khach.py` | `/lien-ket-khach` (P9 chặng 4b): màn hình lễ tân. Duyệt (chọn ứng viên cùng số hoặc nhập mã hồ sơ khác), từ chối kèm lý do, gỡ liên kết. Chỉ `manager` và `receptionist`; `caretaker` 403, khách bị đưa về `/login` |
| `routers/khach_ai.py` | `GET/POST /khach/hoi-dap`, `GET /khach/hoi-dap/{log_id}` (P9 chặng 7): khách hỏi đáp AI, Post/Redirect/Get; hết hạn mức 429, lỗi AI 400 giữ câu đã gõ, log của người khác 404. Chỉ gọi `ai/service.py` — không import model, không `db.*`, chỉ các hàm trong `HAM_AI_CHO_KHACH` (phép canh AST) |
| `routers/lich_cho_duyet.py` | `/lich-cho-duyet` (P9 chặng 5): màn hình duyệt lịch `pending` của lễ tân — danh sách, duyệt, từ chối kèm lý do bắt buộc. Chỉ `manager` và `receptionist`; `caretaker` 403, khách bị đưa về `/login`. Chỉ gọi `scheduling` |
| `routers/khach_du_lieu.py` | `/khach/thu-cung`, `/khach/thu-cung/{id}`, `/khach/lich-hen`, `/khach/hoa-don`, `/khach/hoa-don/{id}` (P9 chặng 4c) và **`GET/POST /khach/dat-lich`** (chặng 5: form xin lịch, lỗi nghiệp vụ hiện lại form 400 giữ ô đã nhập; chặng 6: nhận `thu_cung_id`, `dich_vu_id`, `nhan_vien_id`, `ngay`, `gio` trên query để điền sẵn) và **`GET /khach/khung-trong`** (chặng 6: chọn thú cưng, dịch vụ, ngày → giờ trống từng nhân viên; ngày sai định dạng 400, thú cưng/dịch vụ không có 404). **Chỉ gọi `services/khach_du_lieu.py`**: không import model, không `db.*` — phép canh AST trong `test_architecture.py` |
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
| `templates/khach_base.html` · `khach_dang_ky.html` · `khach_da_gui_thu.html` · `khach_dat_mat_khau.html` · `khach_lien_ket_hong.html` · `khach_dang_nhap.html` · `khach_quen_mat_khau.html` · `khach_dat_lai.html` · `khach_trang_chu.html` · `khach_doi_mat_khau.html` | Cổng khách (P9 chặng 4a). `khach_base.html` **không** dùng `base.html` — khách không bao giờ thấy menu nhân viên. `khach_da_gui_thu.html` có cùng một nội dung dù email có tài khoản hay không |
| `templates/khach_hoi_dap.html` · `khach_ket_qua_hoi_dap.html` | Chặng 7: form hỏi AI (câu khuyến cáo cố định trong template, hiện cả khi AI lỗi / hết lượt; số lượt còn lại; chặn bấm đúp) và trang kết quả đọc lại theo `log_id` (câu hỏi, trả lời, khuyến cáo). Không có dữ liệu thú cưng hay chủ nuôi |
| `templates/khach_khung_trong.html` | Chặng 6: form chọn (thú cưng, dịch vụ, ngày) và từng nhân viên một khối với các giờ trống; mỗi giờ là link `/khach/dat-lich?...` điền sẵn. Chỉ là gợi ý, lúc gửi yêu cầu mọi phép kiểm chạy lại |
| `templates/khach_dat_lich.html` · `lich_cho_duyet.html` | Chặng 5: form khách xin lịch (chọn thú cưng của mình, dịch vụ, nhân viên, ngày giờ; báo số lịch chờ đang có / trần) và màn hình duyệt của lễ tân (từng yêu cầu: nút duyệt, ô lý do + nút từ chối) |
| `templates/khach_lien_ket.html` · `lien_ket_khach.html` | Đợt 4b: form xin liên kết phía khách (kèm trạng thái chờ / từ chối + lý do) và màn hình duyệt của lễ tân (yêu cầu chờ, hồ sơ gợi ý, tài khoản đã nối + nút gỡ) |
| `templates/khach_thu_cung.html` · `khach_chi_tiet_thu_cung.html` · `khach_lich_hen.html` · `khach_hoa_don.html` · `khach_chi_tiet_hoa_don.html` | Đợt 4c: trang dữ liệu của khách. Chỉ đọc các trường nêu rõ; **không** hiện `note`, tên nhân viên, địa chỉ, hồ sơ chăm sóc (test canh bằng chuỗi `BIMAT`) |
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
| `unit/test_users_service.py` | Nghiệp vụ tài khoản: tạo, băm mật khẩu, trùng username, chặn tự khóa; `thu_hoi_phien` và các thao tác tăng `session_version` (R-3) | · `tai_khoan_con_mat_khau_mac_dinh` (3 ca: đổi xong thì thoát danh sách, tài khoản khóa vẫn tính, rỗng khi hết)
| `unit/test_architecture.py` | **Canh ranh giới dự án** (84 ca thu thập, đo 03/10), không kiểm chức năng: **phép canh router AI của khách (chặng 7): chỉ gọi các hàm hỏi đáp của `ai/service.py`, không chạm model/`db.*`, có ca đối chứng**, **phép canh template cổng khách (chặng 6): `khach_*.html` không truy cập `owner.`/`.owner` trong biểu thức Jinja và không có link `/owners`, `/pets/` của trang nhân viên (có ca đối chứng)**, **cổng khách (4c): router dữ liệu khách không chạm model/`db.*`, mọi hàm public của `khach_du_lieu` đi qua `ma_chu_nuoi`/`yeu_cau_so_huu`, mọi route `/khach/*` ngoài trang công khai dùng `khach_hien_tai` (AST, có ca đối chứng)**, router không ghi thẳng CSDL, `services/` không import fastapi, router không import thẳng `app/ai`, mọi loại ô nhập dùng chung quy tắc khung, link tài liệu, `erd.md` khớp model tới từng cột (tập cột, NOT NULL, UNIQUE, FK), `codebase-map` đủ file (so **đuôi đường dẫn**, không so mỗi tên file — xem kẽ hở đã vá 13/09), hàm public có test gọi thẳng, class trong template có quy tắc CSS, chuỗi trạng thái tiền chỉ nằm ở model và service hóa đơn, thông báo lỗi không lộ mã phase, link menu nào cũng có thẻ trên trang chủ, dòng Trạng thái trong README khớp phase mới nhất, số kế hoạch/log phiên/báo cáo ghi trong chính file này khớp số file thật, ba system prompt in trong `ai-safety.md` khớp từng chữ với `prompts.py`, mọi biến trong `config.py` đều có mặt trong `.env.example`, **`CLAUDE.md` có mục 10 và mục 6 trỏ tới nó**. Phép canh đếm số log phiên **bỏ qua khung rỗng hook `SessionStart` vừa tạo** — đếm cả nó thì phép canh đỏ ở đầu mọi phiên chưa kịp ghi log, tức tự báo động giả (sửa 25/09, có test cô lập `dem_log_phien_da_ghi`). Phép canh **ngưỡng thời gian test**: mọi câu "vượt ngưỡng Ns" trong `docs/` phải khớp `test-strategy.md` — con số 90s từng bị chép lệch qua năm tài liệu, ba phiên |
| `unit/test_khoi_dong.py` | Lifespan từ chối khởi động với `SECRET_KEY` mặc định (S1). Gọi thẳng `lifespan`, engine in-memory | · Chế độ công khai từ chối khi còn mật khẩu mẫu, chế độ thường không kiểm, qua sau khi đổi mật khẩu (3 ca); **công khai mà `MAIL_PROVIDER=console` hoặc thiếu `APP_ORIGIN` thì từ chối** (P9 chặng 4a)
| `unit/test_prompts.py` | Dựng prompt, ba system prompt, chèn `DISCLAIMER` (TC-082, 083, 088, 096) |
| `unit/test_guardrail.py` | Ba phép chặn trong code, nặng về **ca âm**: "nhân viên" không được coi là hỏi liều (TC-093) |
| `unit/test_ai_khach.py` | Hỏi đáp AI của khách ở tầng nghiệp vụ (21 ca, chặng 7): log gắn `customer_id`, chỉ câu hỏi đã lọc đi sang AI (không tên/email khách), xin thuốc chặn trước khi gọi, liều bị thay, câu rỗng/quá dài; hạn mức ngày: chạm hạn mức không gọi API không ghi log, tính riêng từng khách, sang ngày mới hỏi lại, lỗi AI không tính lượt; `lay_log_khach` chỉ trả cho chủ (TC-179, TC-180) |
| `unit/test_ai_service.py` | Ba tính năng AI ở tầng nghiệp vụ, lọc dữ liệu cá nhân, ghi `ai_logs` (TC-082→098) |
| `unit/test_ai_quota.py` | Xoay ca model, ngày quota theo giờ Pacific, đếm lượt, bảng quota (TC-103→112) |
| `unit/test_gemini.py` | Đọc phản hồi và phân loại lỗi HTTP; chỉ thay `urlopen` — ranh giới ngoài |
| `unit/test_hooks.py` | Chạy thật hook `session-stop.ps1` trên bản sao dựng trong thư mục tạm: mọi log rỗng bị dọn, log đã điền (kể cả điền dở) còn nguyên. Tự bỏ qua khi máy không có PowerShell |
| `unit/test_conftest_db.py` | Canh fixture `db`: đủ bảng của mọi model, và **một dòng commit ở test trước không lọt sang test sau** (hai ca đứng liền nhau, phụ thuộc thứ tự khai báo). Đột biến 02/10: đổi `db` thành `scope="module"` thì ca thứ hai đỏ |
| `unit/test_run.py` | Test `run.py` (42 ca: 19 từ 02/10 phiên 1 + 23 của chặng 2): `parse_env`, `ensure_env` **không ghi đè `.env` có sẵn (so từng byte)**, chỉ thay đúng dòng `SECRET_KEY` khi còn giá trị mặc định, khóa sinh ra đủ dài và khác nhau mỗi lần, chọn cổng, đường dẫn venv theo hệ điều hành, `db_file` từ chối CSDL không phải SQLite, lệnh con mặc định là `up`. Đột biến 02/10: vô hiệu nhánh `giu` thì hai ca đỏ | **Chặng 2 P9 (+23 ca):** `public_env` (https bắt buộc, bỏ `/` cuối, từ chối đường dẫn), `new_seed_password`, `parse_args` cho `docker` và `--public-url`, `compose_args` (`reset` có `-v`, `down` không), `compose_cmd` (v2 trước v1), `docker_env`, `wait_healthy(alive=…)` bỏ cuộc ngay khi tiến trình chết. 7 đột biến đều bị bắt
| `unit/test_mail.py` | `FakeMailer`, `ConsoleMailer`, `lay_mailer()` chọn theo cấu hình (TC-146) |
| `unit/test_smtp_mailer.py` | `SmtpMailer` nói SMTP thật với **máy chủ cục bộ trong tiến trình test**: người nhận, tiêu đề tiếng Việt, chặn chèn `Bcc:`, lỗi không lộ mật khẩu; và fixture `chan_gui_mail_that` tự canh (TC-147) |
| `unit/test_email_tokens_service.py` | Token: hết hạn đúng ranh giới, dùng một lần (kể cả đối tượng cũ trong bộ nhớ), sai mục đích, chuỗi bịa, cấp mới vô hiệu cũ, không lưu token thô (TC-148) |
| `unit/test_customers_service.py` | Tài khoản khách: đăng ký tạo khách chỉ sau khi bấm link, email có sẵn không tạo bản ghi thứ hai và không lộ, token hết hạn/dùng lại, mật khẩu yếu bị chặn **trước** khi tiêu thụ token, đăng nhập chung một thông báo, đặt lại/đổi mật khẩu thu hồi phiên, lỗi gửi thư bị nuốt (TC-149) |
| `unit/test_link_requests_service.py` | Nối khách với hồ sơ (29 ca): gửi yêu cầu không tra `owners` và không tự nối, một yêu cầu chờ mỗi khách, ghi chú/số sai bị từ chối, danh sách chờ kèm gợi ý và bỏ hồ sơ đã có chủ, duyệt chặn hồ sơ khách khác / duyệt hai lần / hồ sơ không tồn tại, từ chối bắt buộc lý do, gỡ liên kết rồi duyệt lại cho khách khác (TC-156, TC-157) |
| `unit/test_khach_du_lieu_service.py` | Cổng dữ liệu khách (28 ca): `yeu_cau_so_huu` cho qua bản ghi của chính chủ và chặn của chủ khác / khách chưa nối ở cả năm loại bản ghi (thú cưng, hóa đơn, lịch hẹn, tiêm phòng, hồ sơ chăm sóc), thông điệp chặn giống nhau cho id người khác và id không tồn tại, danh sách chỉ của mình và đúng thứ tự, gỡ liên kết có hiệu lực ngay (TC-161) |
| `unit/test_docker_files.py` | Canh file Docker không cần chạy Docker (9 ca): `.dockerignore` loại `.env`/`*.db`/`.venv`/`.git`; Dockerfile không `COPY .env` hay `COPY . .`, có `USER` thường trước `CMD`, CSDL ở `/data`, seed có điều kiện, cài thư viện trước khi chép mã; compose chỉ mở cổng cho `127.0.0.1`, volume có tên, không ghi cứng `SECRET_KEY`/mật khẩu |
| `unit/test_schema_upgrade.py` | `nang_cap_schema` và hai hàm dựng lại bảng (19 ca; **chặng 7: dựng lại `ai_logs`** — giữ dòng cũ, nhận dòng khách, CHECK một chủ, chạy lại, sau `ALTER` tay; trong đó `nang_cap_schema` 8 ca, gồm ca nâng cấp bảng `users` cũ lên có `session_version`): dựng DB từ schema cũ, chạy hai lần, cột có đúng một lần, dữ liệu cũ còn nguyên, từ chối cột không thêm được |
| `unit/test_login_throttle.py` | `GioiHanDangNhap` (13 ca): ngưỡng, khóa tăng dần, trần, đặt lại khi thành công, cách ly theo IP và tên đăng nhập, quên sau thời gian nghỉ, mật khẩu đúng vẫn bị từ chối khi đang khóa |
| `unit/test_csrf_origin.py` | `la_post_cheo_nguon` (27 ca, R-2, gồm các ca `APP_ORIGIN`): `Origin` khác `Host`, `Sec-Fetch-Site` khác `same-origin`/`none`, `Origin: null`, cổng khác, đuôi host giả; GET/HEAD/OPTIONS không bị kiểm; thiếu cả hai header thì qua
| `unit/test_cau_hinh_phien.py` | `SESSION_HTTPS_ONLY` đi từ biến môi trường tới `SessionMiddleware` (3 ca, mỗi giá trị một tiến trình riêng vì middleware dựng lúc import) |
| `unit/test_owners_service.py` | Nghiệp vụ chủ nuôi, thú cưng, tra cứu |
| `unit/test_models_service.py` | Ràng buộc `services`, gói, và **kiểu tiền `Decimal`** |
| `unit/test_catalog_service.py` | Nghiệp vụ dịch vụ, ngưng bán, gói |
| `unit/test_models_appointment.py` | Ràng buộc `appointments`: `end_at > start_at`, CHECK trạng thái |
| `unit/test_models_care_record.py` | Ràng buộc CSDL của `care_records` |
| `unit/test_models_vaccination.py` | Ràng buộc CSDL của `vaccinations`: CHECK `dose_no > 0`, `next_due_at >= given_at` |
| `unit/test_models_link_request.py` | Ràng buộc `link_requests`: mặc định `pending`, hai yêu cầu chờ của một khách bị CSDL từ chối, yêu cầu đã xử lý không chặn yêu cầu mới, `status` sai bị CHECK chặn, xóa chủ nuôi giữ yêu cầu và gán `owner_id` NULL (TC-155) |
| `unit/test_care_records_service.py` | Nghiệp vụ hồ sơ chăm sóc, lịch sử, ba trường suy từ lịch hẹn |
| `unit/test_vaccinations_service.py` | Nghiệp vụ tiêm phòng, ranh giới ngày, luật "chỉ tính mũi mới nhất" (TC-059→062) |
| `unit/test_billing_service.py` | Nghiệp vụ hóa đơn và thanh toán, gồm ca đổi giá dịch vụ không làm đổi hóa đơn cũ (TC-065→073) |
| `unit/test_stats_service.py` | Thống kê: TC-076 → TC-081, bất biến "bảng theo dịch vụ cộng lại bằng tổng", mốc ngày đầu/cuối kỳ, hóa đơn lập kỳ trước thu kỳ này, dịch vụ đã ngưng bán, kỳ mặc định. Dữ liệu đi qua luồng thật: đặt lịch → ghi hồ sơ → lập hóa đơn → thu tiền |
| `unit/test_scheduling.py` | **6 ca biên trùng lịch**, gợi ý khung trống (kèm `toi_da=None` quét cả ngày, TC-174), đổi lịch (TC-044→047), hủy lịch (TC-048, TC-049), chặn hủy lịch còn hóa đơn (TC-074, TC-075) |
| `integration/test_auth.py` | Đăng nhập (TC-001→004) |
| `integration/test_gioi_han_dang_nhap.py` | R-1 qua HTTP (6 ca): chuỗi đăng nhập sai bị 429 kèm `Retry-After`, người dùng/IP khác không bị ảnh hưởng, đăng nhập đúng xóa bộ đếm |
| `integration/test_chan_cheo_nguon.py` | R-2 qua HTTP (6 ca, gồm `APP_ORIGIN`): POST đổi trạng thái kèm `Origin` lạ bị 403 và **không được thực thi**, cùng host vẫn chạy, không header vẫn chạy, đăng nhập từ trang lạ cũng bị chặn, GET không bị chặn
| `integration/test_header_bao_mat.py` | R-4 (5 ca): `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` có trên trang thường, `/static`, trang 404, chuyển hướng và cả phản hồi 403 của middleware khác |
| `integration/test_thu_hoi_phien.py` | R-3 (6 ca): cookie cũ sau đăng xuất / đổi mật khẩu / đặt lại mật khẩu / khóa rồi mở khóa đều bị 303; máy vừa đổi mật khẩu không bị đá; cookie cũ chưa có `sv` vẫn hợp lệ |
| `integration/test_khach_auth.py` | Cổng khách qua HTTP (28 ca, `FakeMailer`): luồng đăng ký trọn vẹn, cùng phản hồi cho email có/không, liên kết theo `APP_ORIGIN` bỏ qua `Host` giả, `GET` không đốt token, 429 theo IP, cookie khách không mở trang nhân viên và ngược lại, đăng nhập bên này xóa phiên bên kia, đăng xuất/đổi/đặt lại mật khẩu giết cookie cũ (TC-150 → TC-153) |
| `integration/test_khach_ai.py` | Khách hỏi đáp AI qua HTTP (18 ca, `FakeProvider`): luồng đủ + khuyến cáo, F5 không gọi AI thêm, số lượt giảm đúng, **prompt và trang không có tên khách / chủ / thú cưng**, xin thuốc bị chặn trước khi gọi, lỡ trả liều thì bị thay, AI lỗi 400 giữ câu và không trừ lượt, hết hạn mức 429 mà provider không bị gọi, log của khách khác = id không tồn tại (cùng 404 từng chữ), log của nhân viên, chưa đăng nhập / cookie nhân viên (TC-181, TC-182) |
| `integration/test_khung_trong.py` | Trang giờ trống qua HTTP (9 ca): nhóm theo nhân viên với link điền sẵn, **không rò tên thú cưng / tên / SĐT chủ khác** (lịch người khác chỉ làm giờ biến mất), bấm giờ → form điền sẵn → gửi tạo `pending` và giờ đó biến mất, thoát ký tự đặc biệt ở ô điền sẵn, thú cưng người khác = id không tồn tại (cùng 404 từng chữ), khách chưa nối, chưa đăng nhập, ngày sai 400, ngày đã qua |
| `integration/test_lich_cho_duyet.py` | Xin lịch và duyệt qua HTTP (14 ca, ba `TestClient`: khách, lễ tân, nhân viên): luồng xin → duyệt → thành lịch đã đặt, từ chối hiện lý do cho khách và trả lại khung giờ, thiếu lý do 400, duyệt lịch quá hạn 400 không 500, thú cưng người khác = id không tồn tại (cùng 404 từng chữ), khách chưa nối không xin được, `caretaker` 403, vượt trần 3 lịch chờ, **lý do hủy nội bộ của lịch nhân viên đặt không lộ cho khách** |
| `integration/test_lien_ket_khach.py` | Nối khách qua HTTP (16 ca, hai `TestClient`: khách và lễ tân): luồng gửi → duyệt → gỡ, từ chối hiện lý do, duyệt bằng mã hồ sơ khác số khách nhập, cùng phản hồi dù số có phải chủ nuôi hay không, `caretaker` 403 ở cả bốn route, khách và người chưa đăng nhập không mở được màn hình duyệt, menu chỉ hiện cho quản lý/lễ tân (TC-158 → TC-160) |
| `integration/test_khach_du_lieu.py` | Cổng khách qua HTTP (24 ca) và **quét IDOR**: khách thấy đúng dữ liệu của mình, id người khác và id không tồn tại cùng một phản hồi 404 giống từng chữ, khách chưa nối nhận danh sách rỗng và 404 ở cả id đúng, không trang nào lộ ghi chú / lý do hủy / hồ sơ chăm sóc / tên nhân viên / địa chỉ, gỡ liên kết có hiệu lực ngay, chưa đăng nhập và nhân viên bị đưa về `/khach/dang-nhap`, mọi route khách có `{..._id}` đều nằm trong phép thử (TC-162 → TC-164) |
| `integration/test_users.py` | Phân quyền và quản lý tài khoản (TC-007, 008, 010→012) |
| `integration/test_owners.py` | Chủ nuôi, thú cưng, tra cứu qua HTTP (TC-013→023) |
| `integration/test_services.py` | Dịch vụ, bảng giá, gói qua HTTP (TC-024→031) |
| `integration/test_care_records.py` | Ghi hồ sơ và trang thú cưng qua HTTP (TC-053, TC-054, TC-057, TC-058) |
| `integration/test_vaccinations.py` | Ghi mũi tiêm, danh sách đến hạn, link menu, khuyến cáo bác sĩ (TC-059, TC-063, TC-064, TC-020) |
| `integration/test_invoices.py` | Hóa đơn qua HTTP: nút trên lưới lịch, thu tiền, hủy, phân quyền (TC-065, TC-068→070, TC-072) |
| `integration/test_ai.py` | Ba tính năng AI qua HTTP: phân quyền, Post/Redirect/Get, AI lỗi không vỡ trang, `ai_logs` sạch dữ liệu liên hệ (TC-084→100) |
| `integration/test_stats.py` | Trang thống kê qua HTTP: TC-006 và lễ tân → 403, kỳ mặc định, kỳ trống, ngày ngược, ngày sai định dạng |
| `integration/test_seed.py` | Chạy `python -m app.seed` trong tiến trình riêng trên CSDL tạm; ngày lập hóa đơn = ngày buổi chăm sóc, ngày thu = ngày lập; dòng tổng kết đếm đúng số lịch hẹn (R-5) | · `SEED_MAT_KHAU` đặt thì đăng nhập bằng nó và seed in nó; trống thì `matkhau123` (2 ca)
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
