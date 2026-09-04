"""Kết nối cơ sở dữ liệu và session SQLAlchemy.

Base ở đây là lớp cha của mọi model. get_db() là dependency của FastAPI, và cũng là
điểm để test thay bằng CSDL in-memory qua app.dependency_overrides.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite: cho phép dùng qua nhiều luồng
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _bat_khoa_ngoai(dbapi_connection, connection_record):
    """SQLite mặc định KHÔNG kiểm tra khóa ngoại — phải bật thủ công từng kết nối.

    Không bật thì mọi ràng buộc FK trong ERD chỉ là chú thích, và các ca như
    "xóa chủ nuôi còn thú cưng thì bị chặn" sẽ âm thầm không hoạt động.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    """Cấp một session cho mỗi request và đóng lại khi xong."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
