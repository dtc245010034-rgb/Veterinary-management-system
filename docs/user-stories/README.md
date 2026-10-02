# Đặc tả User Story

Nguồn: [`đề-bài.md`](../../đề-bài.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`testing/test-cases.md`](../testing/test-cases.md)

Đặc tả được tách thành **chín file theo chín nhóm A–I** (trước 02/10 nằm chung một file). Mỗi story
có mã `US-xx` và đúng ba mục:

1. **Mục tiêu** — "Là <vai trò>, tôi muốn… để…".
2. **Tiêu chí chấp nhận** — các dòng Given/When/Then mô tả hành vi đúng, đường đi chính.
3. **Điều kiện biên** — các dòng Given/When/Then về dữ liệu sai, giá trị sát ngưỡng, trạng thái rỗng
   và những ca dễ bị quên. Story nào chưa có biên riêng thì ghi rõ một dòng nói vậy, không bỏ trống mục.

Mỗi dòng Given/When/Then ở **cả hai mục tiêu chí** tương ứng một test case trong
[`testing/test-cases.md`](../testing/test-cases.md). Cấu trúc ba mục được canh bởi
`test_moi_user_story_co_du_ba_muc_theo_dung_thu_tu` trong `tests/unit/test_architecture.py`.

**Ba vai trò:** `manager` (quản lý) · `receptionist` (lễ tân) · `caretaker` (nhân viên chăm sóc)

---

## Mục lục

| Nhóm | File | Story | Tiêu chí chấp nhận | Điều kiện biên |
|---|---|---|---|---|
| A. Đăng nhập và phân quyền | [`a-dang-nhap-phan-quyen.md`](a-dang-nhap-phan-quyen.md) | US-01 → US-03 (3) | 8 | 7 |
| B. Chủ nuôi và thú cưng | [`b-chu-nuoi-thu-cung.md`](b-chu-nuoi-thu-cung.md) | US-04 → US-06 (3) | 7 | 12 |
| C. Dịch vụ, bảng giá, gói dịch vụ | [`c-dich-vu-bang-gia.md`](c-dich-vu-bang-gia.md) | US-07 → US-09 (3) | 6 | 5 |
| D. Lịch hẹn — trọng tâm nghiệp vụ | [`d-lich-hen.md`](d-lich-hen.md) | US-10 → US-14 (5) | 9 | 14 |
| E. Hồ sơ chăm sóc | [`e-ho-so-cham-soc.md`](e-ho-so-cham-soc.md) | US-15 → US-16 (2) | 3 | 3 |
| F. Tiêm phòng (mức thông tin) | [`f-tiem-phong.md`](f-tiem-phong.md) | US-17 → US-18 (2) | 3 | 4 |
| G. Hóa đơn và thanh toán | [`g-hoa-don-thanh-toan.md`](g-hoa-don-thanh-toan.md) | US-19 → US-21 (3) | 6 | 6 |
| H. Thống kê | [`h-thong-ke.md`](h-thong-ke.md) | US-22 → US-23 (2) | 3 | 3 |
| I. Chức năng AI | [`i-chuc-nang-ai.md`](i-chuc-nang-ai.md) | US-24 → US-28 (5) | 15 | 4 |
| **Tổng** | 9 file | **28** | **60** | **58** |

Tổng cộng **118** tiêu chí Given/When/Then — đếm bằng cách đếm dòng bắt đầu `- Given` trong chín file nhóm.

---

## Đối chiếu với yêu cầu đề bài

### Mục 3.1 — Chức năng quản lý

| # | Yêu cầu đề bài | User story |
|---|---|---|
| 1 | Đăng nhập và phân quyền quản lý, lễ tân, nhân viên chăm sóc | US-01, US-02, US-03 |
| 2 | Quản lý chủ nuôi và thú cưng | US-04, US-05, US-06 |
| 3 | Quản lý dịch vụ chăm sóc, bảng giá, gói dịch vụ | US-07, US-08, US-09 |
| 4 | Đặt lịch chăm sóc, đổi lịch, hủy lịch | US-10, US-11, US-12, US-13, US-14 |
| 5 | Ghi nhận hồ sơ chăm sóc và ghi chú tình trạng | US-15, US-16 |
| 6 | Quản lý lịch nhắc tiêm/phòng bệnh ở mức thông tin | US-17, US-18 |
| 7 | Lập hóa đơn và theo dõi thanh toán | US-19, US-20, US-21 |
| 8 | Thống kê lượt dịch vụ, doanh thu, khách quay lại | US-22, US-23 |

### Mục 3.2 — Chức năng AI

| # | Yêu cầu đề bài | User story |
|---|---|---|
| 1 | AI sinh tin nhắn nhắc lịch chăm sóc hoặc lịch tiêm nhắc | US-24 |
| 2 | AI tóm tắt hồ sơ chăm sóc của thú cưng | US-25 |
| 3 | AI trả lời câu hỏi chăm sóc thông thường với cảnh báo hỏi bác sĩ thú y | US-26, US-27 |

### Mục 4 — Yêu cầu kỹ thuật

| Yêu cầu đề bài | Nơi đáp ứng |
|---|---|
| Có cảnh báo AI không thay thế bác sĩ thú y | US-26, US-27, [`ai-safety.md`](../ai-safety.md) |
| Có test cho lịch hẹn, hóa đơn, hồ sơ và AI | US-10→US-13, US-19→US-21, US-15, US-24→US-28; ma trận [`testing/test-cases.md`](../testing/test-cases.md) |
| Review dữ liệu cá nhân (mục 6, cuối kỳ) | US-28 |

**Kết luận: 8/8 chức năng quản lý và 3/3 chức năng AI của đề bài đều có ít nhất một user story.**
