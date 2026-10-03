# Kế hoạch P9 chặng 8 — Đặc tả, tài liệu, đóng phase

**Trạng thái: XONG phần việc của agent (03/10/2026); ô 8.1 → 8.4 của kế hoạch tổng và khối smoke P9 chờ người dùng tick.** Thuộc [kế hoạch P9](2026-09-25-p9-cong-khach-hang.md) ô 8.1 → 8.4; người dùng yêu cầu 03/10:
"cập nhật lại toàn bộ tài liệu từ readme cho đến những thay đổi … readme.md làm lại sao cho có đầy đủ hướng dẫn chi tiết cách sử dụng project này".

Quy tắc: số liệu trong tài liệu **đếm lại từ hệ thống tập tin và từ lượt chạy test**, không chép từ tài liệu cũ
(`CLAUDE.md` mục 10). Người dùng tự tick các ô 8.x của kế hoạch tổng và khối smoke P9; agent không tick.

## Các bước

- [x] 8.0 Kế hoạch này.
- [x] 8.1 Nhóm J — `user-stories/j-cong-khach-hang.md` (US-29 → US-36: 27 chấp nhận + 40 biên), `user-stories/README.md` lên mười nhóm, 36 US, 185 tiêu chí.
      → verify: `test_architecture.py` (phép canh ba mục, ≥ 28 US, không trùng mã) xanh.
- [x] 8.2 `test-cases.md`: cột US của TC-149 → TC-182 trỏ đúng US-29 → US-36; bảng đối chiếu cộng đủ **182** dòng TC (thêm nhóm P, Q còn thiếu), kết luận 36/36 US.
      → verify: đếm `^| TC-` = 182; tổng cột "Số TC" của bảng = 182; phép canh mã US phải tồn tại trong đặc tả xanh.
- [x] 8.2b `erd.md` (17 bảng), `architecture.md` (17 bảng, sửa dòng `lien_ket_khach` lệch lề), `ai-safety.md` (mục 10: nhân viên đọc được log khách), `codebase-map.md` (nhóm J, số TC, số bảng).
      → verify: đếm `__tablename__` = 17; 84 phép canh kiến trúc xanh.
- [x] 8.3 `roadmap.md`: thêm **P9** vào bảng tổng quan, bảng tiến độ và mục chi tiết kèm DoD; "Chín phase" → "Mười phase".
- [x] 8.4 Báo cáo `testing/reports/2026-10-03-P9.md` (output pytest thật) + khối smoke P9 trong `smoke-checklist.md` **để trống cho người dùng tick**.
- [x] 8.5 Viết lại `README.md`: hướng dẫn chi tiết cài đặt, chạy, tài khoản mẫu, từng màn hình nhân viên và cổng khách, AI, email, biến môi trường, test, cấu trúc, lỗi thường gặp.
      → verify: mọi lệnh và URL trong README đối chiếu với code (`run.py`, `app/main.py`, `app/routers/*`, `.env.example`); phép canh `test_architecture.py` xanh.
- [x] 8.6 Nhật ký phiên + `codebase-map.md` (số kế hoạch, báo cáo) + chạy toàn bộ unit/integration, ghi kết quả thật.

## Phát hiện để chờ người dùng quyết (không sửa)

- Nhân viên (mọi vai trò) đọc được câu hỏi/đáp của khách qua `/ai/ket-qua/{id}` vì `nv.lay_log` không lọc chủ — xem `ai-safety.md` mục 10.
