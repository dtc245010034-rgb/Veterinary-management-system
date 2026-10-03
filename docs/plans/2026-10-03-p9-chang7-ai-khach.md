# Kế hoạch P9 chặng 7 — AI cho khách (hỏi đáp US-26, hạn mức theo tài khoản)

**Trạng thái: ĐANG LÀM (03/10/2026).** Thuộc [kế hoạch P9](2026-09-25-p9-cong-khach-hang.md) ô 7.1 và 7.2; người dùng yêu cầu "tiếp tục P9" ngày 03/10.

## Phản biện trước khi làm (đã kiểm từ code)

| # | Giả định trong kế hoạch P9 | Sự thật trong code | Quyết định |
|---|---|---|---|
| 1 | Mục 5.3: "`ai_logs` đã có `user_id`, không cần bảng mới, không cần migration" | `ai_logs.user_id` là FK tới `users` và **NOT NULL**; khách nằm ở bảng `customers`, không có dòng ở `users` | Phải thêm `ai_logs.customer_id` **và** bỏ NOT NULL của `user_id`. SQLite không bỏ NOT NULL bằng `ALTER` → dựng lại bảng `ai_logs` (cùng cơ chế đã dùng cho `appointments` ở chặng 5) |
| 2 | "Khách dùng AI" | Đề bài và `ai-safety.md` chỉ cho khách US-26 (hỏi đáp). Tóm tắt hồ sơ và nhắc lịch đọc dữ liệu thú cưng/chủ nuôi | Khách **chỉ có hỏi đáp**. Câu hỏi là thứ duy nhất đi sang AI: không kèm tên khách, email, thú cưng, hồ sơ |
| 3 | "Hạn mức đếm từ `ai_logs`" | Câu bị guardrail chặn (xin thuốc) ghi log nhưng không tốn lượt Gemini; lỗi AI cũng ghi log | Đếm các dòng của khách trong ngày có `is_error = 0` (kể cả câu bị từ chối thuốc): vừa chặn bơm log, vừa không phạt khách khi cửa hàng hết quota Gemini |
| 4 | Kết quả AI đọc qua `/ai/ket-qua/{id}` | Route đó dùng cookie nhân viên và `base.html` (menu nhân viên) | Cổng khách có trang kết quả riêng, **chỉ chủ của dòng log mới đọc được**; id của người khác = id không tồn tại = cùng một 404 |

Giới hạn đã biết, chấp nhận: kiểm hạn mức rồi mới gọi API không khoá giao dịch, hai yêu cầu đồng thời của cùng một khách có thể vượt hạn mức 1 lượt (quy mô cửa hàng).

## Các bước

- [x] 7.0 Kế hoạch này.
- [x] 7.1 Model + nâng cấp schema: `AiLog.customer_id`, `user_id` nullable, CHECK đúng một trong hai; `dung_lai_bang_nhat_ky_ai` chạy lúc khởi động.
      → verify: CSDL cũ (user_id NOT NULL, chưa có customer_id) nâng cấp xong giữ nguyên dòng cũ, chèn được dòng của khách; chạy lại không đổi gì.
- [x] 7.2 Service `hoi_dap_khach` + `HAN_MUC_KHACH_MOI_NGAY` (cấu hình `AI_KHACH_TOI_DA_MOI_NGAY`, mặc định 10) + `lay_log_khach`.
      → verify: chạm hạn mức **không gọi API** và **không ghi dòng log mới**; câu xin thuốc bị chặn trước khi gọi; phản hồi có liều bị thay; prompt gửi đi chỉ là câu hỏi đã lọc liên hệ; khách A đầy hạn mức không ảnh hưởng khách B; sang ngày mới được hỏi lại.
- [x] 7.3 Router `khach_ai.py` + template `khach_hoi_dap.html` + link menu: GET/POST `/khach/hoi-dap`, GET `/khach/hoi-dap/{log_id}`; Post/Redirect/Get như màn nhân viên; câu khuyến cáo cố định phía trên, hiện cả khi AI lỗi.
      → verify: HTTP đủ luồng; log của người khác = 404 y hệt id không tồn tại; chưa đăng nhập về trang đăng nhập; cookie nhân viên không dùng được; 429 khi hết hạn mức và provider không bị gọi.
- [x] 7.4 Phép canh: router khách AI không chạm `app.models`/`db.*`; `.env.example` có biến mới; `test-cases.md`, `ai-safety.md` (mục khách), `erd.md`, `architecture.md`, `codebase-map.md`.
- [x] 7.5 Đột biến mọi hành vi mới (xác nhận đột biến đã vào file) + chạy toàn bộ unit/integration + kiểm thử bằng Chrome trên bản sao CSDL.
      → kết quả 03/10/2026: đột biến 11/11 bị bắt; `pytest tests/unit tests/integration` = **1380 passed, 1 skipped**; Chrome trên bản sao `petcare.db` đã nâng cấp (xem mục dưới).

## Kết quả kiểm thử Chrome (bản sao CSDL, `AI_PROVIDER=fake`)

- Bản sao CSDL cũ (trước P9) tự nâng cấp `ai_logs` lúc khởi động: `user_id` nullable, có `customer_id`.
- Khách gõ câu hỏi bằng giao diện → 303 → trang kết quả có câu hỏi, câu trả lời, khuyến cáo; F5 ba lần không tốn lượt (9/10 giữ nguyên).
- Câu xin thuốc: trang kết quả có lời từ chối, không có liều; **vẫn tốn 1 lượt** (đã ghi ở mục 3 trên).
- Câu rỗng → 400. Hết lượt: 8 câu còn lại → 200, câu kế → 429, hiển thị 0/10 và nút "Hỏi AI" bị vô hiệu.
- Khách B còn 10/10 khi khách A hết lượt; log của A với B = 404 y hệt id không tồn tại (cùng nội dung trang, không lộ câu hỏi).
- Luồng liền mạch: liên kết hồ sơ (số điện thoại) → lễ tân duyệt → khách thấy thú cưng/lịch hẹn của chủ nuôi đã nối (thú cưng người khác = 404) → giờ trống → form xin đặt lịch điền sẵn → "Chờ duyệt" → lễ tân duyệt ở `/lich-cho-duyet`.
- Quét GET bốn vai trò nhân viên (quanly 30 trang, letan 28, chamsoc1/2 mỗi người 15): 0 lỗi 5xx, CSDL không đổi.
- Phát hiện: **nhân viên (mọi vai trò) đọc được câu hỏi/đáp của khách qua `/ai/ket-qua/{id}`** (`nv.lay_log` không lọc chủ). Chưa sửa — chờ người dùng quyết định (xem `ai-safety.md` mục 10).
- Một cookie chỉ mang một danh tính: đăng nhập nhân viên đẩy phiên khách ra và ngược lại (chủ ý, `app/auth.py`).

Người dùng tự tick ô 7.x của kế hoạch tổng ([kế hoạch P9](2026-09-25-p9-cong-khach-hang.md)).
