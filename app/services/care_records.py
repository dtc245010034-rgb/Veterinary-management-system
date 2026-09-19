"""Nghiệp vụ hồ sơ chăm sóc.

Phục vụ US-15, US-16 — TC-053 → TC-058.

Ghi hồ sơ là thao tác **duy nhất** đưa lịch hẹn về trạng thái `done`. Không có nút "đánh
dấu hoàn thành" riêng: hai đường tới cùng một trạng thái thì `done` mất nghĩa "đã có hồ
sơ", và mọi thứ dựa vào nó ở P6, P7 đều lung lay.

Hệ quả đã biết và chấp nhận: hệ thống không biểu diễn được "buổi chăm sóc đã diễn ra
nhưng chưa ai ghi hồ sơ". Lịch quên ghi sẽ nằm `booked` mãi. Trang thống kê hiện số lịch
đã qua giờ mà chưa ghi (`stats.ThongKe.so_lich_qua_gio_chua_ghi`) — làm ở P7 chặng 0, lời hứa
cũ ghi "P6 sẽ làm" nhưng P6 đã bỏ sót.

Không import fastapi.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.care_record import CareRecord
from app.models.user import User
from app.services import clock
from app.services.errors import LoiKhongTimThay, LoiNghiepVu

# Ai được ghi hồ sơ — theo bảng phân quyền US-02. Lễ tân chỉ xem.
VAI_TRO_GHI_DUOC = ("manager", "caretaker")


def ghi_ho_so(
    db: Session,
    lich_id: int,
    nguoi_ghi_id: int,
    tinh_trang: str | None,
    viec_da_lam: str | None = None,
    dan_do: str | None = None,
) -> CareRecord:
    """TC-053 → TC-056.

    Ba trường được suy ra từ lịch hẹn chứ không nhận từ form:

    - `pet_id` — hai nguồn lệch nhau thì lịch sử của thú cưng sai mà không ai biết.
    - `staff_id` — người THỰC HIỆN buổi chăm sóc, không phải người đang đăng nhập. Quản
      lý ghi hộ thì lịch sử vẫn phải ghi đúng tên nhân viên đã làm (US-16).
    - `performed_at` — thời điểm buổi chăm sóc diễn ra, không phải lúc bấm nút. Ghi hồ sơ
      sáng hôm sau thì nó vẫn phải nằm đúng chỗ trong lịch sử (TC-057).

    `performed_at` là bản sao của `appointment.start_at`. Nó không thể lệch vì lịch đã
    `done` không đổi giờ được nữa — `TRANG_THAI_SUA_DUOC` trong scheduling.py. NẾU AI NỚI
    RÀNG BUỘC ĐÓ, chỗ này âm thầm sai.
    """
    lich = db.get(Appointment, lich_id)
    if lich is None:
        raise LoiKhongTimThay("Không tìm thấy lịch hẹn.")

    _kiem_quyen(db, lich, nguoi_ghi_id)

    if lich.status == "cancelled":
        raise LoiNghiepVu("Lịch đã hủy nên không ghi hồ sơ được.")
    if lich.status == "done":
        raise LoiNghiepVu("Lịch này đã có hồ sơ chăm sóc. Mỗi lịch hẹn chỉ một hồ sơ.")

    # Nút "Ghi hồ sơ" hiện ngay trên lịch tuần sau trong danh sách của nhân viên, nên đây
    # là lỗ đi qua đúng luồng bình thường chứ không phải đường vòng.
    if lich.start_at > clock.now():
        raise LoiNghiepVu("Buổi chăm sóc chưa diễn ra, chưa ghi hồ sơ được.")

    tinh_trang = (tinh_trang or "").strip()
    if not tinh_trang:
        raise LoiNghiepVu("Phải ghi tình trạng thú cưng.")

    ho_so = CareRecord(
        appointment_id=lich.id,
        pet_id=lich.pet_id,
        staff_id=lich.staff_id,
        performed_at=lich.start_at,
        condition_note=tinh_trang,
        actions_taken=(viec_da_lam or "").strip() or None,
        next_advice=(dan_do or "").strip() or None,
    )
    lich.status = "done"

    db.add(ho_so)
    db.commit()
    db.refresh(ho_so)
    return ho_so


def _kiem_quyen(db: Session, lich: Appointment, nguoi_ghi_id: int) -> None:
    nguoi_ghi = db.get(User, nguoi_ghi_id)
    if nguoi_ghi is None:
        raise LoiKhongTimThay("Không tìm thấy tài khoản.")

    if nguoi_ghi.role not in VAI_TRO_GHI_DUOC:
        raise LoiNghiepVu("Chỉ nhân viên chăm sóc và quản lý mới ghi được hồ sơ.")

    if nguoi_ghi.role == "caretaker" and lich.staff_id != nguoi_ghi.id:
        raise LoiNghiepVu("Chỉ ghi được hồ sơ cho lịch được phân cho mình.")


def lay_ho_so(db: Session, ho_so_id: int) -> CareRecord:
    hs = db.get(CareRecord, ho_so_id)
    if hs is None:
        raise LoiKhongTimThay("Không tìm thấy hồ sơ chăm sóc.")
    return hs


def ho_so_cua_lich(db: Session, lich_id: int) -> CareRecord | None:
    """None khi lịch chưa có hồ sơ — dùng để quyết định hiện nút hay hiện nội dung."""
    return db.scalar(select(CareRecord).where(CareRecord.appointment_id == lich_id))


def lich_su(db: Session, thu_cung_id: int) -> list[CareRecord]:
    """TC-057, TC-058: mới nhất lên đầu."""
    return list(
        db.scalars(
            select(CareRecord)
            .where(CareRecord.pet_id == thu_cung_id)
            .order_by(CareRecord.performed_at.desc())
        )
    )
