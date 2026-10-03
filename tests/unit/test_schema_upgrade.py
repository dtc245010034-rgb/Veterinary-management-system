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


# --- Dựng lại bảng appointments cho CSDL cũ (P9 chặng 5) ----------------------------------------------


def _csdl_lich_hen_cu():
    """CSDL dựng từ trước chặng 5: CHECK chưa có `pending`, `created_by` NOT NULL, chưa có customer_id/decided_by.

    Có bảng con `invoices` tham chiếu `appointments(id)` — chính thứ làm việc dựng lại bảng dễ hỏng nhất
    (DROP bảng cha khi bảng con còn dòng, hoặc đổi tên làm bảng con trỏ nhầm sang bảng tạm).
    """
    e = create_engine("sqlite://")
    with e.begin() as c:
        for bang in ("users", "pets", "services", "customers"):
            c.execute(text(f"CREATE TABLE {bang} (id INTEGER PRIMARY KEY)"))
            c.execute(text(f"INSERT INTO {bang} (id) VALUES (1)"))
        c.execute(
            text(
                "CREATE TABLE appointments (id INTEGER NOT NULL PRIMARY KEY, pet_id INTEGER NOT NULL, "
                "service_id INTEGER NOT NULL, staff_id INTEGER NOT NULL, start_at DATETIME NOT NULL, "
                "end_at DATETIME NOT NULL, status VARCHAR(20) NOT NULL, note TEXT, cancel_reason TEXT, "
                "created_by INTEGER NOT NULL, created_at DATETIME NOT NULL, "
                "CONSTRAINT ck_appointments_thoi_gian CHECK (end_at > start_at), "
                "CONSTRAINT ck_appointments_status CHECK (status IN ('booked', 'rescheduled', 'cancelled', 'done')), "
                "FOREIGN KEY(pet_id) REFERENCES pets (id), FOREIGN KEY(service_id) REFERENCES services (id), "
                "FOREIGN KEY(staff_id) REFERENCES users (id), FOREIGN KEY(created_by) REFERENCES users (id))"
            )
        )
        c.execute(text("CREATE INDEX ix_appointments_staff_start ON appointments (staff_id, start_at)"))
        c.execute(text("CREATE INDEX ix_appointments_pet_start ON appointments (pet_id, start_at)"))
        c.execute(
            text(
                "CREATE TABLE invoices (id INTEGER PRIMARY KEY, appointment_id INTEGER UNIQUE "
                "REFERENCES appointments (id))"
            )
        )
        c.execute(
            text(
                "INSERT INTO appointments VALUES (7, 1, 1, 1, '2026-03-12 09:00:00', '2026-03-12 10:00:00', "
                "'done', 'ghi chu', NULL, 1, '2026-03-01 08:00:00')"
            )
        )
        c.execute(text("INSERT INTO invoices VALUES (1, 7)"))
    return e


def _them_lich_cho(c, ma=8):
    c.execute(
        text(
            "INSERT INTO appointments (id, pet_id, service_id, staff_id, start_at, end_at, status, created_by, "
            "customer_id, created_at) VALUES (:ma, 1, 1, 1, '2026-03-13 09:00:00', '2026-03-13 10:00:00', "
            "'pending', NULL, 1, '2026-03-12 08:00:00')"
        ),
        {"ma": ma},
    )


def test_bang_lich_hen_cu_khong_chen_duoc_pending_truoc_khi_dung_lai():
    # Chứng minh vấn đề có thật: không dựng lại thì `pending` bị CSDL cũ từ chối.
    e = _csdl_lich_hen_cu()
    with pytest.raises(Exception, match="CHECK"):
        with e.begin() as c:
            c.execute(
                text(
                    "INSERT INTO appointments (id, pet_id, service_id, staff_id, start_at, end_at, status, "
                    "created_by, created_at) VALUES (8, 1, 1, 1, '2026-03-13 09:00:00', '2026-03-13 10:00:00', "
                    "'pending', 1, '2026-03-12 08:00:00')"
                )
            )
    e.dispose()


