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

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.appointment import (
    TEN_TRANG_THAI,
    TRANG_THAI_CON_HIEU_LUC,
    Appointment,
)
from app.models.invoice import TRANG_THAI_CON_HIEU_LUC as HOA_DON_CON_HIEU_LUC
from app.models.invoice import Invoice
from app.models.pet import Pet
from app.models.service import Service
from app.models.user import User
from app.services import clock
from app.services.errors import LoiKhongTimThay, LoiNghiepVu

# Giờ làm việc của cửa hàng. Đây là GIẢ ĐỊNH — cửa hàng thật sẽ cần cấu hình được,
# và mỗi nhân viên có thể có ca khác nhau. Đặt ở đây để gợi ý khung trống không đề xuất
# 3 giờ sáng.
GIO_MO_CUA = 8
GIO_DONG_CUA = 18

# Suy ra từ hai hằng trên, không viết cứng: đổi giờ đóng cửa mà quên sửa số này thì
# `catalog` sẽ chặn theo một ngày làm việc khác với `scheduling`. `catalog.py` nhập đúng
# hằng này — nhập một HẰNG SỐ, không gọi hàm, nên hai service vẫn tách ra được.
PHUT_LAM_VIEC_MOI_NGAY = (GIO_DONG_CUA - GIO_MO_CUA) * 60

# Bước nhảy khi dò khung trống, tính bằng phút.
BUOC_GOI_Y = 30

# Số khung trống tối đa gợi ý cho mỗi lần từ chối.
SO_GOI_Y = 5

# Chỉ lịch chưa hủy và chưa làm xong mới đổi hoặc hủy được. Lịch `done` là việc đã
# thực hiện rồi — sửa nó là sửa lịch sử.
TRANG_THAI_SUA_DUOC = ("booked", "rescheduled")

# Lịch `pending` (khách tự xin, P9 chặng 5) giữ chỗ tối đa chừng này giờ kể từ lúc tạo. Không có hạn thì một
# khách xin liền mấy khung đẹp rồi để đó là chặn được cả ngày làm việc của một nhân viên.
HAN_CHO_DUYET_GIO = 24

# Số lịch chờ duyệt còn hạn tối đa của MỖI khách, cùng lý do với hạn ở trên.
TRAN_LICH_CHO_MOI_KHACH = 3

LY_DO_HET_HAN = "Quá hạn chờ duyệt, hệ thống tự hủy."


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


