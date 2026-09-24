"""Nghiệp vụ chủ nuôi và thú cưng.

Phục vụ US-04, US-05, US-06. Không import fastapi — mọi hàm ở đây gọi được trực tiếp
trong test mà không cần khởi động ứng dụng.
"""

from dataclasses import dataclass, field
from datetime import date
import re

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.owner import Owner
from app.models.pet import GIOI_TINH, Pet
from app.services import clock
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.services.text import chuan_hoa


@dataclass
class KetQuaTraCuu:
    chu_nuoi: list[Owner] = field(default_factory=list)
    thu_cung: list[Pet] = field(default_factory=list)

    @property
    def rong(self) -> bool:
        return not self.chu_nuoi and not self.thu_cung


# Trần độ dài cho các ô chữ. Rà 19/09: họ tên 509 ký tự lưu được (L-03). Cột CSDL có
# giới hạn riêng (`String(100)`…) nhưng SQLite KHÔNG ép độ dài, nên ràng buộc thật sự
# duy nhất là ở đây.
DAI_TOI_DA = {"Họ tên": 100, "Tên thú cưng": 50, "Loài": 30, "Giống": 50,
              "Địa chỉ": 255, "Ghi chú": 500}

# Cân nặng và tuổi. Con voi nặng nhất cũng không vào tiệm spa thú cưng; 200 kg đã rộng
# hơn mọi giống chó mèo. Tuổi 40 năm rộng hơn tuổi thọ của mọi loài thú nuôi phổ biến.
CAN_NANG_TOI_DA = 200
TUOI_TOI_DA_NAM = 40

# Số Việt Nam: 10 chữ số bắt đầu bằng 0. Người dùng chốt 24/09.
_MAU_SO_DIEN_THOAI = re.compile(r"^0\d{9}$")

# Đủ chặt để loại `khong-phai-email` và `a@b`, đủ lỏng để không chặn nhầm địa chỉ thật.
# Không dùng RFC 5322 đầy đủ: nó dài hơn cả file này và vẫn không quyết được ca biên.
_MAU_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def _bat_buoc(gia_tri: str | None, ten_truong: str) -> str:
    da_cat = (gia_tri or "").strip()
    if not da_cat:
        raise LoiNghiepVu(f"{ten_truong} không được để trống.")
    return _kiem_do_dai(da_cat, ten_truong)


def _kiem_do_dai(gia_tri: str, ten_truong: str) -> str:
    """L-03. Trả lại chính chuỗi để gọi lồng được vào chỗ đang gán."""
    toi_da = DAI_TOI_DA.get(ten_truong)
    if toi_da is not None and len(gia_tri) > toi_da:
        raise LoiNghiepVu(f"{ten_truong} không được dài quá {toi_da} ký tự.")
    return gia_tri


def _tuy_chon(gia_tri: str | None, ten_truong: str) -> str | None:
    """Ô không bắt buộc: để trống thì thành None, có nhập thì vẫn phải trong trần."""
    da_cat = (gia_tri or "").strip()
    if not da_cat:
        return None
    return _kiem_do_dai(da_cat, ten_truong)


def chuan_hoa_so_dien_thoai(so: str | None) -> str:
    """Bỏ dấu cách, chấm, gạch, ngoặc; quy `+84`/`84` về dạng bắt đầu bằng `0`.

    Công khai vì `tim_theo_so_dien_thoai` phải chuẩn hóa **cùng một cách** trước khi so
    trùng: số đã lưu luôn ở dạng chuẩn, nên tra bằng chuỗi thô người dùng vừa gõ
    (`+84912345678`) sẽ không khớp gì cả và M-07 lại lọt theo một đường khác.

    Chỉ chuẩn hóa, không phán xét — phép kiểm định dạng nằm ở `_kiem_so_dien_thoai`.
    """
    sach = re.sub(r"[\s.\-()]", "", (so or "").strip())
    if sach.startswith("+84"):
        sach = "0" + sach[3:]
    elif sach.startswith("84") and len(sach) == 11:
        sach = "0" + sach[2:]
    return sach


