"""Nâng cấp schema: thêm cột còn thiếu vào bảng đã có.

Dự án không dùng Alembic. `Base.metadata.create_all` chỉ tạo bảng chưa có, không bao giờ thêm
cột — nên một `petcare.db` dựng từ bản cũ sẽ thiếu mọi cột thêm về sau và nổ 500 ở truy vấn
đầu tiên chạm cột đó. Hàm này đọc cột thật trong CSDL, so với model, rồi `ALTER TABLE ADD COLUMN`
phần thiếu. Chạy lại bao nhiêu lần cũng an toàn.

Chỉ làm việc SQLite cho phép, và từ chối thẳng phần còn lại thay vì làm sai âm thầm:
cột khóa chính, cột UNIQUE, cột NOT NULL không có `server_default`. Cột khóa ngoại được thêm
KHÔNG kèm ràng buộc FK (SQLite chỉ nhận ràng buộc lúc tạo bảng); CSDL dựng mới thì có đủ.

Không import fastapi.
"""

from sqlalchemy import MetaData, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateColumn


class LoiNangCap(Exception):
    """Không nâng cấp tự động được — cần xóa CSDL demo hoặc sửa tay."""


def nang_cap_schema(engine: Engine, metadata: MetaData) -> list[str]:
    """Thêm các cột còn thiếu; trả danh sách `"bang.cot"` đã thêm (rỗng nếu không có gì)."""
    thanh_tra = inspect(engine)
    cot_can_them = []
    for bang in metadata.sorted_tables:
        # Bảng chưa có là việc của create_all, không phải của hàm này.
        if not thanh_tra.has_table(bang.name):
            continue
        da_co = {c["name"] for c in thanh_tra.get_columns(bang.name)}
        for cot in bang.columns:
            if cot.name in da_co:
                continue
            ten = f"{bang.name}.{cot.name}"
            if cot.primary_key or cot.unique:
                raise LoiNangCap(f"Cột {ten} là khóa chính/UNIQUE, SQLite không thêm được vào bảng có sẵn.")
            if not cot.nullable and cot.server_default is None:
                raise LoiNangCap(
                    f"Cột {ten} là NOT NULL nhưng không có server_default, SQLite không thêm được "
                    "vào bảng có sẵn. Khai báo server_default trong model, hoặc xóa CSDL demo."
                )
            cot_can_them.append((bang, cot))

    # Kiểm hết rồi mới ghi: một cột không thêm được thì không để lại bảng nâng cấp nửa chừng.
    da_them = []
    with engine.begin() as ket_noi:
        for bang, cot in cot_can_them:
            khai_bao = CreateColumn(cot).compile(dialect=engine.dialect)
            ket_noi.execute(text(f'ALTER TABLE "{bang.name}" ADD COLUMN {khai_bao}'))
            for chi_muc in bang.indexes:
                if cot in chi_muc.columns.values():
                    chi_muc.create(ket_noi, checkfirst=True)
            da_them.append(f"{bang.name}.{cot.name}")
    return da_them
