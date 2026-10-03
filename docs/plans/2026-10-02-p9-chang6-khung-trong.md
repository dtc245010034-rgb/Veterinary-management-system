# Kế hoạch P9 chặng 6 — Bảng khung giờ trống theo nhân viên

Thuộc [kế hoạch tổng P9](2026-09-25-p9-cong-khach-hang.md), chặng 6 (ô 6.1–6.3). Người dùng đã duyệt cả P9 và chốt
"hiện khung trống theo từng nhân viên, có tên nhân viên, không có dữ liệu của khách khác" (mục 1.4 kế hoạch tổng).

## Thiết kế

- `scheduling.khung_gio_trong` thêm tham số `toi_da` (mặc định `SO_GOI_Y`, nên chỗ gọi cũ không đổi); `None` = dò hết ngày.
- `khach_du_lieu.khung_trong_cua_khach(db, khach, thu_cung_id, dich_vu_id, ngay)` trả danh sách (nhân viên, các giờ trống),
  mỗi nhân viên một nhóm. Thú cưng đi qua `yeu_cau_so_huu` (của người khác = id không tồn tại = cùng 404). Khung trống tính
  theo cả nhân viên lẫn thú cưng đó, và lịch `pending` còn hạn đang giữ chỗ nên không hiện là trống.
- Route `GET /khach/khung-trong` (thú cưng, dịch vụ, ngày). Mỗi giờ trống là link sang `GET /khach/dat-lich?...` điền sẵn
  form (ô 6.3). Form vẫn gửi qua `POST /khach/dat-lich`, nên mọi phép kiểm lúc xin lịch giữ nguyên: khung trống chỉ là
  gợi ý, người khác có thể giành chỗ trước khi khách bấm gửi.
- Không hiện gì ngoài giờ và tên nhân viên: không tên thú cưng/chủ nuôi khác, không ghi chú, không trạng thái.

## Checklist

- [x] 6.0 Viết test trước, xác nhận đỏ (service, tích hợp, phép canh).
- [x] 6.1 `toi_da` + `khung_trong_cua_khach` + route + template `khach_khung_trong.html`; xác nhận các test xanh.
- [x] 6.2 Phép canh: template `khach_*.html` không tham chiếu `owner.`/`.owner`/`/owners` trong biểu thức; đột biến thêm
      `{{ ...owner.full_name }}` vào template mới thì phép canh đỏ.
- [x] 6.3 `GET /khach/dat-lich` nhận tham số truy vấn để điền sẵn; link ở trang khung trống trỏ tới đó.
- [x] 6.4 Đột biến từng quy tắc, tài liệu (codebase-map, test-cases, architecture), log phiên, chạy toàn bộ test, kiểm thử
      tay bằng Chrome.
