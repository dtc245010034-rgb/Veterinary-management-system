"""Nghiệp vụ tiêm phòng: ghi mũi tiêm, hồ sơ tiêm của thú cưng, danh sách đến hạn.

Phục vụ US-17, US-18 — TC-059 → TC-064. Không import fastapi.

Đây là chức năng **thông tin**, không phải chỉ định y tế: hệ thống không tự sinh lịch
tiêm, không gợi ý loại vắc-xin, không tính khoảng cách giữa các mũi. Nó chỉ ghi lại điều
người dùng nhập và nhắc lại đúng ngày họ đã ghi. Xem docs/ai-safety.md.

Cả ba vai trò đều có toàn quyền ở mục này theo bảng phân quyền US-02, nên ở đây không có
phép kiểm vai trò nào.
"""

from datetime import date, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.pet import Pet
from app.models.vaccination import Vaccination
from app.services import clock
from app.services.errors import LoiNghiepVu

# Khoảng nhìn trước của danh sách đến hạn, tính từ hôm nay — US-18.
SO_NGAY_NHAC = 30


def ghi_mui_tiem(
    db: Session,
    thu_cung_id: int,
    ten_vac_xin: str | None,
    ngay_tiem: date | None,
    han_nhac: date | None = None,
    so_mui: int | None = None,
    ghi_chu: str | None = None,
) -> Vaccination:
    """TC-059 → TC-061.

    Ba phép kiểm, theo đúng thứ tự tiêu chí của US-17: thú cưng có thật, ngày tiêm không
    ở tương lai, hạn nhắc không sớm hơn ngày tiêm.
    """
    if db.get(Pet, thu_cung_id) is None:
        raise LoiNghiepVu("Không tìm thấy thú cưng.")

    ten = (ten_vac_xin or "").strip()
    if not ten:
        raise LoiNghiepVu("Tên vắc-xin không được để trống.")

    if ngay_tiem is None:
        raise LoiNghiepVu("Ngày tiêm không được để trống.")
    if ngay_tiem > clock.now().date():
        raise LoiNghiepVu("Ngày tiêm không được ở tương lai.")

    # Ranh giới là "sớm hơn", không phải "bằng": tiêm và nhắc lại trong cùng ngày là dữ
    # liệu hợp lệ, dù hiếm.
    if han_nhac is not None and han_nhac < ngay_tiem:
        raise LoiNghiepVu("Ngày hạn nhắc lại không được sớm hơn ngày tiêm.")

    if so_mui is not None and so_mui <= 0:
        raise LoiNghiepVu("Mũi thứ mấy phải là số lớn hơn 0. Không biết thì để trống.")

    v = Vaccination(
        pet_id=thu_cung_id,
        vaccine_name=ten,
        dose_no=so_mui,
        given_at=ngay_tiem,
        next_due_at=han_nhac,
        note=(ghi_chu or "").strip() or None,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def ho_so_tiem(db: Session, thu_cung_id: int) -> list[Vaccination]:
    """Toàn bộ mũi tiêm của một thú cưng, mới nhất lên đầu — US-17, TC-020.

    Khác `den_han()`: ở đây là hồ sơ, giữ đủ mọi mũi kể cả mũi đã có mũi sau thay thế.
    """
    return list(
        db.scalars(
            select(Vaccination)
            .where(Vaccination.pet_id == thu_cung_id)
            .order_by(Vaccination.given_at.desc(), Vaccination.id.desc())
        )
    )


def den_han(db: Session, so_ngay: int = SO_NGAY_NHAC) -> list[Vaccination]:
    """TC-062: hạn nhắc từ quá khứ tới hôm nay + `so_ngay`, hạn gần lên trước.

    Chỉ tính **mũi mới nhất của mỗi loại vắc-xin trên mỗi thú cưng**. Mũi cũ đã có mũi
    sau nối tiếp thì lời nhắc của nó đã hoàn thành; tính cả nó thì nó nằm lì trong danh
    sách quá hạn vĩnh viễn và cả màn hình mất tác dụng. US-18 được sửa công khai ngày
    05/09 để nói rõ điều này.

    Khoảng mở về phía quá khứ chứ không phải chỉ 30 ngày tới: thú cưng quá hạn là đúng
    nhóm cần gọi nhắc nhất, chặn nó lại thì màn hình bỏ sót đúng người quan trọng nhất.
    """
    hom_nay = clock.now().date()
    sau_hon = aliased(Vaccination)

    # "Mũi mới nhất" = không tồn tại mũi nào cùng thú cưng, cùng loại vắc-xin, tiêm sau
    # nó. Cùng ngày thì lấy bản ghi nhập sau — hai mũi cùng loại trong một ngày là dữ
    # liệu bất thường, nhưng phải chọn dứt khoát một bản ghi thay vì hiện cả hai.
    co_mui_sau = (
        select(sau_hon.id)
        .where(
            sau_hon.pet_id == Vaccination.pet_id,
            sau_hon.vaccine_name == Vaccination.vaccine_name,
            or_(
                sau_hon.given_at > Vaccination.given_at,
                and_(sau_hon.given_at == Vaccination.given_at, sau_hon.id > Vaccination.id),
            ),
        )
        .exists()
    )

    return list(
        db.scalars(
            select(Vaccination)
            .where(
                Vaccination.next_due_at.is_not(None),
                Vaccination.next_due_at <= hom_nay + timedelta(days=so_ngay),
                ~co_mui_sau,
            )
            .order_by(Vaccination.next_due_at, Vaccination.id)
        )
    )
