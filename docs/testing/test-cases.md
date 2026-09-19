# Ma trận truy vết test case

Nguồn: [`../user-stories.md`](../user-stories.md) · Guardrail: [`../ai-safety.md`](../ai-safety.md) · Chiến lược: [`test-strategy.md`](test-strategy.md)

**Cách dùng file này.** Mỗi tiêu chí chấp nhận Given/When/Then trong `user-stories.md` sinh ra một
test case ở đây. Khi cài đặt một phase, điền cột **File test** và đổi **Trạng thái** thành ✅. Cuối
kỳ, file này là bằng chứng mọi yêu cầu của đề bài đều có test — đặc biệt yêu cầu ở mục 4:
*"có test cho lịch hẹn, hóa đơn, hồ sơ và AI"*.

**Trạng thái:** ⬜ chưa làm · 🟡 đang làm · ✅ xanh · ❌ đỏ (ghi lý do ở log phiên) · ➖ ngoài phạm
vi (chốt với người dùng, kèm lý do ngay trong dòng — **không** được dùng để cất một ca khó đi)

**Mức test:** `U` unit · `I` integration · `E` e2e — theo định nghĩa ở [`test-strategy.md`](test-strategy.md)

---

## A. Đăng nhập và phân quyền — phase P1

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-001 | US-01 | Đăng nhập đúng mật khẩu → vào được hệ thống | I | `tests/integration/test_auth.py` | ✅ |
| TC-002 | US-01 | Sai mật khẩu → báo lỗi chung, không lộ tài khoản có tồn tại | I | `tests/integration/test_auth.py` | ✅ |
| TC-003 | US-01 | Tài khoản `is_active = false` → bị từ chối | I | `tests/integration/test_auth.py` | ✅ |
| TC-004 | US-01 | Chưa đăng nhập mở trang nội bộ → chuyển về trang đăng nhập | I | `tests/integration/test_auth.py` | ✅ |
| TC-005 | US-01 | Mật khẩu lưu dạng băm, không lưu bản gốc | U | `tests/unit/test_security.py` | ✅ |
| TC-006 | US-02 | `caretaker` mở trang thống kê → 403 | I | `test_stats.py::test_caretaker_mo_trang_thong_ke_bi_chan_403`, `…_le_tan_mo_trang_thong_ke_bi_chan_403` — hoãn từ P1, đóng ở P6 | ✅ |
| TC-007 | US-02 | `receptionist` mở trang quản lý tài khoản → 403 | I | `tests/integration/test_users.py` | ✅ |
| TC-008 | US-02 | `manager` truy cập được mọi trang | I | `tests/integration/test_users.py` | ✅ |
| TC-009 | US-02 | `caretaker` xem lịch → chỉ thấy lịch của mình | I | `test_appointments.py::test_caretaker_go_thang_trang_lich_chung_van_chi_thay_lich_minh` | ✅ |
| TC-010 | US-03 | Tạo tài khoản mới → đăng nhập được ngay | I | `tests/integration/test_users.py`, `tests/unit/test_users_service.py` | ✅ |
| TC-011 | US-03 | Tên đăng nhập trùng → bị từ chối | I | `tests/integration/test_users.py`, `tests/unit/test_models_user.py`, `tests/unit/test_users_service.py::test_tao_tai_khoan_trung_username_bi_tu_choi` | ✅ |
| TC-012 | US-03 | Khóa tài khoản → không đăng nhập được, dữ liệu cũ còn nguyên | I | `tests/integration/test_users.py`, `tests/unit/test_users_service.py::test_quan_ly_khong_tu_khoa_chinh_minh` | ✅ |

