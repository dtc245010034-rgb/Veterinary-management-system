"""Nâng cấp schema: thêm cột còn thiếu vào bảng đã có.

Dự án không dùng Alembic. `Base.metadata.create_all` chỉ tạo bảng chưa có, không bao giờ thêm
cột — nên một `petcare.db` dựng từ bản cũ sẽ thiếu mọi cột thêm về sau và nổ 500 ở truy vấn
đầu tiên chạm cột đó. Hàm này đọc cột thật trong CSDL, so với model, rồi `ALTER TABLE ADD COLUMN`
phần thiếu. Chạy lại bao nhiêu lần cũng an toàn.

Chỉ làm việc SQLite cho phép, và từ chối thẳng phần còn lại thay vì làm sai âm thầm:
cột khóa chính, cột UNIQUE, cột NOT NULL không có `server_default`. Cột khóa ngoại được thêm
KHÔNG kèm ràng buộc FK (SQLite chỉ nhận ràng buộc lúc tạo bảng); CSDL dựng mới thì có đủ.

`dung_lai_bang_lich_hen` và `dung_lai_bang_nhat_ky_ai` làm phần `ADD COLUMN` không làm được: đổi ràng buộc CHECK và
NOT NULL của bảng có sẵn (P9 chặng 5: `appointments` nhận trạng thái `pending` và cho `created_by` NULL; chặng 7:
`ai_logs.user_id` cho NULL vì dòng của khách mang `customer_id`).

Không import fastapi.
"""

from sqlalchemy import MetaData, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateColumn, CreateIndex, CreateTable


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


def dung_lai_bang_lich_hen(engine: Engine, metadata: MetaData) -> bool:
    """Dựng lại `appointments` theo model hiện tại nếu bảng cũ chưa nhận trạng thái `pending`.

    SQLite không sửa được CHECK hay bỏ NOT NULL của cột có sẵn, nên phải dựng bảng mới, chép dòng sang, bỏ bảng
    cũ (quy trình trong tài liệu "ALTER TABLE" của SQLite). Hai bẫy đã tính:

    - Bảng con (`invoices`, `care_records`) tham chiếu `appointments(id)`. Tắt khóa ngoại để DROP không bị chặn,
      và bật `legacy_alter_table` để đổi tên bảng cũ KHÔNG kéo các tham chiếu của bảng con sang tên tạm.
    - Cả quy trình nằm trong một giao dịch: lỗi giữa chừng thì bảng cũ còn nguyên.

    Trả True nếu đã dựng lại, False nếu không cần (bảng chưa có, hoặc đã đủ). Chạy lại bao nhiêu lần cũng an toàn.
    """
    with engine.connect() as ket_noi:
        ddl_hien_tai = ket_noi.execute(
            text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'appointments'")
        ).scalar()
    if ddl_hien_tai is None or "'pending'" in ddl_hien_tai:
        return False

    _dung_lai_bang(engine, metadata.tables["appointments"])
    return True


def dung_lai_bang_nhat_ky_ai(engine: Engine, metadata: MetaData) -> bool:
    """Dựng lại `ai_logs` nếu `user_id` còn NOT NULL (bảng dựng từ trước P9 chặng 7).

    Cùng quy trình với `dung_lai_bang_lich_hen`; `ai_logs` không có bảng con nên không cần lo khóa ngoại đi vào.
    Trả True nếu đã dựng lại, False nếu không cần (bảng chưa có, hoặc `user_id` đã cho NULL).
    """
    with engine.connect() as ket_noi:
        cot_cu = ket_noi.execute(text("PRAGMA table_info(ai_logs)")).fetchall()
    user_id = next((hang for hang in cot_cu if hang[1] == "user_id"), None)
    if user_id is None or not user_id[3]:  # chưa có bảng, hoặc cột đã cho NULL
        return False

    _dung_lai_bang(engine, metadata.tables["ai_logs"])
    return True


def _dung_lai_bang(engine: Engine, bang) -> None:
    """Dựng bảng mới theo model, chép các cột chung, bỏ bảng cũ — trong một giao dịch."""
    ten = bang.name
    raw = engine.raw_connection()
    try:
        raw.isolation_level = None  # tự quản lý giao dịch: PRAGMA khóa ngoại không có tác dụng trong giao dịch
        con_tro = raw.cursor()
        con_tro.execute("PRAGMA foreign_keys=OFF")
        con_tro.execute("PRAGMA legacy_alter_table=ON")
        con_tro.execute("BEGIN")
        try:
            cot_cu = {hang[1] for hang in con_tro.execute(f"PRAGMA table_info({ten})").fetchall()}
            cot_chung = ", ".join(f'"{c.name}"' for c in bang.columns if c.name in cot_cu)
            con_tro.execute(f"ALTER TABLE {ten} RENAME TO {ten}_cu")
            con_tro.execute(str(CreateTable(bang).compile(dialect=engine.dialect)))
            con_tro.execute(f"INSERT INTO {ten} ({cot_chung}) SELECT {cot_chung} FROM {ten}_cu")
            con_tro.execute(f"DROP TABLE {ten}_cu")
            for chi_muc in bang.indexes:
                con_tro.execute(str(CreateIndex(chi_muc).compile(dialect=engine.dialect)))
            if con_tro.execute("PRAGMA foreign_key_check").fetchall():
                raise LoiNangCap(f"Dựng lại bảng {ten} làm hỏng khóa ngoại; đã hoàn tác.")
            con_tro.execute("COMMIT")
        except BaseException:
            con_tro.execute("ROLLBACK")
            raise
        finally:
            con_tro.execute("PRAGMA legacy_alter_table=OFF")
            con_tro.execute("PRAGMA foreign_keys=ON")
    finally:
        raw.close()
