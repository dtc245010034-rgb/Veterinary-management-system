"""Nghiệp vụ lịch hẹn: đặt lịch và chống trùng lịch.

Phục vụ US-10 → US-14. Đề bài nêu đích danh phần này ở mục 6: "KT2: … debug trùng lịch."

Không import fastapi — gọi trực tiếp được trong test.

QUY TẮC TRÙNG LỊCH
------------------
Lịch chiếm khoảng thời gian NỬA MỞ [start_at, end_at). Thời điểm end_at KHÔNG thuộc về
lịch đó, nó thuộc về lịch kế tiếp. Hai lịch giao nhau khi:

    A.start < B.end  AND  B.start < A.end

Dùng `<=` ở đây là lỗi kinh điển: nó khiến 09:00–10:00 và 10:00–11:00 bị coi là trùng,
trong khi xếp lịch liên tiếp là chuyện bình thường ở cửa hàng.

Từ chối khi giao nhau và trùng nhân viên, hoặc giao nhau và trùng thú cưng — một thú cưng
không thể ở hai nơi cùng lúc. Lịch đã hủy không tham gia kiểm tra.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.appointment import TRANG_THAI_CON_HIEU_LUC, Appointment
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.services import clock
from app.services.errors import LoiNghiepVu

# Giờ làm việc của cửa hàng. Đây là GIẢ ĐỊNH — cửa hàng thật sẽ cần cấu hình được,
# và mỗi nhân viên có thể có ca khác nhau. Đặt ở đây để gợi ý khung trống không đề xuất
# 3 giờ sáng.
GIO_MO_CUA = 8
GIO_DONG_CUA = 18

# Bước nhảy khi dò khung trống, tính bằng phút.
BUOC_GOI_Y = 30

# Số khung trống tối đa gợi ý cho mỗi lần từ chối.
SO_GOI_Y = 5


class TrungLich(LoiNghiepVu):
    """Lịch bị trùng. Mang theo danh sách khung giờ trống để gợi ý cho lễ tân.

    Từ chối suông thì lễ tân phải tự dò từng khung — rất mất thời gian khi khách đang
    đứng đợi ở quầy.
    """

    def __init__(self, thong_diep: str, khung_trong: list[datetime] | None = None):
        super().__init__(thong_diep)
        self.khung_trong = khung_trong or []


def _giao_nhau(bat_dau: datetime, ket_thuc: datetime):
    """Điều kiện SQL: lịch trong CSDL giao nhau với khoảng [bat_dau, ket_thuc).

    Dùng `<` chứ KHÔNG phải `<=` — xem ghi chú ở đầu file.
    """
    return and_(Appointment.start_at < ket_thuc, bat_dau < Appointment.end_at)


def tim_lich_trung(
    db: Session,
    thu_cung_id: int,
    nhan_vien_id: int,
    bat_dau: datetime,
    ket_thuc: datetime,
    bo_qua_id: int | None = None,
) -> Appointment | None:
    """Trả về lịch đầu tiên bị trùng, hoặc None.

    `bo_qua_id` dùng khi đổi lịch: phải loại chính bản ghi đang sửa ra khỏi tập so sánh,
    nếu không nó tự báo trùng với chính mình và không lịch nào đổi được (TC-046).

    Kiểm bằng truy vấn SQL thay vì nạp hết rồi lọc trong Python: cách sau chậm dần theo
    số bản ghi. Hai index (staff_id, start_at) và (pet_id, start_at) phục vụ truy vấn này.
    """
    dieu_kien = [
        Appointment.status.in_(TRANG_THAI_CON_HIEU_LUC),
        _giao_nhau(bat_dau, ket_thuc),
        or_(Appointment.staff_id == nhan_vien_id, Appointment.pet_id == thu_cung_id),
    ]
    if bo_qua_id is not None:
        dieu_kien.append(Appointment.id != bo_qua_id)

    return db.scalar(select(Appointment).where(*dieu_kien).order_by(Appointment.start_at))


def khung_gio_trong(
    db: Session,
    nhan_vien_id: int,
    thu_cung_id: int,
    ngay: date,
    thoi_luong_phut: int,
    bo_qua_id: int | None = None,
) -> list[datetime]:
    """Dò các khung giờ còn trống trong ngày, trong giờ làm việc.

    Chỉ lấy khung bắt đầu từ thời điểm hiện tại trở đi — gợi ý một khung đã trôi qua thì
    lễ tân chọn vào sẽ bị từ chối lần nữa vì lý do "đặt lịch trong quá khứ".
    """
    bay_gio = clock.now()
    ket_qua: list[datetime] = []

    moc = datetime.combine(ngay, time(GIO_MO_CUA))
    het_gio = datetime.combine(ngay, time(GIO_DONG_CUA))

    while moc + timedelta(minutes=thoi_luong_phut) <= het_gio:
        if moc >= bay_gio and tim_lich_trung(
            db, thu_cung_id, nhan_vien_id, moc, moc + timedelta(minutes=thoi_luong_phut), bo_qua_id
        ) is None:
            ket_qua.append(moc)
            if len(ket_qua) >= SO_GOI_Y:
                break

        moc += timedelta(minutes=BUOC_GOI_Y)

    return ket_qua


def dat_lich(
    db: Session,
    thu_cung_id: int,
    dich_vu_id: int,
    nhan_vien_id: int,
    bat_dau: datetime,
    nguoi_tao_id: int,
    ghi_chu: str | None = None,
) -> Appointment:
    """TC-032 → TC-042."""
    thu_cung = db.get(Pet, thu_cung_id)
    if thu_cung is None:
        raise LoiNghiepVu("Không tìm thấy thú cưng.")

    dich_vu = db.get(Service, dich_vu_id)
    if dich_vu is None:
        raise LoiNghiepVu("Không tìm thấy dịch vụ.")
    if not dich_vu.is_active:
        raise LoiNghiepVu(f"Dịch vụ “{dich_vu.name}” đã ngưng bán, không đặt lịch mới được.")

    nhan_vien = db.get(User, nhan_vien_id)
    if nhan_vien is None:
        raise LoiNghiepVu("Không tìm thấy nhân viên.")
    if nhan_vien.role != "caretaker":
        raise LoiNghiepVu("Chỉ nhân viên chăm sóc mới được phân lịch.")
    if not nhan_vien.is_active:
        raise LoiNghiepVu("Nhân viên này đã ngưng hoạt động.")

    # Dùng clock.now() thay vì datetime.now() để test cố định được thời gian (TC-033).
    if bat_dau < clock.now():
        raise LoiNghiepVu("Không thể đặt lịch trong quá khứ.")

    # Giờ kết thúc luôn tính từ thời lượng dịch vụ, không cho người dùng nhập tay.
    ket_thuc = bat_dau + timedelta(minutes=dich_vu.duration_min)

    _chan_neu_trung(db, thu_cung_id, nhan_vien_id, bat_dau, ket_thuc, dich_vu.duration_min)

    lich = Appointment(
        pet_id=thu_cung_id,
        service_id=dich_vu_id,
        staff_id=nhan_vien_id,
        start_at=bat_dau,
        end_at=ket_thuc,
        status="booked",
        note=(ghi_chu or "").strip() or None,
        created_by=nguoi_tao_id,
    )
    db.add(lich)
    db.commit()
    db.refresh(lich)
    return lich


def _chan_neu_trung(
    db: Session,
    thu_cung_id: int,
    nhan_vien_id: int,
    bat_dau: datetime,
    ket_thuc: datetime,
    thoi_luong_phut: int,
    bo_qua_id: int | None = None,
) -> None:
    trung = tim_lich_trung(db, thu_cung_id, nhan_vien_id, bat_dau, ket_thuc, bo_qua_id)
    if trung is None:
        return

    if trung.staff_id == nhan_vien_id:
        ly_do = (
            f"Nhân viên {trung.staff.full_name} đã có lịch "
            f"{trung.start_at:%H:%M}–{trung.end_at:%H:%M} ngày {trung.start_at:%d/%m}."
        )
    else:
        ly_do = (
            f"Thú cưng {trung.pet.name} đã có lịch "
            f"{trung.start_at:%H:%M}–{trung.end_at:%H:%M} ngày {trung.start_at:%d/%m}."
        )

    raise TrungLich(
        ly_do,
        khung_gio_trong(
            db, nhan_vien_id, thu_cung_id, bat_dau.date(), thoi_luong_phut, bo_qua_id
        ),
    )


# --- Truy vấn --------------------------------------------------------------------


def lay_lich(db: Session, lich_id: int) -> Appointment:
    a = db.get(Appointment, lich_id)
    if a is None:
        raise LoiNghiepVu("Không tìm thấy lịch hẹn.")
    return a


def lich_theo_ngay(
    db: Session, ngay: date, nhan_vien_id: int | None = None
) -> list[Appointment]:
    """Toàn bộ lịch trong ngày, kể cả lịch đã hủy.

    Lễ tân cần thấy lịch đã hủy để biết khách nào đã báo bận.
    """
    dau_ngay = datetime.combine(ngay, time.min)
    cuoi_ngay = dau_ngay + timedelta(days=1)

    dieu_kien = [Appointment.start_at >= dau_ngay, Appointment.start_at < cuoi_ngay]
    if nhan_vien_id is not None:
        dieu_kien.append(Appointment.staff_id == nhan_vien_id)

    return list(
        db.scalars(select(Appointment).where(*dieu_kien).order_by(Appointment.start_at))
    )