## B. Chủ nuôi và thú cưng — phase P2

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-013 | US-04 | Thêm chủ nuôi hợp lệ → lưu và hiện trong danh sách | I | `tests/integration/test_owners.py` | ✅ |
| TC-014 | US-04 | Thiếu họ tên hoặc số điện thoại → bị từ chối | I | `tests/unit/test_owners_service.py`, `tests/integration/test_owners.py` | ✅ |
| TC-015 | US-04 | Số điện thoại trùng → cảnh báo khách cũ | I | `tests/unit/test_owners_service.py`, `test_owners.py::test_so_dien_thoai_trung_hien_canh_bao_ngay_sau_khi_them` — viết lại 2026-09-05: bản cũ gọi thẳng URL mà giao diện không sinh ra nên xanh dù chức năng không tới được | ✅ |
| TC-016 | US-04 | Xóa chủ nuôi còn thú cưng → bị chặn | U | `tests/unit/test_owners_service.py`, `tests/unit/test_models_owner_pet.py` | ✅ |
| TC-017 | US-05 | Thêm thú cưng gắn chủ nuôi → hiện trong danh sách của chủ | I | `tests/unit/test_owners_service.py`, `tests/integration/test_owners.py` | ✅ |
| TC-018 | US-05 | Ngày sinh ở tương lai → bị từ chối | U | `tests/unit/test_owners_service.py`, `tests/integration/test_owners.py` | ✅ |
| TC-019 | US-05 | Cân nặng âm hoặc bằng 0 → bị từ chối | U | `tests/unit/test_models_owner_pet.py`, `tests/unit/test_owners_service.py` | ✅ |
| TC-020 | US-05 | Trang chi tiết thú cưng hiện chủ nuôi, lịch sử, lịch tiêm | I | `tests/integration/test_owners.py`, `tests/integration/test_care_records.py`, `tests/integration/test_vaccinations.py` | ✅ |
| TC-021 | US-06 | Tìm theo số điện thoại → ra chủ nuôi kèm thú cưng | I | `tests/unit/test_owners_service.py`, `tests/integration/test_owners.py` | ✅ |
| TC-022 | US-06 | Tìm một phần tên, không phân biệt hoa thường và dấu | U | `tests/unit/test_text.py`, `tests/unit/test_owners_service.py`, `tests/integration/test_owners.py` | ✅ |
| TC-023 | US-06 | Không khớp gì → trạng thái rỗng, không lỗi | I | `tests/unit/test_owners_service.py`, `tests/integration/test_owners.py` | ✅ |

## C. Dịch vụ, bảng giá, gói — phase P2

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-024 | US-07 | Thêm dịch vụ hợp lệ → xuất hiện khi đặt lịch | I | `tests/unit/test_catalog_service.py`, `tests/integration/test_services.py`, `tests/integration/test_appointments.py` | ✅ |
| TC-025 | US-07 | Giá âm hoặc thời lượng ≤ 0 → bị từ chối | U | `tests/unit/test_models_service.py`, `tests/unit/test_catalog_service.py`, `tests/integration/test_services.py` | ✅ |
| TC-026 | US-07 | Đổi giá dịch vụ → hóa đơn cũ giữ nguyên giá | U | `tests/unit/test_catalog_service.py`, `tests/integration/test_services.py`, `test_billing_service.py::test_doi_gia_dich_vu_khong_lam_doi_hoa_don_cu` | ✅ |
| TC-027 | US-08 | Tạo gói 3 dịch vụ → hiện khi lập hóa đơn | I | `tests/unit/test_models_service.py`, `tests/unit/test_catalog_service.py`, `tests/integration/test_services.py` — **nửa đầu (tạo gói, gói hiện trong danh sách đang bán) có test và xanh**. Nửa sau ➖: hệ thống **không có nghiệp vụ bán gói** — hóa đơn lập từ một lịch hẹn, mỗi lịch một dịch vụ. Người dùng chốt 11/09 là ngoài phạm vi; gói chỉ dùng để niêm yết giá so sánh. Muốn làm thật thì cần `invoice_items` nhiều dòng và luật trừ dần lượt trong gói — một phase riêng | ➖ |
| TC-028 | US-08 | Chi tiết gói hiện thành phần và tổng giá lẻ để so sánh | I | `tests/unit/test_models_service.py`, `tests/integration/test_services.py` | ✅ |
| TC-029 | US-08 | Gói không có thành phần → không lưu được | U | `tests/unit/test_catalog_service.py`, `tests/integration/test_services.py` | ✅ |
| TC-030 | US-09 | Ngưng bán dịch vụ → biến mất khỏi danh sách đặt lịch mới | I | `tests/unit/test_catalog_service.py`, `tests/unit/test_scheduling.py`, `tests/integration/test_appointments.py` | ✅ |
| TC-031 | US-09 | Hóa đơn cũ chứa dịch vụ đã ngưng bán vẫn hiển thị đủ | I | `test_invoices.py::test_hoa_don_cu_van_hien_du_khi_dich_vu_da_ngung_ban` | ✅ |

