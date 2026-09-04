"""Fixture dùng chung cho toàn bộ test.

Theo docs/testing/test-strategy.md mục 5. Năm fixture: db, client, fake_ai,
frozen_clock, seed_basic.

Các import của ứng dụng đặt bên trong thân fixture, không đặt ở đầu file. Lý do: test
tầng unit (ví dụ test_security.py) phải chạy được ngay cả khi app/main.py chưa tồn tại.
Import ở đầu file sẽ làm pytest lỗi ngay khi thu thập test, và mọi test đều đỏ vì cùng
một lý do không liên quan.
"""

import os
from datetime import datetime

import pytest

# Đặt TRƯỚC khi bất kỳ module app nào được import, vì app.config đọc biến môi trường
# ngay lúc import. Hạ số vòng bcrypt để bộ test không mất hàng chục giây chỉ để băm
# mật khẩu — thuật toán và cách kiểm tra vẫn y nguyên.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

# Mốc thời gian cố định dùng cho mọi test phụ thuộc ngày giờ.
# Chọn một ngày thứ Năm, giờ hành chính, để các ca đặt lịch trong ngày làm việc tự nhiên.
MOC_THOI_GIAN = datetime(2026, 3, 12, 8, 0, 0)


@pytest.fixture
def db():
    """Session SQLAlchemy trên SQLite in-memory, bảng tạo mới cho từng test.

    Không mock CSDL. SQLite in-memory nhanh tới mức không có lý do gì để mock, và
    dùng CSDL thật thì test bắt được cả lỗi ràng buộc UNIQUE, NOT NULL, CHECK.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import app.models  # noqa: F401 — đăng ký mọi bảng vào metadata trước create_all
    from app.db import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # giữ nguyên một kết nối, nếu không DB in-memory sẽ bị xóa
    )
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db):
    """TestClient dùng chung session với fixture db.

    Nhờ override get_db, thứ test chuẩn bị qua fixture db và thứ ứng dụng đọc qua HTTP
    là cùng một CSDL.

    Cố ý KHÔNG dùng `with TestClient(app)`. Context manager sẽ chạy lifespan của ứng
    dụng, mà lifespan gọi create_all trên engine thật — test sẽ tạo file petcare.db
    trong thư mục dự án và có thể ghi đè dữ liệu thật. Bảng cho test đã do fixture db
    tạo sẵn trên CSDL in-memory riêng.
    """
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def frozen_clock():
    """Cố định thời gian hệ thống ở MOC_THOI_GIAN trong suốt một test."""
    from app.services import clock

    with clock.freeze(MOC_THOI_GIAN):
        yield MOC_THOI_GIAN


@pytest.fixture
def fake_ai():
    """FakeProvider ghi lại mọi cặp (system, user) đã nhận.

    Việc ghi lại tham số là điều kiện để kiểm chứng US-28 — prompt không chứa dữ liệu
    cá nhân. Không có nó, US-28 chỉ là một dòng chữ trong tài liệu.

    Khung dựng ở P1; dùng thật từ P7 khi app/ai/ tồn tại.
    """
    pytest.skip("FakeProvider có từ phase P7")


MAT_KHAU_MAU = "matkhau123"


@pytest.fixture(scope="session")
def bam_mat_khau_mau():
    """Băm MAT_KHAU_MAU đúng một lần cho cả phiên test.

    bcrypt cố tình chậm — đó là điểm mạnh của nó khi chạy thật, nhưng nếu băm lại cho
    từng tài khoản của từng test thì riêng việc dựng dữ liệu mẫu đã ngốn vài giây mỗi
    test. Cùng một mật khẩu thì một chuỗi băm là đủ.
    """
    from app.security import hash_password

    return hash_password(MAT_KHAU_MAU)


@pytest.fixture
def seed_basic(db, bam_mat_khau_mau):
    """Dữ liệu mẫu tối thiểu: 1 manager, 1 receptionist, 2 caretaker.

    Mật khẩu của mọi tài khoản đều là 'matkhau123' để test đăng nhập đọc dễ.
    Owner, pet, service sẽ thêm vào fixture này ở P2 khi các model đó tồn tại.
    """
    from app.models.user import User

    tai_khoan = [
        User(username="quanly", full_name="Nguyen Van Quan", role="manager"),
        User(username="letan", full_name="Tran Thi Le", role="receptionist"),
        User(username="chamsoc1", full_name="Le Van Cham", role="caretaker"),
        User(username="chamsoc2", full_name="Pham Thi Soc", role="caretaker"),
    ]
    for u in tai_khoan:
        u.password_hash = bam_mat_khau_mau
        db.add(u)
    db.commit()
    for u in tai_khoan:
        db.refresh(u)

    return {
        "manager": tai_khoan[0],
        "receptionist": tai_khoan[1],
        "caretaker1": tai_khoan[2],
        "caretaker2": tai_khoan[3],
        "mat_khau": MAT_KHAU_MAU,
    }
