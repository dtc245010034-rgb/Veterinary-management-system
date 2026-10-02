"""Hàm nâng cấp schema `app/services/schema.py`: thêm cột còn thiếu vào bảng đã có.

Lý do tồn tại: dự án không có migration, mà `create_all` chỉ tạo bảng thiếu, không bao giờ thêm
cột. Một `petcare.db` dựng từ bản cũ sẽ thiếu cột mới và mọi truy vấn chạm cột đó nổ 500.

Test dựng CSDL "cũ" bằng SQL thô rồi cho nâng cấp lên metadata mới — đúng tình huống thật, không
mock engine.
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect, text

from app.services.schema import LoiNangCap, nang_cap_schema


@pytest.fixture
def engine():
    e = create_engine("sqlite://")
    yield e
    e.dispose()


def _cot(engine, bang):
    return {c["name"] for c in inspect(engine).get_columns(bang)}


def _csdl_cu(engine):
    with engine.begin() as c:
        c.execute(text("CREATE TABLE khach (id INTEGER PRIMARY KEY, ten VARCHAR(50) NOT NULL)"))
        c.execute(text("INSERT INTO khach (ten) VALUES ('An'), ('Binh')"))


def _metadata_moi(*cot_them):
    md = MetaData()
    Table("khach", md, Column("id", Integer, primary_key=True), Column("ten", String(50), nullable=False), *cot_them)
    return md


def test_them_cot_cho_null_va_cot_not_null_co_server_default(engine):
    _csdl_cu(engine)
    md = _metadata_moi(
        Column("ghi_chu", String(100), nullable=True),
        Column("phien_ban", Integer, nullable=False, server_default="0"),
    )

    da_them = nang_cap_schema(engine, md)

    assert da_them == ["khach.ghi_chu", "khach.phien_ban"]
    assert {"ghi_chu", "phien_ban"} <= _cot(engine, "khach")
    with engine.connect() as c:
        hang = c.execute(text("SELECT ten, ghi_chu, phien_ban FROM khach ORDER BY id")).all()
    # Dữ liệu cũ còn nguyên, cột NOT NULL mới nhận giá trị mặc định.
    assert hang == [("An", None, 0), ("Binh", None, 0)]


def test_chay_lan_hai_khong_lam_gi_va_khong_nhan_doi_cot(engine):
    _csdl_cu(engine)
    md = _metadata_moi(Column("phien_ban", Integer, nullable=False, server_default="0"))
    nang_cap_schema(engine, md)

    da_them_lan_hai = nang_cap_schema(engine, md)

    assert da_them_lan_hai == []
    ten_cot = [c["name"] for c in inspect(engine).get_columns("khach")]
    assert ten_cot.count("phien_ban") == 1


def test_bang_chua_ton_tai_thi_bo_qua_de_create_all_lo(engine):
    md = _metadata_moi(Column("ghi_chu", String(10)))

    assert nang_cap_schema(engine, md) == []
    assert "khach" not in inspect(engine).get_table_names()


def test_cot_not_null_khong_co_default_bi_tu_choi_va_khong_sua_gi(engine):
    # SQLite không thêm được cột NOT NULL không giá trị mặc định vào bảng đã có dòng.
    # Phải báo rõ chứ không được nuốt lỗi hay âm thầm tạo cột sai ràng buộc.
    _csdl_cu(engine)
    md = _metadata_moi(Column("bat_buoc", String(10), nullable=False))

    with pytest.raises(LoiNangCap, match="khach.bat_buoc"):
        nang_cap_schema(engine, md)

    assert "bat_buoc" not in _cot(engine, "khach")


def test_cot_unique_bi_tu_choi(engine):
    _csdl_cu(engine)
    md = _metadata_moi(Column("ma", String(10), unique=True))

    with pytest.raises(LoiNangCap, match="khach.ma"):
        nang_cap_schema(engine, md)


def test_cot_co_index_duoc_tao_index(engine):
    _csdl_cu(engine)
    md = _metadata_moi(Column("nhom", String(10), index=True))

    nang_cap_schema(engine, md)

    chi_muc = inspect(engine).get_indexes("khach")
    assert [i["column_names"] for i in chi_muc] == [["nhom"]]


def test_metadata_that_cua_du_an_khoi_phuc_cot_bi_mat(db):
    # CSDL dựng từ model hiện tại, rồi "cũ đi" bằng cách bỏ một cột nullable có thật.
    from app.db import Base

    engine = db.get_bind()
    with engine.begin() as c:
        c.execute(text("ALTER TABLE owners DROP COLUMN email"))
    assert "email" not in _cot(engine, "owners")

    da_them = nang_cap_schema(engine, Base.metadata)

    assert da_them == ["owners.email"]
    assert "email" in _cot(engine, "owners")


def test_csdl_cu_khong_co_session_version_duoc_nang_cap_voi_gia_tri_0():
    """Mô hình `User` thật trên một bảng `users` dựng từ trước R-3: cookie đang có phải còn dùng được."""
    from app.db import Base

    e = create_engine("sqlite://")
    with e.begin() as c:
        c.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, "
                "password_hash VARCHAR(255) NOT NULL, full_name VARCHAR(100) NOT NULL, "
                "role VARCHAR(20) NOT NULL, is_active BOOLEAN NOT NULL, created_at DATETIME NOT NULL)"
            )
        )
        c.execute(text("INSERT INTO users VALUES (1, 'a', 'x', 'A', 'manager', 1, '2026-01-01 00:00:00')"))

    da_them = nang_cap_schema(e, Base.metadata)

    assert "users.session_version" in da_them
    with e.connect() as c:
        assert c.execute(text("SELECT session_version FROM users")).scalar_one() == 0
    e.dispose()