## D. Lịch hẹn — phase P3 · **đề bài yêu cầu đích danh có test**

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-032 | US-10 | Đặt lịch hợp lệ → `booked`, `end_at` tính từ thời lượng dịch vụ | U | `tests/unit/test_scheduling.py`, `tests/unit/test_models_appointment.py` | ✅ |
| TC-033 | US-10 | Giờ bắt đầu trong quá khứ → bị từ chối | U | `tests/unit/test_scheduling.py`, `tests/integration/test_appointments.py` | ✅ |
| TC-034 | US-10 | Nhân viên không phải `caretaker` → bị từ chối | U | `tests/unit/test_scheduling.py` | ✅ |
| TC-035 | US-10 | Lịch vừa tạo hiện đúng khung giờ, đúng nhân viên | I | `tests/integration/test_appointments.py` | ✅ |
| TC-036 | US-11 | **Trùng nhân viên, giao nhau một phần** (09:30 vs 09:00–10:00) → từ chối | U | `tests/unit/test_scheduling.py` | ✅ |
| TC-037 | US-11 | Từ chối kèm gợi ý khung trống trong ngày | U | `tests/unit/test_scheduling.py`, `tests/integration/test_appointments.py` | ✅ |
| TC-038 | US-11 | **Liền kề** (10:00–11:00 sau 09:00–10:00) → chấp nhận | U | `tests/unit/test_scheduling.py`, `tests/integration/test_appointments.py` | ✅ |
| TC-039 | US-11 | **Trùng thú cưng**, khác nhân viên → từ chối | U | `tests/unit/test_scheduling.py` | ✅ |
| TC-040 | US-11 | Lịch cũ đã `cancelled` → khung giờ đó đặt lại được | U | `tests/unit/test_scheduling.py` | ✅ |
| TC-041 | US-11 | **Bao trọn** (08:00–11:00 phủ 09:00–10:00) → từ chối | U | `tests/unit/test_scheduling.py` | ✅ |
| TC-042 | US-11 | **Nằm gọn bên trong** (09:15–09:45) → từ chối | U | `tests/unit/test_scheduling.py` | ✅ |
| TC-043 | US-11 | Chặn trùng lịch qua API, không chỉ ở tầng service | I | `tests/integration/test_appointments.py` | ✅ |
| TC-044 | US-12 | Đổi sang khung trống → cập nhật giờ, trạng thái `rescheduled` | U | `test_scheduling.py::test_doi_sang_khung_trong_cap_nhat_gio_va_chuyen_trang_thai` | ✅ |
| TC-045 | US-12 | Đổi sang khung đã bận → từ chối, **lịch giữ nguyên giờ cũ** | U | `test_scheduling.py::test_doi_sang_khung_ban_bi_tu_choi_va_giu_nguyen_gio_cu` | ✅ |
| TC-046 | US-12 | Đổi lịch **không tự so sánh với chính nó** | U | `test_scheduling.py::test_doi_lich_khong_tu_so_sanh_voi_chinh_no` | ✅ |
| TC-047 | US-12 | Đổi lịch đã `cancelled` hoặc `done` → từ chối | U | `test_scheduling.py::test_doi_lich_da_huy_bi_tu_choi`, `…_da_hoan_thanh_…` | ✅ |
| TC-048 | US-13 | Hủy kèm lý do → `cancelled`, lý do được lưu | U | `test_scheduling.py::test_huy_lich_kem_ly_do_doi_trang_thai_va_luu_ly_do`, `…_khung_gio_sau_khi_huy_dat_lai_duoc` | ✅ |
| TC-049 | US-13 | Hủy lịch đã `done` → từ chối | U | `test_scheduling.py::test_huy_lich_da_hoan_thanh_bi_tu_choi` | ✅ |
| TC-050 | US-14 | `caretaker` chỉ thấy lịch của mình, sắp theo giờ tăng dần | I | `test_appointments.py::test_caretaker_chi_thay_lich_cua_minh` | ✅ |
| TC-051 | US-14 | `receptionist` thấy toàn bộ, lọc được theo ngày và nhân viên | I | `test_appointments.py::test_le_tan_thay_lich_cua_moi_nhan_vien`, `…_loc_lich_theo_nhan_vien` | ✅ |
| TC-052 | US-14 | Ngày không có lịch → trạng thái rỗng | I | `test_appointments.py::test_ngay_khong_co_lich_hien_trang_thai_rong`, `…_caretaker_ngay_khong_co_lich…` | ✅ |

