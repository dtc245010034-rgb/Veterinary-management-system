# Trả nợ kiến trúc và bao phủ test — trước khi vào P4

> **Phase:** xen giữa P3 và P4 · **Mốc:** KT2 · **Duyệt ngày:** 2026-09-05 · **Trạng thái:** xong
>
> Không thêm chức năng nào cho người dùng. Đây là phiên trả hai khoản nợ mà đợt rà soát sau P3
> phát hiện. Quy ước: [`README.md`](README.md).

## Vì sao làm bây giờ

Đợt rà soát sau P3 tìm ra bốn điểm lệch. Hai điểm tài liệu đã sửa ngay (commit `cdeafe3`). Hai điểm
còn lại chạm vào code:

1. **`app/routers/users.py` chứa logic nghiệp vụ** — vi phạm [`../../CLAUDE.md`](../../CLAUDE.md)
   mục 8 và [`../architecture.md`](../architecture.md). Không có `app/services/users.py`.
2. **10 hàm public trong `app/services/` chưa có unit test gọi trực tiếp** — vi phạm luật bao phủ
   ở CLAUDE.md mục 7.

Làm trước P4 vì P4 thêm hai bảng và hai router nữa: nợ kiến trúc để càng lâu càng đắt, và bảng bao
phủ trong báo cáo cuối kỳ sẽ có chỗ hổng khó giải thích.

## Checklist

- [x] 1. Test đơn vị cho `app/services/users.py` — chạy **đỏ** trước
- [x] 2. Viết `app/services/users.py`, chuyển 4 thao tác ra khỏi router
- [x] 3. `app/routers/users.py` chỉ còn HTTP; integration test P1 vẫn xanh
- [x] 4. Test đơn vị cho 6 hàm còn thiếu của `owners.py`
- [x] 5. Test đơn vị cho `lay_goi`, `ban_lai_goi` của `catalog.py`
- [x] 6. Test đơn vị gọi thẳng `tim_lich_trung`, `khung_gio_trong`
- [x] 7. Thử nghiệm đột biến chứng minh test mới có tác dụng
- [x] 8. Cập nhật `codebase-map.md`, `test-cases.md`, log phiên, báo cáo, commit

## Phạm vi từng bước

### Bước 1–3: tách `app/services/users.py`

Chuyển **nguyên vẹn** bốn thao tác đang nằm trong router, không thêm quy tắc mới:

| Hàm | Quy tắc mang theo |
|---|---|
| `danh_sach_tai_khoan(db)` | sắp theo vai trò rồi tên |
| `tao_tai_khoan(db, username, full_name, role, password)` | vai trò phải thuộc `VAI_TRO`; username không được trùng; mật khẩu băm bằng `hash_password` |
| `khoa_tai_khoan(db, ma, nguoi_thao_tac_id)` | không tìm thấy → lỗi; **không cho tự khóa chính mình** |
| `mo_khoa_tai_khoan(db, ma)` | không tìm thấy → lỗi |

Router bắt `LoiNghiepVu` và render 400 y như `owners`, `services`, `appointments` đang làm. Đây là
lý do phải tách: quy tắc "quản lý không tự khóa mình" hiện chỉ có integration test, trong khi nó là
quy tắc nghiệp vụ thuần, kiểm được mà không cần khởi động app.

### Bước 4–6: bù test cho 10 hàm public

| File | Hàm còn thiếu |
|---|---|
| `owners.py` | `sua_chu_nuoi`, `danh_sach_chu_nuoi`, `lay_chu_nuoi`, `sua_thu_cung`, `lay_thu_cung`, `xoa_thu_cung` |
| `catalog.py` | `lay_goi`, `ban_lai_goi` |
| `scheduling.py` | `tim_lich_trung`, `khung_gio_trong` |

Mỗi hàm tối thiểu 1 happy path + 1 ca biên, theo đúng luật ở CLAUDE.md mục 7.

**Ghi nhận thẳng thắn:** 10 hàm này đã có sẵn và chạy đúng, nên test viết cho chúng sẽ xanh ngay lần
đầu. Điều đó **không** chứng minh test có tác dụng — đúng như luật 2 chống test giả đã nói. Vì vậy
bước 7 bắt buộc: làm hỏng code có chủ đích và xác nhận đúng test tương ứng đỏ. Chỉ nhóm
`services/users.py` mới đi được vòng đỏ–xanh thật vì code chưa tồn tại.

## Ngoài phạm vi

Không đổi giao diện, không đổi hành vi mà người dùng nhìn thấy, không đụng tới `owners.py`,
`catalog.py`, `scheduling.py` — chỉ thêm test cho chúng. Không đặt thêm quy tắc nghiệp vụ mới cho
tài khoản.

## Definition of Done

- [x] `app/routers/users.py` không còn `db.add` / `db.commit` / kiểm tra nghiệp vụ
- [x] Không hàm public nào trong `app/services/` thiếu unit test
- [x] Toàn bộ suite xanh, output sạch, không test nào bị skip
- [x] Ít nhất 3 thử nghiệm đột biến, mỗi cái làm đỏ đúng test dự kiến
- [x] `codebase-map.md` có `services/users.py` và `unit/test_users_service.py`