def test_dung_lai_bang_lich_hen_giu_du_lieu_va_nhan_pending():
    from app.db import Base
    from app.services.schema import dung_lai_bang_lich_hen

    e = _csdl_lich_hen_cu()
    assert dung_lai_bang_lich_hen(e, Base.metadata) is True

    with e.begin() as c:
        _them_lich_cho(c)  # pending + created_by NULL + customer_id: trước đó bị từ chối
    with e.connect() as c:
        cu = c.execute(
            text("SELECT status, note, created_by, customer_id, decided_by FROM appointments WHERE id = 7")
        ).one()
        so_hd = c.execute(text("SELECT COUNT(*) FROM invoices")).scalar_one()
    assert cu == ("done", "ghi chu", 1, None, None)
    assert so_hd == 1
    e.dispose()


def test_dung_lai_bang_lich_hen_giu_khoa_ngoai_cua_bang_con_va_index():
    from app.db import Base
    from app.services.schema import dung_lai_bang_lich_hen

    e = _csdl_lich_hen_cu()
    dung_lai_bang_lich_hen(e, Base.metadata)

    with e.connect() as c:
        # Bảng con vẫn trỏ về `appointments` (không phải bảng tạm), và khóa ngoại vẫn có hiệu lực.
        tham_chieu = [r[2] for r in c.execute(text("PRAGMA foreign_key_list(invoices)"))]
        assert tham_chieu == ["appointments"]
        assert c.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    with pytest.raises(Exception, match="FOREIGN KEY"):
        with e.begin() as c:
            c.execute(text("INSERT INTO invoices VALUES (2, 999)"))
    ten_index = {i["name"] for i in inspect(e).get_indexes("appointments")}
    assert {"ix_appointments_staff_start", "ix_appointments_pet_start"} <= ten_index
    assert "appointments_cu" not in inspect(e).get_table_names()
    e.dispose()


def test_dung_lai_bang_lich_hen_chay_lan_hai_khong_lam_gi():
    from app.db import Base
    from app.services.schema import dung_lai_bang_lich_hen

    e = _csdl_lich_hen_cu()
    assert dung_lai_bang_lich_hen(e, Base.metadata) is True

    assert dung_lai_bang_lich_hen(e, Base.metadata) is False
    e.dispose()


def test_dung_lai_bang_lich_hen_bo_qua_csdl_moi_va_csdl_chua_co_bang(db):
    from app.db import Base
    from app.services.schema import dung_lai_bang_lich_hen

    assert dung_lai_bang_lich_hen(db.get_bind(), Base.metadata) is False  # dựng từ model hiện tại: đã đủ
    trong = create_engine("sqlite://")
    assert dung_lai_bang_lich_hen(trong, Base.metadata) is False  # chưa có bảng: việc của create_all
    trong.dispose()


# --- Dựng lại bảng ai_logs cho CSDL cũ (P9 chặng 7) -----------------------------------------------------


def _csdl_nhat_ky_ai_cu():
    """CSDL dựng từ trước chặng 7: `ai_logs.user_id` NOT NULL và chưa có `customer_id`."""
    e = create_engine("sqlite://")
    with e.begin() as c:
        for bang in ("users", "customers"):
            c.execute(text(f"CREATE TABLE {bang} (id INTEGER PRIMARY KEY)"))
            c.execute(text(f"INSERT INTO {bang} (id) VALUES (1)"))
        c.execute(
            text(
                "CREATE TABLE ai_logs (id INTEGER NOT NULL PRIMARY KEY, user_id INTEGER NOT NULL, "
                "feature VARCHAR(20) NOT NULL, prompt TEXT NOT NULL, response TEXT, is_error BOOLEAN NOT NULL, "
                "model VARCHAR(60), created_at DATETIME NOT NULL, "
                "CONSTRAINT ck_ai_logs_feature CHECK (feature IN ('reminder', 'summary', 'qa')), "
                "FOREIGN KEY(user_id) REFERENCES users (id))"
            )
        )
        c.execute(
            text(
                "INSERT INTO ai_logs VALUES (5, 1, 'qa', 'cau hoi cu', 'tra loi cu', 0, 'gemini-x', "
                "'2026-03-01 08:00:00')"
            )
        )
    return e


def _them_log_khach(c, ma=6):
    c.execute(
        text(
            "INSERT INTO ai_logs (id, user_id, customer_id, feature, prompt, is_error, created_at) "
            "VALUES (:ma, NULL, 1, 'qa', 'hoi', 0, '2026-03-12 08:00:00')"
        ),
        {"ma": ma},
    )