## E. Hồ sơ chăm sóc — phase P4 · **đề bài yêu cầu đích danh có test**

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-053 | US-15 | Ghi hồ sơ cho lịch của mình → lưu và lịch chuyển `done` | I | `test_care_records.py::test_nhan_vien_ghi_ho_so_cho_lich_cua_minh`, `test_care_records_service.py` | ✅ |
| TC-054 | US-15 | Ghi hồ sơ cho lịch của nhân viên khác → từ chối | I | `test_care_records.py::test_nhan_vien_khac_khong_ghi_duoc_ho_so` | ✅ |
| TC-055 | US-15 | Ghi hồ sơ lần hai cho cùng lịch → từ chối | U | `test_care_records_service.py::test_ghi_ho_so_lan_hai_cho_cung_lich_bi_tu_choi`, `test_models_care_record.py` | ✅ |
| TC-056 | US-15 | Bỏ trống ghi chú tình trạng → từ chối | U | `test_care_records_service.py::test_bo_trong_ghi_chu_tinh_trang_bi_tu_choi` | ✅ |
| TC-057 | US-16 | Lịch sử chăm sóc theo thời gian giảm dần, đủ thông tin mỗi dòng | I | `test_care_records_service.py::test_lich_su_sap_theo_thoi_gian_giam_dan`, `test_care_records.py::test_trang_thu_cung_hien_lich_su_cham_soc` | ✅ |
| TC-058 | US-16 | Thú cưng chưa dùng dịch vụ → trạng thái rỗng | I | `test_care_records.py::test_thu_cung_chua_dung_dich_vu_hien_trang_thai_rong` | ✅ |

## F. Tiêm phòng — phase P4

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-059 | US-17 | Ghi mũi tiêm hợp lệ → hiện trong hồ sơ tiêm | I | `tests/integration/test_vaccinations.py`, `tests/unit/test_vaccinations_service.py` | ✅ |
| TC-060 | US-17 | `next_due_at` sớm hơn `given_at` → từ chối | U | `tests/unit/test_vaccinations_service.py`, `tests/unit/test_models_vaccination.py` | ✅ |
| TC-061 | US-17 | Ngày tiêm ở tương lai → từ chối | U | `tests/unit/test_vaccinations_service.py`, `tests/integration/test_vaccinations.py` | ✅ |
| TC-062 | US-18 | Danh sách đến hạn: lấy hạn từ quá khứ tới hôm nay + 30 ngày, bỏ hạn xa hơn, sắp theo hạn tăng dần, **chỉ tính mũi mới nhất của mỗi loại vắc-xin** | U | `tests/unit/test_vaccinations_service.py` | ✅ |
| TC-063 | US-18 | Bản ghi quá hạn được đánh dấu rõ | I | `tests/integration/test_vaccinations.py`, `tests/unit/test_vaccinations_service.py` | ✅ |
| TC-064 | US-18 | Không ai đến hạn → trạng thái rỗng | I | `tests/integration/test_vaccinations.py`, `tests/unit/test_vaccinations_service.py` | ✅ |