def _kiem_so_dien_thoai(so: str | None) -> str:
    """M-05. Chuẩn hóa TRƯỚC khi kiểm, và trả về bản đã chuẩn hóa để lưu."""
    tho = _bat_buoc(so, "Số điện thoại")
    sach = chuan_hoa_so_dien_thoai(tho)

    if not _MAU_SO_DIEN_THOAI.match(sach):
        raise LoiNghiepVu(
            "Số điện thoại phải là số Việt Nam 10 chữ số bắt đầu bằng 0, "
            "ví dụ 0912345678."
        )
    return sach


def _kiem_email(email: str | None) -> str | None:
    """M-05. Email là ô KHÔNG bắt buộc — để trống vẫn hợp lệ."""
    da_cat = _tuy_chon(email, "Email")
    if da_cat is None:
        return None
    if not _MAU_EMAIL.match(da_cat):
        raise LoiNghiepVu("Email không đúng định dạng, ví dụ ten@vidu.com.")
    return da_cat


def _kiem_gioi_tinh(gioi_tinh: str | None) -> str | None:
    """L-03. Neo vào chính hằng mà template dựng ô chọn — xem `models/pet.py`."""
    da_cat = (gioi_tinh or "").strip()
    if not da_cat:
        return None
    if da_cat not in GIOI_TINH:
        raise LoiNghiepVu(f"Giới tính chỉ nhận {' hoặc '.join(GIOI_TINH)}.")
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
        phone=_kiem_so_dien_thoai(so_dien_thoai),
        email=_kiem_email(email),
        address=_tuy_chon(dia_chi, "Địa chỉ"),
        note=_tuy_chon(ghi_chu, "Ghi chú"),
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
        o.phone = _kiem_so_dien_thoai(truong["so_dien_thoai"])
    if "email" in truong:
        o.email = _kiem_email(truong["email"])
    for khoa, cot, nhan in (("dia_chi", "address", "Địa chỉ"), ("ghi_chu", "note", "Ghi chú")):
        if khoa in truong:
            setattr(o, cot, _tuy_chon(truong[khoa], nhan))

    db.commit()
    db.refresh(o)
    return o


def danh_sach_chu_nuoi(db: Session) -> list[Owner]:
    return list(db.scalars(select(Owner).order_by(Owner.full_name)))


def lay_chu_nuoi(db: Session, chu_nuoi_id: int) -> Owner:
    o = db.get(Owner, chu_nuoi_id)
    if o is None:
        raise LoiKhongTimThay("Không tìm thấy chủ nuôi.")
    return o


def tim_theo_so_dien_thoai(
    db: Session, so_dien_thoai: str, bo_qua_id: int | None = None
) -> list[Owner]:
    """Dùng để cảnh báo trùng số khi thêm chủ nuôi mới (TC-015).

    Trả về danh sách chứ không phải một bản ghi: số điện thoại cố ý không đặt UNIQUE,
    vì hai người trong cùng gia đình dùng chung một số là chuyện thường.

    `bo_qua_id` loại chính chủ nuôi vừa tạo ra khỏi danh sách cảnh báo — nói "đã có
    người dùng số này" mà trỏ vào chính bản ghi vừa tạo thì vô nghĩa.
    """
    so = chuan_hoa_so_dien_thoai(so_dien_thoai)
    if not so:
        return []

    dieu_kien = [Owner.phone == so]
    if bo_qua_id is not None:
        dieu_kien.append(Owner.id != bo_qua_id)

    return list(db.scalars(select(Owner).where(*dieu_kien)))