def test_bang_ai_logs_cu_khong_nhan_duoc_dong_cua_khach_truoc_khi_dung_lai():
    # Chứng minh vấn đề có thật: user_id NOT NULL và chưa có customer_id.
    e = _csdl_nhat_ky_ai_cu()
    with pytest.raises(Exception, match="customer_id|NOT NULL"):
        with e.begin() as c:
            _them_log_khach(c)
    e.dispose()


def test_dung_lai_bang_nhat_ky_ai_giu_dong_cu_va_nhan_dong_cua_khach():
    from app.db import Base
    from app.services.schema import dung_lai_bang_nhat_ky_ai

    e = _csdl_nhat_ky_ai_cu()
    assert dung_lai_bang_nhat_ky_ai(e, Base.metadata) is True

    with e.begin() as c:
        _them_log_khach(c)
    with e.connect() as c:
        cu = c.execute(
            text("SELECT user_id, customer_id, feature, prompt, response, model FROM ai_logs WHERE id = 5")
        ).one()
        khach = c.execute(text("SELECT user_id, customer_id FROM ai_logs WHERE id = 6")).one()
    assert cu == (1, None, "qa", "cau hoi cu", "tra loi cu", "gemini-x")
    assert khach == (None, 1)
    assert "ai_logs_cu" not in inspect(e).get_table_names()
    e.dispose()


def test_nhat_ky_ai_sau_khi_dung_lai_van_buoc_dung_mot_trong_hai_chu_so_huu():
    from app.db import Base
    from app.services.schema import dung_lai_bang_nhat_ky_ai

    e = _csdl_nhat_ky_ai_cu()
    dung_lai_bang_nhat_ky_ai(e, Base.metadata)

    for user_id, customer_id in ((None, None), (1, 1)):
        with pytest.raises(Exception, match="CHECK"):
            with e.begin() as c:
                c.execute(
                    text(
                        "INSERT INTO ai_logs (user_id, customer_id, feature, prompt, is_error, created_at) "
                        "VALUES (:u, :k, 'qa', 'hoi', 0, '2026-03-12 08:00:00')"
                    ),
                    {"u": user_id, "k": customer_id},
                )
    e.dispose()


def test_dung_lai_bang_nhat_ky_ai_chay_lan_hai_khong_lam_gi():
    from app.db import Base
    from app.services.schema import dung_lai_bang_nhat_ky_ai

    e = _csdl_nhat_ky_ai_cu()
    assert dung_lai_bang_nhat_ky_ai(e, Base.metadata) is True

    assert dung_lai_bang_nhat_ky_ai(e, Base.metadata) is False
    e.dispose()


def test_dung_lai_bang_nhat_ky_ai_di_sau_nang_cap_cot_van_nhan_dong_cua_khach():
    # Đúng thứ tự thật lúc khởi động (app/main.py): nang_cap_schema đã thêm cột + index trước, rồi mới dựng lại.
    # Dựng lại tay hai bước đó vì CSDL cũ giả ở đây chỉ có bảng `ai_logs` thật, các bảng khác chỉ có cột `id`.
    from app.db import Base
    from app.services.schema import dung_lai_bang_nhat_ky_ai

    e = _csdl_nhat_ky_ai_cu()
    with e.begin() as c:
        c.execute(text("ALTER TABLE ai_logs ADD COLUMN customer_id INTEGER"))
        c.execute(text("CREATE INDEX ix_ai_logs_customer_id ON ai_logs (customer_id)"))
    assert dung_lai_bang_nhat_ky_ai(e, Base.metadata) is True

    with e.begin() as c:
        _them_log_khach(c)
    e.dispose()


def test_dung_lai_bang_nhat_ky_ai_bo_qua_csdl_moi_va_csdl_chua_co_bang(db):
    from app.db import Base
    from app.services.schema import dung_lai_bang_nhat_ky_ai

    assert dung_lai_bang_nhat_ky_ai(db.get_bind(), Base.metadata) is False
    trong = create_engine("sqlite://")
    assert dung_lai_bang_nhat_ky_ai(trong, Base.metadata) is False
    trong.dispose()