## G. Hóa đơn và thanh toán — phase P5 · **đề bài yêu cầu đích danh có test**

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-065 | US-19 | Lập hóa đơn từ lịch `done` → `unpaid`, đơn giá chốt tại thời điểm lập | U | `tests/unit/test_billing_service.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-066 | US-19 | `total_amount` bằng `qty × unit_price` của dòng dịch vụ, và **không đọc lại `services.price` khi hiển thị** — đổi giá dịch vụ không làm đổi hóa đơn cũ | U | `tests/unit/test_billing_service.py` | ✅ |
| TC-067 | US-19 | Lập hóa đơn từ lịch chưa `done` → từ chối | U | `tests/unit/test_billing_service.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-068 | US-19 | Lập hóa đơn lần hai cho cùng lịch → từ chối | U | `tests/unit/test_billing_service.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-069 | US-20 | Trả đủ → trạng thái `paid` | U | `tests/unit/test_billing_service.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-070 | US-20 | Trả một phần → `partial`, còn nợ đúng số | U | `tests/unit/test_billing_service.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-071 | US-20 | Trả nốt phần còn lại → `paid`, nợ bằng 0 | U | `tests/unit/test_billing_service.py` | ✅ |
| TC-072 | US-20 | Trả vượt số phải trả → từ chối | U | `tests/unit/test_billing_service.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-073 | US-20 | Số tiền ≤ 0 → từ chối | U | `tests/unit/test_billing_service.py` | ✅ |
| TC-074 | US-21 | Hủy lịch đã có hóa đơn → chặn, nêu mã hóa đơn | U | `tests/unit/test_scheduling.py`, `tests/integration/test_invoices.py` | ✅ |
| TC-075 | US-21 | Hóa đơn đã `cancelled` → lớp chặn hóa đơn nhả ra, lịch bị chặn bởi chính trạng thái nó | U | `tests/unit/test_scheduling.py`, `tests/integration/test_invoices.py` | ✅ |

## H. Thống kê — phase P6

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-076 | US-22 | Tổng lượt, tổng doanh thu, bảng chia theo dịch vụ | U | `test_stats_service.py::test_thong_ke_tong_luot_doanh_thu_va_chia_theo_dich_vu`, `…_bang_theo_dich_vu_cong_lai_bang_dung_hai_con_so_tong`, `…_luot_gom_moi_lich_chua_huy_va_bo_lich_da_huy`, `…_dich_vu_da_ngung_ban_van_co_dong_trong_bang`, `test_stats.py` | ✅ |
| TC-077 | US-22 | Doanh thu chỉ tính **tiền đã thực nhận**; số chưa thu hiển thị riêng | U | `test_stats_service.py::test_doanh_thu_chi_tinh_tien_da_thu_so_chua_thu_hien_rieng`, `…_hoa_don_da_huy_khong_cong_vao_so_chua_thu`, `…_hoa_don_lap_ky_truoc_thu_ky_nay_vao_doanh_thu_ky_nay`, `…_ky_tinh_ca_hai_ngay_dau_va_cuoi` | ✅ |
| TC-078 | US-22 | Kỳ không có dữ liệu → số 0, không lỗi | U | `test_stats_service.py::test_ky_khong_co_du_lieu_ra_so_0_khong_loi`, `test_stats.py::test_ky_khong_co_du_lieu_hien_so_0_va_trang_thai_rong` | ✅ |
| TC-079 | US-22 | Ngày bắt đầu sau ngày kết thúc → từ chối | U | `test_stats_service.py::test_ngay_bat_dau_sau_ngay_ket_thuc_bi_tu_choi`, `…_ky_mot_ngay_hop_le`, `test_stats.py::test_ngay_bat_dau_sau_ngay_ket_thuc_bao_loi_va_giu_ngay_da_nhap` | ✅ |
| TC-080 | US-23 | Có khách dùng ≥ 2 lần → số lượng và tỉ lệ khách quay lại đúng. **Đếm theo số ngày đến**, không theo số lượt (người dùng chốt 11/09) | U | `test_stats_service.py::test_khach_quay_lai_tinh_theo_so_ngay_den_khong_theo_so_luot` | ✅ |
| TC-081 | US-23 | Mọi khách chỉ đến một lần → tỉ lệ bằng 0% | U | `test_stats_service.py::test_moi_khach_chi_den_mot_lan_ti_le_quay_lai_bang_0` | ✅ |

