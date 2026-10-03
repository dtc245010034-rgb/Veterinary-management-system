# Kế hoạch — Kiểm thử P9, CSDL demo, báo cáo tiến độ, hướng dẫn sử dụng

**Trạng thái: XONG phần việc của agent (03/10/2026); B-1, B-2 chờ người dùng quyết có sửa không.** Yêu cầu của người dùng 03/10: quyền đọc
log AI của khách không cần sửa; test hết chức năng và thao tác P9 bằng Chrome, rà bug tồn đọng; chuẩn bị CSDL demo đầy đủ bằng
file `.py` riêng, không ảnh hưởng CSDL chính; commit và đẩy lên nhánh `demo-cac-chuc-nang` (người dùng tự merge vào `main`);
viết báo cáo tiến độ (còn sót gì, bug còn lại) và một file hướng dẫn sử dụng cho người không biết IT.

Quy tắc: kiểm thử chỉ chạy trên CSDL demo (không đụng `petcare.db`); lỗi tìm được chỉ ghi lại và xếp mức độ, **hỏi rồi mới sửa**;
số liệu đếm lại từ hệ thống tập tin, không chép từ tài liệu cũ.

## Các bước

- [x] 1. Ghi quyết định "chấp nhận có chủ ý" quyền đọc log AI của khách vào `ai-safety.md` mục 10.
- [x] 2. `tools/tao_du_lieu_demo.py`: dựng `demo.db` cố định theo hạt giống, từ chối ghi đè `petcare.db`.
      → verify: lịch hoàn thành không có hồ sơ = 0; chạy lại ra đúng dữ liệu cũ.
- [x] 3. Kiểm thử Chrome mọi chức năng P9 (cổng khách, nhân viên, phân quyền, AI) trên `demo.db`.
      → verify: `petcare.db` không đổi mã băm; phát hiện B-1 (thấp), B-2 (trung bình), chưa sửa.
- [x] 4. `HUONG-DAN-SU-DUNG.md`: hướng dẫn từng bước, phân quyền, hạn chế, bằng tiếng Việt đời thường.
      → verify: mọi tên nút, đường dẫn, mật khẩu đối chiếu với code và dữ liệu demo.
- [x] 5. `docs/bao-cao-tien-do.md`: tiến độ P0 → P9, số liệu đếm lại, bug còn lại, việc còn sót.
- [x] 6. Cập nhật README (lịch chờ quá hạn, B-2, khối dựng CSDL demo), báo cáo P9, nhật ký, `codebase-map.md`.
      → verify: `tests/unit/test_architecture.py` xanh; `pytest` toàn bộ xanh.
- [x] 7. Commit lên nhánh `demo-cac-chuc-nang`, đẩy lên `origin`, **không merge** vào `main`.