def xoa_chu_nuoi(db: Session, chu_nuoi_id: int) -> None:
    """TC-016: chặn khi còn thú cưng, kèm thông báo nói rõ phải làm gì.

    Khóa ngoại của SQLite cũng chặn việc này, nhưng nó ném IntegrityError và người dùng
    nhận về lỗi 500. Kiểm ở đây để trả thông báo đọc hiểu được; khóa ngoại giữ vai trò
    lớp chặn cuối nếu có đường ghi nào khác quên gọi hàm này.
    """
    o = lay_chu_nuoi(db, chu_nuoi_id)

    # Phép kiểm rõ ràng cho ca đã biết, vì nó nói được người dùng phải làm gì tiếp.
    so_thu_cung = db.scalar(select(Pet).where(Pet.owner_id == o.id))
    if so_thu_cung is not None:
        raise LoiNghiepVu(
            "Chủ nuôi này vẫn còn thú cưng. Hãy chuyển hoặc xóa thú cưng trước khi xóa chủ nuôi."
        )

    db.delete(o)
    try:
        db.commit()
    except IntegrityError:
        # Lớp chặn cuối cho những bảng chưa tồn tại lúc viết hàm này. `xoa_thu_cung` đã
        # dính đúng lỗi đó một lần: chặn `appointments`, bỏ sót `vaccinations`, và người
        # dùng nhận về trang 500. P5 thêm `invoices` trỏ vào `owners` là ca tiếp theo.
        db.rollback()
        raise LoiNghiepVu(
            "Chủ nuôi này vẫn còn dữ liệu liên quan nên không xóa được."
        )


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
        breed=_tuy_chon(giong, "Giống"),
        sex=_kiem_gioi_tinh(gioi_tinh),
        birth_date=_kiem_ngay_sinh(ngay_sinh),
        weight_kg=_kiem_can_nang(can_nang),
        note=_tuy_chon(ghi_chu, "Ghi chú"),
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
    if "gioi_tinh" in truong:
        p.sex = _kiem_gioi_tinh(truong["gioi_tinh"])
    for khoa, cot, nhan in (("giong", "breed", "Giống"), ("ghi_chu", "note", "Ghi chú")):
        if khoa in truong:
            setattr(p, cot, _tuy_chon(truong[khoa], nhan))

    db.commit()
    db.refresh(p)
    return p


def lay_thu_cung(db: Session, thu_cung_id: int) -> Pet:
    p = db.get(Pet, thu_cung_id)
    if p is None:
        raise LoiKhongTimThay("Không tìm thấy thú cưng.")
    return p


def xoa_thu_cung(db: Session, thu_cung_id: int) -> None:
    """Chặn khi còn dữ liệu trỏ vào thú cưng này.

    Để khóa ngoại quyết định thay vì tự liệt kê bảng. Bản trước hỏi đúng một câu — "còn
    lịch hẹn không?" — nên khi P4 thêm bảng `vaccinations` cũng trỏ vào `pets`, thú cưng
    chỉ có hồ sơ tiêm lọt qua phép chặn và người dùng nhận về trang đen "Internal Server
    Error". Đó là lần thứ hai cùng một lỗi, vì cách chặn cũ bắt phải nhớ sửa hàm này mỗi
    lần thêm bảng.

    Cách này chặn sẵn mọi bảng sẽ thêm ở P5–P7. Đổi lại, thông báo không nói được chính
    xác loại dữ liệu nào đang giữ — chấp nhận, vì im lặng hỏng nặng hơn nói chung chung.
    """
    p = lay_thu_cung(db, thu_cung_id)
    ten = p.name

    db.delete(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise LoiNghiepVu(
            f"“{ten}” vẫn còn dữ liệu liên quan — lịch hẹn, hồ sơ chăm sóc hoặc hồ sơ "
            "tiêm — nên không xóa được. Đó là dữ liệu lịch sử, xóa đi thì không khôi "
            "phục được."
        )


def _kiem_ngay_sinh(ngay_sinh: date | None) -> date | None:
    """TC-018. Dùng clock.now() thay vì date.today() để test cố định được thời gian.

    Ranh giới là "sau hôm nay" mới bị chặn — thú cưng sinh hôm nay là hợp lệ.
    """
    if ngay_sinh is None:
        return None
    hom_nay = clock.now().date()
    if ngay_sinh > hom_nay:
        raise LoiNghiepVu("Ngày sinh không được ở tương lai.")
    if ngay_sinh < hom_nay.replace(year=hom_nay.year - TUOI_TOI_DA_NAM):
        raise LoiNghiepVu(
            f"Ngày sinh không được quá {TUOI_TOI_DA_NAM} năm trước — kiểm lại xem có gõ nhầm không."
        )
    return ngay_sinh


def _kiem_can_nang(can_nang: float | None) -> float | None:
    """TC-019. Để trống khi chưa cân; 0 kg cũng vô lý như số âm."""
    if can_nang is None:
        return None
    if can_nang <= 0:
        raise LoiNghiepVu("Cân nặng phải lớn hơn 0. Chưa cân thì để trống.")
    if can_nang > CAN_NANG_TOI_DA:
        raise LoiNghiepVu(
            f"Cân nặng không được quá {CAN_NANG_TOI_DA} kg — kiểm lại xem có gõ nhầm không."
        )
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