## I. Chức năng AI — phase P7 · **đề bài yêu cầu đích danh có test**

Toàn bộ chạy với `FakeProvider`. Mã `G-xx` tham chiếu bộ ca trong [`../ai-safety.md`](../ai-safety.md) mục 5.

### I.1 Nhắc lịch và tóm tắt

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-082 | US-24 | Tin nhắn nhắc lịch nêu đúng tên thú cưng, dịch vụ, ngày giờ | U | `tests/unit/test_ai_service.py`, `tests/unit/test_prompts.py` | ✅ |
| TC-083 | US-24 | Nhắc lịch tiêm nêu vắc-xin, hạn, kèm khuyến cáo bác sĩ thú y | U | `tests/unit/test_ai_service.py`, `tests/unit/test_prompts.py` | ✅ |
| TC-084 | US-24 | Lễ tân sửa nội dung trước khi gửi → bản sửa được dùng | I | `tests/integration/test_ai.py` | ✅ |
| TC-085 | US-24 | Lời gọi AI lỗi → thông báo rõ ràng, trang không vỡ, lịch còn nguyên (G-17) | I | `tests/integration/test_ai.py` | ✅ |
| TC-086 | US-25 | Tóm tắt hồ sơ nhiều bản ghi → có nội dung, nêu mốc chính | I | `tests/integration/test_ai.py`, `tests/e2e/test_full_flow.py` | ✅ |
| TC-087 | US-25 | Thú cưng chưa có hồ sơ → báo chưa đủ dữ liệu, **không gọi API** (G-20) | U | `tests/unit/test_ai_service.py` | ✅ |
| TC-088 | US-25 | Tóm tắt luôn kèm `DISCLAIMER` | U | `tests/unit/test_ai_service.py`, `tests/unit/test_prompts.py` | ✅ |

### I.2 Guardrail hỏi đáp

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-089 | US-26 | Câu hỏi trong phạm vi → có trả lời, kết thúc bằng `DISCLAIMER` (G-01→G-03) | I | `tests/integration/test_ai.py` | ✅ |
| TC-090 | US-26 | `DISCLAIMER` hiện trên giao diện **kể cả khi lời gọi AI lỗi** (G-19) | I | `tests/integration/test_ai.py` | ✅ |
| TC-091 | US-26 | Mỗi lượt hỏi đáp sinh một bản ghi `ai_logs` | I | `tests/integration/test_ai.py`, `tests/unit/test_ai_service.py` | ✅ |
| TC-092 | US-27 | Câu hỏi dấu hiệu bệnh lý → khuyên đi khám, không kết luận bệnh (G-04→G-07) | U | `tests/unit/test_ai_service.py` | ✅ |
| TC-093 | US-27 | Xin liều thuốc → không trả về số kèm `mg`/`ml`/`viên` (G-08→G-10) | U | `tests/unit/test_guardrail.py`, `tests/unit/test_ai_service.py` | ✅ |
| TC-094 | US-27 | Câu hỏi ngoài phạm vi → từ chối lịch sự, nêu rõ phạm vi (G-11, G-12) | U | `tests/unit/test_prompts.py` + chạy tay với Gemini thật: [`2026-09-19-P7-gemini-gemini-3.6-flash.md`](reports/2026-09-19-P7-gemini-gemini-3.6-flash.md) | ✅ code kiểm system prompt **có** luật này; lượt chạy thật 19/09 cho thấy `gemini-3.6-flash` từ chối đúng G-11, G-12 |
| TC-095 | US-27 | Câu lệnh ép bỏ qua hướng dẫn → guardrail không bị vô hiệu (G-13) | U | `tests/unit/test_ai_service.py`, `tests/unit/test_guardrail.py` | ✅ |
| TC-096 | US-27 | System prompt đúng loại được gắn cho từng `feature` | U | `tests/unit/test_prompts.py`, `tests/unit/test_ai_service.py` | ✅ |

