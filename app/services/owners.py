"""Nghiệp vụ chủ nuôi và thú cưng.

Phục vụ US-04, US-05, US-06. Không import fastapi — mọi hàm ở đây gọi được trực tiếp
trong test mà không cần khởi động ứng dụng.
"""

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.owner import Owner
from app.models.pet import Pet
from app.services import clock
from app.services.errors import LoiNghiepVu
from app.services.text import chuan_hoa


@dataclass
class KetQuaTraCuu:
    chu_nuoi: list[Owner] = field(default_factory=list)
    thu_cung: list[Pet] = field(default_factory=list)

    @property
    def rong(self) -> bool:
        return not self.chu_nuoi and not self.thu_cung


def _bat_buoc(gia_tri: str | None, ten_truong: str) -> str:
    da_cat = (gia_tri or "").strip()
    if not da_cat:
        raise LoiNghiepVu(f"{ten_truong} không được để trống.")
    return da_cat


# --- Chủ nuôi -------------------------------------------------------------------


def tao_chu_nuoi(
    db: Session,
    ho_ten: str,
    so_dien_thoai: str,
    email: str | None = None,
    dia_chi: str | None = None,
    ghi_chu: str | None = None,
) -> Owner:
    o = Owner(
        full_name=_bat_buoc(ho_ten, "Họ tên"),
        phone=_bat_buoc(so_dien_thoai, "Số điện thoại"),
        email=(email or "").strip() or None,
        address=(dia_chi or "").strip() or None,
        note=(ghi_chu or "").strip() or None,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def sua_chu_nuoi(db: Session, chu_nuoi_id: int, **truong) -> Owner:
    o = lay_chu_nuoi(db, chu_nuoi_id)

    if "ho_ten" in truong:
        o.full_name = _bat_buoc(truong["ho_ten"], "Họ tên")
    if "so_dien_thoai" in truong:
        o.phone = _bat_buoc(truong["so_dien_thoai"], "Số điện thoại")
    for khoa, cot in (("email", "email"), ("dia_chi", "address"), ("ghi_chu", "note")):
        if khoa in truong:
            setattr(o, cot, (truong[khoa] or "").strip() or None)

    db.commit()
    db.refresh(o)
    return o


def danh_sach_chu_nuoi(db: Session) -> list[Owner]:
    return list(db.scalars(select(Owner).order_by(Owner.full_name)))


def lay_chu_nuoi(db: Session, chu_nuoi_id: int) -> Owner:
    o = db.get(Owner, chu_nuoi_id)
    if o is None:
        raise LoiNghiepVu("Không tìm thấy chủ nuôi.")
    return o


def tim_theo_so_dien_thoai(db: Session, so_dien_thoai: str) -> list[Owner]:
    """Dùng để cảnh báo trùng số khi thêm chủ nuôi mới (TC-015).

    Trả về danh sách chứ không phải một bản ghi: số điện thoại cố ý không đặt UNIQUE,
    vì hai người trong cùng gia đình dùng chung một số là chuyện thường.
    """
    so = (so_dien_thoai or "").strip()
    if not so:
        return []
    return list(db.scalars(select(Owner).where(Owner.phone == so)))


def xoa_chu_nuoi(db: Session, chu_nuoi_id: int) -> None:
    """TC-016: chặn khi còn thú cưng, kèm thông báo nói rõ phải làm gì.

    Khóa ngoại của SQLite cũng chặn việc này, nhưng nó ném IntegrityError và người dùng
    nhận về lỗi 500. Kiểm ở đây để trả thông báo đọc hiểu được; khóa ngoại giữ vai trò
    lớp chặn cuối nếu có đường ghi nào khác quên gọi hàm này.
    """
    o = lay_chu_nuoi(db, chu_nuoi_id)

    so_thu_cung = db.scalar(select(Pet).where(Pet.owner_id == o.id))
    if so_thu_cung is not None:
        raise LoiNghiepVu(
            "Chủ nuôi này vẫn còn thú cưng. Hãy chuyển hoặc xóa thú cưng trước khi xóa chủ nuôi."
        )

    db.delete(o)
    db.commit()


# --- Thú cưng -------------------------------------------------------------------


def tao_thu_cung(
    db: Session,
    chu_nuoi_id: int,
    ten: str,
    loai: str,
    giong: str | None = None,
    gioi_tinh: str | None = None,
    ngay_sinh: date | None = None,
    can_nang: float | None = None,
    ghi_chu: str | None = None,
) -> Pet:
    chu_nuoi = lay_chu_nuoi(db, chu_nuoi_id)

    p = Pet(
        owner_id=chu_nuoi.id,
        name=_bat_buoc(ten, "Tên thú cưng"),
        species=_bat_buoc(loai, "Loài"),
        breed=(giong or "").strip() or None,
        sex=(gioi_tinh or "").strip() or None,
        birth_date=_kiem_ngay_sinh(ngay_sinh),
        weight_kg=_kiem_can_nang(can_nang),
        note=(ghi_chu or "").strip() or None,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def sua_thu_cung(db: Session, thu_cung_id: int, **truong) -> Pet:
    p = lay_thu_cung(db, thu_cung_id)

    if "ten" in truong:
        p.name = _bat_buoc(truong["ten"], "Tên thú cưng")
    if "loai" in truong:
        p.species = _bat_buoc(truong["loai"], "Loài")
    if "ngay_sinh" in truong:
        p.birth_date = _kiem_ngay_sinh(truong["ngay_sinh"])
    if "can_nang" in truong:
        p.weight_kg = _kiem_can_nang(truong["can_nang"])
    for khoa, cot in (("giong", "breed"), ("gioi_tinh", "sex"), ("ghi_chu", "note")):
        if khoa in truong:
            setattr(p, cot, (truong[khoa] or "").strip() or None)

    db.commit()
    db.refresh(p)
    return p


def lay_thu_cung(db: Session, thu_cung_id: int) -> Pet:
    p = db.get(Pet, thu_cung_id)
    if p is None:
        raise LoiNghiepVu("Không tìm thấy thú cưng.")
    return p


def xoa_thu_cung(db: Session, thu_cung_id: int) -> None:
    """Chặn khi thú cưng còn lịch hẹn hoặc hồ sơ chăm sóc.

    Cùng luật với `xoa_chu_nuoi`: khóa ngoại của SQLite cũng chặn, nhưng nó ném
    IntegrityError và người dùng nhận về lỗi 500. Kiểm ở đây để trả thông báo đọc hiểu
    được; khóa ngoại giữ vai trò lớp chặn cuối.

    Lỗi này tồn tại từ P3 (chỉ có `appointments` trỏ vào) và nặng thêm ở P4 khi có thêm
    `care_records`. Tìm ra khi rà luồng bằng tay sau chặng 1, không phải khi viết code.
    """
    p = lay_thu_cung(db, thu_cung_id)

    if db.scalar(select(Appointment).where(Appointment.pet_id == p.id)) is not None:
        raise LoiNghiepVu(
            f"“{p.name}” vẫn còn lịch hẹn hoặc hồ sơ chăm sóc nên không xóa được. "
            "Hồ sơ chăm sóc là dữ liệu lịch sử, xóa đi thì không khôi phục được."
        )

    db.delete(p)
    db.commit()


def _kiem_ngay_sinh(ngay_sinh: date | None) -> date | None:
    """TC-018. Dùng clock.now() thay vì date.today() để test cố định được thời gian.

    Ranh giới là "sau hôm nay" mới bị chặn — thú cưng sinh hôm nay là hợp lệ.
    """
    if ngay_sinh is None:
        return None
    if ngay_sinh > clock.now().date():
        raise LoiNghiepVu("Ngày sinh không được ở tương lai.")
    return ngay_sinh


def _kiem_can_nang(can_nang: float | None) -> float | None:
    """TC-019. Để trống khi chưa cân; 0 kg cũng vô lý như số âm."""
    if can_nang is None:
        return None
    if can_nang <= 0:
        raise LoiNghiepVu("Cân nặng phải lớn hơn 0. Chưa cân thì để trống.")
    return can_nang


# --- Tra cứu --------------------------------------------------------------------


def tra_cuu(db: Session, tu_khoa: str) -> KetQuaTraCuu:
    """Tìm chủ nuôi và thú cưng theo tên (không dấu) hoặc số điện thoại.

    Tìm trên cột search_name đã chuẩn hóa sẵn, không tính lúc truy vấn: tính lúc truy vấn
    thì SQLite phải quét toàn bảng và không dùng được index.
    """
    tu_khoa = (tu_khoa or "").strip()
    if not tu_khoa:
        # Ô tìm kiếm để trống không được trả về toàn bộ CSDL.
        return KetQuaTraCuu()

    mau = f"%{chuan_hoa(tu_khoa)}%"

    chu_nuoi = db.scalars(
        select(Owner)
        .where(or_(Owner.search_name.like(mau), Owner.phone.like(f"%{tu_khoa}%")))
        .order_by(Owner.full_name)
    )
    thu_cung = db.scalars(select(Pet).where(Pet.search_name.like(mau)).order_by(Pet.name))

    return KetQuaTraCuu(chu_nuoi=list(chu_nuoi), thu_cung=list(thu_cung))
