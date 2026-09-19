# Kế hoạch đã duyệt

Mỗi kế hoạch được người dùng duyệt phải được **chép ngay vào thư mục này** trước khi bắt tay làm.

## Vì sao

Kế hoạch nằm ngoài repo (trong thư mục cấu hình cá nhân của Claude Code) thì phiên chat sau không đọc
được, máy khác không có, và báo cáo cuối kỳ không truy vết được đã quyết định gì ở thời điểm nào.
Chép vào đây thì kế hoạch trở thành một phần của lịch sử dự án, ngang hàng với code.

## Quy ước

- Tên file: `YYYY-MM-DD-<slug-khong-dau>.md`, ví dụ `2026-09-04-kt1-bo-context-va-dac-ta.md`
- Mỗi bước thực hiện là một dòng checklist `- [ ]`, **tick `[x]` ngay khi làm xong bước đó**, không
  để dồn tới cuối
- Kế hoạch bị thay đổi giữa chừng: ghi thêm mục "Điều chỉnh so với kế hoạch gốc" ở cuối file, nêu rõ
  đổi gì và vì sao. **Không sửa đè** phần kế hoạch gốc — chênh lệch giữa dự định và thực tế là thông
  tin có giá trị cho báo cáo
- Kế hoạch bị hủy: giữ file, thêm dòng `> **Đã hủy:** <lý do>` ngay dưới tiêu đề

## Liên hệ với các tài liệu khác

| Tài liệu | Quan hệ |
|---|---|
| [`../roadmap.md`](../roadmap.md) | Chia dự án thành phase P0–P8. Mỗi phase sinh ra một kế hoạch ở thư mục này |
| [`../sessions/`](../sessions/) | Log phiên ghi việc **đã làm**; kế hoạch ghi việc **sẽ làm** |
| [`../testing/test-cases.md`](../testing/test-cases.md) | Kế hoạch mỗi phase phải nêu rõ những TC nào sẽ chuyển sang ✅ |

## Danh sách

| Ngày | Kế hoạch | Phase | Trạng thái |
|---|---|---|---|
| 2026-09-04 | [KT1 — Dựng bộ context, đặc tả và chiến lược kiểm thử](2026-09-04-kt1-bo-context-va-dac-ta.md) | P0 | Hoàn thành |
| 2026-09-04 | [Nền tảng, đăng nhập và phân quyền](2026-09-04-p1-nen-tang-va-xac-thuc.md) | P1 | Hoàn thành |
| 2026-09-04 | [Chủ nuôi và thú cưng](2026-09-04-p2a-chu-nuoi-va-thu-cung.md) | P2a | Hoàn thành |
| 2026-09-05 | [Dịch vụ, bảng giá và gói](2026-09-05-p2b-dich-vu-va-goi.md) | P2b | Hoàn thành |
| 2026-09-05 | [Lịch hẹn và chống trùng lịch](2026-09-05-p3-lich-hen.md) | P3 | Hoàn thành |
| 2026-09-05 | [Hồ sơ chăm sóc và tiêm phòng](2026-09-05-p4-ho-so-va-tiem-phong.md) | P4 | Hoàn thành |
| 2026-09-05 | [Kịch bản e2e xuyên suốt](2026-09-05-e2e-xuyen-suot.md) | P4–P7 | Xong — bước 10 nối ngày 18/09, TC-101 đủ 11/11 |
| 2026-09-05 | [Trả nợ kiến trúc và bao phủ](2026-09-05-tra-no-kien-truc-va-bao-phu.md) | — | Hoàn thành |
| 2026-09-06 | [Hóa đơn và thanh toán](2026-09-06-p5-hoa-don-va-thanh-toan.md) | P5 | Hoàn thành |
| 2026-09-11 | [Thống kê](2026-09-11-p6-thong-ke.md) | P6 | Hoàn thành |
| 2026-09-13 | [Dọn việc tồn của P6](2026-09-13-viec-ton-p6.md) | P6 | Hoàn thành |
| 2026-09-18 | [Tích hợp AI, xoay ca model Gemini và ước tính quota](2026-09-18-p7-tich-hop-ai.md) | P7 | Chặng 0→3 xong 19/09; chờ người dùng tick smoke |
| 2026-09-19 | [Rà soát toàn hệ thống P1 → P7](2026-09-19-ra-soat-P1-P7.md) | P7 | Rà xong 19/09: 3 cao · 8 trung bình · 7 thấp; 3 lỗi cao đã sửa, còn lại chờ người dùng chọn |
| 2026-09-19 | [Sửa ba lỗi cao sau rà soát](2026-09-19-sua-loi-cao-ra-soat.md) | P7 | Hoàn thành |
| 2026-09-19 | [Chế độ AI giả lập: nhãn đúng, không đếm quota](2026-09-19-che-do-ai-gia-lap.md) | P7 | Hoàn thành |

> Bảng này từng dừng ở P3 trong khi thư mục đã có thêm bảy kế hoạch — bổ sung ngày 18/09.