### I.3 Dữ liệu cá nhân

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-097 | US-28 | Prompt nhắc lịch không chứa số điện thoại, email, địa chỉ (G-14) | U | `tests/unit/test_ai_service.py`, `tests/unit/test_guardrail.py` | ✅ |
| TC-098 | US-28 | Prompt tóm tắt không chứa dữ liệu liên hệ (G-15) | U | `tests/unit/test_ai_service.py` | ✅ |
| TC-099 | US-28 | `ai_logs.prompt` đã lưu cũng không chứa dữ liệu liên hệ (G-16) | I | `tests/integration/test_ai.py` | ✅ |
| TC-100 | US-28 | Lời gọi AI lỗi → `ai_logs.is_error = true` (G-18) | I | `tests/integration/test_ai.py`, `tests/unit/test_ai_service.py` | ✅ |

### I.4 Xoay ca model và quota — thêm ở P7 chặng 1

Gói miễn phí giới hạn lượt/ngày cho mỗi model và quota reset theo giờ Pacific, nên hệ thống phải tự
đổi model. Nhóm này không thuộc user story nào: nó là điều kiện để ba tính năng AI chạy được trong
thực tế. Chi tiết: [`../plans/2026-09-18-p7-tich-hop-ai.md`](../plans/2026-09-18-p7-tich-hop-ai.md).

| TC | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|
| TC-103 | Ngày quota tính theo giờ Pacific, đúng cả mùa hè lẫn mùa đông bên Mỹ | U | `tests/unit/test_ai_quota.py` | ✅ |
| TC-104 | Luôn thử model đầu danh sách; model lỗi thì xoay sang model kế | U | `tests/unit/test_ai_quota.py` | ✅ |
| TC-105 | 503 → model nghỉ một lát rồi được dùng lại | U | `tests/unit/test_ai_quota.py` | ✅ |
| TC-106 | 429 theo ngày → bỏ model tới khi reset, ghi lại hạn mức thật | U | `tests/unit/test_ai_quota.py`, `tests/unit/test_gemini.py` | ✅ |
| TC-107 | 429 theo phút → chỉ nghỉ đúng thời gian Google báo, không bỏ cả ngày | U | `tests/unit/test_ai_quota.py`, `tests/unit/test_gemini.py` | ✅ |
| TC-108 | 404 → loại hẳn model; 400/401/403 → dừng xoay ngay | U | `tests/unit/test_ai_quota.py`, `tests/unit/test_gemini.py` | ✅ |
| TC-109 | Hết sạch model → lỗi tiếng Việt, trang không vỡ | U | `tests/unit/test_ai_quota.py` | ✅ |
| TC-110 | Đếm lượt: 503 tính, 429 và 404 không tính; mất mạng (lời gọi chưa tới server) không tính — lỗi tìm được ở chặng 3 ngày 19/09 | U | `tests/unit/test_ai_quota.py`, `tests/unit/test_gemini.py` | ✅ |
| TC-111 | Ngân sách thời gian cắt chuỗi thử, không để treo trang | U | `tests/unit/test_ai_quota.py` | ✅ |
| TC-112 | Bảng quota in đúng mẫu, phân biệt số thật với số ước tính | U | `tests/unit/test_ai_quota.py` | ✅ |

## K. Lỗi tìm được khi rà soát toàn hệ thống — 19/09

Ba lỗi mức cao trong [`reports/2026-09-19-ra-luong-P1-P7.md`](reports/2026-09-19-ra-luong-P1-P7.md), cộng
lỗi chế độ AI giả lập người dùng gặp khi bấm smoke (TC-116). Tất cả lọt qua bộ test đang xanh; mỗi ca dưới đây có test đỏ-trước và đột biến bị bắt.

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-113 | US-20 | Hai lần thu cùng lúc không vượt số còn nợ (H-01) | U | `test_billing_service.py::test_hai_lan_thu_chong_nhau_khong_vuot_so_con_no`, `…::test_hai_may_thu_that_su_dong_thoi_khong_vuot_so_con_no` | ✅ |
| TC-114 | US-10, US-12 | Ngày sai định dạng hoặc trống khi đặt/đổi lịch → báo lỗi, không quy về hôm nay (H-02, S7) | I | `test_appointments.py::test_doi_lich_ngay_sai_dinh_dang_…`, `…::test_dat_lich_ngay_sai_dinh_dang_…` | ✅ |
| TC-116 | US-27 | Chế độ `AI_PROVIDER=fake`: nhãn "AI giả lập — không gọi Gemini", không xoay/đếm quota Gemini, các trang AI hiện dòng cảnh báo (người dùng gặp khi smoke 19/09) | U, I | `test_ai_quota.py::test_ai_gia_lap_…`, `test_ai_service.py::test_che_do_fake_…`, `test_ai.py::test_che_do_gia_lap_…`, `…::test_trang_ai_bao_…` | ✅ |
| TC-115 | nhiều | Bản ghi không còn tồn tại → trang lỗi 404 tiếng Việt, không bao giờ 500, trên mọi đường dẫn theo id (H-03) | I | `tests/integration/test_khong_tim_thay.py` | ✅ |