def _giu_cho():
    """Điều kiện SQL: lịch còn chiếm chỗ.

    Lịch đã đặt/đã đổi/đã xong luôn giữ chỗ. Lịch `pending` giữ chỗ chỉ khi chưa quá hạn: điều kiện này nằm TRONG
    truy vấn chứ không chờ hàm quét đổi trạng thái, nên đúng đắn không phụ thuộc việc có ai chạy quét hay chưa.
    Lịch quá hạn đúng `HAN_CHO_DUYET_GIO` giờ là hết giữ chỗ (`>` chứ không phải `>=`).
    """
    han = clock.now() - timedelta(hours=HAN_CHO_DUYET_GIO)
    return or_(
        Appointment.status.in_(TRANG_THAI_CON_HIEU_LUC),
        and_(Appointment.status == "pending", Appointment.created_at > han),
    )


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
        _giu_cho(),
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
    toi_da: int | None = SO_GOI_Y,
) -> list[datetime]:
    """Dò các khung giờ còn trống trong ngày, trong giờ làm việc.

    `toi_da` mặc định là `SO_GOI_Y` (gợi ý sau khi lễ tân bị từ chối); `None` dò hết ngày (khách xem bảng khung trống).

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
            if toi_da is not None and len(ket_qua) >= toi_da:
                break

        moc += timedelta(minutes=BUOC_GOI_Y)

    return ket_qua


def _kiem_gio_lam_viec(bat_dau: datetime, ket_thuc: datetime) -> None:
    """Cả buổi phải nằm trọn trong giờ mở cửa — M-06 (= S6), người dùng chốt 24/09.

    Một luật chặn cả ba triệu chứng đo được trên giao diện ngày 19/09: đặt lịch lúc 3 giờ
    sáng, buổi 23:50 lấn sang 01:20 hôm sau, và dịch vụ 2.000 phút giữ nhân viên hơn 33
    giờ. Ca cuối bị chặn ở đây vì không khoảng nào dài hơn một ngày làm việc lọt được
    giữa hai mốc; không cần thêm phép kiểm riêng cho thời lượng.

    So `ket_thuc > dong_cua` chứ không phải `>=`: buổi 17:00–18:00 vừa khít giờ đóng cửa
    là hợp lệ. Đây đúng cái bẫy mà TC-038 đã bắt một lần ở phép kiểm trùng lịch.

    Mốc đóng cửa lấy theo ngày của `bat_dau`, nên buổi lấn qua nửa đêm luôn vượt mốc —
    không phải viết thêm phép so sánh ngày.
    """
    mo_cua = datetime.combine(bat_dau.date(), time(GIO_MO_CUA))
    dong_cua = datetime.combine(bat_dau.date(), time(GIO_DONG_CUA))
    if bat_dau < mo_cua or ket_thuc > dong_cua:
        raise LoiNghiepVu(
            f"Cửa hàng chỉ nhận lịch trong giờ làm việc "
            f"{GIO_MO_CUA:02d}:00–{GIO_DONG_CUA:02d}:00. Buổi này bắt đầu "
            f"{bat_dau:%H:%M} ngày {bat_dau:%d/%m} và kéo tới "
            f"{ket_thuc:%H:%M} ngày {ket_thuc:%d/%m}."
        )


def _kiem_dieu_kien_dat(
    db: Session, thu_cung_id: int, dich_vu_id: int, nhan_vien_id: int, bat_dau: datetime
) -> tuple[Service, datetime]:
    """Mọi phép kiểm trước khi tạo một lịch mới; trả (dịch vụ, giờ kết thúc).

    Dùng chung cho lịch lễ tân đặt (`booked`) và lịch khách xin (`pending`): hai đường mà phép kiểm khác nhau
    thì lịch khách xin lọt được thứ lễ tân bị chặn.
    """
    thu_cung = db.get(Pet, thu_cung_id)
    if thu_cung is None:
        raise LoiKhongTimThay("Không tìm thấy thú cưng.")

    dich_vu = db.get(Service, dich_vu_id)
    if dich_vu is None:
        raise LoiKhongTimThay("Không tìm thấy dịch vụ.")
    if not dich_vu.is_active:
        raise LoiNghiepVu(f"Dịch vụ “{dich_vu.name}” đã ngưng bán, không đặt lịch mới được.")

    _kiem_nhan_vien(db, nhan_vien_id)

    # Dùng clock.now() thay vì datetime.now() để test cố định được thời gian (TC-033).
    if bat_dau < clock.now():
        raise LoiNghiepVu("Không thể đặt lịch trong quá khứ.")

    # Giờ kết thúc luôn tính từ thời lượng dịch vụ, không cho người dùng nhập tay.
    ket_thuc = bat_dau + timedelta(minutes=dich_vu.duration_min)

    _kiem_gio_lam_viec(bat_dau, ket_thuc)
    _chan_neu_trung(db, thu_cung_id, nhan_vien_id, bat_dau, ket_thuc, dich_vu.duration_min)
    return dich_vu, ket_thuc


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
    _, ket_thuc = _kiem_dieu_kien_dat(db, thu_cung_id, dich_vu_id, nhan_vien_id, bat_dau)

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


# --- Lịch chờ duyệt (P9 chặng 5) ------------------------------------------------------


def huy_lich_cho_het_han(db: Session) -> int:
    """Đổi lịch `pending` quá hạn sang `cancelled`; trả số lịch đã hủy.

    Chỉ để trạng thái hiển thị đúng — việc nhả chỗ đã do `_giu_cho` làm từ trước. Idempotent.
    """
    han = clock.now() - timedelta(hours=HAN_CHO_DUYET_GIO)
    het_han = list(
        db.scalars(select(Appointment).where(Appointment.status == "pending", Appointment.created_at <= han))
    )
    for lich in het_han:
        lich.status = "cancelled"
        lich.cancel_reason = LY_DO_HET_HAN
    if het_han:
        db.commit()
    return len(het_han)


def so_lich_cho_cua_khach(db: Session, khach_id: int) -> int:
    """Số lịch chờ duyệt CÒN HẠN của một khách."""
    han = clock.now() - timedelta(hours=HAN_CHO_DUYET_GIO)
    return db.scalar(
        select(func.count()).where(
            Appointment.customer_id == khach_id,
            Appointment.status == "pending",
            Appointment.created_at > han,
        )
    )


def tao_yeu_cau_lich(
    db: Session,
    khach_id: int,
    thu_cung_id: int,
    dich_vu_id: int,
    nhan_vien_id: int,
    bat_dau: datetime,
    ghi_chu: str | None = None,
) -> Appointment:
    """Khách xin một lịch: tạo lịch `pending`, giữ chỗ tới khi lễ tân duyệt hoặc quá hạn.

    Hàm này KHÔNG kiểm thú cưng có thuộc khách hay không — đó là việc của cổng chặn chủ trong
    `khach_du_lieu`, nơi duy nhất cổng khách được gọi tới đây.
    """
    huy_lich_cho_het_han(db)
    if so_lich_cho_cua_khach(db, khach_id) >= TRAN_LICH_CHO_MOI_KHACH:
        raise LoiNghiepVu(
            f"Bạn đang có {TRAN_LICH_CHO_MOI_KHACH} lịch chờ duyệt, là mức tối đa. "
            "Hãy chờ cửa hàng xác nhận hoặc từ chối trước khi xin thêm."
        )

    _, ket_thuc = _kiem_dieu_kien_dat(db, thu_cung_id, dich_vu_id, nhan_vien_id, bat_dau)

    lich = Appointment(
        pet_id=thu_cung_id,
        service_id=dich_vu_id,
        staff_id=nhan_vien_id,
        start_at=bat_dau,
        end_at=ket_thuc,
        status="pending",
        note=(ghi_chu or "").strip() or None,
        customer_id=khach_id,
    )
    db.add(lich)
    db.commit()
    db.refresh(lich)
    return lich


def danh_sach_cho_duyet(db: Session) -> list[Appointment]:
    """Lịch chờ duyệt còn hạn, sớm nhất trước — màn duyệt của lễ tân."""
    huy_lich_cho_het_han(db)
    return list(
        db.scalars(select(Appointment).where(Appointment.status == "pending").order_by(Appointment.start_at, Appointment.id))
    )


def _lay_lich_cho(db: Session, lich_id: int) -> Appointment:
    huy_lich_cho_het_han(db)
    lich = lay_lich(db, lich_id)
    if lich.status != "pending":
        raise LoiNghiepVu(f"Lịch này đang ở trạng thái “{lich.ten_trang_thai}”, không còn chờ duyệt.")
    return lich


def duyet_lich_cho(db: Session, lich_id: int, nguoi_duyet_id: int) -> Appointment:
    """Lễ tân duyệt: `pending` → `booked`.

    Kiểm lại những gì có thể đã đổi từ lúc khách xin: giờ hẹn đã qua, nhân viên bị khóa, và phép trùng lịch (loại
    chính lịch này ra). Quá hạn thì `_lay_lich_cho` đã hủy nó nên duyệt sẽ báo "đã hủy".
    """
    lich = _lay_lich_cho(db, lich_id)
    if lich.start_at < clock.now():
        raise LoiNghiepVu("Giờ hẹn đã qua nên không duyệt được. Hãy từ chối kèm lý do để khách xin lại.")
    _kiem_nhan_vien(db, lich.staff_id)
    _chan_neu_trung(
        db, lich.pet_id, lich.staff_id, lich.start_at, lich.end_at, lich.service.duration_min, bo_qua_id=lich.id
    )

    lich.status = "booked"
    lich.decided_by = nguoi_duyet_id
    db.commit()
    db.refresh(lich)
    return lich


def tu_choi_lich_cho(db: Session, lich_id: int, ly_do: str, nguoi_duyet_id: int) -> Appointment:
    """Lễ tân từ chối: `pending` → `cancelled`, lý do bắt buộc (khách đọc được). Khung giờ được trả lại ngay."""
    lich = _lay_lich_cho(db, lich_id)
    ly_do = (ly_do or "").strip()
    if not ly_do:
        raise LoiNghiepVu("Phải ghi lý do từ chối để khách biết vì sao.")

    lich.status = "cancelled"
    lich.cancel_reason = ly_do
    lich.decided_by = nguoi_duyet_id
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


def _kiem_nhan_vien(db: Session, nhan_vien_id: int) -> User:
    nhan_vien = db.get(User, nhan_vien_id)
    if nhan_vien is None:
        raise LoiKhongTimThay("Không tìm thấy nhân viên.")
    if nhan_vien.role != "caretaker":
        raise LoiNghiepVu("Chỉ nhân viên chăm sóc mới được phân lịch.")
    if not nhan_vien.is_active:
        raise LoiNghiepVu("Nhân viên này đã ngưng hoạt động.")
    return nhan_vien


def _chan_neu_khong_sua_duoc(lich: Appointment, hanh_dong: str) -> None:
    if lich.status not in TRANG_THAI_SUA_DUOC:
        raise LoiNghiepVu(
            f"Lịch ở trạng thái “{TEN_TRANG_THAI[lich.status]}” nên không {hanh_dong} được."
        )


def doi_lich(
    db: Session,
    lich_id: int,
    bat_dau: datetime,
    nhan_vien_id: int | None = None,
) -> Appointment:
    """Đổi giờ và/hoặc nhân viên của một lịch hẹn. TC-044 → TC-047.

    THỨ TỰ Ở ĐÂY LÀ BẮT BUỘC: kiểm tra xong hết mới ghi. Cập nhật trước rồi mới kiểm
    sẽ để lịch rơi vào trạng thái nửa vời — giờ đã đổi nhưng thao tác báo lỗi (TC-045).
    """
    lich = lay_lich(db, lich_id)
    _chan_neu_khong_sua_duoc(lich, "đổi")

    if bat_dau < clock.now():
        raise LoiNghiepVu("Không thể đổi lịch về quá khứ.")

    # Kiểm cả khi giữ nguyên nhân viên: người đó có thể bị khóa sau khi được phân lịch, và
    # dời giờ mà giữ họ thì lịch vẫn kẹt trong tay tài khoản không đăng nhập được (S4).
    nhan_vien_moi = lich.staff_id if nhan_vien_id is None else nhan_vien_id
    _kiem_nhan_vien(db, nhan_vien_moi)

    thoi_luong = lich.service.duration_min
    ket_thuc = bat_dau + timedelta(minutes=thoi_luong)

    # Bài học 4 — sửa cả lớp lỗi: chặn ở `dat_lich` mà quên đây thì đặt đúng giờ rồi dời
    # ra 07:00 vẫn lọt, và M-06 chỉ được vá một nửa.
    _kiem_gio_lam_viec(bat_dau, ket_thuc)


    # bo_qua_id: loại chính lịch đang sửa ra khỏi tập so sánh, nếu không nó tự báo trùng
    # với chính mình và không lịch nào đổi giờ được (TC-046).
    _chan_neu_trung(
        db, lich.pet_id, nhan_vien_moi, bat_dau, ket_thuc, thoi_luong, bo_qua_id=lich.id
    )

    # Không có gì đổi thì đừng ghi vào sổ là đã dời (L-06). Rà 19/09: bấm Đổi mà giữ
    # nguyên giờ và nhân viên vẫn làm trạng thái nhảy sang "Đã dời lịch", nên lịch sử của
    # buổi đó kể một chuyện không xảy ra. Phép so đặt TRƯỚC khi gán, vì sau khi gán thì
    # không còn giá trị cũ để so.
    co_thay_doi = lich.start_at != bat_dau or lich.staff_id != nhan_vien_moi

    lich.start_at = bat_dau
    lich.end_at = ket_thuc
    lich.staff_id = nhan_vien_moi
    if co_thay_doi:
        lich.status = "rescheduled"
    db.commit()
    db.refresh(lich)
    return lich


def _chan_neu_con_hoa_don(db: Session, lich: Appointment) -> None:
    """US-21 — TC-074, TC-075.

    Chạy TRƯỚC phép kiểm trạng thái, và đó là toàn bộ giá trị của hàm này. Ở P5 lịch đã
    có hóa đơn thì luôn `done` (hóa đơn chỉ lập từ lịch `done`, và `done` là cửa một
    chiều), nên phép kiểm trạng thái đằng sau cũng chặn được mọi ca ở đây — nhưng bằng
    câu "Lịch ở trạng thái Hoàn thành nên không hủy được", không nói gì về hóa đơn. Lễ
    tân đọc xong vẫn không biết tiền của buổi đó đang nằm ở đâu.

    Đặt ở `scheduling` chứ không gọi sang `billing`: hai service phụ thuộc chéo nhau thì
    lần sau không tách ra được. Ở đây chỉ cần biết model `Invoice`, giống cách file này
    đã biết `Appointment` — xem quyết định 7 trong kế hoạch P5.
    """
    hd = db.scalar(
        select(Invoice)
        .where(Invoice.appointment_id == lich.id, Invoice.status.in_(HOA_DON_CON_HIEU_LUC))
        .order_by(Invoice.id)
    )
    if hd is None:
        return

    raise LoiNghiepVu(
        f"Lịch này đã có hóa đơn #{hd.id} ({hd.ten_trang_thai.lower()}) nên không hủy được. "
        "Hủy hóa đơn ở trang hóa đơn trước; buổi chăm sóc đã ghi nhận hoàn thành thì vẫn "
        "giữ nguyên trong sổ."
    )


def huy_lich(db: Session, lich_id: int, ly_do: str) -> Appointment:
    """Hủy lịch kèm lý do. TC-048, TC-049, TC-074, TC-075.

    Lý do là bắt buộc: khung giờ bị giải phóng mà không ai biết vì sao thì sau này
    không truy nguyên được, và thống kê ở P6 không phân biệt được khách hủy với lỗi vận hành.
    """
    lich = lay_lich(db, lich_id)
    _chan_neu_con_hoa_don(db, lich)
    _chan_neu_khong_sua_duoc(lich, "hủy")

    ly_do = (ly_do or "").strip()
    if not ly_do:
        raise LoiNghiepVu("Phải ghi lý do hủy lịch.")

    lich.status = "cancelled"
    lich.cancel_reason = ly_do
    db.commit()
    db.refresh(lich)
    return lich


# --- Truy vấn --------------------------------------------------------------------


def lay_lich(db: Session, lich_id: int) -> Appointment:
    a = db.get(Appointment, lich_id)
    if a is None:
        raise LoiKhongTimThay("Không tìm thấy lịch hẹn.")
    return a


def so_lich_chua_lam_theo_nhan_vien(db: Session) -> dict[int, int]:
    """Số lịch còn sửa được (chưa hủy, chưa xong) của từng nhân viên — lỗ hổng S4.

    Trang Tài khoản dùng để cảnh báo nhân viên đã khóa vẫn còn giữ lịch: không ai chuyển
    những lịch đó sang người khác thì chúng nằm `booked` mãi.
    """
    return dict(
        db.execute(
            select(Appointment.staff_id, func.count())
            .where(Appointment.status.in_(TRANG_THAI_SUA_DUOC))
            .group_by(Appointment.staff_id)
        ).all()
    )


def lich_theo_ngay(
    db: Session, ngay: date, nhan_vien_id: int | None = None
) -> list[Appointment]:
    """Toàn bộ lịch trong ngày, kể cả lịch đã hủy.

    Lễ tân cần thấy lịch đã hủy để biết khách nào đã báo bận.
    """
    huy_lich_cho_het_han(db)  # lịch chờ quá hạn không được hiện như còn chờ
    dau_ngay = datetime.combine(ngay, time.min)
    cuoi_ngay = dau_ngay + timedelta(days=1)

    dieu_kien = [Appointment.start_at >= dau_ngay, Appointment.start_at < cuoi_ngay]
    if nhan_vien_id is not None:
        dieu_kien.append(Appointment.staff_id == nhan_vien_id)

    return list(
        db.scalars(select(Appointment).where(*dieu_kien).order_by(Appointment.start_at))
    )