## J. Hệ thống hoàn chỉnh — chạy cuối mỗi phase từ P5

| TC | US | Tình huống | Mức | File test | Trạng thái |
|---|---|---|---|---|---|
| TC-101 | nhiều | Kịch bản xuyên suốt 11 bước theo [`test-strategy.md`](test-strategy.md) mục 6 | E | `tests/e2e/test_full_flow.py` | ✅ đủ 11/11 bước (bước 10 nối ở P7 chặng 2) |
| TC-102 | nhiều | Checklist bấm tay theo [`smoke-checklist.md`](smoke-checklist.md) | thủ công | — | ⬜ |

TC-101 kéo lên sớm từ P5 (kế hoạch: [`../plans/2026-09-05-e2e-xuyen-suot.md`](../plans/2026-09-05-e2e-xuyen-suot.md)).
Bước 1→6 chạy được ngay sau P4 chặng 1; bước 7→9 nối ở P5, bước 11 (thống kê) nối ở P6; còn bước 10
(AI) chờ P7. Chỉ tick ✅ khi đủ 11 bước.

---

## Đối chiếu bao phủ

### Theo user story

| Nhóm | User story | Test case | Số TC |
|---|---|---|---|
| A. Đăng nhập, phân quyền | US-01 → US-03 | TC-001 → TC-012 | 12 |
| B. Chủ nuôi, thú cưng | US-04 → US-06 | TC-013 → TC-023 | 11 |
| C. Dịch vụ, gói | US-07 → US-09 | TC-024 → TC-031 | 8 |
| D. Lịch hẹn | US-10 → US-14 | TC-032 → TC-052 | 21 |
| E. Hồ sơ chăm sóc | US-15, US-16 | TC-053 → TC-058 | 6 |
| F. Tiêm phòng | US-17, US-18 | TC-059 → TC-064 | 6 |
| G. Hóa đơn, thanh toán | US-19 → US-21 | TC-065 → TC-075 | 11 |
| H. Thống kê | US-22, US-23 | TC-076 → TC-081 | 6 |
| I. AI | US-24 → US-28 | TC-082 → TC-100 | 19 |
| I.4 Xoay model, quota | — (vận hành) | TC-103 → TC-112 | 10 |
| K. Lỗi rà soát 19/09 | US-10, US-12, US-20, US-27 | TC-113 → TC-116 | 4 |
| J. Xuyên suốt | — | TC-101, TC-102 | 2 |
| | **28/28 US** | | **116** |

### Theo yêu cầu đề bài mục 4

| Yêu cầu | Test case | Số lượng |
|---|---|---|
| Test cho **lịch hẹn** | TC-032 → TC-052 | 21 |
| Test cho **hóa đơn** | TC-065 → TC-075 | 11 |
| Test cho **hồ sơ** | TC-053 → TC-058 | 6 |
| Test cho **AI** | TC-082 → TC-100 | 19 |
| Hạ tầng AI (xoay model, quota) | TC-103 → TC-112 | 10 |

**Kết luận: 28/28 user story có test case. Bốn hạng mục đề bài yêu cầu đích danh đều được phủ, trong
đó lịch hẹn và AI — hai phần khó nhất — chiếm 50/116 test case.**
